# -*- coding: utf-8 -*-
import sqlite3, datetime, io, sys

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_caoduo.txt', 'w', encoding='utf-8')

def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)

out.write('=== 全库含 曹多 ===\n')
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where content like '%曹多%' order by ts desc limit 40"):
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:22], role, (content or '').replace('\n', ' ')[:140]))

out.write('\n=== 含 曹 的私聊会话名 ===\n')
for k, n in c.execute("select talker, display_name from sessions where display_name like '%曹%'"):
    out.write('%s | %s\n' % (k, n))

cut = int(datetime.datetime(2026, 10, 19).timestamp())
out.write('\n=== 10-19 之后有新消息的会话 ===\n')
for k, cnt, a, b in c.execute('select session_key,count(*),min(ts),max(ts) from messages where ts>? group by session_key order by max(ts) desc', (cut,)).fetchall():
    out.write('%-32s %-34s %3d  %s -> %s\n' % (k, name(k)[:32], cnt,
              datetime.datetime.fromtimestamp(a).strftime('%m-%d %H:%M'),
              datetime.datetime.fromtimestamp(b).strftime('%m-%d %H:%M')))

out.write('\n=== 全库最新 ===\n')
n = c.execute('select count(*) from messages').fetchone()[0]
mx = c.execute('select max(ts) from messages').fetchone()[0]
out.write('messages %d latest %s\n' % (n, datetime.datetime.fromtimestamp(mx)))
out.close()
print('done')
