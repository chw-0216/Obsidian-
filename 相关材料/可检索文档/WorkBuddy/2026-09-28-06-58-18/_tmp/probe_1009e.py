# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)
def ts(v): return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M")
T0 = int(datetime.datetime(2026,10,8,14,29,0).timestamp())

GRPS = ["Tripothon S1 中国赛区2群","2025-2026积极分子","CAFA◇灬姎羙𠧫抽象¨人｝🔫℡","白露东21号楼——003网格"]
for g in GRPS:
    p("="*104); p("【%s】" % g); p("="*104)
    rows = c.execute("""select m.ts, s.display_name, m.role, m.type, m.content from messages m
      left join sessions s on s.talker=m.session_key
      where m.ts>=? and s.display_name=? order by m.ts""", (T0,g)).fetchall()
    p("共 %d 条" % len(rows))
    for r in rows:
        cont = (r["content"] or "").replace("\n"," / ")
        if r["type"] in ("image","sticker","video","voice"): cont = "<%s>" % r["type"]
        p("[%s] %-5s %-8s %s" % (ts(r["ts"]), r["role"], r["type"], cont[:250]))
    p("")

# 微信支付（现金流）
p("="*104); p("【微信支付 · 公众号通知】"); p("="*104)
rows = c.execute("""select m.ts, m.content from messages m left join sessions s on s.talker=m.session_key
  where m.ts>=? and s.display_name='微信支付' order by m.ts""", (T0,)).fetchall()
for r in rows:
    p("[%s] %s" % (ts(r["ts"]), (r["content"] or "").replace("\n"," / ")[:220]))
open("probe_1009e.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
