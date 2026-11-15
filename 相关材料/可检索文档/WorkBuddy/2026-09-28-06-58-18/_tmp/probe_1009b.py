# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)
def ts(v): return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M")

TARGETS = [
 ("wxid_wdnk6ue9kiyn22","笑一"),
 ("wxid_0ejd54z34nmv32","舒泽林"),
 ("deerluna","陈晔(导师)"),
]
T0 = int(datetime.datetime(2026,10,8,14,29,0).timestamp())
for tk, nm in TARGETS:
    p("="*104); p("【%s】 %s" % (nm, tk)); p("="*104)
    rows = c.execute("""select ts, role, type, content from messages
        where session_key=? and ts>=? order by ts""", (tk, T0)).fetchall()
    for r in rows:
        cont = (r["content"] or "").replace("\n"," / ")
        p("[%s] %-5s %-3s %s" % (ts(r["ts"]), r["role"], r["type"], cont[:500]))
    p("")
open("probe_1009b.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
