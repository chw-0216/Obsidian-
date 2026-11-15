# -*- coding: utf-8 -*-
r"""probe17.py —— ★★★ 完整驾驶事故史（跨会话 · role=me · 12 个月）"""
import sqlite3, datetime, re
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")

# 会话名映射
NAME = {}
for r in con.execute("select talker, display_name from sessions"):
    NAME[r["talker"]] = r["display_name"] or r["talker"]

KWS = ["剐蹭", "刮了", "刮了一下", "刮花", "蹭了", "撞", "事故", "保险杠", "追尾",
       "碰了", "撞车", "出险", "定损", "理赔", "报案", "修车", "漆面", "钣金",
       "全责", "责任认定", "交强险", "商业险", "车损", "走保险", "扣分", "违章", "罚单"]
seen = {}
for kw in KWS:
    for r in con.execute("select session_key, ts, role, content from messages where content like ? and role='me'", ("%" + kw + "%",)):
        seen[(r["session_key"], r["ts"])] = (r["content"], kw)

rows = sorted([(ts, sk, c, kw) for (sk, ts), (c, kw) in seen.items()])
print("命中 %d 条（去重后 · 全部 role=me）" % len(rows))
print("=" * 100)
cur = None
for ts, sk, c, kw in rows:
    day = f(ts)[:8]
    if day != cur:
        cur = day
        print()
        print("── %s ──" % day)
    cc = (c or "").replace("\n", " ")
    if "<" in cc: cc = cc.split("<")[0].strip()[:110] or "〔媒体〕"
    if len(cc) > 150: cc = cc[:150] + "…"
    print("  [%s] %-12s %s" % (f(ts)[9:], (NAME.get(sk, sk))[:12], cc))

print()
print("=" * 100)
print("按会话聚合（谁听到最多）")
from collections import Counter
c2 = Counter()
for ts, sk, c, kw in rows: c2[NAME.get(sk, sk)] += 1
for k, v in c2.most_common(25):
    print("  %-22s %4d" % (k, v))
