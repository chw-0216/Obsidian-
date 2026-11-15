# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_recent.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


cut = int(datetime.datetime(2026, 10, 15).timestamp())
out.write('=== 10-15 起，含 活动关键词 的消息 ===\n')
kw = ['联合', '沙龙', '论坛', '分享会', '报名', '嘉宾', '讲座', '活动']
seen = set()
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where ts>? order by ts", (cut,)):
    txt = (content or '')
    if not any(w in txt for w in kw):
        continue
    n = name(k)
    if '格拉斯哥' not in n and 'UoG' not in n and '校友' not in n and k not in ('Darwin480015', 'zhouran68', 'filehelper'):
        continue
    head = txt.replace('\n', ' ')[:80]
    if head in seen:
        continue
    seen.add(head)
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), n[:22], role, txt.replace('\n', ' / ')[:300]))

out.write('\n\n=== 校友会2026 群 最近 30 条 ===\n')
for ts, role, content in c.execute("select ts,role,content from messages where session_key='50075185775@chatroom' order by ts desc limit 30").fetchall()[::-1]:
    out.write('%s %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), role, (content or '').replace('\n', ' / ')[:200]))

out.close()
print('done')
