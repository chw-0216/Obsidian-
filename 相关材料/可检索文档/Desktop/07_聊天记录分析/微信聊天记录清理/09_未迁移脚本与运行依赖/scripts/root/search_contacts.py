import sqlite3
import json

DB_PATH = 'data/wechat-private-v2.sqlite3'

print('=== 搜索联系人（模糊匹配）===')
print()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 搜索关键词
keywords = ['赞', '华', '丽萍', '天雪', '晓斌', 'momo', '笑']

for kw in keywords:
    c.execute('''
        SELECT display_name, total_messages
        FROM contact_summary 
        WHERE display_name LIKE ?
        ORDER BY total_messages DESC
        LIMIT 10
    ''', (f'%{kw}%',))
    
    results = c.fetchall()
    if results:
        print(f'关键词 "{kw}" 匹配:')
        for r in results:
            print(f'  {r[0]}: {r[1]}条')
        print()

conn.close()
