# -*- coding: utf-8 -*-
"""本轮最终验收：索引库 + 语料 + 一致性"""
import csv
import datetime
import os
import sqlite3

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\all_sessions"
READ = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\readable_full"
f = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "-"

c = sqlite3.connect(f"file:{IDX}?mode=ro", uri=True)
cur = c.cursor()
m = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
ft = cur.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
ss = cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
print(f"[索引库] messages={m:,}  messages_fts={ft:,}  差={m-ft}  sessions={ss:,}")
print(f"[索引库] 最新一条 {f(cur.execute('SELECT MAX(ts) FROM messages').fetchone()[0])}")
bad = cur.execute("SELECT COUNT(*) FROM messages m JOIN messages_fts f ON f.rowid=m.id WHERE m.content<>f.content").fetchone()[0]
print(f"[索引库] FTS↔id 对齐差异 {bad}")
dup = cur.execute("SELECT COUNT(*) FROM (SELECT session_key,server_id FROM messages WHERE server_id<>0 GROUP BY 1,2 HAVING COUNT(*)>1)").fetchone()[0]
print(f"[索引库] server_id 重复组 {dup}")
named = cur.execute("SELECT COUNT(*) FROM sessions WHERE display_name<>talker AND display_name<>''").fetchone()[0]
print(f"[索引库] 有真名的会话 {named:,}/{ss:,}  ({100.0*named/ss:.1f}%)")
for k, cond in (("私聊", "session_key NOT LIKE '%@chatroom%' AND session_key NOT LIKE 'gh\\_%' ESCAPE '\\' AND session_key NOT LIKE '%@openim%' AND session_key<>'filehelper'"),
                ("群聊", "session_key LIKE '%@chatroom%'"),
                ("公众号", "session_key LIKE 'gh\\_%' ESCAPE '\\'"),
                ("其他", "session_key LIKE '%@openim%' OR session_key='filehelper'")):
    n, a, b = cur.execute(f"SELECT COUNT(*),MIN(ts),MAX(ts) FROM messages WHERE {cond}").fetchone()
    print(f"         {k:<4} {n:>8,}  {f(a)} → {f(b)}")
c.close()

print()
rows = list(csv.DictReader(open(os.path.join(OUT, "_index.csv"), encoding="utf-8-sig")))
print(f"[语料] _index.csv {len(rows):,} 行")
tot = 0
for d in ("private", "group", "channel", "other"):
    n = len([x for x in os.listdir(os.path.join(OUT, d)) if x.endswith(".json")])
    tot += n
    print(f"        {d:<8} {n:>5} 个 JSON")
print(f"        合计 {tot:,} 个 JSON（应 = 会话数 {ss:,}）→ {'一致 ✅' if tot == ss else '不一致 ❌'}")
print(f"[语料] readable_full {len(os.listdir(READ)):,} 份")
sz = sum(os.path.getsize(os.path.join(r, x)) for r, _, fs in os.walk(OUT) for x in fs)
print(f"[语料] all_sessions 体积 {sz/1048576:.0f} MB")
