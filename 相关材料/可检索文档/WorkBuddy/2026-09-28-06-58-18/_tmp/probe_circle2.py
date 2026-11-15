# -*- coding: utf-8 -*-
"""本科圈（城院 37 / 3班 49）114+24 人的消息量普查"""
import sqlite3, io

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/contact/contact.db'
IDX = r'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

d = sqlite3.connect('file:%s?mode=ro' % DEC, uri=True); d.row_factory = sqlite3.Row
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
    return [int(p) for p in buf[k:k + L].decode('ascii', 'ignore').split(',') if p.strip().isdigit()]


c = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
c.row_factory = sqlite3.Row

people = []
for r in d.execute("select username,remark,nick_name,extra_buffer from contact"):
    ids = labels(r['extra_buffer'])
    if 37 in ids or 49 in ids:
        people.append(dict(wx=r['username'], nm=r['remark'] or r['nick_name'] or r['username'],
                           nick=r['nick_name'], ids=ids, in37=37 in ids, in49=49 in ids))

P('本科圈（城院∪3班）= %d 人' % len(people))
P('')

rows = []
for p in people:
    n = c.execute("select count(*) from messages where session_key=?", (p['wx'],)).fetchone()[0]
    me = c.execute("select count(*) from messages where session_key=? and role='me'", (p['wx'],)).fetchone()[0]
    them = c.execute("select count(*) from messages where session_key=? and role='them'", (p['wx'],)).fetchone()[0]
    first = c.execute("select min(ts) from messages where session_key=?", (p['wx'],)).fetchone()[0]
    last = c.execute("select max(ts) from messages where session_key=?", (p['wx'],)).fetchone()[0]
    rows.append((n, p, me, them, first, last))

rows.sort(reverse=True, key=lambda x: x[0])
import datetime
def ts(x):
    return datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d') if x else '—'

P('=== 有消息的（按条数降序）===')
nz = [r for r in rows if r[0] > 0]
for n, p, me, them, f, l in nz:
    tag = ('3班' if p['in49'] else '') + ('城院' if p['in37'] else '')
    P('  %5d 条 (我%4d/他%4d)  %-22s | %-18s | %s→%s | %s'
      % (n, me, them, p['nm'][:22], (p['nick'] or '')[:18], ts(f), ts(l), tag))

P('')
P('=== 零消息的 ===')
z = [r for r in rows if r[0] == 0]
P('共 %d 人：' % len(z))
for n, p, me, them, f, l in z:
    tag = ('3班' if p['in49'] else '') + ('城院' if p['in37'] else '')
    P('  %-22s | %-18s | %s' % (p['nm'][:22], (p['nick'] or '')[:18], tag))

P('')
tot = sum(r[0] for r in rows)
P('=== 汇总 ===')
P('总人数 %d · 有消息 %d · 零消息 %d (%.1f%%)' % (len(rows), len(nz), len(z), 100.0 * len(z) / len(rows)))
P('消息总量 %d 条' % tot)
P('')
P('=== 3班 24 人明细 ===')
for n, p, me, them, f, l in sorted([r for r in rows if r[1]['in49']], key=lambda x: -x[0]):
    P('  %5d 条  %-22s | %-18s | %s→%s' % (n, p['nm'][:22], (p['nick'] or '')[:18], ts(f), ts(l)))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_benke_circle.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_benke_circle.txt')
