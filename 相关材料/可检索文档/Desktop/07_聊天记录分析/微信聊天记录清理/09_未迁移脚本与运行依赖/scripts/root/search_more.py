import sqlite3
import json

DB_PATH = 'data/wechat-private-v2.sqlite3'

print('=== 搜索更多关键词 ===')
print()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 搜索关键词
keywords = ['赞赞', '华赞', '天雪', '丽萍', '萍', '刘', '姐']

for kw in keywords:
    c.execute('''
        SELECT display_name, total_messages
        FROM contact_summary 
        WHERE display_name LIKE ?
        ORDER BY total_messages DESC
        LIMIT 15
    ''', (f'%{kw}%',))
    
    results = c.fetchall()
    if results:
        print(f'关键词 "{kw}" 匹配:')
        for r in results:
            print(f'  {r[0]}: {r[1]}条')
        print()

# 也搜索消息内容
print('=== 搜索消息内容 ===')
keywords2 = ['赞赞', '华赞', '天雪', '丽萍']
for kw in keywords2:
    c.execute('''
        SELECT DISTINCT cs.display_name, cs.total_messages
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN contact_summary cs ON c.id = cs.conversation_id
        WHERE m.content LIKE ?
        LIMIT 5
    ''', (f'%{kw}%',))
    
    results = c.fetchall()
    if results:
        print(f'消息含 "{kw}" 的联系人:')
        for r in results:
            print(f'  {r[0]}: {r[1]}条')
        print()

conn.close()
