# -*- coding: utf-8 -*-
import sqlite3, os, datetime, io, re
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
M = 1 << 64
WEN = 'wxid_uhulgmrvfq4a12'; LI = 'wxid_4yurl8wrbi4a22'
def fmt(t):
    try: return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

sc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'sns', 'sns.db').replace('\\', '/'), uri=True)
sc.row_factory = sqlite3.Row
print('=== 李博文 feed 全 31 条 ===')
rr = list(sc.execute('select tid,username,create_time,last_read_time,is_read from SnsTopItem_1 where username=? order by create_time', (LI,)))
for r in rr:
    print('  post=%s  last_read=%s  is_read=%s' % (fmt(r['create_time']), fmt(r['last_read_time']), r['is_read']))
print('  合计', len(rr))
print()
print('=== 周雯娟 feed 全部 ===')
for r in sc.execute('select tid,username,create_time,last_read_time,is_read from SnsTopItem_1 where username=?', (WEN,)):
    print('  post=%s  last_read=%s  is_read=%s  tid=%s' % (fmt(r['create_time']), fmt(r['last_read_time']), r['is_read'], r['tid']))
print()
print('=== 今日(10-11) feed 中 last_read 落在 19:00 之后的会话 ===')
import datetime as dt
t0 = dt.datetime(2026,10,11,0,0).timestamp(); t1 = dt.datetime(2026,10,11,19,0).timestamp()
for r in sc.execute('select username,create_time,last_read_time from SnsTopItem_1 where last_read_time>=? order by last_read_time', (t1,)):
    print('  read=%s | post=%s | %s' % (fmt(r['last_read_time']), fmt(r['create_time']), r['username']))
print()
print('=== analysis.sqlite 里这两人 ===')
ADB = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
ac = sqlite3.connect('file:%s?mode=ro' % ADB.replace('\\', '/'), uri=True); ac.row_factory = sqlite3.Row
for kw in ('李博文', '周雯娟', '周文娟', '博文', '雯娟'):
    for tb, col in (('persons', 'name'), ('aliases', 'alias')):
        try:
            rows = list(ac.execute('select * from %s where %s like ?' % (tb, col), ('%'+kw+'%',)))
        except Exception as e:
            rows = []
        if rows:
            print('  %s.%s 「%s」 -> %d' % (tb, col, kw, len(rows)))
            for r in rows[:5]: print('     ', dict(r))
    n = ac.execute("select count(*) from events where 事件全文 like ?", ('%'+kw+'%',)).fetchone()[0] if True else 0
    if n: print('  events 含「%s」 -> %d' % (kw, n))
    n2 = ac.execute("select count(*) from evidence where quote like ?", ('%'+kw+'%',)).fetchone()[0]
    if n2: print('  evidence 含「%s」 -> %d' % (kw, n2))
