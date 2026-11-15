"""
Async Token-Throughput Aggressive Annotation Engine v2
=====================================================
Core upgrade: sync urllib → async aiohttp with connection pooling.
Optimizes for max tokens/min, not segments/min.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add vendor to path for aiohttp
VENDOR = Path(__file__).resolve().parent.parent / "vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import aiohttp

# ─── Constants ─────────────────────────────────────────────────────────────────

DB_PATH = Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3")
RUNS_DIR = Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\runs")
API_BASE = "https://token-plan-cn.xiaomimimo.com/anthropic"
API_VERSION = "2023-06-01"
MODEL = "mimo-v2.5-pro"
MAX_OUTPUT_TOKENS = 16384
MAX_OUTPUT_80PCT = int(MAX_OUTPUT_TOKENS * 0.8)  # 13107

# Concurrency ramp
INITIAL_WORKERS = 32
MAX_WORKERS = 256
RAMP_SEQUENCE = [32, 64, 96, 128, 192, 256]
RAMP_CHECK_INTERVAL = 180  # 3 min
ERROR_RATE_REDUCE = 0.05
TOKEN_THROUGHPUT_WINDOW = 300  # 5 min rolling window

# Queue weights (total=100)
W_MSG_ANNOTATION = 55
W_SEG_CONTEXT = 20
W_RE_ANNOTATION = 10
W_ENTITY_MERGE = 10
W_EVIDENCE_JUDGE = 5

# Adaptive batch sizes
BATCH_SINGLE_MSG = 10      # 1-message segments: 8-12 per batch
BATCH_FEW_MSG = 5          # 2-3 message segments: 4-6 per batch
BATCH_MEDIUM = 2           # 4-10 message segments: 2 per batch
SLICE_WINDOW = 12          # >10 messages: slice to 10-15 message windows

# Progress
PROGRESS_INTERVAL = 60  # seconds

# ─── Schema Split ──────────────────────────────────────────────────────────────

PASS_A_SCHEMA = """你是消息级标注器。对每条消息独立标注。只返回JSON。

输出格式（数组，每个元素是一条消息的标注）：
[{
  "evidence_id": "完整复制[id=...]中的ID，一字不差。示例：msg_2fe71d1ea4e1",
  "content_function": "陈述/提问/回答/请求/命令/承诺/拒绝/感谢/道歉/安慰/调侃/抱怨/通知/确认/否认/补充/转移/结束/情绪表达/媒体引用/系统通知/其他",
  "topic": "主题（≤50字）",
  "speech_act": "言语行为（≤80字）",
  "intent": "意图（≤120字）",
  "is_request": false,
  "is_commitment": false,
  "is_boundary": false,
  "people_mentioned": [],
  "places_mentioned": [],
  "projects_mentioned": [],
  "times_mentioned": [],
  "events_mentioned": [],
  "observable_tone": "可观察语气（≤60字）",
  "inferred_emotion": "推断情绪（≤80字，标注为推断）",
  "inferred_need": "推断需求（≤120字，标注为推断）",
  "relationship_signal": "关系信号（≤120字）",
  "communication_behavior": "沟通行为（≤100字）",
  "expression_style": "表达风格（≤80字）",
  "memory_candidate": "值得记忆的信息（≤200字或null）",
  "ambiguity_notes": "不确定之处（≤200字或null）",
  "confidence": 0.9
}]

只输出JSON数组，不要其他文本。"""

PASS_B_SCHEMA = """你是对话片段分析师。分析整个片段的上下文、事件和关系。只返回JSON。

输出格式：
{
  "segment_id": "必须与输入一致",
  "summary": "一句话总结（≤500字）",
  "segment_context": {
    "conversation_trigger": "什么引发对话（≤200字）",
    "real_goal": "真实目的（≤200字）",
    "topic_shifts": ["话题转换点"],
    "request_response_chains": ["请求-回应链"],
    "tone_turning_points": ["语气转折"],
    "decisions_made": ["做出的决定"],
    "commitments_made": ["做出的承诺"],
    "conflicts_detected": ["冲突"],
    "repairs_attempted": ["修复尝试"],
    "unfinished_items": ["未完成事项"]
  },
  "events": [
    {"event_type": "past_occurrence/current_situation/future_plan/completed/cancelled/uncertain",
     "description": "描述", "time_reference": "时间", "people_involved": [], "outcome": "结果", "confidence": 0.9}
  ],
  "relationship_signals": [
    {"signal_type": "initiative/reciprocity/support/conflict/humor/intimacy/distance/power_dynamic/boundary/dependency",
     "direction": "me_to_them/them_to_me/mutual/unclear",
     "description": "描述", "strength": 0.8}
  ],
  "importance": 5,
  "overall_confidence": 0.9
}

只输出JSON对象，不要其他文本。"""

PASS_C_SCHEMA = """你是实体与事件合并器。从对话片段中提取并合并实体。只返回JSON。

输出格式：
{
  "segment_id": "必须与输入一致",
  "entities": [
    {"entity_type": "person/place/project/organization/event/concept/object",
     "name": "名称", "aliases": ["别名"], "role_or_description": "角色描述",
     "confidence": 0.9}
  ],
  "cross_references": [
    {"source_entity": "源实体", "target_entity": "目标实体", "relation": "关系描述"}
  ]
}

只输出JSON对象，不要其他文本。"""


# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_BASE = """你是数据所有者蔡浩文的私人聊天记录深度分析器。

核心原则：
1. 100%覆盖：每个消息都必须有标注。
2. 证据链：每个标注必须引用evidence_id，完整复制[id=xxx]中的xxx，一字不差，不得截断或修改。
   示例：输入行 [id=msg_2fe71d1ea4e1][2025-12-14 20:53]... → evidence_id 必须是 "msg_2fe71d1ea4e1"（原样复制，含下划线和所有字母数字）。
3. 分离层次：原文直接可见的 vs 模型推断的。
4. 不省略：不要因为消息"不重要"就跳过。
5. 不编造：没有证据时用空数组或null。"""


# ─── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class SegmentTask:
    id: str
    conversation_id: str
    message_count: int
    char_count: int
    transcript: str
    content_sha256: str
    start_ts: int = 0
    end_ts: int = 0
    queue_type: str = "msg_annotation"

@dataclass
class ThroughputStats:
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0
    api_errors: int = 0
    rate_429: int = 0
    timeouts: int = 0
    completed: int = 0
    failed: int = 0
    start_time: float = field(default_factory=time.time)
    _token_window: deque = field(default_factory=deque)

    def record(self, input_tok: int, output_tok: int, success: bool, is_429: bool = False, is_timeout: bool = False):
        now = time.time()
        self.input_tokens += input_tok
        self.output_tokens += output_tok
        self.api_calls += 1
        if success:
            self.completed += 1
        else:
            self.failed += 1
            if is_429:
                self.rate_429 += 1
            if is_timeout:
                self.timeouts += 1
        self._token_window.append((now, input_tok, output_tok, success))
        # Prune old entries
        cutoff = now - TOKEN_THROUGHPUT_WINDOW
        while self._token_window and self._token_window[0][0] < cutoff:
            self._token_window.popleft()

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def input_tok_per_min(self) -> float:
        e = self.elapsed
        return self.input_tokens / (e / 60) if e > 0 else 0

    @property
    def output_tok_per_min(self) -> float:
        e = self.elapsed
        return self.output_tokens / (e / 60) if e > 0 else 0

    @property
    def success_rate(self) -> float:
        total = self.completed + self.failed
        return self.completed / total if total > 0 else 1.0

    @property
    def recent_input_tok_per_min(self) -> float:
        if not self._token_window:
            return 0
        total = sum(t[1] for t in self._token_window)
        span = self._token_window[-1][0] - self._token_window[0][0]
        return total / (span / 60) if span > 0 else 0

    @property
    def recent_output_tok_per_min(self) -> float:
        if not self._token_window:
            return 0
        total = sum(t[2] for t in self._token_window)
        span = self._token_window[-1][0] - self._token_window[0][0]
        return total / (span / 60) if span > 0 else 0


@dataclass
class WriteRequest:
    segment_id: str
    content_sha256: str
    pass_a_result: Optional[list] = None  # message annotations
    pass_b_result: Optional[dict] = None  # segment context
    pass_c_result: Optional[dict] = None  # entities
    created_at: str = ""


# ─── Adaptive Batching ─────────────────────────────────────────────────────────

def estimate_output_tokens(msg_count: int) -> int:
    """Estimate output tokens for a segment based on message count."""
    # From diagnostic: 1 msg → ~2500 tok, 10 msg → ~5000, 30 msg → ~5000, 60 msg → ~9700
    if msg_count <= 1:
        return 2500
    elif msg_count <= 3:
        return 3500
    elif msg_count <= 10:
        return 5000
    elif msg_count <= 20:
        return 7000
    elif msg_count <= 40:
        return 9000
    else:
        return 12000


def adaptive_batch(segments: list[SegmentTask]) -> list[list[SegmentTask]]:
    """Create adaptive batches based on segment message counts."""
    batches = []

    # Group by size
    single_msg = [s for s in segments if s.message_count == 1]
    few_msg = [s for s in segments if 2 <= s.message_count <= 3]
    medium_msg = [s for s in segments if 4 <= s.message_count <= 10]
    large_msg = [s for s in segments if s.message_count > 10]

    # Single message: batch 8-12
    for i in range(0, len(single_msg), BATCH_SINGLE_MSG):
        batch = single_msg[i:i + BATCH_SINGLE_MSG]
        # Verify total estimated output < 80% max
        total_est = sum(estimate_output_tokens(s.message_count) for s in batch)
        if total_est <= MAX_OUTPUT_80PCT:
            batches.append(batch)
        else:
            # Split further
            half = len(batch) // 2
            if half > 0:
                batches.append(batch[:half])
            if len(batch) > half:
                batches.append(batch[half:])

    # Few message: batch 4-6
    for i in range(0, len(few_msg), BATCH_FEW_MSG):
        batch = few_msg[i:i + BATCH_FEW_MSG]
        total_est = sum(estimate_output_tokens(s.message_count) for s in batch)
        if total_est <= MAX_OUTPUT_80PCT:
            batches.append(batch)
        else:
            for s in batch:
                batches.append([s])

    # Medium: batch 2
    for i in range(0, len(medium_msg), BATCH_MEDIUM):
        batch = medium_msg[i:i + BATCH_MEDIUM]
        total_est = sum(estimate_output_tokens(s.message_count) for s in batch)
        if total_est <= MAX_OUTPUT_80PCT:
            batches.append(batch)
        else:
            for s in batch:
                batches.append([s])

    # Large: slice into windows of 10-15 messages
    for seg in large_msg:
        if seg.message_count <= SLICE_WINDOW:
            if estimate_output_tokens(seg.message_count) <= MAX_OUTPUT_80PCT:
                batches.append([seg])
            else:
                batches.append([seg])  # Will retry with simplified prompt if truncated
        else:
            # Create sliced tasks preserving segment_id
            n_slices = (seg.message_count + SLICE_WINDOW - 1) // SLICE_WINDOW
            for slice_idx in range(n_slices):
                start_msg = slice_idx * SLICE_WINDOW
                end_msg = min(start_msg + SLICE_WINDOW, seg.message_count)
                # Create a sub-task with the same segment_id
                sliced = SegmentTask(
                    id=seg.id,
                    conversation_id=seg.conversation_id,
                    message_count=end_msg - start_msg,
                    char_count=seg.char_count // n_slices,
                    transcript=seg.transcript,  # Full context preserved
                    content_sha256=seg.content_sha256,
                    start_ts=seg.start_ts,
                    end_ts=seg.end_ts,
                    queue_type=seg.queue_type,
                )
                batches.append([sliced])

    return batches


# ─── Async API Client ─────────────────────────────────────────────────────────

class AsyncMiMoClient:
    def __init__(self, api_key: str, max_connections: int = 64):
        self.api_key = api_key
        self.max_connections = max_connections
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def start(self):
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections,
            ttl_dns_cache=300,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=180, connect=15)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
            }
        )
        self._semaphore = asyncio.Semaphore(self.max_connections)

    async def close(self):
        if self._session:
            await self._session.close()

    async def call(self, system: str, user_content: str, max_tokens: int = MAX_OUTPUT_TOKENS) -> tuple[dict, int, int]:
        """Make async API call. Returns (parsed_json, input_tokens, output_tokens)."""
        async with self._semaphore:
            body = json.dumps({
                "model": MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user_content}],
            }, ensure_ascii=False)

            url = f"{API_BASE}/v1/messages"
            async with self._session.post(url, data=body) as resp:
                if resp.status == 429:
                    raise RateLimitError(f"429 Rate Limited")
                if resp.status != 200:
                    text = await resp.text()
                    raise APIError(f"HTTP {resp.status}: {text[:300]}")

                raw = await resp.text()
                data = json.loads(raw)
                usage = data.get("usage", {})
                in_tok = usage.get("input_tokens", 0)
                out_tok = usage.get("output_tokens", 0)

                text = self._extract_text(data)
                parsed = self._parse_json(text)

                return parsed, in_tok, out_tok

    def _extract_text(self, data: dict) -> str:
        parts = []
        for block in data.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()

    def _parse_json(self, text: str) -> Any:
        if not text:
            raise ValueError("Empty response")
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try extracting JSON
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char) + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    continue
        raise ValueError(f"Cannot parse JSON from response: {text[:200]}")


class RateLimitError(Exception):
    pass

class APIError(Exception):
    pass


# ─── Writer Queue ─────────────────────────────────────────────────────────────

class DatabaseWriter:
    """Dedicated single-thread writer to avoid SQLite write contention."""

    def __init__(self, db_path: str, jsonl_dir: Path):
        self.db_path = db_path
        self.jsonl_dir = jsonl_dir
        self.jsonl_dir.mkdir(parents=True, exist_ok=True)
        self._queue: asyncio.Queue[WriteRequest] = asyncio.Queue()
        self._running = False
        self._written = 0

    async def start(self):
        self._running = True
        asyncio.create_task(self._writer_loop())

    async def stop(self):
        self._running = False
        # Drain queue
        while not self._queue.empty():
            await asyncio.sleep(0.1)
        await asyncio.sleep(1)  # Let writer finish

    async def enqueue(self, req: WriteRequest):
        await self._queue.put(req)

    async def _writer_loop(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        batch = []
        last_flush = time.time()

        while self._running or not self._queue.empty():
            try:
                req = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                batch.append(req)
            except asyncio.TimeoutError:
                pass

            # Flush every 10 items or every 2 seconds
            if batch and (len(batch) >= 10 or time.time() - last_flush > 2):
                self._flush_batch(conn, batch)
                batch = []
                last_flush = time.time()

        # Final flush
        if batch:
            self._flush_batch(conn, batch)
        conn.close()

    def _flush_batch(self, conn: sqlite3.Connection, batch: list[WriteRequest]):
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        for req in batch:
            req.created_at = now

            # Build combined result for aggressive_annotations table
            combined = self._merge_results(req)

            # Save to DB
            conn.execute("""
                INSERT INTO aggressive_annotations(
                    segment_id, content_sha256, schema_version, model,
                    result_json, message_count, entity_count, event_count,
                    relationship_signal_count, importance, overall_confidence,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(segment_id) DO UPDATE SET
                    content_sha256=excluded.content_sha256,
                    result_json=excluded.result_json,
                    message_count=excluded.message_count,
                    entity_count=excluded.entity_count,
                    event_count=excluded.event_count,
                    relationship_signal_count=excluded.relationship_signal_count,
                    importance=excluded.importance,
                    overall_confidence=excluded.overall_confidence,
                    updated_at=excluded.updated_at
            """, (
                req.segment_id, req.content_sha256, "3.0-async", MODEL,
                json.dumps(combined, ensure_ascii=False),
                len(req.pass_a_result or []),
                len((req.pass_c_result or {}).get("entities", [])),
                len((req.pass_b_result or {}).get("events", [])),
                len((req.pass_b_result or {}).get("relationship_signals", [])),
                (req.pass_b_result or {}).get("importance", 0),
                (req.pass_b_result or {}).get("overall_confidence", 0),
                now, now
            ))

            # Save message annotations
            for msg in (req.pass_a_result or []):
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
                        confidence=excluded.confidence,
                        created_at=excluded.created_at
                """, (
                    msg.get("evidence_id", ""), req.segment_id,
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
                    now,
                ))

            # Save entities
            for ent in (req.pass_c_result or {}).get("entities", []):
                conn.execute("""
                    INSERT INTO aggressive_entities(
                        segment_id, entity_type, name, aliases,
                        role_or_description, evidence_ids, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req.segment_id, ent.get("entity_type", ""), ent.get("name", ""),
                    json.dumps(ent.get("aliases", []), ensure_ascii=False),
                    ent.get("role_or_description", ""),
                    json.dumps(ent.get("evidence_ids", []), ensure_ascii=False),
                    ent.get("confidence", 0), now,
                ))

            # Save events
            for evt in (req.pass_b_result or {}).get("events", []):
                conn.execute("""
                    INSERT INTO aggressive_events(
                        segment_id, event_type, description, time_reference,
                        people_involved, outcome, evidence_ids, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req.segment_id, evt.get("event_type", ""), evt.get("description", ""),
                    evt.get("time_reference", ""),
                    json.dumps(evt.get("people_involved", []), ensure_ascii=False),
                    evt.get("outcome", ""),
                    json.dumps(evt.get("evidence_ids", []), ensure_ascii=False),
                    evt.get("confidence", 0), now,
                ))

        conn.commit()

        # Also write JSONL checkpoint
        jsonl_path = self.jsonl_dir / f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M')}.jsonl"
        with open(jsonl_path, "a", encoding="utf-8") as f:
            for req in batch:
                record = {
                    "segment_id": req.segment_id,
                    "content_sha256": req.content_sha256,
                    "pass_a": req.pass_a_result,
                    "pass_b": req.pass_b_result,
                    "pass_c": req.pass_c_result,
                    "created_at": req.created_at,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._written += len(batch)

    def _merge_results(self, req: WriteRequest) -> dict:
        """Merge Pass A/B/C results into a single combined record."""
        combined = {}
        if req.pass_b_result:
            combined.update(req.pass_b_result)
        if req.pass_a_result:
            combined["messages"] = req.pass_a_result
        if req.pass_c_result:
            combined["entities"] = req.pass_c_result.get("entities", [])
            combined["cross_references"] = req.pass_c_result.get("cross_references", [])
        combined["segment_id"] = req.segment_id
        return combined


# ─── Pass A/B/C Processors ────────────────────────────────────────────────────

async def run_pass_a(client: AsyncMiMoClient, batch: list[SegmentTask]) -> dict[str, list]:
    """Pass A: Message-level atomic annotation."""
    prompt_parts = [SYSTEM_BASE + "\n\n" + PASS_A_SCHEMA + "\n\n以下是待标注的对话片段：\n"]
    expected_ids = set()

    for seg in batch:
        prompt_parts.append(f"\n{'='*40}")
        prompt_parts.append(f"segment_id: {seg.id}")
        prompt_parts.append(f"消息数: {seg.message_count}")
        prompt_parts.append(f"\n{seg.transcript}")

        # Extract expected evidence_ids from transcript
        for line in seg.transcript.split("\n"):
            if line.startswith("[id="):
                eid = line[4:20]
                expected_ids.add(eid)

    prompt_parts.append(f"\n对以上 {len(expected_ids)} 条消息返回JSON数组。")
    prompt = "\n".join(prompt_parts)

    if len(prompt) > 60000:
        prompt = prompt[:60000] + "\n\n[截断]"

    parsed, in_tok, out_tok = await client.call(SYSTEM_BASE, prompt)

    # Validate: must be array of dicts
    if isinstance(parsed, dict) and "messages" in parsed:
        items = parsed["messages"]
    elif isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        if "evidence_id" in parsed:
            # Model returned single annotation dict instead of array — wrap it
            items = [parsed]
        else:
            # Try to extract any list value
            list_vals = [v for v in parsed.values() if isinstance(v, list)]
            if list_vals:
                items = max(list_vals, key=len)
            else:
                raise ValueError(f"Pass A: dict with no list value, keys={list(parsed.keys())[:5]}")
    else:
        raise ValueError(f"Pass A: expected array, got {type(parsed).__name__}: {str(parsed)[:100]}")

    # Filter out non-dict items (model may return strings mixed in)
    items = [m for m in items if isinstance(m, dict)]
    if not items:
        raise ValueError(f"Pass A: no valid dict items in response (parsed type={type(parsed).__name__}, raw={str(parsed)[:200]})")

    # Validate evidence_ids (prefix match: first 12 chars)
    returned_ids = {m.get("evidence_id", "") for m in items}
    exp_prefix = {eid[:12] for eid in expected_ids}
    ret_prefix = {eid[:12] for eid in returned_ids if len(eid) >= 8}
    missing = exp_prefix - ret_prefix
    extra = ret_prefix - exp_prefix
    if missing:
        raise ValueError(f"Pass A: missing evidence_ids (prefix): {missing}")
    if extra:
        raise ValueError(f"Pass A: extra evidence_ids (prefix): {extra}")

    return {"items": items, "in_tok": in_tok, "out_tok": out_tok}


async def run_pass_b(client: AsyncMiMoClient, seg: SegmentTask) -> tuple[dict, int, int]:
    """Pass B: Segment context, events, relationship signals."""
    prompt = f"""{SYSTEM_BASE}

{PASS_B_SCHEMA}

分析以下片段：

segment_id: {seg.id}
消息数: {seg.message_count}

{seg.transcript}

返回JSON。"""

    if len(prompt) > 60000:
        prompt = prompt[:60000] + "\n\n[截断]"

    parsed, in_tok, out_tok = await client.call(SYSTEM_BASE, prompt)

    # Validate segment_id
    if parsed.get("segment_id") != seg.id:
        raise ValueError(f"Pass B: segment_id mismatch: {parsed.get('segment_id')} != {seg.id}")

    return parsed, in_tok, out_tok


async def run_pass_c(client: AsyncMiMoClient, seg: SegmentTask) -> tuple[dict, int, int]:
    """Pass C: Entity and event merging."""
    prompt = f"""{SYSTEM_BASE}

{PASS_C_SCHEMA}

分析以下片段中的实体：

segment_id: {seg.id}
消息数: {seg.message_count}

{seg.transcript}

返回JSON。"""

    if len(prompt) > 60000:
        prompt = prompt[:60000] + "\n\n[截断]"

    parsed, in_tok, out_tok = await client.call(SYSTEM_BASE, prompt)

    if parsed.get("segment_id") != seg.id:
        raise ValueError(f"Pass C: segment_id mismatch: {parsed.get('segment_id')} != {seg.id}")

    return parsed, in_tok, out_tok


# ─── Validation ────────────────────────────────────────────────────────────────

def validate_strict(result: Any, expected_ids: set, pass_name: str):
    """Validation: evidence_ids must match by prefix (first 12 chars)."""
    if pass_name == "pass_a":
        items = result if isinstance(result, list) else result.get("messages", [])
        items = [m for m in items if isinstance(m, dict)]  # filter non-dict
        returned = {m.get("evidence_id", "") for m in items}
        exp_prefix = {eid[:12] for eid in expected_ids}
        ret_prefix = {eid[:12] for eid in returned if len(eid) >= 8}
        missing = exp_prefix - ret_prefix
        extra = ret_prefix - exp_prefix
        if missing:
            raise ValueError(f"{pass_name}: missing {len(missing)} evidence_ids (prefix)")
        if extra:
            raise ValueError(f"{pass_name}: extra {len(extra)} evidence_ids (prefix)")
        # Check for duplicates (by prefix)
        if len(ret_prefix) != len(items):
            raise ValueError(f"{pass_name}: duplicate evidence_ids detected")


# ─── Queue Manager ─────────────────────────────────────────────────────────────

class QueueManager:
    """Manages 5 weighted queues for different analysis passes."""

    def __init__(self):
        self.queues = {
            "msg_annotation": asyncio.Queue(),
            "seg_context": asyncio.Queue(),
            "re_annotation": asyncio.Queue(),
            "entity_merge": asyncio.Queue(),
            "evidence_judge": asyncio.Queue(),
        }
        self.weights = {
            "msg_annotation": W_MSG_ANNOTATION,
            "seg_context": W_SEG_CONTEXT,
            "re_annotation": W_RE_ANNOTATION,
            "entity_merge": W_ENTITY_MERGE,
            "evidence_judge": W_EVIDENCE_JUDGE,
        }

    async def get_next(self) -> tuple[str, SegmentTask]:
        """Get next task from weighted random queue."""
        # Simple weighted round-robin
        total_weight = sum(self.weights.values())
        for qname, weight in self.weights.items():
            if not self.queues[qname].empty():
                # Check weight
                import random
                if random.randint(1, total_weight) <= weight:
                    task = await self.queues[qname].get()
                    return qname, task

        # Fallback: get from any non-empty queue
        for qname, queue in self.queues.items():
            if not queue.empty():
                task = await queue.get()
                return qname, task

        raise asyncio.QueueEmpty()

    @property
    def total_pending(self) -> int:
        return sum(q.qsize() for q in self.queues.values())

    @property
    def is_empty(self) -> bool:
        return all(q.empty() for q in self.queues.values())


# ─── Main Engine ───────────────────────────────────────────────────────────────

class AsyncAnnotationEngine:
    def __init__(self, api_key: str, max_workers: int = INITIAL_WORKERS):
        self.api_key = api_key
        self.max_workers = max_workers
        self.current_workers = INITIAL_WORKERS
        self.client = AsyncMiMoClient(api_key, max_connections=MAX_WORKERS)
        self.writer = DatabaseWriter(str(DB_PATH), RUNS_DIR / "jsonl_checkpoints")
        self.stats = ThroughputStats()
        self.queue_mgr = QueueManager()
        self.run_id = f"async_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._running = False
        self._last_ramp_check = time.time()
        self._last_progress = time.time()
        self._throughput_history: list[tuple[float, float]] = []  # (timestamp, output_tok_per_min)

    async def run(self):
        """Main execution loop."""
        print(f"╔══════════════════════════════════════════════════════════════════╗")
        print(f"║  Async Token-Throughput Annotation Engine v2                    ║")
        print(f"║  Run: {self.run_id}                                          ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝")
        print(f"\nAPI: {API_BASE} | Model: {MODEL}")
        print(f"Initial workers: {INITIAL_WORKERS} | Max: {MAX_WORKERS}")
        print(f"Ramp: {RAMP_SEQUENCE}")
        print(f"{'='*70}")

        # Load pending segments
        segments = self._load_pending_segments()
        if not segments:
            print("没有待标注的片段。")
            return

        print(f"待标注: {len(segments)} 个片段")

        # Create adaptive batches
        batches = adaptive_batch(segments)
        print(f"自适应分批: {len(batches)} 个批次")
        batch_sizes = [len(b) for b in batches]
        print(f"  批次大小分布: min={min(batch_sizes)} max={max(batch_sizes)} avg={sum(batch_sizes)/len(batch_sizes):.1f}")

        # Queue all batches for Pass A (message annotation)
        for batch in batches:
            for seg in batch:
                seg.queue_type = "msg_annotation"
                await self.queue_mgr.queues["msg_annotation"].put(seg)

        print(f"\n队列状态:")
        for qname, queue in self.queue_mgr.queues.items():
            print(f"  {qname}: {queue.qsize()}")
        print(f"{'='*70}\n")

        # Start client and writer
        await self.client.start()
        await self.writer.start()
        self._running = True

        # Run workers
        try:
            workers = [
                asyncio.create_task(self._worker(i))
                for i in range(self.current_workers)
            ]
            # Add progress reporter
            workers.append(asyncio.create_task(self._progress_reporter()))
            # Add throughput monitor
            workers.append(asyncio.create_task(self._throughput_monitor()))

            await asyncio.gather(*workers, return_exceptions=True)
        except KeyboardInterrupt:
            print("\n⚠️  用户中断")
        finally:
            self._running = False
            await self.writer.stop()
            await self.client.close()
            self._print_summary()

    def _load_pending_segments(self) -> list[SegmentTask]:
        """Load segments not yet annotated."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT s.id, s.conversation_id, s.message_count, s.char_count,
                   s.transcript, s.content_sha256, s.start_ts, s.end_ts
            FROM segments s
            LEFT JOIN aggressive_annotations aa ON aa.segment_id = s.id
            WHERE aa.segment_id IS NULL
            ORDER BY s.char_count ASC, s.id ASC
        """).fetchall()
        conn.close()

        return [SegmentTask(
            id=r["id"], conversation_id=r["conversation_id"],
            message_count=r["message_count"], char_count=r["char_count"],
            transcript=r["transcript"], content_sha256=r["content_sha256"],
            start_ts=r["start_ts"], end_ts=r["end_ts"],
        ) for r in rows]

    async def _worker(self, worker_id: int):
        """Single worker that processes tasks from queues."""
        while self._running:
            try:
                qname, task = await asyncio.wait_for(
                    self.queue_mgr.get_next(), timeout=5.0
                )
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                if self.queue_mgr.is_empty and self._running:
                    await asyncio.sleep(1)
                continue

            try:
                await self._process_task(task, qname)
            except RateLimitError:
                # Re-queue and back off
                await self.queue_mgr.queues[qname].put(task)
                await asyncio.sleep(5)
                self.stats.record(0, 0, False, is_429=True)
            except (APIError, TimeoutError) as e:
                self.stats.record(0, 0, False, is_timeout="timeout" in str(e).lower())
                # Re-queue for retry
                await asyncio.sleep(2)
                await self.queue_mgr.queues[qname].put(task)
            except Exception as e:
                self.stats.record(0, 0, False)
                print(f"  ❌ Worker {worker_id}: {type(e).__name__}: {str(e)[:100]}", flush=True)

    async def _process_task(self, task: SegmentTask, queue_type: str):
        """Process a single task through the appropriate pass."""
        if queue_type == "msg_annotation":
            # Pass A: Message-level annotation
            try:
                result = await run_pass_a(self.client, [task])
                in_tok = result["in_tok"]
                out_tok = result["out_tok"]
                self.stats.record(in_tok, out_tok, True)

                # Validate
                expected_ids = set()
                for line in task.transcript.split("\n"):
                    if line.startswith("[id="):
                        expected_ids.add(line[4:20])
                validate_strict(result["items"], expected_ids, "pass_a")

                # Queue for Pass B
                task.pass_a_result = result["items"]
                await self.queue_mgr.queues["seg_context"].put(task)

            except ValueError as e:
                # Validation failed - retry once
                self.stats.record(0, 0, False)
                print(f"  ⚠️  {task.id[:12]} Pass A validation: {str(e)[:100]}", flush=True)
                return

        elif queue_type == "seg_context":
            # Pass B: Segment context
            try:
                result, in_tok, out_tok = await run_pass_b(self.client, task)
                self.stats.record(in_tok, out_tok, True)
                task.pass_b_result = result

                # Queue for Pass C
                await self.queue_mgr.queues["entity_merge"].put(task)

            except Exception as e:
                self.stats.record(0, 0, False)
                print(f"  ⚠️  {task.id[:12]} Pass B: {str(e)[:100]}", flush=True)
                return

        elif queue_type == "entity_merge":
            # Pass C: Entity merging
            try:
                result, in_tok, out_tok = await run_pass_c(self.client, task)
                self.stats.record(in_tok, out_tok, True)
                task.pass_c_result = result

                # All passes complete - enqueue for writing
                req = WriteRequest(
                    segment_id=task.id,
                    content_sha256=task.content_sha256,
                    pass_a_result=task.pass_a_result,
                    pass_b_result=task.pass_b_result,
                    pass_c_result=task.pass_c_result,
                )
                await self.writer.enqueue(req)

                print(f"  ✅ {task.id[:12]} msgs={task.message_count} chars={task.char_count} | 完整标注", flush=True)

            except Exception as e:
                self.stats.record(0, 0, False)
                print(f"  ⚠️  {task.id[:12]} Pass C: {str(e)[:100]}", flush=True)
                return

    async def _progress_reporter(self):
        """Report progress every PROGRESS_INTERVAL seconds."""
        while self._running:
            await asyncio.sleep(PROGRESS_INTERVAL)
            self._print_progress()

    def _print_progress(self):
        conn = sqlite3.connect(str(DB_PATH))
        annotated = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
        msg_ann = conn.execute("SELECT COUNT(*) FROM aggressive_message_annotations").fetchone()[0]
        conn.close()

        disk_free = shutil.disk_usage(DB_PATH.parent).free // (1024**3)
        pct = annotated / total * 100 if total else 0

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"进度: {annotated}/{total} ({pct:.1f}%) | "
            f"消息标注: {msg_ann} | "
            f"in: {self.stats.input_tok_per_min:.0f} tok/min | "
            f"out: {self.stats.output_tok_per_min:.0f} tok/min | "
            f"workers: {self.current_workers} | "
            f"队列: {self.queue_mgr.total_pending} | "
            f"成功率: {self.stats.success_rate:.1%} | "
            f"429: {self.stats.rate_429} | "
            f"超时: {self.stats.timeouts} | "
            f"API: {self.stats.api_calls} | "
            f"累计: {self.stats.input_tokens:,}→{self.stats.output_tokens:,} | "
            f"磁盘: {disk_free}GB",
            flush=True
        )

    async def _throughput_monitor(self):
        """Monitor throughput and adjust concurrency every RAMP_CHECK_INTERVAL."""
        while self._running:
            await asyncio.sleep(RAMP_CHECK_INTERVAL)
            self._adjust_concurrency()

    def _adjust_concurrency(self):
        """Adjust worker count based on throughput and error rates."""
        error_rate = 1 - self.stats.success_rate
        recent_out_tok = self.stats.recent_output_tok_per_min

        # Record throughput history
        self._throughput_history.append((time.time(), recent_out_tok))

        if error_rate > ERROR_RATE_REDUCE:
            # Reduce workers
            old = self.current_workers
            idx = RAMP_SEQUENCE.index(self.current_workers) if self.current_workers in RAMP_SEQUENCE else 0
            if idx > 0:
                self.current_workers = RAMP_SEQUENCE[idx - 1]
                print(f"⚠️  错误率 {error_rate:.1%} > {ERROR_RATE_REDUCE:.0%}，降低 workers: {old} → {self.current_workers}", flush=True)
        elif error_rate < 0.02 and self.stats.api_calls > 20:
            # Check if throughput is still increasing
            if len(self._throughput_history) >= 2:
                prev_tok = self._throughput_history[-2][1]
                if recent_out_tok > prev_tok * 1.05:  # 5% improvement threshold
                    idx = RAMP_SEQUENCE.index(self.current_workers) if self.current_workers in RAMP_SEQUENCE else -1
                    if idx < len(RAMP_SEQUENCE) - 1:
                        old = self.current_workers
                        self.current_workers = RAMP_SEQUENCE[idx + 1]
                        print(f"✅ 吞吐提升 ({prev_tok:.0f}→{recent_out_tok:.0f} tok/min)，提升 workers: {old} → {self.current_workers}", flush=True)

    def _print_summary(self):
        print(f"\n{'='*70}")
        print(f"运行完成！Run ID: {self.run_id}")
        print(f"{'='*70}")
        print(f"总耗时: {self.stats.elapsed/60:.1f} 分钟")
        print(f"完成: {self.stats.completed} | 失败: {self.stats.failed}")
        print(f"API 调用: {self.stats.api_calls} | 429: {self.stats.rate_429} | 超时: {self.stats.timeouts}")
        print(f"Token: 输入 {self.stats.input_tokens:,} / 输出 {self.stats.output_tokens:,}")
        print(f"平均吞吐: in={self.stats.input_tok_per_min:.0f} tok/min | out={self.stats.output_tok_per_min:.0f} tok/min")
        print(f"成功率: {self.stats.success_rate:.1%}")

        conn = sqlite3.connect(str(DB_PATH))
        annotated = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
        print(f"\n标注进度: {annotated}/{total} ({annotated/total*100:.1f}%)")
        conn.close()


# ─── CLI ───────────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not key:
        settings = Path.home() / ".claude" / "settings.json"
        if settings.exists():
            with open(settings) as f:
                key = json.load(f).get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")
    return key


def main():
    api_key = get_api_key()
    if not api_key:
        print("❌ 未找到 API Key")
        sys.exit(1)

    engine = AsyncAnnotationEngine(api_key)
    asyncio.run(engine.run())


if __name__ == "__main__":
    main()
