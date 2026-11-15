# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()
def dt(ts): return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

# 找文件传输助手
cur.execute("SELECT talker, display_name FROM sessions WHERE display_name LIKE '%文件传输%'")
print("会话:", cur.fetchall())
tk = cur.fetchone()
cur.execute("SELECT talker FROM sessions WHERE display_name LIKE '%文件传输%' LIMIT 1")
row = cur.fetchone()
tk = row[0] if row else None
print("talker =", tk)

lo = int(datetime.datetime(2026,4,1,0,0).timestamp())
hi = int(datetime.datetime(2026,4,30,23,59).timestamp())
cur.execute("""SELECT m.ts, m.role, m.content FROM messages m
   WHERE m.session_key=? AND m.ts BETWEEN ? AND ? ORDER BY m.ts""", (tk, lo, hi))
rows = cur.fetchall()
print(f"2026-04 文件传输助手共 {len(rows)} 条\n")

lines = []
for ts, role, c in rows:
    c = str(c)
    if any(x in c for x in ['<img','<msg','<appmsg','<emoji','<videomsg','CDATA']):
        c = c.split('<')[0][:200] + " 〔图/附件〕"
    lines.append(f"[{dt(ts)}] {'我' if role=='me' else '对方'}:\n{c}")

open("_tmp_jinglin/文件传输助手_202604.txt","w",encoding="utf-8").write("\n\n".join(lines))
print("已写出 _tmp_jinglin/文件传输助手_202604.txt")
# 打印长文本索引
for ts, role, c in rows:
    c = str(c)
    if len(c) > 1200 and not any(x in c for x in ['CDATA','support.weixin']):
        print(f"  [{dt(ts)}] {len(c)}字  {c[:60].replace(chr(10),' ')}")
