# -*- coding: utf-8 -*-
r"""probe18.py —— ★★★ 舒泽林全深度：逐月结构 / 我发占比 / 近 3 个月全文 / 话题 / 转账 / 与机器画像对账"""
import sqlite3, datetime, re
from collections import Counter, defaultdict
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
SK = "wxid_0ejd54z34nmv32"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")
def cl(c):
    if not c: return ""
    if "<" in c:
        h = c.split("<")[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else ("〔转账〕" if 'transfer' in c.lower() or '收到转账' in c else "〔卡片〕"))))
        return (h[:150] + " " + tag) if h else tag
    return c.replace("\n", " ")[:200]

rows = con.execute("select ts, role, content from messages where session_key=? order by ts", (SK,)).fetchall()
print("#" * 96)
print("① 舒泽林 · 总量与结构")
print("#" * 96)
me = sum(1 for r in rows if r["role"] == "me")
th = sum(1 for r in rows if r["role"] == "them")
print("  总 %d 条 · 我发 %d (%.0f%%) · 他发 %d (%.0f%%) · 窗口 %s ~ %s"
      % (len(rows), me, 100 * me / len(rows), th, 100 * th / len(rows), f(rows[0]["ts"])[:11], f(rows[-1]["ts"])[:11]))

print()
print("  逐月分布：")
mm = defaultdict(lambda: [0, 0])
for r in rows:
    k = f(r["ts"])[:5]
    mm[k][0 if r["role"] == "me" else 1] += 1
print("  %-8s %6s %6s %6s %7s" % ("月", "我发", "他发", "合计", "我占比"))
for k in sorted(mm):
    a, b = mm[k]
    tot = a + b
    print("  %-8s %6d %6d %6d %6.0f%%  %s" % (k, a, b, tot, 100 * a / tot, "█" * min(tot // 8, 60)))

print()
print("#" * 96)
print("② 近 3 个月全文（2026-07-01 → 现在）")
print("#" * 96)
t0 = int(datetime.datetime(2026, 7, 1).timestamp())
for r in rows:
    if r["ts"] >= t0:
        print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else "他", cl(r["content"])))

print()
print("#" * 96)
print("③ 他发的全部「长消息」（≥60 字）—— 看他在什么话题上会展开")
print("#" * 96)
n = 0
for r in rows:
    if r["role"] == "them" and r["content"] and len(r["content"]) >= 60 and "<" not in r["content"]:
        n += 1
        print("  [%s] %s" % (f(r["ts"]), r["content"].replace("\n", " ")[:230]))
print("  → 共 %d 条长消息" % n)

print()
print("#" * 96)
print("④ 我发的「长消息」（≥80 字）—— 看我在向他倾诉什么")
print("#" * 96)
n = 0
for r in rows:
    if r["role"] == "me" and r["content"] and len(r["content"]) >= 80 and "<" not in r["content"]:
        n += 1
        print("  [%s] %s" % (f(r["ts"]), r["content"].replace("\n", " ")[:230]))
print("  → 共 %d 条长消息" % n)

print()
print("#" * 96)
print("⑤ 话题关键词（全库该会话）")
print("#" * 96)
blob = "\n".join([(r["content"] or "") for r in rows])
for kw in ["谢谢", "感谢", "哥", "请教", "帮我", "麻烦", "钱", "借", "还", "转", "酒", "吃",
           "滑雪", "洗车", "局", "二爷", "面试", "工作", "单位", "装修", "钓鱼", "泡澡"]:
    print("    %-6s %4d 次" % (kw, blob.count(kw)))
