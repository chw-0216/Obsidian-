from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from common import connect_database, utc_now


def md_escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def local_time(timestamp: int) -> str:
    if not timestamp:
        return "—"
    return datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M")


def collect_report(connection) -> dict[str, object]:
    totals = dict(
        connection.execute(
            """
            SELECT
                (SELECT count(*) FROM conversations) AS conversations,
                (SELECT count(*) FROM messages) AS messages,
                (SELECT count(*) FROM segments) AS segments,
                (SELECT count(*) FROM annotations) AS annotations,
                (SELECT min(create_ts) FROM messages WHERE create_ts > 0) AS first_ts,
                (SELECT max(create_ts) FROM messages WHERE create_ts > 0) AS last_ts,
                (SELECT sum(is_send) FROM messages) AS sent,
                (SELECT count(*) - sum(is_send) FROM messages) AS received
            """
        ).fetchone()
    )
    current_annotations = int(
        connection.execute(
            """
            SELECT count(*) FROM annotations a
            JOIN segments s ON s.id=a.segment_id
            WHERE a.source_sha256=s.content_sha256
            """
        ).fetchone()[0]
    )
    totals["current_annotations"] = current_annotations
    totals["coverage"] = (
        current_annotations / totals["segments"] if totals.get("segments") else 0.0
    )

    months = [
        dict(row)
        for row in connection.execute(
            """
            SELECT strftime('%Y-%m', create_ts, 'unixepoch', 'localtime') AS month,
                   count(*) AS messages,
                   sum(is_send) AS sent,
                   count(*) - sum(is_send) AS received
            FROM messages
            WHERE create_ts > 0
            GROUP BY month
            ORDER BY month
            """
        )
    ]
    contacts = [
        dict(row)
        for row in connection.execute(
            """
            SELECT c.display_name, count(m.id) AS messages,
                   sum(m.is_send) AS sent, count(m.id)-sum(m.is_send) AS received,
                   min(m.create_ts) AS first_ts, max(m.create_ts) AS last_ts
            FROM conversations c
            JOIN messages m ON m.conversation_id=c.id
            GROUP BY c.id
            ORDER BY messages DESC
            LIMIT 25
            """
        )
    ]

    topics: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    tones: Counter[str] = Counter()
    high_importance: list[dict] = []
    open_actions: list[dict] = []
    annotation_rows = connection.execute(
        """
        SELECT a.result_json, s.start_ts, s.end_ts, c.display_name
        FROM annotations a
        JOIN segments s ON s.id=a.segment_id AND a.source_sha256=s.content_sha256
        JOIN conversations c ON c.id=s.conversation_id
        """
    )
    for row in annotation_rows:
        try:
            item = json.loads(row["result_json"])
        except json.JSONDecodeError:
            continue
        topics.update(str(value) for value in item.get("topics", []) if value)
        categories.update(str(value) for value in item.get("interaction_category", []) if value)
        tones.update(str(value) for value in item.get("observed_tone", []) if value)
        if int(item.get("importance", 0)) >= 4:
            high_importance.append(
                {
                    "display_name": row["display_name"],
                    "start_ts": row["start_ts"],
                    "end_ts": row["end_ts"],
                    "summary": item.get("summary", ""),
                    "importance": item.get("importance", 0),
                    "confidence": item.get("confidence", 0),
                    "evidence": item.get("evidence_message_ids", []),
                }
            )
        for action in item.get("action_items", []):
            if action.get("status") in {"待办", "进行中"}:
                open_actions.append(
                    {
                        "display_name": row["display_name"],
                        "time": row["end_ts"],
                        **action,
                    }
                )

    high_importance.sort(key=lambda item: (item["importance"], item["end_ts"]), reverse=True)
    open_actions.sort(key=lambda item: item["time"], reverse=True)
    return {
        "generated_at": utc_now(),
        "totals": totals,
        "months": months,
        "top_contacts": contacts,
        "top_topics": topics.most_common(30),
        "top_categories": categories.most_common(20),
        "top_tones": tones.most_common(20),
        "high_importance": high_importance[:40],
        "open_actions": open_actions[:60],
    }


def render_markdown(report: dict[str, object]) -> str:
    totals = report["totals"]
    lines = [
        "# WeFlow 私聊分析概览",
        "",
        f"生成时间：{report['generated_at']}",
        "",
        "## 数据覆盖",
        "",
        f"- 有内容的私聊：{totals['conversations']:,} 个",
        f"- 消息：{totals['messages']:,} 条（我发送 {int(totals['sent'] or 0):,}，收到 {int(totals['received'] or 0):,}）",
        f"- 时间范围：{local_time(int(totals['first_ts'] or 0))} 至 {local_time(int(totals['last_ts'] or 0))}",
        f"- 对话片段：{totals['segments']:,} 个",
        f"- MiMo 当前有效标注：{totals['current_annotations']:,} 个，覆盖率 {totals['coverage']:.1%}",
        "",
        "> 本报告只汇总可观察记录。情绪和关系标签是检索线索，不是对任何人的心理诊断或事实判决。",
        "",
        "## 月度消息量",
        "",
        "| 月份 | 总消息 | 我发送 | 收到 |",
        "|---|---:|---:|---:|",
    ]
    for row in report["months"]:
        lines.append(
            f"| {row['month']} | {row['messages']:,} | {int(row['sent'] or 0):,} | {int(row['received'] or 0):,} |"
        )

    lines.extend(
        [
            "",
            "## 消息量最多的联系人",
            "",
            "| 联系人 | 消息 | 我发送 | 收到 | 最近记录 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in report["top_contacts"]:
        lines.append(
            f"| {md_escape(row['display_name'])} | {row['messages']:,} | "
            f"{int(row['sent'] or 0):,} | {int(row['received'] or 0):,} | "
            f"{local_time(int(row['last_ts'] or 0))} |"
        )

    if report["top_topics"]:
        lines.extend(["", "## MiMo 标注概况", "", "### 高频主题", ""])
        lines.append("、".join(f"{md_escape(name)}（{count}）" for name, count in report["top_topics"][:20]))
        lines.extend(["", "### 互动类型", ""])
        lines.append("、".join(f"{md_escape(name)}（{count}）" for name, count in report["top_categories"]))
        lines.extend(["", "### 可观察语气", ""])
        lines.append("、".join(f"{md_escape(name)}（{count}）" for name, count in report["top_tones"]))

    if report["open_actions"]:
        lines.extend(
            [
                "",
                "## 待办与进行中事项",
                "",
                "| 联系人 | 时间 | 责任方 | 状态 | 事项 | 截止信息 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in report["open_actions"]:
            lines.append(
                f"| {md_escape(item['display_name'])} | {local_time(int(item['time'] or 0))} | "
                f"{md_escape(item.get('owner'))} | {md_escape(item.get('status'))} | "
                f"{md_escape(item.get('action'))} | {md_escape(item.get('due_date') or '—')} |"
            )

    if report["high_importance"]:
        lines.extend(
            [
                "",
                "## 高重要度片段",
                "",
                "| 联系人 | 时间 | 重要度 | 置信度 | 摘要 | 证据消息 ID |",
                "|---|---|---:|---:|---|---|",
            ]
        )
        for item in report["high_importance"]:
            evidence = ", ".join(item["evidence"][:6])
            lines.append(
                f"| {md_escape(item['display_name'])} | {local_time(int(item['end_ts'] or 0))} | "
                f"{item['importance']} | {float(item['confidence'] or 0):.2f} | "
                f"{md_escape(item['summary'])} | {md_escape(evidence)} |"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="生成私聊分析概览。")
    parser.add_argument("--database", type=Path, default=project_root / "data" / "wechat-private-v2.sqlite3")
    parser.add_argument("--output", type=Path, default=project_root / "reports" / "overview.md")
    parser.add_argument("--json-output", type=Path, default=project_root / "reports" / "overview.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    connection = connect_database(args.database)
    report = collect_report(connection)
    connection.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(report), encoding="utf-8")
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(args.output.resolve()),
                "json": str(args.json_output.resolve()),
                "messages": report["totals"]["messages"],
                "annotation_coverage": report["totals"]["coverage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
