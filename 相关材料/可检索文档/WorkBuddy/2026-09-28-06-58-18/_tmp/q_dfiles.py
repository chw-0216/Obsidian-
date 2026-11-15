# -*- coding: utf-8 -*-
import sqlite3, datetime, io, re

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_dfiles.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


cut = int(datetime.datetime(2026, 8, 1).timestamp())
out.write('=== 8-01 起，Darwin 发出的 文件/链接 类消息 ===\n')
for ts, k, sender, content in c.execute(
        "select ts,session_key,sender,content from messages where ts>? and "
        "(sender like '%Darwin%' or content like '%Darwin480015%') order by ts", (cut,)):
    txt = content or ''
    if not re.search(r'\.(pdf|docx?|xlsx?|pptx?|zip)\b', txt, re.I) and '<appmsg' not in txt and 'mp.weixin' not in txt:
        continue
    t = datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
    m = re.search(r'<title>(.*?)</title>', txt)
    title = m.group(1)[:80] if m else ''
    out.write('%s [%s] sender=%s | %s\n' % (t, name(k)[:18], (sender or '')[:14], (title or txt.replace('\n', ' ')[:120])))

out.write('\n\n=== 8-01 起，所有群里的【文件】消息（不限发送者）===\n')
for ts, k, sender, content in c.execute(
        "select ts,session_key,sender,content from messages where ts>? order by ts", (cut,)):
    txt = content or ''
    if not re.search(r'\.(pdf|docx?|xlsx?|pptx?)\b', txt, re.I):
        continue
    t = datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
    out.write('%s [%s] %s | %s\n' % (t, name(k)[:18], (sender or '')[:14], txt.replace('\n', ' ')[:110]))

out.close()
print('done')
