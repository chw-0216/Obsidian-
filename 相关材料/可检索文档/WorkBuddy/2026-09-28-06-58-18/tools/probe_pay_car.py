# -*- coding: utf-8 -*-
"""支付/消费记录倒推 + 极狐（车）线（只读）"""
import sqlite3, time, os, collections, re

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
def fmt(ts): return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

sess = {}
for tk, dn, st in c.execute("select talker, display_name, session_type from sessions"):
    sess[tk] = (dn or tk, st or "")

L = []; W = L.append

W("=" * 100)
W("【1】所有会话名里含「支付 / 服务通知 / 银行 / 极狐 / 车 / 保险」的")
W("=" * 100)
KW_SESS = ["微信支付", "服务通知", "银行", "极狐", "车", "保险", "充电", "加油站", "中石化", "中石油",
           "ETC", "停车", "洗车", "贴膜", "违章", "交管", "滴滴", "高德", "曹操", "美团"]
hits = [(nm, st, sk) for sk, (nm, st) in sess.items() if any(k in nm for k in KW_SESS)]
seen = set()
for nm, st, sk in sorted(hits, key=lambda x: x[0]):
    if nm in seen: continue
    seen.add(nm)
    n = list(c.execute("select count(*) from messages where session_key=?", (sk,)))[0][0]
    if n < 5: continue
    fl = list(c.execute("select min(ts), max(ts) from messages where session_key=?", (sk,)))[0]
    W(f"   {n:>6} 条  {st:<4} {nm[:38]:<38} {fmt(fl[0])[:10]} → {fmt(fl[1])[:10]}")

W("")
W("=" * 100)
W("【2】★ 极狐（车）线 · 全量内容")
W("=" * 100)
for sk, (nm, st) in sess.items():
    if "极狐" not in nm: continue
    W(f"\n─── 【{nm}】{st}")
    n = 0
    for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? order by ts", (sk,)):
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct or ct.startswith("<") or "版本不支持" in ct: continue
        W(f"   {fmt(ts)}  {'我' if role=='me' else '对方'}  {ct[:170]}")
        n += 1
        if n >= 90: 
            W("   …（截断）"); break

W("")
W("=" * 100)
W("【3】★ 与「车」相关的关键词命中（全库真人会话，排除公众号）")
W("=" * 100)
CAR = ["买车", "提车", "上牌", "车牌", "行驶证", "购车", "车款", "首付", "极狐", "T5",
       "保险", "交强险", "商业险", "驾意", "4S", "保养", "年检", "摇号", "指标", "二手车",
       "违章", "驾照", "扣分", "罚款", "充电桩", "充电"]
mat = collections.defaultdict(list)
for sk, ts, role, ct in c.execute("select session_key, ts, role, content from messages"):
    if not ct or sk not in sess: continue
    if str(sk).startswith("gh_") or "@chatroom" in str(sk): continue
    for k in CAR:
        if k in ct:
            mat[k].append((ts, sess[sk][0], role, ct.strip()[:150]))
            break
for k in CAR:
    if k not in mat: continue
    W(f"\n── 【{k}】命中 {len(mat[k])} 条（最早 {fmt(mat[k][0][0])[:10]}）")
    for ts, nm, role, ct in mat[k][:12]:
        W(f"   {fmt(ts)[:16]}  [{nm[:14]}]  {'我' if role=='me' else '对'}  {ct}")

W("")
W("=" * 100)
W("【4】★ 母亲转账 · 大额笔（≥2000 元）逐笔")
W("=" * 100)
cands = [sk for sk, (nm, st) in sess.items() if "刘丽萍" in nm and st == "私聊"]
if not cands:
    cands = [sk for sk, (nm, st) in sess.items() if nm == "刘丽萍"]
if not cands:
    cands = [sk for sk, (nm, st) in sess.items() if "妈妈" in nm or "妈" == nm]
W(f"母亲会话候选：{[(sess[s][0], sess[s][1]) for s in cands][:5]}")
mom = cands[0] if cands else None
big = []
if mom:
  for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? order by ts", (mom,)):
    if ct and "微信转账" in ct:
        m = re.search(r"转账(?:￥)?([\d.]+)", ct)
        if m and float(m.group(1)) >= 2000:
            big.append((ts, role, float(m.group(1))))
W(f"共 {len(big)} 笔 ≥2000 元")
for ts, role, v in big:
    W(f"   {fmt(ts)}  {'我' if role=='me' else '妈'}  {v:>10.2f}")

W("")
W("=" * 100)
W("【5】微信支付 / 服务通知 · 内容（消费记录倒推）")
W("=" * 100)
for name in ["微信支付", "服务通知"]:
    ks = [sk for sk, (nm, st) in sess.items() if nm == name]
    if not ks: continue
    sk = ks[0]
    W(f"\n─── 【{name}】")
    n = 0
    for ts, role, ct in c.execute("select ts, role, content from messages where session_key=? order by ts desc", (sk,)):
        ct = (ct or "").replace("\n", " / ").strip()
        if not ct: continue
        W(f"   {fmt(ts)[:16]}  {ct[:160]}")
        n += 1
        if n >= 60: break

open(os.path.join(OUT, "focus_year_pay.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
