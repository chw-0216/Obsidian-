"""v3 事件中心 · 深度分析阶段：为已确认事件构建「完整聊天包」。

DEEP-REVIEW-SPEC 深度分析阶段第 1 步：对已确认的高信号事件，收集完整事件包和跨联系人证据。

本模块（0 API，只读）：
- 输入：`_v3_event_judgments.event_id`（最终事件，可能为原候选 evc_* 或拆分产物 evs_*）。
- 对每个事件检索：
  - 事件元数据（judgment）；
  - 源候选元数据 + 深度预填档案（analysis_profile，含确定性 facts 与空深度槽位）；
  - 全部证据（_v3_event_evidence，quote 为信号消息节选，带 signal_types/match_terms，可回链 message_id）；
  - 联系人（_v3_event_contacts）；
  - 完整聊天包：事件时间窗口内、相关会话中的全部片段 transcript（含信号片段+上下文片段，
    保留 segment_id / conversation_id / 消息时间戳 回链）。
- 输出：每个事件一个 package JSON + 汇总清单（含规模与 token 估算）。

诚实边界：本模块不调用 API、不生成任何模型结论；输出仅供深度分析调用方作为输入，
并在包内标注 estimated_input_tokens（按 char 保守估算，供 token 预算核对）。

运行：
  python -m src.v3_event_pkg build --db data/wechat-analysis-v3.sqlite3 \
      --events evc_a5d9c3c5dbbb6caf,evc_59a505bbba79b7e8,evc_93130b1552a25445 \
      --outdir runs/deep_p1
  python -m src.v3_event_pkg build --db data/wechat-analysis-v3.sqlite3 --outdir runs/deep_p1
      # 无 --events 时自动取全部 keep 的最终事件
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from .v3_io import utc_now, write_json_atomic

#: 完整聊天包 schema 版本
PKG_SCHEMA_VERSION = "deep-event-package-1.0"

#: 深度分析槽位键（与 v3_events.DEEP_ANALYSIS_SLOTS 一致，供调用方填充）
DEEP_ANALYSIS_SLOTS: tuple[str, ...] = (
    "deep_hypotheses", "alternative_hypotheses", "relationship_profile",
    "value_assumptions", "communication_advice",
)


def _utc_cn_now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def _iso(ts: Optional[int]) -> Optional[str]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        return str(ts)


def _db_connect(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# 事件 → 源候选解析
# ─────────────────────────────────────────────────────────────────────────────

def resolve_source_candidates(conn: sqlite3.Connection, event_id: str) -> list[str]:
    """从 _v3_event_judgments 解析 source_candidate_ids；失败时回退为 event_id 本身。"""
    if conn.row_factory is None:
        conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT source_candidate_ids FROM _v3_event_judgments WHERE event_id=?", (event_id,)
    ).fetchone()
    if row and row["source_candidate_ids"]:
        try:
            ids = json.loads(row["source_candidate_ids"])
            return [x for x in ids if isinstance(x, str) and x]
        except (json.JSONDecodeError, TypeError):
            return [event_id]
    return [event_id]


# ─────────────────────────────────────────────────────────────────────────────
# 检索：片段 transcript（完整聊天包核心）
# ─────────────────────────────────────────────────────────────────────────────

def _involved_conversations(conn: sqlite3.Connection, candidate_ids: list[str]) -> list[str]:
    """事件涉及的会话 = 证据所在会话 ∪ 联系人登记会话。

    只取 evidence 会漏掉「联系人表已登记但无直接信号证据」的会话（如只出现在
    联系人盘点、无独立信号消息的会话），导致完整聊天包缺块；合并两个来源可保证
    深度分析不会漏掉事件的相关会话。
    """
    ph = ",".join("?" * len(candidate_ids))
    rows = conn.execute(
        f"""
        SELECT DISTINCT conversation_id FROM _v3_event_evidence
        WHERE candidate_id IN ({ph}) AND conversation_id IS NOT NULL
        UNION
        SELECT DISTINCT conversation_id FROM _v3_event_contacts
        WHERE candidate_id IN ({ph}) AND conversation_id IS NOT NULL
        """,
        candidate_ids * 2,
    ).fetchall()
    return [r["conversation_id"] for r in rows]


def _signal_segment_ids(conn: sqlite3.Connection, candidate_ids: list[str]) -> set[str]:
    ph = ",".join("?" * len(candidate_ids))
    rows = conn.execute(
        f"SELECT DISTINCT segment_id FROM _v3_event_evidence "
        f"WHERE candidate_id IN ({ph}) AND segment_id IS NOT NULL",
        candidate_ids,
    ).fetchall()
    return {r["segment_id"] for r in rows}


def retrieve_segments(
    conn: sqlite3.Connection,
    conv_ids: list[str],
    start_ts: int,
    end_ts: int,
    signal_seg_ids: set[str],
) -> list[dict]:
    """取事件窗口内相关会话的全部片段（含上下文片段），保留回链字段。"""
    if not conv_ids:
        return []
    ph = ",".join("?" * len(conv_ids))
    rows = conn.execute(
        f"""
        SELECT s.id, s.conversation_id, s.ordinal, s.start_ts, s.end_ts,
               s.message_count, s.char_count, s.transcript
        FROM segments s
        WHERE s.conversation_id IN ({ph}) AND s.start_ts <= ? AND s.end_ts >= ?
        ORDER BY s.conversation_id, s.start_ts
        """,
        conv_ids + [end_ts, start_ts],
    ).fetchall()
    names = {
        row["id"]: row["display_name"]
        for row in conn.execute(
            "SELECT id, display_name FROM conversations WHERE id IN ({})".format(
                ",".join("?" * len(conv_ids))
            ),
            conv_ids,
        )
    }
    out = []
    for r in rows:
        out.append({
            "segment_id": r["id"],
            "conversation_id": r["conversation_id"],
            "display_name": names.get(r["conversation_id"]),
            "ordinal": r["ordinal"],
            "start_ts": r["start_ts"],
            "end_ts": r["end_ts"],
            "message_count": r["message_count"],
            "char_count": r["char_count"],
            "is_signal_segment": r["id"] in signal_seg_ids,
            "transcript": r["transcript"] or "",
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 检索：证据 / 联系人 / 元数据
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_evidence(conn: sqlite3.Connection, candidate_ids: list[str]) -> list[dict]:
    ph = ",".join("?" * len(candidate_ids))
    rows = conn.execute(
        f"""
        SELECT evidence_id, candidate_id, message_id, segment_id, conversation_id,
               create_ts, quote, signal_types, match_terms
        FROM _v3_event_evidence WHERE candidate_id IN ({ph})
        ORDER BY create_ts
        """,
        candidate_ids,
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "evidence_id": r["evidence_id"],
            "candidate_id": r["candidate_id"],
            "message_id": r["message_id"],
            "segment_id": r["segment_id"],
            "conversation_id": r["conversation_id"],
            "create_ts": r["create_ts"],
            "create_time": _iso(r["create_ts"]),
            "quote": r["quote"] or "",
            "signal_types": json.loads(r["signal_types"]) if r["signal_types"] else [],
            "match_terms": json.loads(r["match_terms"]) if r["match_terms"] else [],
        })
    return out


def retrieve_contacts(conn: sqlite3.Connection, candidate_ids: list[str]) -> list[dict]:
    ph = ",".join("?" * len(candidate_ids))
    rows = conn.execute(
        f"""
        SELECT conversation_id, display_name, message_count, role_hint, role_certainty
        FROM _v3_event_contacts WHERE candidate_id IN ({ph})
        ORDER BY message_count DESC
        """,
        candidate_ids,
    ).fetchall()
    return [dict(r) for r in rows]


def retrieve_candidate(conn: sqlite3.Connection, candidate_id: str) -> dict:
    r = conn.execute(
        "SELECT * FROM _v3_event_candidates WHERE candidate_id=?", (candidate_id,)
    ).fetchone()
    if not r:
        return {}
    d = dict(r)
    # 解析 JSON 列，便于消费方直接使用
    for col in ("strong_entities", "project_terms", "task_categories",
                "time_ref_texts", "resolved_dates", "candidate_json"):
        if d.get(col):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    if d.get("analysis_profile_json"):
        try:
            d["analysis_profile"] = json.loads(d["analysis_profile_json"])
        except (json.JSONDecodeError, TypeError):
            d["analysis_profile"] = None
    return d


def retrieve_judgment(conn: sqlite3.Connection, event_id: str) -> dict:
    r = conn.execute(
        "SELECT * FROM _v3_event_judgments WHERE event_id=?", (event_id,)
    ).fetchone()
    return dict(r) if r else {}


# ─────────────────────────────────────────────────────────────────────────────
# 包构建
# ─────────────────────────────────────────────────────────────────────────────

def estimate_input_tokens(pkg: dict) -> int:
    """按 char 保守估算完整包输入 token（中文约 1 字/token；片段含元数据前缀，实际略高）。

    只统计会进提示词正文的部分：各片段 transcript + 证据 quote + 元数据 json。
    """
    n = 0
    for seg in pkg.get("segments", []):
        n += len(seg.get("transcript") or "")
    for ev in pkg.get("evidence", []):
        n += len(ev.get("quote") or "")
    meta = json.dumps(
        {
            "event": pkg.get("event"),
            "candidate": pkg.get("candidate"),
            "contacts": pkg.get("contacts"),
            "facts": (pkg.get("candidate") or {}).get("analysis_profile", {}).get("facts"),
        },
        ensure_ascii=False,
    )
    n += len(meta)
    return int(n)


def build_event_package(db: str, event_id: str) -> dict:
    """为单个最终事件构建完整聊天包（0 API）。"""
    conn = _db_connect(db)
    try:
        judgment = retrieve_judgment(conn, event_id)
        if not judgment:
            raise ValueError(f"event_id 不在 _v3_event_judgments 中: {event_id}")
        source_ids = resolve_source_candidates(conn, event_id)

        candidates = [retrieve_candidate(conn, cid) for cid in source_ids]
        candidates = [c for c in candidates if c]
        if not candidates:
            raise ValueError(f"源候选不存在: {source_ids}")

        # 事件时间窗 = judgment 时间或首候选时间
        start_ts = judgment.get("start_ts") or candidates[0].get("start_ts")
        end_ts = judgment.get("end_ts") or candidates[0].get("end_ts")

        conv_ids = _involved_conversations(conn, source_ids)
        signal_seg_ids = _signal_segment_ids(conn, source_ids)
        segments = retrieve_segments(conn, conv_ids, start_ts, end_ts, signal_seg_ids)
        evidence = retrieve_evidence(conn, source_ids)
        contacts = retrieve_contacts(conn, source_ids)

        pkg = {
            "schema_version": PKG_SCHEMA_VERSION,
            "generated_at": _utc_cn_now(),
            "event": {
                "event_id": judgment.get("event_id"),
                "title": judgment.get("title"),
                "start_ts": start_ts,
                "end_ts": end_ts,
                "time_certainty": judgment.get("time_certainty"),
                "keep_recommendation": judgment.get("keep_recommendation"),
                "note": judgment.get("note"),
                "source_candidate_ids": source_ids,
            },
            "candidate": candidates[0] if len(candidates) == 1 else {
                "merged": True,
                "candidate_ids": source_ids,
                "candidates": candidates,
            },
            "contacts": contacts,
            "evidence": evidence,
            "segments": segments,
            "stats": {
                "conversation_count": len(conv_ids),
                "segment_count": len(segments),
                "signal_segment_count": len(signal_seg_ids),
                "message_count_in_segments": sum(s["message_count"] for s in segments),
                "evidence_count": len(evidence),
                "char_count_total": sum(s["char_count"] or 0 for s in segments),
                "estimated_input_tokens": 0,  # 下方计算
            },
        }
        pkg["stats"]["estimated_input_tokens"] = estimate_input_tokens(pkg)
        return pkg
    finally:
        conn.close()


def build_all_events(db: str, event_ids: Optional[list[str]] = None) -> list[dict]:
    """构建多个事件包；未指定时自动取全部 keep 的最终事件。"""
    conn = _db_connect(db)
    try:
        if event_ids:
            ids = event_ids
        else:
            rows = conn.execute(
                "SELECT event_id FROM _v3_event_judgments "
                "WHERE keep_recommendation='keep' ORDER BY created_at"
            ).fetchall()
            ids = [r["event_id"] for r in rows]
    finally:
        conn.close()
    return [build_event_package(db, eid) for eid in ids]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def cmd_build(args: argparse.Namespace) -> int:
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    events_dir = out_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    pkgs = build_all_events(args.db, args.events)
    summary = []
    for pkg in pkgs:
        fname = pkg["event"]["event_id"] + ".package.json"
        write_json_atomic(events_dir / fname, pkg)
        st = pkg["stats"]
        summary.append({
            "event_id": pkg["event"]["event_id"],
            "title": pkg["event"]["title"],
            "file": str(events_dir / fname),
            **st,
        })
    manifest = {
        "schema_version": PKG_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "count": len(pkgs),
        "events": summary,
    }
    write_json_atomic(out_dir / "event_packages_summary.json", manifest)
    write_json_atomic(out_dir / "event_packages_summary.pretty.json", manifest)

    print(f"[event_pkg] 已构建 {len(pkgs)} 个完整聊天包 -> {events_dir}")
    for s in summary:
        print(
            f"  {s['event_id']} {s['title']}: "
            f"{s['segment_count']}片段/{s['conversation_count']}会话/"
            f"{s['evidence_count']}证据/{s['char_count_total']}字符 "
            f"~{s['estimated_input_tokens']} tok(估)"
        )
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="v3 事件中心：构建深度分析完整聊天包（0 API）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_b = sub.add_parser("build", help="构建事件完整聊天包")
    p_b.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_b.add_argument("--events", default=None,
                     help="逗号分隔 event_id；缺省=全部 keep 事件")
    p_b.add_argument("--outdir", default="runs/deep_p1")
    p_b.set_defaults(func=cmd_build)

    args = ap.parse_args()
    args.events = [e.strip() for e in args.events.split(",") if e.strip()] if args.events else None
    args.func(args)


if __name__ == "__main__":
    main()
