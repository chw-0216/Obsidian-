from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from common import connect_database


def timestamp_start(value: str) -> int:
    return int(datetime.fromisoformat(value).astimezone().timestamp()) if value else 0


def timestamp_end(value: str) -> int:
    if not value:
        return 2**63 - 1
    parsed = datetime.fromisoformat(value)
    if len(value) <= 10:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    return int(parsed.astimezone().timestamp())


def search_messages(connection, query: str, contact: str, date_from: str, date_to: str, limit: int):
    query = query.strip()
    parameters: list[object]
    if len(query) >= 3:
        sql = """
            SELECT m.id, c.display_name, m.created_at, m.is_send,
                   snippet(messages_fts, 3, '【', '】', '…', 24) AS content
            FROM messages_fts
            JOIN messages m ON m.id=messages_fts.message_id
            JOIN conversations c ON c.id=m.conversation_id
            WHERE messages_fts MATCH ?
              AND c.display_name LIKE ?
              AND m.create_ts BETWEEN ? AND ?
            ORDER BY m.create_ts DESC
            LIMIT ?
        """
        parameters = [query, f"%{contact}%", timestamp_start(date_from), timestamp_end(date_to), limit]
    else:
        sql = """
            SELECT m.id, c.display_name, m.created_at, m.is_send, m.clean_content AS content
            FROM messages m
            JOIN conversations c ON c.id=m.conversation_id
            WHERE m.clean_content LIKE ?
              AND c.display_name LIKE ?
              AND m.create_ts BETWEEN ? AND ?
            ORDER BY m.create_ts DESC
            LIMIT ?
        """
        parameters = [f"%{query}%", f"%{contact}%", timestamp_start(date_from), timestamp_end(date_to), limit]
    return [dict(row) for row in connection.execute(sql, parameters)]


def search_annotations(connection, query: str, contact: str, limit: int):
    rows = connection.execute(
        """
        SELECT a.segment_id, c.display_name, s.start_ts, s.end_ts, a.result_json
        FROM annotations a
        JOIN segments s ON s.id=a.segment_id AND a.source_sha256=s.content_sha256
        JOIN conversations c ON c.id=s.conversation_id
        WHERE a.result_json LIKE ? AND c.display_name LIKE ?
        ORDER BY s.end_ts DESC
        LIMIT ?
        """,
        (f"%{query}%", f"%{contact}%", limit),
    )
    results = []
    for row in rows:
        item = json.loads(row["result_json"])
        results.append(
            {
                "segment_id": row["segment_id"],
                "contact": row["display_name"],
                "summary": item.get("summary"),
                "topics": item.get("topics", []),
                "importance": item.get("importance"),
                "confidence": item.get("confidence"),
                "evidence_ids": item.get("evidence_message_ids", []),
            }
        )
    return results


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="搜索 WeFlow 私聊索引。")
    parser.add_argument("query", help="关键词或标注主题")
    parser.add_argument("--database", type=Path, default=project_root / "data" / "wechat-private-v2.sqlite3")
    parser.add_argument("--scope", choices=["messages", "annotations"], default="messages")
    parser.add_argument("--contact", default="")
    parser.add_argument("--from", dest="date_from", default="")
    parser.add_argument("--to", dest="date_to", default="")
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    connection = connect_database(args.database)
    if args.scope == "messages":
        results = search_messages(
            connection, args.query, args.contact, args.date_from, args.date_to, args.limit
        )
    else:
        results = search_annotations(connection, args.query, args.contact, args.limit)
    connection.close()
    print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
