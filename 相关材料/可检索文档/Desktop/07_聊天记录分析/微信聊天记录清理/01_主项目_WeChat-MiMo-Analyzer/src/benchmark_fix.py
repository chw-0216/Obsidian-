"""
基准测试：验证 evidence_id 前缀匹配修复效果
运行 20 个未标注片段，统计 Pass A 成功率和吞吐。
"""
import asyncio
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from async_executor import (
    AsyncMiMoClient, SegmentTask, run_pass_a, get_api_key,
    DB_PATH, INITIAL_WORKERS
)

P = lambda *a, **kw: print(*a, **kw, flush=True)


def load_sample(n=20):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT s.id, s.conversation_id, s.message_count, s.char_count,
               s.transcript, s.content_sha256, s.start_ts, s.end_ts
        FROM segments s
        LEFT JOIN aggressive_annotations aa ON aa.segment_id = s.id
        WHERE aa.segment_id IS NULL
        ORDER BY s.char_count ASC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [SegmentTask(
        id=r["id"], conversation_id=r["conversation_id"],
        message_count=r["message_count"], char_count=r["char_count"],
        transcript=r["transcript"], content_sha256=r["content_sha256"],
        start_ts=r["start_ts"], end_ts=r["end_ts"],
    ) for r in rows]


async def run_benchmark():
    api_key = get_api_key()
    if not api_key:
        P("❌ 未找到 API Key")
        return

    segments = load_sample(20)
    if not segments:
        P("❌ 没有待标注片段")
        return

    P(f"基准测试: {len(segments)} 个片段")
    P(f"片段大小: min={min(s.char_count for s in segments)} max={max(s.char_count for s in segments)}")
    P("=" * 60)

    client = AsyncMiMoClient(api_key)
    await client.start()

    success = 0
    fail = 0
    total_in_tok = 0
    total_out_tok = 0
    errors = []
    t0 = time.time()

    # Run one at a time to isolate errors
    for i, seg in enumerate(segments):
        P(f"  ⏳ [{i+1}/{len(segments)}] {seg.id[:20]}... ({seg.message_count}msg, {seg.char_count}char) 调用中...", end="")
        try:
            result = await run_pass_a(client, [seg])
            in_tok = result["in_tok"]
            out_tok = result["out_tok"]
            total_in_tok += in_tok
            total_out_tok += out_tok
            success += 1
            P(f" ✅ ({in_tok}+{out_tok} tok)")
        except Exception as e:
            fail += 1
            err_msg = str(e)[:120]
            errors.append(err_msg)
            P(f" ❌ {err_msg}")

    elapsed = time.time() - t0
    await client.close()

    P("\n" + "=" * 60)
    P(f"结果: {success}/{success+fail} 成功 ({100*success/(success+fail):.0f}%)")
    P(f"耗时: {elapsed:.0f}s")
    P(f"Token: {total_in_tok} in + {total_out_tok} out = {total_in_tok+total_out_tok} total")
    if elapsed > 0:
        P(f"吞吐: {total_out_tok*60/elapsed:.0f} output tok/min")
    if errors:
        P(f"\n失败原因:")
        for e in errors:
            P(f"  - {e}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
