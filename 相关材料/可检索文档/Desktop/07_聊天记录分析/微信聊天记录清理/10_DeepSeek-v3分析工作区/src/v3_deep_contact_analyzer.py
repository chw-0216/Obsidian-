"""深度联系人分析脚本——按联系人聚合消息，分批送模型做人格/关系/进化分析"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_api import ApiClient, RateLimitError, ApiError, extract_openai_text


def _connect_ro(path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    tmp.replace(path)

# ───────────────────────── 系统提示词 ─────────────────────────
DEEP_CONTACT_SYSTEM = """你是一位**深度关系分析师**，专门分析微信聊天记录中的人际关系。

## 任务
分析以下联系人（{contact_name}）的完整聊天记录，输出一份**深度关系分析报告**。

## 分析维度
1. **关系本质** — 对方在你生命中的角色（朋友/同事/家人/恋人/客户/导师/其他），关系的亲密度和权力结构
2. **时间演化** — 关系随时间的变化轨迹（升温/降温/稳定/转折），标注关键时间节点
3. **关键事件** — 重大对话节点：承诺、冲突、共同经历、情感暴露、求助、告别
4. **情感基调** — 整体情感倾向（积极/消极/中性/混合），信任度，情绪传染模式
5. **互动模式** — 谁更主动？对话节奏（密集/稀疏/间歇），回应模式（秒回/拖延/已读不回）
6. **自我进化** — 通过这段关系，你（用户）学到了什么、改变了什么、成长了什么
7. **重要性评分** — 综合消息量、互动深度、情感权重、时间跨度，给出 1-10 分

## 输出格式
请严格输出 JSON（不要 markdown 包裹）：
{{
  "contact_name": "联系人名称",
  "message_count": 消息总数,
  "time_span": "2024-01-01 ~ 2025-06-15",
  "analysis": {{
    "role": "朋友/同事/...",
    "intimacy": 1-10,
    "power_structure": "平等/对方主导/我方主导/交替",
    "evolution": "升温/降温/稳定/波动",
    "evolution_detail": "一段详细描述",
    "key_events": [{{"date": "大致日期", "event": "事件描述", "impact": "正面/负面/中性"}}],
    "emotional_tone": {{
      "overall": "积极/消极/中性/混合",
      "trust_level": 1-10,
      "positivity_ratio": 0.0-1.0
    }},
    "interaction_pattern": {{
      "initiator": "对方/我方/均衡",
      "rhythm": "密集/稀疏/间歇",
      "response_style": "秒回/正常/拖延/单向"
    }},
    "self_evolution": "一段描述——你通过这段关系学到了什么、改变了什么",
    "importance": 1-10,
    "importance_reason": "为什么给这个分数"
  }},
  "summary": "一段 200 字以内的中文总结"
}}

只输出 JSON，不要额外解释。"""

# ───────────────────────── 队列构建 ─────────────────────────
def build_contact_queue(db_path: str, min_msgs: int = 10, max_contacts: int = None):
    """按消息数降序排列联系人，返回分析任务队列"""
    conn = _connect_ro(db_path)
    conn.row_factory = None
    rows = conn.execute("""
        SELECT c.display_name, c.loaded_message_count,
               c.first_ts, c.last_ts, c.id as conv_id
        FROM conversations c
        WHERE c.loaded_message_count >= ?
        ORDER BY c.loaded_message_count DESC
    """, (min_msgs,)).fetchall()
    conn.close()

    if max_contacts:
        rows = rows[:max_contacts]

    return rows  # [(name, msg_count, first_ts, last_ts, conv_id), ...]


def fetch_contact_messages(db_path: str, conv_id: int, max_chars: int = 60000):
    """拉取联系人全部消息，按时间排序，截断到 max_chars"""
    conn = _connect_ro(db_path)
    conn.row_factory = None
    rows = conn.execute("""
        SELECT m.create_ts, m.is_send, m.message_type, m.clean_content,
               m.sender_name
        FROM messages m
        WHERE m.conversation_id = ?
        ORDER BY m.create_ts ASC
    """, (conv_id,)).fetchall()
    conn.close()

    if not rows:
        return "", 0

    lines = []
    total_chars = 0
    for ts, is_from_me, msg_type, content, sender in rows:
        speaker = "我" if is_from_me else (sender or "对方")
        text = (content or "").strip()
        if not text:
            continue
        ts_str = str(ts) if ts else ""
        line = f"[{ts_str[:19]}] {speaker}: {text}"
        if total_chars + len(line) > max_chars:
            break
        lines.append(line)
        total_chars += len(line)

    return "\n".join(lines), len(rows)


# ───────────────────────── 主循环 ─────────────────────────
async def analyze_contacts(
    base_url: str,
    token: str,
    model: str,
    db_path: str,
    output_dir: str,
    min_msgs: int = 10,
    max_contacts: int = None,
    rpm_limit: int = 30,
    max_chars: int = 60000,
    max_tokens: int = 4096,
    workers: int = 4,
):
    queue = build_contact_queue(db_path, min_msgs=min_msgs, max_contacts=max_contacts)
    print(f"[queue] {len(queue)} 个联系人待分析")

    if not queue:
        print("[queue] 无符合条件的联系人，退出")
        return

    client = ApiClient(
        base_url=base_url,
        token=token,
        model=model,
        api_style="openai",
        rpm_limit=rpm_limit,
        rate_burst=min(workers, 3),
        max_output_tokens=max_tokens,
        request_timeout=180,
        connect_timeout=20,
    )
    await client.start()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    sem = asyncio.Semaphore(workers)

    async def analyze_one(idx: int, name: str, msg_count: int, first_ts: str, last_ts: str, conv_id: int):
        async with sem:
            t0 = time.time()
            try:
                chat_text, total_msgs = fetch_contact_messages(db_path, conv_id, max_chars=max_chars)
                if not chat_text.strip():
                    print(f"  [{idx}/{len(queue)}] {name} — 无消息内容，跳过")
                    return None

                prompt = f"联系人: {name}\n消息总数: {msg_count}\n时间跨度: {str(first_ts)[:10] if first_ts else '?'} ~ {str(last_ts)[:10] if last_ts else '?'}\n\n=== 聊天记录 ===\n{chat_text}\n=== 结束 ==="
                system = DEEP_CONTACT_SYSTEM.format(contact_name=name)

                parsed, in_tok, out_tok = await client.call(system=system, user_content=prompt)

                elapsed = int((time.time() - t0) * 1000)
                print(f"  [{idx}/{len(queue)}] {name} ✅ ({msg_count}条, {elapsed}ms) 重要性={parsed.get('analysis',{}).get('importance','?')}")

                return {
                    "idx": idx,
                    "contact_name": name,
                    "message_count": msg_count,
                    "total_msgs_in_db": total_msgs,
                    "chars_sent": len(chat_text),
                    "analysis": parsed,
                    "elapsed_ms": elapsed,
                }

            except RateLimitError as e:
                print(f"  [{idx}/{len(queue)}] {name} ⚠️ 429 — 放回队列")
                await asyncio.sleep(30)
                return {"idx": idx, "contact_name": name, "error": "429", "detail": str(e)}
            except ApiError as e:
                print(f"  [{idx}/{len(queue)}] {name} ❌ API错误: {e}")
                return {"idx": idx, "contact_name": name, "error": "api_error", "detail": str(e)}
            except Exception as e:
                print(f"  [{idx}/{len(queue)}] {name} ❌ 异常: {e}")
                return {"idx": idx, "contact_name": name, "error": "exception", "detail": str(e)}

    tasks = [
        analyze_one(i + 1, name, cnt, fts, lts, cid)
        for i, (name, cnt, fts, lts, cid) in enumerate(queue)
    ]
    raw_results = await asyncio.gather(*tasks)

    # 过滤失败
    results = [r for r in raw_results if r and "error" not in r]
    errors = [r for r in raw_results if r and "error" in r]

    print(f"\n[完成] {len(results)}/{len(queue)} 成功, {len(errors)} 失败")

    # 按重要性排序输出
    results.sort(key=lambda r: r["analysis"].get("analysis", {}).get("importance", 0), reverse=True)

    # 写入汇总报告
    report = {
        "total_contacts": len(queue),
        "successful": len(results),
        "failed": len(errors),
        "model": model,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ranking": results,
        "errors": errors,
    }
    _write_json(out_dir / "deep_contact_analysis.json", report)
    print(f"[report] 已写入 {out_dir / 'deep_contact_analysis.json'}")

    # 打印 Top 10 排名
    print("\n========== 重要性排名 TOP 10 ==========")
    for i, r in enumerate(results[:10]):
        a = r["analysis"].get("analysis", {})
        print(f"  #{i+1} {r['contact_name']:20s} 重要性={a.get('importance','?')} 角色={a.get('role','?')} 亲密度={a.get('intimacy','?')}")

    await client.close()
    return results


# ───────────────────────── CLI ─────────────────────────
def main():
    parser = argparse.ArgumentParser(description="深度联系人分析")
    parser.add_argument("--db", default="data/scale/wechat-analysis-scale.sqlite3")
    parser.add_argument("--output", default="runs/deep_contact_analysis")
    parser.add_argument("--model", default="custom/deepseek-v4-pro")
    parser.add_argument("--base-url", default="http://156.238.239.147:3000/v1")
    parser.add_argument("--token", default=os.environ.get("ANTHROPIC_AUTH_TOKEN", ""))
    parser.add_argument("--min-msgs", type=int, default=10, help="最少消息数")
    parser.add_argument("--max-contacts", type=int, default=None, help="最多分析几个联系人")
    parser.add_argument("--rpm", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-chars", type=int, default=60000, help="每个联系人最大输入字符数")
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    asyncio.run(analyze_contacts(
        base_url=args.base_url,
        token=args.token,
        model=args.model,
        db_path=args.db,
        output_dir=args.output,
        min_msgs=args.min_msgs,
        max_contacts=args.max_contacts,
        rpm_limit=args.rpm,
        max_chars=args.max_chars,
        max_tokens=args.max_tokens,
        workers=args.workers,
    ))


if __name__ == "__main__":
    main()