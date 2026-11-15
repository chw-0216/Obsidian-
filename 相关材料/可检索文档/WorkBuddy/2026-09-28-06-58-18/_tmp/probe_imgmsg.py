# -*- coding: utf-8 -*-
"""查 06/07 窗口的图片消息：谁在什么时候发了图"""
import sqlite3, sys, datetime, re, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
con = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row

name = {}
for sk, dn, st in con.execute("select talker, display_name, session_type from sessions"):
    name[sk] = (dn or sk, st or "")

def win(tag, lo, hi):
    a = int(datetime.datetime.strptime(lo, "%Y-%m-%d").timestamp())
    b = int(datetime.datetime.strptime(hi, "%Y-%m-%d").timestamp())
    print("\n" + "=" * 74)
    print("%s  %s ~ %s" % (tag, lo, hi))
    print("=" * 74)
    rows = list(con.execute(
        "select ts, session_key, role, content from messages "
        "where type='image' and ts>=? and ts<=? order by ts", (a, b)))
    print("  图片消息 %d 条" % len(rows))
    cnt = collections.Counter()
    for r in rows:
        sk = r["session_key"]; nm, st = name.get(sk, (sk, ""))
        cnt[(nm, st, r["role"])] += 1
    print("  按会话（前 20）：")
    for (nm, st, role), n in cnt.most_common(20):
        print("    %-30s %-6s %-6s %d" % (nm[:30], st, role, n))
    # 打印几条 me 的
    print("  role=me 抽样（时间 / 会话 / 内容摘要）：")
    k = 0
    for r in rows:
        if r["role"] != "me": continue
        nm, st = name.get(r["session_key"], (r["session_key"], ""))
        d = datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M")
        txt = re.sub(r"<[^>]+>", " ", r["content"] or "")[:70]
        print("    %s %-24s %s" % (d, nm[:24], txt))
        k += 1
        if k >= 15: break

win("06 厦门集美", "2026-04-18", "2026-05-20")
win("07 北京台实习", "2026-01-01", "2026-02-20")
win("08 数字人/交互", "2026-07-01", "2026-09-30")
