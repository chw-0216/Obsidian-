# -*- coding: utf-8 -*-
"""正确解析 contact.extra_buffer field 30 = ASCII 逗号分隔的标签 ID 列表"""
import sqlite3, io
from collections import Counter

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/contact/contact.db'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

d = sqlite3.connect('file:%s?mode=ro' % DEC, uri=True)
d.row_factory = sqlite3.Row
lab = {int(i): n for i, n in d.execute("select label_id_, label_name_ from contact_label")}


def read_varint(b, i):
    shift = 0; val = 0
    while i < len(b):
        x = b[i]; i += 1
        val |= (x & 0x7F) << shift
        if not (x & 0x80): return val, i
        shift += 7
    return None, i


def labels(buf):
    if not buf: return []
    if isinstance(buf, str): buf = buf.encode('latin-1', 'ignore')
    j = buf.find(b'\xf2\x01')
    if j < 0: return []
    L, k = read_varint(buf, j + 2)
    if L is None or L <= 0 or k + L > len(buf): return []
    txt = buf[k:k + L].decode('ascii', 'ignore')
    res = []
    for p in txt.split(','):
        p = p.strip()
        if p.isdigit(): res.append(int(p))
    return res


rows = d.execute("select username,remark,nick_name,extra_buffer from contact").fetchall()
cnt = Counter(); has = 0
for r in rows:
    ids = labels(r['extra_buffer'])
    if ids:
        has += 1
        for x in set(ids): cnt[x] += 1

P('contact 总数 %d · 有标签 %d' % (len(rows), has))
P('')
P('===== 标签 ID → 人数 =====')
for k, v in cnt.most_common(80):
    P('   %3d  %-22s %5d' % (k, lab.get(k, '(字典无)'), v))

P('')
P('===== 城院(37) 成员 =====')
m37 = []
for r in rows:
    if 37 in labels(r['extra_buffer']):
        m37.append((r['remark'] or r['nick_name'] or r['username'], r['nick_name']))
P('城院 = %d 人' % len(m37))
for a, b in sorted(m37)[:130]:
    P('   %-24s | %s' % (a, b))

P('')
P('===== 3班(49) 成员 =====')
m49 = []
for r in rows:
    if 49 in labels(r['extra_buffer']):
        m49.append((r['remark'] or r['nick_name'] or r['username'], r['nick_name']))
P('3班 = %d 人' % len(m49))
for a, b in sorted(m49)[:130]:
    P('   %-24s | %s' % (a, b))

P('')
P('===== 37∩49 交集 =====')
s37 = set(); s49 = set()
for r in rows:
    ids = set(labels(r['extra_buffer']))
    nm = r['remark'] or r['nick_name'] or r['username']
    if 37 in ids: s37.add(nm)
    if 49 in ids: s49.add(nm)
P('37∩49 = %d 人：%s' % (len(s37 & s49), '、'.join(sorted(s37 & s49))))
P('37-49 = %d 人' % len(s37 - s49))
P('49-37 = %d 人' % len(s49 - s37))

P('')
P('===== 指定人物 =====')
for wx, nm in [('wxid_uhulgmrvfq4a12', '周雯娟'), ('wxid_4yurl8wrbi4a22', '李博文'),
               ('wxid_j5ekmvhqltug22', '程颂孟秋')]:
    r = d.execute("select username,remark,nick_name,extra_buffer from contact where username=?", (wx,)).fetchone()
    if r:
        ids = labels(r['extra_buffer'])
        P('%s: %s -> %s' % (nm, ids, [lab.get(x, '?') for x in ids]))

P('')
P('===== 标签字典全表 =====')
for k in sorted(lab): P('   %3d = %s' % (k, lab[k]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_tags_v3.txt',
        'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_tags_v3.txt')
