# -*- coding: utf-8 -*-
r"""probe19.py —— 舒泽林 10-06~10-07 原始消息（含图片XML） + 昨天饭局全库定位"""
import sqlite3, datetime, re, os, glob
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
SK = "wxid_0ejd54z34nmv32"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M:%S")

t0 = int(datetime.datetime(2026, 10, 6, 0, 0).timestamp())

print("#" * 96)
print("① 舒泽林 10-06 00:00 → 现在 · 原始 content（不截断）")
print("#" * 96)
rows = con.execute("select ts, role, type, content from messages where session_key=? and ts>=? order by ts", (SK, t0)).fetchall()
for r in rows:
    print("-" * 90)
    print("[%s] role=%s type=%s len=%d" % (f(r["ts"]), r["role"], r["type"], len(r["content"] or "")))
    print((r["content"] or "")[:1500])

print()
print("#" * 96)
print("② 全库 10-06 00:00 → 10-07 12:00 · 含「舒」「饭」「局」「来」的会话（找昨天饭局）")
print("#" * 96)
rows2 = con.execute("select m.session_key, s.display_name, m.ts, m.role, m.content from messages m left join sessions s on s.talker=m.session_key where m.ts>=? and m.ts<? order by m.ts",
                    (t0, int(datetime.datetime(2026, 10, 7, 12, 0).timestamp()))).fetchall()
kws = ["舒", "饭", "局", "来吧", "来吗", "一起吃", "晚上", "喝酒", "聚"]
hit = 0
for r in rows2:
    c = r["content"] or ""
    if any(k in c for k in kws) and "<" not in c[:5]:
        hit += 1
        nm = r["display_name"] or r["session_key"]
        print("  [%s] %-18s %-4s %s" % (f(r["ts"]), nm[:18], "我" if r["role"] == "me" else "他", c.replace("\n", " ")[:160]))
print("  → 命中 %d 条" % hit)

print()
print("#" * 96)
print("③ 10-06 全天活跃会话 TOP（看饭局前后谁在说话）")
print("#" * 96)
from collections import Counter
cnt = Counter()
for r in rows2:
    cnt[r["display_name"] or r["session_key"]] += 1
for k, v in cnt.most_common(30):
    print("    %-26s %4d" % (k[:26], v))

print()
print("#" * 96)
print("④ 找图：索引库 media 目录 / 解密目录里 10-07 附近的图片文件")
print("#" * 96)
for root in [r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp",
             r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted"]:
    print("  -- root: %s  存在=%s" % (root, os.path.isdir(root)))
    if os.path.isdir(root):
        for d in os.listdir(root)[:40]:
            p = os.path.join(root, d)
            print("     %s%s" % (d, "/" if os.path.isdir(p) else ""))

print()
print("#" * 96)
print("⑤ index.sqlite 里所有表")
print("#" * 96)
for r in con.execute("select name from sqlite_master where type='table'"):
    print("   ", r["name"])
