# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_darwin.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


def dump(k, since, label):
    out.write('\n' + '=' * 20 + ' %s (%s) %s ' % (label, k, since) + '=' * 20 + '\n')
    cut = int(datetime.datetime(*since).timestamp())
    rows = c.execute('select ts,role,content from messages where session_key=? and ts>? order by ts', (k, cut)).fetchall()
    out.write('count=%d\n' % len(rows))
    for ts, role, content in rows:
        txt = (content or '').replace('\n', ' / ')
        for tag in ['<img', '<video', '<emoji', '<appmsg']:
            if txt.startswith(tag):
                txt = '[' + tag[1:] + '] ' + txt[:200]
        out.write('%s %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), role, txt[:400]))


dump('Darwin480015', (2026, 10, 10), 'Darwin 曹总')
dump('zhouran68', (2026, 10, 10), '周冉')

out.write('\n' + '=' * 20 + ' 近 10 天含 mp.weixin / 图文 / 链接 的消息 ' + '=' * 20 + '\n')
cut = int(datetime.datetime(2026, 10, 10).timestamp())
for ts, k, role, content in c.execute(
        "select ts,session_key,role,content from messages where ts>? and "
        "(content like '%mp.weixin%' or content like '%公众号%' or content like '%图文%' or content like '%推送%') order by ts desc limit 60", (cut,)):
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:24], role, (content or '').replace('\n', ' ')[:200]))

out.close()
print('done')
