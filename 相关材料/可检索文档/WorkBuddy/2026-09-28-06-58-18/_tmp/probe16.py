# -*- coding: utf-8 -*-
r"""probe16.py —— 深度：① 柯益盈 251 条的时间分布（是否只有两天）② 极狐事故模式 ③ 决策中枢六线资源冲突"""
import sqlite3, datetime
from collections import Counter, defaultdict
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")
def d(ts): return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

print("#" * 92); print("① 柯益盈 251 条 · 逐日分布"); print("#" * 92)
rows = con.execute("select ts, role, content from messages where session_key='wxid_5049180491911' order by ts").fetchall()
print("  总 %d 条" % len(rows))
byday = defaultdict(lambda: [0, 0, 0])   # day -> [me, them, total]
for r in rows:
    k = d(r["ts"])
    byday[k][2] += 1
    byday[k][0 if r["role"] == "me" else 1] += 1
print("  %-12s %6s %6s %6s" % ("日期", "我发", "她发", "合计"))
for k in sorted(byday):
    me, th, tot = byday[k]
    print("  %-12s %6d %6d %6d   %s" % (k, me, th, tot, "█" * min(tot, 60)))
print()
print("  ★ 结论：%d 个有消息的日子" % len(byday))

print()
print("  --- 2025-11-08 那天的时段分布 ---")
h = Counter()
for r in rows:
    if d(r["ts"]) == "2025-11-08":
        h[datetime.datetime.fromtimestamp(r["ts"]).hour] += 1
for k in sorted(h): print("    %02d 时  %3d 条  %s" % (k, h[k], "▉" * h[k]))

print()
print("  --- 谁先开口 / 谁先结束 ---")
print("    首条 [%s] %s" % (f(rows[0]["ts"]), "我" if rows[0]["role"] == "me" else "她"))
print("    末条 [%s] %s : %s" % (f(rows[-1]["ts"]), "我" if rows[-1]["role"] == "me" else "她", (rows[-1]["content"] or "")[:80]))
print()
print("  --- 最后 12 条 ---")
for r in rows[-12:]:
    cc = (r["content"] or "").replace("\n", " ")
    if "<" in cc: cc = cc.split("<")[0].strip()[:80] or "〔媒体〕"
    print("    [%s] %-3s %s" % (f(r["ts"]), "我" if r["role"] == "me" else "她", cc[:150]))

print()
print("#" * 92); print("② 极狐事故模式（三次事故的上下文）"); print("#" * 92)
SEG = [("2026-06-25", "2026-07-06"), ("2026-07-15", "2026-07-20"),
       ("2026-08-18", "2026-08-22"), ("2026-09-07", "2026-09-10"),
       ("2026-09-24", "2026-09-27"), ("2026-10-06", "2026-10-08")]
SES = [("wxid_vk33qtlz3yyn22", "极狐售后"), ("wxid_1wa75s1kze3o22", "母亲"),
       ("45219356839@chatroom", "T5服务群"), ("wxid_wdnk6ue9kiyn22", "笑一")]
for a, b in SEG:
    t0 = int(datetime.datetime.strptime(a, "%Y-%m-%d").timestamp())
    t1 = int(datetime.datetime.strptime(b, "%Y-%m-%d").timestamp()) + 86400
    print("  ==== %s ~ %s ====" % (a, b))
    for sk, lab in SES:
        rr = con.execute("select ts, role, content from messages where session_key=? and ts>=? and ts<? order by ts", (sk, t0, t1)).fetchall()
        if not rr: continue
        for x in rr:
            cc = (x["content"] or "").replace("\n", " ")
            if "<" in cc: cc = cc.split("<")[0].strip()[:100] or "〔媒体〕"
            if len(cc) > 130: cc = cc[:130] + "…"
            if cc in ("〔媒体〕",) or len(cc) > 3:
                print("    [%s] %-8s %-4s %s" % (f(x["ts"]), lab, "我" if x["role"] == "me" else "他", cc))
    print()

print("#" * 92); print("③ 事故关键词全库（车相关）"); print("#" * 92)
for kw in ["剐蹭", "刮了", "又刮", "事故", "蹭了", "碰了", "追尾", "保险杠", "倒车"]:
    rr = con.execute("select session_key, ts, role, content from messages where content like ? order by ts", ("%" + kw + "%",)).fetchall()
    mine = [x for x in rr if x["role"] == "me"]
    print("  【%s】全库 %d 条 · 我发 %d 条" % (kw, len(rr), len(mine)))
    for x in mine[:14]:
        cc = (x["content"] or "").replace("\n", " ")[:120]
        print("     [%s] %-30s %s" % (f(x["ts"]), x["session_key"][:30], cc))
    print()
