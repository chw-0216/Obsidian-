"""v3 事件中心 · 深度分析完整聊天包 · 无 API 测试。

覆盖 src/v3_event_pkg.py：
- 事件包 schema 与回链完整性（event_id -> 源候选 -> 证据/片段/联系人）；
- 事件窗口内完整片段检索（含上下文片段，信号片段正确标记）；
- token 估算为正整数且随 transcript 增大；
- 未确认/未知 event_id 报错、源候选解析、merged 候选结构。

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

from src import v3_event_pkg, v3_events  # noqa: E402


def _build_fixture_db(tmp: str) -> str:
    """构造最小 DB：2 会话 / 2 片段 / 1 候选 / 证据 / 联系人 / 最终判断。"""
    db = str(Path(tmp) / "pkg.sqlite3")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    CREATE TABLE conversations (
      id TEXT PRIMARY KEY, display_name TEXT, source_relpath TEXT, source_sha256 TEXT,
      declared_message_count INTEGER, loaded_message_count INTEGER,
      first_ts INTEGER, last_ts INTEGER, updated_at TEXT
    );
    CREATE TABLE segments (
      id TEXT PRIMARY KEY, conversation_id TEXT, ordinal INTEGER,
      start_ts INTEGER, end_ts INTEGER, message_count INTEGER, char_count INTEGER,
      transcript TEXT, content_sha256 TEXT, updated_at TEXT
    );
    CREATE TABLE messages (
      id TEXT PRIMARY KEY, conversation_id TEXT, local_id TEXT, platform_message_id TEXT,
      create_ts INTEGER, created_at TEXT, is_send INTEGER, sender_name TEXT,
      message_type TEXT, local_type TEXT, raw_content TEXT, clean_content TEXT,
      source_payload TEXT, content_sha256 TEXT, source_file TEXT, segment_id TEXT
    );
    """)
    conn.execute("INSERT INTO conversations(id, display_name) VALUES ('conv1','周冉'),('conv2','达尔文')")
    # 片段：conv1 两条（一条信号、一条上下文），conv2 一条
    conn.execute(
        "INSERT INTO segments(id,conversation_id,ordinal,start_ts,end_ts,message_count,char_count,transcript) VALUES"
        "('seg_sig','conv1',1,1780000000,1780000600,3,80,"
        "'[id=msg1][2026-06-01 10:00][对方][文本] 明天格拉校友会招生活动见\\n[id=msg2][2026-06-01 10:01][我][文本] 好的 周五下午过去'),"
        "('seg_ctx','conv1',2,1780000700,1780000800,2,40,"
        "'[id=msg3][2026-06-01 10:05][对方][文本] 海报我晚点发你'),"
        "('seg_c2','conv2',1,1780010000,1780010100,2,60,"
        "'[id=msg4][2026-06-02 09:00][对方][文本] 周四下午去井邻看房')"
    )
    conn.execute(
        "INSERT INTO messages(id,conversation_id,create_ts,is_send,message_type,clean_content,segment_id) VALUES"
        "('msg1','conv1',1780000000,0,'文本消息','明天格拉校友会招生活动见','seg_sig'),"
        "('msg2','conv1',1780000600,1,'文本消息','好的 周五下午过去','seg_sig'),"
        "('msg3','conv1',1780000700,0,'文本消息','海报我晚点发你','seg_ctx'),"
        "('msg4','conv2',1780010000,0,'文本消息','周四下午去井邻看房','seg_c2')"
    )
    v3_events.ensure_event_schema(conn)
    conn.execute(
        """
        INSERT INTO _v3_event_candidates(
          candidate_id, title, category, description, start_ts, end_ts,
          time_certainty, fact_status, strong_entities, project_terms,
          task_categories, time_ref_texts, resolved_dates,
          conversation_count, day_span, msg_count, signal_score, key_context,
          status, analysis_status, analysis_profile_json, confidence,
          candidate_json, created_at, updated_at
        ) VALUES (
          'evc_pkgtest','周冉 · 格拉校友会 · 约见','appoint','描述',
          1780000000,1780010100,'fact','unknown',
          '["格拉斯哥","校友会"]','["校友会","格拉斯哥"]','["appoint","plan"]',
          '["明天","周五下午"]','["2026-06-15"]',
          2,1.3,3,42.5,1,'draft','retrieval_ready',
          '{"schema_version":"prefill-profile-1.0","facts":[],"deep_hypotheses":[],"alternative_hypotheses":[],"counter_evidence":[],"relationship_profile":null,"value_assumptions":[],"communication_advice":[],"conclusion_stability":{"status":"tentative"}}',
          NULL,'{}', '2026-08-07','2026-08-07'
        )
        """
    )
    conn.execute(
        """
        INSERT INTO _v3_event_evidence(evidence_id,candidate_id,message_id,segment_id,conversation_id,create_ts,quote,signal_types,match_terms,created_at) VALUES
        ('eve_sig1','evc_pkgtest','msg1','seg_sig','conv1',1780000000,'[对方] 明天格拉校友会招生活动见','["time","entity","task"]','["格拉斯哥","校友会","apply"]','2026-08-07'),
        ('eve_sig2','evc_pkgtest','msg2','seg_sig','conv1',1780000600,'[我] 好的 周五下午过去','["task"]','["plan"]','2026-08-07')
        """
    )
    conn.execute(
        """
        INSERT INTO _v3_event_contacts(candidate_id,conversation_id,display_name,message_count,role_hint,role_certainty,created_at) VALUES
        ('evc_pkgtest','conv1','周冉',2,NULL,NULL,'2026-08-07'),
        ('evc_pkgtest','conv2','达尔文',1,NULL,NULL,'2026-08-07')
        """
    )
    conn.execute(
        """
        INSERT INTO _v3_event_judgments(
          event_id, source_candidate_ids, title, start_ts, end_ts,
          time_certainty, fact_status, roles_json, expectation,
          value_score, value_tags, keep_recommendation, note, created_at
        ) VALUES (
          'evc_pkgtest','["evc_pkgtest"]','2025中秋联谊会·筹备报名',
          1780000000,1780010100,'fact','unknown','{}','',70,'["友情"]','keep','测试事件','2026-08-07'
        )
        """
    )
    conn.commit()
    conn.close()
    return db


class EventPackageBuildTests(unittest.TestCase):

    def test_build_event_package_returns_complete_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = _build_fixture_db(tmp)
            pkg = v3_event_pkg.build_event_package(db, "evc_pkgtest")

            self.assertEqual(pkg["schema_version"], "deep-event-package-1.0")
            self.assertEqual(pkg["event"]["event_id"], "evc_pkgtest")
            self.assertEqual(pkg["event"]["title"], "2025中秋联谊会·筹备报名")
            self.assertEqual(pkg["event"]["keep_recommendation"], "keep")

            # 源候选解析
            self.assertEqual(pkg["event"]["source_candidate_ids"], ["evc_pkgtest"])
            self.assertEqual(pkg["candidate"]["candidate_id"], "evc_pkgtest")

            # 证据回链
            self.assertEqual(len(pkg["evidence"]), 2)
            ev = pkg["evidence"][0]
            for k in ("evidence_id", "message_id", "segment_id", "conversation_id",
                      "create_ts", "quote", "signal_types", "match_terms"):
                self.assertIn(k, ev)

            # 完整片段：窗口内（conv1 + conv2）都检索到，信号片段正确标记
            segs = {s["segment_id"]: s for s in pkg["segments"]}
            self.assertEqual(set(segs), {"seg_sig", "seg_ctx", "seg_c2"})
            self.assertTrue(segs["seg_sig"]["is_signal_segment"])
            self.assertFalse(segs["seg_ctx"]["is_signal_segment"])
            self.assertFalse(segs["seg_c2"]["is_signal_segment"])

            # 联系人
            self.assertEqual(len(pkg["contacts"]), 2)
            names = {c["display_name"] for c in pkg["contacts"]}
            self.assertEqual(names, {"周冉", "达尔文"})

            # stats
            st = pkg["stats"]
            self.assertEqual(st["conversation_count"], 2)
            self.assertEqual(st["segment_count"], 3)
            self.assertEqual(st["signal_segment_count"], 1)
            self.assertEqual(st["evidence_count"], 2)

    def test_estimate_input_tokens_positive_and_scales(self) -> None:
        pkg = {
            "event": {"event_id": "x", "title": "t"},
            "candidate": {"analysis_profile": {"facts": []}},
            "contacts": [],
            "evidence": [{"quote": "abc"}],
            "segments": [{"transcript": "一二三四五"}, {"transcript": "六七八九十"}],
        }
        small = v3_event_pkg.estimate_input_tokens(pkg)
        self.assertIsInstance(small, int)
        self.assertGreater(small, 0)
        pkg["segments"][0]["transcript"] = "一" * 10000  # 增大 transcript
        big = v3_event_pkg.estimate_input_tokens(pkg)
        self.assertGreater(big, small)

    def test_build_unknown_event_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = _build_fixture_db(tmp)
            with self.assertRaises(ValueError):
                v3_event_pkg.build_event_package(db, "evc_not_exist")

    def test_resolve_source_candidates_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = _build_fixture_db(tmp)
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                ids = v3_event_pkg.resolve_source_candidates(conn, "evc_pkgtest")
                self.assertEqual(ids, ["evc_pkgtest"])
                # 未知 event_id -> 回退为自身（调用方随后会因无 judgment 报错）
                ids2 = v3_event_pkg.resolve_source_candidates(conn, "evc_zzz")
                self.assertEqual(ids2, ["evc_zzz"])
            finally:
                conn.close()

    def test_merged_candidate_structure(self) -> None:
        """多源候选合并时，candidate 字段为 merged 结构。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = _build_fixture_db(tmp)
            conn = sqlite3.connect(db)
            # 追加第二个候选与判断（两候选合并到同一事件）
            conn.execute(
                """
                INSERT INTO _v3_event_candidates(
                  candidate_id, title, category, start_ts, end_ts, time_certainty,
                  strong_entities, project_terms, task_categories, time_ref_texts,
                  resolved_dates, conversation_count, day_span, msg_count, signal_score,
                  key_context, status, analysis_status, candidate_json, created_at, updated_at
                ) VALUES (
                  'evc_pkgtest2','达尔文 · 出行','travel',1780010000,1780010100,'fact',
                  '["井邻"]','["井邻"]','["travel"]','[]','[]',1,0.1,1,20,0,
                  'draft','retrieval_ready','{}','2026-08-07','2026-08-07'
                )
                """
            )
            conn.execute(
                "UPDATE _v3_event_judgments SET source_candidate_ids=? WHERE event_id='evc_pkgtest'",
                ('["evc_pkgtest","evc_pkgtest2"]',),
            )
            conn.commit()
            conn.close()
            pkg = v3_event_pkg.build_event_package(db, "evc_pkgtest")
            self.assertTrue(pkg["candidate"]["merged"])
            self.assertEqual(len(pkg["candidate"]["candidates"]), 2)
            # 证据来自两候选
            self.assertEqual(len(pkg["evidence"]), 2)

    def test_retrieve_segments_window_boundary(self) -> None:
        """窗口外片段不进入完整包（只取事件窗口内）。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = _build_fixture_db(tmp)
            conn = sqlite3.connect(db)
            # conv1 加一条远早于事件窗口的片段
            conn.execute(
                "INSERT INTO segments(id,conversation_id,ordinal,start_ts,end_ts,message_count,char_count,transcript) VALUES"
                "('seg_old','conv1',0,1770000000,1770000100,1,10,'[id=msgx][2026-02-01][对方][文本] 旧消息')"
            )
            conn.commit()
            conn.close()
            pkg = v3_event_pkg.build_event_package(db, "evc_pkgtest")
            seg_ids = {s["segment_id"] for s in pkg["segments"]}
            self.assertNotIn("seg_old", seg_ids)


if __name__ == "__main__":
    unittest.main()
