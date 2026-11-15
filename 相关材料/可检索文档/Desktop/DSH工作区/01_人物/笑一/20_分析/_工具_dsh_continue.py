# -*- coding: utf-8 -*-
"""
DSH 工作区延续分析 v4
沿用 W-PRISM 框架 + 追加 8/17-8/31 增量
数据: 3852 条 (2026-05-08 ~ 2026-08-31)
"""
import json, sys, io, re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC_FULL = r"C:/Users/wardc/Desktop/DSH工作区/01_人物/笑一/10_数据/笑一-聊天记录.json"
SRC_OLD  = r"C:/Users/wardc/Documents/ChatArchive/00_raw/2026/笑一聊天记录_20260815/笑一-聊天记录.json"

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

full = load(SRC_FULL)
old  = load(SRC_OLD)
msgs = sorted(full['messages'], key=lambda m: m['createTime'])
MY = full['myWxid']
def is_me(m): return m['senderUsername'] == MY
def dt(m): return datetime.fromtimestamp(m['createTime'])

# ---------- 称呼字典 (来自你的速查卡) ----------
CALL = {
    '老公': '安全感充足 ✅',
    '好老公': '现实轨确认 ✅',
    '宝贝': '照顾者模式 ⚠️',
    '宝宝': '心疼你/Fawn激活 ⚠️',
}
CALL_WORDS = list(CALL.keys()) + ['亲爱的','宝']

def count_calls(text):
    r = {}
    for w in CALL_WORDS:
        c = text.count(w)
        if c: r[w] = c
    return r

# ---------- 核心指标(全量) ----------
n = len(msgs)
me = [m for m in msgs if is_me(m)]
her = [m for m in msgs if not is_me(m)]
n_me, n_her = len(me), len(her)
c_me = sum(len(m.get('content') or '') for m in me)
c_her = sum(len(m.get('content') or '') for m in her)

print("="*80)
print(f"【DSH 延续分析】{full['displayName']}  {dt(msgs[0]).strftime('%Y-%m-%d')} ~ {dt(msgs[-1]).strftime('%Y-%m-%d')}")
print(f"总计 {n} 条（旧档 2880 → 新增 {n - 2880} 条）")
print("="*80)

print("\n■ 1. 总量对比")
print(f"  我: {n_me} 条 / {c_me} 字 (均 {c_me/n_me:.1f})")
print(f"  她: {n_her} 条 / {c_her} 字 (均 {c_her/n_her:.1f})")
print(f"  条数比 {n_me/n_her:.2f} : 1   字数比 {c_me/c_her:.2f} : 1")
print(f"  → 旧档字数比 3.43:1  →  现在 {c_me/c_her:.2f}:1")

# ---------- 8/17-8/31 增量段专项 ----------
SEG_A = datetime(2026,8,17); SEG_B = datetime(2026,9,1)
seg = [m for m in msgs if SEG_A <= dt(m) < SEG_B]
s_me = [m for m in seg if is_me(m)]; s_her = [m for m in seg if not is_me(m)]
sc_me = sum(len(m.get('content') or '') for m in s_me)
sc_her = sum(len(m.get('content') or '') for m in s_her)

print("\n■ 2. 增量段 8/17-8/31（15天，旧档没有的新数据）")
print(f"  总 {len(seg)} 条，日均 {len(seg)/15:.1f}")
print(f"  我: {len(s_me)} 条 / {sc_me} 字 (均 {sc_me/max(len(s_me),1):.1f})")
print(f"  她: {len(s_her)} 条 / {sc_her} 字 (均 {sc_her/max(len(s_her),1):.1f})")
print(f"  字数比 {sc_me/max(sc_her,1):.2f} : 1")
print(f"  → 对比全量 {c_me/c_her:.2f}:1，增量段{'改善' if sc_me/max(sc_her,1) < c_me/c_her else '恶化'}")

# ---------- 称呼字典分析 ----------
print("\n■ 3. 称呼字典分析（你的速查卡框架）")
def call_stat(ms, label):
    cnt = Counter()
    for m in ms:
        for w, c in count_calls(m.get('content') or '').items():
            cnt[w] += c
    total = sum(cnt.values())
    print(f"\n  {label}（共 {total} 次）")
    for w, c in cnt.most_common():
        tag = CALL.get(w, '')
        print(f"    {w:6s} {c:4d}  {tag}")
    return cnt

cm = call_stat(me, '我发出的称呼')
ch = call_stat(her, '她发出的称呼')

# 她称呼的时段演变
print("\n  她称呼的时间演变（按月）:")
for mo in ['2026-05','2026-06','2026-07','2026-08']:
    mm = [m for m in her if dt(m).strftime('%Y-%m') == mo]
    if not mm: continue
    cnt = Counter()
    for m in mm:
        for w, c in count_calls(m.get('content') or '').items():
            cnt[w] += c
    tot = sum(cnt.values())
    detail = "  ".join(f"{w}:{c}" for w, c in cnt.most_common(4))
    print(f"    {mo}: {len(mm):4d}条, 称呼{tot:3d}次  |  {detail}")

# ---------- 响应延迟 / 主动发起 ----------
def delays():
    md, hd = [], []
    ps, pt = None, None
    for m in msgs:
        mme = is_me(m)
        if ps is not None and ps != mme:
            g = m['createTime'] - pt
            if 0 < g < 43200:
                (md if mme else hd).append(g)
        ps, pt = mme, m['createTime']
    return md, hd
md, hd = delays()
def med(x):
    if not x: return 0
    s = sorted(x); k = len(s)
    return round(s[k//2] if k%2 else (s[k//2-1]+s[k//2])/2, 1)

print("\n■ 4. 响应延迟（秒）")
print(f"  我响应她: 中位 {med(md)}s / 均 {sum(md)/len(md):.0f}s  (n={len(md)})")
print(f"  她响应我: 中位 {med(hd)}s / 均 {sum(hd)/len(hd):.0f}s  (n={len(hd)})")

# 主动发起
def init():
    a = b = 0; pt = None
    for m in msgs:
        if pt is None or (m['createTime'] - pt) > 3600:
            if is_me(m): a += 1
            else: b += 1
        pt = m['createTime']
    return a, b
ia, ib = init()
print(f"\n■ 5. 主动发起（1小时空档后）")
print(f"  我 {ia} 次 vs 她 {ib} 次（我占比 {ia/(ia+ib):.2f}）")

# 8/17后的主动发起
ia2 = ib2 = 0; pt = None
for m in seg:
    if pt is None or (m['createTime'] - pt) > 3600:
        if is_me(m): ia2 += 1
        else: ib2 += 1
    pt = m['createTime']
print(f"  增量段: 我 {ia2} vs 她 {ib2}（我占比 {ia2/max(ia2+ib2,1):.2f}）")

# ---------- 沉默期 ----------
print("\n■ 6. 沉默期 > 24h")
prev = None
for m in msgs:
    if prev is not None:
        g = m['createTime'] - prev['createTime']
        if g > 86400:
            print(f"  {g/3600:6.1f}h  {dt(prev).strftime('%m-%d %H:%M')} → {dt(m).strftime('%m-%d %H:%M')}  打破者: {'我' if is_me(m) else '她'}")
    prev = m

# ---------- 三态 / 感官词 (私密空间指标) ----------
print("\n■ 7. 私密/情感强度词频（三态信号）")
SENSE = ['想你','喜欢','爱你','贴','抱','亲','摸','舒服','想要','停下','不要','轻点','慢','疼']
for label, data in [('我', me), ('她', her)]:
    cnt = Counter()
    for m in data:
        c = m.get('content') or ''
        for w in SENSE:
            cnt[w] += c.count(w)
    print(f"  {label}: " + "  ".join(f"{w}:{cnt[w]}" for w in SENSE if cnt[w]))

# ---------- 每日趋势(8月) ----------
print("\n■ 8. 8月逐日（旧档截止8/16，新增8/17-8/31）")
daily = defaultdict(lambda: {'me':0,'her':0,'mc':0,'hc':0})
for m in msgs:
    d = dt(m).strftime('%m-%d')
    if not d.startswith('08'): continue
    if is_me(m): daily[d]['me']+=1; daily[d]['mc']+=len(m.get('content') or '')
    else: daily[d]['her']+=1; daily[d]['hc']+=len(m.get('content') or '')
for d in sorted(daily):
    v = daily[d]
    mark = " ← 新增" if d >= '08-17' else ""
    print(f"  {d} | 我{v['me']:4d}条/{v['mc']:5d}字 | 她{v['her']:4d}条/{v['hc']:5d}字{mark}")

# ---------- 最后对话 ----------
print("\n■ 9. 最后 20 条（当前状态）")
for m in msgs[-20:]:
    who = "我" if is_me(m) else "她"
    print(f"  {dt(m).strftime('%m-%d %H:%M')} {who} | {(m.get('content') or '').replace(chr(10),' ')[:55]}")
