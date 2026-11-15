# -*- coding: utf-8 -*-
"""买车钱路径 + 家教线专项（只读）"""
import sqlite3, time, os, collections, re

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
def fmt(ts): return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

sess = {}
for tk, dn, st in c.execute("select talker, display_name, session_type from sessions"):
    sess[tk] = (dn or tk, st or "")

L = []; W = L.append

# ============ A. 家教线：找出所有会话名含「家教 / 老师群 / 辅导 / 兼职」的 ============
W("=" * 100)
W("【A】家教 / 老师群 / 兼职 类会话")
W("=" * 100)
KW = ["家教", "老师群", "辅导", "兼职", "招聘", "代课", "助教"]
hits = []
for sk, (nm, st) in sess.items():
    if not any(k in nm for k in KW): continue
    n = list(c.execute("select count(*) from messages where session_key=?", (sk,)))[0][0]
    if n < 20: continue
    fl = list(c.execute("select min(ts), max(ts) from messages where session_key=?", (sk,)))[0]
    hits.append((n, nm, st, fl[0], fl[1], sk))
for n, nm, st, a, b, sk in sorted(hits, reverse=True)[:40]:
    W(f"   {n:>7} 条  {st:<4} {nm[:44]:<44} {fmt(a)[:10]} → {fmt(b)[:10]}")

# ============ B. 家教主会话：角色拆分 ============
W("")
W("=" * 100)
W("【B】家教主会话 · 角色结构 + 逐月 + 内容抽样")
W("=" * 100)
top = sorted(hits, reverse=True)[:3]
for n, nm, st, a, b, sk in top:
    W(f"\n{'─'*90}\n─── 【{nm}】{st} · {n} 条 · {fmt(a)[:10]} → {fmt(b)[:10]}")
    role_c = collections.Counter()
    mon = collections.Counter()
    for ts, role in c.execute("select ts, role from messages where session_key=?", (sk,)):
        role_c[role] += 1
        mon[fmt(ts)[:7]] += 1
    W(f"   role: {dict(role_c)}")
    W("   逐月: " + " ".join(f"{k}:{v}" for k, v in sorted(mon.items())))
    # 抽样：他发的
    W("   ── 他发的（首/中/末各 15 条）")
    me = [(ts, ct) for ts, role, ct in c.execute(
        "select ts, role, content from messages where session_key=? and role='me' order by ts", (sk,)) if ct]
    picks = me[:15] + me[len(me)//2:len(me)//2+15] + me[-15:]
    for ts, ct in picks:
        W(f"      {fmt(ts)[:16]}  {ct.replace(chr(10),' / ')[:120]}")
    W("   ── 对方发的（首 20 条）")
    th = [(ts, ct) for ts, role, ct in c.execute(
        "select ts, role, content from messages where session_key=? and role!='me' order by ts", (sk,)) if ct]
    for ts, ct in th[:20]:
        W(f"      {fmt(ts)[:16]}  {ct.replace(chr(10),' / ')[:120]}")

# ============ C. 买车钱：母亲会话两个关键窗口全量 ============
W("")
W("=" * 100)
W("【C】★ 母亲会话 · 买车窗口全量（2025-12-20 → 2026-01-10；2026-04-15 → 2026-05-30）")
W("=" * 100)
mom = [sk for sk, (nm, st) in sess.items() if nm == "刘丽萍"][0]
WINS = [("2025-12-20", "2026-01-10"), ("2026-04-15", "2026-05-30"), ("2026-07-01", "2026-07-10")]
for w0, w1 in WINS:
    t0 = time.mktime(time.strptime(w0, "%Y-%m-%d"))
    t1 = time.mktime(time.strptime(w1, "%Y-%m-%d"))
    W(f"\n{'─'*90}\n─── 窗口 {w0} → {w1}")
    for ts, role, ct in c.execute(
            "select ts, role, content from messages where session_key=? and ts>=? and ts<? order by ts",
            (mom, t0, t1)):
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct or ct.startswith("<") or "版本不支持" in ct: continue
        W(f"   {fmt(ts)}  {'我' if role=='me' else '妈'}  {ct[:150]}")

# ============ D. 他本人 filehelper 里的车/钱记录 ============
W("")
W("=" * 100)
W("【D】filehelper · 车 / 首付 / 贷款 / 保险 关键词")
W("=" * 100)
CAR2 = ["买车", "提车", "首付", "尾款", "极狐", "车款", "上牌", "指标", "保险", "贷款", "月供",
        "还款", "逾期", "征信", "车贷"]
for ts, role, ct in c.execute(
        "select ts, role, content from messages where session_key='filehelper' order by ts"):
    if not ct: continue
    for k in CAR2:
        if k in ct:
            W(f"   {fmt(ts)}  [{k}]  {ct.replace(chr(10),' / ')[:180]}")
            break

open(os.path.join(OUT, "car_money_jiajiao.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
