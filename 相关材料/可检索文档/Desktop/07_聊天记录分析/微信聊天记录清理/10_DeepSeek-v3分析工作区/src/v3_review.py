"""v3 人机协作复核与价值判断：复核包 → 静态 HTML 复核界面 → 反馈落库 → 会话级价值汇总。

全程不调用 API：
- build_review_bundle：从 v3_annotations + segments.transcript 构建复核包；
- render_review_html：把复核包内嵌进自包含 HTML（双击打开，无服务器，导出 review_feedback.jsonl）；
- load_feedback：读取并校验复核界面导出的反馈；
- apply_feedback：写 v3_review 表（片段级：确认/修正/拒绝 + 手动价值）；
- aggregate_final_judgments：按 conversation_id 聚合手动价值 → v3_final_judgments。

注意：v3_annotations.conversation_id 历史为空，会话 ID 一律经 segments 表解析。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .v3_core import build_units
from .v3_io import ensure_v3_schema, upsert_final_judgment, upsert_review, utc_now, write_json_atomic

#: 复核界面展示的候选组（顺序即展示顺序）
CANDIDATE_GROUPS: tuple[tuple[str, str], ...] = (
    ("relationship_signals", "关系信号"),
    ("requests", "请求"),
    ("commitments", "承诺"),
    ("events", "事件"),
    ("entities", "实体"),
    ("memory_candidates", "记忆候选"),
    ("alternative_explanations", "替代解释"),
)

VALUE_TAGS: tuple[str, ...] = ("亲情", "友情", "工作", "生意", "信息源", "其他")
KEEP_OPTIONS: tuple[tuple[str, str], ...] = (("keep", "保留"), ("pending", "待定"), ("cleanup", "清理"))


def _connect_ro(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _window_size(cfg: dict) -> int:
    return int(cfg.get("batching", {}).get("window_size_msgs", 15) or 15)


def _bucket_of(message_count: int) -> str:
    if message_count <= 1:
        return "1"
    if message_count <= 3:
        return "2-3"
    if message_count <= 10:
        return "4-10"
    if message_count <= 30:
        return "11-30"
    return "31+"


def load_annotated_units(cfg: dict, run_id: str) -> list[dict]:
    """读取指定运行成功单元的标注（只读，按 segment_id 分组由调用方处理）。"""
    conn = _connect_ro(cfg["paths"]["db"])
    try:
        rows = conn.execute(
            """
            SELECT unit_key, segment_id, window_idx, message_count, result_json
            FROM v3_annotations
            WHERE run_id=? AND status='success'
            ORDER BY segment_id, window_idx
            """,
            (run_id,),
        ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        ann: dict = {}
        if r["result_json"]:
            try:
                parsed = json.loads(r["result_json"])
                ann = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                ann = {}
        out.append({
            "unit_key": r["unit_key"],
            "segment_id": r["segment_id"],
            "window_idx": r["window_idx"],
            "message_count": r["message_count"],
            "annotation": ann,
        })
    return out


def build_review_bundle(cfg: dict, run_id: str) -> dict:
    """从已标注数据构建复核包：每段含原文证据行 + 模型候选判断，供人确认/修正/拒绝。

    证据行用 build_units + render_for_prompt 按窗口重建，与发送给模型的内容一致。
    """
    units = load_annotated_units(cfg, run_id)
    by_seg: dict[str, list[dict]] = {}
    for u in units:
        by_seg.setdefault(u["segment_id"], []).append(u)

    ws = _window_size(cfg)
    conn = _connect_ro(cfg["paths"]["db"])
    segments: list[dict] = []
    try:
        for seg_id in sorted(by_seg):
            trow = conn.execute(
                "SELECT transcript, conversation_id, message_count FROM segments WHERE id=?",
                (seg_id,),
            ).fetchone()
            if trow is None:
                continue
            conv = trow["conversation_id"] or ""
            built = build_units(
                seg_id,
                trow["transcript"],
                segment_sha256="",
                conversation_id=conv,
                window_size=ws,
                segment_message_count=trow["message_count"],
            )
            by_widx = {u.window_idx: u for u in built}
            seg_units = []
            for u in sorted(by_seg[seg_id], key=lambda x: x["window_idx"]):
                bu = by_widx.get(u["window_idx"])
                evidence_lines = bu.render_for_prompt().split("\n") if bu else []
                seg_units.append({
                    "unit_key": u["unit_key"],
                    "window_idx": u["window_idx"],
                    "message_count": u["message_count"],
                    "evidence_lines": evidence_lines,
                    "annotation": u["annotation"],
                })
            segments.append({
                "segment_id": seg_id,
                "conversation_id": conv,
                "message_count": int(trow["message_count"] or 0),
                "bucket": _bucket_of(int(trow["message_count"] or 0)),
                "units": seg_units,
            })
    finally:
        conn.close()

    return {
        "schema_version": "review-1.0",
        "run_id": run_id,
        "generated_at": utc_now(),
        "segment_count": len(segments),
        "unit_count": len(units),
        "segments": segments,
    }


def render_review_html(cfg: dict, bundle: dict) -> Path:
    """把复核包内嵌进自包含 HTML 并写出，返回 HTML 路径。"""
    out_dir = Path(cfg["paths"]["runs_dir"]) / bundle["run_id"] / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_dir / "review_bundle.json", bundle)
    data_json = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
    html = (
        _REVIEW_HTML_TEMPLATE
        .replace("__REVIEW_DATA__", data_json)
        .replace("__RUN_ID__", bundle["run_id"])
    )
    out_html = out_dir / "review.html"
    out_html.write_text(html, encoding="utf-8")
    return out_html


# ─── 反馈读取与落库 ────────────────────────────────────────────────────────────

_REVIEW_STATUSES = {"pending", "confirmed", "corrected"}


def load_feedback(path: Path) -> list[dict]:
    """读取复核界面导出的 review_feedback.jsonl 并校验结构。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"反馈文件不存在: {path}")
    out: list[dict] = []
    problems: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"第{lineno}行不是 JSON: {exc}")
                continue
            if not isinstance(obj, dict):
                problems.append(f"第{lineno}行不是对象")
                continue
            if not isinstance(obj.get("segment_id"), str) or not obj["segment_id"]:
                problems.append(f"第{lineno}行缺少 segment_id")
                continue
            st = obj.get("review_status", "pending")
            if st not in _REVIEW_STATUSES:
                problems.append(f"第{lineno}行 review_status 非法: {st!r}")
                continue
            if not isinstance(obj.get("corrections") or {}, dict):
                problems.append(f"第{lineno}行 corrections 不是对象")
                continue
            if obj.get("value_score") is not None and not isinstance(obj.get("value_score"), (int, float)):
                problems.append(f"第{lineno}行 value_score 非数值")
                continue
            keep = obj.get("keep_recommendation")
            if keep is not None and keep not in dict(KEEP_OPTIONS):
                problems.append(f"第{lineno}行 keep_recommendation 非法: {keep!r}")
                continue
            out.append(obj)
    if problems:
        raise ValueError("反馈文件校验失败：\n" + "\n".join(problems[:20]))
    return out


def apply_feedback(cfg: dict, run_id: str, feedback: list[dict]) -> int:
    """把反馈逐行 upsert 进 v3_review 表。返回写入行数。"""
    conn = sqlite3.connect(cfg["paths"]["db"], timeout=30)
    try:
        ensure_v3_schema(conn)
        for row in feedback:
            r = dict(row)
            r["run_id"] = run_id
            upsert_review(conn, r)
        conn.commit()
    finally:
        conn.close()
    return len(feedback)


def aggregate_final_judgments(cfg: dict, run_id: str) -> dict:
    """按会话聚合已复核片段的手动价值 → v3_final_judgments（0 API，规则派生）。

    派生规则（保守）：会话内 cleanup>0 → 清理；否则 pending>0 → 待定；否则保留。
    """
    conn = sqlite3.connect(cfg["paths"]["db"], timeout=30)
    try:
        rows = conn.execute(
            "SELECT segment_id, conversation_id, review_status, value_score, keep_recommendation "
            "FROM v3_review WHERE run_id=? AND review_status != 'pending'",
            (run_id,),
        ).fetchall()
    finally:
        conn.close()

    bundle = build_review_bundle(cfg, run_id)
    total_by_conv: dict[str, int] = {}
    for s in bundle["segments"]:
        total_by_conv[s["conversation_id"]] = total_by_conv.get(s["conversation_id"], 0) + 1

    by_conv: dict[str, list[dict]] = {}
    for seg_id, conv, _st, score, keep in rows:
        by_conv.setdefault(conv, []).append({"segment_id": seg_id, "score": score, "keep": keep})

    results: list[dict] = []
    for conv in sorted(by_conv):
        items = by_conv[conv]
        scores = [it["score"] for it in items if it["score"] is not None]
        keeps: dict[str, int] = {}
        for it in items:
            k = it["keep"] or "pending"
            keeps[k] = keeps.get(k, 0) + 1
        avg = round(sum(scores) / len(scores), 1) if scores else None
        lo = min(scores) if scores else None
        hi = max(scores) if scores else None
        if keeps.get("cleanup", 0) > 0:
            rec = "cleanup"
        elif keeps.get("pending", 0) > 0:
            rec = "pending"
        else:
            rec = "keep"
        results.append({
            "run_id": run_id,
            "conversation_id": conv,
            "segment_count": total_by_conv.get(conv, 0),
            "reviewed_count": len(items),
            "avg_value_score": avg,
            "min_value_score": lo,
            "max_value_score": hi,
            "keep_counts": keeps,
            "keep_recommendation": rec,
            "derived_note": "派生规则：cleanup>0→清理；否则 pending>0→待定；否则保留。仅基于已复核片段。",
        })

    conn = sqlite3.connect(cfg["paths"]["db"], timeout=30)
    try:
        ensure_v3_schema(conn)
        for r in results:
            upsert_final_judgment(conn, r)
        conn.commit()
    finally:
        conn.close()

    out_dir = Path(cfg["paths"]["runs_dir"]) / run_id / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "final_judgments.jsonl", "w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    return {
        "reviewed_segments": len(rows),
        "conversation_count": len(results),
        "conversations": results,
    }


# ─── 自包含复核界面（数据内嵌，无服务器） ──────────────────────────────────────

_REVIEW_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>复核 · 关系/预期/背景候选 → 价值判定 · __RUN_ID__</title>
<style>
  :root { --bg:#f6f7f9; --card:#fff; --line:#e2e5ea; --accent:#2f6fed; --ok:#1d9e6b; --warn:#c98a13; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:"Segoe UI","Microsoft YaHei",sans-serif; background:var(--bg); color:#1f2430; }
  header { position:sticky; top:0; background:#fff; border-bottom:1px solid var(--line); padding:10px 18px; z-index:5; }
  header h1 { font-size:16px; margin:0 0 8px; }
  .toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  button { border:1px solid var(--line); background:#fff; border-radius:6px; padding:6px 12px; cursor:pointer; font-size:13px; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
  .progress { display:flex; align-items:center; gap:10px; font-size:13px; color:#555; }
  .bar { width:220px; height:8px; background:#e8ebf0; border-radius:4px; overflow:hidden; }
  .bar > div { height:100%; background:var(--ok); }
  .filters { display:flex; gap:12px; margin-top:8px; flex-wrap:wrap; }
  .filters label { font-size:12px; color:#556; }
  main { padding:14px 18px; max-width:1080px; margin:0 auto; }
  .seg { background:var(--card); border:1px solid var(--line); border-radius:10px; margin:14px 0; padding:12px 14px; }
  .seg-head { display:flex; flex-wrap:wrap; gap:10px; align-items:center; border-bottom:1px solid var(--line); padding-bottom:8px; margin-bottom:10px; }
  .badge { font-size:12px; padding:2px 8px; border-radius:10px; background:#eef2fb; color:#33415c; }
  .st { font-size:12px; padding:2px 8px; border-radius:10px; }
  .st.pending { background:#eceef2; color:#556; }
  .st.confirmed { background:#e5f7ef; color:#1d6b4e; }
  .st.corrected { background:#fff3e0; color:#8a5a00; }
  .unit { border:1px dashed var(--line); border-radius:8px; padding:10px; margin:8px 0; background:#fbfcfe; }
  .unit h4 { margin:0 0 6px; font-size:13px; color:#445; }
  pre.evidence { background:#0f172a; color:#d8e0ee; font-size:12px; padding:10px; border-radius:8px; overflow:auto; white-space:pre-wrap; word-break:break-word; }
  .group { margin:10px 0; }
  .group h5 { margin:0 0 4px; font-size:12px; color:#667; }
  .item { border:1px solid var(--line); border-radius:8px; padding:8px; margin:6px 0; background:#fff; }
  .item .desc { font-size:13px; }
  .item .ev { font-size:11px; color:#889; font-family:Consolas,monospace; margin-top:2px; }
  .item .actions { display:flex; gap:12px; align-items:center; margin-top:6px; font-size:13px; }
  .item .actions label { display:flex; align-items:center; gap:4px; }
  .item textarea { width:100%; min-height:70px; font-family:Consolas,monospace; font-size:12px; margin-top:6px; border:1px solid var(--line); border-radius:6px; padding:6px; }
  .item.bad { border-color:#c9412f; }
  .badnote { color:#c9412f; font-size:12px; margin-top:4px; }
  .value-form { border-top:1px solid var(--line); margin-top:10px; padding-top:10px; display:flex; flex-wrap:wrap; gap:12px 18px; align-items:center; }
  .value-form label { font-size:13px; }
  .value-form .tags span { display:inline-flex; align-items:center; gap:4px; font-size:12px; margin-right:8px; }
  .value-form .keep label { display:inline-flex; align-items:center; gap:4px; margin-right:10px; font-size:13px; }
  .note { width:100%; }
  .note textarea { width:100%; min-height:44px; font-size:13px; border:1px solid var(--line); border-radius:6px; padding:6px; }
  .hint { font-size:12px; color:#889; }
</style>
</head>
<body>
<header>
  <h1>复核 · 候选关系/预期/背景判断 → 价值判定（运行 __RUN_ID__）</h1>
  <div class="toolbar">
    <button class="primary" onclick="exportFeedback()">导出 review_feedback.jsonl</button>
    <button onclick="showFeedbackText()">备用：查看/复制反馈文本</button>
    <label>导入继续：<input type="file" id="importFile" accept=".jsonl,.json" onchange="importFeedback(event)"></label>
    <button onclick="saveLocal()">保存到浏览器</button>
    <button onclick="clearLocal()">清除本地状态</button>
    <span class="progress"><span class="bar"><div id="barFill"></div></span><span id="progText"></span></span>
  </div>
  <div id="clipPanel" style="display:none;margin-top:8px;">
    <textarea id="clipText" rows="6" style="width:100%;font-family:Consolas,monospace;font-size:12px;" placeholder="反馈 JSONL 文本（已自动全选，Ctrl+C 或点下方按钮复制）"></textarea>
    <button onclick="copyClip()">复制到剪贴板</button>
  </div>
  <div class="filters">
    <label><input type="checkbox" id="fPending" checked onchange="render()">未复核</label>
    <label><input type="checkbox" id="fConfirmed" checked onchange="render()">已确认</label>
    <label><input type="checkbox" id="fCorrected" checked onchange="render()">已修正</label>
    <label><input type="checkbox" id="fCollapse" onchange="render()">折叠已复核</label>
  </div>
</header>
<main id="main"></main>
<script>
'use strict';
const DATA = __REVIEW_DATA__;
const VALUE_TAGS = ["亲情","友情","工作","生意","信息源","其他"];
const KEEP_OPTS = [["keep","保留"],["pending","待定"],["cleanup","清理"]];
const GROUPS = [["relationship_signals","关系信号"],["requests","请求"],["commitments","承诺"],["events","事件"],["entities","实体"],["memory_candidates","记忆候选"],["alternative_explanations","替代解释"]];
const ST_LABEL = {pending:"未复核", confirmed:"已确认", corrected:"已修正"};

function emptyState(){ return {review_status:"pending", corrections:{}, value_score:null, value_tags:[], keep_recommendation:"pending", note:""}; }
let state = {};
function initState(){ state = {}; for (const s of DATA.segments) state[s.segment_id] = emptyState(); }
function loadLocal(){ try { const raw = localStorage.getItem("review_"+DATA.run_id); if (raw) state = JSON.parse(raw); } catch(e){} }
function saveLocal(){ try { localStorage.setItem("review_"+DATA.run_id, JSON.stringify(state)); } catch(e){} }
let _saveTimer = null;
function scheduleSave(){ if (_saveTimer) clearTimeout(_saveTimer); _saveTimer = setTimeout(function(){ saveLocal(); }, 400); }
function clearLocal(){ try { localStorage.removeItem("review_"+DATA.run_id); } catch(e){} initState(); render(); }
function esc(x){ return String(x==null?"":x).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
initState(); loadLocal();

function findUnit(seg, unitKey){ for (let i=0;i<seg.units.length;i++) if (seg.units[i].unit_key===unitKey) return seg.units[i]; return null; }
function findSeg(segId){ for (let i=0;i<DATA.segments.length;i++) if (DATA.segments[i].segment_id===segId) return DATA.segments[i]; return null; }
function getCand(segId, unitKey, group, idx){
  const seg = findSeg(segId); if (!seg) return null;
  const u = findUnit(seg, unitKey); if (!u) return null;
  return (u.annotation[group] || [])[idx];
}
function corrOf(segId, unitKey, group, idx){
  const c = state[segId].corrections[unitKey] || {};
  return (c[group] || {})[idx] || {action:"accept", payload:null};
}
function segHasCorrection(segId){
  const c = state[segId].corrections;
  for (const uk in c) for (const g in c[uk]) for (const i in c[uk][g]) if (c[uk][g][i].action !== "accept") return true;
  return false;
}
function refreshStatus(segId){
  if (segHasCorrection(segId)) state[segId].review_status = "corrected";
  render();
}
function setStatus(segId, st){ state[segId].review_status = st; render(); }
function setAction(segId, unitKey, group, idx, action){
  const c = state[segId].corrections[unitKey] = state[segId].corrections[unitKey] || {};
  const g = c[group] = c[group] || {};
  const item = g[idx] = g[idx] || {action:"accept", payload:null};
  item.action = action;
  if (action === "correct" && !item.payload) {
    const orig = getCand(segId, unitKey, group, idx);
    item.payload = orig ? JSON.stringify(orig, null, 2) : "{}";
  }
  refreshStatus(segId);
}
function setPayload(segId, unitKey, group, idx, val){
  const c = state[segId].corrections[unitKey] = state[segId].corrections[unitKey] || {};
  const g = c[group] = c[group] || {};
  const item = g[idx] = g[idx] || {action:"correct", payload:null};
  item.action = "correct";
  item.payload = val;
  scheduleSave();
}
function onScore(segId, el){ const v = +el.value; state[segId].value_score = v; const b = document.getElementById("vs_"+segId); if (b) b.textContent = v; scheduleSave(); }
function toggleTag(segId, t){ const a = state[segId].value_tags; const i = a.indexOf(t); if (i>=0) a.splice(i,1); else a.push(t); scheduleSave(); }
function setKeep(segId, k){ state[segId].keep_recommendation = k; scheduleSave(); }
function setNote(segId, v){ state[segId].note = v; scheduleSave(); }

function problemList(){
  const bad = [];
  for (const s of DATA.segments){
    const c = state[s.segment_id].corrections;
    for (const uk in c) for (const g in c[uk]) for (const i in c[uk][g]) {
      const item = c[uk][g][i];
      if (item.action !== "correct") continue;
      const raw = (typeof item.payload === "string") ? item.payload : JSON.stringify(item.payload || {});
      try { JSON.parse(raw); } catch(e){ bad.push(s.segment_id+" · "+uk+" · "+g+"["+i+"]"); }
    }
  }
  return bad;
}

function buildFeedbackString(){
  const lines = [];
  for (const s of DATA.segments){
    const st = state[s.segment_id];
    const corrections = {};
    for (const uk in (st.corrections || {})){
      corrections[uk] = {};
      for (const g in st.corrections[uk]){
        corrections[uk][g] = {};
        for (const i in st.corrections[uk][g]){
          const item = st.corrections[uk][g][i];
          const out = {action:item.action, payload:null};
          if (item.action === "correct"){
            if (typeof item.payload === "string"){
              try { out.payload = JSON.parse(item.payload); }
              catch(e){ out.payload = item.payload; out.payload_error = true; }
            } else { out.payload = item.payload; }
          }
          corrections[uk][g][i] = out;
        }
      }
    }
    lines.push(JSON.stringify({
      run_id: DATA.run_id,
      segment_id: s.segment_id,
      conversation_id: s.conversation_id,
      message_count: s.message_count,
      unit_keys: s.units.map(function(u){ return u.unit_key; }),
      review_status: st.review_status,
      corrections: corrections,
      value_score: st.value_score,
      value_tags: st.value_tags,
      keep_recommendation: st.keep_recommendation,
      note: st.note,
      reviewed_at: st.review_status === "pending" ? null : new Date().toISOString()
    }));
  }
  return lines.join("\n");
}

function exportFeedback(){
  const bad = problemList();
  if (bad.length){
    const shown = bad.slice(0,5).join("\n") + (bad.length>5 ? "\n…（共 "+bad.length+" 处）" : "");
    if (!confirm("有 "+bad.length+" 处修正项的 JSON 无法解析：\n"+shown+"\n\n仍要导出吗？\n这些项会保留你填写的原文并标记 payload_error，可在导入后继续修。")) return;
  }
  const blob = new Blob([buildFeedbackString()], {type:"application/jsonl;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "review_feedback.jsonl";
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function showFeedbackText(){
  const bad = problemList();
  if (bad.length){
    const shown = bad.slice(0,5).join("\n") + (bad.length>5 ? "\n…（共 "+bad.length+" 处）" : "");
    if (!confirm("有 "+bad.length+" 处修正项的 JSON 无法解析：\n"+shown+"\n\n仍要复制吗？")) return;
  }
  const ta = document.getElementById("clipText");
  ta.value = buildFeedbackString();
  document.getElementById("clipPanel").style.display = "block";
  ta.focus(); ta.select();
  try { document.execCommand("copy"); } catch(e){}
}
function copyClip(){
  const ta = document.getElementById("clipText");
  ta.focus(); ta.select();
  try { if (document.execCommand("copy")) { alert("已复制到剪贴板"); return; } } catch(e){}
  alert("自动复制失败，请直接 Ctrl+C 复制文本框内容");
}

function importFeedback(ev){
  const f = ev.target.files && ev.target.files[0]; if (!f) return;
  const reader = new FileReader();
  reader.onload = function(){
    const lines = String(reader.result).split("\n");
    for (let i=0;i<lines.length;i++){
      const line = lines[i].trim(); if (!line) continue;
      try {
        const o = JSON.parse(line);
        if (!o.segment_id || !(o.segment_id in state)) continue;
        state[o.segment_id] = {
          review_status: o.review_status || "pending",
          corrections: o.corrections || {},
          value_score: (o.value_score != null) ? o.value_score : null,
          value_tags: o.value_tags || [],
          keep_recommendation: o.keep_recommendation || "pending",
          note: o.note || ""
        };
      } catch(e){}
    }
    render();
  };
  reader.readAsText(f);
}

function progress(){
  const total = DATA.segments.length;
  let reviewed = 0;
  for (const s of DATA.segments) if (state[s.segment_id].review_status !== "pending") reviewed++;
  const pct = total ? Math.round(reviewed/total*100) : 0;
  document.getElementById("barFill").style.width = pct + "%";
  document.getElementById("progText").textContent = reviewed + " / " + total + " 段已复核";
}

function candidateItem(segId, unitKey, g, idx, item){
  const c = corrOf(segId, unitKey, g, idx);
  const action = c.action;
  const desc = item.description || item.content || item.claim || JSON.stringify(item).slice(0,120);
  const ev = (item.evidence_ids && item.evidence_ids.length) ? item.evidence_ids.join(", ") : (item.evidence_id || "");
  let payloadBox = "";
  let badPayload = false;
  if (action === "correct") {
    const val = (typeof c.payload === "string") ? c.payload : JSON.stringify(item, null, 2);
    try { JSON.parse(val); } catch(e){ badPayload = true; }
    payloadBox = '<textarea onchange="setPayload(\''+segId+'\',\''+unitKey+'\',\''+g+'\','+idx+',this.value)">' + esc(val) + '</textarea>'
      + (badPayload ? '<div class="badnote">⚠ 此修正项 JSON 无法解析。可直接点「接受」或「拒绝」跳过，或修正此框内容。</div>' : '');
  }
  const conf = (item.confidence != null) ? ' <span class="hint">conf=' + item.confidence + '</span>' : "";
  return '<div class="item' + (badPayload ? ' bad' : '') + '">'
    + '<div class="desc">' + esc(desc) + conf + '</div>'
    + (ev ? '<div class="ev">' + esc(ev) + '</div>' : '')
    + '<div class="actions">'
    + '<label><input type="radio" name="c_'+segId+'_'+unitKey+'_'+g+'_'+idx+'" value="accept" ' + (action==="accept"?"checked":"") + ' onchange="setAction(\''+segId+'\',\''+unitKey+'\',\''+g+'\','+idx+',\'accept\')">接受</label>'
    + '<label><input type="radio" name="c_'+segId+'_'+unitKey+'_'+g+'_'+idx+'" value="correct" ' + (action==="correct"?"checked":"") + ' onchange="setAction(\''+segId+'\',\''+unitKey+'\',\''+g+'\','+idx+',\'correct\')">修正</label>'
    + '<label><input type="radio" name="c_'+segId+'_'+unitKey+'_'+g+'_'+idx+'" value="reject" ' + (action==="reject"?"checked":"") + ' onchange="setAction(\''+segId+'\',\''+unitKey+'\',\''+g+'\','+idx+',\'reject\')">拒绝</label>'
    + '</div>' + payloadBox + '</div>';
}

function unitBlock(segId, u){
  let html = '<div class="unit"><h4>窗口 ' + u.window_idx + ' · ' + u.message_count + ' 条 · ' + esc(u.unit_key) + '</h4>';
  html += '<pre class="evidence">' + u.evidence_lines.map(esc).join("\n") + '</pre>';
  for (let gi=0; gi<GROUPS.length; gi++){
    const g = GROUPS[gi][0], label = GROUPS[gi][1];
    const items = (u.annotation[g] || []);
    if (!items.length) continue;
    html += '<div class="group"><h5>' + label + '</h5>';
    for (let idx=0; idx<items.length; idx++) html += candidateItem(segId, u.unit_key, g, idx, items[idx]);
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function segmentCard(s, st, collapsed){
  const stCls = st.review_status;
  const unitsHtml = collapsed
    ? '<p class="hint">已折叠（取消“折叠已复核”可展开）</p>'
    : s.units.map(function(u){ return unitBlock(s.segment_id, u); }).join("");
  const vs = (st.value_score != null) ? st.value_score : "";
  const tags = VALUE_TAGS.map(function(t){
    return '<span><label><input type="checkbox" ' + (st.value_tags.indexOf(t)>=0?"checked":"") + ' onchange="toggleTag(\''+s.segment_id+'\',\''+t+'\')">' + t + '</label></span>';
  }).join("");
  const keep = KEEP_OPTS.map(function(k){
    return '<label><input type="radio" name="keep_'+s.segment_id+'" value="'+k[0]+'" ' + (st.keep_recommendation===k[0]?"checked":"") + ' onchange="setKeep(\''+s.segment_id+'\',\''+k[0]+'\')">' + k[1] + '</label>';
  }).join("");
  return '<section class="seg">'
    + '<div class="seg-head">'
    + '<span class="badge">' + s.bucket + '桶 · ' + s.message_count + '条</span>'
    + '<span class="badge">段 ' + esc(s.segment_id.slice(0,16)) + '…</span>'
    + '<span class="badge">会话 ' + esc(s.conversation_id.slice(0,12)) + '…</span>'
    + '<span class="st ' + stCls + '">' + ST_LABEL[stCls] + '</span>'
    + '</div>'
    + unitsHtml
    + '<div class="value-form">'
    + '<label>价值 <input type="range" min="0" max="100" step="1" value="' + ((st.value_score!=null)?st.value_score:50) + '" oninput="onScore(\''+s.segment_id+'\',this)"><b id="vs_'+s.segment_id+'">' + vs + '</b></label>'
    + '<span class="tags">' + tags + '</span>'
    + '<span class="keep">' + keep + '</span>'
    + '<button class="primary" onclick="setStatus(\''+s.segment_id+'\',\'confirmed\')">✔ 确认本段</button>'
    + '<button onclick="setStatus(\''+s.segment_id+'\',\'pending\')">↺ 待定</button>'
    + '<div class="note"><textarea placeholder="备注（价值依据 / 修正说明）" onchange="setNote(\''+s.segment_id+'\',this.value)">' + esc(st.note) + '</textarea></div>'
    + '</div>'
    + '</section>';
}

function render(){
  const showPending = document.getElementById("fPending").checked;
  const showConfirmed = document.getElementById("fConfirmed").checked;
  const showCorrected = document.getElementById("fCorrected").checked;
  const collapse = document.getElementById("fCollapse").checked;
  let html = "";
  for (const s of DATA.segments){
    const st = state[s.segment_id];
    if (st.review_status === "pending" && !showPending) continue;
    if (st.review_status === "confirmed" && !showConfirmed) continue;
    if (st.review_status === "corrected" && !showCorrected) continue;
    html += segmentCard(s, st, collapse && st.review_status !== "pending");
  }
  document.getElementById("main").innerHTML = html;
  progress();
  scheduleSave();
}
window.addEventListener("beforeunload", saveLocal);
render();
</script>
</body>
</html>
"""
