"""
Stage 0 Diagnostic — 逐步验证 MiMo API 和标注流程。
不启动并发，不做全量任务。每次请求都有即时日志。
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DB_PATH = Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3")
API_BASE = "https://token-plan-cn.xiaomimimo.com/anthropic"
API_VERSION = "2023-06-01"
MODEL = "mimo-v2.5-pro"

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not key:
        settings = Path.home() / ".claude" / "settings.json"
        if settings.exists():
            with open(settings) as f:
                key = json.load(f).get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")
    return key

API_KEY = get_api_key()

# ─── Minimal API call ─────────────────────────────────────────────────────────

def api_call_raw(system: str, user_content: str, max_tokens: int, timeout: int) -> dict:
    """Single API call with full logging. Returns raw API response dict."""
    body = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_content}],
    }, ensure_ascii=False).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": API_VERSION,
    }

    url = f"{API_BASE}/v1/messages"
    req = Request(url, data=body, headers=headers, method="POST")

    t0 = time.time()
    print(f"  → POST {url}")
    print(f"    system={len(system)}chars, user={len(user_content)}chars, max_tokens={max_tokens}, timeout={timeout}s")

    resp = urlopen(req, timeout=timeout)
    raw = resp.read().decode("utf-8")
    elapsed = time.time() - t0

    data = json.loads(raw)
    usage = data.get("usage", {})
    print(f"  ← {resp.status} in {elapsed:.2f}s | model={data.get('model')} | "
          f"tokens: {usage.get('input_tokens',0)}→{usage.get('output_tokens',0)}")

    return {"data": data, "elapsed": elapsed, "raw_text": extract_text(data)}


def extract_text(data: dict) -> str:
    parts = []
    for block in data.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts).strip()


# ─── Step 1: Minimal ping ─────────────────────────────────────────────────────

def step1_minimal_ping():
    print("\n" + "="*70)
    print("Step 1/5: 最小请求 — 确认接口基础响应")
    print("="*70)

    try:
        result = api_call_raw(
            system="只返回JSON。不要其他文本。",
            user_content='返回 {"ok":true}',
            max_tokens=256,
            timeout=45,
        )
        text = result["raw_text"]
        print(f"    响应文本: {text[:200]}")

        # Try parse
        parsed = json.loads(text) if text.startswith("{") else None
        if not parsed:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])

        if parsed and parsed.get("ok") is True:
            print(f"  ✅ 最小请求成功 ({result['elapsed']:.2f}s)")
            return True
        else:
            print(f"  ⚠️  响应不是 {{ok:true}}: {text[:100]}")
            return True  # API works, just format different

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500] if hasattr(e, "read") else ""
        print(f"  ❌ HTTP Error: {e.code} {e.reason}")
        print(f"    Body: {body}")
        return False
    except URLError as e:
        print(f"  ❌ URL Error: {e.reason}")
        return False
    except TimeoutError:
        print(f"  ❌ Timeout (45s)")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected: {type(e).__name__}: {e}")
        return False


# ─── Step 2: Find small segments ──────────────────────────────────────────────

def step2_find_small_segments():
    print("\n" + "="*70)
    print("Step 2/5: 查找小片段 (1-5 条消息)")
    print("="*70)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT s.id, s.conversation_id, s.message_count, s.char_count,
               s.start_ts, s.end_ts, s.transcript
        FROM segments s
        WHERE s.message_count BETWEEN 1 AND 5
        ORDER BY s.message_count ASC, RANDOM()
        LIMIT 10
    """).fetchall()

    print(f"  找到 {len(rows)} 个小片段:")
    for i, r in enumerate(rows):
        preview = r["transcript"][:80].replace("\n", " ")
        print(f"    [{i}] msg={r['message_count']} char={r['char_count']} | {preview}...")

    conn.close()
    return [dict(r) for r in rows]


# ─── Step 3: Test minimal schema on small segment ─────────────────────────────

def step3_test_minimal_schema(segments: list[dict]):
    print("\n" + "="*70)
    print("Step 3/5: 最小 Schema 标注测试 (1个小片段, max_tokens=2048)")
    print("="*70)

    if not segments:
        print("  ⚠️  没有可用片段")
        return False

    seg = segments[0]
    print(f"  测试片段: {seg['id'][:16]}... ({seg['message_count']}条消息, {seg['char_count']}字)")

    minimal_schema = {
        "segment_id": "string",
        "summary": "一句话总结",
        "message_count": "number",
        "topics": ["主题1"],
        "tone": "语气",
        "confidence": 0.0
    }

    system = """你是聊天记录分析器。只返回一个JSON对象，不要其他文本。

输出格式：
{
  "segment_id": "片段ID",
  "summary": "一句话总结",
  "message_count": 消息数,
  "topics": ["主题1", "主题2"],
  "tone": "整体语气",
  "confidence": 0.0到1.0
}"""

    user = f"""分析以下对话片段：

segment_id: {seg['id']}
消息数: {seg['message_count']}

内容:
{seg['transcript']}

返回JSON。"""

    try:
        result = api_call_raw(system, user, max_tokens=2048, timeout=60)
        text = result["raw_text"]
        print(f"\n    响应 ({len(text)} 字符):")
        print(f"    {text[:500]}")

        # Parse
        parsed = None
        if text.startswith("{"):
            parsed = json.loads(text)
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])

        if parsed:
            print(f"\n  ✅ 最小Schema标注成功 ({result['elapsed']:.2f}s)")
            print(f"    segment_id: {parsed.get('segment_id', '?')}")
            print(f"    summary: {parsed.get('summary', '?')}")
            print(f"    topics: {parsed.get('topics', [])}")
            print(f"    tone: {parsed.get('tone', '?')}")
            print(f"    confidence: {parsed.get('confidence', '?')}")
            return True
        else:
            print(f"  ❌ 无法解析为JSON")
            return False

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500] if hasattr(e, "read") else ""
        print(f"  ❌ HTTP Error: {e.code}")
        print(f"    Body: {body}")
        return False
    except TimeoutError:
        print(f"  ❌ Timeout (60s)")
        return False
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")
        return False


# ─── Step 4: Test full schema on small segment ────────────────────────────────

FULL_SCHEMA_EXAMPLE = '''{
  "segment_id": "片段ID",
  "summary": "一句话总结",
  "messages": [
    {
      "evidence_id": "消息前16字符ID",
      "content_function": "陈述/提问/回答/请求/承诺/拒绝/感谢/道歉/调侃/情绪表达/系统通知/其他",
      "topic": "主题",
      "speech_act": "具体言语行为",
      "intent": "发送者意图",
      "is_request": false,
      "is_commitment": false,
      "is_boundary": false,
      "people_mentioned": [],
      "observable_tone": "可观察语气",
      "inferred_emotion": "推断情绪",
      "relationship_signal": "关系信号",
      "confidence": 0.9
    }
  ],
  "segment_context": {
    "conversation_trigger": "什么引发对话",
    "real_goal": "真实目的",
    "unfinished_items": ["未完成事项"]
  },
  "entities": [
    {"entity_type": "person", "name": "名称", "confidence": 0.9}
  ],
  "relationship_signals": [
    {"signal_type": "support", "direction": "mutual", "description": "描述", "strength": 0.8}
  ],
  "importance": 5,
  "overall_confidence": 0.9
}'''


def step4_test_full_schema(segments: list[dict]):
    print("\n" + "="*70)
    print("Step 4/5: 完整 Schema 标注测试 (1个小片段, max_tokens=4096)")
    print("="*70)

    if not segments:
        print("  ⚠️  没有可用片段")
        return False

    seg = segments[0]
    print(f"  测试片段: {seg['id'][:16]}... ({seg['message_count']}条消息, {seg['char_count']}字)")

    system = f"""你是数据所有者蔡浩文的私人聊天记录分析器。对每个消息和片段进行全面标注。

只返回一个JSON对象，不要其他文本。格式：
{FULL_SCHEMA_EXAMPLE}

每条消息都必须有标注。没有证据时用空数组或null。"""

    user = f"""分析以下对话片段：

segment_id: {seg['id']}
消息数: {seg['message_count']}

内容:
{seg['transcript']}

返回JSON。"""

    try:
        result = api_call_raw(system, user, max_tokens=4096, timeout=120)
        text = result["raw_text"]
        print(f"\n    响应 ({len(text)} 字符):")
        # Show first 800 chars
        print(f"    {text[:800]}")
        if len(text) > 800:
            print(f"    ... ({len(text)-800} more chars)")

        # Parse
        parsed = None
        if text.startswith("{"):
            parsed = json.loads(text)
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])

        if parsed and "messages" in parsed:
            msg_count = len(parsed["messages"])
            ent_count = len(parsed.get("entities", []))
            print(f"\n  ✅ 完整Schema标注成功 ({result['elapsed']:.2f}s)")
            print(f"    消息标注: {msg_count} 条")
            print(f"    实体: {ent_count} 个")
            print(f"    importance: {parsed.get('importance', '?')}")
            print(f"    confidence: {parsed.get('overall_confidence', '?')}")
            if parsed.get("messages"):
                m0 = parsed["messages"][0]
                print(f"    首条消息: {m0.get('content_function','?')} | {m0.get('topic','?')} | {m0.get('observable_tone','?')}")
            return True
        else:
            print(f"  ❌ 响应缺少 messages 数组")
            return False

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500] if hasattr(e, "read") else ""
        print(f"  ❌ HTTP Error: {e.code}")
        print(f"    Body: {body}")
        return False
    except TimeoutError:
        print(f"  ❌ Timeout (120s)")
        return False
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON Parse Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")
        return False


# ─── Step 5: Three consecutive successes ───────────────────────────────────────

def step5_consecutive_test(segments: list[dict]):
    print("\n" + "="*70)
    print("Step 5/5: 连续3次成功测试")
    print("="*70)

    if len(segments) < 3:
        print(f"  ⚠️  只有 {len(segments)} 个片段，用可用的")
        test_segs = segments
    else:
        test_segs = segments[:3]

    results = []
    for i, seg in enumerate(test_segs):
        print(f"\n  --- 第 {i+1}/{len(test_segs)} 次: {seg['id'][:16]} ({seg['message_count']}条) ---")

        system = f"""你是聊天记录分析器。只返回JSON。
{FULL_SCHEMA_EXAMPLE}"""

        user = f"segment_id: {seg['id']}\n消息数: {seg['message_count']}\n\n{seg['transcript']}\n\n返回JSON。"

        try:
            result = api_call_raw(system, user, max_tokens=4096, timeout=120)
            text = result["raw_text"]
            parsed = None
            if text.startswith("{"):
                parsed = json.loads(text)
            else:
                s = text.find("{")
                e = text.rfind("}") + 1
                if s >= 0 and e > s:
                    parsed = json.loads(text[s:e])

            if parsed and "messages" in parsed:
                print(f"  ✅ 成功 ({result['elapsed']:.2f}s, {len(parsed['messages'])}条标注)")
                results.append(True)
            else:
                print(f"  ❌ 响应格式不正确")
                results.append(False)

        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")
            results.append(False)

        # Small pause between calls
        if i < len(test_segs) - 1:
            time.sleep(1)

    print(f"\n  结果: {sum(results)}/{len(results)} 成功")
    return all(results) if results else False


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  WeChat-MiMo Aggressive Pipeline — Stage 0 Diagnostic          ║")
    print("║  逐步验证，不启动并发，不做全量任务                                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    if not API_KEY:
        print("\n❌ 未找到 API Key。设置 ANTHROPIC_AUTH_TOKEN 或检查 ~/.claude/settings.json")
        sys.exit(1)

    print(f"\nAPI: {API_BASE}")
    print(f"Model: {MODEL}")
    print(f"DB: {DB_PATH}")

    # Step 1
    if not step1_minimal_ping():
        print("\n⛔ 最小请求失败。检查 API Key 和网络连接。")
        sys.exit(1)

    # Step 2
    segments = step2_find_small_segments()
    if not segments:
        print("\n⛔ 没有找到小片段。")
        sys.exit(1)

    # Step 3
    if not step3_test_minimal_schema(segments):
        print("\n⛔ 最小Schema测试失败。")
        sys.exit(1)

    # Step 4
    if not step4_test_full_schema(segments):
        print("\n⛔ 完整Schema测试失败。可能需要简化schema或增大max_tokens。")
        sys.exit(1)

    # Step 5
    if not step5_consecutive_test(segments):
        print("\n⛔ 连续3次测试未全部通过。")
        sys.exit(1)

    print("\n" + "="*70)
    print("✅ 全部诊断通过！可以启动全量标注。")
    print("="*70)
    print("\n建议启动命令 (先小规模):")
    print(f'  python src/aggressive_executor.py --limit 20 --batch-size 1 --workers 2')


if __name__ == "__main__":
    main()
