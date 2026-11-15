from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from common import (
    SCHEMA_VERSION,
    clean_text,
    connect_database,
    display_time,
    file_sha256,
    json_text,
    normalize_timestamp,
    stable_hash,
    utc_now,
)


MESSAGE_TYPE_NAMES = {
    "1": "文本",
    "3": "图片",
    "34": "语音",
    "42": "名片",
    "43": "视频",
    "47": "表情",
    "48": "位置",
    "49": "链接或文件",
    "50": "通话",
    "10000": "系统消息",
}


def normalize_local_type(value: object) -> str:
    """WeChat 4.0 的 localType 高位含子类型位；只保留低 32 位基类型。"""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return json_text(value)
    if number > 0xFFFFFFFF:
        number &= 0xFFFFFFFF
    return str(number)


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            source_relpath TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            declared_message_count INTEGER NOT NULL DEFAULT 0,
            loaded_message_count INTEGER NOT NULL DEFAULT 0,
            first_ts INTEGER NOT NULL DEFAULT 0,
            last_ts INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            local_id TEXT,
            platform_message_id TEXT,
            create_ts INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            is_send INTEGER NOT NULL,
            sender_name TEXT NOT NULL,
            message_type TEXT NOT NULL,
            local_type TEXT NOT NULL,
            raw_content TEXT NOT NULL,
            clean_content TEXT NOT NULL,
            source_payload TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            source_file TEXT NOT NULL,
            segment_id TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
            ON messages(conversation_id, create_ts, id);
        CREATE INDEX IF NOT EXISTS idx_messages_segment
            ON messages(segment_id);

        CREATE TABLE IF NOT EXISTS segments (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            start_ts INTEGER NOT NULL,
            end_ts INTEGER NOT NULL,
            message_count INTEGER NOT NULL,
            char_count INTEGER NOT NULL,
            transcript TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_segments_pending
            ON segments(end_ts, message_count);

        CREATE TABLE IF NOT EXISTS annotations (
            segment_id TEXT PRIMARY KEY REFERENCES segments(id) ON DELETE CASCADE,
            source_sha256 TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            model TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            model TEXT NOT NULL,
            segment_count INTEGER NOT NULL DEFAULT 0,
            pii_replacements INTEGER NOT NULL DEFAULT 0,
            cost_usd REAL,
            status TEXT NOT NULL,
            error_summary TEXT
        );
        """
    )
    connection.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING "
        "fts5(message_id UNINDEXED, conversation_name, sender_name, content, tokenize='trigram')"
    )


def set_metadata(connection: sqlite3.Connection, key: str, value: object) -> None:
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def message_display_content(message: dict, clean_content_value: str) -> str:
    if clean_content_value:
        return clean_content_value
    local_type = str(message.get("localType") or message.get("type") or "未知")
    label = MESSAGE_TYPE_NAMES.get(local_type, f"类型 {local_type}")
    return f"<{label}>"


def build_segments(
    connection: sqlite3.Connection,
    conversation_id: str,
    messages: list[dict],
    *,
    gap_minutes: int,
    max_messages: int,
    max_chars: int,
) -> int:
    rows: list[dict] = []
    for message in messages:
        content = message_display_content(message, message["clean_content"])
        role = "我" if message["is_send"] else "对方"
        type_name = MESSAGE_TYPE_NAMES.get(message["local_type"], message["local_type"] or "未知")
        evidence_id = message["id"][:16]
        line = f"[id={evidence_id}][{message['created_at']}][{role}][{type_name}] {content}"
        rows.append({**message, "line": line})

    groups: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0
    previous_ts = 0
    gap_seconds = max(1, gap_minutes) * 60

    for row in rows:
        line_size = len(row["line"]) + 1
        should_break = bool(
            current
            and (
                (row["create_ts"] and previous_ts and row["create_ts"] - previous_ts > gap_seconds)
                or len(current) >= max_messages
                or current_chars + line_size > max_chars
            )
        )
        if should_break:
            groups.append(current)
            current = []
            current_chars = 0
        current.append(row)
        current_chars += line_size
        if row["create_ts"]:
            previous_ts = row["create_ts"]
    if current:
        groups.append(current)

    seen_segments: set[str] = set()
    now = utc_now()
    for ordinal, group in enumerate(groups, start=1):
        transcript = "\n".join(item["line"] for item in group)
        segment_id = stable_hash(
            conversation_id,
            group[0]["id"],
            group[-1]["id"],
            prefix="seg_",
        )
        seen_segments.add(segment_id)
        content_sha256 = stable_hash(transcript)
        timestamps = [item["create_ts"] for item in group if item["create_ts"]]
        start_ts = min(timestamps) if timestamps else 0
        end_ts = max(timestamps) if timestamps else 0
        connection.execute(
            """
            INSERT INTO segments(
                id, conversation_id, ordinal, start_ts, end_ts, message_count,
                char_count, transcript, content_sha256, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                ordinal=excluded.ordinal,
                start_ts=excluded.start_ts,
                end_ts=excluded.end_ts,
                message_count=excluded.message_count,
                char_count=excluded.char_count,
                transcript=excluded.transcript,
                content_sha256=excluded.content_sha256,
                updated_at=excluded.updated_at
            """,
            (
                segment_id,
                conversation_id,
                ordinal,
                start_ts,
                end_ts,
                len(group),
                len(transcript),
                transcript,
                content_sha256,
                now,
            ),
        )
        connection.executemany(
            "UPDATE messages SET segment_id=? WHERE id=?",
            [(segment_id, item["id"]) for item in group],
        )

    existing_ids = {
        row[0]
        for row in connection.execute(
            "SELECT id FROM segments WHERE conversation_id=?", (conversation_id,)
        )
    }
    stale_ids = existing_ids - seen_segments
    if stale_ids:
        connection.executemany("DELETE FROM segments WHERE id=?", [(item,) for item in stale_ids])
    return len(groups)


def ingest_file(
    connection: sqlite3.Connection,
    source_root: Path,
    path: Path,
    *,
    gap_minutes: int,
    max_messages: int,
    max_chars: int,
) -> tuple[str, int, int, Counter[str]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise ValueError("缺少 WeFlow messages 数组")

    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    source_relpath = str(path.relative_to(source_root))
    session_key = session.get("wxid") or source_relpath
    conversation_id = stable_hash(session_key, prefix="conv_")
    display_name_value = (
        session.get("displayName")
        or session.get("remark")
        or session.get("nickname")
        or path.stem.removeprefix("私聊_")
        or "未命名联系人"
    )
    display_name_value = clean_text(display_name_value) or "未命名联系人"
    source_digest = file_sha256(path)

    normalized_messages: list[dict] = []
    local_types: Counter[str] = Counter()
    for index, raw_message in enumerate(payload["messages"]):
        if not isinstance(raw_message, dict):
            continue
        create_ts = normalize_timestamp(raw_message.get("createTime"))
        raw_content = json_text(raw_message.get("content"))
        cleaned = clean_text(raw_message.get("content"))
        source_payload = json_text(raw_message.get("source"))
        local_id = json_text(raw_message.get("localId"))
        platform_id = json_text(raw_message.get("platformMessageId"))
        local_type = normalize_local_type(raw_message.get("localType") or raw_message.get("type"))
        is_send = 1 if bool(raw_message.get("isSend")) else 0
        sender_name = clean_text(raw_message.get("senderDisplayName"))
        message_id = stable_hash(
            conversation_id,
            platform_id or local_id or "",
            create_ts,
            raw_content,
            index,
            prefix="msg_",
        )
        content_digest = stable_hash(raw_content, source_payload, local_type)
        normalized_messages.append(
            {
                "id": message_id,
                "conversation_id": conversation_id,
                "local_id": local_id,
                "platform_message_id": platform_id,
                "create_ts": create_ts,
                "created_at": display_time(create_ts),
                "is_send": is_send,
                "sender_name": sender_name,
                "message_type": json_text(raw_message.get("type")),
                "local_type": local_type,
                "raw_content": raw_content,
                "clean_content": cleaned,
                "source_payload": source_payload,
                "content_sha256": content_digest,
                "source_file": source_relpath,
            }
        )
        local_types[local_type] += 1

    normalized_messages.sort(key=lambda item: (item["create_ts"], item["local_id"], item["id"]))
    timestamps = [item["create_ts"] for item in normalized_messages if item["create_ts"]]
    first_ts = min(timestamps) if timestamps else 0
    last_ts = max(timestamps) if timestamps else 0
    now = utc_now()
    connection.execute(
        """
        INSERT INTO conversations(
            id, display_name, source_relpath, source_sha256,
            declared_message_count, loaded_message_count, first_ts, last_ts, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            display_name=excluded.display_name,
            source_relpath=excluded.source_relpath,
            source_sha256=excluded.source_sha256,
            declared_message_count=excluded.declared_message_count,
            loaded_message_count=excluded.loaded_message_count,
            first_ts=excluded.first_ts,
            last_ts=excluded.last_ts,
            updated_at=excluded.updated_at
        """,
        (
            conversation_id,
            display_name_value,
            source_relpath,
            source_digest,
            int(session.get("messageCount") or 0),
            len(normalized_messages),
            first_ts,
            last_ts,
            now,
        ),
    )
    connection.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
    connection.executemany(
        """
        INSERT INTO messages(
            id, conversation_id, local_id, platform_message_id, create_ts, created_at,
            is_send, sender_name, message_type, local_type, raw_content, clean_content,
            source_payload, content_sha256, source_file
        ) VALUES (
            :id, :conversation_id, :local_id, :platform_message_id, :create_ts, :created_at,
            :is_send, :sender_name, :message_type, :local_type, :raw_content, :clean_content,
            :source_payload, :content_sha256, :source_file
        )
        """,
        normalized_messages,
    )
    segment_count = build_segments(
        connection,
        conversation_id,
        normalized_messages,
        gap_minutes=gap_minutes,
        max_messages=max_messages,
        max_chars=max_chars,
    )
    return conversation_id, len(normalized_messages), segment_count, local_types


def rebuild_fts(connection: sqlite3.Connection) -> int:
    connection.execute("DELETE FROM messages_fts")
    connection.execute(
        """
        INSERT INTO messages_fts(message_id, conversation_name, sender_name, content)
        SELECT m.id, c.display_name, m.sender_name, m.clean_content
        FROM messages m
        JOIN conversations c ON c.id=m.conversation_id
        WHERE length(m.clean_content) > 0
        """
    )
    return int(connection.execute("SELECT count(*) FROM messages_fts").fetchone()[0])


def run_ingest(
    source_root: Path,
    database_path: Path,
    *,
    gap_minutes: int = 90,
    max_messages: int = 60,
    max_chars: int = 10_000,
) -> dict[str, object]:
    source_root = source_root.resolve()
    files = sorted(source_root.rglob("私聊_*.json"))
    connection = connect_database(database_path)
    create_schema(connection)
    connection.execute("CREATE TEMP TABLE IF NOT EXISTS seen_conversations(id TEXT PRIMARY KEY)")
    connection.execute("DELETE FROM seen_conversations")

    valid_files = 0
    invalid_files = 0
    message_count = 0
    segment_count = 0
    type_counts: Counter[str] = Counter()
    errors: list[str] = []

    for index, path in enumerate(files, start=1):
        try:
            with connection:
                conversation_id, messages, segments, local_types = ingest_file(
                    connection,
                    source_root,
                    path,
                    gap_minutes=gap_minutes,
                    max_messages=max_messages,
                    max_chars=max_chars,
                )
                connection.execute(
                    "INSERT OR IGNORE INTO seen_conversations(id) VALUES(?)", (conversation_id,)
                )
            valid_files += 1
            message_count += messages
            segment_count += segments
            type_counts.update(local_types)
        except Exception as exc:  # keep the full import resumable
            invalid_files += 1
            errors.append(f"{path.name}: {type(exc).__name__}")
        if index % 100 == 0:
            print(f"已读取 {index}/{len(files)} 个私聊 JSON", flush=True)

    with connection:
        connection.execute(
            "DELETE FROM conversations WHERE id NOT IN (SELECT id FROM seen_conversations)"
        )
        fts_rows = rebuild_fts(connection)
        set_metadata(connection, "schema_version", SCHEMA_VERSION)
        set_metadata(connection, "source_root", source_root)
        set_metadata(connection, "source_json_files", len(files))
        set_metadata(connection, "valid_json_files", valid_files)
        set_metadata(connection, "invalid_json_files", invalid_files)
        set_metadata(connection, "messages", message_count)
        set_metadata(connection, "segments", segment_count)
        set_metadata(connection, "fts_rows", fts_rows)
        set_metadata(connection, "last_ingest_at", utc_now())
        set_metadata(connection, "local_type_counts", json.dumps(type_counts, ensure_ascii=False))
        set_metadata(connection, "ingest_errors", json.dumps(errors, ensure_ascii=False))
    connection.close()
    return {
        "source_json_files": len(files),
        "valid_json_files": valid_files,
        "invalid_json_files": invalid_files,
        "messages": message_count,
        "segments": segment_count,
        "fts_rows": fts_rows,
        "database": str(database_path.resolve()),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入 WeFlow 私聊详细 JSON，并建立本地索引。")
    parser.add_argument("--source", type=Path, required=True, help="WeFlow 可读导出根目录")
    parser.add_argument("--database", type=Path, required=True, help="输出 SQLite 数据库")
    parser.add_argument("--gap-minutes", type=int, default=90, help="超过此间隔切分对话片段")
    parser.add_argument("--max-messages", type=int, default=60, help="单片段最多消息数")
    parser.add_argument("--max-chars", type=int, default=10_000, help="单片段最多字符数")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"找不到 WeFlow 导出目录：{args.source}")
    result = run_ingest(
        args.source,
        args.database,
        gap_minutes=args.gap_minutes,
        max_messages=args.max_messages,
        max_chars=args.max_chars,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
