# -*- coding: utf-8 -*-
import sqlite3, io, sys, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row

def p(*a):
    print(*a, file=out)

# 1) 最近 3 小时所有消息
p("="*90); p("① 最近 3 小时全部消息（按时间）"); p("="*90)
rows = c.execute("""
 select m.ts, m.time_text, s.display_name, m.session_key, m.role, m.type,
        substr(replace(m.content, char(10), ' / '),1,220) as c
 from messages m left join sessions s on s.talker = m.session_key
 where m.ts >= strftime('%s','now','localtime') - 3*3600
 order by m.ts
""").fetchall()
p("命中 %d 条" % len(rows))
for r in rows:
    t = datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M:%S")
    p("[%s] %-22s %-4s %-3s | %s" % (t, (r["display_name"] or "?")[:22], r["role"], r["type"], r["c"]))

# 2) 今日（00:00 起）按会话聚合
p(""); p("="*90); p("② 今日（10-08 00:00 起）按会话聚合"); p("="*90)
rows = c.execute("""
 select s.display_name, m.session_key, count(*) n, min(m.ts) a, max(m.ts) b,
        sum(case when m.role='me' then 1 else 0 end) me,
        sum(case when m.role='them' then 1 else 0 end) them
 from messages m left join sessions s on s.talker = m.session_key
 where m.ts >= strftime('%s', date('now','localtime','start of day'))
 group by m.session_key order by n desc
""").fetchall()
for r in rows:
    p("%-28s n=%-4d me=%-4d them=%-4d  %s ~ %s" % (
        (r["display_name"] or r["session_key"])[:28], r["n"], r["me"] or 0, r["them"] or 0,
        datetime.datetime.fromtimestamp(r["a"]).strftime("%m-%d %H:%M"),
        datetime.datetime.fromtimestamp(r["b"]).strftime("%H:%M")))

# 3) 六大主线水位
p(""); p("="*90); p("③ 主要会话水位"); p("="*90)
TALKERS = {
 "deerluna":"陈晔","wxid_wdnk6ue9kiyn22":"笑一","wxid_id1nfp5f20e122":"沐茜妍(林立娜)",
 "wxid_0ejd54z34nmv32":"舒泽林","wxid_5049180491911":"柯益盈","huxiaomi123":"何一莎",
 "a35599192":"yumilier","wxid_y8f0y4jfthgs21":"关宇佳","filehelper":"文件传输助手",
}
for tk, nm in TALKERS.items():
    r = c.execute("""select count(*) n, max(ts) b, min(ts) a,
        sum(case when role='me' then 1 else 0 end) me,
        sum(case when role='them' then 1 else 0 end) them
        from messages where session_key=?""", (tk,)).fetchone()
    if not r or not r["n"]:
        p("%-18s (无)" % nm); continue
    p("%-18s n=%-6d me=%-6d them=%-6d  %s ~ %s  (距今天 %d)" % (
        nm, r["n"], r["me"] or 0, r["them"] or 0,
        datetime.datetime.fromtimestamp(r["a"]).strftime("%Y-%m-%d"),
        datetime.datetime.fromtimestamp(r["b"]).strftime("%Y-%m-%d %H:%M"),
        (datetime.date.today() - datetime.date.fromtimestamp(r["b"])).days))

# 4) 全库总览
p(""); p("="*90); p("④ 全库总览"); p("="*90)
p("messages 总数 = %d" % c.execute("select count(*) from messages").fetchone()[0])
p("sessions 总数 = %d" % c.execute("select count(*) from sessions").fetchone()[0])
mx = c.execute("select max(ts) from messages").fetchone()[0]
p("全库最新 = %s" % datetime.datetime.fromtimestamp(mx).strftime("%Y-%m-%d %H:%M:%S"))

open("probe_delta.out","w",encoding="utf-8").write(out.getvalue())
print("written probe_delta.out, %d chars" % len(out.getvalue()))
