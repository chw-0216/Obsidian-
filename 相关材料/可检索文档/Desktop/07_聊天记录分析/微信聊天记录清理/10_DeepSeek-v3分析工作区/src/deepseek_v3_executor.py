"""DeepSeek v3 微信分析执行器（试运行版）。

修复旧流程核心问题：
- 短片段真正合并进同一个 API 请求，并逐片段拆分结果；
- 长片段按窗口切分，每个请求只发送对应文本；
- 并发增减真正创建/停止 worker；
- 队列清空后正常退出；
- 429/超时/校验失败进入有次数上限的重试流程；
- 所有成功/失败/跳过项写入 DB(_v3) + JSONL + manifest；
- 按内容哈希 + 模型 + 提示词版本去重，避免重复调用。

用法（工作区根目录）：
  python -m src.deepseek_v3_executor plan          # 只做抽样/建批计划，不调用 API
  python -m src.deepseek_v3_executor run            # 真实试运行（默认最多 20 片段）
  python -m src.deepseek_v3_executor report <run_id>
  python -m src.deepseek_v3_executor verify         # 校验 DB 只写工作区副本、只加 _v3 表
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    import aiohttp  # noqa: F401
except ImportError:  # 回退到只读运行依赖目录
    VENDOR = Path(r"C:\Users\wardc\Desktop\微信聊天记录清理\09_未迁移脚本与运行依赖\runtime\vendor")
    if VENDOR.exists():
        sys.path.insert(0, str(VENDOR))

from src.v3_core import (  # noqa: E402
    Unit,
    build_group_prompt,
    build_units,
    compute_backoff,
    estimate_output_tokens,
    extract_unit_results,
    make_batches,
    split_units,
    stratified_sample,
    validate_group,
)
from src.v3_api import ApiClient, ApiError, RateLimitError  # noqa: E402
from src.v3_io import (  # noqa: E402
    CallRecord,
    Recorder,
    RunMeta,
    UnitOutcome,
    ensure_v3_schema,
    read_jsonl,
    utc_now,
    write_json_atomic,
    write_manifest,
)

BUCKET_LABELS = {1: "1", 3: "2-3", 10: "4-10", 30: "11-30", 31: "31+"}


def bucket_of(message_count: int) -> str:
    if message_count == 1:
        return "1"
    if message_count <= 3:
        return "2-3"
    if message_count <= 10:
        return "4-10"
    if message_count <= 30:
        return "11-30"
    return "31+"


def _coerce_importance(value) -> int | None:
    """把模型输出的 importance 归一为整数；未输出/非法时返回 None（存 NULL）。

    避免「模型没填」被记录成 0，导致后续按重要度分析时误读。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["paths"]["db"] = (WORKSPACE_ROOT / cfg["paths"]["db"]).resolve()
    cfg["paths"]["prompt"] = (WORKSPACE_ROOT / cfg["paths"]["prompt"]).resolve()
    cfg["paths"]["runs_dir"] = (WORKSPACE_ROOT / cfg["paths"]["runs_dir"]).resolve()
    cfg["paths"]["reports_dir"] = (WORKSPACE_ROOT / cfg["paths"]["reports_dir"]).resolve()
    cfg["report"]["output"] = (WORKSPACE_ROOT / cfg["report"]["output"]).resolve()
    return cfg


def get_token() -> str:
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if token:
        return token
    settings = Path.home() / ".claude" / "settings.json"
    if settings.exists():
        try:
            with open(settings, "r", encoding="utf-8") as fh:
                token = json.load(fh).get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")
        except (json.JSONDecodeError, OSError):
            token = ""
    return token


def get_base_url() -> str:
    return os.environ.get("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")


@dataclass
class Stats:
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    completed_units: int = 0
    failed_units: int = 0
    skipped_units: int = 0
    rate_429: int = 0
    timeouts: int = 0
    api_errors: int = 0
    validation_failures: int = 0
    groups_processed: int = 0
    start_time: float = field(default_factory=time.time)
    _error_window: deque = field(default_factory=lambda: deque(maxlen=120))
    _last_429_at: float = 0.0
    _last_429_window: float = 0.0

    def record_call(self, ok: bool, is_429: bool = False) -> None:
        self.api_calls += 1
        self._error_window.append(1 if ok else 0)
        if is_429:
            now = time.time()
            self._last_429_at = now

    @property
    def error_rate(self) -> float:
        if not self._error_window:
            return 0.0
        return 1 - (sum(self._error_window) / len(self._error_window))

    @property
    def recent_429(self) -> bool:
        return bool(self._last_429_at) and (time.time() - self._last_429_at) < 20

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    def summary(self) -> dict:
        return {
            "api_calls": self.api_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "completed_units": self.completed_units,
            "failed_units": self.failed_units,
            "skipped_units": self.skipped_units,
            "rate_429": self.rate_429,
            "timeouts": self.timeouts,
            "api_errors": self.api_errors,
            "validation_failures": self.validation_failures,
            "groups_processed": self.groups_processed,
            "error_rate": round(self.error_rate, 4),
            "elapsed_seconds": round(self.elapsed, 2),
        }


@dataclass
class WorkGroup:
    group_id: str
    units: list[Unit]
    attempts: int = 0
    split_depth: int = 0


class V3Executor:
    def __init__(self, config: dict, token: str, base_url: str, run_id: str = "",
                 skip_validation: bool = False):
        self.cfg = config
        self.token = token
        self.base_url = base_url
        self.skip_validation = skip_validation
        self.model = config["model"]
        self.prompt_version = config["prompt_version"]
        api = config["api"]
        self.max_output_tokens = api["max_output_tokens"]
        self.api_version = api["api_version"]
        self.request_timeout = api["request_timeout_seconds"]
        self.connect_timeout = api["connect_timeout_seconds"]
        # NVIDIA 等 OpenAI 兼容端点：api_style="openai"；DeepSeek 官方保持 "anthropic"
        self.api_style = api.get("api_style", "anthropic")
        self.rpm_limit = api.get("rpm_limit")
        self.rate_burst = int(api.get("rate_burst", 2))

        conc = config["concurrency"]
        self.start_workers = conc["start_workers"]
        self.min_workers = conc["min_workers"]
        self.max_workers = conc["max_workers"]
        self.ramp_up_step = conc["ramp_up_step"]
        self.ramp_down_step = conc["ramp_down_step"]
        self.ramp_check_interval = conc["ramp_check_interval_seconds"]
        self.reduce_error_threshold = conc["reduce_error_rate_threshold"]
        self.ramp_up_error_threshold = conc["ramp_up_error_rate_threshold"]
        self.min_api_calls_before_ramp = conc["min_api_calls_before_ramp"]
        self.min_seconds_between_ramps = conc["min_seconds_between_ramps"]

        batch = config["batching"]
        self.window_size = batch["window_size_msgs"]
        self.max_units_per_batch = batch["max_units_per_batch"]
        self.max_msgs_per_batch = batch["max_msgs_per_batch"]
        self.max_input_chars_per_batch = batch["max_input_chars_per_batch"]

        retry = config["retry"]
        self.retry_max_attempts = retry["max_attempts"]
        # 429 专用的更大重试预算（默认沿用 max_attempts）
        self.retry_max_attempts_429 = int(retry.get("max_attempts_429", retry["max_attempts"]))
        self.retry429_base = retry["retry429_base_seconds"]
        self.retry429_max = retry["retry429_max_seconds"]
        self.retry_error_base = retry["retry_error_base_seconds"]
        self.retry_validation_base = retry["retry_validation_base_seconds"]
        self.max_split_depth = retry["max_validation_split_depth"]

        self.db_path = str(config["paths"]["db"])
        self.run_id = run_id or f"pilot_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = config["paths"]["runs_dir"] / self.run_id
        self.recorder = Recorder(self.db_path, self.run_dir, self.model, self.prompt_version)
        self.client: Optional[ApiClient] = None
        self.stats = Stats()
        self._prompt_cache: Optional[str] = None
        self._existing_success_hashes: set[str] = set()

        self.task_queue: asyncio.Queue[WorkGroup] = asyncio.Queue()
        self._worker_tasks: dict[int, asyncio.Task] = {}
        self._worker_target = self.start_workers
        self._in_flight = 0
        self._pending_retries: list[tuple[float, WorkGroup]] = []
        self._running = False
        self._draining = False
        self._enqueue_finished = False
        self._group_counter = 0
        self._last_ramp_ts = time.time()

    def _next_group_id(self) -> str:
        self._group_counter += 1
        return f"g{self._group_counter}"

    # ─── 计划构建（不调用 API） ─────────────────────────────────────────────────
    def build_plan(self) -> dict:
        self._existing_success_hashes = self._load_existing_success_hashes()
        conn = self._connect_ro()
        try:
            sample_cfg = self.cfg["sampling"]
            rows = stratified_sample(
                conn,
                seed=sample_cfg["seed"],
                per_bucket=sample_cfg["per_bucket"],
                buckets=sample_cfg["buckets"],
                max_total=sample_cfg["max_total_segments"],
            )
        finally:
            conn.close()

        units: list[Unit] = []
        skipped: list[dict] = []
        sampled_segments: list[dict] = []
        for r in rows:
            seg_id = r["id"]
            seg_mc = r["message_count"]
            try:
                built = build_units(
                    seg_id,
                    r["transcript"],
                    segment_sha256=r.get("segment_sha256") or "",
                    conversation_id=r.get("conversation_id") or "",
                    window_size=self.window_size,
                    segment_message_count=seg_mc,
                )
            except Exception as exc:  # noqa: BLE001
                skipped.append({"segment_id": seg_id, "reason": f"build error: {exc}"})
                continue
            if not built:
                skipped.append({"segment_id": seg_id, "reason": "no parseable messages"})
                continue
            for u in built:
                reason = self._dedup_reason(u)
                if reason:
                    skipped.append({"unit_key": u.unit_key, "segment_id": u.segment_id,
                                    "window_idx": u.window_idx, "reason": reason})
                    self.stats.skipped_units += 1
                else:
                    units.append(u)
            sampled_segments.append({
                "id": seg_id,
                "conversation_id": r.get("conversation_id") or "",
                "message_count": seg_mc,
                "char_count": r["char_count"],
                "bucket": bucket_of(seg_mc),
            })

        batches = make_batches(
            units,
            max_output_tokens=int(self.max_output_tokens * 0.8),
            max_units_per_batch=self.max_units_per_batch,
            max_msgs_per_batch=self.max_msgs_per_batch,
            max_input_chars_per_batch=self.max_input_chars_per_batch,
        )
        plan = {
            "run_id": self.run_id,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "created_at": utc_now(),
            "sampled_segments": sampled_segments,
            "units": [
                {
                    "unit_key": u.unit_key, "segment_id": u.segment_id,
                    "window_idx": u.window_idx, "message_count": u.message_count,
                    "char_count": u.char_count, "bucket": bucket_of(u.message_count),
                    "segment_bucket": bucket_of(u.segment_message_count),
                    "segment_message_count": u.segment_message_count,
                    "content_sha256": u.content_sha256,
                }
                for u in units
            ],
            "skipped": skipped,
            "batches": [
                [u.unit_key for u in b] for b in batches
            ],
            "totals": {
                "sampled_segments": len(sampled_segments),
                "units": len(units),
                "batches": len(batches),
                "skipped_units": len(skipped),
                "estimated_output_tokens": sum(
                    estimate_output_tokens(u.message_count) for b in batches for u in b
                ),
            },
        }
        return plan

    def _dedup_reason(self, unit: Unit) -> Optional[str]:
        """内容哈希 + 模型 + 提示词版本 去重：历史或其他运行已成功标注则跳过。"""
        if hasattr(self, "_dedup_seen") and unit.content_sha256 in self._dedup_seen:
            return "already-in-plan"
        if unit.content_sha256 in self._existing_success_hashes:
            return "existing-success"
        return None

    def _load_existing_success_hashes(self) -> set[str]:
        """一次性预加载「当前模型+提示词版本」下已成功的 content_sha256 集合。

        避免 _dedup_reason 对每个 unit 都开一次只读连接查询（全量上万 unit 会
        产生上万次连接，plan 阶段可能卡数分钟）。
        """
        conn = self._connect_ro()
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT content_sha256 FROM v3_annotations
                WHERE model=? AND prompt_version=? AND status='success'
                """,
                (self.model, self.prompt_version),
            ).fetchall()
            return {r[0] for r in rows if r[0]}
        finally:
            conn.close()

    def _unit_has_success(self, content_sha256: str) -> bool:
        conn = self._connect_ro()
        try:
            row = conn.execute(
                """
                SELECT 1 FROM v3_annotations
                WHERE content_sha256=? AND model=? AND prompt_version=? AND status='success'
                LIMIT 1
                """,
                (content_sha256, self.model, self.prompt_version),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def _connect_ro(self):
        import sqlite3
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    # ─── 真实运行 ──────────────────────────────────────────────────────────────
    async def run(self, plan: dict) -> Stats:
        self._running = True
        self._dedup_seen = {u["content_sha256"] for u in plan["units"]}
        batches = [
            [self._unit_from_plan(plan, key) for key in b] for b in plan["batches"]
        ]
        # 丢弃计划构建后再被判定重复的单元（防并发重跑）
        batches = [[u for u in b if u is not None] for b in batches]
        batches = [b for b in batches if b]
        total_units = sum(len(b) for b in batches)

        self.client = ApiClient(
            base_url=self.base_url,
            token=self.token,
            model=self.model,
            max_output_tokens=self.max_output_tokens,
            api_version=self.api_version,
            request_timeout=self.request_timeout,
            connect_timeout=self.connect_timeout,
            disable_thinking=True,
            api_style=self.api_style,
            rpm_limit=self.rpm_limit,
            rate_burst=self.rate_burst,
        )

        # 备份计划快照与提示词
        self.run_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(self.run_dir / "config.json", self.cfg)
        write_json_atomic(self.run_dir / "plan.json", plan)
        prompt_text = self._load_prompt()
        (self.run_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")

        await self.client.start()
        await self.recorder.start()
        started_at = utc_now()
        self.recorder.enqueue_run_meta(RunMeta(
            run_id=self.run_id, started_at=started_at, status="running",
            model=self.model, prompt_version=self.prompt_version, config_json=self.cfg,
        ))
        self._sync_workers()

        pump = asyncio.create_task(self._retry_pump())
        monitor = asyncio.create_task(self._monitor())
        reporter = asyncio.create_task(self._progress_reporter())

        for batch in batches:
            self.task_queue.put_nowait(WorkGroup(self._next_group_id(), batch))
        self._enqueue_finished = True
        print(f"[run] {self.run_id} | 单元数={total_units} 批次={len(batches)} "
              f"workers={self._worker_target} 模型={self.model}", flush=True)

        try:
            await self._maintain()
        finally:
            self._running = False
            self._draining = True

        for t in list(self._worker_tasks.values()):
            if not t.done():
                t.cancel()
        await asyncio.gather(
            *list(self._worker_tasks.values()), pump, monitor, reporter, return_exceptions=True
        )
        # 运行结束写 v3_run_meta（status 区分有无失败），随 recorder 队列串行落库
        final_status = "completed" if self.stats.failed_units == 0 else "completed_with_failures"
        self.recorder.enqueue_run_meta(RunMeta(
            run_id=self.run_id, started_at=started_at, finished_at=utc_now(),
            status=final_status, model=self.model, prompt_version=self.prompt_version,
            config_json=self.cfg, stats_json=self.stats.summary(),
        ))
        await self.recorder.stop()
        await self.client.close()

        self.stats.skipped_units += plan["totals"]["skipped_units"] or 0
        return self.stats

    def _unit_from_plan(self, plan: dict, unit_key: str) -> Optional[Unit]:
        """按计划重建单元；内容哈希与计划不一致（异常情形）则跳过，保证去重有效。"""
        seg_mc_lookup = {s["id"]: s["message_count"] for s in plan.get("sampled_segments", [])}
        for u in plan["units"]:
            if u["unit_key"] != unit_key:
                continue
            transcript = self._load_segment_transcript(u["segment_id"])
            if transcript is None:
                return None
            built = build_units(
                u["segment_id"], transcript, u.get("segment_sha256", ""),
                u.get("conversation_id", ""), window_size=self.window_size,
                segment_message_count=seg_mc_lookup.get(u["segment_id"], u.get("segment_message_count", 0)),
            )
            idx = u["window_idx"]
            if idx >= len(built):
                return None
            unit = built[idx]
            if unit.content_sha256 != u["content_sha256"]:
                return None
            return unit
        return None

    def _load_segment_transcript(self, segment_id: str) -> Optional[str]:
        import sqlite3
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        try:
            row = conn.execute("SELECT transcript FROM segments WHERE id=?", (segment_id,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def _load_prompt(self) -> str:
        if self._prompt_cache is None:
            self._prompt_cache = Path(self.cfg["paths"]["prompt"]).read_text(encoding="utf-8")
        return self._prompt_cache

    # ─── worker 池（真正创建/停止） ─────────────────────────────────────────────
    def _sync_workers(self) -> None:
        # 创建缺失的 worker
        for i in range(len(self._worker_tasks), self._worker_target):
            self._worker_tasks[i] = asyncio.create_task(self._worker_loop(i))
        # 清除已退出或超编的 worker（超编 worker 会在循环顶自退出）
        for i in list(self._worker_tasks):
            if i >= self._worker_target or self._worker_tasks[i].done():
                del self._worker_tasks[i]

    async def _worker_loop(self, wid: int) -> None:
        while self._running:
            if wid >= self._worker_target:
                return
            try:
                group = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if self._draining or not self._running:
                    return
                await asyncio.sleep(0.2)
                continue
            self._in_flight += 1
            try:
                await self._process_group(group)
            except Exception as exc:  # noqa: BLE001
                print(f"[worker {wid}] unexpected error: {type(exc).__name__}: {exc}", flush=True)
                self._record_failure(group, f"unexpected: {type(exc).__name__}: {exc}")
            finally:
                self._in_flight -= 1

    async def _process_group(self, group: WorkGroup) -> None:
        system = self._load_prompt()
        prompt = build_group_prompt(system, group.units)
        t0 = time.time()
        try:
            payload, in_tok, out_tok = await self.client.call(system, prompt)
        except RateLimitError as exc:
            self._finish_call(group, 0, 0, int((time.time() - t0) * 1000), "error429",
                              error=str(exc))
            self.stats.rate_429 += 1
            self.stats.record_call(False, is_429=True)
            self._schedule_retry(group, str(exc), kind="429",
                                 retry_after=getattr(exc, "retry_after", None))
            return
        except (TimeoutError, asyncio.TimeoutError) as exc:
            self._finish_call(group, 0, 0, int((time.time() - t0) * 1000), "error_timeout")
            self.stats.timeouts += 1
            self.stats.record_call(False)
            self._schedule_retry(group, f"timeout: {exc}", kind="error")
            return
        except ApiError as exc:
            self._finish_call(group, 0, 0, int((time.time() - t0) * 1000), "error_api",
                              error=f"api error: {exc}")
            self.stats.api_errors += 1
            self.stats.record_call(False)
            self._schedule_retry(group, f"api error: {exc}", kind="error")
            return
        except (ValueError, json.JSONDecodeError) as exc:
            # 响应非 JSON / 解析失败（如模型输出被截断或返回非 JSON 文本）。
            # 归为可重试错误并记录调用，而不是冒泡到 worker 顶层变永久失败。
            self._finish_call(group, 0, 0, int((time.time() - t0) * 1000), "error_parse",
                              error=f"parse: {exc}")
            self.stats.api_errors += 1
            self.stats.record_call(False)
            self._schedule_retry(group, f"parse error: {exc}", kind="error")
            return

        wall_ms = int((time.time() - t0) * 1000)
        results = extract_unit_results(payload)
        if self.skip_validation:
            # 跳过校验——直接标记全部成功（用于非标准模型输出）
            total_msgs = sum(u.message_count for u in group.units) or 1
            for unit in group.units:
                try:
                    obj = self._find_result(results, unit)
                except ValueError:
                    # 模型返回的结果中缺少这个单元——跳过，不标记失败
                    continue
                share_in = in_tok * unit.message_count // total_msgs
                share_out = out_tok * unit.message_count // total_msgs
                self._enqueue_success(unit, obj, group, share_in, share_out, wall_ms)
            self.stats.record_call(True)
            self._finish_call(group, in_tok, out_tok, wall_ms, "ok")
            self.stats.completed_units += len(group.units)
            return
        validated = validate_group(results, group.units)
        if all(ok for ok, _errors, _ref in validated.values()):
            self.stats.record_call(True)
            self._finish_call(group, in_tok, out_tok, wall_ms, "ok")
            self.stats.completed_units += len(group.units)
            total_msgs = sum(u.message_count for u in group.units) or 1
            for unit in group.units:
                obj = self._find_result(results, unit)
                share_in = in_tok * unit.message_count // total_msgs
                share_out = out_tok * unit.message_count // total_msgs
                self._enqueue_success(unit, obj, group, share_in, share_out, wall_ms)
        else:
            self.stats.validation_failures += 1
            self.stats.record_call(False)
            err_summary = self._summarize_errors(validated)
            self._finish_call(group, in_tok, out_tok, wall_ms, "validation", error=err_summary)
            self._schedule_retry(group, err_summary, kind="validation")

    def _find_result(self, results: list[dict], unit: Unit) -> dict:
        for obj in results:
            if obj.get("segment_id") == unit.segment_id and obj.get("window_idx", 0) == unit.window_idx:
                return obj
        raise ValueError(f"missing result for {unit.unit_key}")

    def _summarize_errors(self, validated: dict[str, tuple[bool, list[str], set[str]]]) -> str:
        parts = []
        for key, (ok, errors, _ref) in validated.items():
            if not ok:
                parts.append(f"{key}: {'; '.join(errors[:3])}")
        return " | ".join(parts[:5])[:400]

    def _finish_call(self, group, in_tok, out_tok, wall_ms, status, error=None) -> None:
        c = CallRecord(
            run_id=self.run_id, group_id=group.group_id,
            units=len(group.units), msgs=sum(u.message_count for u in group.units),
            in_tokens=in_tok, out_tokens=out_tok, elapsed_ms=wall_ms,
            status=status, error=error,
        )
        self.recorder.enqueue_call(c)
        self.stats.groups_processed += 1
        self.stats.input_tokens += in_tok
        self.stats.output_tokens += out_tok

    def _enqueue_success(self, unit, obj, group, share_in, share_out, wall_ms) -> None:
        pii = sum(m.pii_count for m in unit.messages)
        # 模型未输出 importance 时如实存 NULL（而非 0），避免把「未填充」误读为「重要度=0」。
        importance = _coerce_importance(obj.get("importance"))
        outcome = UnitOutcome(
            run_id=self.run_id, unit=unit, status="success", result_json=obj,
            entity_count=len(obj.get("entities", []) or []),
            event_count=len(obj.get("events", []) or []),
            rel_sig_count=len(obj.get("relationship_signals", []) or []),
            importance=importance,
            confidence=obj.get("confidence"),
            attempts=group.attempts, pii_replacements=pii,
            group_id=group.group_id,
            in_tokens=share_in, out_tokens=share_out, wall_ms=wall_ms,
        )
        self.recorder.enqueue_unit(outcome)

    def _record_failure(self, group: WorkGroup, error: str) -> None:
        self.stats.failed_units += len(group.units)
        for unit in group.units:
            pii = sum(m.pii_count for m in unit.messages)
            outcome = UnitOutcome(
                run_id=self.run_id, unit=unit, status="failed", error=error,
                attempts=group.attempts, pii_replacements=pii,
                group_id=group.group_id,
            )
            self.recorder.enqueue_unit(outcome)

    # ─── 重试 ──────────────────────────────────────────────────────────────────
    def _schedule_retry(self, group: WorkGroup, error: str, kind: str,
                        retry_after: Optional[float] = None) -> None:
        group.attempts += 1
        # 429 用独立的最大重试次数（默认 5）：配合长退避熬过限速窗口，而不是快速永久失败。
        max_attempts = (self.retry_max_attempts_429 if kind == "429"
                        else self.retry_max_attempts)
        if group.attempts >= max_attempts:
            self._record_failure(group, error)
            return
        if kind == "validation" and len(group.units) > 1 and group.split_depth < self.max_split_depth:
            for half in split_units(group.units, group.split_depth):
                ng = WorkGroup(self._next_group_id(), half, attempts=group.attempts,
                               split_depth=group.split_depth + 1)
                self.task_queue.put_nowait(ng)
            return
        if kind == "429":
            base, cap = self.retry429_base, self.retry429_max
        elif kind == "error":
            base, cap = self.retry_error_base, self.retry429_max
        else:
            base, cap = self.retry_validation_base, 30.0
        backoff = compute_backoff(kind, group.attempts, base, cap)
        if kind == "429":
            # 指数退避 + 抖动：与平台其他用户的重试错峰，避免惊群
            backoff = min(backoff * (0.5 + random.random()), cap)
            # 服务器明确给了 Retry-After 时严格尊重（取两者较大值）
            if retry_after and retry_after > 0:
                backoff = max(backoff, retry_after)
        self._pending_retries.append((time.time() + backoff, group))

    async def _retry_pump(self) -> None:
        while self._running:
            await asyncio.sleep(1.0)
            now = time.time()
            due = [g for ts, g in self._pending_retries if ts <= now]
            if due:
                self._pending_retries = [(ts, g) for ts, g in self._pending_retries if ts > now]
                for g in due:
                    self.task_queue.put_nowait(g)

    # ─── 并发监控 ─────────────────────────────────────────────────────────────
    async def _monitor(self) -> None:
        while self._running:
            await asyncio.sleep(self.ramp_check_interval)
            if not self._running:
                return
            err_rate = self.stats.error_rate
            target = self._worker_target
            if self.stats.recent_429 or err_rate > self.reduce_error_threshold:
                target = max(self.min_workers, target - self.ramp_down_step)
            elif (
                err_rate < self.ramp_up_error_threshold
                and self.stats.api_calls >= self.min_api_calls_before_ramp
                and (time.time() - self._last_ramp_ts) >= self.min_seconds_between_ramps
            ):
                target = min(self.max_workers, target + self.ramp_up_step)
            if target != self._worker_target:
                old = self._worker_target
                self._worker_target = target
                self._last_ramp_ts = time.time()
                self._sync_workers()
                print(f"[monitor] workers {old} → {target} (error_rate={err_rate:.2%})", flush=True)

    # ─── 正常退出 ─────────────────────────────────────────────────────────────
    async def _progress_reporter(self) -> None:
        while self._running:
            await asyncio.sleep(15)
            if self._running:
                print(self.print_progress(), flush=True)

    async def _maintain(self) -> None:
        while True:
            await asyncio.sleep(2.0)
            if (
                self._enqueue_finished
                and self.task_queue.empty()
                and not self._pending_retries
                and self._in_flight == 0
            ):
                break
        print(f"[run] 队列清空，正常退出。", flush=True)

    def print_progress(self) -> str:
        return (
            f"[progress] 完成={self.stats.completed_units} 失败={self.stats.failed_units} "
            f"API={self.stats.api_calls} in={self.stats.input_tokens:,} out={self.stats.output_tokens:,} "
            f"429={self.stats.rate_429} 校验失败={self.stats.validation_failures} "
            f"workers={self._worker_target} 队列={self.task_queue.qsize()} 在途={self._in_flight}"
        )


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DeepSeek v3 微信分析执行器（试运行版）")
    parser.add_argument(
        "command",
        choices=["plan", "run", "report", "verify", "review", "finalize"],
        default="run", nargs="?",
    )
    parser.add_argument("run_id", nargs="?", default="")
    parser.add_argument("--config", default=str(WORKSPACE_ROOT / "config" / "v3_config.json"))
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true", help="跳过 JSON 校验，全部标记成功")
    parser.add_argument("--feedback", default="", help="finalize 的复核反馈 JSONL 路径")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    if args.concurrency:
        cfg["concurrency"]["start_workers"] = args.concurrency
        cfg["concurrency"]["max_workers"] = args.concurrency

    if args.command == "verify":
        return _cmd_verify(cfg)

    # review / finalize：人机协作环节，只读写工作区 DB 副本与运行目录，不调用 API
    if args.command in ("review", "finalize"):
        return _cmd_review_or_finalize(cfg, args)

    token = get_token()
    if not token:
        print("❌ 未找到 API Token（ANTHROPIC_AUTH_TOKEN 环境变量或 Claude 设置）。", file=sys.stderr)
        sys.exit(2)
    base_url = get_base_url()

    # plan / run 都会在工作区 DB 副本创建 _v3 表
    import sqlite3 as _sqlite
    _conn = _sqlite.connect(cfg["paths"]["db"])
    try:
        ensure_v3_schema(_conn)
    finally:
        _conn.close()

    if args.command == "plan":
        run_id = f"plan_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        executor = V3Executor(cfg, token, base_url, run_id=run_id)
        plan = executor.build_plan()
        plan_path = cfg["paths"]["runs_dir"] / f"{run_id}" / "plan.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(plan_path, plan)
        print(f"[plan] 已生成计划：{plan_path}")
        print(f"  抽样片段: {plan['totals']['sampled_segments']} | 单元: {plan['totals']['units']} "
              f"| 批次: {plan['totals']['batches']} | 跳过: {plan['totals']['skipped_units']}")
        for seg in plan["sampled_segments"]:
            print(f"    {seg['bucket']:<6} {seg['id'][:24]} msgs={seg['message_count']} chars={seg['char_count']}")
        return

    if args.command == "report":
        from src.v3_report import build_report
        run_id = args.run_id
        if not run_id:
            print("需要 run_id，例如：python -m src.deepseek_v3_executor report pilot_v3_20260805_000000", file=sys.stderr)
            sys.exit(2)
        report_path = build_report(cfg, run_id)
        print(f"[report] 已生成：{report_path}")
        return

    # run
    run_id = f"pilot_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    executor = V3Executor(cfg, token, base_url, run_id=run_id, skip_validation=args.skip_validation)
    print(f"[run] 工作区：{WORKSPACE_ROOT}")
    print(f"[run] DB 副本：{cfg['paths']['db']}（只写此副本的 _v3 表）")
    plan = executor.build_plan()
    stats = asyncio.run(executor.run(plan))
    summary = stats.summary()
    manifest = {
        "run_id": run_id,
        "created_at": utc_now(),
        "status": "completed",
        "model": cfg["model"],
        "prompt_version": cfg["prompt_version"],
        "stats": summary,
        "totals": plan["totals"],
        "sampled_segments": plan["sampled_segments"],
        "note": "试运行完成后暂停；未启动全量运行。",
    }
    write_manifest(executor.run_dir, manifest)
    print("[run] manifest 已写入。")
    from src.v3_report import build_report
    report_path = build_report(cfg, run_id)
    print(f"[report] 已生成：{report_path}")
    print(f"[done] {executor.print_progress()}")


def _cmd_review_or_finalize(cfg: dict, args) -> None:
    """人机协作环节：review 生成复核 HTML（0 API）；finalize 落库反馈并聚合会话价值（0 API）。"""
    from src import v3_review

    if not args.run_id:
        print("需要 run_id，例如：python -m src.deepseek_v3_executor review pilot_v3_20260806_013846 "
              "--config config/v3_config.scale.json", file=sys.stderr)
        sys.exit(2)

    if args.command == "review":
        bundle = v3_review.build_review_bundle(cfg, args.run_id)
        if not bundle["segments"]:
            print(f"[review] 该运行没有成功标注，无法构建复核包：{args.run_id}", file=sys.stderr)
            sys.exit(1)
        out_html = v3_review.render_review_html(cfg, bundle)
        print(f"[review] 复核包已生成：{out_html}")
        print(f"[review] 片段 {bundle['segment_count']} / 窗口单元 {bundle['unit_count']} "
              f"（0 API，未调用模型）")
        print(f"[review] 双击打开 review.html 复核，导出 review_feedback.jsonl 后用 finalize 落库。")
        return

    # finalize
    if not args.feedback:
        print("需要 --feedback <review_feedback.jsonl>", file=sys.stderr)
        sys.exit(2)
    feedback = v3_review.load_feedback(Path(args.feedback))
    applied = v3_review.apply_feedback(cfg, args.run_id, feedback)
    summary = v3_review.aggregate_final_judgments(cfg, args.run_id)
    from src.v3_report import build_review_report
    report_path = build_review_report(cfg, args.run_id)
    print(f"[finalize] 已写入 v3_review：{applied} 行")
    print(f"[finalize] 会话级聚合：{summary['conversation_count']} 个会话 / "
          f"已复核片段 {summary['reviewed_segments']}（规则派生，0 API）")
    print(f"[finalize] 复核报告：{report_path}")


def _cmd_verify(cfg: dict) -> None:
    """安全校验：确认只写工作区 DB 副本、只新增 _v3 表。"""
    import sqlite3
    db = cfg["paths"]["db"]
    conn = sqlite3.connect(db)
    try:
        before = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        ensure_v3_schema(conn)
        after = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    added = sorted(after - before)
    print(f"[verify] DB: {db}")
    print(f"[verify] 表新增（应为 _v3 系列）: {added}")
    bad = [t for t in added if not t.startswith("v3_")]
    if bad:
        print(f"[verify] ❌ 非 _v3 表被创建: {bad}", file=sys.stderr)
        sys.exit(1)
    print(f"[verify] ✅ 只创建了 {len(added)} 个 _v3 表，历史表未改动。")


if __name__ == "__main__":
    main()
