from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from common import clean_text, redact_for_model  # noqa: E402
from weflow_ingest import run_ingest  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_ingest_segments_and_search_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "export"
            folder = root / "私聊_测试联系人"
            folder.mkdir(parents=True)
            payload = {
                "weflow": {"version": "test"},
                "session": {
                    "wxid": "wxid_test",
                    "displayName": "测试联系人",
                    "messageCount": 3,
                },
                "messages": [
                    {
                        "localId": "1",
                        "createTime": 1700000000,
                        "type": 1,
                        "localType": 1,
                        "content": "项目计划已经开始",
                        "isSend": True,
                    },
                    {
                        "localId": "2",
                        "createTime": 1700000060,
                        "type": 1,
                        "localType": 1,
                        "content": "好的，明天继续",
                        "isSend": False,
                    },
                    {
                        "localId": "3",
                        "createTime": 1700010000,
                        "type": 3,
                        "localType": 3,
                        "content": "",
                        "isSend": False,
                    },
                ],
                "avatars": {},
            }
            path = folder / "私聊_测试联系人.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            database = Path(temp_dir) / "test.sqlite3"
            result = run_ingest(root, database, gap_minutes=90)
            self.assertEqual(result["messages"], 3)
            self.assertEqual(result["segments"], 2)
            connection = sqlite3.connect(database)
            self.assertEqual(connection.execute("SELECT count(*) FROM messages").fetchone()[0], 3)
            self.assertEqual(connection.execute("SELECT count(*) FROM messages_fts").fetchone()[0], 2)
            hit = connection.execute(
                "SELECT count(*) FROM messages_fts WHERE messages_fts MATCH ?", ("项目计划",)
            ).fetchone()[0]
            connection.close()
            self.assertEqual(hit, 1)

    def test_clean_and_redact(self) -> None:
        self.assertEqual(clean_text("你好\x00  世界\r\n"), "你好 世界")
        redacted, count = redact_for_model("电话 13800138000，邮箱 test@example.com")
        self.assertEqual(count, 2)
        self.assertNotIn("13800138000", redacted)
        self.assertNotIn("test@example.com", redacted)


if __name__ == "__main__":
    unittest.main()
