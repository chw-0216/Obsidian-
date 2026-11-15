"""v3 无 API 测试：结构、Schema、数据库、合批、窗口、重试、并发池。

运行：python -m unittest discover -s tests -v
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.v3_core import (  # noqa: E402
    ParsedMessage,
    Unit,
    build_group_prompt,
    build_units,
    chunk_messages,
    clean_text,
    compute_backoff,
    extract_unit_results,
    make_batches,
    parse_transcript,
    redact_for_model,
    split_units,
    stratified_sample,
    validate_group,
    validate_unit,
)
from src.v3_io import (  # noqa: E402
    CallRecord,
    Recorder,
    RunMeta,
    UnitOutcome,
    ensure_v3_schema,
    read_jsonl,
)
from src.deepseek_v3_executor import (  # noqa: E402
    V3Executor,
    _coerce_importance,
    bucket_of,
    load_config,
)
from src import v3_hist, v3_review  # noqa: E402


def _msg(eid: str, sender: str = "我", mtype: str = "文本", content: str = "你好",
         ts: str = "2026-01-01 00:00:00") -> ParsedMessage:
    redacted, pii = redact_for_model(clean_text(content))
    return ParsedMessage(eid, ts, sender, mtype, clean_text(content), redacted, pii)


def _transcript(msgs: list[tuple[str, str, str, str]]) -> str:
    out = []
    for eid, sender, mtype, content in msgs:
        out.append(f"[id={eid}][2026-01-01 00:00:00][{sender}][{mtype}] {content}")
    return "\n".join(out)


def _review_cfg(tmp: str) -> dict:
    """复核流程测试用最小配置（临时 DB + 临时 runs 目录）。"""
    return {
        "paths": {"db": str(Path(tmp) / "db.sqlite3"), "runs_dir": str(Path(tmp) / "runs")},
        "batching": {"window_size_msgs": 15},
    }


_SEGMENTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS segments (
  id TEXT PRIMARY KEY, conversation_id TEXT, ordinal INTEGER,
  start_ts TEXT, end_ts TEXT, message_count INTEGER, char_count INTEGER,
  transcript TEXT, content_sha256 TEXT, updated_at TEXT
);
"""


def _seed_review_db(cfg: dict, run_id: str, segments: list[dict], units: list[dict]) -> None:
    """向临时 DB 写入 segments 与成功标注，供复核流程测试。

    ensure_v3_schema 只建 _v3 表，segments 表按真实结构在此创建。
    """
    conn = sqlite3.connect(cfg["paths"]["db"])
    try:
        conn.executescript(_SEGMENTS_SCHEMA_SQL)
        ensure_v3_schema(conn)
        for s in segments:
            conn.execute(
                "INSERT INTO segments(id, conversation_id, ordinal, message_count, char_count, transcript) "
                "VALUES (?,?,?,?,?,?)",
                (s["id"], s.get("conversation_id", ""), s.get("ordinal", 0),
                 s.get("message_count", 0), s.get("char_count", 0), s["transcript"]),
            )
        for u in units:
            conn.execute(
                """INSERT INTO v3_annotations(run_id, unit_key, segment_id, window_idx, content_sha256,
                   segment_sha256, conversation_id, message_count, char_count, model, prompt_version,
                   status, result_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, u["unit_key"], u["segment_id"], u.get("window_idx", 0),
                 u.get("content_sha256", "h"), u.get("segment_sha256", "sh"),
                 u.get("conversation_id", ""), u.get("message_count", 0), u.get("char_count", 0),
                 "deepseek-v4-flash", "base-v1.1-compact", "success",
                 json.dumps(u["result_json"], ensure_ascii=False),
                 "2026-08-06T00:00:00+08:00", "2026-08-06T00:00:00+08:00"),
            )
        conn.commit()
    finally:
        conn.close()


class TranscriptTests(unittest.TestCase):
    def test_parse_basic(self) -> None:
        t = _transcript([("msg_a", "我", "文本", "你好"), ("msg_b", "对方", "文本", "在吗")])
        msgs = parse_transcript(t)
        self.assertEqual([m.evidence_id for m in msgs], ["msg_a", "msg_b"])
        self.assertEqual(msgs[0].sender, "我")
        self.assertEqual(msgs[0].content, "你好")

    def test_parse_multiline_content(self) -> None:
        t = (
            "[id=msg_a][2026-01-01 00:00:00][我][文本] 第一行\n第二行\n第三行\n"
            "[id=msg_b][2026-01-01 00:01:00][对方][文本] 好的"
        )
        msgs = parse_transcript(t)
        self.assertEqual(len(msgs), 2)
        self.assertIn("第二行", msgs[0].content)

    def test_parse_missing_type_bracket(self) -> None:
        t = "[id=msg_a][2026-01-01 00:00:00][我] 无类型消息"
        msgs = parse_transcript(t)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].msg_type, "")

    def test_clean_html_entities(self) -> None:
        self.assertEqual(clean_text("a&#x0A;b&#x20;c"), "a\nb c")
        self.assertEqual(clean_text("A&amp;B &lt;3"), "A&B <3")

    def test_redact_pii(self) -> None:
        redacted, count = redact_for_model("电话 13800138000，邮箱 test@example.com")
        self.assertEqual(count, 2)
        self.assertNotIn("13800138000", redacted)
        self.assertNotIn("test@example.com", redacted)


class WindowAndBatchTests(unittest.TestCase):
    def test_window_slicing(self) -> None:
        msgs = [_msg(f"m{i:02d}") for i in range(40)]
        windows = chunk_messages(msgs, 15)
        self.assertEqual([len(w) for w in windows], [15, 15, 10])
        self.assertEqual(windows[0][0].evidence_id, "m00")
        self.assertEqual(windows[2][-1].evidence_id, "m39")

    def test_build_units_short_is_single(self) -> None:
        units = build_units("seg_x", _transcript([("m1", "我", "文本", "a")]), "sha", window_size=15)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].window_idx, 0)

    def test_build_units_long_is_windowed(self) -> None:
        msgs = [("m%02d" % i, "我", "文本", f"内容{i}") for i in range(32)]
        units = build_units("seg_y", _transcript(msgs), "sha", window_size=15)
        self.assertEqual(len(units), 3)
        self.assertEqual([u.message_count for u in units], [15, 15, 2])
        # 每个窗口只含对应文本
        self.assertEqual(units[1].messages[0].evidence_id, "m15")
        self.assertNotIn("内容0", "\n".join(u.render_for_prompt() for u in units[1:]))

    def test_make_batches_respects_budget(self) -> None:
        # 20 个单消息单元：合批后每个批次累计估计输出 ≤ 预算
        units = []
        for i in range(20):
            u = Unit(segment_id=f"seg_{i}", window_idx=0, messages=[_msg(f"m{i:02d}")])
            units.append(u)
        budget = 5000
        batches = make_batches(units, max_output_tokens=budget, max_units_per_batch=8, max_msgs_per_batch=30)
        for b in batches:
            est = sum(900 + 231 * u.message_count for u in b)
            if len(b) > 1:
                self.assertLessEqual(est, budget)
        self.assertGreaterEqual(len(batches), 3)  # 20 个单元 / 每批至多 8

    def test_batch_prompt_only_contains_unit_text(self) -> None:
        msgs = [("m%02d" % i, "我", "文本", f"正文{i}") for i in range(32)]
        units = build_units("seg_z", _transcript(msgs), "sha", window_size=15)
        prompt = build_group_prompt("SYS", units[:2])  # 只取前两个窗口（共 3 个窗口）
        self.assertIn("segment_id=seg_z", prompt)
        self.assertIn("正文0", prompt)
        self.assertIn("正文15", prompt)
        self.assertNotIn("正文30", prompt)  # 未纳入的第三个窗口文本不得出现

    def test_make_batches_oversized_unit_alone(self) -> None:
        # 单条 5 万字符消息 → 只能独占一批（max_input_chars 上限）
        big = _msg("mbig", content="长" * 60000)
        u = Unit(segment_id="seg", window_idx=0, messages=[big])
        batches = make_batches([u], max_input_chars_per_batch=40000)
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0][0].unit_key, u.unit_key)


class ValidationTests(unittest.TestCase):
    def _unit(self) -> Unit:
        msgs = [_msg("m1", "我", "文本", "明天见"), _msg("m2", "对方", "文本", "好的")]
        return Unit(segment_id="seg_v", window_idx=0, messages=msgs)

    def _good_result(self, seg_id: str = "seg_v") -> dict:
        return {
            "segment_id": seg_id,
            "window_idx": 0,
            "summary": "简短约定",
            "messages": [
                {"evidence_id": "m1", "content_function": "通知", "topic": "t", "intent": "i",
                 "is_request": False, "is_commitment": False, "is_boundary": False,
                 "observable_tone": "平静", "inferred_emotion": "无", "confidence": 0.9},
                {"evidence_id": "m2", "content_function": "确认", "topic": "t", "intent": "i",
                 "is_request": False, "is_commitment": False, "is_boundary": False,
                 "observable_tone": "平静", "inferred_emotion": "无", "confidence": 0.8},
            ],
            "requests": [{"description": "约明天", "requester": "me", "evidence_ids": ["m1"]}],
            "commitments": [],
            "events": [{"event_type": "future_plan", "description": "明天见", "time_reference": "明天",
                        "people_involved": [], "outcome": "", "confidence": 0.9, "evidence_ids": ["m2"]}],
            "entities": [],
            "relationship_signals": [],
            "memory_candidates": [],
            "alternative_explanations": [],
            "confidence": 0.85,
            "evidence_ids": ["m1", "m2"],
        }

    def test_validate_ok(self) -> None:
        unit = self._unit()
        ok, errors, _ = validate_unit(self._good_result(), unit)
        self.assertTrue(ok, errors)

    def test_validate_missing_evidence_fails(self) -> None:
        unit = self._unit()
        result = self._good_result()
        result["messages"] = result["messages"][:1]
        ok, errors, _ = validate_unit(result, unit)
        self.assertFalse(ok)
        self.assertTrue(any("缺少证据ID" in e for e in errors))

    def test_validate_extra_hallucinated_fails(self) -> None:
        unit = self._unit()
        result = self._good_result()
        result["messages"].append({"evidence_id": "nope999", "content_function": "x", "confidence": 0.5})
        ok, errors, _ = validate_unit(result, unit)
        self.assertFalse(ok)
        self.assertTrue(any("多余证据ID" in e for e in errors))

    def test_validate_reference_outside_expected_fails(self) -> None:
        unit = self._unit()
        result = self._good_result()
        result["events"][0]["evidence_ids"] = ["bogus000"]
        ok, errors, _ = validate_unit(result, unit)
        self.assertFalse(ok)
        self.assertTrue(any("不存在的证据ID" in e for e in errors))

    def test_validate_group_missing_unit(self) -> None:
        unit = self._unit()
        results = [self._good_result()]
        validated = validate_group(results, [unit])
        self.assertTrue(validated[unit.unit_key][0])

    def test_extract_unit_results_shapes(self) -> None:
        arr = [{"segment_id": "s", "window_idx": 0}]
        self.assertEqual(len(extract_unit_results(arr)), 1)
        wrapped = {"results": arr}
        self.assertEqual(len(extract_unit_results(wrapped)), 1)
        single = {"segment_id": "s", "window_idx": 0}
        self.assertEqual(len(extract_unit_results(single)), 1)

    def test_split_units(self) -> None:
        units = [self._unit()]
        halves = split_units(units, 0)
        self.assertEqual(len(halves), 1)
        units2 = [self._unit(), self._unit()]
        halves = split_units(units2, 0)
        self.assertEqual(len(halves), 2)


class MiscLogicTests(unittest.TestCase):
    def test_compute_backoff(self) -> None:
        self.assertEqual(compute_backoff("429", 1, 8, 60), 8)
        self.assertEqual(compute_backoff("429", 3, 8, 60), 32)
        self.assertEqual(compute_backoff("429", 5, 8, 60), 60)  # 封顶

    def test_bucket_of(self) -> None:
        self.assertEqual(bucket_of(1), "1")
        self.assertEqual(bucket_of(3), "2-3")
        self.assertEqual(bucket_of(10), "4-10")
        self.assertEqual(bucket_of(30), "11-30")
        self.assertEqual(bucket_of(31), "31+")
        self.assertEqual(bucket_of(60), "31+")

    def test_unit_sha_deterministic(self) -> None:
        u1 = Unit(segment_id="s", window_idx=0, messages=[_msg("m1")])
        u2 = Unit(segment_id="s", window_idx=0, messages=[_msg("m1")])
        self.assertEqual(u1.content_sha256, u2.content_sha256)

    def test_coerce_importance(self) -> None:
        # 模型未输出 → None（存 NULL），不能落成 0
        self.assertIsNone(_coerce_importance(None))
        self.assertIsNone(_coerce_importance({}))
        # 真实输出（数字/数字字符串）→ 归一为 int
        self.assertEqual(_coerce_importance(3), 3)
        self.assertEqual(_coerce_importance(3.7), 3)
        self.assertEqual(_coerce_importance("5"), 5)
        self.assertEqual(_coerce_importance(0), 0)  # 显式 0 是真实 0，保留
        # 非法值 → None，而不是崩溃或假 0
        self.assertIsNone(_coerce_importance("abc"))
        self.assertIsNone(_coerce_importance(True))


class DbRecorderTests(unittest.TestCase):
    def test_recorder_roundtrip(self) -> None:
        async def scenario(tmp_db: str, run_dir: Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1")
            await rec.start()
            unit = Unit(segment_id="seg_ok", window_idx=0, messages=[_msg("m1")],
                        segment_sha256="sh", conversation_id="conv1")
            outcome = UnitOutcome(
                run_id="run_t", unit=unit, status="success",
                result_json={
                    "segment_id": "seg_ok", "window_idx": 0,
                    "summary": "s",
                    "messages": [{"evidence_id": "m1", "content_function": "通知", "topic": "t",
                                  "intent": "i", "is_request": False, "is_commitment": False,
                                  "is_boundary": False, "observable_tone": "平", "inferred_emotion": "无",
                                  "confidence": 0.9}],
                    "entities": [], "events": [], "relationship_signals": [],
                    "confidence": 0.9, "evidence_ids": ["m1"],
                },
                entity_count=0, event_count=0, rel_sig_count=0, confidence=0.9,
                group_id="g1", in_tokens=10, out_tokens=5, wall_ms=100,
            )
            rec.enqueue_unit(outcome)
            rec.enqueue_call(CallRecord("run_t", "g1", 1, 1, 10, 5, 100, "ok"))
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v3_annotations").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v3_message_annotations").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v3_call_log").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT status FROM v3_annotations").fetchone()[0], "success")
            conn.close()
            tasks = read_jsonl(run_dir / "tasks.jsonl")
            results = read_jsonl(run_dir / "results.jsonl")
            calls = read_jsonl(run_dir / "call_log.jsonl")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(len(results), 1)
            self.assertEqual(len(calls), 1)

    def test_recorder_importance_none_when_absent(self) -> None:
        # result_json 无 importance 且 UnitOutcome 未传 importance → 落库 NULL，而非 0
        async def scenario(tmp_db: str, run_dir: Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1")
            await rec.start()
            unit = Unit(segment_id="seg_ok", window_idx=0, messages=[_msg("m1")],
                        segment_sha256="sh", conversation_id="conv1")
            outcome = UnitOutcome(
                run_id="run_t", unit=unit, status="success",
                result_json={
                    "segment_id": "seg_ok", "window_idx": 0, "summary": "s",
                    "messages": [{"evidence_id": "m1", "content_function": "通知", "topic": "t",
                                  "intent": "i", "is_request": False, "is_commitment": False,
                                  "is_boundary": False, "observable_tone": "平", "inferred_emotion": "无",
                                  "confidence": 0.9}],
                    "entities": [], "events": [], "relationship_signals": [],
                    "confidence": 0.9, "evidence_ids": ["m1"],
                },
                entity_count=0, event_count=0, rel_sig_count=0, confidence=0.9,
                group_id="g1", in_tokens=10, out_tokens=5, wall_ms=100,
            )
            rec.enqueue_unit(outcome)
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            val = conn.execute("SELECT importance FROM v3_annotations").fetchone()[0]
            conn.close()
            self.assertIsNone(val)

    def test_recorder_failure(self) -> None:
        async def scenario(tmp_db: str, run_dir: Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1")
            await rec.start()
            unit = Unit(segment_id="seg_bad", window_idx=0, messages=[_msg("m1")])
            rec.enqueue_unit(UnitOutcome(run_id="run_t", unit=unit, status="failed", error="429 耗尽", attempts=3))
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            self.assertEqual(conn.execute("SELECT status FROM v3_annotations").fetchone()[0], "failed")
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v3_failures").fetchone()[0], 1)
            conn.close()
            self.assertEqual(len(read_jsonl(run_dir / "failures.jsonl")), 1)

    def test_recorder_writes_run_meta(self) -> None:
        async def scenario(tmp_db: str, run_dir: Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1.1-compact")
            await rec.start()
            rec.enqueue_run_meta(RunMeta(
                run_id="run_r", started_at="2026-08-05T20:00:00+08:00", status="running",
                model="deepseek-v4-flash", prompt_version="base-v1.1-compact",
                config_json={"k": "v"},
            ))
            rec.enqueue_run_meta(RunMeta(
                run_id="run_r", started_at="2026-08-05T20:00:00+08:00",
                finished_at="2026-08-05T20:10:00+08:00", status="completed",
                model="deepseek-v4-flash", prompt_version="base-v1.1-compact",
                config_json={"k": "v"}, stats_json={"units": 5},
            ))
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            row = conn.execute("SELECT status, prompt_version, stats_json FROM v3_run_meta WHERE run_id='run_r'").fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "completed")
            self.assertEqual(row[1], "base-v1.1-compact")
            self.assertEqual(json.loads(row[2])["units"], 5)

    def test_recorder_run_meta_accepts_path_config(self) -> None:
        """真实配置含 WindowsPath 对象，run_meta 序列化必须 default=str，不能崩掉 recorder。"""
        from pathlib import Path as _Path

        async def scenario(tmp_db: str, run_dir: _Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1.1-compact")
            await rec.start()
            rec.enqueue_run_meta(RunMeta(
                run_id="run_p", started_at="2026-08-05T20:00:00+08:00", status="completed",
                model="deepseek-v4-flash", prompt_version="base-v1.1-compact",
                config_json={"paths": {"db": _Path("data/scale/x.sqlite3")}, "n": 1},
                stats_json={"units": 3},
            ))
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            row = conn.execute("SELECT status, config_json FROM v3_run_meta WHERE run_id='run_p'").fetchone()
            conn.close()
            self.assertIsNotNone(row)
            cfg = json.loads(row[1])
            # default=str 序列化后是平台的 Path 字符串形式（Windows 下为反斜杠）
            self.assertEqual(cfg["paths"]["db"], str(_Path("data/scale/x.sqlite3")))

    def test_recorder_success_clears_stale_failure(self) -> None:
        """此前运行失败、本次运行成功的同一 unit_key，失败残留应被清除。"""
        async def scenario(tmp_db: str, run_dir: Path) -> None:
            conn = sqlite3.connect(tmp_db)
            ensure_v3_schema(conn)
            # 模拟上一次运行留下的 failure（不同 run_id）
            conn.execute(
                "INSERT INTO v3_failures(run_id, unit_key, segment_id, window_idx, attempts, error, created_at) "
                "VALUES('run_old', 'seg_x:0', 'seg_x', 0, 3, '429 耗尽', '2026-08-05T10:00:00+08:00')"
            )
            conn.commit()
            conn.close()
            rec = Recorder(tmp_db, run_dir, "deepseek-v4-flash", "base-v1.1-compact")
            await rec.start()
            unit = Unit(segment_id="seg_x", window_idx=0, messages=[_msg("m1")],
                        segment_sha256="sh", conversation_id="conv1")
            outcome = UnitOutcome(
                run_id="run_new", unit=unit, status="success",
                result_json={
                    "segment_id": "seg_x", "window_idx": 0, "summary": "s",
                    "messages": [{"evidence_id": "m1", "content_function": "通知",
                                  "intent": "i", "is_request": False, "is_commitment": False,
                                  "is_boundary": False, "observable_tone": "平",
                                  "inferred_emotion": "无", "confidence": 0.9}],
                    "confidence": 0.9, "evidence_ids": ["m1"],
                },
                confidence=0.9, group_id="g1", in_tokens=10, out_tokens=5, wall_ms=100,
            )
            rec.enqueue_unit(outcome)
            await rec.stop()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = str(Path(tmp) / "t.sqlite3")
            run_dir = Path(tmp) / "run"
            asyncio.run(scenario(tmp_db, run_dir))
            conn = sqlite3.connect(tmp_db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v3_failures WHERE unit_key='seg_x:0'").fetchone()[0], 0)
            # 保留 v3_annotations 的运行级历史（跨运行版本化设计）
            self.assertEqual(
                conn.execute("SELECT status FROM v3_annotations WHERE run_id='run_new' AND unit_key='seg_x:0'").fetchone()[0],
                "success",
            )
            conn.close()


class SamplingTests(unittest.TestCase):
    def _make_db(self) -> tuple[str, Path]:
        tmp = tempfile.mkdtemp()
        db = str(Path(tmp) / "s.sqlite3")
        conn = sqlite3.connect(db)
        conn.executescript("""
        CREATE TABLE segments (
          id TEXT PRIMARY KEY, conversation_id TEXT, message_count INTEGER,
          char_count INTEGER, transcript TEXT, content_sha256 TEXT, updated_at TEXT
        );
        CREATE TABLE annotations (segment_id TEXT PRIMARY KEY, result_json TEXT);
        CREATE TABLE aggressive_annotations (segment_id TEXT PRIMARY KEY, result_json TEXT);
        """)
        seg_id = 0
        sizes = [1, 2, 10, 30, 60] * 6  # 每档 6 条
        for mc in sizes:
            seg_id += 1
            conn.execute(
                "INSERT INTO segments(id, conversation_id, message_count, char_count, transcript, content_sha256) VALUES(?,?,?,?,?,?)",
                (f"seg_{seg_id}", f"conv_{seg_id}", mc, mc * 10,
                 _transcript([(f"m{seg_id}_{i}", "我", "文本", f"内容{i}") for i in range(min(mc, 3))]),
                 f"sha_{seg_id}"),
            )
        # 标注前两条单消息片段，验证优先未标注
        conn.execute("INSERT INTO annotations(segment_id, result_json) VALUES('seg_1','{}')")
        conn.execute("INSERT INTO aggressive_annotations(segment_id, result_json) VALUES('seg_2','{}')")
        conn.commit()
        conn.close()
        return db, Path(tmp)

    def test_stratified_sample_prefers_unannotated(self) -> None:
        db, tmp = self._make_db()
        conn = sqlite3.connect(db)
        try:
            ensure_v3_schema(conn)
        finally:
            conn.close()
        conn = sqlite3.connect(db)
        rows = stratified_sample(
            conn, seed=42, per_bucket=4,
            buckets=[["1", 1], ["2-3", 3], ["4-10", 10], ["11-30", 30], ["31+", 31]],
        )
        conn.close()
        by_bucket: dict[str, list] = {}
        for r in rows:
            by_bucket.setdefault(bucket_of(r["message_count"]), []).append(r)
        self.assertEqual([len(v) for v in by_bucket.values()], [4, 4, 4, 4, 4])
        # 单消息桶应避开已标注的 seg_1 / seg_2
        singles = {r["id"] for r in by_bucket["1"]}
        self.assertNotIn("seg_1", singles)
        self.assertNotIn("seg_2", singles)
        # 确定性
        conn = sqlite3.connect(db)
        rows2 = stratified_sample(conn, seed=42, per_bucket=4,
                                  buckets=[["1", 1], ["2-3", 3], ["4-10", 10], ["11-30", 30], ["31+", 31]])
        conn.close()
        self.assertEqual([r["id"] for r in rows], [r["id"] for r in rows2])


class HistNormalizationTests(unittest.TestCase):
    """历史标注（annotations / aggressive_*）归一化为 _v3_hist_* 备查表（0 API，只读源表）。"""

    _SEG_SQL = "CREATE TABLE IF NOT EXISTS segments (id TEXT PRIMARY KEY, conversation_id TEXT, message_count INTEGER, char_count INTEGER)"
    _ANN_SQL = "CREATE TABLE IF NOT EXISTS annotations (segment_id TEXT PRIMARY KEY, schema_version TEXT, model TEXT, result_json TEXT, created_at TEXT)"
    _AGR_SQL = "CREATE TABLE IF NOT EXISTS aggressive_annotations (segment_id TEXT PRIMARY KEY, schema_version TEXT, model TEXT, result_json TEXT, created_at TEXT)"
    _AGRM_SQL = (
        "CREATE TABLE IF NOT EXISTS aggressive_message_annotations ("
        " evidence_id TEXT PRIMARY KEY, segment_id TEXT, content_function TEXT, topic TEXT, speech_act TEXT,"
        " intent TEXT, is_request INTEGER, is_commitment INTEGER, is_boundary INTEGER,"
        " people_mentioned TEXT, places_mentioned TEXT, projects_mentioned TEXT, times_mentioned TEXT, events_mentioned TEXT,"
        " observable_tone TEXT, inferred_emotion TEXT, inferred_need TEXT, relationship_signal TEXT,"
        " communication_behavior TEXT, expression_style TEXT, memory_candidate TEXT, ambiguity_notes TEXT,"
        " confidence REAL, created_at TEXT)"
    )

    def _seed(self, conn: sqlite3.Connection) -> None:
        for sql in (self._SEG_SQL, self._ANN_SQL, self._AGR_SQL, self._AGRM_SQL):
            conn.execute(sql)
        conn.execute(
            "INSERT INTO segments VALUES ('seg_a','conv1',3,120),('seg_b','conv2',1,40)"
        )
        conn.execute(
            "INSERT INTO annotations VALUES ('seg_a','1.0','mimo-v2.5-pro',?,?)",
            (
                json.dumps({"segment_id": "seg_a", "importance": 0,
                            "relationship_signals": [{"signal": "x"}],
                            "summary": "s"}, ensure_ascii=False),
                "2026-01-01T00:00:00+08:00",
            ),
        )
        conn.execute(
            "INSERT INTO aggressive_annotations VALUES ('seg_b','3.0-async','mimo-v2.5-pro',?,?)",
            (
                json.dumps({"segment_id": "seg_b", "importance": 5,
                            "overall_confidence": 0.95,
                            "entities": [{"name": "A"}], "events": [], "relationship_signals": [],
                            "messages": [{"evidence_id": "msg_1"}]}, ensure_ascii=False),
                "2026-01-01T00:00:00+08:00",
            ),
        )
        conn.execute(
            "INSERT INTO aggressive_message_annotations VALUES "
            "('msg_1','seg_b','情绪表达','表达惊讶','表达惊讶',"
            "'推断',1,0,0,'[]','[]','[]','[]','[]','突然','惊讶','表达','弱信号',"
            "'突发','简洁',NULL,NULL,0.4,'2026-01-01T00:00:00+08:00')"
        )
        conn.commit()

    def test_hist_normalizes_three_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "h.sqlite3")
            conn = sqlite3.connect(db)
            try:
                self._seed(conn)
                st = v3_hist.build_v3_hist(conn)
                self.assertEqual(st["segments"], 2)
                self.assertEqual(st["messages"], 1)
                self.assertEqual(st["segments_by_source"],
                                 {"annotations": 1, "aggressive_annotations": 1})

                # 归一化字段：annotations 1.0 importance 原样保留 0；aggressive 3.0 importance=5
                r = conn.execute(
                    "SELECT source_table, importance, overall_confidence, message_count, "
                    "relationship_signal_count, key_message_count FROM _v3_hist_segments "
                    "WHERE segment_id='seg_a'").fetchone()
                self.assertEqual(r, ("annotations", 0, None, 3, 1, 0))
                r = conn.execute(
                    "SELECT importance, overall_confidence, entity_count, key_message_count "
                    "FROM _v3_hist_segments WHERE segment_id='seg_b'").fetchone()
                self.assertEqual(r, (5, 0.95, 1, 1))

                # 消息级归一
                r = conn.execute(
                    "SELECT segment_id, is_request, relationship_signal, confidence "
                    "FROM _v3_hist_messages WHERE evidence_id='msg_1'").fetchone()
                self.assertEqual(r, ("seg_b", 1, "弱信号", 0.4))
            finally:
                conn.close()

    def test_hist_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "h.sqlite3")
            conn = sqlite3.connect(db)
            try:
                self._seed(conn)
                v3_hist.build_v3_hist(conn)
                v3_hist.build_v3_hist(conn)  # 重跑不应翻倍
                self.assertEqual(
                    conn.execute("SELECT count(*) FROM _v3_hist_segments").fetchone()[0], 2)
                self.assertEqual(
                    conn.execute("SELECT count(*) FROM _v3_hist_messages").fetchone()[0], 1)
            finally:
                conn.close()


class ConcurrencyPoolTests(unittest.TestCase):
    def test_pool_creates_and_stops_workers(self) -> None:
        async def scenario() -> None:
            cfg = load_config(WORKSPACE / "config" / "v3_config.json")
            cfg["paths"]["db"] = "ignored.sqlite3"
            ex = V3Executor(cfg, "fake-token", "https://example.com")
            ex._running = True
            ex._sync_workers()
            await asyncio.sleep(0.3)
            self.assertEqual(len(ex._worker_tasks), ex.start_workers)
            # 增加并发 → 真正新建 worker
            ex._worker_target = ex.start_workers + 2
            ex._sync_workers()
            await asyncio.sleep(0.3)
            self.assertEqual(len(ex._worker_tasks), ex.start_workers + 2)
            # 降低并发 → 多余 worker 真正退出
            ex._worker_target = ex.start_workers - 2
            ex._sync_workers()
            await asyncio.sleep(1.6)
            self.assertEqual(len(ex._worker_tasks), ex.start_workers - 2)
            ex._running = False
            ex._draining = True
            for t in ex._worker_tasks.values():
                if not t.done():
                    t.cancel()
            await asyncio.gather(*ex._worker_tasks.values(), return_exceptions=True)

        asyncio.run(scenario())


class ApiClientTests(unittest.TestCase):
    """DeepSeek 兼容端点解析与请求体构造（不联网）。"""

    def test_parse_json_code_fence(self) -> None:
        from src.v3_api import parse_json
        payload = '{"segment_id": "seg_x", "messages": []}'
        self.assertEqual(parse_json(f"```json\n{payload}\n```"), json.loads(payload))

    def test_parse_json_plain(self) -> None:
        from src.v3_api import parse_json
        payload = [{"segment_id": "seg_x"}]
        self.assertEqual(parse_json(json.dumps(payload, ensure_ascii=False)), payload)

    def test_parse_json_leading_text(self) -> None:
        from src.v3_api import parse_json
        self.assertEqual(parse_json('好的，结果如下：\n{"a": 1}'), {"a": 1})

    def test_call_body_disables_thinking(self) -> None:
        """DeepSeek 兼容端点默认启用思维链会耗尽 max_tokens，必须显式禁用。"""
        from src.v3_api import ApiClient
        client = ApiClient(
            base_url="https://example.com", token="t", model="m",
            max_output_tokens=8192, disable_thinking=True,
        )
        body = client.build_body("s", "c")
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertEqual(body["model"], "m")
        self.assertEqual(body["max_tokens"], 8192)

    def test_call_body_thinking_allowed_when_disabled_false(self) -> None:
        from src.v3_api import ApiClient
        client = ApiClient(
            base_url="https://example.com", token="t", model="m",
            max_output_tokens=8192, disable_thinking=False,
        )
        body = client.build_body("s", "c")
        self.assertNotIn("thinking", body)

    def test_openai_style_url_and_body(self) -> None:
        """OpenAI 兼容端点：URL 走 /chat/completions，body 用 messages+stream，disable_thinking 时发送 thinking。"""
        from src.v3_api import ApiClient
        client = ApiClient(
            base_url="https://integrate.api.nvidia.com/v1", token="t",
            model="deepseek-ai/deepseek-v4-pro", max_output_tokens=8192,
            api_style="openai", disable_thinking=True,
        )
        self.assertEqual(client.url, "https://integrate.api.nvidia.com/v1/chat/completions")
        body = client.build_body("sys", "usr")
        self.assertEqual(body.get("thinking"), {"type": "disabled"})
        self.assertNotIn("system", body)  # system 作为 messages[0]
        self.assertEqual(body["model"], "deepseek-ai/deepseek-v4-pro")
        self.assertFalse(body["stream"])
        self.assertEqual(body["messages"][0], {"role": "system", "content": "sys"})
        self.assertEqual(body["messages"][1], {"role": "user", "content": "usr"})

    def test_anthropic_url_unchanged(self) -> None:
        """默认仍是 Anthropic 兼容，DeepSeek 官方端点不回归。"""
        from src.v3_api import ApiClient
        client = ApiClient(base_url="https://api.deepseek.com/anthropic", token="t",
                           model="m", max_output_tokens=8192)
        self.assertEqual(client.url, "https://api.deepseek.com/anthropic/v1/messages")
        self.assertIn("system", client.build_body("s", "c"))

    def test_extract_openai_text_string_and_blocks(self) -> None:
        from src.v3_api import extract_openai_text
        self.assertEqual(
            extract_openai_text({"choices": [{"message": {"content": "  {\"a\":1}  "}}]}),
            '{"a":1}',
        )
        self.assertEqual(
            extract_openai_text({"choices": [{"message": {"content": [
                {"type": "text", "text": "{\"a\":"},
                {"type": "text", "text": "1}"},
            ]}}]}),
            '{"a":\n1}',
        )

    def test_token_bucket_limits_rate(self) -> None:
        """令牌桶在 rpm 下确实限速：20 次 acquire 在 120 RPM 下至少约 9.5s。"""
        import time as _time
        from src.v3_api import TokenBucket

        async def scenario() -> None:
            bucket = TokenBucket(rpm=120, burst=1)  # 每 0.5s 一个令牌
            t0 = _time.monotonic()
            for _ in range(20):
                await bucket.acquire()
            elapsed = _time.monotonic() - t0
            # 20 个令牌，间隔 0.5s → 约 19*0.5=9.5s；留余量断言 ≥ 9.0s
            self.assertGreaterEqual(elapsed, 9.0)

        asyncio.run(scenario())


class ReviewFlowTests(unittest.TestCase):
    """人机协作复核流程（0 API）：复核包、HTML 内嵌、反馈校验、落库与聚合。"""

    def test_v3_review_tables_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "db.sqlite3")
            conn = sqlite3.connect(db)
            ensure_v3_schema(conn)
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            conn.close()
            self.assertIn("v3_review", tables)
            self.assertIn("v3_final_judgments", tables)

    def test_review_bundle_builds_from_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _review_cfg(tmp)
            transcript = _transcript([("msg_a", "我", "文本", "你好"), ("msg_b", "对方", "文本", "在吗")])
            _seed_review_db(
                cfg, "run_r",
                [{"id": "seg_a", "conversation_id": "conv1", "message_count": 2,
                  "char_count": 5, "transcript": transcript}],
                [{"unit_key": "seg_a:0", "segment_id": "seg_a", "window_idx": 0, "message_count": 2,
                  "result_json": {
                      "segment_id": "seg_a", "window_idx": 0, "summary": "s",
                      "messages": [
                          {"evidence_id": "msg_a", "content_function": "陈述", "intent": "打招呼", "confidence": 0.9},
                          {"evidence_id": "msg_b", "content_function": "提问", "intent": "询问", "confidence": 0.9},
                      ],
                      "relationship_signals": [
                          {"signal_type": "initiative", "direction": "me_to_them",
                           "description": "主动开口", "strength": 0.6, "evidence_ids": ["msg_a"]},
                      ],
                      "confidence": 0.9, "evidence_ids": ["msg_a", "msg_b"],
                  }}],
            )
            bundle = v3_review.build_review_bundle(cfg, "run_r")
            self.assertEqual(bundle["segment_count"], 1)
            self.assertEqual(bundle["unit_count"], 1)
            seg = bundle["segments"][0]
            self.assertEqual(seg["conversation_id"], "conv1")
            self.assertEqual(seg["bucket"], "2-3")
            self.assertEqual(len(seg["units"]), 1)
            u = seg["units"][0]
            self.assertEqual(len(u["evidence_lines"]), 2)
            self.assertIn("msg_a", u["evidence_lines"][0])
            self.assertEqual(u["annotation"]["relationship_signals"][0]["signal_type"], "initiative")

    def test_review_html_embeds_data_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _review_cfg(tmp)
            # 内容注入 </script>，验证内嵌数据被转义、不会破坏 HTML
            transcript = _transcript([("m1", "我", "文本", "</script><b>hack</b>")])
            _seed_review_db(
                cfg, "run_r",
                [{"id": "seg_a", "conversation_id": "conv1", "message_count": 1,
                  "char_count": 20, "transcript": transcript}],
                [{"unit_key": "seg_a:0", "segment_id": "seg_a", "window_idx": 0, "message_count": 1,
                  "result_json": {"segment_id": "seg_a", "window_idx": 0, "summary": "s",
                                  "messages": [{"evidence_id": "m1", "content_function": "陈述", "confidence": 0.9}],
                                  "confidence": 0.9, "evidence_ids": ["m1"]}}],
            )
            bundle = v3_review.build_review_bundle(cfg, "run_r")
            html_path = v3_review.render_review_html(cfg, bundle)
            html = html_path.read_text(encoding="utf-8")
            self.assertNotIn("__REVIEW_DATA__", html)  # 占位符已替换
            self.assertIn("seg_a", html)
            self.assertIn("run_r", html)
            # 模板自身恰好 1 个 </script>；注入内容若未转义会让计数 >1
            self.assertEqual(html.count("</script>"), 1)
            # 数据 JSON 里不应出现字面 </script>
            data_json = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
            self.assertNotIn("</script>", data_json)
            self.assertTrue((html_path.parent / "review_bundle.json").exists())

    def test_feedback_load_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = {
                "run_id": "run_r", "segment_id": "seg_a", "conversation_id": "conv1",
                "message_count": 2, "unit_keys": ["seg_a:0"], "review_status": "corrected",
                "corrections": {"seg_a:0": {"relationship_signals": {"0": {"action": "reject", "payload": None}}}},
                "value_score": 80, "value_tags": ["工作"], "keep_recommendation": "keep",
                "note": "n", "reviewed_at": "2026-08-06T00:00:00Z",
            }
            path = Path(tmp) / "f.jsonl"
            path.write_text(json.dumps(good, ensure_ascii=False) + "\n", encoding="utf-8")
            got = v3_review.load_feedback(path)
            self.assertEqual(len(got), 1)

            bad = Path(tmp) / "bad.jsonl"
            bad.write_text(json.dumps({"segment_id": "seg_a", "review_status": "nope"}) + "\n",
                           encoding="utf-8")
            with self.assertRaises(ValueError):
                v3_review.load_feedback(bad)

    def test_apply_and_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _review_cfg(tmp)
            t1 = _transcript([("m1", "我", "文本", "a")])
            t2 = _transcript([("m2", "我", "文本", "b")])
            t3 = _transcript([("m3", "我", "文本", "c")])
            _seed_review_db(
                cfg, "run_r",
                [{"id": "seg_a", "conversation_id": "conv1", "message_count": 1, "char_count": 1, "transcript": t1},
                 {"id": "seg_b", "conversation_id": "conv1", "message_count": 1, "char_count": 1, "transcript": t2},
                 {"id": "seg_c", "conversation_id": "conv2", "message_count": 1, "char_count": 1, "transcript": t3}],
                [{"unit_key": "seg_a:0", "segment_id": "seg_a", "window_idx": 0, "message_count": 1,
                  "result_json": {"segment_id": "seg_a", "window_idx": 0, "summary": "s",
                                  "messages": [{"evidence_id": "m1", "content_function": "陈述", "confidence": 0.9}],
                                  "confidence": 0.9, "evidence_ids": ["m1"]}},
                 {"unit_key": "seg_b:0", "segment_id": "seg_b", "window_idx": 0, "message_count": 1,
                  "result_json": {"segment_id": "seg_b", "window_idx": 0, "summary": "s",
                                  "messages": [{"evidence_id": "m2", "content_function": "陈述", "confidence": 0.9}],
                                  "confidence": 0.9, "evidence_ids": ["m2"]}},
                 {"unit_key": "seg_c:0", "segment_id": "seg_c", "window_idx": 0, "message_count": 1,
                  "result_json": {"segment_id": "seg_c", "window_idx": 0, "summary": "s",
                                  "messages": [{"evidence_id": "m3", "content_function": "陈述", "confidence": 0.9}],
                                  "confidence": 0.9, "evidence_ids": ["m3"]}}],
            )
            fb = [
                {"segment_id": "seg_a", "conversation_id": "conv1", "message_count": 1,
                 "unit_keys": ["seg_a:0"], "review_status": "confirmed", "corrections": {},
                 "value_score": 90, "value_tags": ["亲情"], "keep_recommendation": "keep", "note": ""},
                {"segment_id": "seg_b", "conversation_id": "conv1", "message_count": 1,
                 "unit_keys": ["seg_b:0"], "review_status": "confirmed", "corrections": {},
                 "value_score": 40, "value_tags": [], "keep_recommendation": "cleanup", "note": ""},
                {"segment_id": "seg_c", "conversation_id": "conv2", "message_count": 1,
                 "unit_keys": ["seg_c:0"], "review_status": "confirmed", "corrections": {},
                 "value_score": 70, "value_tags": ["工作"], "keep_recommendation": "keep", "note": ""},
            ]
            self.assertEqual(v3_review.apply_feedback(cfg, "run_r", fb), 3)
            summary = v3_review.aggregate_final_judgments(cfg, "run_r")
            self.assertEqual(summary["reviewed_segments"], 3)
            self.assertEqual(summary["conversation_count"], 2)
            conv1 = next(c for c in summary["conversations"] if c["conversation_id"] == "conv1")
            self.assertEqual(conv1["segment_count"], 2)
            self.assertEqual(conv1["reviewed_count"], 2)
            self.assertEqual(conv1["avg_value_score"], 65.0)
            self.assertEqual(conv1["min_value_score"], 40)
            self.assertEqual(conv1["max_value_score"], 90)
            self.assertEqual(conv1["keep_counts"], {"keep": 1, "cleanup": 1})
            self.assertEqual(conv1["keep_recommendation"], "cleanup")  # cleanup 优先规则
            conv2 = next(c for c in summary["conversations"] if c["conversation_id"] == "conv2")
            self.assertEqual(conv2["avg_value_score"], 70.0)
            self.assertEqual(conv2["keep_recommendation"], "keep")
            conn = sqlite3.connect(cfg["paths"]["db"])
            n = conn.execute(
                "SELECT COUNT(*) FROM v3_final_judgments WHERE run_id='run_r'").fetchone()[0]
            conn.close()
            self.assertEqual(n, 2)


if __name__ == "__main__":
    unittest.main()
