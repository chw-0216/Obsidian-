from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from common import SCHEMA_VERSION, connect_database, redact_for_model, utc_now


SYSTEM_INSTRUCTIONS = """你是私人聊天记录的结构化分析器。任务是帮助数据所有者检索和理解自己的记录。

必须遵守：
1. 只能依据输入片段中的可见文字，不补写事实，不猜测未表达的动机。
2. relationship_signals 只写可观察的互动迹象，例如主动邀约、持续回应、明确拒绝、表达感谢；不要诊断人格、心理疾病，也不要推断政治、宗教、性取向、健康状况等敏感身份。
3. 所有事件、待办和关系迹象尽量引用输入里的 id；禁止编造 id。
4. “我”代表数据所有者，“对方”代表匿名联系人。不同 segment_id 可能属于不同联系人，不得跨片段串联身份。
5. 没有证据时使用空数组或“无法判断”，不要为了填满字段强行下结论。
6. summary 使用简洁中文，说明发生了什么，不复述大段原文。
7. 只返回符合给定 JSON Schema 的对象。
"""


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def pending_segments(
    connection,
    minimum_messages: int,
    minimum_chars: int,
    require_two_way: bool,
    limit: int,
) -> list[dict]:
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
            s.id, s.conversation_id, s.start_ts, s.end_ts, s.message_count,
            s.char_count, s.transcript, s.content_sha256
        FROM segments s
        JOIN direction d ON d.segment_id=s.id
        LEFT JOIN annotations a ON a.segment_id=s.id
        WHERE s.message_count >= ?
          AND s.char_count >= ?
          AND (? = 0 OR (d.sent > 0 AND d.received > 0))
          AND (a.segment_id IS NULL OR a.source_sha256 <> s.content_sha256)
        ORDER BY
            (CASE WHEN d.sent > 0 AND d.received > 0 THEN 20 ELSE 0 END)
            + min(s.message_count, 30)
            + min(CAST(s.char_count / 250 AS INTEGER), 30) DESC,
            s.end_ts DESC
    """
    parameters: list[object] = [minimum_messages, minimum_chars, 1 if require_two_way else 0]
    if limit > 0:
        sql += " LIMIT ?"
        parameters.append(limit)
    return [dict(row) for row in connection.execute(sql, parameters)]


def make_batches(rows: list[dict], batch_size: int, max_chars: int) -> list[list[dict]]:
    batches: list[list[dict]] = []
    current: list[dict] = []
    characters = 0
    for row in rows:
        row_chars = len(row["transcript"])
        if current and (len(current) >= batch_size or characters + row_chars > max_chars):
            batches.append(current)
            current = []
            characters = 0
        current.append(row)
        characters += row_chars
    if current:
        batches.append(current)
    return batches


def build_prompt(batch: list[dict], redact: bool) -> tuple[str, int]:
    parts = [SYSTEM_INSTRUCTIONS, "\n以下是待分析片段："]
    replacements = 0
    for row in batch:
        transcript = row["transcript"]
        if redact:
            transcript, count = redact_for_model(transcript)
            replacements += count
        anonymous_contact = row["conversation_id"][-10:]
        parts.append(
            "\n---\n"
            f"segment_id: {row['id']}\n"
            f"anonymous_contact: 联系人-{anonymous_contact}\n"
            f"message_count: {row['message_count']}\n"
            f"messages:\n{transcript}"
        )
    return "\n".join(parts), replacements


def call_claude(
    claude_path: str,
    project_root: Path,
    prompt: str,
    schema: dict,
    model: str,
    max_budget_usd: float,
) -> tuple[dict, float | None]:
    command = [
        claude_path,
        "-p",
        "--model",
        model,
        "--tools",
        "",
        "--safe-mode",
        "--no-session-persistence",
        "--effort",
        "low",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]
    if max_budget_usd > 0:
        command.extend(["--max-budget-usd", str(max_budget_usd)])
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        cwd=project_root,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Claude Code 返回退出码 {completed.returncode}")
    try:
        outer = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Claude Code 没有返回可解析的 JSON") from exc
    if outer.get("is_error"):
        raise RuntimeError("MiMo 接口返回错误")
    structured = outer.get("structured_output")
    if structured is None:
        result = outer.get("result")
        structured = json.loads(result) if isinstance(result, str) else result
    if not isinstance(structured, dict) or not isinstance(structured.get("segments"), list):
        raise RuntimeError("结构化结果缺少 segments")
    cost = outer.get("total_cost_usd")
    return structured, float(cost) if cost is not None else None


def validate_result(result: dict, batch: list[dict]) -> list[dict]:
    expected = {row["id"] for row in batch}
    items = result.get("segments", [])
    returned = {item.get("segment_id") for item in items if isinstance(item, dict)}
    if returned != expected:
        missing = len(expected - returned)
        extra = len(returned - expected)
        raise RuntimeError(f"返回片段不完整（缺少 {missing}，多出 {extra}）")
    return items


def run_analysis(args: argparse.Namespace) -> dict[str, object]:
    project_root = Path(__file__).resolve().parents[1]
    claude_path = args.claude or shutil.which("claude")
    if not claude_path:
        fallback = Path.home() / ".local" / "bin" / "claude.exe"
        claude_path = str(fallback) if fallback.exists() else None
    if not claude_path:
        raise SystemExit("找不到 Claude Code，请确认 claude.exe 已安装。")

    schema = load_schema(args.schema)
    connection = connect_database(args.database)
    requested_limit = 0
    if args.limit_batches > 0:
        requested_limit = args.limit_batches * args.batch_size
    rows = pending_segments(
        connection,
        args.minimum_messages,
        args.minimum_chars,
        args.require_two_way,
        requested_limit,
    )
    batches = make_batches(rows, args.batch_size, args.max_chars)
    if args.limit_batches > 0:
        batches = batches[: args.limit_batches]

    started_at = utc_now()
    cursor = connection.execute(
        "INSERT INTO analysis_runs(started_at, model, status) VALUES(?, ?, 'running')",
        (started_at, args.model),
    )
    run_id = int(cursor.lastrowid)
    connection.commit()

    processed = 0
    pii_replacements = 0
    total_cost = 0.0
    known_cost = False
    try:
        for batch_index, batch in enumerate(batches, start=1):
            prompt, replacements = build_prompt(batch, redact=not args.no_redact)
            last_error: Exception | None = None
            result: dict | None = None
            cost: float | None = None
            for attempt in range(1, args.retries + 2):
                try:
                    result, cost = call_claude(
                        claude_path,
                        project_root,
                        prompt,
                        schema,
                        args.model,
                        args.max_budget_per_batch,
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt <= args.retries:
                        time.sleep(min(2**attempt, 8))
            if result is None:
                raise last_error or RuntimeError("未知 MiMo 调用错误")
            items = validate_result(result, batch)
            source_hashes = {row["id"]: row["content_sha256"] for row in batch}
            now = utc_now()
            with connection:
                connection.executemany(
                    """
                    INSERT INTO annotations(
                        segment_id, source_sha256, schema_version, model, result_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(segment_id) DO UPDATE SET
                        source_sha256=excluded.source_sha256,
                        schema_version=excluded.schema_version,
                        model=excluded.model,
                        result_json=excluded.result_json,
                        created_at=excluded.created_at
                    """,
                    [
                        (
                            item["segment_id"],
                            source_hashes[item["segment_id"]],
                            SCHEMA_VERSION,
                            args.model,
                            json.dumps(item, ensure_ascii=False, separators=(",", ":")),
                            now,
                        )
                        for item in items
                    ],
                )
            processed += len(items)
            pii_replacements += replacements
            if cost is not None:
                total_cost += cost
                known_cost = True
            print(
                f"第 {batch_index}/{len(batches)} 批完成：{len(items)} 个片段，"
                f"累计 {processed} 个；模型输入已替换 {pii_replacements} 处常见敏感标识。",
                flush=True,
            )
            if args.max_total_cost_usd > 0 and known_cost and total_cost >= args.max_total_cost_usd:
                print(
                    f"已达到本次用量保护线 ${args.max_total_cost_usd:.2f}，保留进度并停止。",
                    flush=True,
                )
                break

        with connection:
            connection.execute(
                """
                UPDATE analysis_runs
                SET finished_at=?, segment_count=?, pii_replacements=?, cost_usd=?, status='completed'
                WHERE id=?
                """,
                (utc_now(), processed, pii_replacements, total_cost if known_cost else None, run_id),
            )
    except Exception as exc:
        with connection:
            connection.execute(
                """
                UPDATE analysis_runs
                SET finished_at=?, segment_count=?, pii_replacements=?, cost_usd=?,
                    status='failed', error_summary=?
                WHERE id=?
                """,
                (
                    utc_now(),
                    processed,
                    pii_replacements,
                    total_cost if known_cost else None,
                    f"{type(exc).__name__}: {str(exc)[:240]}",
                    run_id,
                ),
            )
        raise
    finally:
        connection.close()

    return {
        "pending_selected": len(rows),
        "batches": len(batches),
        "processed": processed,
        "pii_replacements": pii_replacements,
        "cost_usd": round(total_cost, 6) if known_cost else None,
        "model": args.model,
    }


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="通过 Claude Code + MiMo 标注聊天片段。")
    parser.add_argument("--database", type=Path, default=project_root / "data" / "wechat-private-v2.sqlite3")
    parser.add_argument("--schema", type=Path, default=project_root / "config" / "analysis.schema.json")
    parser.add_argument("--claude", default="", help="claude.exe 路径，默认自动查找")
    parser.add_argument("--model", default="mimo-v2.5-pro")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-chars", type=int, default=35_000)
    parser.add_argument("--minimum-messages", type=int, default=3)
    parser.add_argument("--minimum-chars", type=int, default=0)
    parser.add_argument("--require-two-way", action="store_true", help="只分析双方都有发言的片段")
    parser.add_argument("--limit-batches", type=int, default=1, help="0 表示处理全部待标注片段")
    parser.add_argument("--max-budget-per-batch", type=float, default=0.25)
    parser.add_argument("--max-total-cost-usd", type=float, default=2.0, help="本次运行的用量保护线；0 表示不限制")
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--no-redact", action="store_true", help="不建议：把常见敏感标识原样发送给模型")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.database.exists():
        raise SystemExit("索引数据库不存在，请先运行 ingest。")
    result = run_analysis(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
