"""v3 事件中心 · 无 API 测试：预填判断档案、低负担复核反馈、schema、结论稳定性。

覆盖 DEEP-REVIEW-SPEC 强制要求：
- 预填字段导出/导入幂等（bundle -> feedback -> 落库 -> 重导幂等）；
- 模型猜测与用户修正并存（model_guess 与 user_correction 同时落库）；
- 反证槽位存在（analysis_profile.counter_evidence 键保留）；
- 不足三事件的稳定结论被标为暂定（assess_stability）。

运行：python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src import v3_event_review, v3_events  # noqa: E402


def _sig(message_id: str = "m1", conv_id: str = "conv1", segment_id: str = "seg1",
         create_ts: int = 1780000000, text: str = "明天格拉校友会招生活动见",
         is_send: int = 0, sender_name: str = "周冉") -> v3_events.MsgSignal:
    sig = v3_events.MsgSignal(
        message_id=message_id, conversation_id=conv_id, segment_id=segment_id,
        create_ts=create_ts, text=text, is_send=is_send, sender_name=sender_name,
    )
    cleaned = v3_events._clean_text(text)
    sig.time_signals = v3_events.extract_time_signals(cleaned)
    for t in sig.time_signals:
        t["resolved"] = v3_events.resolve_single(t, create_ts)
    sig.entity_signals = v3_events.extract_entity_signals(cleaned, [])
    sig.task_signals = v3_events.extract_task_signals(cleaned)
    sig.score = sum(s["weight"] for s in sig.time_signals) \
        + sum(s["weight"] for s in sig.entity_signals) \
        + sum(s["weight"] for s in sig.task_signals)
    return sig


def _cand() -> dict:
    """最小候选 dict（含证据消息、时间/实体/任务信号），供预填档案与 bundle 构建。"""
    msgs = [
        _sig("m1", "conv1", "seg1", 1780000000, "明天格拉校友会招生活动见", 0, "周冉"),
        _sig("m2", "conv1", "seg1", 1780000900, "好的，我周五下午过去帮忙摆摊", 1, "我"),
        _sig("m3", "conv2", "seg2", 1780864000, "周四下午去井邻看房，房东那边约好了", 0, "房东"),
    ]
    strong = {"格拉斯哥", "校友会"}
    return {
        "candidate_id": "evc_testabc1234567",
        "strong_entities": sorted(strong),
        "entity_terms": ["格拉斯哥", "校友会", "招生", "井邻", "房东"],
        "project_terms": ["格拉斯哥", "校友会", "招生"],
        "discovered_terms": [],
        "task_categories": ["appoint", "travel", "house"],
        "time_types": ["tomorrow", "weekday", "month_day"],
        "time_ref_texts": ["明天", "周五下午", "周四下午"],
        "resolved_dates": ["2026-06-15"],
        "start_ts": 1780000000,
        "end_ts": 1780864000,
        "day_span": 1.0,
        "msg_count": 3,
        "conv_ids": ["conv1", "conv2"],
        "conversation_count": 2,
        "key_context": True,
        "signal_score": 42.5,
        "msgs": msgs,
    }


def _feedback_row(cid: str, verdict: str = "confirmed", note: str = "") -> dict:
    """复核界面导出的单行反馈（含 model_guess 与 user_correction）。"""
    return {
        "candidate_id": cid,
        "run_id": "run_test",
        "user_verdict": verdict,
        "review_status": "confirmed" if verdict == "confirmed" else "corrected",
        "user_correction": {
            "title": {"guess": "格拉校友会 · 约见", "corrected": "格拉校友会招生活动", "reason": ""},
            "note": {"guess": "", "corrected": note, "reason": ""},
        },
        "model_guess": {"analysis_status": "retrieval_ready", "schema_version": "prefill-profile-1.0"},
        "title_override": "",
        "start_ts": 1780000000, "end_ts": 1780864000,
        "time_certainty": "inferred", "fact_status": "unknown",
        "roles": {}, "merge_into": "", "split_parts": [],
        "expectation": "", "value_score": 70, "value_tags": ["友情"],
        "keep_recommendation": "keep", "note": note,
        "reviewed_at": "2026-08-07T00:00:00+08:00",
    }


class PrefillProfileTests(unittest.TestCase):
    """改动一：深度预填判断档案数据契约。"""

    def test_profile_has_traceable_facts(self) -> None:
        profile = v3_events.build_analysis_profile(_cand(), {"conv1": "周冉", "conv2": "房东"})
        self.assertEqual(profile["analysis_status"], "retrieval_ready")
        self.assertIsNone(profile["confidence"])  # 无 API 阶段不伪造模型置信度
        self.assertGreaterEqual(len(profile["facts"]), 1)
        for f in profile["facts"]:
            self.assertIn("status", f)
            self.assertIn(f["status"], ("fact", "inferred", "unknown"))
            self.assertIn("evidence_ids", f)
            for eid in f["evidence_ids"]:
                self.assertTrue(eid.startswith("eve_"))  # 证据可回链

    def test_profile_deep_slots_empty_honest(self) -> None:
        """无 API 阶段：深度槽位必须为空/None，绝不假装模型已推理。"""
        profile = v3_events.build_analysis_profile(_cand(), {"conv1": "周冉"})
        for key in ("deep_hypotheses", "alternative_hypotheses"):
            self.assertIn(key, profile)
            self.assertEqual(profile[key], [])
        for key in ("relationship_profile",):
            self.assertIsNone(profile[key])
        self.assertIn("value_assumptions", profile)
        self.assertIn("communication_advice", profile)
        self.assertIn("待深度分析", profile["analysis_note"])

    def test_counter_evidence_slot_exists(self) -> None:
        """反证槽位必须存在（即使为空），保证 schema 可追溯。"""
        profile = v3_events.build_analysis_profile(_cand(), {"conv1": "周冉"})
        self.assertIn("counter_evidence", profile)
        self.assertIsInstance(profile["counter_evidence"], list)

    def test_stability_tentative_below_three(self) -> None:
        """不足 3 个独立已确认事件 -> 暂定假设；>=3 -> 稳定。"""
        for n in (0, 1, 2):
            r = v3_events.assess_stability(n)
            self.assertEqual(r["status"], "tentative", f"n={n} 应暂定")
            self.assertEqual(r["required"], 3)
        r = v3_events.assess_stability(3)
        self.assertEqual(r["status"], "stable")
        r = v3_events.assess_stability(4)
        self.assertEqual(r["status"], "stable")

    def test_bundle_carries_analysis_profile_and_status(self) -> None:
        bundle = v3_events.build_bundle([_cand()], {"conv1": "周冉", "conv2": "房东"}, limit=30)
        self.assertEqual(bundle["schema_version"], "event-review-1.1")
        item = bundle["candidates"][0]
        self.assertEqual(item["analysis_status"], "retrieval_ready")
        self.assertIn("analysis_profile", item)
        self.assertEqual(item["analysis_profile"]["candidate_id"], item["candidate_id"])

    def test_event_schema_has_analysis_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "e.sqlite3")
            conn = sqlite3.connect(db)
            v3_events.ensure_event_schema(conn)
            cand_cols = {r[1] for r in conn.execute("PRAGMA table_info(_v3_event_candidates)")}
            review_cols = {r[1] for r in conn.execute("PRAGMA table_info(_v3_event_review)")}
            conn.close()
            for col in ("analysis_status", "analysis_profile_json", "confidence"):
                self.assertIn(col, cand_cols)
            for col in ("user_verdict", "user_correction_json", "model_guess_json"):
                self.assertIn(col, review_cols)

    def test_schema_migration_idempotent_on_existing(self) -> None:
        """老库缺列时补列；重复 ensure 不报错（幂等迁移）。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "e.sqlite3")
            conn = sqlite3.connect(db)
            conn.executescript("""
            CREATE TABLE _v3_event_candidates (
              candidate_id TEXT PRIMARY KEY,
              title TEXT, candidate_json TEXT
            );
            CREATE TABLE _v3_event_review (
              candidate_id TEXT PRIMARY KEY,
              review_status TEXT
            );
            """)
            conn.commit()
            v3_events.ensure_event_schema(conn)  # 补列
            v3_events.ensure_event_schema(conn)  # 幂等
            cols = {r[1] for r in conn.execute("PRAGMA table_info(_v3_event_candidates)")}
            self.assertIn("analysis_status", cols)
            conn.close()


class FeedbackPersistenceTests(unittest.TestCase):
    """改动二：低负担复核反馈导出/重导幂等 + 猜测/修正并存。"""

    def _db(self, tmp: str) -> str:
        db = str(Path(tmp) / "fb.sqlite3")
        conn = sqlite3.connect(db)
        v3_events.ensure_event_schema(conn)
        conn.close()
        return db

    def test_apply_feedback_idempotent(self) -> None:
        """同一反馈重导两次 -> 行数不变（幂等 upsert）。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            rows = [_feedback_row("evc_a", "confirmed", "n1"), _feedback_row("evc_b", "partial", "n2")]
            n1 = v3_event_review.apply_event_feedback(db, rows)
            n2 = v3_event_review.apply_event_feedback(db, rows)
            self.assertEqual(n1, 2)
            self.assertEqual(n2, 2)
            conn = sqlite3.connect(db)
            count = conn.execute("SELECT COUNT(*) FROM _v3_event_review").fetchone()[0]
            conn.close()
            self.assertEqual(count, 2)

    def test_model_guess_and_user_correction_coexist(self) -> None:
        """落库后 model_guess_json 与 user_correction_json 同时存在、内容分别可读。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            row = _feedback_row("evc_a", "partial", "其实是师兄师姐线下组织的")
            v3_event_review.apply_event_feedback(db, [row])
            conn = sqlite3.connect(db)
            r = conn.execute(
                "SELECT user_verdict, user_correction_json, model_guess_json "
                "FROM _v3_event_review WHERE candidate_id='evc_a'"
            ).fetchone()
            conn.close()
            self.assertIsNotNone(r)
            verdict, corr_json, guess_json = r
            self.assertEqual(verdict, "partial")
            corr = json.loads(corr_json)
            guess = json.loads(guess_json)
            # 模型猜测存在（原样保留）
            self.assertEqual(guess["analysis_status"], "retrieval_ready")
            # 用户修正存在且非模型猜测
            self.assertEqual(corr["title"]["corrected"], "格拉校友会招生活动")
            self.assertNotEqual(corr["title"]["corrected"], corr["title"]["guess"])

    def test_export_import_roundtrip_feedback(self) -> None:
        """导出的反馈行 -> load_event_feedback 校验通过 -> 再落库行数一致（幂等）。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            path = Path(tmp) / "feedback.jsonl"
            rows = [_feedback_row("evc_a", "confirmed", "x"), _feedback_row("evc_b", "incorrect", "y")]
            path.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                encoding="utf-8",
            )
            loaded = v3_event_review.load_event_feedback(path)
            self.assertEqual(len(loaded), 2)
            v3_event_review.apply_event_feedback(db, loaded)
            conn = sqlite3.connect(db)
            count = conn.execute("SELECT COUNT(*) FROM _v3_event_review").fetchone()[0]
            conn.close()
            self.assertEqual(count, 2)

    def test_load_feedback_rejects_bad_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(
                json.dumps({"candidate_id": "evc_a", "user_verdict": "nope", "review_status": "confirmed"}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                v3_event_review.load_event_feedback(path)


class EventReviewRenderTests(unittest.TestCase):
    def test_render_html_shows_prefill_and_slots(self) -> None:
        """首屏展示预填档案：analysis_status 横幅、facts、反证槽位、稳定性。"""
        with tempfile.TemporaryDirectory() as tmp:
            bundle = v3_events.build_bundle([_cand()], {"conv1": "周冉", "conv2": "房东"}, limit=30)
            bundle["run_id"] = "run_r"
            html = v3_event_review.render_event_review_html(bundle, Path(tmp))
            text = html.read_text(encoding="utf-8")
            self.assertIn("待深度分析", text)           # analysis_status 横幅
            self.assertIn("反证", text)                # counter_evidence 槽位
            self.assertIn("暂定假设", text)             # conclusion_stability
            self.assertIn("用户修正", text)             # 低负担操作
            self.assertIn("evc_testabc1234567", text)  # 候选 id
            # 数据内嵌安全：注入 < 被转义
            self.assertNotIn("__EVENT_DATA__", text)
            self.assertEqual(text.count("</script>"), 1)


if __name__ == "__main__":
    unittest.main()
