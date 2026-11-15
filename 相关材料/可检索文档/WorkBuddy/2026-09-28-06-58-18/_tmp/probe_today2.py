# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)

p("="*96); p("① sessions.session_type 取值分布"); p("="*96)
for r in c.execute("select session_type, count(*) n from sessions group by session_type order by n desc"):
    p("  %-14s %d" % (r["session_type"], r["n"]))

t0 = int(datetime.datetime(2026,10,8,0,0,0).timestamp())
p(""); p("="*96); p("② 今日群聊（session_key 含 @chatroom）"); p("="*96)
rows = c.execute("""select m.ts, s.display_name, m.role, m.type, m.content, m.session_key
  from messages m left join sessions s on s.talker=m.session_key
  where m.ts>=? and m.session_key like '%@chatroom' order by m.ts""",(t0,)).fetchall()
p("命中 %d 条" % len(rows))
for r in rows:
    t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%H:%M")
    p("  [%s] %-26s %-5s %-5s | %s" % (t,(r["display_name"] or "?")[:26],r["role"],r["type"],
      (r["content"] or "").replace("\n"," / ")[:200]))

p(""); p("="*96); p("③ yumilier☔ 全量（a35599192）"); p("="*96)
rows = c.execute("""select ts, role, type, content from messages where session_key='a35599192' order by ts""").fetchall()
p("共 %d 条" % len(rows))
for r in rows:
    t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d %H:%M")
    p("  [%s] %-5s %-5s | %s" % (t,r["role"],r["type"],(r["content"] or "").replace("\n"," / ")[:220]))

p(""); p("="*96); p("④ 舒泽林 10-07 起"); p("="*96)
t1 = int(datetime.datetime(2026,10,6,0,0,0).timestamp())
rows = c.execute("""select ts, role, type, content from messages
  where session_key='wxid_0ejd54z34nmv32' and ts>=? order by ts""",(t1,)).fetchall()
for r in rows:
    t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M")
    p("  [%s] %-5s %-5s | %s" % (t,r["role"],r["type"],(r["content"] or "").replace("\n"," / ")[:200]))

open("probe_today2.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
