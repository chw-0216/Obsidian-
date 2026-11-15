# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_ev.txt', 'w', encoding='utf-8')


def name(k):
    r = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
    return (r[0] if r and r[0] else k)


cut = int(datetime.datetime(2026, 10, 18).timestamp())

out.write('=== 10-18 起，Darwin 的全部发言 ===\n')
for ts, k, content in c.execute("select ts,session_key,content from messages where ts>? and (sender like '%Darwin%') order by ts", (cut,)):
    txt = (content or '').replace('\n', ' / ')
    out.write('%s [%s] %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:20], txt[:220]))

out.write('\n\n=== 10-13 起，含 万圣 / Halloween / 沙龙 / 派对 的消息 ===\n')
cut2 = int(datetime.datetime(2026, 10, 13).timestamp())
seen = set()
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where ts>? order by ts", (cut2,)):
    txt = content or ''
    if not any(w in txt for w in ['万圣', 'Halloween', '沙龙', '派对', '就业指导']):
        continue
    head = txt.replace('\n', ' ')[:70]
    if head in seen:
        continue
    seen.add(head)
    out.write('%s [%s] %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), name(k)[:20], role, txt.replace('\n', ' / ')[:200]))

out.write('\n\n=== 校友会2026 群 10-14 之后全部 ===\n')
cut3 = int(datetime.datetime(2026, 10, 14, 1).timestamp())
for ts, role, content in c.execute("select ts,role,content from messages where session_key='50075185775@chatroom' and ts>? order by ts", (cut3,)):
    out.write('%s %-5s %s\n' % (datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'), role, (content or '').replace('\n', ' / ')[:200]))

out.close()
print('done')
