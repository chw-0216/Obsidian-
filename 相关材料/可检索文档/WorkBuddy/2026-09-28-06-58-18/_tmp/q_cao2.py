# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_cao2.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


out.write('=== 含 多伟 / 曹多 的消息 ===\n')
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where content like '%多伟%' or content like '%曹多%' order by ts desc limit 40"):
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:22], role, (content or '').replace('\n', ' ')[:160]))

out.write('\n=== Darwin 会话概况 ===\n')
r = c.execute("select count(*),min(ts),max(ts) from messages where session_key='Darwin480015'").fetchone()
out.write('count=%d  %s -> %s\n' % (r[0], datetime.datetime.fromtimestamp(r[1]), datetime.datetime.fromtimestamp(r[2])))

out.write('\n=== Darwin 最后 15 条（含类型）===\n')
for ts, role, content in c.execute("select ts,role,content from messages where session_key='Darwin480015' order by ts desc limit 15").fetchall()[::-1]:
    out.write('%s %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), role, (content or '').replace('\n', ' / ')[:200]))

out.write('\n=== 周冉 最后 15 条 ===\n')
for ts, role, content in c.execute("select ts,role,content from messages where session_key='zhouran68' order by ts desc limit 15").fetchall()[::-1]:
    out.write('%s %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), role, (content or '').replace('\n', ' / ')[:200]))

out.write('\n=== 10-19 之后，我发出的消息（全部会话）===\n')
cut = int(datetime.datetime(2026, 10, 19).timestamp())
for ts, k, content in c.execute("select ts,session_key,content from messages where ts>? and role='me' order by ts", (cut,)):
    out.write('%s [%s] %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:22], (content or '').replace('\n', ' / ')[:200]))

out.close()
print('done')
