"""自我进化深度分析流水线

Phase 1: 全量标注（已有 v3_executor 在跑）
Phase 2: 模式提取——从标注数据中归纳关系模式、行为规律、情感演化
Phase 3: 自我进化——模型反思 Phase 2 的分析，提出改进，重新分析
Phase 4: 最终汇总——按重要性排序，输出深度联系人报告 + 进化轨迹
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# 复用现有 ApiClient
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_api import ApiClient, RateLimitError, ApiError, extract_openai_text, parse_json


def _write_json(path: Path, data):
    """原子写入 JSON（写临时文件再 rename）"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    tmp.replace(path)

# ═══════════════════════ Phase 2: 模式提取 ═══════════════════════

PHASE2_SYSTEM = """你是一位**关系模式分析师**。下面是某个联系人的 v3 标注结果（JSON 数组），请提取以下模式：

1. **互动节奏**：对话频率、时间分布（工作日/周末/深夜）、谁更主动
2. **话题聚类**：主要讨论什么话题（工作/情感/日常/学术/游戏/其他），各占比多少
3. **情感曲线**：从最早到最晚，情感基调如何变化（升温/降温/稳定/波动）
4. **关系锚点**：有哪些关键事件/承诺/冲突改变了关系
5. **自我投射**：你（用户）在这个关系中扮演什么角色，展现了什么性格侧面

输出严格 JSON：
{
  "contact_name": "...",
  "patterns": {
    "rhythm": { "frequency": "高频/中频/低频", "active_hours": ["白天","深夜"], "initiator": "对方/我/均衡", "avg_reply_gap": "秒回/分钟/小时/天" },
    "topics": [ {"topic": "话题名", "ratio": 0.0-1.0, "examples": ["关键词1","关键词2"]} ],
    "emotion_curve": { "trend": "升温/降温/稳定/波动", "phases": [ {"period": "时间段", "tone": "积极/消极/中性", "trigger": "原因"} ] },
    "anchors": [ {"event": "事件描述", "date": "大致日期", "impact": "正面/负面/转折", "evidence": "证据片段"} ],
    "self_projection": { "roles": ["角色1","角色2"], "traits": ["性格特征1","性格特征2"], "growth": "这段关系中的成长" }
  }
}"""


async def phase2_extract_patterns(
    client: ApiClient,
    db_path: str,
    output_dir: Path,
    max_contacts: int = None,
    workers: int = 2,
):
    """从 v3_annotations 中读取已标注数据，按联系人聚合，提取模式"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 获取有标注的联系人
    contacts = conn.execute("""
        SELECT DISTINCT c.display_name, c.id as conv_id, c.loaded_message_count,
               c.first_ts, c.last_ts,
               COUNT(a.run_id) as annotation_count
        FROM v3_annotations a
        JOIN segments s ON a.segment_id = s.id
        JOIN conversations c ON s.conversation_id = c.id
        WHERE a.status = 'success'
        GROUP BY c.id
        ORDER BY c.loaded_message_count DESC
    """).fetchall()

    if max_contacts:
        contacts = contacts[:max_contacts]

    print(f"[Phase 2] {len(contacts)} 个联系人待分析模式")

    # 获取所有标注的 JSON 内容（通过 segments 桥接 conversation_id）
    annotations = {}
    for row in conn.execute("""
        SELECT a.run_id, s.conversation_id, a.segment_id, a.window_idx,
               a.result_json, a.message_count, a.input_tokens, a.output_tokens
        FROM v3_annotations a
        JOIN segments s ON a.segment_id = s.id
        WHERE a.status = 'success'
        ORDER BY s.conversation_id, a.segment_id, a.window_idx
    """).fetchall():
        cid = row["conversation_id"]
        if cid not in annotations:
            annotations[cid] = []
        annotations[cid].append(dict(row))

    conn.close()

    # 转为普通 dict（conn.close() 后 Row 会失效）
    contacts = [dict(r) for r in contacts]
    for cid in annotations:
        annotations[cid] = [dict(r) for r in annotations[cid]]

    out_dir = output_dir / "phase2_patterns"
    out_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(workers)
    results = []

    async def analyze_one(idx: int, contact):
        async with sem:
            cid = contact["conv_id"]
            name = contact["display_name"] or f"conv_{cid}"
            msgs = contact["loaded_message_count"]
            ann_count = contact["annotation_count"]
            span = f"{str(contact['first_ts'])[:10] if contact['first_ts'] else '?'} ~ {str(contact['last_ts'])[:10] if contact['last_ts'] else '?'}"
            anns = annotations.get(cid, [])
            if not anns:
                return None

            # 取标注中的关键字段摘要
            summary_items = []
            for a in anns[:50]:  # 最多 50 条标注
                try:
                    obj = json.loads(a["result_json"]) if isinstance(a["result_json"], str) else a["result_json"]
                    # 只取关键字段，减少 token
                    slim = {
                        "seg": a["segment_id"],
                        "msg_count": a["message_count"],
                    }
                    if isinstance(obj, dict):
                        for k in ("entities", "events", "sentiment", "topics", "requests", "commitments", "relationship_signals"):
                            if k in obj:
                                slim[k] = obj[k]
                    summary_items.append(slim)
                except (json.JSONDecodeError, TypeError):
                    summary_items.append({"seg": a["segment_id"], "raw": str(a["annotation_json"])[:200]})

            prompt = f"联系人: {name}\n消息总数: {msgs}\n已标注片段: {ann_count}\n时间跨度: {span}\n\n=== 标注摘要 ===\n{json.dumps(summary_items, ensure_ascii=False, indent=1)}\n=== 结束 ==="

            try:
                t0 = time.time()
                parsed, in_tok, out_tok = await client.call(system=PHASE2_SYSTEM, user_content=prompt)
                elapsed = int((time.time() - t0) * 1000)
                print(f"  [P2 {idx}/{len(contacts)}] {name} ✅ ({elapsed}ms)")

                result = {
                    "contact_name": name,
                    "message_count": msgs,
                    "annotation_count": ann_count,
                    "time_span": span,
                    "patterns": parsed,
                    "elapsed_ms": elapsed,
                }
                _write_json(out_dir / f"{name}.json", result)
                return result

            except RateLimitError as e:
                print(f"  [P2 {idx}/{len(contacts)}] {name} ⚠️ 429")
                await asyncio.sleep(30)
                return None
            except Exception as e:
                print(f"  [P2 {idx}/{len(contacts)}] {name} ❌ {e}")
                return None

    tasks = [analyze_one(i + 1, c) for i, c in enumerate(contacts)]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    for i, r in enumerate(raw):
        if isinstance(r, Exception):
            print(f"  [P2 err] #{i}: {type(r).__name__}: {r}")
    results = [r for r in raw if r is not None and not isinstance(r, Exception)]
    print(f"[Phase 2] 完成 {len(results)}/{len(contacts)}")

    # 汇总
    summary = {
        "phase": 2,
        "total_contacts": len(contacts),
        "completed": len(results),
        "results": results,
    }
    _write_json(out_dir / "_phase2_summary.json", summary)
    return results


# ═══════════════════════ Phase 3: 自我进化 ═══════════════════════

PHASE3_SYSTEM = """你是一位**自我进化分析师**。下面是某联系人的 Phase 2 模式分析结果，以及原始标注摘要。

请进行以下反思和进化：

1. **批判性审视**：Phase 2 的分析有哪些遗漏？哪些结论缺乏证据？哪些推断过于武断？
2. **深层挖掘**：从原始标注中挖掘 Phase 2 没注意到的模式——隐藏的情感、未言明的需求、微妙的权力动态
3. **修正与补充**：对 Phase 2 的结论进行修正，补充新的发现
4. **进化轨迹**：这个联系人的关系如何塑造了你？你在这段关系中获得了什么、失去了什么、变成了什么？
5. **最终重要性评分**：1-10 分，并给出详细理由

输出严格 JSON：
{
  "contact_name": "...",
  "phase2_critique": {
    "blind_spots": ["遗漏1", "遗漏2"],
    "overconfident": ["武断结论1"],
    "missing_evidence": ["缺少证据的推断1"]
  },
  "deeper_insights": {
    "hidden_emotions": ["隐藏情绪1"],
    "unspoken_needs": ["未言明需求1"],
    "power_dynamics": "权力动态描述",
    "subtext": "弦外之音"
  },
  "evolution": {
    "what_i_gained": ["收获1", "收获2"],
    "what_i_lost": ["失去1"],
    "how_i_changed": "我如何改变",
    "lessons": ["教训1", "教训2"]
  },
  "final_importance": 1-10,
  "importance_rationale": "详细理由",
  "summary_200words": "200字总结"
}"""


async def phase3_evolve(
    client: ApiClient,
    phase2_dir: Path,
    db_path: str,
    output_dir: Path,
    workers: int = 2,
):
    """对 Phase 2 的每个结果进行自我进化反思"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 加载 Phase 2 结果
    p2_files = sorted(phase2_dir.glob("*.json"))
    p2_files = [f for f in p2_files if not f.name.startswith("_")]
    print(f"[Phase 3] {len(p2_files)} 个 Phase 2 结果待进化")

    # 加载标注摘要
    annotations = {}
    for row in conn.execute("""
        SELECT a.conversation_id, a.result_json, a.segment_id, a.message_count
        FROM v3_annotations a
        WHERE a.status = 'success'
        ORDER BY a.conversation_id, a.segment_id
    """).fetchall():
        cid = row["conversation_id"]
        if cid not in annotations:
            annotations[cid] = []
        annotations[cid].append(dict(row))
    conn.close()

    out_dir = output_dir / "phase3_evolution"
    out_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(workers)
    results = []

    async def evolve_one(idx: int, p2_file: Path):
        async with sem:
            try:
                with open(p2_file, "r", encoding="utf-8") as f:
                    p2_data = json.load(f)
            except Exception:
                return None

            name = p2_data.get("contact_name", p2_file.stem)
            # 找对应的原始标注
            raw_anns = []
            for cid, anns in annotations.items():
                # 用 display_name 匹配
                for a in anns[:20]:
                    try:
                        obj = json.loads(a["result_json"]) if isinstance(a["result_json"], str) else a["result_json"]
                        raw_anns.append({"seg": a["segment_id"], "msgs": a["message_count"], "obj": obj})
                    except Exception:
                        pass
                if len(raw_anns) >= 10:
                    break

            prompt = f"Phase 2 分析结果:\n{json.dumps(p2_data.get('patterns', {}), ensure_ascii=False, indent=1)[:4000]}\n\n原始标注摘要:\n{json.dumps(raw_anns, ensure_ascii=False, indent=1)[:4000]}"

            try:
                t0 = time.time()
                parsed, in_tok, out_tok = await client.call(system=PHASE3_SYSTEM, user_content=prompt)
                elapsed = int((time.time() - t0) * 1000)
                print(f"  [P3 {idx}/{len(p2_files)}] {name} ✅ ({elapsed}ms) importance={parsed.get('final_importance','?')}")

                result = {
                    "contact_name": name,
                    "phase2_file": str(p2_file),
                    "evolution": parsed,
                    "elapsed_ms": elapsed,
                }
                _write_json(out_dir / f"{name}_evolved.json", result)
                return result

            except RateLimitError:
                print(f"  [P3 {idx}/{len(p2_files)}] {name} ⚠️ 429")
                await asyncio.sleep(30)
                return None
            except Exception as e:
                print(f"  [P3 {idx}/{len(p2_files)}] {name} ❌ {e}")
                return None

    tasks = [evolve_one(i + 1, f) for i, f in enumerate(p2_files)]
    raw = await asyncio.gather(*tasks)
    results = [r for r in raw if r is not None]
    print(f"[Phase 3] 完成 {len(results)}/{len(p2_files)}")

    # 按重要性排序
    results.sort(key=lambda r: r["evolution"].get("final_importance", 0), reverse=True)

    summary = {
        "phase": 3,
        "total": len(p2_files),
        "completed": len(results),
        "ranking": [
            {
                "rank": i + 1,
                "name": r["contact_name"],
                "importance": r["evolution"].get("final_importance", 0),
                "summary": r["evolution"].get("summary_200words", ""),
            }
            for i, r in enumerate(results)
        ],
    }
    _write_json(out_dir / "_phase3_ranking.json", summary)

    # 打印排名
    print("\n========== 最终重要性排名 TOP 20 ==========")
    for i, r in enumerate(results[:20]):
        ev = r["evolution"]
        print(f"  #{i+1:2d} {r['contact_name']:20s} 重要性={ev.get('final_importance','?'):.0f}")

    return results


# ═══════════════════════ CLI ═══════════════════════

async def main_async(args):
    client = ApiClient(
        base_url=args.base_url,
        token=args.token,
        model=args.model,
        max_output_tokens=args.max_tokens,
        api_style="openai",
        rpm_limit=args.rpm,
        rate_burst=1,
        request_timeout=180,
        connect_timeout=20,
    )
    await client.start()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.phase in (2, "all"):
            await phase2_extract_patterns(
                client, args.db,
                output_dir=output_dir,
                max_contacts=args.max_contacts,
                workers=args.workers,
            )

        if args.phase in (3, "all"):
            phase2_dir = output_dir / "phase2_patterns"
            await phase3_evolve(
                client, phase2_dir,
                db_path=args.db,
                output_dir=output_dir,
                workers=args.workers,
            )
    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(description="自我进化深度分析流水线")
    parser.add_argument("--phase", type=int, choices=[2, 3], default=2, help="运行哪个阶段")
    parser.add_argument("--db", default="data/scale/wechat-analysis-scale.sqlite3")
    parser.add_argument("--output", default="runs/deep_evolution")
    parser.add_argument("--model", default="custom/deepseek-v4-pro")
    parser.add_argument("--base-url", default="http://156.238.239.147:3000/v1")
    parser.add_argument("--token", default=os.environ.get("ANTHROPIC_AUTH_TOKEN", ""))
    parser.add_argument("--rpm", type=int, default=15)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--max-contacts", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()