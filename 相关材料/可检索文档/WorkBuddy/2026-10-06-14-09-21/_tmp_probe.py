# -*- coding: utf-8 -*-
"""定向核查：8/2 寻街我在不在场 / 8/20 英文错误谁说的 / 寻街 全库命中"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
def T(s): return int(datetime.datetime.strptime(s, '%Y-%m-%d %H:%M').timestamp())

# 1) 8/20 19:34 央美美育工作站 群的 sender 原始 wxid
sk = c.execute("select talker from sessions where display_name='央美美育工作站'").fetchone()[0]
print("=== 央美美育工作站 session_key:", sk)
rows = c.execute("""select ts, role, sender, substr(content,1,120) from messages
   where session_key=? and ts>=? and ts<? order by ts""", (sk, T('2026-08-20 19:00'), T('2026-08-20 20:30'))).fetchall()
for ts, role, sd, ct in rows:
    print(f"{fmt(ts)} role={role} sender={sd} :: {ct}")

# 2) 8/2 全天 工作站群 + 关键人，看领导是否到工作站
print("\n=== 8/2 央美美育工作站 群全天 ===")
rows = c.execute("""select ts, role, sender, substr(content,1,160) from messages
   where session_key=? and ts>=? and ts<? order by ts""", (sk, T('2026-08-02 00:00'), T('2026-08-03 00:00'))).fetchall()
for ts, role, sd, ct in rows:
    if '<img' in ct or '<msg' in ct: ct = ct.split('<')[0][:60] + ' 〔图〕'
    print(f"{fmt(ts)} {role:<5} {str(sd)[:24]:<26} {ct}")

# 3) 全库搜 寻街 / 开街 相关（井邻线）
print("\n=== 全库『寻街』命中 ===")
for ts, skk, role, sd, ct in c.execute("""select ts, session_key, role, sender, substr(content,1,150) from messages
   where content like '%寻街%' and ts>=? and ts<? order by ts""", (T('2026-07-01 00:00'), T('2026-10-07 00:00'))).fetchall():
    nm = c.execute("select display_name from sessions where talker=?", (skk,)).fetchone()
    print(f"{fmt(ts)} [{nm[0] if nm else skk}] {role} {ct[:130]}")

# 4) 8/20 领导是否到过工作站（群里提到）
print("\n=== 8/20 全库『区长/文旅局/领导』命中 ===")
for ts, skk, role, sd, ct in c.execute("""select ts, session_key, role, sender, substr(content,1,180) from messages
   where (content like '%区长%' or content like '%文旅局%' or content like '%视察%') and ts>=? and ts<? order by ts""",
   (T('2026-08-18 00:00'), T('2026-08-22 00:00'))).fetchall():
    nm = c.execute("select display_name from sessions where talker=?", (skk,)).fetchone()
    print(f"{fmt(ts)} [{nm[0] if nm else skk}] {role} {ct[:150]}")
