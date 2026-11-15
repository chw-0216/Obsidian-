"""语义质量抽查：抽取 N 个已标注单元，把原文与模型结论配对输出，供人工核对。

检查维度：错判、过度推断、事件归属、证据是否真正支持结论。
用法：python diag/semantic_review.py <run_id> [N] [out.md]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]

BUCKET_LABELS = {"1": "单消息", "2-3": "2-3条", "4-10": "4-10条", "11-30": "11-30条", "31+": "31条以上"}


def bucket_of(mc: int) -> str:
    if mc == 1:
        return "1"
    if mc <= 3:
        return "2-3"
    if mc <= 10:
        return "4-10"
    if mc <= 30:
        return "11-30"
    return "31+"


def main() -> None:
    run_id = sys.argv[1] if len(sys.argv) > 1 else ""
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    if not run_id:
        print("需要 run_id")
        sys.exit(1)
    run_dir = WORKSPACE_ROOT / "runs" / run_id
    db = WORKSPACE_ROOT / "data" / "scale" / "wechat-analysis-scale.sqlite3"

    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    results = [
        json.loads(l) for l in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    seg_mc = {s["id"]: s["message_count"] for s in plan["sampled_segments"]}

    # 按桶分层取 N 个：每桶 ceil(N/5) 个
    import math
    per_bucket = math.ceil(n / 5)
    picked: list[dict] = []
    seen_bucket: dict[str, int] = {}
    for r in results:
        seg_mc_ = r.get("segment_message_count") or r.get("message_count") or 0
        b = bucket_of(seg_mc_)
        if seen_bucket.get(b, 0) >= per_bucket:
            continue
        seen_bucket[b] = seen_bucket.get(b, 0) + 1
        picked.append(r)
        if len(picked) >= n:
            break

    lines: list[str] = []
    lines.append(f"# 语义质量抽查 · {run_id}")
    lines.append(f"- 抽取 {len(picked)} 个单元（每桶至多 {per_bucket} 个）")
    lines.append("")
    for i, task in enumerate(picked, 1):
        seg = task["segment_id"]
        widx = task.get("window_idx", 0)
        mc = task.get("segment_message_count") or task.get("message_count") or 0
        lines.append(f"## {i}. {seg[:20]}… :{widx} （{BUCKET_LABELS[bucket_of(mc)]}，片段 {mc} 条）")
        lines.append("")
        # 原文（证据）
        row = conn.execute("SELECT transcript FROM segments WHERE id=?", (seg,)).fetchone()
        transcript = row[0] if row else ""
        from src.v3_core import build_units
        built = build_units(seg, transcript, "", "", 15, mc)
        unit = built[widx] if widx < len(built) else None
        lines.append("### 原文证据（本窗口）")
        lines.append("```")
        if unit:
            lines.append(unit.render_for_prompt())
        else:
            lines.append(f"（无法重建窗口 {widx}）")
        lines.append("```")
        lines.append("")
        # 模型结论
        res = task.get("result_json") or {}
        lines.append("### 模型结论")
        lines.append(f"- summary：{res.get('summary')}")
        lines.append(f"- topic：{res.get('topic')}")
        lines.append(f"- confidence：{res.get('confidence')}")
        msgs = res.get("messages") or []
        lines.append("")
        lines.append("| 消息 | 互动功能 | intent | tone | 推断情绪 | 记忆候选 |")
        lines.append("|---|---|---|---|---|---|")
        for m in msgs:
            lines.append(
                f"| {m.get('evidence_id')} | {m.get('content_function')} | {m.get('intent')} "
                f"| {m.get('observable_tone')} | {m.get('inferred_emotion')} | {m.get('memory_candidate')} |"
            )
        for label, key in [("请求", "requests"), ("承诺", "commitments"), ("事件", "events"),
                           ("实体", "entities"), ("关系信号", "relationship_signals"),
                           ("记忆候选", "memory_candidates"), ("替代解释", "alternative_explanations")]:
            items = res.get(key) or []
            if items:
                lines.append("")
                lines.append(f"#### {label}")
                for it in items:
                    ev = it.get("evidence_ids") or []
                    lines.append(f"- {json.dumps(it, ensure_ascii=False)}  → 证据: {ev}")
        lines.append("")
        lines.append("---")
        lines.append("")

    conn.close()
    text = "\n".join(lines)
    if out:
        out.write_text(text, encoding="utf-8")
        print(f"written -> {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
