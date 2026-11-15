# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DB = 'file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro'
c = sqlite3.connect(DB, uri=True)
out = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\q_body.txt', 'w', encoding='utf-8')

picks = ['2026-03-28 18:24', '2025-12-05 09:50', '2025-11-26 09:21', '2026-01-05 17:01']
for ts, k, role, content in c.execute("select ts,session_key,role,content from messages where role='me' and content like '%【联合活动】%' order by ts"):
    t = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    if t not in picks:
        continue
    out.write('\n' + '=' * 30 + ' ' + t + ' ' + '=' * 30 + '\n')
    out.write((content or '') + '\n')

out.close()
print('done')
