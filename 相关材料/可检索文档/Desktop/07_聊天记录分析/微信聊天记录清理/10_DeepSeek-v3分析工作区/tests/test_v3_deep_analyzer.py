"""v3 事件中心 · 深度分析 · 无 API 测试。

覆盖 src/v3_deep_analyzer.py：
- build_deep_input：渲染事实/联系人/证据/完整片段，保留消息 id 回链；
- parse_deep_result：解析合法 JSON、拒绝错误 schema、拒绝引用输入中不存在的消息 id；
- _evidence_coverage：引用去重 / 输入消息 id 数；
- apply_deep_result：落库 _v3_event_deep_analysis + 回填 _v3_event_candidates.analysis_profile_json。

运行：python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src import v3_deep_analyzer as da  # noqa: E402
from src.v3_events import ensure_event_schema  # noqa: E402

_TEST_DB = WORKSPACE / ".tmp-deep-test.sqlite3"


def _fixture_pkg() -> dict:
    return {
        "schema_version": "deep-event-package-1.0",
        "event": {
            "event_id": "evc_test",
            "title": "测试事件",
            "start_ts": 1780000000,
            "end_ts": 1780001000,
            "keep_recommendation": "keep",
            "note": None,
        },
        "candidate": {
            "candidate_id": "evc_test",
            "merged": False,
            "analysis_profile": {
                "facts": [
                    {"statement": "时间范围 X~Y", "status": "fact", "confidence": 1.0,
                     "evidence_ids": ["msg1"]}
                ]
            },
        },
        "contacts": [
            {"conversation_id": "conv1", "display_name": "周冉", "message_count": 2}
        ],
        "evidence": [
            {"evidence_id": "eve1", "message_id": "msg1", "quote": "[对方] 明天见",
             "signal_types": ["time"]},
            {"evidence_id": "eve2", "message_id": "msg2", "quote": "[我] 好的",
             "signal_types": ["task"]},
        ],
        "segments": [
            {
                "segment_id": "seg1", "conversation_id": "conv1", "ordinal": 1,
                "start_ts": 1780000000, "end_ts": 1780000100,
                "message_count": 2, "char_count": 30, "is_signal_segment": True,
                "transcript": "[id=msg1][2026-06-01 10:00][对方][文本] 明天见\n"
                             "[id=msg2][2026-06-01 10:01][我][文本] 好的",
            }
        ],
    }


def _valid_result() -> dict:
    return {
        "schema_version": "deep-analysis-1.0",
        "deep_hypotheses": [{
            "hypothesis": "约见面", "surface_purpose": "见面", "possible_underlying_purpose": None,
            "status": "inferred", "confidence": 0.8, "evidence_ids": ["msg1", "msg2"],
        }],
        "alternative_hypotheses": [{
            "alternative": "只是寒暄", "why_plausible": "无明确承诺", "evidence_ids": ["msg2"],
        }],
        "counter_evidence": [{"observation": "未定时间", "evidence_ids": ["msg1"]}],
        "relationship_profile": [{
            "conversation_id": "conv1", "display_name": "周冉", "positioning": "朋友",
            "event_role": "参与者", "reciprocity": "对等",
            "power_dynamic": {
                "balance": "unequal", "dominant_side": "them",
                "asymmetry_dimensions": ["status"], "gender_relevant": "学姐",
                "evidence_ids": ["msg1"],
            },
            "user_expectation": "推进",
            "other_expectation": "见面", "evidence_ids": ["msg1"],
        }],
        "value_assumptions": [{
            "dimension": "cooperation", "assumption": "合作", "evidence_ids": ["msg2"],
        }],
        "communication_advice": [{
            "advice": "确认时间", "rationale": "明确", "respects_boundary": True,
        }],
        "confidence": 0.8,
        "fact_status": "inferred",
        "needs_user_confirmation": ["时间待定"],
    }


class BuildInputTests(unittest.TestCase):

    def test_build_deep_input_renders_core_fields(self) -> None:
        pkg = _fixture_pkg()
        user, stats = da.build_deep_input(pkg)
        self.assertIn("测试事件", user)
        self.assertIn("evc_test", user)
        self.assertIn("周冉", user)
        self.assertIn("时间范围 X~Y", user)
        self.assertIn("[id=msg1]", user)
        self.assertIn("明天见", user)
        self.assertEqual(stats["segment_count"], 1)
        self.assertEqual(stats["evidence_count"], 2)
        self.assertEqual(stats["contact_count"], 1)
        self.assertGreater(stats["input_chars"], 0)

    def test_collect_facts_merged(self) -> None:
        pkg = _fixture_pkg()
        pkg["candidate"] = {
            "merged": True,
            "candidates": [
                {"analysis_profile": {"facts": [{"statement": "a"}]}},
                {"analysis_profile": {"facts": [{"statement": "b"}]}},
            ],
        }
        facts = da._collect_facts(pkg)
        self.assertEqual([f["statement"] for f in facts], ["a", "b"])


class ParseResultTests(unittest.TestCase):

    def test_parse_valid_result(self) -> None:
        pkg = _fixture_pkg()
        result = da.parse_deep_result(json.dumps(_valid_result(), ensure_ascii=False), pkg)
        self.assertEqual(result["schema_version"], "deep-analysis-1.0")
        self.assertEqual(len(result["deep_hypotheses"]), 1)
        self.assertEqual(result["relationship_profile"][0]["display_name"], "周冉")

    def test_parse_rejects_bad_schema(self) -> None:
        pkg = _fixture_pkg()
        r = _valid_result()
        r["schema_version"] = "wrong"
        with self.assertRaises(ValueError):
            da.parse_deep_result(json.dumps(r), pkg)

    def test_parse_rejects_unknown_evidence_id(self) -> None:
        pkg = _fixture_pkg()
        r = _valid_result()
        r["deep_hypotheses"][0]["evidence_ids"] = ["msg_zzz"]
        with self.assertRaises(ValueError):
            da.parse_deep_result(json.dumps(r), pkg)

    def test_parse_result_keeps_power_dynamic(self) -> None:
        pkg = _fixture_pkg()
        result = da.parse_deep_result(json.dumps(_valid_result(), ensure_ascii=False), pkg)
        pd = result["relationship_profile"][0]["power_dynamic"]
        self.assertEqual(pd["balance"], "unequal")
        self.assertEqual(pd["dominant_side"], "them")
        self.assertEqual(pd["asymmetry_dimensions"], ["status"])
        self.assertEqual(pd["gender_relevant"], "学姐")

    def test_parse_fills_missing_slots(self) -> None:
        pkg = _fixture_pkg()
        r = {"schema_version": "deep-analysis-1.0"}
        result = da.parse_deep_result(json.dumps(r), pkg)
        self.assertEqual(result["deep_hypotheses"], [])
        self.assertEqual(result["alternative_hypotheses"], [])
        self.assertIsNone(result["relationship_profile"])

    def test_evidence_coverage(self) -> None:
        pkg = _fixture_pkg()
        result = _valid_result()
        cov = da._evidence_coverage(result, pkg)
        # 输入消息 id = {msg1, msg2}（transcript + evidence message_id）
        # 结果引用 msg1, msg2 -> 2/2
        self.assertEqual(cov, 1.0)


class ApplyResultTests(unittest.TestCase):

    def setUp(self) -> None:
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(_TEST_DB) + suffix)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    def tearDown(self) -> None:
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(_TEST_DB) + suffix)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    def _seed_db(self) -> None:
        conn = sqlite3.connect(str(_TEST_DB))
        ensure_event_schema(conn)
        conn.execute(
            "INSERT INTO _v3_event_judgments(event_id, source_candidate_ids, title, created_at) "
            "VALUES ('evc_test', '[\"evc_test\"]', '测试事件', '2026-08-01')"
        )
        conn.execute(
            "INSERT INTO _v3_event_candidates(candidate_id, title, analysis_profile_json, "
            "analysis_status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            ("evc_test", "测试事件", json.dumps({"facts": [], "analysis_status": "retrieval_ready"}),
             "retrieval_ready", "2026-08-01", "2026-08-01"),
        )
        conn.commit()
        conn.close()

    def test_apply_deep_result_backfills_profile(self) -> None:
        self._seed_db()
        pkg = _fixture_pkg()
        result = _valid_result()
        summary = da.apply_deep_result(str(_TEST_DB), "evc_test", pkg, result, {
            "model": "deepseek-v4-flash", "input_chars": 100, "estimated_input_tokens": 100,
            "input_tokens": 50, "output_tokens": 200,
        })
        self.assertEqual(summary["event_id"], "evc_test")
        self.assertAlmostEqual(summary["evidence_coverage"], 1.0)

        conn = sqlite3.connect(str(_TEST_DB))
        try:
            row = conn.execute(
                "SELECT result_json, status, model, input_tokens, output_tokens "
                "FROM _v3_event_deep_analysis WHERE event_id='evc_test'"
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "success")
            self.assertEqual(row[2], "deepseek-v4-flash")
            stored = json.loads(row[0])
            self.assertEqual(stored["deep_hypotheses"][0]["hypothesis"], "约见面")

            prof_row = conn.execute(
                "SELECT analysis_profile_json, analysis_status, confidence "
                "FROM _v3_event_candidates WHERE candidate_id='evc_test'"
            ).fetchone()
            prof = json.loads(prof_row[0])
            self.assertEqual(prof_row[1], "analyzed")
            self.assertEqual(prof["deep_hypotheses"][0]["hypothesis"], "约见面")
            self.assertEqual(prof["counter_evidence"][0]["observation"], "未定时间")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
