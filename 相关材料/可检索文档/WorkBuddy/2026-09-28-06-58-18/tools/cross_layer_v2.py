# -*- coding: utf-8 -*-
"""cross_layer_v2.py — 多层次交叉分析（只读）
层1 钱 / 层2 关系 / 层3 事件 / 层4 结构 / 层5 无人时
"""
import sqlite3, time, collections, statistics, os

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\cross_layer_v2.txt"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
def fmt(t): return time.strftime("%Y-%m-%d", time.localtime(t))
def ym(t): return time.strftime("%Y-%m", time.localtime(t))
NOW = time.time()

L = []; W = L.append
sess = {tk: (dn or tk, st or "", mc) for tk, dn, st, mc in
        c.execute("select talker,display_name,session_type,message_count from sessions")}

# ============ 层 4：结构 —— 我发占比全库分布 ============
W("=" * 96); W("【层 4 · 结构】我发占比：全库分布（私聊 ≥150 条）"); W("=" * 96)
rows = []
for tk, dn, st, mc in c.execute(
        "select talker,display_name,session_type,message_count from sessions "
        "where session_type='私聊' and message_count>=150"):
    d = dict(c.execute("select role,count(*) from messages where session_key=? group by role", (tk,)))
    me = d.get("me", 0)
    if me == 0:
        rows.append((mc, 0, dn)); continue
    last = list(c.execute("select max(ts) from messages where session_key=?", (tk,)))[0][0]
    rows.append((mc, me / mc, dn, int((NOW - last) / 86400)))
rows = [r for r in rows if r[1] > 0]
rows.sort(key=lambda x: -x[1])
pcts = [r[1] for r in rows]
W(f"样本 {len(rows)} 人（零发言者已剔除）")
W(f"我发占比：中位数 {statistics.median(pcts)*100:.1f}%  均值 {statistics.mean(pcts)*100:.1f}%  "
  f"最低 {min(pcts)*100:.1f}%  最高 {max(pcts)*100:.1f}%")
q = statistics.quantiles(pcts, n=4)
W(f"四分位：Q1 {q[0]*100:.1f}%  Q2 {q[1]*100:.1f}%  Q3 {q[2]*100:.1f}%")
W("")
W("★ 高我发占比 TOP15（他供给最多）")
for r in rows[:15]:
    W(f"   {r[1]*100:>5.1f}%  {r[0]:>5} 条  距今{r[3]:>4}天  {r[2][:34]}")
W("")
W("★ 低我发占比 BOTTOM15（对方供给更多）")
for r in rows[-15:]:
    W(f"   {r[1]*100:>5.1f}%  {r[0]:>5} 条  距今{r[3]:>4}天  {r[2][:34]}")
W("")
# 分桶
buckets = collections.Counter()
for p in pcts:
    buckets[f"{int(p*10)*10}-{int(p*10)*10+10}%"] += 1
W("分布：")
for k in sorted(buckets, key=lambda x: int(x.split("-")[0])):
    W(f"   {k:<8} {buckets[k]:>4} 人  {'█'*int(buckets[k]/2)}")

# ============ 层 1：钱 —— 2026-06 低谷构成 ============
W(""); W("=" * 96); W("【层 1 · 钱】2026-06 全库低谷（16,932）构成"); W("=" * 96)
for m in ["2026-04", "2026-05", "2026-06", "2026-07"]:
    t0 = time.mktime(time.strptime(m + "-01", "%Y-%m-%d"))
    t1 = t0 + 31 * 86400
    n = list(c.execute("select count(*) from messages where ts>=? and ts<?", (t0, t1)))[0][0]
    me = list(c.execute("select count(*) from messages where ts>=? and ts<? and role='me'", (t0, t1)))[0][0]
    W(f"   {m}  总 {n:>6}  他发 {me:>6} ({me/n*100:>4.1f}%)")

# ============ 层 2：关系 —— 母亲线 16,336 逐月 vs 旧结论 ============
W(""); W("=" * 96); W("【层 2 · 关系】母亲线（16,336 条 · 我发 45.4%）对旧结论的冲击"); W("=" * 96)
mom = [tk for tk, (dn, st, mc) in sess.items() if dn == "刘丽萍"][0]
mm = collections.Counter()
for ts, in c.execute("select ts from messages where session_key=?", (mom,)):
    mm[ym(ts)] += 1
W("  逐月：" + "  ".join(f"{k[2:]}:{v}" for k, v in sorted(mm.items())))
W("")
W("  ★ 旧结论：『母亲 142 条 ≠ 关系淡，因为同住，微信只承担事务通知』")
W(f"  ★ 实际：{sum(mm.values()):,} 条 —— 是旧快照的 {sum(mm.values())/142:.0f} 倍")
W("  ★ 修正：母亲不是『142 条事务通知』，是**全库第二大私聊**（仅次于家教群口径下的她本人）")

# ============ 层 3：事件 —— 车/家教/债务 三线时序交叉 ============
W(""); W("=" * 96); W("【层 3 · 事件】2026-05/06 三线同时转向"); W("=" * 96)
W("  2026-05-16  提车（首付 80,000 付出）")
W("  2026-06-12  陈昶文「待会儿那你信息借网贷」")
W("  2026-06     全库低谷 16,932（当月 -24%）+ 家教群断崖 1,235 → 366（-70%）")
W("")
# 家教群逐月
jj = [tk for tk, (dn, st, mc) in sess.items() if "家教老师群" in dn]
if jj:
    jm = collections.Counter()
    for ts, in c.execute("select ts from messages where session_key=?", (jj[0],)):
        jm[ym(ts)] += 1
    W("  家教群逐月：" + " ".join(f"{k[2:]}:{v}" for k, v in sorted(jm.items())))

# ============ 层 4b：零发言结构 ============
W(""); W("=" * 96); W("【层 4b · 结构】零发言会话 = 48% 的库"); W("=" * 96)
zero = []
for tk, (dn, st, mc) in sess.items():
    d = dict(c.execute("select role,count(*) from messages where session_key=? group by role", (tk,)))
    if d.get("me", 0) == 0:
        zero.append((mc, st, dn))
W(f"  零发言会话 {len(zero)} 个 · {sum(z[0] for z in zero):,} 条 = {sum(z[0] for z in zero)/388705*100:.1f}%")
bytype = collections.Counter()
for mc, st, dn in zero: bytype[st] += mc
W(f"  按类型条数：{dict(bytype)}")

open(os.path.dirname(OUT) + "/" + os.path.basename(OUT), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
