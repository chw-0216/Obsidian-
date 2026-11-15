# -*- coding: utf-8 -*-
"""严谨解析 contact.extra_buffer 的 field 30（标签 ID 列表）—— varint 长度"""
import sqlite3, io, re
from collections import Counter

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/contact/contact.db'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a)
    out.append(t); print(t)

d = sqlite3.connect('file:%s?mode=ro' % DEC, uri=True)
d.row_factory = sqlite3.Row

lab = {int(i): n for i, n in d.execute("select label_id_, label_name_ from contact_label")}
P('标签字典（%d 个）:' % len(lab))
for k in sorted(lab): P('   %3d = %s' % (k, lab[k]))
P('')


def read_varint(b, i):
    """返回 (value, next_index)"""
    shift = 0; val = 0
    while i < len(b):
        x = b[i]; i += 1
        val |= (x & 0x7F) << shift
        if not (x & 0x80):
            return val, i
        shift += 7
        if shift > 63: break
    return None, i


def parse_labels(buf):
    """扫 field 30 (tag = 0xf2 0x01) 的 length-delimited 段，返回标签 ID 列表"""
    if not buf: return []
    if isinstance(buf, str): buf = buf.encode('latin-1', 'ignore')
    ids = []
    i = 0
    while True:
        j = buf.find(b'\xf2\x01', i)
        if j < 0: break
        L, k = read_varint(buf, j + 2)
        if L is None or L <= 0 or k + L > len(buf):
            i = j + 2; continue
        seg = buf[k:k + L]
        # seg 每个字节是一个标签 ID（若出现 varint 多字节，则按 varint 逐个读）
        m = 0
        while m < len(seg):
            v, m2 = read_varint(seg, m)
            if v is None or m2 == m: break
            ids.append(v); m = m2
        i = k + L
    return ids


P('===== 全量统计 =====')
cnt = Counter()
total = 0
rows = d.execute("select username, remark, nick_name, extra_buffer from contact").fetchall()
P('contact 总数 =', len(rows))
for r in rows:
    ids = parse_labels(r['extra_buffer'])
    if ids:
        total += 1
        for x in set(ids):
            cnt[x] += 1
P('有标签的人 =', total)
P('')
P('===== 标签 ID → 人数（降序）=====')
for k, v in cnt.most_common(60):
    P('   %3d  %-14s  %5d 人' % (k, lab.get(k, '?'), v))

P('')
P('===== 指定人物 =====')
TARGETS = {
    'wxid_uhulgmrvfq4a12': '周雯娟',
    'wxid_4yurl8wrbi4a22': '李博文',
}
for wx, nm in TARGETS.items():
    r = d.execute("select username,remark,nick_name,extra_buffer from contact where username=?", (wx,)).fetchone()
    if r:
        ids = parse_labels(r['extra_buffer'])
        P('%s (%s): 标签 ID = %s -> %s' % (nm, wx, ids, [lab.get(x, '?') for x in ids]))
    else:
        P('%s (%s): contact 无记录' % (nm, wx))

# 程颂孟秋 / 其他人：按备注找
P('')
P('===== 按备注找：程颂孟秋 / 孟秋 =====')
for r in d.execute("select username,remark,nick_name,extra_buffer from contact "
                   "where remark like '%孟秋%' or nick_name like '%孟秋%' or remark like '%程颂%'"):
    ids = parse_labels(r['extra_buffer'])
    P('  %s | remark=%s | nick=%s | 标签=%s -> %s' % (r['username'], r['remark'], r['nick_name'], ids, [lab.get(x, '?') for x in ids]))

P('')
P('===== 标签 49 / 37 分别是谁（前 30）=====')
for target in (37, 49, 51, 55, 44, 48, 52, 57):
    members = []
    for r in rows:
        if target in set(parse_labels(r['extra_buffer'])):
            members.append(r['remark'] or r['nick_name'] or r['username'])
    P('[%d = %s] %d 人：%s' % (target, lab.get(target, '?'), len(members), '、'.join(members[:30])))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_tags_rigorous.txt',
        'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_tags_rigorous.txt')
