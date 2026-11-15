"""诊断脚本：用失败批次 batch[0] 的同一提示词做一次 API 调用，保存原始响应到文件。

目的：确认模型对 5 个单消息单元合批时返回的到底是截断 JSON / 非 JSON 文本 / 空响应。
Token 只在请求头使用，绝不写入任何输出文件。
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    import aiohttp  # noqa: F401
except ImportError:
    VENDOR = Path(r"C:\Users\wardc\Desktop\微信聊天记录清理\09_未迁移脚本与运行依赖\runtime\vendor")
    if VENDOR.exists():
        sys.path.insert(0, str(VENDOR))

from src.v3_api import extract_text  # noqa: E402
from src.v3_core import Unit, build_group_prompt  # noqa: E402

CONFIG = json.loads(
    (WORKSPACE_ROOT / "config" / "v3_config.json").read_text(encoding="utf-8")
)
PLAN = json.loads(
    (WORKSPACE_ROOT / "runs" / "plan_v3_20260805_183059" / "plan.json").read_text(encoding="utf-8")
)
PROMPT = (WORKSPACE_ROOT / "prompts" / "base_annotation.md").read_text(encoding="utf-8")

DB_PATH = WORKSPACE_ROOT / "data" / "wechat-analysis-v3.sqlite3"


def rebuild_unit(unit_meta: dict) -> Unit:
    import sqlite3
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT transcript FROM segments WHERE id=?", (unit_meta["segment_id"],)
        ).fetchone()
        transcript = row[0] if row else ""
    finally:
        conn.close()
    from src.v3_core import build_units
    built = build_units(
        unit_meta["segment_id"],
        transcript,
        segment_sha256="",
        conversation_id="",
        window_size=CONFIG["batching"]["window_size_msgs"],
        segment_message_count=unit_meta["segment_message_count"],
    )
    for u in built:
        if u.window_idx == unit_meta["window_idx"]:
            return u
    raise ValueError(f"unit not rebuilt: {unit_meta['unit_key']}")


async def main() -> None:
    import aiohttp

    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    api_cfg = CONFIG["api"]
    model = CONFIG["model"]
    max_tokens = api_cfg["max_output_tokens"]

    batch0_keys = PLAN["batches"][0]
    unit_metas = [u for u in PLAN["units"] if u["unit_key"] in batch0_keys]
    units = [rebuild_unit(m) for m in unit_metas]
    prompt = build_group_prompt(PROMPT, units)
    print(f"batch0 units: {len(units)}, msgs: {sum(u.message_count for u in units)}", flush=True)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": token,
        "Authorization": f"Bearer {token}",
        "anthropic-version": api_cfg["api_version"],
    }
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
        "system": PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        t0 = asyncio.get_event_loop().time()
        async with session.post(
            f"{base_url.rstrip('/')}/v1/messages", data=json.dumps(body, ensure_ascii=False)
        ) as resp:
            raw = await resp.text()
            elapsed = asyncio.get_event_loop().time() - t0
            status = resp.status
            resp_headers = dict(resp.headers)

    data = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pass

    text = extract_text(data) if isinstance(data, dict) else ""
    usage = (data or {}).get("usage") if isinstance(data, dict) else None
    stop = (data or {}).get("stop_reason") if isinstance(data, dict) else None

    out = Path(WORKSPACE_ROOT) / "diag" / "diag_batch0_response.txt"
    out.write_text(
        "\n".join([
            f"status={status} elapsed={elapsed:.1f}s stop_reason={stop}",
            f"usage={json.dumps(usage, ensure_ascii=False) if usage else None}",
            f"resp_content_types={[b.get('type') for b in (data or {}).get('content', [])] if isinstance(data, dict) else 'N/A'}",
            "--- raw text (first 3000 chars) ---",
            text[:3000],
            "--- raw json dump (first 3000 chars) ---",
            raw[:3000],
        ]),
        encoding="utf-8",
    )
    print(f"written -> diag/diag_batch0_response.txt")
    print(f"status={status} stop_reason={stop} text_len={len(text)}")
    if usage:
        print(f"usage in={usage.get('input_tokens')} out={usage.get('output_tokens')}")


if __name__ == "__main__":
    asyncio.run(main())
