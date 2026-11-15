# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)

NAMES = ["曹庆辉","孙天智","武脉仪","叶敏","林茂","中关村","当兵","征兵","中期汇报","井邻","3D","3d","三维"]
p("="*100); p("① 通讯录 / 会话名命中"); p("="*100)
for n in NAMES:
    rows = c.execute("select talker, display_name, session_type, message_count from sessions where display_name like ? limit 5", ("%"+n+"%",)).fetchall()
    if rows:
        for r in rows: p("  [会话] %-8s -> %-30s %-6s %s" % (n, r["display_name"], r["session_type"], r["message_count"]))
    else:
        p("  [会话] %-8s -> (无)" % n)

p(""); p("="*100); p("② 消息正文命中（最近 120 天，最多各 8 条）"); p("="*100)
T0 = int(datetime.datetime(2026,6,1).timestamp())
for n in ["曹庆辉","孙天智","武脉仪","叶敏","林茂","中关村","当兵","征兵","中期汇报","井邻"]:
    rows = c.execute("""select m.ts, s.display_name, m.role, substr(m.content,1,150) c
      from messages m left join sessions s on s.talker=m.session_key
      where m.ts>=? and m.content like ? and length(m.content)<3000
      order by m.ts desc limit 8""", (T0, "%"+n+"%")).fetchall()
    p("--- %s : %d 条 ---" % (n, len(rows)))
    for r in rows:
        p("   [%s] %-22s %-5s %s" % (datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M"),
          (r["display_name"] or "?")[:22], r["role"], (r["c"] or "").replace("\n"," / ")[:150]))

open("probe_names_1009.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
