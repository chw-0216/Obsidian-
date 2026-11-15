# -*- coding: utf-8 -*-
import sqlite3, datetime, io
from pathlib import Path

con = sqlite3.connect(r"file:C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite?mode=ro", uri=True)
out = io.open(Path(__file__).parent / "recalc_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")

tot = con.execute("select count(*) from messages").fetchone()[0]
P("总条数  :", tot)
P("会话数  :", con.execute("select count(distinct session_key) from messages").fetchone()[0])
P("sessions:", con.execute("select count(*) from sessions").fetchone()[0])
r = con.execute("select min(ts),max(ts) from messages").fetchone()
P("时间范围:", datetime.datetime.fromtimestamp(r[0]), "->", datetime.datetime.fromtimestamp(r[1]))
P("")
P("--- 按类型 ---")
for r in con.execute("select s.session_type, count(*) from messages m left join sessions s on s.talker=m.session_key group by 1 order by 2 desc"):
    P("  ", r[0], r[1])
P("")
q = ("select count(*) from (select session_key, sum(role='me') me from messages group by 1) where me=0")
z = con.execute(q).fetchone()[0]
q2 = ("select sum(c) from (select session_key, count(*) c, sum(role='me') me from messages group by 1) where me=0")
nz = con.execute(q2).fetchone()[0]
P("零发言会话:", z)
P("零发言条数:", nz, "占比 %.1f%%" % (100.0 * nz / tot))
P("")
P("关键人:")
for name, sid in [("陈晔", "deerluna"), ("笑一", "wxid_wdnk6ue9kiyn22"), ("母亲", "wxid_1wa75s1kze3o22"),
                  ("陈昶文", "wxid_0gb0smyjaoyk22"), ("王利敏", "a35599192")]:
    P("  ", name, con.execute("select count(*) from messages where session_key=?", (sid,)).fetchone()[0])
P("")
P("FTS:", con.execute("select count(*) from messages_fts").fetchone()[0],
  "| 孤儿:", con.execute("select count(*) from messages_fts f left join messages m on m.rowid=f.rowid where m.rowid is null").fetchone()[0])
out.close()
