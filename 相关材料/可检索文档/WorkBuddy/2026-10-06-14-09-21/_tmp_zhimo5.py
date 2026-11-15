# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()
def dt(ts): return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
TARGETS = ["2026-04-24 05:09:50", "2026-04-24 04:24:41", "2026-04-05 08:33:01", "2026-04-24 10:20"]
for t in TARGETS:
    try:
        d = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except Exception:
        d = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
    lo = int(d.timestamp()) - 90
    hi = int(d.timestamp()) + 90
    cur.execute("""SELECT m.ts, m.content FROM messages m
       WHERE m.session_key='filehelper' AND m.ts BETWEEN ? AND ? ORDER BY m.ts""", (lo,hi))
    for ts, c in cur.fetchall():
        print("="*74)
        print(f"[{dt(ts)}]  长度 {len(str(c))}")
        print("="*74)
        print(str(c))
        print()
