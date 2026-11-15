"""v3 历史标注归一化：把 annotations / aggressive_annotations / aggressive_message_annotations
三套历史 schema 归一成版本化 _v3_hist_* 备查表（0 API、只读源表、幂等 upsert）。

用途：把旧管线的 227 段标注放到一个可查询的统一结构里，供备查与抽样参照；
不覆盖任何历史表，不并入 v3_annotations 主流程。

运行：python -m src.v3_hist --db <path>
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

V3_HIST_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS _v3_hist_segments (
  segment_id TEXT PRIMARY KEY,
  source_table TEXT NOT NULL,
  schema_version TEXT,
  model TEXT,
  conversation_id TEXT,
  message_count INTEGER,
  char_count INTEGER,
  importance INTEGER,            -- 旧管线 result_json 原样保留（annotations 1.0 输出 0，勿当缺失）
  overall_confidence REAL,
  entity_count INTEGER DEFAULT 0,
  event_count INTEGER DEFAULT 0,
  relationship_signal_count INTEGER DEFAULT 0,
  key_message_count INTEGER DEFAULT 0,
  result_json TEXT,              -- 原始结果，保留备查
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS _v3_hist_messages (
  evidence_id TEXT PRIMARY KEY,
  segment_id TEXT NOT NULL,
  source_table TEXT NOT NULL,
  schema_version TEXT,
  content_function TEXT,
  topic TEXT,
  speech_act TEXT,
  intent TEXT,
  is_request INTEGER DEFAULT 0,
  is_commitment INTEGER DEFAULT 0,
  is_boundary INTEGER DEFAULT 0,
  people_mentioned TEXT,
  places_mentioned TEXT,
  projects_mentioned TEXT,
  times_mentioned TEXT,
  events_mentioned TEXT,
  observable_tone TEXT,
  inferred_emotion TEXT,
  inferred_need TEXT,
  relationship_signal TEXT,
  communication_behavior TEXT,
  expression_style TEXT,
  memory_candidate TEXT,
  ambiguity_notes TEXT,
  confidence REAL,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_v3_hist_msg_seg ON _v3_hist_messages(segment_id);
"""


def ensure_v3_hist_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(V3_HIST_SCHEMA_SQL)
    conn.commit()


def _load(rj: Any) -> dict:
    if not rj:
        return {}
    try:
        o = json.loads(rj)
        return o if isinstance(o, dict) else {}
    except json.JSONDecodeError:
        return {}


def _importance_or_none(v: Any) -> Optional[int]:
    """旧管线的 importance 原样归一：缺失→NULL，数值→int，非法→NULL。"""
    if isinstance(v, bool) or v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _len_or_zero(v: Any) -> int:
    return len(v) if isinstance(v, list) else 0


def _norm_segments(conn: sqlite3.Connection) -> list[dict]:
    seg_meta: dict[str, tuple] = {
        sid: (conv, mc, cc)
        for sid, conv, mc, cc in conn.execute(
            "SELECT id, conversation_id, message_count, char_count FROM segments"
        )
    }
    rows: list[dict] = []

    def push(src: str, sid: str, sv: Any, model: Any, rj: Any, created: Any) -> None:
        o = _load(rj)
        conv, mc, cc = seg_meta.get(sid, (None, None, None))
        rows.append({
            "segment_id": sid,
            "source_table": src,
            "schema_version": sv,
            "model": model,
            "conversation_id": conv,
            "message_count": mc,
            "char_count": cc,
            "importance": _importance_or_none(o.get("importance")),
            "overall_confidence": _as_float(o.get("overall_confidence")),
            "entity_count": _len_or_zero(o.get("entities")),
            "event_count": _len_or_zero(o.get("events")),
            "relationship_signal_count": _len_or_zero(o.get("relationship_signals")),
            "key_message_count": _len_or_zero(o.get("messages")),
            "result_json": rj,
            "created_at": created,
        })

    for sid, sv, model, rj, created in conn.execute(
        "SELECT segment_id, schema_version, model, result_json, created_at FROM annotations"
    ):
        push("annotations", sid, sv, model, rj, created)
    for sid, sv, model, rj, created in conn.execute(
        "SELECT segment_id, schema_version, model, result_json, created_at FROM aggressive_annotations"
    ):
        push("aggressive_annotations", sid, sv, model, rj, created)
    return rows


def _norm_messages(conn: sqlite3.Connection) -> list[dict]:
    # 用 aggressive_annotations 的 schema_version 归一到消息行，保持父子一致
    seg_sv = dict(conn.execute("SELECT segment_id, schema_version FROM aggressive_annotations"))
    cols = [d[1] for d in conn.execute("PRAGMA table_info(aggressive_message_annotations)")]
    rows: list[dict] = []
    for row in conn.execute("SELECT * FROM aggressive_message_annotations"):
        d = dict(zip(cols, row))
        rows.append({
            "evidence_id": d.get("evidence_id"),
            "segment_id": d.get("segment_id"),
            "source_table": "aggressive_message_annotations",
            "schema_version": seg_sv.get(d.get("segment_id")),
            "content_function": d.get("content_function"),
            "topic": d.get("topic"),
            "speech_act": d.get("speech_act"),
            "intent": d.get("intent"),
            "is_request": 1 if d.get("is_request") else 0,
            "is_commitment": 1 if d.get("is_commitment") else 0,
            "is_boundary": 1 if d.get("is_boundary") else 0,
            "people_mentioned": d.get("people_mentioned"),
            "places_mentioned": d.get("places_mentioned"),
            "projects_mentioned": d.get("projects_mentioned"),
            "times_mentioned": d.get("times_mentioned"),
            "events_mentioned": d.get("events_mentioned"),
            "observable_tone": d.get("observable_tone"),
            "inferred_emotion": d.get("inferred_emotion"),
            "inferred_need": d.get("inferred_need"),
            "relationship_signal": d.get("relationship_signal"),
            "communication_behavior": d.get("communication_behavior"),
            "expression_style": d.get("expression_style"),
            "memory_candidate": d.get("memory_candidate"),
            "ambiguity_notes": d.get("ambiguity_notes"),
            "confidence": _as_float(d.get("confidence")),
            "created_at": d.get("created_at"),
        })
    return rows


def build_v3_hist(conn: sqlite3.Connection) -> dict[str, int]:
    """读历史表 → 归一 → 幂等写入 _v3_hist_*。返回统计。"""
    ensure_v3_hist_schema(conn)
    segs = _norm_segments(conn)
    msgs = _norm_messages(conn)

    seg_cols = [
        "segment_id", "source_table", "schema_version", "model", "conversation_id",
        "message_count", "char_count", "importance", "overall_confidence",
        "entity_count", "event_count", "relationship_signal_count",
        "key_message_count", "result_json", "created_at",
    ]
    for s in segs:
        conn.execute(
            f"""
            INSERT INTO _v3_hist_segments({','.join(seg_cols)})
            VALUES ({','.join('?' * len(seg_cols))})
            ON CONFLICT(segment_id) DO UPDATE SET
              source_table=excluded.source_table, schema_version=excluded.schema_version,
              model=excluded.model, conversation_id=excluded.conversation_id,
              message_count=excluded.message_count, char_count=excluded.char_count,
              importance=excluded.importance, overall_confidence=excluded.overall_confidence,
              entity_count=excluded.entity_count, event_count=excluded.event_count,
              relationship_signal_count=excluded.relationship_signal_count,
              key_message_count=excluded.key_message_count,
              result_json=excluded.result_json, created_at=excluded.created_at
            """,
            [s[c] for c in seg_cols],
        )

    msg_cols = [
        "evidence_id", "segment_id", "source_table", "schema_version",
        "content_function", "topic", "speech_act", "intent",
        "is_request", "is_commitment", "is_boundary",
        "people_mentioned", "places_mentioned", "projects_mentioned",
        "times_mentioned", "events_mentioned",
        "observable_tone", "inferred_emotion", "inferred_need",
        "relationship_signal", "communication_behavior", "expression_style",
        "memory_candidate", "ambiguity_notes", "confidence", "created_at",
    ]
    for m in msgs:
        conn.execute(
            f"""
            INSERT INTO _v3_hist_messages({','.join(msg_cols)})
            VALUES ({','.join('?' * len(msg_cols))})
            ON CONFLICT(evidence_id) DO UPDATE SET
              segment_id=excluded.segment_id, source_table=excluded.source_table,
              schema_version=excluded.schema_version,
              content_function=excluded.content_function, topic=excluded.topic,
              speech_act=excluded.speech_act, intent=excluded.intent,
              is_request=excluded.is_request, is_commitment=excluded.is_commitment,
              is_boundary=excluded.is_boundary,
              people_mentioned=excluded.people_mentioned,
              places_mentioned=excluded.places_mentioned,
              projects_mentioned=excluded.projects_mentioned,
              times_mentioned=excluded.times_mentioned,
              events_mentioned=excluded.events_mentioned,
              observable_tone=excluded.observable_tone,
              inferred_emotion=excluded.inferred_emotion,
              inferred_need=excluded.inferred_need,
              relationship_signal=excluded.relationship_signal,
              communication_behavior=excluded.communication_behavior,
              expression_style=excluded.expression_style,
              memory_candidate=excluded.memory_candidate,
              ambiguity_notes=excluded.ambiguity_notes,
              confidence=excluded.confidence, created_at=excluded.created_at
            """,
            [m[c] for c in msg_cols],
        )

    conn.commit()
    by_src: dict[str, int] = {}
    for (src,) in conn.execute("SELECT source_table FROM _v3_hist_segments"):
        by_src[src] = by_src.get(src, 0) + 1
    return {
        "segments": len(segs),
        "messages": len(msgs),
        "segments_by_source": by_src,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="把历史标注归一化为 _v3_hist_* 备查表（0 API）")
    ap.add_argument("--db", default=str(Path("data/scale/wechat-analysis-scale.sqlite3")))
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    try:
        st = build_v3_hist(conn)
        print(f"[hist] 片段 {st['segments']} / 消息 {st['messages']} / 0 API")
        for k, v in sorted(st["segments_by_source"].items()):
            print(f"  {k}: {v}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
