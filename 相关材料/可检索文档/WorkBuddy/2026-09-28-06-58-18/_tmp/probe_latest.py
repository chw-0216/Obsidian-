# -*- coding: utf-8 -*-
import sqlite3, datetime, io
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M')
    except Exception: return str(t)
out=[]; P=lambda *a: out.append(' '.join(str(x) for x in a))
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

T0 = int(datetime.datetime(2026,10,12,7,0).timestamp())

P('===== 0) 库现状 =====')
n = i.execute('select count(*) from messages').fetchone()[0]
mx = i.execute('select max(ts) from messages').fetchone()[0]
ns = i.execute('select count(distinct session_key) from messages').fetchone()[0]
P('  总条数 %d · 会话 %d · 最新 %s' % (n, ns, ts2s(mx)))

P('')
P('===== 1) 10-12 07:00 之后增量（按会话 top 25） =====')
rows = i.execute("""select session_key, count(*) c, sum(role='me') m, max(ts) mt
    from messages where ts>? group by session_key order by c desc limit 25""", (T0,)).fetchall()
tot = i.execute('select count(*) from messages where ts>?', (T0,)).fetchone()[0]
P('  增量合计 %d 条 / %d 会话' % (tot, i.execute('select count(distinct session_key) from messages where ts>?',(T0,)).fetchone()[0]))
# 群名映射
d = sqlite3.connect('file:C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/contact/contact.db?mode=ro', uri=True)
def nm(sk):
    try:
        r = i.execute('select display_name from sessions where talker=?', (sk,)).fetchone()
        if r and r[0]: return r[0]
    except Exception: pass
    try:
        r = d.execute('select remark, nick_name from contact where username=?', (sk,)).fetchone()
        if r: return r[0] or r[1] or sk
    except Exception: pass
    return sk
for sk, c, m, mt in rows:
    P('  %-30s %4d 条 (我 %3d) 末 %s' % (nm(sk)[:30], c, m or 0, ts2s(mt)))

P('')
P('===== 2) 笑一线 10-12 07:00 后全量 =====')
for ts, role, c in i.execute("select ts,role,content from messages where session_key='wxid_wdnk6ue9kiyn22' and ts>? order by ts asc", (T0,)):
    P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:150]))

P('')
P('===== 3) 两个班群 10-12 07:00 后 =====')
for g in ('57413014124@chatroom','47564321348@chatroom'):
    P('--- %s ---' % nm(g))
    for ts, role, c in i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc", (g, T0)):
        P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:140]))

P('')
P('===== 4) 舒泽林 / 陈晔 / 母亲 10-12 07:00 后 =====')
for sk, lab in (('wxid_0ejd54z34nmv32','舒泽林'),('deerluna','陈晔'),('wxid_1wa75s1kze3o22','母亲')):
    P('--- %s ---' % lab)
    rs = i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc", (sk, T0)).fetchall()
    if not rs: P('  （无）')
    for ts, role, c in rs[:25]:
        P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:130]))

P('')
P('===== 5) 今日 10-13 全部会话分布 =====')
D0 = int(datetime.datetime(2026,10,13,0,0).timestamp())
rows = i.execute("""select session_key, count(*) c, sum(role='me') m from messages
    where ts>? group by session_key order by c desc limit 20""", (D0,)).fetchall()
P('  今日合计 %d 条' % i.execute('select count(*) from messages where ts>?', (D0,)).fetchone()[0])
for sk, c, m in rows:
    P('  %-30s %4d 条 (我 %3d)' % (nm(sk)[:30], c, m or 0))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_latest.txt','w',encoding='utf-8').write('\n'.join(out))
print('OK lines=%d' % len(out))
