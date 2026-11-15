"""v3 事件中心 · 深度分析阶段：对已确认事件做模型级深度推理，填充深度判断槽位。

对应 DEEP-REVIEW-SPEC 的「深度分析阶段」：
  1. 对已确认的高信号事件，收集完整事件包和跨联系人证据（已由 v3_event_pkg 完成）。
  2. 用模型生成主结论、备选解释、反证与沟通建议。
  3. 深度判断预填入复核卡，供用户低负担确认（复用 v3_event_review 的 finalize）。
  4. 记录每个事件包的 token、模型、提示词版本、证据覆盖率和失败情况。

模块职责（本文件）：
- build_deep_input：把事件包转成深度分析输入（完整片段 transcript + 证据 quote + 联系人 + 预填 facts），
  控制 token 规模；返回渲染文本与统计。
- DEEP_SYSTEM_PROMPT：深度分析指令 + 输出 JSON schema（5 深度槽位 + 反证 + 备选 + 置信度）。
- parse_deep_result：解析并校验 API 返回（evidence_id 必须回链到输入中的消息 id）。
- apply_deep_result：落库 _v3_event_deep_analysis（记录 token/模型/prompt 版本/证据覆盖），
  并把深度槽位回填到 _v3_event_candidates.analysis_profile_json。
- CLI：dryrun（0 API，展示每个事件的输入规模与 prompt 预览）/ analyze（真正调用，需用户授权）。

诚实边界：本模块在 dryrun 阶段 0 API；analyze 仅在用户明确授权后调用 DeepSeek。
稳定的人格/关系/沟通模式至少需要 3 个独立已确认事件支撑（见 v3_events.assess_stability），
单事件观察在 prompt 中被要求标注为「暂定」，不当作稳定结论。

运行：
  python -m src.v3_deep_analyzer dryrun runs/deep_p1 --db data/wechat-analysis-v3.sqlite3
  python -m src.v3_deep_analyzer analyze runs/deep_p1 --db data/wechat-analysis-v3.sqlite3
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .v3_events import DEEP_ANALYSIS_SLOTS, ensure_event_schema
from .v3_io import utc_now, write_json_atomic

#: 深度分析提示词版本（变更提示词时递增，去重键含此版本）
DEEP_PROMPT_VERSION = "deep-v1"

#: aiohttp 回退导入目录（只读，与 deepseek_v3_executor 一致；本机无 aiohttp）
VENDOR_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "09_未迁移脚本与运行依赖" / "runtime" / "vendor"
)

#: 深度分析结果 schema 版本
DEEP_RESULT_SCHEMA_VERSION = "deep-analysis-1.0"

#: 价值假设维度（DEEP-REVIEW-SPEC 改动一第 5 点）
VALUE_DIMENSIONS: tuple[str, ...] = (
    "growth", "cooperation", "emotional_reciprocity", "resource", "risk", "boundary",
)

# ─────────────────────────────────────────────────────────────────────────────
# 系统提示词
# ─────────────────────────────────────────────────────────────────────────────

DEEP_SYSTEM_PROMPT = """你是数据所有者蔡浩文的私人聊天记录深度分析器。你的任务是对一个「已确认事件」做深度分析，输出可核验的深度判断，而非复述原文。

## 输入说明
- 输入包含：事件元数据、确定性事实（facts）、联系人列表、若干聊天片段 transcript、证据节选。
- 每条消息形如 `[id=msg_...][时间][我/对方][类型] 内容`。`[我]` 是数据所有者本人，`[对方]` 是对面联系人。
- 所有引用必须使用消息行里的完整 `id`（msg_...），一字不差；禁止截断、改写或编造不存在的 id。
- PII 已替换为占位符（如 <PHONE:xxxx>），属正常，不要试图还原。

## 核心原则
1. 明确区分三层：**事实**（原文直接可见）/ **推断**（合理推测，标注 inferred）/ **未知**（证据不足，标注 unknown）。
2. 证据链：每条结论给出 evidence_ids；没有证据的项用 null 或省略。
3. 不编造：面谈、电话、群聊、未导出内容一律视为未知，不臆造。
4. 主动反证：必须给出至少一种备选解释，并列出不支持主结论的观察；没有反证的判断是确认偏误。
5. 稳定模式需谨慎：本输入只是单个事件；涉及「人格/关系/沟通模式」的结论只能视为**单事件观察**，不得上升为稳定模式。
6. 不做道德评判或操控性建议；沟通建议只服务于清晰、尊重和边界。
7. 不输出思维链、不解释过程，只输出最终 JSON。

## 权力结构分析（重点）
对每个联系人，显式分析关系中的权力动态：
- `balance`：权力是否对等（equal/unequal/unclear）；`dominant_side`：谁更主导（me/them/mutual/unclear）。
- 不对称维度：resource（资源）、information（信息）、emotional（情感）、decision（决策）、status（身份地位，如师生/学姐学弟/会长成员）。
- 只依据可观察证据（称谓、语气、谁发起、谁决定、谁求助、资源流向）；不臆测性别、不刻板化、不做道德评判。
- `gender_relevant` 只记录证据中明确出现的性别线索（如「学姐」「学长」称谓、代词），无明确证据时写 null。

## 输出格式
只输出一个 JSON 对象，结构如下（数组无内容时省略该字段，字符串无内容用 null）：

{
  "schema_version": "deep-analysis-1.0",
  "deep_hypotheses": [
    {
      "hypothesis": "发生了什么的主解释（≤120字）",
      "surface_purpose": "表面目的（≤40字）",
      "possible_underlying_purpose": "潜在目的（≤40字，无则null）",
      "status": "fact|inferred|unknown",
      "confidence": 0.8,
      "evidence_ids": ["msg_..."]
    }
  ],
  "alternative_hypotheses": [
    {"alternative": "另一种合理解释（≤80字）", "why_plausible": "为何合理（≤40字）", "evidence_ids": ["msg_..."]}
  ],
  "counter_evidence": [
    {"observation": "不支持主结论的观察（≤80字）", "evidence_ids": ["msg_..."]}
  ],
  "relationship_profile": [
    {
      "conversation_id": "输入中的 conversation_id",
      "display_name": "输入中的 display_name",
      "positioning": "关系定位（≤30字）",
      "event_role": "事件中角色（≤30字）",
      "reciprocity": "互惠/资源结构（≤40字）",
      "power_dynamic": {
        "balance": "equal|unequal|unclear",
        "dominant_side": "me|them|mutual|unclear",
        "asymmetry_dimensions": ["resource","information","emotional","decision","status"],
        "gender_relevant": "基于可观察证据的性别相关线索（≤40字，无则null，不刻板化）",
        "evidence_ids": ["msg_..."]
      },
      "user_expectation": "用户可能的期待（≤40字）",
      "other_expectation": "对方可能的期待（≤40字）",
      "evidence_ids": ["msg_..."]
    }
  ],
  "value_assumptions": [
    {"dimension": "growth|cooperation|emotional_reciprocity|resource|risk|boundary", "assumption": "价值假设（≤60字）", "evidence_ids": ["msg_..."]}
  ],
  "communication_advice": [
    {"advice": "下一步沟通建议（≤60字）", "rationale": "理由（≤40字）", "respects_boundary": true}
  ],
  "confidence": 0.8,
  "fact_status": "inferred",
  "needs_user_confirmation": ["需要用户确认的项（≤40字）"]
}

## 硬性要求
- `relationship_profile` 必须覆盖输入中的**每个**联系人（conversation_id 与 display_name 与输入一致）。
- `evidence_ids` 只能引用输入中出现过的 `msg_...`；不得出现输入中不存在的 id。
- 只输出 JSON 对象，不要 Markdown 代码块、不要任何解释性文本。
"""


# ─────────────────────────────────────────────────────────────────────────────
# 输入构建
# ─────────────────────────────────────────────────────────────────────────────

def _collect_facts(pkg: dict) -> list[dict]:
    """从事件包提取确定性 facts（兼容单候选与 merged 多候选结构）。"""
    cand = pkg.get("candidate") or {}
    facts: list[dict] = []
    if cand.get("merged"):
        for c in cand.get("candidates", []):
            prof = (c or {}).get("analysis_profile") or {}
            facts.extend(prof.get("facts") or [])
    else:
        prof = cand.get("analysis_profile") or {}
        facts.extend(prof.get("facts") or [])
    return facts


def _render_transcript(pkg: dict) -> str:
    """按 会话 + 时间 顺序渲染完整片段 transcript，保留消息 id 回链。"""
    segs = sorted(
        pkg.get("segments", []),
        key=lambda s: (s.get("conversation_id") or "", s.get("start_ts") or 0),
    )
    blocks = []
    for s in segs:
        tag = "信号片段" if s.get("is_signal_segment") else "上下文片段"
        head = (
            f"[SEG {s.get('segment_id')}] {tag} · {s.get('display_name') or s.get('conversation_id')} · "
            f"{s.get('message_count')} 条消息"
        )
        blocks.append(head + "\n" + (s.get("transcript") or "").strip())
    return "\n\n".join(blocks)


def _render_contacts(pkg: dict) -> str:
    rows = []
    for c in pkg.get("contacts", []):
        rows.append(
            f"- {c.get('display_name') or c.get('conversation_id')} "
            f"(conversation_id={c.get('conversation_id')}, 消息数={c.get('message_count')})"
        )
    return "\n".join(rows) if rows else "（无联系人）"


def _render_facts(facts: list[dict]) -> str:
    if not facts:
        return "（无确定性事实）"
    rows = []
    for f in facts:
        st = f.get("status", "unknown")
        conf = f.get("confidence")
        conf_s = "" if conf is None else f" [置信度{conf:.0%}]"
        rows.append(f"- [{st}]{conf_s} {f.get('statement', '')}")
    return "\n".join(rows)


def build_deep_input(pkg: dict) -> tuple[str, dict]:
    """把事件包渲染成深度分析 user_content，返回 (文本, 统计)。

    统计含 input_chars 与 estimated_input_tokens（char 保守估算，中文实际略低）。
    """
    ev = pkg.get("event") or {}
    facts = _collect_facts(pkg)
    transcript = _render_transcript(pkg)
    contacts = _render_contacts(pkg)
    evidence = pkg.get("evidence") or []
    evidence_lines = []
    for e in evidence:
        evidence_lines.append(
            f"[{e.get('evidence_id')}] {e.get('quote')} (signal={','.join(e.get('signal_types') or [])})"
        )

    user = (
        f"# 事件\n标题：{ev.get('title')}\n"
        f"event_id：{ev.get('event_id')}\n"
        f"时间范围：{ev.get('start_ts')} ~ {ev.get('end_ts')}\n"
        f"保留建议：{ev.get('keep_recommendation')}\n"
        f"事件备注：{ev.get('note') or '（无）'}\n\n"
        f"# 确定性事实\n{_render_facts(facts)}\n\n"
        f"# 联系人\n{contacts}\n\n"
        f"# 证据节选（{len(evidence)} 条）\n" + "\n".join(evidence_lines) + "\n\n"
        f"# 完整聊天片段\n{transcript}\n"
    )

    input_chars = len(user)
    stats = {
        "input_chars": input_chars,
        "estimated_input_tokens": input_chars,
        "segment_count": len(pkg.get("segments", [])),
        "evidence_count": len(evidence),
        "contact_count": len(pkg.get("contacts", [])),
        "fact_count": len(facts),
    }
    return user, stats


# ─────────────────────────────────────────────────────────────────────────────
# 结果解析与校验
# ─────────────────────────────────────────────────────────────────────────────

def _input_msg_ids(pkg: dict) -> set[str]:
    """收集输入中出现过的全部消息 id（用于 evidence_id 回链校验）。"""
    ids: set[str] = set()
    for s in pkg.get("segments", []):
        for tok in (s.get("transcript") or "").split("id=")[1:]:
            mid = tok.split("]")[0]
            if mid.startswith("msg_"):
                ids.add(mid)
    for e in pkg.get("evidence", []):
        ids.add(e.get("message_id", ""))
    ids.discard("")
    return ids


def _walk_evidence_ids(obj: Any, out: set[str]) -> None:
    """递归收集结果里所有 evidence_ids / evidence_id 字段。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("evidence_ids", "evidence_id") and isinstance(v, str):
                out.add(v)
            elif k == "evidence_ids" and isinstance(v, list):
                out.update(x for x in v if isinstance(x, str))
            else:
                _walk_evidence_ids(v, out)
    elif isinstance(obj, list):
        for it in obj:
            _walk_evidence_ids(it, out)


def parse_deep_result(text: str, pkg: dict) -> dict:
    """解析 API 返回并校验：schema_version 与 evidence_id 回链。"""
    from .v3_api import parse_json  # 局部导入，避免 dryrun 阶段强依赖 aiohttp
    result = parse_json(text)
    if not isinstance(result, dict):
        raise ValueError("深度分析结果必须是 JSON 对象")
    if result.get("schema_version") != DEEP_RESULT_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version 不匹配：期望 {DEEP_RESULT_SCHEMA_VERSION}，得到 {result.get('schema_version')}"
        )
    # 校验槽位键存在（缺失则视为未填充，保持空）
    for slot in DEEP_ANALYSIS_SLOTS:
        result.setdefault(slot, [] if slot != "relationship_profile" else None)
    # 证据回链校验
    valid_ids = _input_msg_ids(pkg)
    cited: set[str] = set()
    _walk_evidence_ids(result, cited)
    bad = cited - valid_ids
    if bad:
        raise ValueError(f"深度分析结果引用了输入中不存在的消息 id: {sorted(bad)[:5]}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 落库
# ─────────────────────────────────────────────────────────────────────────────

DEEP_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS _v3_event_deep_analysis (
  event_id TEXT PRIMARY KEY,
  package_schema_version TEXT,
  prompt_version TEXT,
  model TEXT,
  result_json TEXT,              -- 深度分析结果（5 槽位 + 反证 + 备选 + 置信度）
  confidence REAL,
  fact_status TEXT,
  input_chars INTEGER,
  estimated_input_tokens INTEGER,
  input_tokens INTEGER,
  output_tokens INTEGER,
  evidence_coverage REAL,        -- 引用证据 id 去重数 / 输入消息 id 数
  status TEXT,                   -- success / failed
  error TEXT,
  created_at TEXT
);
"""


def ensure_deep_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(DEEP_SCHEMA_SQL)
    conn.commit()


def _evidence_coverage(result: dict, pkg: dict) -> float:
    valid = _input_msg_ids(pkg)
    cited: set[str] = set()
    _walk_evidence_ids(result, cited)
    cited = cited & valid
    if not valid:
        return 0.0
    return round(len(cited) / len(valid), 4)


def _backfill_profile(conn: sqlite3.Connection, event_id: str, result: dict) -> None:
    """把深度槽位回填到 _v3_event_candidates.analysis_profile_json。

    只更新该候选的 analysis_status/confidence/analysis_profile_json，不改历史表。
    """
    row = conn.execute(
        "SELECT source_candidate_ids FROM _v3_event_judgments WHERE event_id=?", (event_id,)
    ).fetchone()
    if not row:
        return
    try:
        src_ids = json.loads(row[0]) if row[0] else []
    except (json.JSONDecodeError, TypeError):
        src_ids = []
    for cid in src_ids:
        cur = conn.execute(
            "SELECT analysis_profile_json FROM _v3_event_candidates WHERE candidate_id=?", (cid,)
        ).fetchone()
        if not cur:
            continue
        try:
            prof = json.loads(cur[0]) if cur[0] else {}
        except (json.JSONDecodeError, TypeError):
            prof = {}
        if not isinstance(prof, dict):
            prof = {}
        for slot in DEEP_ANALYSIS_SLOTS:
            if slot in result:
                prof[slot] = result[slot]
        prof["counter_evidence"] = result.get("counter_evidence") or []
        prof["confidence"] = result.get("confidence")
        prof["analysis_status"] = "analyzed"
        conn.execute(
            "UPDATE _v3_event_candidates SET analysis_profile_json=?, confidence=?, "
            "analysis_status='analyzed', updated_at=? WHERE candidate_id=?",
            (json.dumps(prof, ensure_ascii=False), result.get("confidence"), utc_now(), cid),
        )


def apply_deep_result(
    db: str,
    event_id: str,
    pkg: dict,
    result: dict,
    meta: Optional[dict] = None,
) -> dict:
    """落库深度分析结果到 _v3_event_deep_analysis，并回填候选槽位。返回统计。"""
    meta = meta or {}
    conn = sqlite3.connect(db, timeout=30)
    try:
        ensure_event_schema(conn)
        ensure_deep_schema(conn)
        coverage = _evidence_coverage(result, pkg)
        conn.execute(
            """
            INSERT INTO _v3_event_deep_analysis(
              event_id, package_schema_version, prompt_version, model, result_json,
              confidence, fact_status, input_chars, estimated_input_tokens,
              input_tokens, output_tokens, evidence_coverage, status, error, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(event_id) DO UPDATE SET
              result_json=excluded.result_json, confidence=excluded.confidence,
              fact_status=excluded.fact_status, input_chars=excluded.input_chars,
              estimated_input_tokens=excluded.estimated_input_tokens,
              input_tokens=excluded.input_tokens, output_tokens=excluded.output_tokens,
              evidence_coverage=excluded.evidence_coverage, status=excluded.status,
              error=excluded.error, model=excluded.model,
              prompt_version=excluded.prompt_version,
              package_schema_version=excluded.package_schema_version
            """,
            (
                event_id,
                pkg.get("schema_version"),
                DEEP_PROMPT_VERSION,
                meta.get("model"),
                json.dumps(result, ensure_ascii=False),
                result.get("confidence"),
                result.get("fact_status"),
                meta.get("input_chars"),
                meta.get("estimated_input_tokens"),
                meta.get("input_tokens"),
                meta.get("output_tokens"),
                coverage,
                "success",
                None,
                utc_now(),
            ),
        )
        _backfill_profile(conn, event_id, result)
        conn.commit()
    finally:
        conn.close()
    return {
        "event_id": event_id,
        "evidence_coverage": coverage,
        "confidence": result.get("confidence"),
        "fact_status": result.get("fact_status"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _load_packages(outdir: Path) -> dict[str, dict]:
    events_dir = outdir / "events"
    if not events_dir.exists():
        raise FileNotFoundError(f"未找到事件包目录: {events_dir}（先运行 v3_event_pkg build）")
    pkgs: dict[str, dict] = {}
    for f in sorted(events_dir.glob("*.package.json")):
        pkg = json.loads(f.read_text(encoding="utf-8"))
        pkgs[pkg["event"]["event_id"]] = pkg
    return pkgs


def cmd_dryrun(args: argparse.Namespace) -> int:
    pkgs = _load_packages(Path(args.outdir))
    if not pkgs:
        print("（无事件包）")
        return 0
    total_chars = 0
    print(f"=== 深度分析 dry-run（0 API）· {len(pkgs)} 个事件 ===\n")
    for eid, pkg in pkgs.items():
        user, stats = build_deep_input(pkg)
        total_chars += stats["input_chars"]
        print(
            f"{eid} {pkg['event']['title']}: "
            f"{stats['segment_count']}片段/{stats['evidence_count']}证据/"
            f"{stats['contact_count']}联系人/{stats['fact_count']}事实 "
            f"-> {stats['input_chars']}字符 ~{stats['estimated_input_tokens']} tok(估)"
        )
    print(f"\n合计输入字符：{total_chars}，估算 token：{total_chars}")
    print("（analyze 会真正调用 DeepSeek，消耗 API Token；请先确认预算）")
    if args.preview:
        eid0 = next(iter(pkgs))
        user, _ = build_deep_input(pkgs[eid0])
        print(f"\n===== 输入预览（{eid0}，前 2000 字符）=====\n")
        print(user[:2000])
    return 0


async def _analyze_all(args: argparse.Namespace) -> None:
    from .v3_api import ApiClient

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    model = args.model
    if not base_url or not token:
        raise RuntimeError("缺少 ANTHROPIC_BASE_URL 或 ANTHROPIC_AUTH_TOKEN 环境变量")
    pkgs = _load_packages(Path(args.outdir))
    client = ApiClient(
        base_url, token, model, max_output_tokens=args.max_tokens,
        vendor_dir=VENDOR_DIR, api_style=getattr(args, "api_style", "anthropic"),
        rpm_limit=getattr(args, "rpm_limit", None),
    )
    await client.start()
    try:
        for eid, pkg in pkgs.items():
            user, stats = build_deep_input(pkg)
            print(f"[analyze] {eid} {pkg['event']['title']} -> {stats['input_chars']} 字符 ...")
            try:
                result, in_tok, out_tok = await client.call(DEEP_SYSTEM_PROMPT, user)
                summary = apply_deep_result(args.db, eid, pkg, result, {
                    "model": model, "input_chars": stats["input_chars"],
                    "estimated_input_tokens": stats["estimated_input_tokens"],
                    "input_tokens": in_tok, "output_tokens": out_tok,
                })
                print(f"  ok conf={summary['confidence']} 覆盖={summary['evidence_coverage']:.1%} "
                      f"in={in_tok} out={out_tok}")
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED: {type(exc).__name__}: {exc}")
                conn = sqlite3.connect(args.db, timeout=30)
                try:
                    ensure_deep_schema(conn)
                    conn.execute(
                        "INSERT INTO _v3_event_deep_analysis(event_id, prompt_version, model, "
                        "status, error, created_at) VALUES (?,?,?,?,?,?) "
                        "ON CONFLICT(event_id) DO UPDATE SET status='failed', error=excluded.error",
                        (eid, DEEP_PROMPT_VERSION, model, "failed", str(exc)[:500], utc_now()),
                    )
                    conn.commit()
                finally:
                    conn.close()
    finally:
        await client.close()


def cmd_analyze(args: argparse.Namespace) -> int:
    import asyncio
    print("⚠ 即将调用 DeepSeek API（消耗 Token）。确认预算后继续。")
    asyncio.run(_analyze_all(args))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="v3 事件中心：深度分析（模型级深度推理）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_d = sub.add_parser("dryrun", help="0 API：构建输入并展示规模")
    p_d.add_argument("outdir", default="runs/deep_p1")
    p_d.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_d.add_argument("--preview", action="store_true", help="打印第一个事件的输入预览")
    p_d.set_defaults(func=cmd_dryrun)

    p_a = sub.add_parser("analyze", help="真正调用 DeepSeek（需授权 + 环境变量）")
    p_a.add_argument("outdir", default="runs/deep_p1")
    p_a.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_a.add_argument("--model", default="deepseek-v4-flash")
    p_a.add_argument("--max-tokens", type=int, default=8192)
    p_a.add_argument("--api-style", choices=["anthropic", "openai"], default="anthropic",
                     help="openai = NVIDIA 等 OpenAI 兼容端点")
    p_a.add_argument("--rpm-limit", type=float, default=None, help="全局限速（次/分钟）")
    p_a.set_defaults(func=cmd_analyze)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
