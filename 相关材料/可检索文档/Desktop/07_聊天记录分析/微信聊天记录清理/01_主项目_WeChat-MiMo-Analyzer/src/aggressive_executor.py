"""
Aggressive Parallel Annotation Executor for WeChat-MiMo-Analyzer
Stage 1: Full-coverage annotation with direct MiMo API calls.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ─── Config ────────────────────────────────────────────────────────────────────

API_BASE = os.environ.get("MIMO_API_BASE", "https://token-plan-cn.xiaomimimo.com/anthropic")
API_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.5-pro")
API_VERSION = "2023-06-01"

# Worker ramp: start conservative, increase on stability
INITIAL_WORKERS = 4
MAX_WORKERS = 32
RAMP_CHECK_INTERVAL = 60  # seconds between ramp checks
ERROR_RATE_THRESHOLD = 0.08
RAMP_UP_FACTOR = 1.5

# Batch sizing
DEFAULT_BATCH_SIZE = 1          # segments per API call (1 = most reliable)
MAX_PROMPT_CHARS = 40000        # max total chars in a single prompt
MAX_OUTPUT_TOKENS = 16384       # max tokens in API response
DEFAULT_MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0

# Progress
CHECKPOINT_INTERVAL = 10        # save progress every N results
PROGRESS_LOG_INTERVAL = 30      # log progress every N seconds

# ─── Database Schema Extension ─────────────────────────────────────────────────

EXTENDED_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS aggressive_annotations (
    segment_id TEXT PRIMARY KEY REFERENCES segments(id) ON DELETE CASCADE,
    content_sha256 TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    model TEXT NOT NULL,
    result_json TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    entity_count INTEGER NOT NULL DEFAULT 0,
    event_count INTEGER NOT NULL DEFAULT 0,
    relationship_signal_count INTEGER NOT NULL DEFAULT 0,
    importance INTEGER NOT NULL DEFAULT 0,
    overall_confidence REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aggressive_message_annotations (
    evidence_id TEXT NOT NULL,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
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
    confidence REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (evidence_id, segment_id)
);

CREATE TABLE IF NOT EXISTS aggressive_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    aliases TEXT,
    role_or_description TEXT,
    evidence_ids TEXT,
    confidence REAL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aggressive_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    time_reference TEXT,
    people_involved TEXT,
    outcome TEXT,
    evidence_ids TEXT,
    confidence REAL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aggressive_run_stats (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    total_segments INTEGER NOT NULL DEFAULT 0,
    completed_segments INTEGER NOT NULL DEFAULT 0,
    failed_segments INTEGER NOT NULL DEFAULT 0,
    skipped_segments INTEGER NOT NULL DEFAULT 0,
    total_api_calls INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    current_workers INTEGER NOT NULL DEFAULT 0,
    estimated_remaining_minutes REAL,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE INDEX IF NOT EXISTS idx_agg_entities_segment ON aggressive_entities(segment_id);
CREATE INDEX IF NOT EXISTS idx_agg_entities_type_name ON aggressive_entities(entity_type, name);
CREATE INDEX IF NOT EXISTS idx_agg_events_segment ON aggressive_events(segment_id);
CREATE INDEX IF NOT EXISTS idx_agg_events_type ON aggressive_events(event_type);
CREATE INDEX IF NOT EXISTS idx_agg_msg_ann_segment ON aggressive_message_annotations(segment_id);
"""

# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是数据所有者蔡浩文的私人聊天记录深度分析器。你必须以最激进、最全面的策略分析每一条消息和每一个对话片段。

## 核心原则

1. **100%覆盖**：每个消息都必须有标注，包括短回复、表情、媒体占位符和系统消息。
2. **无上限深度**：在主题、言语行为、意图、人物、事件、情绪、需求、关系信号、沟通行为、表达风格、记忆候选等所有维度上进行最细致的标注。
3. **证据链**：每个标注必须引用 evidence_id（消息的前16字符ID）。没有证据时用空数组或"无法判断"。
4. **分离层次**：原文直接可见的（高置信度）vs 模型推断的（需标注为推断）。
5. **不省略**：不要因为消息看起来"不重要"就跳过或简化标注。

## 消息级标注要求（每条消息）

对每条消息（通过 evidence_id 标识），必须分析：
- content_function：消息的功能（陈述/提问/回答/请求/命令/承诺/拒绝/感谢/道歉/安慰/调侃/抱怨/通知/确认/否认/补充/转移/结束/情绪表达/媒体引用/系统通知/其他）
- topic：这条消息讨论的核心主题（自由文本，不超过50字）
- speech_act：具体的言语行为描述（如"请求对方提供帮助"、"表达不满"、"确认收到"）
- intent：发送者的真实意图（可以包含推断，但要标注推断置信度）
- is_request/is_commitment/is_boundary：是否包含请求/承诺/边界设定
- people_mentioned/places_mentioned/projects_mentioned/times_mentioned/events_mentioned：提到的实体
- observable_tone：可观察到的语气（如"轻松"、"急切"、"敷衍"、"热情"）
- inferred_emotion：推断的情绪状态（标注为推断）
- inferred_need：推断的底层需求（标注为推断）
- relationship_signal：这条消息对关系的信号（如"表达依赖"、"建立边界"、"展示幽默"）
- communication_behavior：沟通行为模式（如"简短回复可能表示不想深入"、"主动发起话题"）
- expression_style：表达风格特征（如"使用自嘲化解尴尬"、"直接坦率"）
- memory_candidate：这条消息是否包含值得长期记忆的信息
- ambiguity_notes：标注中的不确定之处
- confidence：整体标注的置信度（0-1）

## 片段级分析要求

在消息级标注之上，分析整个对话片段的：
- conversation_trigger：什么引发了这段对话
- real_goal：对话的真实目的（可能不同于表面）
- topic_shifts：话题转换点
- request_response_chains：请求-回应-结果链条
- tone_turning_points：语气/情绪转折点
- decisions_made/commitments_made：做出的决定和承诺
- conflicts_detected/repairs_attempted：冲突和修复尝试
- unfinished_items：未完成的事项

## 实体和事件提取

提取片段中出现的所有：
- 人物（含别名、备注名、角色描述）
- 地点
- 项目
- 组织
- 事件（区分过去发生/当前状况/未来计划/已完成/已取消）
- 概念/物品

## 关系信号分析

分析互动中的关系动力：
- 主动性（谁发起、谁回应）
- 互惠性（是否平衡）
- 权力动态
- 核心张力
- 支持/冲突模式
- 幽默使用
- 亲密度/距离感
- 边界设定
- 依赖关系

## 九维语义深描

从以下九个维度独立分析：
1. content：内容层面说了什么
2. action：行为层面做了什么
3. relationship：关系层面暗示什么
4. emotion：情绪层面表达什么
5. need：需求层面渴望什么
6. identity：身份层面展现什么
7. style：风格层面有什么特征
8. memory：记忆层面有什么意义
9. uncertainty：不确定性在哪里

## 输出格式

严格按照给定的 JSON Schema 输出。不要输出任何额外文本。"""

# ─── API Client ────────────────────────────────────────────────────────────────

class MiMoClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._lock = threading.Lock()
        self._call_count = 0
        self._error_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._last_rps_check = time.time()
        self._rps_window_calls = 0

    def call(self, prompt: str, schema: dict, max_tokens: int = MAX_OUTPUT_TOKENS) -> dict:
        """Make a single API call and return parsed JSON response."""
        url = f"{self.base_url}/v1/messages"
        # Include output format instructions in system prompt
        full_system = SYSTEM_PROMPT + "\n\n## 输出格式\n\n你必须且只返回一个JSON对象，结构如下：\n```json\n" + json.dumps(schema, ensure_ascii=False, indent=2) + "\n```\n\n不要输出JSON以外的任何文本。不要用markdown代码块包裹。直接输出JSON。"
        body = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "system": full_system,
            "messages": [{"role": "user", "content": prompt}],
        }, ensure_ascii=False).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
        }

        req = Request(url, data=body, headers=headers, method="POST")

        with self._lock:
            self._call_count += 1
            self._rps_window_calls += 1

        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))

        usage = data.get("usage", {})
        with self._lock:
            self._total_input_tokens += usage.get("input_tokens", 0)
            self._total_output_tokens += usage.get("output_tokens", 0)

        # Extract text content
        content_blocks = data.get("content", [])
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        raw_text = "\n".join(text_parts).strip()

        # Try to parse as JSON
        if raw_text.startswith("```"):
            # Strip markdown code fences
            lines = raw_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines)

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            # Try to find JSON object in text
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw_text[start:end])
            raise ValueError(f"Cannot parse API response as JSON: {e}\nRaw: {raw_text[:500]}")

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "total_calls": self._call_count,
                "total_errors": self._error_count,
                "input_tokens": self._total_input_tokens,
                "output_tokens": self._total_output_tokens,
            }

    def increment_errors(self):
        with self._lock:
            self._error_count += 1


# ─── Prompt Builder ────────────────────────────────────────────────────────────

def build_segment_prompt(segments: list[dict], include_message_details: bool = True) -> str:
    """Build the analysis prompt for a batch of segments."""
    parts = ["以下是待分析的对话片段。请对每个片段进行最全面、最深度的标注。\n"]

    for seg in segments:
        parts.append(f"\n{'='*60}")
        parts.append(f"segment_id: {seg['id']}")
        parts.append(f"conversation_id: {seg['conversation_id']}")
        parts.append(f"message_count: {seg['message_count']}")
        parts.append(f"char_count: {seg['char_count']}")
        parts.append(f"时间范围: {seg.get('start_ts', '未知')} ~ {seg.get('end_ts', '未知')}")
        parts.append(f"\n对话内容:")
        parts.append(seg['transcript'])

    parts.append(f"\n{'='*60}")
    parts.append("\n请严格按照 JSON Schema 输出分析结果。每个片段的所有消息都必须有标注。")
    return "\n".join(parts)


# ─── Result Validator ──────────────────────────────────────────────────────────

def validate_result(result: dict, batch: list[dict]) -> list[dict]:
    """Validate the API result covers all segments in the batch."""
    expected_ids = {seg["id"] for seg in batch}
    items = result.get("segments", [])
    returned_ids = {item.get("segment_id") for item in items if isinstance(item, dict)}

    missing = expected_ids - returned_ids
    extra = returned_ids - expected_ids

    if missing:
        raise ValueError(f"Missing segments in response: {missing}")
    if extra:
        raise ValueError(f"Extra segments in response: {extra}")

    # Validate each segment has required fields
    for item in items:
        if not item.get("messages"):
            raise ValueError(f"Segment {item.get('segment_id')} has no messages array")
        if not item.get("segment_context"):
            raise ValueError(f"Segment {item.get('segment_id')} has no segment_context")

    return items


# ─── Database Operations ───────────────────────────────────────────────────────

def init_extended_schema(conn: sqlite3.Connection):
    """Create the extended annotation tables."""
    conn.executescript(EXTENDED_SCHEMA_SQL)
    conn.commit()


def get_pending_segments(conn: sqlite3.Connection, limit: int = 0) -> list[dict]:
    """Get segments that haven't been annotated with the aggressive schema.
    Sort by char_count ASC — start small to build confidence and catch errors early."""
    sql = """
        SELECT s.id, s.conversation_id, s.ordinal, s.start_ts, s.end_ts,
               s.message_count, s.char_count, s.transcript, s.content_sha256
        FROM segments s
        LEFT JOIN aggressive_annotations aa ON aa.segment_id = s.id
        WHERE aa.segment_id IS NULL
        ORDER BY s.char_count ASC, s.id ASC
    """
    if limit > 0:
        sql += f" LIMIT {limit}"
    return [dict(row) for row in conn.execute(sql)]


def get_all_segments(conn: sqlite3.Connection) -> list[dict]:
    """Get all segments."""
    sql = """
        SELECT s.id, s.conversation_id, s.ordinal, s.start_ts, s.end_ts,
               s.message_count, s.char_count, s.transcript, s.content_sha256
        FROM segments s
        ORDER BY s.conversation_id, s.ordinal
    """
    return [dict(row) for row in conn.execute(sql)]


def save_annotation_result(conn: sqlite3.Connection, segment_id: str,
                           content_sha256: str, result: dict, now: str):
    """Save a single segment's annotation result to the database."""
    # Save main annotation
    conn.execute("""
        INSERT INTO aggressive_annotations(
            segment_id, content_sha256, schema_version, model,
            result_json, message_count, entity_count, event_count,
            relationship_signal_count, importance, overall_confidence,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(segment_id) DO UPDATE SET
            content_sha256=excluded.content_sha256,
            schema_version=excluded.schema_version,
            model=excluded.model,
            result_json=excluded.result_json,
            message_count=excluded.message_count,
            entity_count=excluded.entity_count,
            event_count=excluded.event_count,
            relationship_signal_count=excluded.relationship_signal_count,
            importance=excluded.importance,
            overall_confidence=excluded.overall_confidence,
            updated_at=excluded.updated_at
    """, (
        segment_id, content_sha256, "2.0-aggressive", MODEL,
        json.dumps(result, ensure_ascii=False),
        len(result.get("messages", [])),
        len(result.get("entities", [])),
        len(result.get("events", [])),
        len(result.get("relationship_signals", [])),
        result.get("importance", 0),
        result.get("overall_confidence", 0),
        now, now
    ))

    # Save message-level annotations
    for msg in result.get("messages", []):
        conn.execute("""
            INSERT INTO aggressive_message_annotations(
                evidence_id, segment_id, content_function, topic, speech_act,
                intent, is_request, is_commitment, is_boundary,
                people_mentioned, places_mentioned, projects_mentioned,
                times_mentioned, events_mentioned, observable_tone,
                inferred_emotion, inferred_need, relationship_signal,
                communication_behavior, expression_style, memory_candidate,
                ambiguity_notes, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id, segment_id) DO UPDATE SET
                content_function=excluded.content_function,
                topic=excluded.topic,
                speech_act=excluded.speech_act,
                intent=excluded.intent,
                is_request=excluded.is_request,
                is_commitment=excluded.is_commitment,
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
                confidence=excluded.confidence,
                created_at=excluded.created_at
        """, (
            msg.get("evidence_id", ""), segment_id,
            msg.get("content_function", ""), msg.get("topic", ""),
            msg.get("speech_act", ""), msg.get("intent", ""),
            1 if msg.get("is_request") else 0,
            1 if msg.get("is_commitment") else 0,
            1 if msg.get("is_boundary") else 0,
            json.dumps(msg.get("people_mentioned", []), ensure_ascii=False),
            json.dumps(msg.get("places_mentioned", []), ensure_ascii=False),
            json.dumps(msg.get("projects_mentioned", []), ensure_ascii=False),
            json.dumps(msg.get("times_mentioned", []), ensure_ascii=False),
            json.dumps(msg.get("events_mentioned", []), ensure_ascii=False),
            msg.get("observable_tone", ""),
            msg.get("inferred_emotion", ""),
            msg.get("inferred_need", ""),
            msg.get("relationship_signal", ""),
            msg.get("communication_behavior", ""),
            msg.get("expression_style", ""),
            msg.get("memory_candidate", ""),
            msg.get("ambiguity_notes", ""),
            msg.get("confidence", 0),
            now
        ))

    # Save entities
    for ent in result.get("entities", []):
        conn.execute("""
            INSERT INTO aggressive_entities(
                segment_id, entity_type, name, aliases,
                role_or_description, evidence_ids, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment_id, ent.get("entity_type", ""), ent.get("name", ""),
            json.dumps(ent.get("aliases", []), ensure_ascii=False),
            ent.get("role_or_description", ""),
            json.dumps(ent.get("evidence_ids", []), ensure_ascii=False),
            ent.get("confidence", 0), now
        ))

    # Save events
    for evt in result.get("events", []):
        conn.execute("""
            INSERT INTO aggressive_events(
                segment_id, event_type, description, time_reference,
                people_involved, outcome, evidence_ids, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            segment_id, evt.get("event_type", ""), evt.get("description", ""),
            evt.get("time_reference", ""),
            json.dumps(evt.get("people_involved", []), ensure_ascii=False),
            evt.get("outcome", ""),
            json.dumps(evt.get("evidence_ids", []), ensure_ascii=False),
            evt.get("confidence", 0), now
        ))

    conn.commit()


def update_run_stats(conn: sqlite3.Connection, run_id: str, stats: dict):
    """Update run statistics."""
    conn.execute("""
        UPDATE aggressive_run_stats SET
            updated_at=?,
            completed_segments=?,
            failed_segments=?,
            skipped_segments=?,
            total_api_calls=?,
            total_errors=?,
            current_workers=?,
            estimated_remaining_minutes=?,
            status=?
        WHERE run_id=?
    """, (
        stats["updated_at"],
        stats["completed"],
        stats["failed"],
        stats["skipped"],
        stats["api_calls"],
        stats["errors"],
        stats["workers"],
        stats["est_remaining_min"],
        stats["status"],
        run_id
    ))
    conn.commit()


def get_annotated_count(conn: sqlite3.Connection) -> int:
    """Count how many segments have aggressive annotations."""
    row = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()
    return row[0] if row else 0


# ─── Worker ────────────────────────────────────────────────────────────────────

BATCH_TIMEOUT = 300  # 5 minutes total per batch


def process_batch(
    batch: list[dict],
    client: MiMoClient,
    schema: dict,
    db_path: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> tuple[int, int, str]:
    """Process a single batch of segments. Returns (success_count, error_count, error_msg)."""
    batch_start = time.time()
    prompt = build_segment_prompt(batch)

    # Truncate if too long
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[内容过长已截断]"

    seg = batch[0] if batch else {}
    seg_info = f"seg={seg.get('id','?')[:12]} msgs={seg.get('message_count',0)} chars={seg.get('char_count',0)}"

    last_error = ""
    for attempt in range(max_retries + 1):
        # Check total batch timeout
        if time.time() - batch_start > BATCH_TIMEOUT:
            last_error = f"Batch timeout ({BATCH_TIMEOUT}s)"
            print(f"  ⏰ {seg_info} | 超时 {BATCH_TIMEOUT}s", flush=True)
            break

        try:
            result = client.call(prompt, schema)

            # Validate
            items = validate_result(result, batch)

            # Save to database (thread-safe with own connection)
            conn = sqlite3.connect(db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            now = datetime.now().astimezone().isoformat(timespec="seconds")

            for item in items:
                seg_id = item["segment_id"]
                seg_match = next((s for s in batch if s["id"] == seg_id), None)
                sha = seg_match["content_sha256"] if seg_match else ""
                save_annotation_result(conn, seg_id, sha, item, now)

            conn.close()
            elapsed = time.time() - batch_start
            print(f"  ✅ {seg_info} | {elapsed:.1f}s | {len(items)} 标注", flush=True)
            return len(items), 0, ""

        except (HTTPError, URLError, TimeoutError) as e:
            last_error = f"{type(e).__name__}: {str(e)[:200]}"
            client.increment_errors()
            print(f"  ⚠️  {seg_info} | attempt {attempt+1} | {last_error}", flush=True)
            if attempt < max_retries:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
            continue
        except (json.JSONDecodeError, ValueError) as e:
            last_error = f"Parse error: {str(e)[:200]}"
            client.increment_errors()
            print(f"  ⚠️  {seg_info} | attempt {attempt+1} | {last_error}", flush=True)
            if attempt < max_retries:
                time.sleep(RETRY_BASE_DELAY)
            continue
        except Exception as e:
            last_error = f"Unexpected: {type(e).__name__}: {str(e)[:200]}"
            client.increment_errors()
            print(f"  ⚠️  {seg_info} | attempt {attempt+1} | {last_error}", flush=True)
            if attempt < max_retries:
                time.sleep(RETRY_BASE_DELAY)
            continue

    print(f"  ❌ {seg_info} | 最终失败: {last_error[:100]}", flush=True)
    return 0, 1, last_error


# ─── Progress Tracker ──────────────────────────────────────────────────────────

class ProgressTracker:
    def __init__(self, total: int, run_id: str, db_path: str):
        self.total = total
        self.run_id = run_id
        self.db_path = db_path
        self.completed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
        self._last_log = time.time()
        self._batch_times: list[float] = []
        self._errors: list[str] = []

    def record_success(self, count: int):
        with self._lock:
            self.completed += count
            self._batch_times.append(time.time())

    def record_failure(self, error: str):
        with self._lock:
            self.failed += 1
            self._errors.append(error[:100])
            if len(self._errors) > 50:
                self._errors = self._errors[-25:]

    def record_skip(self, count: int = 1):
        with self._lock:
            self.skipped += count

    def log_progress(self, client: MiMoClient, workers: int):
        now = time.time()
        if now - self._last_log < PROGRESS_LOG_INTERVAL:
            return
        self._last_log = now

        with self._lock:
            elapsed = now - self.start_time
            done = self.completed + self.failed + self.skipped
            pct = (done / self.total * 100) if self.total else 0
            rate = self.completed / (elapsed / 60) if elapsed > 0 else 0
            remaining = (self.total - done) / rate if rate > 0 else 0

            # Recent throughput (last 5 min)
            recent = [t for t in self._batch_times if now - t < 300]
            recent_rate = len(recent) / 5 if recent else 0

            api_stats = client.stats

            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"进度: {done}/{self.total} ({pct:.1f}%) | "
                f"完成: {self.completed} 失败: {self.failed} 跳过: {self.skipped} | "
                f"速率: {rate:.1f}/min (近5min: {recent_rate:.1f}/min) | "
                f"Workers: {workers} | "
                f"API调用: {api_stats['total_calls']} 错误: {api_stats['total_errors']} | "
                f"Token: {api_stats['input_tokens']:,}→{api_stats['output_tokens']:,} | "
                f"剩余: ~{remaining:.0f}min",
                flush=True
            )

    def save_checkpoint(self, client: MiMoClient, workers: int):
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        elapsed = time.time() - self.start_time
        done = self.completed + self.failed + self.skipped
        rate = self.completed / (elapsed / 60) if elapsed > 0 else 0
        remaining = (self.total - done) / rate / 60 if rate > 0 else None

        stats = {
            "updated_at": now,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "api_calls": client.stats["total_calls"],
            "errors": client.stats["total_errors"],
            "workers": workers,
            "est_remaining_min": remaining,
            "status": "running" if done < self.total else "completed",
        }

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            update_run_stats(conn, self.run_id, stats)
            conn.close()
        except Exception:
            pass

    @property
    def recent_error_rate(self) -> float:
        with self._lock:
            total = self.completed + self.failed
            if total < 10:
                return 0.0
            return self.failed / total

    @property
    def recent_errors(self) -> list[str]:
        with self._lock:
            return list(self._errors[-10:])


# ─── Main Executor ─────────────────────────────────────────────────────────────

def run_aggressive_annotation(args: argparse.Namespace):
    """Main execution loop."""
    db_path = str(args.database)
    schema_path = str(args.schema)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Load schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Initialize database
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    init_extended_schema(conn)

    # Get pending segments
    if args.force_reannotate:
        segments = get_all_segments(conn)
        # Clear existing aggressive annotations
        conn.execute("DELETE FROM aggressive_annotations")
        conn.execute("DELETE FROM aggressive_message_annotations")
        conn.execute("DELETE FROM aggressive_entities")
        conn.execute("DELETE FROM aggressive_events")
        conn.commit()
        print(f"强制重新标注模式：清空已有标注，重新处理全部 {len(segments)} 个片段")
    else:
        segments = get_pending_segments(conn)
        print(f"增量标注模式：{len(segments)} 个待标注片段")

    if not segments:
        print("没有待标注的片段。使用 --force-reannotate 强制重新处理。")
        conn.close()
        return

    # Apply limit if set
    if args.limit > 0:
        segments = segments[:args.limit]
        print(f"限制处理数量: {args.limit}")

    total = len(segments)

    # Create batches
    batches = []
    current_batch = []
    current_chars = 0
    for seg in segments:
        seg_chars = len(seg["transcript"])
        if current_batch and (
            len(current_batch) >= args.batch_size or
            current_chars + seg_chars > MAX_PROMPT_CHARS
        ):
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(seg)
        current_chars += seg_chars
    if current_batch:
        batches.append(current_batch)

    print(f"分为 {len(batches)} 个批次 (每批 {args.batch_size} 个片段)")
    print(f"API: {API_BASE} | 模型: {MODEL}")
    print(f"初始 Workers: {args.workers} | 最大: {MAX_WORKERS}")
    print(f"{'='*80}")

    # Create run record
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    conn.execute("""
        INSERT INTO aggressive_run_stats(
            run_id, started_at, updated_at, total_segments, status
        ) VALUES (?, ?, ?, ?, 'running')
    """, (run_id, now, now, total))
    conn.commit()
    conn.close()

    # Initialize client and tracker
    api_key = args.api_key or API_KEY
    if not api_key:
        # Try to read from settings
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
                api_key = settings.get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")

    if not api_key:
        print("错误：未找到 API Key。请设置 --api-key 或 ANTHROPIC_AUTH_TOKEN 环境变量。")
        return

    client = MiMoClient(API_BASE, api_key, MODEL)
    tracker = ProgressTracker(total, run_id, db_path)

    # Adaptive worker management
    current_workers = args.workers
    last_ramp_check = time.time()

    def adjust_workers():
        nonlocal current_workers, last_ramp_check
        now = time.time()
        if now - last_ramp_check < RAMP_CHECK_INTERVAL:
            return
        last_ramp_check = now

        error_rate = tracker.recent_error_rate
        if error_rate > ERROR_RATE_THRESHOLD:
            new_workers = max(2, current_workers // 2)
            if new_workers != current_workers:
                print(f"⚠️  错误率 {error_rate:.1%} 超阈值，降低 workers: {current_workers} → {new_workers}")
                current_workers = new_workers
        elif error_rate < 0.02 and current_workers < MAX_WORKERS:
            new_workers = min(MAX_WORKERS, int(current_workers * RAMP_UP_FACTOR))
            if new_workers != current_workers:
                print(f"✅ 错误率低 {error_rate:.1%}，提升 workers: {current_workers} → {new_workers}")
                current_workers = new_workers

    # Main execution loop
    batch_queue = list(enumerate(batches))
    completed_batches = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        active_futures = {}

        while batch_queue or active_futures:
            # Submit new batches up to current_workers
            while batch_queue and len(active_futures) < current_workers:
                batch_idx, batch = batch_queue.pop(0)
                future = executor.submit(
                    process_batch, batch, client, schema, db_path, args.max_retries
                )
                active_futures[future] = (batch_idx, batch)

            # Process completed futures
            done_futures = [f for f in active_futures if f.done()]
            for future in done_futures:
                batch_idx, batch = active_futures.pop(future)
                try:
                    success, errors, error_msg = future.result(timeout=5)
                    if success > 0:
                        tracker.record_success(success)
                    if errors > 0:
                        tracker.record_failure(error_msg)
                except Exception as e:
                    tracker.record_failure(f"Future exception: {e}")

                completed_batches += 1

            # Log and checkpoint
            tracker.log_progress(client, current_workers)
            if completed_batches % CHECKPOINT_INTERVAL == 0 and completed_batches > 0:
                tracker.save_checkpoint(client, current_workers)
                adjust_workers()

            # Small sleep to avoid busy-waiting
            if not done_futures:
                time.sleep(0.1)

    # Final checkpoint
    tracker.save_checkpoint(client, current_workers)

    # Print summary
    elapsed = time.time() - start_time
    api_stats = client.stats
    annotated = get_annotated_count(sqlite3.connect(db_path))

    print(f"\n{'='*80}")
    print(f"运行完成！Run ID: {run_id}")
    print(f"{'='*80}")
    print(f"总耗时: {elapsed/60:.1f} 分钟")
    print(f"标注完成: {tracker.completed} 个片段")
    print(f"标注失败: {tracker.failed} 个片段")
    print(f"跳过: {tracker.skipped} 个片段")
    print(f"累计标注: {annotated}/{total+get_annotated_count(sqlite3.connect(db_path))-tracker.completed} 个片段")
    print(f"API 调用: {api_stats['total_calls']} 次")
    print(f"API 错误: {api_stats['total_errors']} 次")
    print(f"Token 用量: 输入 {api_stats['input_tokens']:,} / 输出 {api_stats['output_tokens']:,}")
    print(f"平均速率: {tracker.completed/(elapsed/60):.1f} 片段/分钟")

    if tracker.recent_errors:
        print(f"\n最近错误:")
        for err in tracker.recent_errors:
            print(f"  - {err}")

    # Update final status
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE aggressive_run_stats SET status='completed' WHERE run_id=?", (run_id,))
    conn.commit()
    conn.close()

    # Write run manifest
    manifest = {
        "run_id": run_id,
        "started_at": start_time,
        "finished_at": time.time(),
        "duration_seconds": elapsed,
        "total_segments": total,
        "completed": tracker.completed,
        "failed": tracker.failed,
        "skipped": tracker.skipped,
        "api_calls": api_stats["total_calls"],
        "api_errors": api_stats["total_errors"],
        "input_tokens": api_stats["input_tokens"],
        "output_tokens": api_stats["output_tokens"],
        "model": MODEL,
        "schema": "2.0-aggressive",
    }
    manifest_path = Path(db_path).parent.parent / "runs" / run_id / "run-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n清单已保存: {manifest_path}")


# ─── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggressive Parallel Annotation Executor - 全量深度标注引擎"
    )
    parser.add_argument(
        "--database", type=Path,
        default=Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3"),
        help="SQLite 数据库路径"
    )
    parser.add_argument(
        "--schema", type=Path,
        default=Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\config\aggressive-annotation.schema.json"),
        help="JSON Schema 路径"
    )
    parser.add_argument("--api-key", default="", help="MiMo API Key (默认从 settings.json 读取)")
    parser.add_argument("--workers", type=int, default=INITIAL_WORKERS, help=f"初始 worker 数量 (默认 {INITIAL_WORKERS})")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help=f"最大重试次数 (默认 {DEFAULT_MAX_RETRIES})")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"每批片段数 (默认 {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--limit", type=int, default=0, help="限制处理片段数 (0=全部)")
    parser.add_argument("--force-reannotate", action="store_true", help="强制重新标注所有片段")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_aggressive_annotation(args)
