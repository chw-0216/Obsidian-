"""样本选择：为每轮分析选择高信息量片段。

继承旧系统的评分逻辑：双向对话 +20，消息数上限 +30，字符数/250 上限 +30。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def select_high_info_segments(
    connection: sqlite3.Connection,
    minimum_messages: int = 5,
    minimum_chars: int = 500,
    require_two_way: bool = True,
    limit: int = 40,
    exclude_annotated: bool = True,
) -> list[dict]:
    """选择高信息量片段，按评分排序。"""
    sql = """
        WITH direction AS (
            SELECT segment_id,
                   sum(is_send) AS sent,
                   count(*) - sum(is_send) AS received
            FROM messages
            WHERE segment_id IS NOT NULL
            GROUP BY segment_id
        )
        SELECT
            s.id, s.conversation_id, s.start_ts, s.end_ts,
            s.message_count, s.char_count, s.transcript
        FROM segments s
        JOIN direction d ON d.segment_id = s.id
    """
    conditions = [
        "s.message_count >= ?",
        "s.char_count >= ?",
    ]
    params: list[object] = [minimum_messages, minimum_chars]

    if require_two_way:
        conditions.append("d.sent > 0 AND d.received > 0")

    if exclude_annotated:
        conditions.append("""
            NOT EXISTS (
                SELECT 1 FROM observations o
                WHERE o.segment_id = s.id AND o.source_sha256 = s.content_sha256
            )
        """)

    sql += " WHERE " + " AND ".join(conditions)
    sql += """
        ORDER BY
            (CASE WHEN d.sent > 0 AND d.received > 0 THEN 20 ELSE 0 END)
            + min(s.message_count, 30)
            + min(CAST(s.char_count / 250 AS INTEGER), 30) DESC,
            s.end_ts DESC
    """

    if limit > 0:
        sql += " LIMIT ?"
        params.append(limit)

    return [dict(row) for row in connection.execute(sql, params)]


def select_contacts_by_volume(
    connection: sqlite3.Connection,
    min_messages: int = 100,
    limit: int = 30,
) -> list[dict]:
    """按消息量选择联系人，用于 R2 关系分析。"""
    sql = """
        SELECT
            c.id AS conversation_id,
            c.display_name,
            count(m.id) AS message_count,
            min(m.create_ts) AS first_ts,
            max(m.create_ts) AS last_ts,
            sum(m.is_send) AS sent,
            count(m.id) - sum(m.is_send) AS received
        FROM conversations c
        JOIN messages m ON m.conversation_id = c.id
        GROUP BY c.id
        HAVING count(m.id) >= ?
        ORDER BY count(m.id) DESC
        LIMIT ?
    """
    return [dict(row) for row in connection.execute(sql, [min_messages, limit])]


if __name__ == "__main__":
    print("select_samples.py — 样本选择模块")
