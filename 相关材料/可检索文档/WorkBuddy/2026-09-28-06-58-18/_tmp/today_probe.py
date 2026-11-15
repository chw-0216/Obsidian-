# -*- coding: utf-8 -*-
r"""today_probe.py —— 看今天发生了什么 + 定位指定人物"""
import os, sqlite3, datetime, sys, io

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

# 今天零点
today = datetime.date(2026, 10, 6)
t0 = int(datetime.datetime(2026, 10, 6, 0, 0, 0).timestamp())
t1 = int(datetime.datetime(2026, 10, 7, 0, 0, 0).timestamp())

print("=" * 70)
print("① 今天（2026-10-06）有消息的会话")
print("=" * 70)
rows = con.execute("""
  select session_key, count(*) n, min(ts) a, max(ts) b,
         sum(case when role='me' then 1 else 0 end) me
    from messages where ts >= ? and ts < ?
   group by session_key order by b desc
""", (t0, t1)).fetchall()
print("会话数：%d" % len(rows))
names = {}
for r in con.execute("select talker, display_name from sessions"):
    names[r["talker"]] = r["display_name"]
for r in rows:
    print("  %-42s %-4d 我%-3d  %s → %s" % (
        (names.get(r["session_key"]) or r["session_key"])[:40],
        r["n"], r["me"], fmt(r["a"])[11:], fmt(r["b"])[11:]))

print()
print("=" * 70)
print("② 关键人物定位（按 display_name / 正文）")
print("=" * 70)
for kw in ["舒泽林", "舒哥", "王逸伦", "逸伦", "王若彤", "若彤"]:
    print("--- %s ---" % kw)
    # 会话名
    for r in con.execute(
            "select talker, display_name, session_type, message_count from sessions "
            "where display_name like ?", ("%" + kw + "%",)):
        print("   [会话] %s | %s | %s | %d 条" % (
            r["display_name"], r["talker"], r["session_type"], r["message_count"]))
    # 正文
    for r in con.execute(
            "select session_key, ts, role, substr(content,1,80) c from messages "
            "where content like ? order by ts desc limit 6", ("%" + kw + "%",)):
        print("   [正文] %s | %s | %s | %s" % (
            fmt(r["ts"]), (names.get(r["session_key"]) or r["session_key"])[:22],
            r["role"], (r["c"] or "").replace("\n", " ")))
    print()
