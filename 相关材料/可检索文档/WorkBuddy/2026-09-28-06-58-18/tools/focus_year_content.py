# -*- coding: utf-8 -*-
"""聚焦这一年（2025-10-01 → 2026-10-04）· 内容层挖掘（只读）
目标：不再数条数，而是看他「说了什么」「钱怎么走」「谁在索取」
"""
import sqlite3, time, os, collections, json

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)

T0 = int(time.mktime(time.strptime("2025-10-01", "%Y-%m-%d")))   # 最近 12 个月起点
def fmt(ts): return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
def ym(ts):  return time.strftime("%Y-%m", time.localtime(ts))

key2name = {}
for tk, dn in c.execute("select talker, display_name from sessions"):
    key2name[tk] = dn or tk

lines = []
W = lines.append

W("=" * 100)
W("【1】filehelper（文件传输助手）· 这一年他给自己写了什么")
W("=" * 100)
fh = list(c.execute("select talker from sessions where display_name='文件传输助手'"))
fh_key = fh[0][0] if fh else None
W(f"session_key = {fh_key}")
rows = list(c.execute("select ts, role, type, content from messages where session_key=? and ts>=? order by ts", (fh_key, T0)))
W(f"这一年共 {len(rows)} 条")
by_m = collections.Counter(ym(t) for t, r, ty, ct in rows)
W("逐月: " + " | ".join(f"{m}:{n}" for m, n in sorted(by_m.items())))
W("")

# 逐月抽样正文
for m in sorted(by_m):
    sub = [(t, ct) for t, r, ty, ct in rows if ym(t) == m and ct]
    txt = [ct.strip() for t, ct in sub if ct and len(ct.strip()) > 2
           and not ct.startswith("<") and "微信转账" not in ct and "版本不支持" not in ct]
    W(f"── {m}（{len(sub)} 条，可读正文 {len(txt)} 条）")
    for t, ct in sub:
        ct = (ct or "").strip().replace("\n", " / ")
        if not ct or ct.startswith("<") or "版本不支持" in ct: continue
        if len(ct) < 3: continue
        W(f"   {fmt(t)[5:]}  {ct[:180]}")
    W("")

W("")
W("=" * 100)
W("【2】这一年 · 金钱全量（含「借/还/钱/房租/工资/欠/贷/花呗/信用卡」）")
W("=" * 100)
MONEY = ["借钱", "还钱", "还你", "欠你", "房租", "工资", "发薪", "转账", "网贷", "贷款",
         "花呗", "信用卡", "分期", "利息", "还款", "收款码", "打款", "结账", "报销", "学费", "定金"]
mrows = []
for sk, ts, role, ct in c.execute("select session_key, ts, role, content from messages where ts>=?", (T0,)):
    if not ct: continue
    for kw in MONEY:
        if kw in ct:
            mrows.append((ts, sk, role, kw, ct))
            break
W(f"命中 {len(mrows)} 条")
by_kw = collections.Counter(r[3] for r in mrows)
W("关键词分布: " + " | ".join(f"{k}:{v}" for k, v in by_kw.most_common()))
W("")
# 排除公众号（无 role 或 session 是 gh_）
real = [r for r in mrows if r[1] in key2name and not str(r[1]).startswith("gh_")]
W(f"其中真人/群会话 {len(real)} 条 —— 按会话聚合 TOP25：")
agg = collections.Counter()
for ts, sk, role, kw, ct in real:
    agg[key2name.get(sk, sk)] += 1
for nm, n in agg.most_common(25):
    W(f"   {n:>4}  {nm}")
W("")
W("── 真人会话里的原文（按时间，最多 120 条）")
for ts, sk, role, kw, ct in real[:120]:
    W(f"   {fmt(ts)}  [{key2name.get(sk,sk)[:16]:<16}] {'我' if role=='me' else '对方'}  {(ct or '').strip()[:130]}")

open(os.path.join(OUT, "focus_year_content.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok", len(lines))
