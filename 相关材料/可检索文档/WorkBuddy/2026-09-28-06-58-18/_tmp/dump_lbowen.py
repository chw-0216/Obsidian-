# -*- coding: utf-8 -*-
import sqlite3, os, datetime, io, json
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
LI = 'wxid_4yurl8wrbi4a22'
OUT = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\lbowen_full.txt'

def fmt(t):
    try:
        return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(t)

con = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
con.row_factory = sqlite3.Row
rows = list(con.execute(
    "select ts, role, content, type from messages where session_key=? order by ts", (LI,)))
print('rows:', len(rows))
if rows:
    print('first:', fmt(rows[0]['ts']), '| last:', fmt(rows[-1]['ts']))
    print('cols:', rows[0].keys())

import re
def clean(ct, typ=None):
    ct = ct or ''
    if '<img' in ct or '<msg' in ct or ct.startswith('<?xml'):
        head = ct.split('<')[0].strip()
        return (head[:80] + ' 〔图片/附件/卡片〕') if head else '〔图片/附件/卡片〕'
    return ct.replace('\n', ' ⏎ ')

buf = []
buf.append('# 李博文 城市学院（wxid_4yurl8wrbi4a22）· 私聊全量 · 源：index.sqlite')
buf.append('# 条数 %d · %s → %s' % (len(rows), fmt(rows[0]['ts']) if rows else '-', fmt(rows[-1]['ts']) if rows else '-'))
buf.append('')
for r in rows:
    who = {'me': '我', 'them': '他', 'system': '系统'}.get(r['role'], r['role'])
    buf.append('%s | %-3s | %s' % (fmt(r['ts']), who, clean(r['content'], r['type'])[:400]))

io.open(OUT, 'w', encoding='utf-8', newline='').write('\n'.join(buf))
print('written', OUT, len('\n'.join(buf).encode('utf-8')), 'bytes')

# 月度分布
from collections import Counter
c = Counter(fmt(r['ts'])[:7] for r in rows)
print('\n月度分布:')
for k in sorted(c):
    print('   %s  %d' % (k, c[k]))
