"""R1 Standard 模式：批量标注全部高信息量片段。"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OLD_DB = Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3")
NEW_DB = PROJECT_ROOT / "data" / "wechat-personal.sqlite3"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "round-1-observation.schema.json"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "round-1-observation.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pending_segments(old_conn: sqlite3.Connection, new_db: Path, limit: int = 0) -> list[dict]:
    """选择未标注的高信息量片段（从旧库选，排除新库已有的）。"""
    old_conn.execute(f"ATTACH DATABASE '{new_db}' AS newdb")
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
            s.id, s.conversation_id, s.message_count, s.char_count, s.transcript
        FROM segments s
        JOIN direction d ON d.segment_id = s.id
        WHERE s.message_count >= 5
          AND s.char_count >= 500
          AND d.sent > 0 AND d.received > 0
          AND NOT EXISTS (
              SELECT 1 FROM newdb.observations o
              WHERE o.segment_id = s.id
          )
        ORDER BY
            (CASE WHEN d.sent > 0 AND d.received > 0 THEN 20 ELSE 0 END)
            + min(s.message_count, 30)
            + min(CAST(s.char_count / 250 AS INTEGER), 30) DESC,
            s.end_ts DESC
    """
    if limit > 0:
        sql += f" LIMIT {limit}"
    results = [dict(r) for r in old_conn.execute(sql)]
    old_conn.execute("DETACH DATABASE newdb")
    return results


def make_batches(rows: list[dict], batch_size: int = 4, max_chars: int = 35000) -> list[list[dict]]:
    """将片段分批。"""
    batches, current, chars = [], [], 0
    for row in rows:
        rc = len(row["transcript"])
        if current and (len(current) >= batch_size or chars + rc > max_chars):
            batches.append(current)
            current, chars = [], 0
        current.append(row)
        chars += rc
    if current:
        batches.append(current)
    return batches


def build_prompt(batch: list[dict], prompt_template: str) -> str:
    """构建完整提示词。"""
    parts = [prompt_template, "\n\n## 待分析数据\n"]
    for row in batch:
        # 获取联系人名称
        old_conn = sqlite3.connect(OLD_DB)
        old_conn.row_factory = sqlite3.Row
        conv = old_conn.execute("SELECT display_name FROM conversations WHERE id=?", (row["conversation_id"],)).fetchone()
        name = conv["display_name"] if conv else "未知"
        old_conn.close()

        parts.append(
            f"\n---\nsegment_id: {row['id']}\n"
            f"contact_name: {name}\n"
            f"message_count: {row['message_count']}\n"
            f"messages:\n{row['transcript']}"
        )
    return "\n".join(parts)


def call_claude(prompt: str, schema: dict, model: str, budget: float) -> dict:
    """调用 Claude Code + MiMo。"""
    command = [
        "claude", "-p",
        "--model", model,
        "--tools", "",
        "--safe-mode",
        "--no-session-persistence",
        "--effort", "low",
        "--output-format", "json",
        "--json-schema", json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]
    if budget > 0:
        command.extend(["--max-budget-usd", str(budget)])

    completed = subprocess.run(
        command, input=prompt, text=True, encoding="utf-8", errors="replace",
        capture_output=True, cwd=PROJECT_ROOT, timeout=300, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Claude 退出码 {completed.returncode}: {completed.stderr[:200]}")

    outer = json.loads(completed.stdout)
    structured = outer.get("structured_output")
    if structured is None:
        result = outer.get("result")
        structured = json.loads(result) if isinstance(result, str) else result
    return structured


def save_results(conn: sqlite3.Connection, batch: list[dict], result: dict):
    """保存标注结果到新系统数据库。"""
    source_hashes = {}
    old_conn = sqlite3.connect(OLD_DB)
    old_conn.row_factory = sqlite3.Row
    for row in batch:
        seg = old_conn.execute("SELECT content_sha256 FROM segments WHERE id=?", (row["id"],)).fetchone()
        source_hashes[row["id"]] = seg["content_sha256"] if seg else ""
    old_conn.close()

    now = utc_now()
    segments = result.get("segments", [])
    for seg in segments:
        seg_id = seg["segment_id"]
        conn.execute(
            """
            INSERT INTO observations(segment_id, round, schema_version, model, result_json, source_sha256, user_confirmed, created_at, updated_at)
            VALUES (?, 'R1', '1.0', 'mimo-v2.5-pro', ?, ?, 'pending', ?, ?)
            ON CONFLICT(segment_id) DO UPDATE SET
                result_json=excluded.result_json,
                source_sha256=excluded.source_sha256,
                updated_at=excluded.updated_at
            """,
            (seg_id, json.dumps(seg, ensure_ascii=False), source_hashes.get(seg_id, ""), now, now),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="限制片段数，0=全部")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-batches", type=int, default=10)
    parser.add_argument("--budget", type=float, default=0.25)
    parser.add_argument("--total-budget", type=float, default=5.0)
    parser.add_argument("--model", default="mimo-v2.5-pro")
    args = parser.parse_args()

    # 连接数据库
    old_conn = sqlite3.connect(OLD_DB)
    old_conn.row_factory = sqlite3.Row
    new_conn = sqlite3.connect(NEW_DB)
    new_conn.row_factory = sqlite3.Row

    # 加载 Schema 和 Prompt
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    # 选择片段
    rows = pending_segments(old_conn, NEW_DB, args.limit)
    batches = make_batches(rows, args.batch_size)
    if args.max_batches > 0:
        batches = batches[:args.max_batches]

    print(f"待标注片段: {len(rows)}, 批次数: {len(batches)}")

    total_cost = 0.0
    processed = 0

    for i, batch in enumerate(batches, 1):
        prompt = build_prompt(batch, prompt_template)

        last_error = None
        result = None
        for attempt in range(3):
            try:
                result = call_claude(prompt, schema, args.model, args.budget)
                break
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(min(2 ** (attempt + 1), 8))

        if result is None:
            print(f"第 {i}/{len(batches)} 批失败: {last_error}")
            continue

        # 验证返回的 segment_id
        returned = {s["segment_id"] for s in result.get("segments", [])}
        expected = {r["id"] for r in batch}
        if returned != expected:
            print(f"第 {i}/{len(batches)} 批: 片段不匹配 (缺 {len(expected-returned)}, 多 {len(returned-expected)})")
            continue

        save_results(new_conn, batch, result)
        processed += len(batch)
        print(f"第 {i}/{len(batches)} 批完成: {len(batch)} 个片段, 累计 {processed} 个")

        if args.total_budget > 0 and total_cost >= args.total_budget:
            print(f"已达预算上限 ${args.total_budget:.2f}，停止。")
            break

    old_conn.close()
    new_conn.close()

    print(f"\n完成: {processed} 个片段已标注")
    print(f"数据库: {NEW_DB}")


if __name__ == "__main__":
    main()
