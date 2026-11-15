import sqlite3

c = sqlite3.connect(r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3')
c.row_factory = sqlite3.Row

contacts = c.execute('SELECT display_name, loaded_message_count, first_ts, last_ts FROM conversations ORDER BY loaded_message_count DESC LIMIT 80').fetchall()
print(f'{"联系人":30s} {"消息数":>5}  {"时间跨度"}')
print('-' * 60)
for r in contacts:
    first = str(r['first_ts'])[:10] if r['first_ts'] else '?'
    last = str(r['last_ts'])[:10] if r['last_ts'] else '?'
    print(f'{r["display_name"]:30s} {r["loaded_message_count"]:5d}  {first} ~ {last}')
c.close()