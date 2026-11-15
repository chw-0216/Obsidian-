import sqlite3
import json

DB_PATH = 'data/wechat-private-v2.sqlite3'

# 用户指定的人
target_contacts = [
    '高晓斌 初中',
    '刘华赞',
    '赞赞姐',
    '笑一',
    '华天雪',
    '刘丽萍',
    'momo'
]

print('=== 查找用户指定的联系人 ===')
print()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 搜索这些联系人（模糊匹配）
found = []
for target in target_contacts:
    c.execute('''
        SELECT display_name, conversation_id, total_messages, sent_count, received_count, active_months
        FROM contact_summary 
        WHERE display_name LIKE ? OR display_name LIKE ?
        ORDER BY total_messages DESC
    ''', (f'%{target}%', f'%{target[:2]}%'))
    
    results = c.fetchall()
    if results:
        for r in results:
            found.append({
                'search': target,
                'name': r[0],
                'conv_id': r[1],
                'total': r[2],
                'sent': r[3],
                'received': r[4],
                'months': r[5]
            })
            print(f'找到: {target} -> {r[0]} ({r[2]}条消息)')
    else:
        print(f'未找到: {target}')

conn.close()

print()
print(f'共找到 {len(found)} 个匹配')

# 保存
with open('layer2_target_contacts.json', 'w', encoding='utf-8') as f:
    json.dump(found, f, ensure_ascii=False, indent=2)
