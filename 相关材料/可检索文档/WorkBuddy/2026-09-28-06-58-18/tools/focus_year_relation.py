# -*- coding: utf-8 -*-
"""第二轮 · 关系结构层（只读）
- 这一年「我发占比」（谁在索取他 / 他单向供给）
- 这一年首次出现的真人
- 笑一 / 导师线 / 母亲线 内容抽样
- 「老公 / 宝 / 乖」称呼分布
"""
import sqlite3, time, os, collections

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)

T0 = int(time.mktime(time.strptime("2025-10-01", "%Y-%m-%d")))
def fmt(ts): return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

sess = {}
for tk, dn, st, mc in c.execute("select talker, display_name, session_type, message_count from sessions"):
    sess[tk] = (dn or tk, st or "", mc or 0)

L = []; W = L.append

W("=" * 100)
W("【A】这一年 · 私聊「我发占比」（谁在索取他）")
W("=" * 100)
agg = collections.defaultdict(lambda: [0, 0])   # sk -> [me, them]
for sk, role in c.execute("select session_key, role from messages where ts>=?", (T0,)):
    if sk not in sess: continue
    nm, st, mc = sess[sk]
    if st != "私聊": continue
    a = agg[sk]
    if role == "me": a[0] += 1
    else: a[1] += 1

rows = []
for sk, (me, them) in agg.items():
    tot = me + them
    if tot < 60: continue
    rows.append((tot, me, them, me / tot, sess[sk][0]))
rows.sort(key=lambda r: -r[3])
W(f"共 {len(rows)} 个私聊会话（≥60 条）")
W("")
W("── 他「单向供给」最严重（我发占比最高，TOP30）")
W("   {:<4} {:<6} {:<6} {:<7} {}".format("总", "我", "对方", "我占比", "会话"))
for tot, me, them, r, nm in rows[:30]:
    W("   {:<4} {:<6} {:<6} {:<7} {}".format(tot, me, them, f"{r*100:.0f}%", nm))
W("")
W("── 他「被动接收」最多（我发占比最低，TOP15）")
for tot, me, them, r, nm in sorted(rows, key=lambda x: x[3])[:15]:
    W("   {:<4} {:<6} {:<6} {:<7} {}".format(tot, me, them, f"{r*100:.0f}%", nm))
W("")
W("── 高体量关系（≥1000 条）的我发占比")
for tot, me, them, r, nm in sorted(rows, key=lambda x: -x[0])[:25]:
    W("   {:<6} {:<7} {}  (我 {} / 对方 {})".format(tot, f"{r*100:.0f}%", nm, me, them))

W("")
W("=" * 100)
W("【B】这一年「首次出现」的真人会话（第一条消息 ≥ 2025-10-01，且不是公众号）")
W("=" * 100)
firsts = []
for sk, ts in c.execute("select session_key, min(ts) from messages group by session_key"):
    if sk not in sess: continue
    if ts < T0: continue
    nm, st, mc = sess[sk]
    if str(sk).startswith("gh_") or "@chatroom" in str(sk): continue
    if mc < 30: continue
    firsts.append((ts, mc, st, nm))
firsts.sort()
W(f"共 {len(firsts)} 个（≥30 条）")
for ts, mc, st, nm in firsts:
    W("   {}  {:>5} 条  {:<5} {}".format(fmt(ts)[:16], mc, st, nm))

W("")
W("=" * 100)
W("【C】称呼分布（这一年）· 「老公 / 宝 / 乖 / 想」出现在哪些会话")
W("=" * 100)
PAT = {"老公": "老公", "宝": "宝", "乖": "乖", "想你了": "想你了", "男朋友": "男朋友", "女朋友": "女朋友"}
hit = collections.defaultdict(collections.Counter)
for sk, ct in c.execute("select session_key, content from messages where ts>=?", (T0,)):
    if not ct or sk not in sess: continue
    for k, kw in PAT.items():
        if kw in ct: hit[k][sess[sk][0]] += 1
for k in PAT:
    top = hit[k].most_common(8)
    W(f"  【{k}】" + " | ".join(f"{nm}:{n}" for nm, n in top))

W("")
W("=" * 100)
W("【D】笑一 · 这一年逐月 + 内容抽样（最早 60 条）")
W("=" * 100)
xy = [sk for sk, (nm, st, mc) in sess.items() if nm == "笑一"]
if xy:
    sk = xy[0]
    bym = collections.Counter()
    rows2 = []
    for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? and ts>=? order by ts", (sk, T0)):
        bym[time.strftime("%Y-%m", time.localtime(ts))] += 1
        rows2.append((ts, role, ct))
    W("逐月: " + " | ".join(f"{m}:{n}" for m, n in sorted(bym.items())))
    W("")
    W("── 最早 60 条原文")
    for ts, role, ct in rows2[:60]:
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct or ct.startswith("<") or "版本不支持" in ct: continue
        W("   {}  {}  {}".format(fmt(ts)[5:16], "我" if role == "me" else "她", ct[:150]))

W("")
W("=" * 100)
W("【E】导师线 · 这一年内容抽样（2026 年，最早 50 条）")
W("=" * 100)
ds = [sk for sk, (nm, st, mc) in sess.items() if nm and nm.startswith("导！急速回")]
if ds:
    sk = ds[0]
    T1 = int(time.mktime(time.strptime("2026-01-01", "%Y-%m-%d")))
    n = 0
    for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? and ts>=? order by ts", (sk, T1)):
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct or ct.startswith("<") or "版本不支持" in ct: continue
        W("   {}  {}  {}".format(fmt(ts)[:16], "我" if role == "me" else "师", ct[:150]))
        n += 1
        if n >= 50: break

W("")
W("=" * 100)
W("【F】母亲线 · 这一年 转账/金额 相关原文")
W("=" * 100)
mom = [sk for sk, (nm, st, mc) in sess.items() if nm == "刘丽萍" and st == "私聊"]
if mom:
    sk = mom[0]
    n = 0
    for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? and ts>=? order by ts", (sk, T0)):
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct: continue
        if any(k in ct for k in ["转账", "还钱", "借钱", "钱", "工资", "房租", "医院", "病"]):
            W("   {}  {}  {}".format(fmt(ts)[:16], "我" if role == "me" else "妈", ct[:150]))
            n += 1
            if n >= 60: break

open(os.path.join(OUT, "focus_year_relation.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
