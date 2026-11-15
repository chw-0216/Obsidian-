# -*- coding: utf-8 -*-
import sqlite3, io, datetime, json
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
c = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\","/"), uri=True)
c.row_factory = sqlite3.Row
out = io.StringIO()
def p(*a): print(*a, file=out)
def dt(v): return datetime.datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M")

p("="*90); p("一、数据底座"); p("="*90)
n = c.execute("select count(*) from messages").fetchone()[0]
s = c.execute("select count(distinct session_key) from messages").fetchone()[0]
a,b = c.execute("select min(ts),max(ts) from messages").fetchone()
p("消息总数 = %d" % n); p("会话总数 = %d" % s); p("时间范围 = %s → %s" % (dt(a), dt(b)))
p("")
for r in c.execute("""select s.session_type, count(*) n, sum(s.message_count) m
   from sessions s group by 1 order by m desc"""):
    p("  %-6s 会话 %-5d 条数 %d" % (r["session_type"], r["n"], r["m"]))

p(""); p("--- 零发言会话 ---")
r = c.execute("""select count(*) n, sum(cnt) t from (
   select session_key, count(*) cnt, sum(case when role='me' then 1 else 0 end) me
   from messages group by session_key) where me=0""").fetchone()
p("  零发言会话 = %d 个 / %d 条 = %.1f%%" % (r["n"], r["t"], 100.0*r["t"]/n))

p(""); p("="*90); p("二、关键人基准（私聊·实时）"); p("="*90)
NAMES = ["刘丽萍","蔡峰峰","笑一","陈昶文","Eloise","沐茜妍","甘泉","🍬🍬","Parapluie","小苹果",
         "薛伟东","汪伊俊","舒泽林","王若彤","yumilier","deerluna","filehelper","huxiaomi123",
         "wxid_5049180491911","wxid_y8f0y4jfthgs21","wxid_id1nfp5f20e122","wxid_wdnk6ue9kiyn22",
         "wxid_0ejd54z34nmv32"]
today = datetime.date(2026,10,8)
rows=[]
for nm in NAMES:
    q = c.execute("""select m.session_key, count(*) n, min(m.ts) a, max(m.ts) b,
        sum(case when m.role='me' then 1 else 0 end) me
        from messages m where m.session_key=? or m.session_key in
        (select talker from sessions where display_name=?)
        group by m.session_key order by n desc limit 1""",(nm,nm)).fetchone()
    if not q: 
        p("  %-22s (无)" % nm); continue
    disp = c.execute("select display_name from sessions where talker=?",(q["session_key"],)).fetchone()
    disp = disp["display_name"] if disp else q["session_key"]
    d = (today - datetime.date.fromtimestamp(q["b"])).days
    pct = 100.0*(q["me"] or 0)/q["n"]
    p("  %-24s %-22s n=%-6d 我发%5.1f%% 距今天 %-4d  %s → %s" % (
        nm, (disp or "")[:22], q["n"], pct, d,
        datetime.date.fromtimestamp(q["a"]).isoformat(), dt(q["b"])))

p(""); p("="*90); p("三、逐月分布（近 8 个月）"); p("="*90)
for r in c.execute("""select strftime('%Y-%m', ts,'unixepoch','localtime') ym, count(*) n,
   count(distinct session_key) sk,
   sum(case when role='me' then 1 else 0 end) me
   from messages group by 1 order by 1 desc limit 10"""):
    p("  %s  %-7d 会话 %-5d 我发 %5.1f%%" % (r["ym"], r["n"], r["sk"], 100.0*(r["me"] or 0)/r["n"]))

p(""); p("="*90); p("四、我发占比基准（私聊 ≥150 条）"); p("="*90)
rows = c.execute("""select m.session_key, count(*) n,
   sum(case when m.role='me' then 1 else 0 end) me
   from messages m join sessions s on s.talker=m.session_key
   where s.session_type='私聊' group by m.session_key having n>=150""").fetchall()
pcts = sorted(100.0*(r["me"] or 0)/r["n"] for r in rows)
import statistics
p("  人数 = %d" % len(pcts))
p("  中位数 = %.1f%%  均值 = %.1f%%  Q1 = %.1f%%  Q3 = %.1f%%" % (
    statistics.median(pcts), statistics.mean(pcts),
    pcts[int(len(pcts)*0.25)], pcts[int(len(pcts)*0.75)]))
low = [(100.0*(r["me"] or 0)/r["n"], r["session_key"], r["n"]) for r in rows if 100.0*(r["me"] or 0)/r["n"]<45]
low.sort()
p("  对方发得比他多的（<45%%）共 %d 人：" % len(low))
for pc,k,nn in low:
    d = c.execute("select display_name from sessions where talker=?",(k,)).fetchone()
    p("    %-24s %.1f%%  (%d 条)" % ((d["display_name"] if d else k)[:24], pc, nn))

open("recalc_1008b.out","w",encoding="utf-8").write(out.getvalue())
print("ok", len(out.getvalue()))
