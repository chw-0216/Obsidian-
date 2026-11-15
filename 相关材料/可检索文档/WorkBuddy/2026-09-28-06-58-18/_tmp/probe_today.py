# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)

today = datetime.datetime(2026,10,8,0,0,0)
t0 = int(today.timestamp())

TARGETS = {
 "a35599192":"yumilier☔（小王阿姨？）",
 "filehelper":"文件传输助手（我自己的记录）",
 "deerluna":"陈晔（导师）",
}
for tk, nm in TARGETS.items():
    p("="*96); p("【%s】  %s" % (nm, tk)); p("="*96)
    rows = c.execute("""select ts, role, type, content from messages
        where session_key=? and ts>=? order by ts""", (tk, t0)).fetchall()
    if not rows:
        p("  (今日无)"); p("")
        continue
    for r in rows:
        t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%H:%M:%S")
        cont = (r["content"] or "").replace("\n"," / ")
        p("  [%s] %-5s t=%-3s %s" % (t, r["role"], r["type"], cont[:400]))
    p("")

# 群：Tripothon / 泰语 / 立项2群
p("="*96); p("【群聊 · 今日】"); p("="*96)
rows = c.execute("""select m.ts, s.display_name, m.role, m.type, m.content
    from messages m left join sessions s on s.talker=m.session_key
    where m.ts>=? and s.session_type in ('group','channel')
      and s.display_name in ('Tripothon S1 中国赛区2群','2026泰语学习群（暗黑）',
      '立项2群-第三届Movers4Climate绿色乡村青年行动','跨媒体艺术','【F333】像素蛋糕AI修图产品体验群')
    order by m.ts""", (t0,)).fetchall()
for r in rows:
    t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%H:%M")
    p("  [%s] %-30s %s | %s" % (t, (r["display_name"] or "?")[:30], r["role"], (r["content"] or "").replace("\n"," / ")[:260]))

open("probe_today.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
