from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import connect_database


REQUIRED_ANNOTATION_FIELDS = {
    "segment_id",
    "summary",
    "interaction_category",
    "topics",
    "observed_tone",
    "key_events",
    "action_items",
    "relationship_signals",
    "importance",
    "privacy_level",
    "confidence",
    "evidence_message_ids",
}


def verify(database: Path) -> dict[str, object]:
    connection = connect_database(database)
    problems: list[str] = []
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        problems.append(f"SQLite integrity_check: {integrity}")

    counts = {
        table: int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        for table in ("conversations", "messages", "segments", "annotations", "messages_fts")
    }
    if counts["messages"] != counts["messages_fts"]:
        problems.append("消息数与全文索引数不一致")

    checked_annotations = 0
    invalid_evidence = 0
    for row in connection.execute(
        """
        SELECT a.segment_id, a.source_sha256, a.result_json, s.content_sha256
        FROM annotations a JOIN segments s ON s.id=a.segment_id
        """
    ):
        checked_annotations += 1
        try:
            result = json.loads(row["result_json"])
        except json.JSONDecodeError:
            problems.append(f"标注 JSON 无法解析：{row['segment_id']}")
            continue
        missing = REQUIRED_ANNOTATION_FIELDS - set(result)
        if missing:
            problems.append(f"标注缺字段：{row['segment_id']} ({len(missing)})")
        if result.get("segment_id") != row["segment_id"]:
            problems.append(f"标注片段 ID 不一致：{row['segment_id']}")
        if row["source_sha256"] != row["content_sha256"]:
            problems.append(f"标注已过期：{row['segment_id']}")
        valid_evidence = {
            message[0][:16]
            for message in connection.execute(
                "SELECT id FROM messages WHERE segment_id=?", (row["segment_id"],)
            )
        }
        evidence_sets = [result.get("evidence_message_ids", [])]
        evidence_sets.extend(item.get("evidence_ids", []) for item in result.get("key_events", []))
        evidence_sets.extend(item.get("evidence_ids", []) for item in result.get("action_items", []))
        evidence_sets.extend(
            item.get("evidence_ids", []) for item in result.get("relationship_signals", [])
        )
        for evidence_id in (item for values in evidence_sets for item in values):
            if evidence_id not in valid_evidence:
                invalid_evidence += 1
    if invalid_evidence:
        problems.append(f"发现 {invalid_evidence} 个无法回指当前片段的证据 ID")

    connection.close()
    return {
        "ok": not problems,
        "integrity": integrity,
        "counts": counts,
        "checked_annotations": checked_annotations,
        "invalid_evidence_ids": invalid_evidence,
        "problems": problems,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="核验本地索引和 MiMo 标注完整性。")
    parser.add_argument(
        "--database", type=Path, default=project_root / "data" / "wechat-private-v2.sqlite3"
    )
    args = parser.parse_args()
    result = verify(args.database)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
