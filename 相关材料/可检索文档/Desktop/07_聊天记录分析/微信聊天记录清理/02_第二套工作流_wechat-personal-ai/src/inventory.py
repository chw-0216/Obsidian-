"""Round 0: 数据契约和质量盘点。

只回答"有什么数据、缺什么数据、能否追溯"，不理解内容。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def count_messages(connection: sqlite3.Connection) -> dict:
    """统计消息总数、发送/接收、时间范围。"""
    row = connection.execute(
        "SELECT count(*), sum(is_send), min(create_ts), max(create_ts) FROM messages"
    ).fetchone()
    return {
        "total": row[0],
        "sent": row[1] or 0,
        "received": (row[0] - (row[1] or 0)),
        "first_ts": row[2],
        "last_ts": row[3],
    }


def count_segments(connection: sqlite3.Connection) -> dict:
    """统计片段总数和平均长度。"""
    row = connection.execute(
        "SELECT count(*), avg(message_count), avg(char_count) FROM segments"
    ).fetchone()
    return {
        "total": row[0],
        "avg_messages": round(row[1] or 0, 1),
        "avg_chars": round(row[2] or 0, 0),
    }


def count_annotations(connection: sqlite3.Connection) -> dict:
    """统计标注数量和覆盖率。"""
    total_segments = connection.execute("SELECT count(*) FROM segments").fetchone()[0]
    total_annotations = connection.execute("SELECT count(*) FROM annotations").fetchone()[0]
    current_annotations = connection.execute(
        """
        SELECT count(*) FROM annotations a
        JOIN segments s ON a.segment_id = s.id
        WHERE a.source_sha256 = s.content_sha256
        """
    ).fetchone()[0]
    return {
        "total": total_annotations,
        "current": current_annotations,
        "stale": total_annotations - current_annotations,
        "coverage": current_annotations / total_segments if total_segments else 0,
    }


def count_message_types(connection: sqlite3.Connection) -> dict:
    """按消息类型统计。"""
    rows = connection.execute(
        "SELECT message_type, count(*) FROM messages GROUP BY message_type ORDER BY count(*) DESC"
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def run_inventory(db_path: Path) -> dict:
    """执行完整的数据盘点。"""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    result = {
        "messages": count_messages(connection),
        "segments": count_segments(connection),
        "annotations": count_annotations(connection),
        "message_types": count_message_types(connection),
        "conversations": connection.execute("SELECT count(*) FROM conversations").fetchone()[0],
    }

    connection.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="R0 数据盘点")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = run_inventory(args.database)
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"盘点结果已写入 {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
