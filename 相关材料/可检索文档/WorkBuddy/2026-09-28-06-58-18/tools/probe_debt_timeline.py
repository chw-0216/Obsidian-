# -*- coding: utf-8 -*-
"""债务时间线 · 精确逐月（只读）"""
import sqlite3, time, collections

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
def ym(ts): return time.strftime("%Y-%m", time.localtime(ts))

sess = {}
for tk, dn, st in c.execute("select talker, display_name, session_type from sessions"):
    sess[tk] = (dn or tk, st or "")

print("=" * 96)
print("A. 母亲（刘丽萍）· 逐月「转账」笔数 + 金额合计（全窗口）")
print("=" * 96)
mom = [sk for sk, (nm, st) in sess.items() if nm == "刘丽萍" and st == "私聊"][0]
import re
by_m = collections.defaultdict(lambda: [0, 0.0])
for ts, ct in c.execute("select ts, content from messages where session_key=?", (mom,)):
    if ct and "微信转账" in ct:
        m = re.search(r"转账(?:￥)?([\d.]+)", ct)
        by_m[ym(ts)][0] += 1
        if m: by_m[ym(ts)][1] += float(m.group(1))
tot_n = tot_a = 0
for k in sorted(by_m):
    n, a = by_m[k]
    tot_n += n; tot_a += a
    print(f"   {k}   {n:>3} 笔   合计 {a:>10.2f} 元")
print(f"   ── 全窗口合计 {tot_n} 笔 / {tot_a:.2f} 元")

print()
print("=" * 96)
print("B. 债务关键词 · 逐月（全库，排除公众号）")
print("=" * 96)
KW = ["借钱", "欠钱", "欠了", "还钱", "还你", "贷款", "逾期", "网贷", "催收", "花呗",
      "信用卡", "分期", "借条", "还款", "房租", "利息", "欠款", "债"]
mat = collections.defaultdict(collections.Counter)
detail = collections.defaultdict(list)
for sk, ts, role, ct in c.execute("select session_key, ts, role, content from messages"):
    if not ct or sk not in sess: continue
    if str(sk).startswith("gh_"): continue
    for kw in KW:
        if kw in ct:
            m = ym(ts)
            mat[m][kw] += 1
            if role == "me" and len(detail[m]) < 6 and kw in ("借钱", "欠钱", "欠了", "还钱", "还你", "逾期", "网贷", "贷款", "借条"):
                detail[m].append((time.strftime("%m-%d %H:%M", time.localtime(ts)), sess[sk][0][:14], ct.strip()[:110]))
            break

print("   月份     " + " ".join(f"{k:>5}" for k in KW[:9]) + "   Σ")
for m in sorted(mat):
    row = " ".join(f"{mat[m].get(k,0):>5}" for k in KW[:9])
    print(f"   {m}  {row}   {sum(mat[m].values()):>4}")

print()
print("=" * 96)
print("C. 「他本人发出」的债务类原文（按月，最有信息量）")
print("=" * 96)
for m in sorted(detail):
    if not detail[m]: continue
    print(f"\n   ── {m}")
    for t, nm, txt in detail[m]:
        print(f"      {t}  [{nm}]  {txt}")

print()
print("=" * 96)
print("D. 全库「催收 / 逾期」类系统短信（filehelper 与私聊）")
print("=" * 96)
for sk, ts, role, ct in c.execute("select session_key, ts, role, content from messages"):
    if not ct: continue
    if any(k in ct for k in ["逾期", "催收", "征信", "失信", "法务", "还款提醒", "欠款", "违约"]):
        if sess.get(sk, ("", ""))[1] != "私聊" and sk != "filehelper": continue
        print(f"   {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}  [{sess.get(sk,('filehelper',''))[0][:12]}]  {ct.strip()[:160]}")
print()
print("ok")
