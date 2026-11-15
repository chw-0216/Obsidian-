# -*- coding: utf-8 -*-
"""
cross_payment_events.py —— 支付流 × 事件库 深度交叉（只读）

做四件事：
  A. 高支出日 × 当天事件（钱动了，那天还发生了什么）
  B. 高负荷事件日 × 当天支出（出事了，那天花了多少）
  C. 「双高日」—— 支出与事件同时高
  D. 逐月三线对齐（支出 / 事件数 / 高负荷事件）
  E. 关键窗口逐日深挖（2025-03 / 2025-10 / 2026-05 / 2026-08 / 2026-09）

输出：
  _tmp/payment_event_cross.txt
  _tmp/payment_event_daily.csv   逐日合并表
"""
import csv, io, os
from collections import defaultdict, Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
PAY = os.path.join(WS, "_tmp", "payment_flow.csv")
EVT = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\事件库.csv"
OUT = os.path.join(WS, "_tmp")
os.makedirs(OUT, exist_ok=True)

# ---------- 读支付流 ----------
pay_day_amt = defaultdict(float)
pay_day_n = defaultdict(int)
pay_day_items = defaultdict(list)
with io.open(PAY, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        d = r["时间"][:10]
        pay_day_n[d] += 1
        if r["方向"] == "支出" and r["金额"]:
            v = float(r["金额"])
            pay_day_amt[d] += v
            pay_day_items[d].append((v, r["来源"], r["原文"][:70]))

# ---------- 读事件库 ----------
evt_day = defaultdict(list)
with io.open(EVT, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        d = (r["日期"] or "").strip()
        if len(d) == 10:
            evt_day[d].append(r)

# ---------- 逐日合并 ----------
all_days = sorted(set(pay_day_amt) | set(pay_day_n) | set(evt_day))
rows = []
for d in all_days:
    evs = evt_day.get(d, [])
    load = sum(int(e["负荷分"] or 0) for e in evs)
    rows.append({
        "日期": d,
        "支出": round(pay_day_amt.get(d, 0), 2),
        "支付条数": pay_day_n.get(d, 0),
        "事件数": len(evs),
        "负荷分": load,
        "高负荷事件": sum(1 for e in evs if e["情感负荷"] == "高"),
    })

# 只统计有支付流数据的区间（2025-08 起）
win = [r for r in rows if r["日期"] >= "2025-08-01"]

L = []
W = L.append
W("支付流 × 事件库 深度交叉（只读）")
W("=" * 78)
W("支付流区间: %s → %s（%d 天有数据）" % (win[0]["日期"], win[-1]["日期"], len(win)))
W("事件库区间: %s → %s" % (min(evt_day), max(evt_day)))
W("")

# ---------- A. 高支出日 ----------
W("=" * 78)
W("A. 高支出日 TOP25 × 当天事件")
W("=" * 78)
for r in sorted(win, key=lambda x: -x["支出"])[:25]:
    d = r["日期"]
    W("\n[%s]  支出 ¥%s（%d 笔）  事件 %d 条 · 负荷 %d" %
      (d, format(r["支出"], ",.2f"), r["支付条数"], r["事件数"], r["负荷分"]))
    for v, src, txt in sorted(pay_day_items.get(d, []), reverse=True)[:3]:
        W("     ¥%-10s %-8s %s" % (format(v, ",.2f"), src, txt))
    for e in evt_day.get(d, [])[:6]:
        W("     · [%s][%s] %s" % (e["距离半径"], e["对话人"][:14], (e["事件"] or "")[:86]))

# ---------- B. 高负荷事件日 ----------
W("\n" + "=" * 78)
W("B. 高负荷事件日 TOP25 × 当天支出")
W("=" * 78)
for r in sorted(win, key=lambda x: -x["负荷分"])[:25]:
    d = r["日期"]
    if r["负荷分"] == 0:
        break
    W("\n[%s]  负荷 %d  事件 %d 条  支出 ¥%s（%d 笔）" %
      (d, r["负荷分"], r["事件数"], format(r["支出"], ",.2f"), r["支付条数"]))
    for e in sorted(evt_day.get(d, []), key=lambda x: -int(x["负荷分"] or 0))[:4]:
        W("     · [%s][%s] %s" % (e["距离半径"], e["对话人"][:14], (e["事件"] or "")[:86]))

# ---------- C. 双高日 ----------
W("\n" + "=" * 78)
W("C. ★「双高日」—— 支出 ≥ ¥300 且 事件 ≥ 3 条（钱与事同时发生）")
W("=" * 78)
for r in sorted(win, key=lambda x: -x["支出"]):
    if r["支出"] >= 300 and r["事件数"] >= 3:
        d = r["日期"]
        W("\n[%s]  支出 ¥%s  事件 %d 条 · 负荷 %d" %
          (d, format(r["支出"], ",.2f"), r["事件数"], r["负荷分"]))
        for v, src, txt in sorted(pay_day_items.get(d, []), reverse=True)[:2]:
            W("     ¥%-10s %-8s %s" % (format(v, ",.2f"), src, txt))
        for e in sorted(evt_day.get(d, []), key=lambda x: -int(x["负荷分"] or 0))[:4]:
            W("     · [%s][%s] %s" % (e["距离半径"], e["对话人"][:14], (e["事件"] or "")[:84]))

# ---------- D. 逐月三线 ----------
W("\n" + "=" * 78)
W("D. 逐月三线对齐（支出 / 事件数 / 高负荷事件）")
W("=" * 78)
W("%-9s %12s %10s %8s %10s" % ("月份", "支出", "事件数", "高负荷", "负荷分"))
m_amt = defaultdict(float); m_evt = defaultdict(int); m_hi = defaultdict(int); m_load = defaultdict(int)
for r in win:
    m = r["日期"][:7]
    m_amt[m] += r["支出"]; m_evt[m] += r["事件数"]
    m_hi[m] += r["高负荷事件"]; m_load[m] += r["负荷分"]
for m in sorted(set(m_amt) | set(m_evt)):
    W("%-9s %12s %10d %8d %10d" % (m, format(m_amt[m], ",.2f"), m_evt[m], m_hi[m], m_load[m]))

# ---------- E. 关键窗口 ----------
W("\n" + "=" * 78)
W("E. 关键窗口逐日深挖")
W("=" * 78)
WINDOWS = [
    ("2025-03-08", "2025-03-28", "父亲开胸手术 + 债务线起点"),
    ("2025-09-15", "2025-10-05", "2025-10 大额月"),
    ("2026-05-01", "2026-05-20", "提车 + 借网贷"),
    ("2026-08-20", "2026-09-01", "央美学费 ¥20,000"),
    ("2026-09-01", "2026-09-12", "云南行"),
]
for a, b, title in WINDOWS:
    W("\n--- 【%s】%s ~ %s ---" % (title, a, b))
    for r in win:
        if a <= r["日期"] <= b and (r["支出"] > 0 or r["事件数"] > 0):
            W("  %s  支出 ¥%-9s 事件 %2d  负荷 %3d" %
              (r["日期"], format(r["支出"], ",.2f"), r["事件数"], r["负荷分"]))
            for e in sorted(evt_day.get(r["日期"], []), key=lambda x: -int(x["负荷分"] or 0))[:2]:
                W("        · [%s][%s] %s" % (e["距离半径"], e["对话人"][:14], (e["事件"] or "")[:80]))

# ---------- 写文件 ----------
io.open(os.path.join(OUT, "payment_event_cross.txt"), "w", encoding="utf-8").write("\n".join(L))
with io.open(os.path.join(OUT, "payment_event_daily.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["日期", "支出", "支付条数", "事件数", "负荷分", "高负荷事件"])
    w.writeheader()
    for r in rows:
        if r["日期"] >= "2025-08-01":
            w.writerow(r)

print("\n".join(L[:70]))
print("\n... 共 %d 行 → _tmp/payment_event_cross.txt" % len(L))
