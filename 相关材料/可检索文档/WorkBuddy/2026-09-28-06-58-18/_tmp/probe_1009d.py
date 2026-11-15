# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)
def ts(v): return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M")

T0 = int(datetime.datetime(2026,10,8,14,29,0).timestamp())
for tk, nm in [("wxid_0gb0smyjaoyk22","陈昶文"), ("wxid_5049180491911","柯益盈")]:
    p("="*104); p("【%s】 %s" % (nm, tk)); p("="*104)
    rows = c.execute("""select ts, role, type, content from messages
        where session_key=? and ts>=? order by ts""", (tk, T0)).fetchall()
    p("共 %d 条" % len(rows))
    for r in rows:
        cont = (r["content"] or "").replace("\n"," / ")
        if r["type"] in ("image","sticker","video","voice"): cont = "<%s>" % r["type"]
        p("[%s] %-5s %-8s %s" % (ts(r["ts"]), r["role"], r["type"], cont[:420]))
    p("")

# 陈昶文：这条线的历史（归零点与重启点）
p("="*104); p("【陈昶文 · 历史脉络】近 20 条 + 断点"); p("="*104)
rows = c.execute("""select ts, role, substr(content,1,120) c from messages
    where session_key='wxid_0gb0smyjaoyk22' order by ts desc limit 30""").fetchall()
for r in reversed(rows):
    p("[%s] %-5s %s" % (datetime.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d %H:%M"), r["role"], (r["c"] or "").replace("\n"," / ")[:130]))
p("")
p("--- 按月分布 ---")
for r in c.execute("""select strftime('%Y-%m',ts,'unixepoch','localtime') ym, count(*) n
    from messages where session_key='wxid_0gb0smyjaoyk22' group by 1 order by 1 desc limit 14"""):
    p("  %s  %d" % (r["ym"], r["n"]))

# 李紫懿
p(""); p("="*104); p("【李紫懿】"); p("="*104)
rows = c.execute("""select m.ts, m.role, m.type, m.content, s.talker from messages m
    left join sessions s on s.talker=m.session_key
    where m.ts>=? and s.display_name like '%李紫懿%' order by m.ts""", (T0,)).fetchall()
for r in rows:
    cont = (r["content"] or "").replace("\n"," / ")
    if r["type"] in ("image","sticker","video","voice"): cont = "<%s>" % r["type"]
    p("[%s] %-5s %-8s %s" % (ts(r["ts"]), r["role"], r["type"], cont[:350]))

open("probe_1009d.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
