# -*- coding: utf-8 -*-
import sqlite3, io, os, sys, datetime, re

IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
AN  = 'C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/analysis.sqlite'

out = []
def P(*a):
    out.append(' '.join(str(x) for x in a))

def ts2s(t):
    try:
        return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return str(t)

# ---------- 1) analysis.sqlite ----------
P('===== 1) analysis.sqlite =====')
c = sqlite3.connect('file:%s?mode=ro' % AN, uri=True)
P('tables:', c.execute("select count(*) from sqlite_master where type='table'").fetchone()[0])
for t in ('events','evidence','persons','aliases'):
    P('  %-10s %d' % (t, c.execute('select count(*) from '+t).fetchone()[0]))
for kw in ('朱子涵','子涵','李紫','紫'):
    rows = c.execute("select person_id,name,talker,relation,distance from persons where name like ?", ('%'+kw+'%',)).fetchall()
    if rows:
        P('  persons[%s] ->' % kw, rows)
P('  aliases 模糊:')
for kw in ('朱子涵','子涵','李紫'):
    rows = c.execute("select alias,person_id,kind from aliases where alias like ?", ('%'+kw+'%',)).fetchall()
    if rows:
        P('   ', kw, rows)

# 事件里搜「中期汇报」「汇报」
P('  events 含「中期」:')
for r in c.execute("select event_id,date,event from events where event like '%中期%' order by date desc limit 12"):
    P('   ', r[0], r[1], (r[2] or '')[:90])
P('  events 含「汇报」:')
for r in c.execute("select event_id,date,event from events where event like '%汇报%' order by date desc limit 12"):
    P('   ', r[0], r[1], (r[2] or '')[:90])

# ---------- 2) contact.db ----------
P('')
P('===== 2) contact.db =====')
DECU = DEC.replace('\\', '/')
try:
    d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DECU, uri=True)
    for kw in ('朱子涵','子涵','李紫','李紫怡','李紫依','李紫漪'):
        rows = d.execute(
            "select username,remark,nick_name,alias from contact where remark like ? or nick_name like ? or alias like ?",
            ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')).fetchall()
        P('  [%s] %d 条' % (kw, len(rows)))
        for r in rows[:25]:
            P('     ', r)
except Exception as e:
    P('  contact ERR', e)

# ---------- 3) index.sqlite sessions ----------
P('')
P('===== 3) index.sqlite sessions =====')
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
for kw in ('朱子涵','子涵','李紫'):
    rows = i.execute("select talker,display_name,session_type,message_count,first_ts,last_ts from sessions where display_name like ? or talker like ?",
                     ('%'+kw+'%', '%'+kw+'%')).fetchall()
    P('  [%s] %d' % (kw, len(rows)))
    for r in rows[:25]:
        P('     ', r[0], '|', r[1], '|', r[2], '|', r[3], '|', ts2s(r[4]), '->', ts2s(r[5]))

# ---------- 4) 消息表按 talker 计 ----------
P('')
P('===== 4) 消息量（若上一步命中 talker） =====')
talks = set()
for kw in ('朱子涵','李紫'):
    for r in i.execute("select talker from sessions where display_name like ?", ('%'+kw+'%',)):
        talks.add(r[0])
for tk in talks:
    row = i.execute("select count(*), sum(role='me'), min(ts), max(ts) from messages where session_key=?", (tk,)).fetchone()
    P('  ', tk, row[0], '我发', row[1], ts2s(row[2]), '->', ts2s(row[3]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1013.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
