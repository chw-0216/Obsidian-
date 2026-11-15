# -*- coding: utf-8 -*-
"""噪音群清理 · 步骤 2：删除（已在步骤 1 备份 + 源库可重建，双向可逆）。

删三处：
  1. messages       —— 4,121 行
  2. messages_fts   —— 4,124 行（FTS5 trigram，session_key 为 UNINDEXED 列，需全表扫）
  3. sessions       —— 2 行（否则留下 message_count=0 的孤儿会话）
"""
import shutil
import sqlite3
import time
from pathlib import Path

INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
NOISE = ["25410000808@chatroom", "18440588614@chatroom"]

print("清理前文件大小: %.1f MB" % (INDEX.stat().st_size / 1024 / 1024))

con = sqlite3.connect(INDEX)
con.execute("PRAGMA journal_mode=WAL")
cur = con.cursor()

before = {
    "messages": cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
    "fts": cur.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0],
    "sessions": cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
    "distinct": cur.execute("SELECT COUNT(DISTINCT session_key) FROM messages").fetchone()[0],
}
print("清理前:", before)

t0 = time.time()
cur.execute("DELETE FROM messages WHERE session_key IN (?,?)", NOISE)
d_msg = cur.rowcount
con.commit()
print("  messages 删除 %d 行" % d_msg)

cur.execute("DELETE FROM messages_fts WHERE session_key IN (?,?)", NOISE)
d_fts = cur.rowcount
con.commit()
print("  messages_fts 删除 %d 行" % d_fts)

cur.execute("DELETE FROM sessions WHERE talker IN (?,?)", NOISE)
d_sess = cur.rowcount
con.commit()
print("  sessions 删除 %d 行" % d_sess)

con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
print("耗时 %.1f 秒" % (time.time() - t0))

after = {
    "messages": cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
    "fts": cur.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0],
    "sessions": cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
    "distinct": cur.execute("SELECT COUNT(DISTINCT session_key) FROM messages").fetchone()[0],
}
print("清理后:", after)

print("\n=== 验证 ===")
for sid in NOISE:
    a = cur.execute("SELECT COUNT(*) FROM messages WHERE session_key=?", (sid,)).fetchone()[0]
    b = cur.execute("SELECT COUNT(*) FROM sessions WHERE talker=?", (sid,)).fetchone()[0]
    c = cur.execute("SELECT COUNT(*) FROM messages_fts WHERE session_key=?", (sid,)).fetchone()[0]
    print("  %-24s messages=%d sessions=%d fts=%d  %s" % (sid, a, b, c, "✅ 已清空" if a == b == c == 0 else "❌ 残留"))

print("\n关键人未受影响（抽查）:")
for sid, name in [("deerluna", "陈晔"), ("wxid_wdnk6ue9kiyn22", "笑一"), ("wxid_1wa75s1kze3o22", "母亲")]:
    n = cur.execute("SELECT COUNT(*) FROM messages WHERE session_key=?", (sid,)).fetchone()[0]
    print("  %-24s %-6s %d 条" % (sid, name, n))

con.close()
print("\n清理后文件大小: %.1f MB" % (INDEX.stat().st_size / 1024 / 1024))
