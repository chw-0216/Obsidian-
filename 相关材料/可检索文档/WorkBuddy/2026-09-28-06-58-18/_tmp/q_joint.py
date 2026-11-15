# -*- coding: utf-8 -*-
import sqlite3, datetime, io, re

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_joint.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


out.write('=== 含「联合活动」的消息（去重后按时间）===\n')
seen = set()
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where content like '%联合活动%' order by ts"):
    txt = (content or '').replace('\n', ' / ').strip()
    head = txt[:60]
    if head in seen:
        continue
    seen.add(head)
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M'), name(k)[:20], role, txt[:220]))

out.write('\n\n=== 本人发出的、以【 开头的活动文案（标题行）===\n')
seen2 = set()
for ts, content in c.execute("select ts,content from messages where role='me' and content like '【%' order by ts"):
    first = (content or '').split('\n')[0][:70]
    if first in seen2:
        continue
    seen2.add(first)
    out.write('%s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M'), first))

out.close()
print('done')
