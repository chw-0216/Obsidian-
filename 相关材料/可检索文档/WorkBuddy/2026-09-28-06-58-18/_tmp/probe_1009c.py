# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)
def ts(v): return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M")

T0 = int(datetime.datetime(2026,10,8,14,29,0).timestamp())
TARGETS = [
 ("wxid_1wa75s1kze3o22","刘丽萍(母)"),
 ("guo647789","李老师(海燕·中传)"),
 ("filehelper","文件传输助手"),
]
for tk, nm in TARGETS:
    p("="*104); p("【%s】 %s" % (nm, tk)); p("="*104)
    rows = c.execute("""select ts, role, type, content from messages
        where session_key=? and ts>=? order by ts""", (tk, T0)).fetchall()
    for r in rows:
        cont = (r["content"] or "").replace("\n"," / ")
        if r["type"] in ("image","sticker","video","voice"):
            cont = "<%s>" % r["type"]
        p("[%s] %-5s %-10s %s" % (ts(r["ts"]), r["role"], r["type"], cont[:400]))
    p("")

# 陈昶文：单独拉（会话 key 待定）
p("="*104); p("【陈昶文】查找会话 key"); p("="*104)
for r in c.execute("select talker, display_name, session_type, message_count from sessions where display_name like '%陈昶文%'"):
    p(dict(r))
open("probe_1009c.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
