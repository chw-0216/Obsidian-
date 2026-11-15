# -*- coding: utf-8 -*-
import sqlite3, io, datetime
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
out = io.StringIO()
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
def p(*a): print(*a, file=out)
def ts(v): return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M:%S")

# 上次水位 = 2026-10-08 14:29
T0 = int(datetime.datetime(2026,10,8,14,29,0).timestamp())

p("="*100); p("① 增量总览（10-08 14:29 之后）"); p("="*100)
r = c.execute("select count(*) n, count(distinct session_key) sk from messages where ts>=?", (T0,)).fetchone()
p("新增 %d 条 · 涉及 %d 个会话" % (r["n"], r["sk"]))

p(""); p("="*100); p("② 按会话聚合（按条数降序，前 40）"); p("="*100)
rows = c.execute("""
 select m.session_key, s.display_name, s.session_type, count(*) n, min(m.ts) a, max(m.ts) b,
        sum(case when m.role='me' then 1 else 0 end) me,
        sum(case when m.role='them' then 1 else 0 end) them
 from messages m left join sessions s on s.talker=m.session_key
 where m.ts>=? group by m.session_key order by n desc limit 40
""", (T0,)).fetchall()
for r in rows:
    p("%-30s %-8s n=%-5d me=%-5d them=%-5d  %s ~ %s" % (
        (r["display_name"] or r["session_key"])[:30], r["session_type"] or "?", r["n"],
        r["me"] or 0, r["them"] or 0, ts(r["a"]), ts(r["b"])))

p(""); p("="*100); p("③ 主要会话水位（截至 10-09 09:00）"); p("="*100)
TALKERS = {
 "deerluna":"陈晔(导师)","wxid_wdnk6ue9kiyn22":"笑一","wxid_id1nfp5f20e122":"沐茜妍(林立娜)",
 "wxid_0ejd54z34nmv32":"舒泽林","wxid_5049180491911":"柯益盈","huxiaomi123":"何一莎",
 "a35599192":"王利敏(小王阿姨)","guo647789":"李老师(海燕)","wxid_y8f0y4jfthgs21":"关宇佳",
 "filehelper":"文件传输助手","wxid_1wa75s1kze3o22":"刘丽萍(母)",
}
for tk, nm in TALKERS.items():
    r = c.execute("""select count(*) n, max(ts) b, min(ts) a,
        sum(case when role='me' then 1 else 0 end) me
        from messages where session_key=?""", (tk,)).fetchone()
    if not r or not r["n"]:
        p("%-20s (无)" % nm); continue
    d = (datetime.date(2026,10,9) - datetime.date.fromtimestamp(r["b"])).days
    p("%-20s n=%-6d me=%-6d 我发%5.1f%%  %s → %s  (距今天 %d)" % (
        nm, r["n"], r["me"] or 0, 100.0*(r["me"] or 0)/r["n"],
        datetime.date.fromtimestamp(r["a"]).isoformat(), ts(r["b"]), d))

p(""); p("="*100); p("④ 全库总览"); p("="*100)
p("messages = %d" % c.execute("select count(*) from messages").fetchone()[0])
p("sessions = %d" % c.execute("select count(*) from sessions").fetchone()[0])
p("全库最新 = %s" % ts(c.execute("select max(ts) from messages").fetchone()[0]))

open("probe_1009.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
