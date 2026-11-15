# -*- coding: utf-8 -*-
"""
渠道场景逆推：私聊的人 ↔ 共同群
================================================================
思路：
  群聊消息的 sender 是 wxid → 可与私聊 talker 直接匹配
  → 得出「这个私聊对象，和我在哪些共同群里」
  → 群名本身 = 场景（如「北京家教信息」「四周内尽力恢复年纪前十」）
  → 再叠加「加好友时间」，判断「是在哪件事上认识的」

⚠️ 局限：只能查到「在群里发过言」的人。查不到 ≠ 不是群里加的。
输出：_tmp/group_channel.txt
"""
import sqlite3, csv, os, sys, re, io, collections
from datetime import datetime

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
CONTACTS = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
            r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
            r'\contacts_2026-07-23T20-56-25.csv')
OUT = os.path.join(WS, '_tmp', 'group_channel.txt')

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
cur = con.cursor()
NOW = datetime.now().timestamp()


def t2s(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except Exception:
        return '?'


# ---- 会话表 ----
groups = {}   # talker -> display_name（群）
priv = {}     # talker -> display_name（私聊）
for t, n, st in cur.execute('select talker, display_name, session_type from sessions'):
    if st == '群聊':
        groups[t] = n or t
    elif st == '私聊':
        priv[t] = n or t

# ---- sender -> 群集合 ----
sender_groups = collections.defaultdict(set)
for sk, sd in cur.execute("select session_key, sender from messages where session_key like '%@chatroom'"):
    if sd:
        sender_groups[sd].add(sk)

# ---- 通讯录 ----
ct = {}
with open(CONTACTS, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        u = (r.get('用户名') or '').strip()
        if u:
            ct[u] = r

# ---- 私聊首末时间 ----
span = {}
for t, f, l, c in cur.execute('select session_key, min(ts), max(ts), count(*) from messages '
                              'where session_key not like "%@chatroom" group by session_key'):
    span[t] = (f, l, c)

# ---- 统计：私聊人能否匹配到共同群 ----
matched = 0
multi = collections.Counter()
rows = []
for t, n in priv.items():
    gs = sender_groups.get(t, set())
    if gs:
        matched += 1
        multi[len(gs)] += 1
    rows.append((t, n, gs))

print(f'私聊 {len(priv)} 人 ｜ 能在群聊里找到发言记录 {matched} 人 ({matched/len(priv)*100:.1f}%)')
print('共同群数量分布：', dict(sorted(multi.items())[:12]))

# ---- 输出：重点名单（近候选 + 高互动）----
buf = io.StringIO()
buf.write('=' * 80 + '\n')
buf.write('渠道场景逆推：私聊对象 ↔ 共同群\n')
buf.write('=' * 80 + '\n')
buf.write(f'私聊 {len(priv)} 人 ｜ 有共同群记录 {matched} 人\n')
buf.write(f'共同群数量分布：{dict(sorted(multi.items())[:12])}\n\n')

targets = sorted([r for r in rows if span.get(r[0], (0, 0, 0))[2] >= 300],
                 key=lambda r: -span[r[0]][2])
for t, n, gs in targets:
    f, l, c = span[t]
    cc = ct.get(t, {})
    tags = (cc.get('标签') or '').strip()
    since = round((NOW - l) / 86400)
    buf.write('-' * 80 + '\n')
    buf.write(f"### {n}   {c} 条 ｜ 加于 {t2s(f)} ｜ 距今 {since} 天 ｜ 标签={tags or '—'}\n")
    if gs:
        for g in sorted(gs):
            gn = groups.get(g, g)
            buf.write(f"    共同群：{gn}   ({g})\n")
    else:
        buf.write("    共同群：无记录（未在群里发言 / 非群渠道）\n")

# ---- 反向：哪些群是「加人渠道」 ----
buf.write('\n\n' + '=' * 80 + '\n')
buf.write('★ 反向：哪些群「产出」了最多私聊关系\n')
buf.write('=' * 80 + '\n')
gcount = collections.Counter()
for t, n, gs in rows:
    if span.get(t, (0, 0, 0))[2] >= 30:      # 只看有实质互动的
        for g in gs:
            gcount[g] += 1
for g, v in gcount.most_common(40):
    buf.write(f"  {v:>4}  {groups.get(g, g)}\n")

open(OUT, 'w', encoding='utf-8').write(buf.getvalue())
print('已写', OUT, len(buf.getvalue()), '字符')
