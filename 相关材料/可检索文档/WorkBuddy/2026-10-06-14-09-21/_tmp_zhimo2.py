# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

def dt(ts): return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

# 精确取 2026-04-24 与 2026-04-05 文件传输助手的长文本
lo = int(datetime.datetime(2026,4,24,0,0).timestamp())
hi = int(datetime.datetime(2026,4,25,0,0).timestamp())
cur.execute("""SELECT m.ts, s.display_name, m.content FROM messages m
   LEFT JOIN sessions s ON m.session_key=s.talker
   WHERE m.ts BETWEEN ? AND ? AND length(m.content) > 800 ORDER BY m.ts""", (lo,hi))
rows = cur.fetchall()
print(f"### 2026-04-24 长文本 {len(rows)} 条\n")
for ts, dn, c in rows:
    print("="*72)
    print(f"[{dt(ts)}] {dn}  长度={len(str(c))}")
    print("="*72)
    print(str(c)[:9000])
    print()

lo2 = int(datetime.datetime(2026,4,5,0,0).timestamp())
hi2 = int(datetime.datetime(2026,4,6,0,0).timestamp())
cur.execute("""SELECT m.ts, s.display_name, m.content FROM messages m
   LEFT JOIN sessions s ON m.session_key=s.talker
   WHERE m.ts BETWEEN ? AND ? AND length(m.content) > 800 ORDER BY m.ts""", (lo2,hi2))
rows2 = cur.fetchall()
print(f"\n\n### 2026-04-05 长文本 {len(rows2)} 条\n")
for ts, dn, c in rows2:
    print("="*72)
    print(f"[{dt(ts)}] {dn}  长度={len(str(c))}")
    print("="*72)
    print(str(c)[:12000])
    print()
