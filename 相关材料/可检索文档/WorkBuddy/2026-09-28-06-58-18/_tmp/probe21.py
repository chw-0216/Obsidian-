# -*- coding: utf-8 -*-
r"""probe21.py —— 10-07 更新：全库增量 + 全天消息 + 关键人物动态"""
import sqlite3, datetime
from collections import Counter
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M:%S")

print("#" * 96); print("① 索引库总览"); print("#" * 96)
n = con.execute("select count(*) c from messages").fetchone()["c"]
ns = con.execute("select count(*) c from sessions").fetchone()["c"]
mn = con.execute("select min(ts) a, max(ts) b from messages").fetchone()
print("  消息 %d · 会话 %d · 窗口 %s ~ %s" % (n, ns, f(mn["a"]), f(mn["b"])))

print(); print("#" * 96); print("② 10-07 全天 · 全部消息"); print("#" * 96)
t0 = int(datetime.datetime(2026, 10, 7, 0, 0).timestamp())
rows = con.execute("select m.session_key, s.display_name, m.ts, m.role, m.type, m.content from messages m left join sessions s on s.talker=m.session_key where m.ts>=? order by m.ts", (t0,)).fetchall()
print("  共 %d 条 · 活跃会话 %d" % (len(rows), len(set(r["session_key"] for r in rows))))
print()
for r in rows:
    c = (r["content"] or "").replace("\n", " ")
    if "<" in c[:6]:
        c = "〔%s〕%s" % (r["type"], c.split("<")[0].strip()[:60])
    nm = (r["display_name"] or r["session_key"])[:18]
    print("  [%s] %-18s %-4s %s" % (f(r["ts"])[9:], nm, "我" if r["role"] == "me" else "他", c[:160]))

print(); print("#" * 96); print("③ 关键人物 10-06 00:00 → 现在"); print("#" * 96)
names = ["舒泽林", "笑一", "柯益盈", "刘丽萍", "何一沙", "汪伊俊", "王逸伦", "王若彤", "安鹏", "王义", "榆巷", "极狐", "gay学", "韩"]
t1 = int(datetime.datetime(2026, 10, 6, 0, 0).timestamp())
seen = set()
for nm in names:
    for s in con.execute("select talker, display_name from sessions where display_name like ?", ("%" + nm + "%",)).fetchall():
        if s["talker"] in seen: continue
        seen.add(s["talker"])
        msgs = con.execute("select ts, role, type, content from messages where session_key=? and ts>=? order by ts", (s["talker"], t1)).fetchall()
        if msgs:
            print("  ── %s（%s）%d 条" % (s["display_name"], s["talker"], len(msgs)))
            for m in msgs:
                c = (m["content"] or "").replace("\n", " ")
                if "<" in c[:6]: c = "〔%s〕" % m["type"]
                print("     [%s] %-4s %s" % (f(m["ts"]), "我" if m["role"] == "me" else "他", c[:150]))
