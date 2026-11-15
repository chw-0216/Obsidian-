"""v3 持久化：工作区数据库副本的 `_v3` 表 + 运行目录 JSONL 记录。

只写本工作区数据库副本；不触碰 annotations / aggressive_* / contact_* 历史表。
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from .v3_core import Unit
except ImportError:
    from v3_core import Unit

V3_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS v3_run_meta (
  run_id TEXT PRIMARY KEY,
  started_at TEXT, finished_at TEXT, status TEXT,
  model TEXT, prompt_version TEXT,
  config_json TEXT, stats_json TEXT
);
CREATE TABLE IF NOT EXISTS v3_annotations (
  run_id TEXT NOT NULL, unit_key TEXT NOT NULL,
  segment_id TEXT NOT NULL, window_idx INTEGER NOT NULL DEFAULT 0,
  content_sha256 TEXT NOT NULL, segment_sha256 TEXT NOT NULL,
  conversation_id TEXT, message_count INTEGER NOT NULL DEFAULT 0,
  char_count INTEGER NOT NULL DEFAULT 0,
  model TEXT, prompt_version TEXT,
  status TEXT NOT NULL,
  result_json TEXT,
  entity_count INTEGER DEFAULT 0, event_count INTEGER DEFAULT 0,
  relationship_signal_count INTEGER DEFAULT 0,
  importance INTEGER,  -- 提示词未输出时存 NULL（勿当 0 用）
  confidence REAL,
  input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0,
  attempts INTEGER DEFAULT 0, wall_ms INTEGER DEFAULT 0,
  pii_replacements INTEGER DEFAULT 0,
  error TEXT,
  created_at TEXT, updated_at TEXT,
  PRIMARY KEY(run_id, unit_key)
);
CREATE INDEX IF NOT EXISTS idx_v3_annotations_dedup
  ON v3_annotations(content_sha256, model, prompt_version, status);
CREATE TABLE IF NOT EXISTS v3_message_annotations (
  run_id TEXT NOT NULL, evidence_id TEXT NOT NULL, segment_id TEXT NOT NULL,
  window_idx INTEGER NOT NULL DEFAULT 0,
  content_function TEXT, topic TEXT, intent TEXT,
  is_request INTEGER DEFAULT 0, is_commitment INTEGER DEFAULT 0, is_boundary INTEGER DEFAULT 0,
  observable_tone TEXT, inferred_emotion TEXT,
  memory_candidate TEXT, ambiguity_notes TEXT, confidence REAL,
  created_at TEXT,
  PRIMARY KEY(run_id, evidence_id, segment_id)
);
CREATE INDEX IF NOT EXISTS idx_v3_msg_seg ON v3_message_annotations(segment_id, run_id);
CREATE TABLE IF NOT EXISTS v3_call_log (
  run_id TEXT NOT NULL, group_id TEXT NOT NULL,
  units INTEGER DEFAULT 0, msgs INTEGER DEFAULT 0,
  in_tokens INTEGER DEFAULT 0, out_tokens INTEGER DEFAULT 0,
  elapsed_ms INTEGER DEFAULT 0, status TEXT, error TEXT,
  created_at TEXT,
  PRIMARY KEY(run_id, group_id)
);
CREATE TABLE IF NOT EXISTS v3_failures (
  run_id TEXT NOT NULL, unit_key TEXT NOT NULL, segment_id TEXT NOT NULL,
  window_idx INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0,
  error TEXT, created_at TEXT,
  PRIMARY KEY(run_id, unit_key)
);
CREATE TABLE IF NOT EXISTS v3_review (
  run_id TEXT NOT NULL, segment_id TEXT NOT NULL,
  conversation_id TEXT,
  message_count INTEGER NOT NULL DEFAULT 0,
  unit_keys TEXT,
  review_status TEXT,          -- pending / confirmed / corrected
  corrections_json TEXT,       -- {unit_key: {group: {index: {action, payload}}}}
  value_score INTEGER,         -- 手动价值 0-100
  value_tags TEXT,             -- JSON 数组
  keep_recommendation TEXT,    -- keep / pending / cleanup
  note TEXT,
  reviewed_at TEXT,
  PRIMARY KEY(run_id, segment_id)
);
CREATE INDEX IF NOT EXISTS idx_v3_review_conv ON v3_review(run_id, conversation_id);
CREATE TABLE IF NOT EXISTS v3_final_judgments (
  run_id TEXT NOT NULL, conversation_id TEXT NOT NULL,
  segment_count INTEGER NOT NULL DEFAULT 0,
  reviewed_count INTEGER NOT NULL DEFAULT 0,
  avg_value_score REAL,
  min_value_score INTEGER,
  max_value_score INTEGER,
  keep_counts TEXT,            -- {"keep":n,"pending":n,"cleanup":n}
  keep_recommendation TEXT,    -- 派生规则：cleanup 优先
  derived_note TEXT,
  created_at TEXT,
  PRIMARY KEY(run_id, conversation_id)
);
"""


def utc_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_v3_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(V3_SCHEMA_SQL)
    conn.commit()


@dataclass
class UnitOutcome:
    run_id: str
    unit: Unit
    status: str  # success / failed / skipped
    result_json: Optional[dict] = None
    entity_count: int = 0
    event_count: int = 0
    rel_sig_count: int = 0
    importance: Optional[int] = None  # 模型未输出时存 None（NULL），勿当 0 用
    confidence: Optional[float] = None
    error: Optional[str] = None
    attempts: int = 0
    pii_replacements: int = 0
    group_id: str = ""
    in_tokens: int = 0
    out_tokens: int = 0
    wall_ms: int = 0
    created_at: str = field(default_factory=utc_now)


@dataclass
class CallRecord:
    run_id: str
    group_id: str
    units: int
    msgs: int
    in_tokens: int
    out_tokens: int
    elapsed_ms: int
    status: str  # ok / error429 / error_timeout / error_api / validation / failed
    error: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class RunMeta:
    """v3_run_meta 的一行：运行开始/结束状态、配置、汇总指标。"""
    run_id: str
    started_at: str
    status: str  # running / completed / completed_with_failures / superseded
    finished_at: Optional[str] = None
    model: str = ""
    prompt_version: str = ""
    config_json: Optional[dict] = None
    stats_json: Optional[dict] = None


def _to_bool_int(value: Any) -> int:
    return 1 if value else 0


def _insert_unit(conn: sqlite3.Connection, o: UnitOutcome, model: str, prompt_version: str) -> None:
    now = utc_now()
    # 单元最终成功时，清除该 unit_key 的历史失败残留（跨运行），
    # 避免“此前失败、后一次运行成功”的陈旧 failure 干扰后续报告与重试判断。
    if o.status == "success":
        conn.execute("DELETE FROM v3_failures WHERE unit_key=?", (o.unit.unit_key,))
    conn.execute(
        """
        INSERT INTO v3_annotations(
          run_id, unit_key, segment_id, window_idx, content_sha256, segment_sha256,
          conversation_id, message_count, char_count, model, prompt_version, status,
          result_json, entity_count, event_count, relationship_signal_count,
          importance, confidence, input_tokens, output_tokens, attempts, wall_ms,
          pii_replacements, error, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(run_id, unit_key) DO UPDATE SET
          status=excluded.status, result_json=excluded.result_json,
          entity_count=excluded.entity_count, event_count=excluded.event_count,
          relationship_signal_count=excluded.relationship_signal_count,
          importance=excluded.importance, confidence=excluded.confidence,
          input_tokens=excluded.input_tokens, output_tokens=excluded.output_tokens,
          attempts=excluded.attempts, wall_ms=excluded.wall_ms,
          pii_replacements=excluded.pii_replacements, error=excluded.error,
          updated_at=excluded.updated_at
        """,
        (
            o.run_id, o.unit.unit_key, o.unit.segment_id, o.unit.window_idx,
            o.unit.content_sha256, o.unit.segment_sha256, o.unit.conversation_id,
            o.unit.message_count, o.unit.char_count, model, prompt_version, o.status,
            json.dumps(o.result_json, ensure_ascii=False) if o.result_json is not None else None,
            o.entity_count, o.event_count, o.rel_sig_count, o.importance,
            o.confidence, o.in_tokens, o.out_tokens, o.attempts, o.wall_ms,
            o.pii_replacements, o.error, now, now,
        ),
    )


def _insert_message_annotations(conn: sqlite3.Connection, o: UnitOutcome) -> None:
    msgs = (o.result_json or {}).get("messages")
    if not isinstance(msgs, list):
        return
    now = utc_now()
    for m in msgs:
        if not isinstance(m, dict):
            continue
        eid = m.get("evidence_id")
        if not isinstance(eid, str) or not eid:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO v3_message_annotations(
              run_id, evidence_id, segment_id, window_idx,
              content_function, topic, intent,
              is_request, is_commitment, is_boundary,
              observable_tone, inferred_emotion,
              memory_candidate, ambiguity_notes, confidence, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                o.run_id, eid, o.unit.segment_id, o.unit.window_idx,
                str(m.get("content_function") or ""), str(m.get("topic") or ""),
                str(m.get("intent") or ""),
                _to_bool_int(m.get("is_request")), _to_bool_int(m.get("is_commitment")),
                _to_bool_int(m.get("is_boundary")),
                str(m.get("observable_tone") or ""), str(m.get("inferred_emotion") or ""),
                m.get("memory_candidate"), m.get("ambiguity_notes"),
                m.get("confidence"), now,
            ),
        )


def _insert_failure(conn: sqlite3.Connection, o: UnitOutcome) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO v3_failures(run_id, unit_key, segment_id, window_idx, attempts, error, created_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (o.run_id, o.unit.unit_key, o.unit.segment_id, o.unit.window_idx,
         o.attempts, o.error, o.created_at),
    )


def _insert_call(conn: sqlite3.Connection, c: CallRecord) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO v3_call_log(
          run_id, group_id, units, msgs, in_tokens, out_tokens, elapsed_ms, status, error, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (c.run_id, c.group_id, c.units, c.msgs, c.in_tokens, c.out_tokens,
         c.elapsed_ms, c.status, c.error, c.created_at),
    )


def _insert_run_meta(conn: sqlite3.Connection, m: RunMeta) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO v3_run_meta(
          run_id, started_at, finished_at, status, model, prompt_version, config_json, stats_json
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (m.run_id, m.started_at, m.finished_at, m.status, m.model, m.prompt_version,
         json.dumps(m.config_json, ensure_ascii=False, default=str) if m.config_json else None,
         json.dumps(m.stats_json, ensure_ascii=False, default=str) if m.stats_json else None),
    )


def upsert_review(conn: sqlite3.Connection, row: dict) -> None:
    """写入一条片段级复核反馈（复核界面导出的单行，结构见 v3_review.load_feedback）。"""
    conn.execute(
        """
        INSERT INTO v3_review(
          run_id, segment_id, conversation_id, message_count, unit_keys,
          review_status, corrections_json, value_score, value_tags,
          keep_recommendation, note, reviewed_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(run_id, segment_id) DO UPDATE SET
          conversation_id=excluded.conversation_id,
          message_count=excluded.message_count,
          unit_keys=excluded.unit_keys,
          review_status=excluded.review_status,
          corrections_json=excluded.corrections_json,
          value_score=excluded.value_score,
          value_tags=excluded.value_tags,
          keep_recommendation=excluded.keep_recommendation,
          note=excluded.note,
          reviewed_at=excluded.reviewed_at
        """,
        (
            row["run_id"], row["segment_id"], row.get("conversation_id"),
            row.get("message_count", 0),
            json.dumps(row.get("unit_keys") or [], ensure_ascii=False),
            row.get("review_status"),
            json.dumps(row.get("corrections") or {}, ensure_ascii=False),
            row.get("value_score"),
            json.dumps(row.get("value_tags") or [], ensure_ascii=False),
            row.get("keep_recommendation"), row.get("note"),
            row.get("reviewed_at") or utc_now(),
        ),
    )


def upsert_final_judgment(conn: sqlite3.Connection, row: dict) -> None:
    """写入一条会话级价值聚合。"""
    conn.execute(
        """
        INSERT INTO v3_final_judgments(
          run_id, conversation_id, segment_count, reviewed_count,
          avg_value_score, min_value_score, max_value_score,
          keep_counts, keep_recommendation, derived_note, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(run_id, conversation_id) DO UPDATE SET
          segment_count=excluded.segment_count,
          reviewed_count=excluded.reviewed_count,
          avg_value_score=excluded.avg_value_score,
          min_value_score=excluded.min_value_score,
          max_value_score=excluded.max_value_score,
          keep_counts=excluded.keep_counts,
          keep_recommendation=excluded.keep_recommendation,
          derived_note=excluded.derived_note,
          created_at=excluded.created_at
        """,
        (
            row["run_id"], row["conversation_id"],
            row.get("segment_count", 0), row.get("reviewed_count", 0),
            row.get("avg_value_score"),
            row.get("min_value_score"), row.get("max_value_score"),
            json.dumps(row.get("keep_counts") or {}, ensure_ascii=False),
            row.get("keep_recommendation"), row.get("derived_note"),
            row.get("created_at") or utc_now(),
        ),
    )


def _task_json(o: UnitOutcome) -> dict:
    return {
        "run_id": o.run_id,
        "unit_key": o.unit.unit_key,
        "segment_id": o.unit.segment_id,
        "window_idx": o.unit.window_idx,
        "message_count": o.unit.message_count,
        "segment_message_count": o.unit.segment_message_count,
        "char_count": o.unit.char_count,
        "conversation_id": o.unit.conversation_id,
        "status": o.status,
        "attempts": o.attempts,
        "error": o.error,
        "in_tokens": o.in_tokens,
        "out_tokens": o.out_tokens,
        "wall_ms": o.wall_ms,
        "created_at": o.created_at,
    }


def _result_json(o: UnitOutcome) -> dict:
    d = _task_json(o)
    d["result_json"] = o.result_json
    d["entity_count"] = o.entity_count
    d["event_count"] = o.event_count
    d["relationship_signal_count"] = o.rel_sig_count
    d["importance"] = o.importance
    d["confidence"] = o.confidence
    d["pii_replacements"] = o.pii_replacements
    d["group_id"] = o.group_id
    return d


class Recorder:
    """单写者：串行写工作区 DB 副本 + 运行目录 JSONL。"""

    def __init__(self, db_path: str, run_dir: Path, model: str, prompt_version: str):
        self.db_path = db_path
        self.run_dir = Path(run_dir)
        self.model = model
        self.prompt_version = prompt_version
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def enqueue_unit(self, o: UnitOutcome) -> None:
        self._queue.put_nowait(o)

    def enqueue_call(self, c: CallRecord) -> None:
        self._queue.put_nowait(c)

    def enqueue_run_meta(self, m: RunMeta) -> None:
        self._queue.put_nowait(m)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await self._task

    async def _loop(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        # 自动压缩窗口：更小 checkpoint 阈值 + WAL 硬上限，避免长跑时 WAL 无限膨胀。
        # wal_autocheckpoint=256 页(≈1MB) 每次 commit 检查；journal_size_limit=8MB 超限强制合并。
        conn.execute("PRAGMA wal_autocheckpoint=256")
        conn.execute("PRAGMA journal_size_limit=8388608")
        files = {
            name: open(self.run_dir / fname, "a", encoding="utf-8")
            for name, fname in [
                ("tasks", "tasks.jsonl"),
                ("results", "results.jsonl"),
                ("failures", "failures.jsonl"),
                ("calls", "call_log.jsonl"),
            ]
        }
        try:
            while self._running or not self._queue.empty():
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                if isinstance(item, UnitOutcome):
                    self._handle_unit(conn, files, item)
                elif isinstance(item, CallRecord):
                    self._handle_call(conn, files, item)
                elif isinstance(item, RunMeta):
                    _insert_run_meta(conn, item)
                if self._queue.empty():
                    conn.commit()
                    # 队列空闲点主动压缩 WAL（PASSIVE 非阻塞，只合并已提交页）
                    try:
                        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                    except sqlite3.OperationalError:
                        pass
        finally:
            for fh in files.values():
                fh.flush()
                fh.close()
            conn.commit()
            try:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except sqlite3.OperationalError:
                pass
            conn.close()

    def _handle_unit(self, conn, files, o: UnitOutcome) -> None:
        _insert_unit(conn, o, self.model, self.prompt_version)
        files["tasks"].write(json.dumps(_task_json(o), ensure_ascii=False) + "\n")
        if o.status == "success" and o.result_json is not None:
            _insert_message_annotations(conn, o)
            files["results"].write(json.dumps(_result_json(o), ensure_ascii=False) + "\n")
        elif o.status == "failed":
            _insert_failure(conn, o)
            files["failures"].write(json.dumps(_result_json(o), ensure_ascii=False) + "\n")

    def _handle_call(self, conn, files, c: CallRecord) -> None:
        _insert_call(conn, c)
        files["calls"].write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


# ─── Manifest / 原子写入 ───────────────────────────────────────────────────────

def write_json_atomic(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def write_manifest(run_dir: Path, manifest: dict) -> None:
    write_json_atomic(run_dir / "manifest.json", manifest)


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
