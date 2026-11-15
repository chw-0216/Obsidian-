# -*- coding: utf-8 -*-
"""两年全窗口事件挖掘（2024-11-10 → 2026-10-04）—— 单次全表扫描版"""
import sqlite3, os, io, datetime, collections

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
buf = io.StringIO()
def p(*a):
    buf.write(' '.join(str(x) for x in a) + "\n")

def ym(ts):
    return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m')

KW = ['考研', '考编', '事业编', '国考', '初试', '复试', '调剂',
      '央美', '研究生', '导师', '陈晔', '实验艺术',
      '格拉斯哥', '格拉', '毕业', '学位',
      '支教', '澜沧', '云南', '美育', '洞台', '井邻', '长城', '怀柔',
      '实习', '美术馆', '北京台', 'AIGC',
      '债务', '网贷', '还钱', '借钱', '信用卡',
      '笑一', '女朋友', '分手', '老公',
      '入党', '积极分子', '党员', '党课',
      '植墨', '丝网', '版画', '文化衫',
      '博士', '面试', 'offer', '简历', '何一沙']

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c = con.cursor()

name = {}
for t, n, st, mc in c.execute('select talker, display_name, session_type, message_count from sessions'):
    name[t] = (n or t, st, mc)
def nm(t):
    return name.get(t, (t, '?', 0))[0]

# ============ 单次全表扫描 ============
m_all = collections.Counter()
m_sess = collections.defaultdict(set)
ms = collections.defaultdict(collections.Counter)
kwmat = collections.defaultdict(collections.Counter)
tot = 0
for sk, ts, ct in c.execute('select session_key, ts, content from messages'):
    k = ym(ts)
    m_all[k] += 1
    m_sess[k].add(sk)
    ms[k][sk] += 1
    tot += 1
    if ct:
        for kw in KW:
            if kw in ct:
                kwmat[kw][k] += 1
print('scanned', tot)

# ---------- 1 ----------
p('=' * 92)
p('一、逐月总量')
p('=' * 92)
for k in sorted(m_all):
    p(f"  {k}  {m_all[k]:>7} 条  {len(m_sess[k]):>4} 会话  {'█'*max(1,m_all[k]//1200)}")

# ---------- 2 ----------
p('')
p('=' * 92)
p('二、逐月 TOP6 会话')
p('=' * 92)
for k in sorted(ms):
    p(f"  ── {k}")
    for sk, v in ms[k].most_common(6):
        p(f"      {v:>5}  {nm(sk)[:32]}")

# ---------- 3 ----------
first = collections.defaultdict(list); last = collections.defaultdict(list)
for t, f, l, mc in c.execute('select talker, first_ts, last_ts, message_count from sessions'):
    if f:
        first[ym(f)].append((mc, t, l))
    if l:
        last[ym(l)].append((mc, t, f))
p('')
p('=' * 92)
p('三、★ 每月「新出现」会话（消息量≥30）')
p('=' * 92)
for k in sorted(first):
    rs = sorted([r for r in first[k] if r[0] >= 30], reverse=True)
    if rs:
        p(f"  ── {k}（{len(rs)} 个）")
        for mc, t, l in rs[:12]:
            p(f"      {mc:>5} 条  {nm(t)[:32]}   最后={ym(l) if l else '?'}")
p('')
p('=' * 92)
p('四、★ 每月「最后活跃」会话（消息量≥50）')
p('=' * 92)
for k in sorted(last):
    rs = sorted([r for r in last[k] if r[0] >= 50], reverse=True)
    if rs:
        p(f"  ── {k}（{len(rs)} 个）")
        for mc, t, f in rs[:12]:
            p(f"      {mc:>5} 条  {nm(t)[:32]}   首={ym(f) if f else '?'}")

# ---------- 5 ----------
p('')
p('=' * 92)
p('五、★ 关键词 × 月份矩阵')
p('=' * 92)
months = sorted(m_all)
p('  ' + '关键词'.ljust(13) + ' '.join(m[-2:] for m in months))
for kw in KW:
    row = [kwmat[kw].get(m, 0) for m in months]
    if sum(row) == 0:
        continue
    p(f"  {kw:<13}" + ' '.join(f"{v:>3}" if v else '  ·' for v in row) + f"   Σ{sum(row)}")

con.close()
open(os.path.join(WS, '_tmp', 'two_years.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
