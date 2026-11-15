# -*- coding: utf-8 -*-
"""
关系起点逆推 v2 —— 修正 v1 的两处问题：
  ① v1 用 sessions.first_ts（部分为 NULL）→ 改用 messages 的 min(ts)/max(ts)
  ② v1 误读「他加我=0」→ 实测 %已添加你% 命中 0 条，微信不记录此类消息
     → 结论修正为：「无法判断谁加谁，只能判断他是否主动加过」

输出四问所需原料：
  ① 我怎么加的：是否主动加 / 加的时间 / 打招呼附言 / 我的第一句话
  ② 对方是什么人：标签 / 备注 / 地区 / 对方第一句话
  ③ 当时价值：加的时间 → 人生阶段
  ④ 之后价值：消息量年度分布 / 距今天数 / 近期片段
"""
import sqlite3, csv, os, sys, re, io, collections
from datetime import datetime

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
CONTACTS = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
            r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
            r'\contacts_2026-07-23T20-56-25.csv')
OUT = os.path.join(WS, '_tmp', 'relation_origin_v2.txt')

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
cur = con.cursor()
NOW = datetime.now().timestamp()


def t2s(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except Exception:
        return '?'


def clean(c):
    return re.sub(r'<[^>]+>', '', c or '').replace('\n', ' ').strip()


ct = {}
with open(CONTACTS, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        u = (r.get('用户名') or '').strip()
        if u:
            ct[u] = r

# 会话
sess = {}
for t, n, st in cur.execute('select talker, display_name, session_type from sessions'):
    if st == '私聊':
        sess[t] = n or ''

# 消息时间范围 + 年度分布 + 我发条数
agg = {}
for t, cnt, f, l in cur.execute('''select session_key, count(*), min(ts), max(ts)
        from messages group by session_key'''):
    agg[t] = dict(cnt=cnt, f=f, l=l)
yearly = collections.defaultdict(collections.Counter)
for t, ts in cur.execute('select session_key, ts from messages'):
    if t in sess and ts:
        yearly[t][datetime.fromtimestamp(int(ts)).year] += 1

# 谁主动加（system）
origin = {}
for sk, ts, c in cur.execute("select session_key, ts, content from messages where type='system' order by ts asc"):
    s = clean(c)
    if s.startswith('你已添加了'):
        origin.setdefault(sk, ('他主动加', s, ts))
    elif '通过了你的朋友验证' in s:
        origin.setdefault(sk, ('他主动加（对方通过）', s, ts))

# 我的第一句 / 对方第一句
first_me = {}
first_them = {}
for sk, role, ts, c in cur.execute("select session_key, role, ts, content from messages "
                                   "where type='text' order by ts asc"):
    if sk not in sess:
        continue
    if role == 'me':
        first_me.setdefault(sk, clean(c))
    elif role == 'them':
        first_them.setdefault(sk, clean(c))

targets = [t for t in sess if agg.get(t, {}).get('cnt', 0) >= 1000]
targets.sort(key=lambda t: -agg[t]['cnt'])

buf = io.StringIO()
for t in targets:
    n = sess[t]
    if n == '文件传输助手':
        continue
    a = agg[t]
    c = ct.get(t, {})
    remark = (c.get('备注') or '').strip()
    nick = (c.get('昵称') or '').strip()
    tags = (c.get('标签') or '').strip()
    d, txt, ots = origin.get(t, ('无 system 记录（可能早已互加/扫码/群转私）', '', a['f']))
    since = round((NOW - a['l']) / 86400)
    yc = yearly.get(t, {})
    ystr = ' · '.join(f'{y}:{v}' for y, v in sorted(yc.items()))

    buf.write('=' * 80 + '\n')
    buf.write(f"### {n}   {a['cnt']} 条\n")
    buf.write(f"  标签={tags or '—'} ｜ 备注={remark or nick} ｜ 地区={c.get('地区','') or '—'}\n")
    buf.write(f"  ① 加好友：{d} ｜ {t2s(ots)}  ｜ system: {txt[:60]}\n")
    buf.write(f"  ① 我的第一句：{(first_me.get(t) or '—')[:90]}\n")
    buf.write(f"  ② 对方第一句：{(first_them.get(t) or '—')[:90]}\n")
    buf.write(f"  ③④ 首次 {t2s(a['f'])} → 末次 {t2s(a['l'])}（距今 {since} 天）\n")
    buf.write(f"     年度分布：{ystr}\n")
    buf.write('  --- 最近 4 条 ---\n')
    for ts2, role, ty, cc in cur.execute(
            'select ts, role, type, content from messages where session_key=? order by ts desc limit 4', (t,)):
        buf.write(f"   [{t2s(ts2)}] {role:<6} {ty:<8} {clean(cc)[:100]}\n")
    buf.write('\n')

open(OUT, 'w', encoding='utf-8').write(buf.getvalue())
print('已写', OUT, len(buf.getvalue()), '字符 ·', len(targets), '人')
