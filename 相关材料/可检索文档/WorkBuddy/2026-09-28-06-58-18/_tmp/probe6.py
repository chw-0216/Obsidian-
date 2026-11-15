# -*- coding: utf-8 -*-
r"""probe6.py —— 定位新线索：安鹏 / 柯益盈 / 何一沙 / Tripo / 极狐 北汽"""
import sqlite3, datetime, re
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
def cl(c):
    if not c: return ""
    if '<' in c:
        h=c.split('<')[0].strip(); return (h[:90]+' 〔卡片/图〕') if h else '〔卡片/图〕'
    return c.replace("\n"," ")[:150]
names = {r["talker"]: r["display_name"] for r in con.execute("select talker, display_name from sessions")}

KWS = ["安鹏","柯益盈","益盈","何一沙","何一莎","一沙","Tripo","tripo","极狐","北汽","洗车","数字人"]
for kw in KWS:
    print("=" * 74)
    print("【%s】" % kw)
    print("=" * 74)
    hit = 0
    for r in con.execute("select talker, display_name, session_type, message_count from sessions where display_name like ?", ("%"+kw+"%",)):
        print("  [会话] %s | %s | %s | %s 条" % (r["display_name"], r["talker"], r["session_type"], r["message_count"]))
        hit += 1
    for r in con.execute("select session_key, ts, role, content from messages where content like ? order by ts desc limit 8", ("%"+kw+"%",)):
        print("  [正文] %s | %-16s | %-3s | %s" % (f(r["ts"]),
              (names.get(r["session_key"]) or r["session_key"])[:16],
              "我" if r["role"]=="me" else ("他" if r["role"]=="them" else "sys"), cl(r["content"])))
        hit += 1
    if not hit: print("  （无命中）")
    print()
