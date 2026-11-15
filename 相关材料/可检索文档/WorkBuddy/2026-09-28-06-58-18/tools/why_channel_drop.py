# -*- coding: utf-8 -*-
"""追查：旧 index.sqlite 的 68,184 条公众号消息来自哪里？新库为何只有 15,348？"""
import sqlite3

c = sqlite3.connect(r"file:C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite?mode=ro", uri=True)
cur = c.cursor()

G = "session_key LIKE 'gh\\_%' ESCAPE '\\'"
cur.execute(f"SELECT COUNT(*) FROM messages WHERE {G}")
print("旧库公众号消息总数:", cur.fetchone()[0])

print("\n-- 按 sessions.source_file --")
cur.execute(f"""
SELECT COALESCE(s.source_file,'(空)'), COUNT(*)
FROM messages m JOIN sessions s ON s.talker = m.session_key
WHERE m.{G.replace('session_key','session_key')} GROUP BY 1 ORDER BY 2 DESC
""")
for a, b in cur.fetchall():
    print(f"  {a}: {b:,}")

print("\n-- 公众号会话数 按来源 --")
cur.execute(f"SELECT COALESCE(source_file,'(空)'), COUNT(*) FROM sessions WHERE talker LIKE 'gh\\_%' ESCAPE '\\' GROUP BY 1 ORDER BY 2 DESC")
for a, b in cur.fetchall():
    print(f"  {a}: {b}")

print("\n-- 重复情况：旧库公众号里有多少是同 (session_key,ts,content) 重复 --")
cur.execute(f"""
SELECT COUNT(*) FROM (SELECT session_key,ts,content FROM messages WHERE {G} GROUP BY 1,2,3 HAVING COUNT(*)>1)
""")
print("  重复组:", cur.fetchone()[0])
cur.execute(f"SELECT COUNT(*) FROM (SELECT DISTINCT session_key,ts,content FROM messages WHERE {G})")
print("  严格去重后:", cur.fetchone()[0])

print("\n-- 旧库公众号消息时间范围 --")
cur.execute(f"SELECT MIN(ts), MAX(ts) FROM messages WHERE {G}")
import datetime
a, b = cur.fetchone()
print("  ", datetime.datetime.fromtimestamp(a), "→", datetime.datetime.fromtimestamp(b))

print("\n-- 旧库公众号内容样本（前 5）--")
cur.execute(f"SELECT session_key, content FROM messages WHERE {G} AND length(content)>4 LIMIT 5")
for k, t in cur.fetchall():
    print(f"  [{k}] {(t or '')[:90]}")

c.close()

print("\n\n==== 新库 index_v2 公众号 ====")
n = sqlite3.connect(r"file:C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index_v2.sqlite?mode=ro", uri=True)
ncur = n.cursor()
ncur.execute(f"SELECT COUNT(*), COUNT(DISTINCT session_key) FROM messages WHERE {G}")
print("  条数 / 会话数:", ncur.fetchone())
ncur.execute(f"SELECT MIN(ts), MAX(ts) FROM messages WHERE {G}")
a, b = ncur.fetchone()
print("  时间范围:", datetime.datetime.fromtimestamp(a), "→", datetime.datetime.fromtimestamp(b))
ncur.execute(f"SELECT session_key, content FROM messages WHERE {G} AND length(content)>4 LIMIT 5")
for k, t in ncur.fetchall():
    print(f"  [{k}] {(t or '')[:90]}")
n.close()
