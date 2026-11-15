"""v3 试运行报告生成：读 runs/<run-id> 的 JSONL + manifest，产出 PILOT-QUALITY-REPORT.md。

指标（START-HERE 要求）：
- 各尺寸片段数量、耗时、Schema 合格率、证据回链率
- Token 统计与费用估算
- 失败原因分布
- 与全量运行的差距说明
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .v3_io import read_jsonl

BUCKET_LABELS = {"1": "单消息", "2-3": "2-3条", "4-10": "4-10条", "11-30": "11-30条", "31+": "31条以上"}


def bucket_of(message_count: int) -> str:
    if message_count == 1:
        return "1"
    if message_count <= 3:
        return "2-3"
    if message_count <= 10:
        return "4-10"
    if message_count <= 30:
        return "11-30"
    return "31+"


def _evidence_stats(task: dict) -> dict:
    """证据回链率：返回 messages 中 evidence_id 与输入 expected 的匹配情况。

    results.jsonl 里没有保存 expected_ids，改为在报告期按校验结果评估：
    schema 校验在运行时已要求 messages 的 evidence_id 必须与输入完全一致，
    因此这里的“回链”度量用结果对象里各结构字段引用的 evidence_id 与
    messages 实际证据的覆盖率近似。更准确的指标在 manifest 里给出。
    """
    result = task.get("result_json") or {}
    msgs = result.get("messages") or []
    returned = {m.get("evidence_id") for m in msgs if isinstance(m, dict)}
    referenced: set[str] = set()
    for key in (
        "evidence_ids", "requests", "commitments", "events", "entities",
        "relationship_signals", "memory_candidates", "alternative_explanations",
    ):
        val = result.get(key)
        if key == "evidence_ids" and isinstance(val, list):
            referenced.update(x for x in val if isinstance(x, str))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    for inner in ("evidence_ids", "evidence_id"):
                        v = item.get(inner)
                        if isinstance(v, list):
                            referenced.update(x for x in v if isinstance(x, str))
                        elif isinstance(v, str):
                            referenced.add(v)
    return {
        "message_count": len(returned),
        "referenced_ids": len(referenced),
        "referenced_within_returned": len(referenced & returned),
    }


def build_report(cfg: dict, run_id: str) -> Path:
    runs_dir = Path(cfg["paths"]["runs_dir"])
    run_dir = runs_dir / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"运行目录不存在: {run_dir}")

    manifest = {}
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan = {}
    plan_path = run_dir / "plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))

    tasks = read_jsonl(run_dir / "tasks.jsonl")
    results = read_jsonl(run_dir / "results.jsonl")
    failures = read_jsonl(run_dir / "failures.jsonl")
    calls = read_jsonl(run_dir / "call_log.jsonl")

    # 各尺寸统计
    per_bucket: dict[str, dict] = {}
    for task in tasks:
        # 按原始片段桶统计（窗口单元归到所属片段的桶）
        seg_mc = task.get("segment_message_count") or task["message_count"]
        bucket = bucket_of(seg_mc)
        b = per_bucket.setdefault(bucket, {
            "units": 0, "segments": 0, "success": 0, "failed": 0, "skipped": 0,
            "wall_ms": 0, "in_tokens": 0, "out_tokens": 0,
            "pii_replacements": 0, "message_count": 0,
        })
        b["units"] += 1
        b["message_count"] += task["message_count"]
        b["wall_ms"] += task.get("wall_ms", 0) or 0
        b["in_tokens"] += task.get("in_tokens", 0) or 0
        b["out_tokens"] += task.get("out_tokens", 0) or 0
        b["pii_replacements"] += task.get("pii_replacements", 0) or 0
        if task["status"] == "success":
            b["success"] += 1
        elif task["status"] == "failed":
            b["failed"] += 1
        else:
            b["skipped"] += 1
    # 各桶原始片段数（来自计划）
    seg_count_by_bucket: dict[str, int] = {}
    for seg in plan.get("sampled_segments", []):
        b = seg.get("bucket") or bucket_of(seg.get("message_count", 0))
        seg_count_by_bucket[b] = seg_count_by_bucket.get(b, 0) + 1

    # 失败原因分布
    failure_reasons: dict[str, int] = {}
    for f in failures:
        err = f.get("error") or ""
        if "429" in err:
            reason = "429 限流耗尽"
        elif "timeout" in err.lower():
            reason = "请求超时耗尽"
        elif "api error" in err.lower() or "network" in err.lower() or "HTTP" in err:
            reason = "API/网络错误耗尽"
        elif "missing evidence" in err or "多余证据ID" in err or "证据ID" in err:
            reason = "证据ID校验失败耗尽"
        elif "不是数组" in err or "confidence" in err or "segment_id 不一致" in err:
            reason = "Schema 校验失败耗尽"
        else:
            reason = "其他"
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

    # 证据回链（针对成功结果）
    ev_stats = [_evidence_stats(t) for t in results]
    msg_count_total = sum(e["message_count"] for e in ev_stats)
    referenced_total = sum(e["referenced_ids"] for e in ev_stats)
    referenced_valid_total = sum(e["referenced_within_returned"] for e in ev_stats)

    # API 调用统计
    call_ok = sum(1 for c in calls if c.get("status") == "ok")
    call_429 = sum(1 for c in calls if c.get("status") == "error429")
    call_timeout = sum(1 for c in calls if c.get("status") == "error_timeout")
    call_api_err = sum(1 for c in calls if c.get("status") == "error_api")
    call_validation = sum(1 for c in calls if c.get("status") == "validation")
    in_tokens = sum(c.get("in_tokens", 0) for c in calls)
    out_tokens = sum(c.get("out_tokens", 0) for c in calls)
    call_wall_ms = sum(c.get("elapsed_ms", 0) for c in calls)

    stats = manifest.get("stats", {})

    def fmt_ms(ms: int) -> str:
        if ms <= 0:
            return "-"
        if ms < 1000:
            return f"{ms}ms"
        return f"{ms/1000:.1f}s"

    lines: list[str] = []
    lines.append(f"# PILOT-QUALITY-REPORT · {run_id}")
    lines.append("")
    lines.append(f"- 生成时间：{manifest.get('created_at', '-')}")
    lines.append(f"- 模型：{manifest.get('model') or cfg.get('model', '-')}")
    lines.append(f"- 提示词版本：{manifest.get('prompt_version') or cfg.get('prompt_version', '-')}")
    lines.append(f"- 状态：{manifest.get('status', '?')}")
    lines.append("")

    lines.append("## 1. 总体")
    lines.append("")
    lines.append(f"- 抽样片段：{manifest.get('totals', {}).get('sampled_segments', '-')}")
    lines.append(f"- 标注单元：{manifest.get('totals', {}).get('units', '-')}")
    lines.append(f"- 批次（API 请求）：{manifest.get('totals', {}).get('batches', '-')}")
    lines.append(f"- 成功单元：{stats.get('completed_units', '-')} / 失败：{stats.get('failed_units', '-')} / 跳过：{stats.get('skipped_units', '-')}")
    lines.append(f"- API 调用次数：{stats.get('api_calls', '-')}（429={stats.get('rate_429', 0)} 超时={stats.get('timeouts', 0)} 校验失败={stats.get('validation_failures', 0)}）")
    lines.append(f"- 输入 Token：{stats.get('input_tokens', in_tokens):,} / 输出 Token：{stats.get('output_tokens', out_tokens):,}")
    lines.append(f"- 耗时：{stats.get('elapsed_seconds', '-')} 秒")
    lines.append(f"- 错误率：{stats.get('error_rate', '-')}")
    lines.append("")

    lines.append("## 2. 各尺寸片段")
    lines.append("")
    lines.append("| 尺寸 | 片段数 | 单元数 | 成功 | 失败 | 跳过 | 消息数 | 耗时(含重试) | 输入Token | 输出Token | PII替换 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for label in ["1", "2-3", "4-10", "11-30", "31+"]:
        b = per_bucket.get(label)
        if not b:
            continue
        segs = seg_count_by_bucket.get(label, 0)
        lines.append(
            f"| {BUCKET_LABELS[label]} | {segs} | {b['units']} | {b['success']} | {b['failed']} | {b['skipped']} "
            f"| {b['message_count']} | {fmt_ms(b['wall_ms'])} | {b['in_tokens']:,} | {b['out_tokens']:,} "
            f"| {b['pii_replacements']} |"
        )
    lines.append("")

    lines.append("## 3. Schema 合格率与证据回链")
    lines.append("")
    total_units = len(tasks)
    passed_units = len(results)
    if total_units:
        lines.append(f"- Schema 合格率（成功/非跳过单元）：{passed_units}/{total_units} = {passed_units/total_units:.1%}")
    if msg_count_total:
        lines.append(
            f"- 证据回链率：结果引用的证据ID中 {referenced_valid_total}/{referenced_total} 落在本单元实际证据内 "
            f"= {referenced_valid_total/referenced_total:.1%}"
        )
        lines.append(f"- 成功单元消息标注数：{msg_count_total}")
    lines.append("")

    lines.append("## 4. 失败原因分布")
    lines.append("")
    if failure_reasons:
        for reason, count in sorted(failure_reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- 无失败。")
    lines.append("")

    lines.append("## 5. 单请求耗时与 Token")
    lines.append("")
    if calls:
        ok_calls = [c for c in calls if c.get("status") == "ok"]
        if ok_calls:
            avg_in = sum(c.get("in_tokens", 0) for c in ok_calls) / len(ok_calls)
            avg_out = sum(c.get("out_tokens", 0) for c in ok_calls) / len(ok_calls)
            avg_ms = sum(c.get("elapsed_ms", 0) for c in ok_calls) / len(ok_calls)
            lines.append(f"- 成功请求数：{len(ok_calls)}")
            lines.append(f"- 平均每请求：in={avg_in:.0f} tok / out={avg_out:.0f} tok / {fmt_ms(int(avg_ms))}")
            lines.append(f"- 平均 output 速率：{avg_out / max(avg_ms / 60000, 1e-9):.0f} tok/min（按单请求耗时推算）")
    lines.append("")

    lines.append("## 6. 说明")
    lines.append("")
    lines.append("- 本次为最多 20 个分层片段的试运行，未启动全量。")
    lines.append("- 长片段按 15 条消息窗口切分，每个请求只发送对应窗口文本。")
    lines.append("- 短片段合批为单个 API 请求，结果逐片段拆分并严格校验证据 ID。")
    lines.append(f"- 费用估算：输出 Token {out_tokens:,} × 单价（DeepSeek Flash 单价未知，需按账单核实）。")
    lines.append("")

    report = "\n".join(lines)
    out = Path(cfg["report"]["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return out


# ─── 复核与价值判断报告（人机协作环节，0 API） ──────────────────────────────────

_KEEP_LABELS = {"keep": "保留", "pending": "待定", "cleanup": "清理"}


def _correction_stats(corrections_json) -> dict[str, dict[str, int]]:
    """统计复核反馈中的修正/拒绝动作，按候选组汇总。"""
    stats: dict[str, dict[str, int]] = {}
    try:
        corr = json.loads(corrections_json) if corrections_json else {}
    except json.JSONDecodeError:
        corr = {}
    for _uk, groups in (corr or {}).items():
        for group, items in groups.items():
            for _idx, item in items.items():
                action = (item or {}).get("action")
                if action in ("correct", "reject"):
                    g = stats.setdefault(group, {"correct": 0, "reject": 0})
                    g[action] += 1
    return stats


def build_review_report(cfg: dict, run_id: str) -> Path:
    """生成 REVIEW-VALUE-REPORT-<run_id>.md：复核覆盖、修正统计、会话价值聚合。"""
    import sqlite3

    conn = sqlite3.connect(cfg["paths"]["db"])
    try:
        reviews = conn.execute(
            "SELECT segment_id, conversation_id, review_status, value_score, value_tags, "
            "keep_recommendation, note, corrections_json FROM v3_review WHERE run_id=?",
            (run_id,),
        ).fetchall()
        finals = conn.execute(
            "SELECT conversation_id, segment_count, reviewed_count, avg_value_score, "
            "min_value_score, max_value_score, keep_counts, keep_recommendation, derived_note "
            "FROM v3_final_judgments WHERE run_id=?",
            (run_id,),
        ).fetchall()
    finally:
        conn.close()

    status_counts: dict[str, int] = {"pending": 0, "confirmed": 0, "corrected": 0}
    reviewed = 0
    scores: list[int] = []
    keep_all: dict[str, int] = {"keep": 0, "pending": 0, "cleanup": 0}
    corr_total: dict[str, dict[str, int]] = {}
    for r in reviews:
        st = r[2] or "pending"
        status_counts[st] = status_counts.get(st, 0) + 1
        if st != "pending":
            reviewed += 1
            if r[3] is not None:
                scores.append(int(r[3]))
            keep_all[r[5] or "pending"] = keep_all.get(r[5] or "pending", 0) + 1
            cs = _correction_stats(r[7])
            for g, counts in cs.items():
                d = corr_total.setdefault(g, {"correct": 0, "reject": 0})
                d["correct"] += counts["correct"]
                d["reject"] += counts["reject"]

    lines: list[str] = []
    lines.append(f"# REVIEW-VALUE-REPORT · {run_id}")
    lines.append("")
    lines.append("- 生成时间：{0}".format(datetime.now().astimezone().isoformat(timespec="seconds")))
    lines.append("- 来源：v3_review（人工复核反馈）+ v3_final_judgments（规则聚合）· 0 API")
    lines.append("")

    lines.append("## 1. 复核覆盖")
    lines.append("")
    lines.append(f"- 反馈片段数：{len(reviews)}")
    lines.append(f"- 已复核：{reviewed}（确认 {status_counts.get('confirmed', 0)} / "
                 f"修正 {status_counts.get('corrected', 0)}）")
    lines.append(f"- 未复核：{status_counts.get('pending', 0)}")
    lines.append("")

    lines.append("## 2. 候选修正统计（correct / reject）")
    lines.append("")
    if corr_total:
        lines.append("| 候选组 | 修正 | 拒绝 |")
        lines.append("|---|---|---|")
        for g, counts in sorted(corr_total.items()):
            lines.append(f"| {g} | {counts['correct']} | {counts['reject']} |")
    else:
        lines.append("- 无修正/拒绝记录。")
    lines.append("")

    lines.append("## 3. 会话价值聚合（已复核片段）")
    lines.append("")
    if finals:
        lines.append("| 会话 | 抽样片段 | 已复核 | 价值均值 | 区间 | 保留建议（片段计数） | 派生建议 |")
        lines.append("|---|---|---|---|---|---|---|")
        for f in finals:
            conv = f[0]
            try:
                keeps = json.loads(f[6]) if f[6] else {}
            except json.JSONDecodeError:
                keeps = {}
            keep_str = " ".join(
                f"{_KEEP_LABELS.get(k, k)}={v}" for k, v in sorted(keeps.items())
            )
            avg = f"{f[3]:.1f}" if f[3] is not None else "-"
            rng = f"{f[4]}-{f[5]}" if f[4] is not None else "-"
            lines.append(
                f"| `{conv[:12]}…` | {f[1]} | {f[2]} | {avg} | {rng} | {keep_str} | "
                f"{_KEEP_LABELS.get(f[7], f[7])} |"
            )
    else:
        lines.append("- 尚无已复核会话。")
    lines.append("")

    lines.append("## 4. 价值分数分布（已复核片段，0-100）")
    lines.append("")
    if scores:
        bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
        for lo, hi in bins:
            n = sum(1 for s in scores if lo <= s < hi)
            bar = "#" * int(round(n / max(len(scores), 1) * 20))
            lines.append(f"- {lo:>2}-{hi - 1:>3}: {n:>3}  {bar}")
        lines.append(f"- 均值：{sum(scores) / len(scores):.1f} / 样本 {len(scores)}")
    else:
        lines.append("- 暂无价值分数。")
    lines.append("")

    lines.append("## 5. 备注")
    lines.append("")
    lines.append("- 会话级建议由 v3_review.aggregate_final_judgments 规则派生（cleanup>0→清理；"
                 "否则 pending>0→待定；否则保留），仅基于已复核片段。")
    lines.append("- 如需覆盖会话建议，可在 v3_final_judgments 中人工更新。")
    lines.append("")

    report = "\n".join(lines)
    out = cfg["report"]["output"].with_name(f"REVIEW-VALUE-REPORT-{run_id}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return out
