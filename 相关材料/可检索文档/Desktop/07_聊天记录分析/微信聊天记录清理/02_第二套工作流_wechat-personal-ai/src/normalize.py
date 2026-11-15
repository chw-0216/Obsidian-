"""数据规范化：从旧系统导入并生成新系统所需的数据层。

原始数据只读，任何清洗都生成新层。
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


# 新系统的数据库 Schema
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL UNIQUE,
    round TEXT NOT NULL DEFAULT 'R1',
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    user_confirmed TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    round TEXT NOT NULL DEFAULT 'R2',
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    user_confirmed TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS self_patterns (
    id TEXT PRIMARY KEY,
    round TEXT NOT NULL DEFAULT 'R3',
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    user_confirmed TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coaching_experiments (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL UNIQUE,
    round TEXT NOT NULL DEFAULT 'R4',
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    user_feedback TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS persona_rules (
    id TEXT PRIMARY KEY,
    memory_block TEXT NOT NULL,
    round TEXT NOT NULL DEFAULT 'R5',
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    user_confirmed TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    action TEXT NOT NULL,
    content TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL
);
"""


def stable_hash(*parts: str, prefix: str = "") -> str:
    """确定性哈希，与旧系统一致。"""
    joined = "\x1f".join(str(p) for p in parts)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest


def create_database(db_path: Path) -> sqlite3.Connection:
    """创建新系统数据库。"""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.executescript(SCHEMA_SQL)
    connection.commit()
    return connection


def import_segments_from_old(old_db: Path, new_db: Path) -> int:
    """从旧系统导入片段元数据（不复制正文）。"""
    old_conn = sqlite3.connect(old_db)
    old_conn.row_factory = sqlite3.Row
    new_conn = create_database(new_db)

    segments = old_conn.execute(
        "SELECT id, conversation_id, start_ts, end_ts, message_count FROM segments"
    ).fetchall()

    for seg in segments:
        new_conn.execute(
            """
            INSERT OR IGNORE INTO audit_log(round, action, details, created_at)
            VALUES ('R0', 'import_segment', ?, datetime('now'))
            """,
            (json.dumps({"segment_id": seg["id"], "conversation_id": seg["conversation_id"]}),),
        )

    new_conn.commit()
    old_conn.close()
    new_conn.close()
    return len(segments)


if __name__ == "__main__":
    print("normalize.py — 数据规范化模块（骨架）")
    print("用法：在 run_round.py 中调用 import_segments_from_old()")
