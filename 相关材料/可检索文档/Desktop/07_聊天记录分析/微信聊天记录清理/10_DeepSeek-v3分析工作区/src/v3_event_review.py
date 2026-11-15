"""v3 事件中心 · 人机协作复核：event_review.html 静态复核页 + 反馈落库 + 最终事件判断。

全程 0 API：
- render_event_review_html：把事件候选包内嵌成自包含 HTML（双击打开，导出 event_review_feedback.jsonl）；
- load_event_feedback：读取并校验复核反馈；
- apply_event_feedback：写 _v3_event_review（候选级：确认/改名/调时间/合并拆分/角色/事实推测/期待/价值）；
- aggregate_event_judgments：按确认后的候选/合并/拆分产物写 _v3_event_judgments。

运行：
  python -m src.v3_event_review render  runs/event_review_p1/event_review_bundle.json --outdir runs/event_review_p1
  python -m src.v3_event_review finalize runs/event_review_p1/event_review_feedback.jsonl --db data/wechat-analysis-v3.sqlite3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .v3_events import ensure_event_schema
from .v3_io import utc_now, write_json_atomic

VALUE_TAGS: tuple[str, ...] = ("亲情", "友情", "工作", "生意", "信息源", "其他")
KEEP_OPTIONS: tuple[tuple[str, str], ...] = (("keep", "保留"), ("pending", "待定"), ("cleanup", "清理"))
REVIEW_STATUSES: tuple[str, ...] = ("pending", "confirmed", "corrected", "merged", "split", "rejected")
CERTAINTY_OPTIONS: tuple[tuple[str, str], ...] = (("fact", "事实"), ("inferred", "推测"), ("unknown", "未知"))

#: 低负担复核：用户主要操作（DEEP-REVIEW-SPEC 改动二）
USER_VERDICTS: tuple[tuple[str, str], ...] = (
    ("confirmed", "确认"), ("partial", "部分正确"), ("incorrect", "错误"), ("rejected", "拒绝"),
)


def render_event_review_html(bundle: dict, out_dir: Path) -> Path:
    """把候选包内嵌进自包含 event_review.html，返回 HTML 路径。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_dir / "event_review_bundle.json", bundle)
    run_id = bundle.get("run_id") or bundle.get("generated_at", "event")
    data_json = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
    html = (
        _EVENT_REVIEW_HTML_TEMPLATE
        .replace("__EVENT_DATA__", data_json)
        .replace("__RUN_ID__", run_id)
    )
    out_html = out_dir / "event_review.html"
    out_html.write_text(html, encoding="utf-8")
    return out_html


# ─── 反馈读取与落库 ───────────────────────────────────────────────────────────

def load_event_feedback(path: Path) -> list[dict]:
    """读取复核界面导出的 event_review_feedback.jsonl 并校验结构。"""
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
            cid = obj.get("candidate_id")
            if not isinstance(cid, str) or not cid:
                problems.append(f"第{lineno}行缺少 candidate_id")
                continue
            st = obj.get("review_status", "pending")
            if st not in REVIEW_STATUSES:
                problems.append(f"第{lineno}行 review_status 非法: {st!r}")
                continue
            uv = obj.get("user_verdict")
            if uv is not None and uv not in dict(USER_VERDICTS):
                problems.append(f"第{lineno}行 user_verdict 非法: {uv!r}")
                continue
            if obj.get("value_score") is not None and not isinstance(obj.get("value_score"), (int, float)):
                problems.append(f"第{lineno}行 value_score 非数值")
                continue
            keep = obj.get("keep_recommendation")
            if keep is not None and keep not in dict(KEEP_OPTIONS):
                problems.append(f"第{lineno}行 keep_recommendation 非法: {keep!r}")
                continue
            corr = obj.get("user_correction")
            if corr is not None and not isinstance(corr, dict):
                problems.append(f"第{lineno}行 user_correction 非对象")
                continue
            out.append(obj)
    if problems:
        raise ValueError("反馈文件校验失败：\n" + "\n".join(problems[:20]))
    return out


def apply_event_feedback(db: str, feedback: list[dict]) -> int:
    """把反馈逐行 upsert 进 _v3_event_review。返回写入行数。"""
    conn = sqlite3.connect(db, timeout=30)
    try:
        ensure_event_schema(conn)
        now = utc_now()
        for row in feedback:
            conn.execute(
                """
                INSERT INTO _v3_event_review(
                  candidate_id, review_status, user_verdict, user_correction_json,
                  model_guess_json, title_override, start_ts, end_ts,
                  time_certainty, fact_status, roles_json, merge_into, split_parts_json,
                  expectation, value_score, value_tags, note, reviewed_at, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(candidate_id) DO UPDATE SET
                  review_status=excluded.review_status, user_verdict=excluded.user_verdict,
                  user_correction_json=excluded.user_correction_json,
                  model_guess_json=excluded.model_guess_json,
                  title_override=excluded.title_override,
                  start_ts=excluded.start_ts, end_ts=excluded.end_ts,
                  time_certainty=excluded.time_certainty, fact_status=excluded.fact_status,
                  roles_json=excluded.roles_json, merge_into=excluded.merge_into,
                  split_parts_json=excluded.split_parts_json, expectation=excluded.expectation,
                  value_score=excluded.value_score, value_tags=excluded.value_tags,
                  note=excluded.note, reviewed_at=excluded.reviewed_at
                """,
                (
                    row["candidate_id"], row.get("review_status", "pending"),
                    row.get("user_verdict"),
                    json.dumps(row.get("user_correction") or {}, ensure_ascii=False),
                    json.dumps(row.get("model_guess") or {}, ensure_ascii=False),
                    row.get("title_override"),
                    _opt_int(row.get("start_ts")), _opt_int(row.get("end_ts")),
                    row.get("time_certainty"), row.get("fact_status"),
                    json.dumps(row.get("roles") or {}, ensure_ascii=False),
                    row.get("merge_into"),
                    json.dumps(row.get("split_parts") or [], ensure_ascii=False),
                    row.get("expectation"),
                    _opt_int(row.get("value_score")),
                    json.dumps(row.get("value_tags") or [], ensure_ascii=False),
                    row.get("note"),
                    row.get("reviewed_at") or now, now,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return len(feedback)


def _opt_int(v: Any) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def aggregate_event_judgments(db: str, bundle_path: Path, feedback: list[dict]) -> dict:
    """把已复核候选聚合为最终事件判断（_v3_event_judgments）。

    规则（保守）：
    - 已确认/已修正且未合并未拆分 → 一个事件（title 用 title_override 或原标题）。
    - merge_into 指定 → 归入目标事件（source_candidate_ids 累积）。
    - split_parts 非空 → 每个拆分部件一个事件。
    - rejected / pending → 不落最终判断。
    """
    bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    cand_by_id = {c["candidate_id"]: c for c in bundle.get("candidates", [])}

    final: list[dict] = []
    merged_sources: dict[str, list[str]] = {}
    for row in feedback:
        cid = row["candidate_id"]
        st = row.get("review_status", "pending")
        cand = cand_by_id.get(cid, {})
        target = row.get("merge_into")
        if target:
            merged_sources.setdefault(target, []).append(cid)
        if st in ("pending", "rejected", "merged"):
            continue
        if row.get("split_parts"):
            for idx, part in enumerate(row["split_parts"]):
                if not isinstance(part, dict) or not part.get("name"):
                    continue
                final.append(_judgment_row(
                    _split_event_id(cid, idx), cand, row, part["name"], part.get("note", ""),
                ))
            continue
        title = row.get("title_override") or cand.get("title") or cid
        final.append(_judgment_row(cid, cand, row, title, ""))

    # 归并 merge 来源到目标
    for ev in final:
        ev["source_candidate_ids"] = sorted(set([ev["event_id"]] + merged_sources.get(ev["event_id"], [])))

    conn = sqlite3.connect(db, timeout=30)
    try:
        ensure_event_schema(conn)
        now = utc_now()
        for ev in final:
            conn.execute(
                """
                INSERT INTO _v3_event_judgments(
                  event_id, source_candidate_ids, title, start_ts, end_ts,
                  time_certainty, fact_status, roles_json, expectation,
                  value_score, value_tags, keep_recommendation, note, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(event_id) DO UPDATE SET
                  source_candidate_ids=excluded.source_candidate_ids, title=excluded.title,
                  start_ts=excluded.start_ts, end_ts=excluded.end_ts,
                  time_certainty=excluded.time_certainty, fact_status=excluded.fact_status,
                  roles_json=excluded.roles_json, expectation=excluded.expectation,
                  value_score=excluded.value_score, value_tags=excluded.value_tags,
                  keep_recommendation=excluded.keep_recommendation, note=excluded.note
                """,
                (
                    ev["event_id"], json.dumps(ev["source_candidate_ids"], ensure_ascii=False),
                    ev["title"], _opt_int(ev.get("start_ts")), _opt_int(ev.get("end_ts")),
                    ev.get("time_certainty"), ev.get("fact_status"),
                    json.dumps(ev.get("roles") or {}, ensure_ascii=False),
                    ev.get("expectation"), _opt_int(ev.get("value_score")),
                    json.dumps(ev.get("value_tags") or [], ensure_ascii=False),
                    ev.get("keep_recommendation"), ev.get("note"), now,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    # 同时导出 JSONL 便于核查
    out_dir = Path(bundle_path).parent
    with open(out_dir / "event_final_judgments.jsonl", "w", encoding="utf-8") as fh:
        for ev in final:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

    return {
        "finalized_events": len(final),
        "merged_sources": sum(len(v) for v in merged_sources.values()),
        "pending_or_rejected": sum(1 for r in feedback if r.get("review_status") in ("pending", "rejected")),
        "output": str(out_dir / "event_final_judgments.jsonl"),
    }


def _judgment_row(event_id: str, cand: dict, row: dict, title: str, note: str) -> dict:
    return {
        "event_id": event_id,
        "source_candidate_ids": [event_id],
        "title": title,
        "start_ts": row.get("start_ts") or cand.get("start_ts"),
        "end_ts": row.get("end_ts") or cand.get("end_ts"),
        "time_certainty": row.get("time_certainty") or cand.get("time_certainty", "unknown"),
        "fact_status": row.get("fact_status") or "unknown",
        "roles": row.get("roles") or {},
        "expectation": row.get("expectation"),
        "value_score": row.get("value_score"),
        "value_tags": row.get("value_tags") or [],
        "keep_recommendation": row.get("keep_recommendation") or "pending",
        "note": note or row.get("note"),
    }


def _split_event_id(cid: str, idx: int) -> str:
    h = hashlib.sha256(f"{cid}|split|{idx}".encode("utf-8")).hexdigest()[:16]
    return "evs_" + h


# ─── 自包含低负担复核界面（首屏预填档案，数据内嵌，无服务器） ──────────────────

# 模板说明（DEEP-REVIEW-SPEC 改动二）：
# - 每张卡首屏展示预填判断档案：facts（事实/置信度/证据回链）、analysis_status 横幅、
#   深度分析槽位（deep_hypotheses / alternative_hypotheses / counter_evidence /
#   relationship_profile / value_assumptions / communication_advice）与结论稳定性。
# - 主要操作为 确认/部分正确/错误/拒绝、合并/拆分、一句真实背景补充（note）。
# - 用户修正以 {field: {guess, corrected, reason}} 结构记录，与原模型猜测并存；
#   model_guess 快照随反馈一起导出，供幂等重导落库。
# - 数据经 __EVENT_DATA__ 内嵌；导出 event_review_feedback.jsonl；localStorage 自动保存。

_EVENT_REVIEW_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>事件复核 · 深度预填档案确认 · __RUN_ID__</title>
<style>
  :root { --bg:#f6f7f9; --card:#fff; --line:#e2e5ea; --accent:#2f6fed; --ok:#1d9e6b;
          --warn:#c98a13; --bad:#c9412f; --muted:#667; --amber-bg:#fff7e0; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:"Segoe UI","Microsoft YaHei",sans-serif; background:var(--bg); color:#1f2430; }
  header { position:sticky; top:0; background:#fff; border-bottom:1px solid var(--line); padding:10px 18px; z-index:5; }
  header h1 { font-size:16px; margin:0 0 8px; }
  .toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  button { border:1px solid var(--line); background:#fff; border-radius:6px; padding:6px 12px; cursor:pointer; font-size:13px; }
  button.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
  button.warn { border-color:var(--warn); color:#8a5a00; }
  .progress { display:flex; align-items:center; gap:10px; font-size:13px; color:#555; }
  .bar { width:200px; height:8px; background:#e8ebf0; border-radius:4px; overflow:hidden; }
  .bar > div { height:100%; background:var(--ok); }
  .filters { display:flex; gap:12px; margin-top:8px; flex-wrap:wrap; font-size:12px; color:#556; }
  main { padding:14px 18px; max-width:1120px; margin:0 auto; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; margin:16px 0; padding:12px 14px; }
  .card-head { display:flex; flex-wrap:wrap; gap:8px; align-items:center; border-bottom:1px solid var(--line); padding-bottom:8px; margin-bottom:10px; }
  .card-head input.title { flex:1 1 340px; font-size:14px; font-weight:600; border:1px solid var(--line); border-radius:6px; padding:4px 8px; }
  .badge { font-size:12px; padding:2px 8px; border-radius:10px; background:#eef2fb; color:#33415c; }
  .st { font-size:12px; padding:2px 8px; border-radius:10px; }
  .st.pending { background:#eceef2; color:#556; }
  .st.confirmed { background:#e5f7ef; color:#1d6b4e; }
  .st.partial { background:#fff3e0; color:#8a5a00; }
  .st.incorrect, .st.rejected { background:#fdecea; color:#a03a2a; }
  .st.tentative { background:var(--amber-bg); color:#8a5a00; }
  .st.stable { background:#e5f7ef; color:#1d6b4e; }
  .st.fact { background:#e5f7ef; color:#1d6b4e; }
  .st.inferred { background:#fff3e0; color:#8a5a00; }
  .st.unknown { background:#eceef2; color:#556; }
  .banner { background:var(--amber-bg); border:1px solid #ecd9a8; border-radius:8px; padding:8px 10px; font-size:12px; color:#6b4a00; margin:8px 0; }
  .banner.ok { background:#e5f7ef; border-color:#bfe3d2; color:#1d6b4e; }
  .facts { margin:8px 0; }
  .fact-row { display:flex; gap:8px; align-items:flex-start; border:1px solid var(--line); border-radius:8px; padding:7px 9px; margin:6px 0; background:#fbfcfe; font-size:13px; }
  .fact-row .txt { flex:1; }
  .fact-row .ev { font-size:11px; color:#889; font-family:Consolas,monospace; margin-top:2px; word-break:break-all; }
  .slots { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:10px; margin:10px 0; }
  .slot { border:1px dashed #c9d2e0; border-radius:8px; padding:8px 10px; background:#fbfcfe; font-size:12px; }
  .slot h5 { margin:0 0 4px; font-size:12px; color:var(--accent); }
  .slot .empty { color:#99a; font-style:italic; }
  .meta { display:flex; flex-wrap:wrap; gap:6px 14px; font-size:12px; color:var(--muted); margin:6px 0; }
  .meta b { color:#445; }
  .verdicts { display:flex; gap:8px; align-items:center; margin:10px 0; flex-wrap:wrap; }
  .verdicts label { display:inline-flex; align-items:center; gap:4px; font-size:13px; border:1px solid var(--line); border-radius:6px; padding:5px 10px; cursor:pointer; background:#fff; }
  .verdicts label.sel { border-color:var(--accent); background:#eef4ff; }
  .verdicts input { accent-color:var(--accent); }
  .corr-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:10px; margin:10px 0; }
  .field { border:1px solid var(--line); border-radius:8px; padding:8px 10px; background:#fff; }
  .field label { display:block; font-size:12px; color:#556; margin-bottom:4px; }
  .field .guess { font-size:11px; color:#889; background:#f4f6fa; border-radius:4px; padding:3px 6px; margin-bottom:4px; white-space:pre-wrap; word-break:break-word; }
  .field textarea, .field input { width:100%; font-size:13px; border:1px solid var(--line); border-radius:6px; padding:5px 7px; font-family:inherit; }
  .field textarea { min-height:52px; }
  .note textarea { width:100%; min-height:48px; font-size:13px; border:1px solid var(--line); border-radius:6px; padding:6px; }
  .evidence { margin:10px 0; }
  details.ev-detail { border:1px solid var(--line); border-radius:8px; background:#0f172a; }
  details.ev-detail summary { padding:8px 10px; cursor:pointer; color:#b8c4d8; font-size:13px; }
  pre.evidence { margin:0; color:#d8e0ee; font-size:12px; padding:0 10px 10px; overflow:auto; white-space:pre-wrap; word-break:break-word; }
  .hint { font-size:12px; color:#889; }
  .foot { text-align:center; color:#99a; font-size:12px; padding:16px; }
</style>
</head>
<body>
<header>
  <h1>事件复核 · 深度预填档案确认 · <span id="runId"></span></h1>
  <div class="toolbar">
    <span class="progress">已复核 <b id="doneN">0</b> / <b id="totalN">0</b>
      <span class="bar"><div id="barFill"></div></span></span>
    <button id="btnSave" class="primary">保存到本地</button>
    <button id="btnExport">导出反馈 JSONL</button>
    <button id="btnImport">重导反馈</button>
    <input type="file" id="fileImport" accept=".jsonl,.json" style="display:none">
  </div>
  <div class="filters">
    快速跳转：
    <span id="jumpList"></span>
  </div>
</header>
<main id="cards"></main>
<div class="foot">数据仅存本机：localStorage 自动保存；「导出反馈 JSONL」生成 event_review_feedback.jsonl 供落库。
预填档案为无 API 阶段确定性证据 + 深度分析槽位；模型级深度推理未执行。</div>

<script>
"use strict";
const DATA = __EVENT_DATA__;
const RUN_ID = "__RUN_ID__";
const VERDICT_LABEL = {"confirmed":"确认","partial":"部分正确","incorrect":"错误","rejected":"拒绝"};
const LS_KEY = "v3_event_review_" + RUN_ID;

let state = {};
function loadState() { try { state = JSON.parse(localStorage.getItem(LS_KEY) || "{}"); } catch(e) { state = {}; } }
function saveState() {
  localStorage.setItem(LS_KEY, JSON.stringify(state));
  renderProgress();
}
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

// ── 反馈结构：每个字段记录 {guess, corrected, reason}，模型猜测与用户修正并存 ──
function correctionFor(cid, field, guess) {
  let obj = (state[cid] && state[cid].corrections && state[cid].corrections[field]) || {};
  return { guess: guess == null ? "" : String(guess), corrected: obj.corrected || "", reason: obj.reason || "" };
}

function buildFeedback() {
  const lines = [];
  for (const c of DATA.candidates) {
    const cid = c.candidate_id;
    const s = state[cid] || {};
    const profile = c.analysis_profile || {};
    const verdict = s.verdict || "pending";
    const corrections = {};
    // 标题
    corrections.title = correctionFor(cid, "title", c.title);
    // 期望（用户自己的期待）
    corrections.expectation = correctionFor(cid, "expectation", "");
    // 关系定位（每个联系人一行，guess 来自角色槽位提示）
    const rolesGuess = {};
    (c.conversations || []).forEach(conv => { rolesGuess[conv.conversation_id] = conv.display_name; });
    corrections.roles = correctionFor(cid, "roles", JSON.stringify(rolesGuess));
    // 价值/建议（槽位，guess 为空）
    corrections.value_assumptions = correctionFor(cid, "value_assumptions", "");
    corrections.communication_advice = correctionFor(cid, "communication_advice", "");
    // 一句真实背景补充
    corrections.note = correctionFor(cid, "note", "");

    const line = {
      candidate_id: cid,
      run_id: RUN_ID,
      user_verdict: verdict,
      review_status: (verdict === "confirmed" ? "confirmed" : (verdict === "partial" ? "corrected" : verdict)),
      user_correction: corrections,
      model_guess: profile,               // 原模型猜测快照并存
      title_override: (s.title || ""),
      start_ts: c.start_ts, end_ts: c.end_ts,
      time_certainty: c.time_certainty || "unknown",
      fact_status: c.fact_status || "unknown",
      roles: (s.roles || {}),
      merge_into: (s.merge_into || ""),
      split_parts: (s.split_parts || []),
      expectation: (s.expectation || ""),
      value_score: (s.value_score == null ? null : Number(s.value_score)),
      value_tags: (s.value_tags || []),
      keep_recommendation: (s.keep_recommendation || "pending"),
      note: (s.note || ""),
      reviewed_at: (s.reviewed_at || new Date().toISOString()),
    };
    lines.push(line);
  }
  return lines;
}

function roleCorrection(cid, convId) {
  const s = state[cid] || {};
  const corr = (s.corrections && s.corrections["role_" + convId]) || {};
  return corr.corrected || "";
}

function renderCard(c, idx) {
  const cid = c.candidate_id;
  const s = state[cid] || {};
  const verdict = s.verdict || "pending";
  const profile = c.analysis_profile || {};
  const stability = profile.conclusion_stability || {status:"tentative", required:3, supporting_events:0};
  const as = profile.analysis_status || "retrieval_ready";
  const facts = profile.facts || [];

  const verdictBtns = ["confirmed","partial","incorrect","rejected"].map(v =>
    `<label class="${verdict===v?"sel":""}"><input type="radio" name="v_${cid}" value="${v}" ${verdict===v?"checked":""} onchange="setVerdict('${cid}','${v}')">${VERDICT_LABEL[v]}</label>`
  ).join("");

  const factHtml = facts.map(f => {
    const st = (f.status || "unknown");
    const conf = f.confidence == null ? "—" : Math.round(f.confidence*100)+"%";
    const evs = (f.evidence_ids || []).join("  ");
    return `<div class="fact-row"><span class="st ${st}">${st} ${conf}</span><div class="txt">${esc(f.statement)}
      <div class="ev">证据: ${esc(evs)}</div></div></div>`;
  }).join("");

  const slot = (key, label, emptyText) => {
    const arr = profile[key];
    const isEmpty = !arr || (Array.isArray(arr) && arr.length === 0) || arr == null;
    let body;
    if (isEmpty) {
      body = `<div class="empty">${emptyText}</div>`;
    } else if (typeof arr === "string") {
      body = `<div>${esc(arr)}</div>`;
    } else {
      body = `<div>${esc(JSON.stringify(arr))}</div>`;
    }
    return `<div class="slot"><h5>${label}</h5>${body}</div>`;
  };

  const convMeta = (c.conversations || []).map(conv => `${esc(conv.display_name || conv.conversation_id)}×${conv.message_count}`).join("、");
  const evLines = (c.evidence || []).map(e => `[${e.evidence_id}] ${e.quote} (${e.signal_types.join("+")})`).join("\n");

  const rolesFields = (c.conversations || []).map(conv => {
    const cid2 = conv.conversation_id;
    const guess = conv.display_name || cid2;
    const corrVal = roleCorrection(cid, cid2);
    return `<div class="field"><label>角色 · ${esc(guess)}</label>
      <div class="guess">模型猜测（预填角色提示）：${esc(guess)}</div>
      <textarea data-cid="${cid}" data-field="role_${cid2}" data-guess="${esc(guess)}" placeholder="用户修正角色（留空=接受）">${esc(corrVal)}</textarea></div>`;
  }).join("");

  const card = document.createElement("div");
  card.className = "card";
  card.id = "card_" + cid;
  card.innerHTML = `
    <div class="card-head">
      <span class="badge">${idx+1}</span>
      <input class="title" value="${esc(s.title || c.title)}" data-cid="${cid}" data-field="title"
             onchange="setField('${cid}','title',this.value)" title="改名（用户修正）">
      <span class="st ${as === 'retrieval_ready' ? 'inferred' : (as==='pending_deep_analysis'?'pending':'stable')}">${as === 'retrieval_ready' ? '待深度分析' : (as==='pending_deep_analysis'?'已入队':'已分析')}</span>
      <span class="st ${verdict}">${verdict==='pending'?'未复核':VERDICT_LABEL[verdict]}</span>
      <span class="st ${stability.status}">${stability.status==='tentative'?'暂定假设':'稳定'}</span>
    </div>
    ${as !== 'analyzed' ? `<div class="banner">无 API 阶段：预填档案仅含确定性证据包与推断/反证槽位；模型级深度推理未执行
      （analysis_status=${esc(as)}）。深度分析须另行确认 token 预算。</div>` : `<div class="banner ok">深度分析已完成（analysis_status=analyzed）。</div>`}
    <div class="meta">
      <span>类别 <b>${esc(c.category || "")}</b></span>
      <span>时间 <b>${esc(new Date(c.start_ts*1000).toLocaleString())} ~ ${esc(new Date(c.end_ts*1000).toLocaleString())}</b></span>
      <span>时间确定性 <b>${esc(c.time_certainty || "unknown")}</b></span>
      <span>联系人 <b>${esc(convMeta)}</b></span>
      <span>实体 <b>${esc((c.strong_entities||[]).join("、"))}</b></span>
      <span>线索 <b>${esc((c.task_categories||[]).join("、"))}</b></span>
      <span>签名分数 <b>${esc(c.signal_score)}</b></span>
    </div>
    <div class="facts">${factHtml || '<div class="hint">（无确定性事实可生成）</div>'}</div>
    <div class="slots">
      ${slot("deep_hypotheses","深度假设(发生了什么/目的)","待深度分析阶段填充")}
      ${slot("alternative_hypotheses","备选解释","待深度分析阶段填充")}
      ${slot("counter_evidence","反证","反证槽位：待深度分析阶段填充（槽位已保留）")}
      ${slot("relationship_profile","关系档案","待深度分析阶段填充")}
      ${slot("value_assumptions","价值假设","待深度分析阶段填充")}
      ${slot("communication_advice","沟通建议","待深度分析阶段填充")}
    </div>
    <div class="verdicts">${verdictBtns}</div>
    <div class="corr-grid">
      <div class="field"><label>用户期望（我在这件事里的期待）</label>
        <div class="guess">模型猜测：槽位未填充</div>
        <textarea data-cid="${cid}" data-field="expectation" onchange="setField('${cid}','expectation',this.value)">${esc(s.expectation || "")}</textarea></div>
      ${rolesFields}
      <div class="field"><label>价值假设修正</label>
        <div class="guess">模型猜测：槽位未填充</div>
        <textarea data-cid="${cid}" data-field="value_assumptions" onchange="setField('${cid}','value_assumptions',this.value)">${esc((s.corrections||{}).value_assumptions ? (s.corrections.value_assumptions.corrected||"") : "")}</textarea></div>
      <div class="field"><label>沟通建议修正</label>
        <div class="guess">模型猜测：槽位未填充</div>
        <textarea data-cid="${cid}" data-field="communication_advice" onchange="setField('${cid}','communication_advice',this.value)">${esc((s.corrections||{}).communication_advice ? (s.corrections.communication_advice.corrected||"") : "")}</textarea></div>
      <div class="field"><label>价值分 0-100</label>
        <input type="number" min="0" max="100" value="${s.value_score == null ? "" : s.value_score}" data-cid="${cid}" data-field="value_score" onchange="setField('${cid}','value_score',this.value)"></div>
      <div class="field"><label>保留建议</label>
        <select data-cid="${cid}" data-field="keep" onchange="setField('${cid}','keep',this.value)">
          <option value="pending" ${s.keep_recommendation==="pending"?"selected":""}>待定</option>
          <option value="keep" ${s.keep_recommendation==="keep"?"selected":""}>保留</option>
          <option value="cleanup" ${s.keep_recommendation==="cleanup"?"selected":""}>清理</option>
        </select></div>
      <div class="field"><label>合并到（candidate_id，留空=不合并）</label>
        <input value="${esc(s.merge_into || "")}" data-cid="${cid}" data-field="merge_into" onchange="setField('${cid}','merge_into',this.value)" placeholder="evc_..."></div>
      <div class="field"><label>拆分为 JSON（[{name,evidence_note}]）</label>
        <textarea data-cid="${cid}" data-field="split_parts" onchange="setField('${cid}','split_parts',this.value)">${esc(JSON.stringify(s.split_parts || []))}</textarea></div>
    </div>
    <div class="note"><label><b>一句真实背景补充</b>（用户修正的重点；与原模型猜测并存）</label>
      <textarea data-cid="${cid}" data-field="note" onchange="setField('${cid}','note',this.value)">${esc(s.note || "")}</textarea></div>
    <details class="ev-detail"><summary>证据包（${(c.evidence||[]).length} 条）</summary>
      <pre class="evidence">${esc(evLines)}</pre></details>
  `;
  // 角色 textarea 用单独的绑定（避免模板里拼 data-field 冲突）
  card.querySelectorAll("textarea[data-field^='role_']").forEach(ta => {
    ta.onchange = () => setRoleField(cid, ta.dataset.field, ta.value, ta.dataset.guess);
  });
  return card;
}

function render() {
  const main = document.getElementById("cards");
  main.innerHTML = "";
  (DATA.candidates || []).forEach((c, i) => main.appendChild(renderCard(c, i)));
  document.getElementById("runId").textContent = RUN_ID;
  document.getElementById("totalN").textContent = DATA.candidates.length;
  const jump = (DATA.candidates || []).map((c, i) =>
    `<a href="#card_${c.candidate_id}" style="margin-right:8px;color:var(--accent)">${i+1}</a>`).join("");
  document.getElementById("jumpList").innerHTML = jump;
  renderProgress();
}

function renderProgress() {
  const total = DATA.candidates.length;
  const done = (DATA.candidates || []).filter(c => state[c.candidate_id] && state[c.candidate_id].verdict && state[c.candidate_id].verdict !== "pending").length;
  document.getElementById("doneN").textContent = done;
  document.getElementById("barFill").style.width = total ? (done/total*100).toFixed(0)+"%" : "0%";
}

function setVerdict(cid, v) {
  state[cid] = state[cid] || {};
  state[cid].verdict = v;
  state[cid].reviewed_at = new Date().toISOString();
  saveState();
  const card = document.getElementById("card_" + cid);
  const b = card.querySelectorAll(".verdicts label");
  b.forEach(l => l.classList.toggle("sel", l.querySelector("input").value === v));
  const st = card.querySelector(".card-head .st[class*='confirmed'], .card-head .st[class*='partial'], .card-head .st[class*='incorrect'], .card-head .st[class*='rejected'], .card-head .st.pending");
  if (st) { st.className = "st " + v; st.textContent = v === "pending" ? "未复核" : VERDICT_LABEL[v]; }
}

function setField(cid, field, val) {
  state[cid] = state[cid] || {};
  if (field === "title") { state[cid].title = val; }
  else if (field === "expectation") { state[cid].expectation = val; }
  else if (field === "value_score") { state[cid].value_score = val === "" ? null : Number(val); }
  else if (field === "keep") { state[cid].keep_recommendation = val; }
  else if (field === "merge_into") { state[cid].merge_into = val; }
  else if (field === "split_parts") {
    try { state[cid].split_parts = JSON.parse(val || "[]"); } catch(e) { state[cid].split_parts = []; }
  }
  else if (field === "note") { state[cid].note = val; }
  else if (field === "value_assumptions" || field === "communication_advice") {
    state[cid].corrections = state[cid].corrections || {};
    state[cid].corrections[field] = { guess: "", corrected: val, reason: "" };
  }
  state[cid].reviewed_at = new Date().toISOString();
  saveState();
}

function setRoleField(cid, field, val, guess) {
  state[cid] = state[cid] || {};
  state[cid].corrections = state[cid].corrections || {};
  state[cid].corrections[field] = { guess: guess || "", corrected: val, reason: "" };
  state[cid].roles = state[cid].roles || {};
  const convId = field.replace(/^role_/, "");
  state[cid].roles[convId] = { role: val, certainty: "inferred" };
  state[cid].reviewed_at = new Date().toISOString();
  saveState();
}

function download(filename, text) {
  const blob = new Blob([text], {type: "application/jsonl;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function exportFeedback() {
  const lines = buildFeedback();
  const txt = lines.map(l => JSON.stringify(l)).join("\n");
  download("event_review_feedback.jsonl", txt);
  alert("已导出 " + lines.length + " 条反馈（含 model_guess 原模型猜测 + user_correction 用户修正）。");
}

function importFeedback() {
  document.getElementById("fileImport").click();
}

function handleImport(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const txt = String(reader.result);
    let imported = 0, errors = 0;
    for (const line of txt.split("\n")) {
      const t = line.trim();
      if (!t) continue;
      try {
        const obj = JSON.parse(t);
        if (!obj.candidate_id) continue;
        state[obj.candidate_id] = state[obj.candidate_id] || {};
        const s = state[obj.candidate_id];
        s.verdict = obj.user_verdict || obj.review_status || "pending";
        if (obj.title_override) s.title = obj.title_override;
        if (obj.expectation) s.expectation = obj.expectation;
        if (obj.roles) s.roles = obj.roles;
        if (obj.merge_into) s.merge_into = obj.merge_into;
        if (obj.split_parts) s.split_parts = obj.split_parts;
        if (obj.note) s.note = obj.note;
        if (obj.value_score != null) s.value_score = obj.value_score;
        if (obj.keep_recommendation) s.keep_recommendation = obj.keep_recommendation;
        if (obj.user_correction && obj.user_correction.note) s.note = obj.user_correction.note;
        if (obj.reviewed_at) s.reviewed_at = obj.reviewed_at;
        imported++;
      } catch (err) { errors++; }
    }
    saveState();
    render();
    alert(`已重导 ${imported} 条反馈${errors ? "（"+errors+" 行解析失败）" : ""}。`);
  };
  reader.readAsText(file, "utf-8");
  e.target.value = "";
}

document.getElementById("btnSave").addEventListener("click", () => { saveState(); alert("已保存到 localStorage。"); });
document.getElementById("btnExport").addEventListener("click", exportFeedback);
document.getElementById("btnImport").addEventListener("click", importFeedback);
document.getElementById("fileImport").addEventListener("change", handleImport);

loadState();
render();
</script>
</body>
</html>"""


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cmd_render(args: argparse.Namespace) -> int:
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    if args.run_id:
        bundle["run_id"] = args.run_id
    out = render_event_review_html(bundle, Path(args.outdir))
    print(f"[render] {len(bundle.get('candidates', []))} 候选 -> {out}")
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    feedback = load_event_feedback(Path(args.feedback))
    n = apply_event_feedback(args.db, feedback)
    agg = aggregate_event_judgments(args.db, Path(args.bundle), feedback)
    print(f"[finalize] 已写入 {n} 条复核；最终事件 {agg['finalized_events']} 个（合并来源 {agg['merged_sources']}）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="v3 事件中心：人机协作复核（0 API）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_r = sub.add_parser("render", help="从 bundle JSON 渲染 event_review.html")
    p_r.add_argument("bundle")
    p_r.add_argument("--outdir", default="runs/event_review_p1")
    p_r.add_argument("--run-id", default="")
    p_r.set_defaults(func=cmd_render)

    p_f = sub.add_parser("finalize", help="反馈落库 + 最终事件判断")
    p_f.add_argument("feedback")
    p_f.add_argument("--bundle", required=True)
    p_f.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_f.set_defaults(func=cmd_finalize)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
