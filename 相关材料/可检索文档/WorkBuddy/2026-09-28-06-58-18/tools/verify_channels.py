# -*- coding: utf-8 -*-
"""公众号回灌后验收：条数 / FTS 对齐 / 时间范围 / sessions 同步"""
import datetime
import sqlite3

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
G = "session_key LIKE 'gh\\_%' ESCAPE '\\'"
f = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "-"

c = sqlite3.connect(f"file:{IDX}?mode=ro", uri=True)
cur = c.cursor()

print("== 总量 ==")
m = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
ft = cur.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
s = cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
print(f"  messages={m:,}  messages_fts={ft:,}  差={m-ft}  sessions={s:,}")

print("\n== FTS rowid 与 messages.id 是否 1:1 对齐 ==")
bad = cur.execute("""
SELECT COUNT(*) FROM messages m JOIN messages_fts f ON f.rowid = m.id
WHERE m.content <> f.content
""").fetchone()[0]
print(f"  内容不一致的行数: {bad}  → {'对齐 ✅' if bad == 0 else '未对齐 ❌'}")
print("  fts rowid 范围:", cur.execute("SELECT MIN(rowid), MAX(rowid) FROM messages_fts").fetchone())
print("  msg id 范围:   ", cur.execute("SELECT MIN(id), MAX(id) FROM messages").fetchone())

print("\n== 公众号 ==")
n, mn, mx, sess = cur.execute(f"SELECT COUNT(*), MIN(ts), MAX(ts), COUNT(DISTINCT session_key) FROM messages WHERE {G}").fetchone()
print(f"  条数 {n:,} · 会话 {sess:,} · 范围 {f(mn)} → {f(mx)}")

print("\n== 公众号按月分布 ==")
for ym, cnt in cur.execute(f"SELECT strftime('%Y-%m',ts,'unixepoch','localtime') ym, COUNT(*) FROM messages WHERE {G} GROUP BY ym ORDER BY ym"):
    print(f"  {ym}  {cnt:>6,}")

print("\n== sessions 同步检查 ==")
mismatch = cur.execute("""
SELECT COUNT(*) FROM sessions s
WHERE s.message_count <> (SELECT COUNT(*) FROM messages m WHERE m.session_key = s.talker)
""").fetchone()[0]
print(f"  sessions.message_count 与实况不符的会话数: {mismatch}  → {'同步 ✅' if mismatch == 0 else '需修'}")

print("\n== server_id 唯一性 ==")
dup = cur.execute("SELECT COUNT(*) FROM (SELECT session_key,server_id FROM messages WHERE server_id<>0 GROUP BY 1,2 HAVING COUNT(*)>1)").fetchone()[0]
print(f"  server_id 重复组: {dup}  → {'唯一 ✅' if dup == 0 else '有重复 ❌'}")

print("\n== 全库最新 ==")
print("  ", f(cur.execute("SELECT MAX(ts) FROM messages").fetchone()[0]))

c.close()
