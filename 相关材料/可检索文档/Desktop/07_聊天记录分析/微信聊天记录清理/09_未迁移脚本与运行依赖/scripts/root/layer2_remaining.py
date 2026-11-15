import sqlite3
import json
import os

# 配置
DB_PATH = 'data/wechat-private-v2.sqlite3'

# 已分析的人
already_analyzed = [
    '导！急速回，三思回得体！！！', '陈昶文', 'Eloise',
    '蔡峰峰', '舒泽林', '郑英泽',
    '高晓斌 初中', '程颂孟秋', '汪伊俊', '李紫懿', '子辰',
    'Sīrius R', 'Lyj', 'ɪɴɢ 📎'
]

# 用户说不重要的人
exclude_list = [
    '笑一', '沐茜妍', '甘泉',
    '小苹果', '薛伟东', '🍬🍬', '王若彤', '杨丁懿', '金钰1500h'
]

print('=== 继续分析剩余重要联系人 ===')

# 获取所有联系人
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''
    SELECT display_name, total_messages, sent_count, received_count, active_months
    FROM contact_summary 
    WHERE contact_type = 'personal'
    ORDER BY total_messages DESC
''')

all_contacts = c.fetchall()
conn.close()

# 筛选待分析的人
remaining = []
for row in all_contacts:
    name = row[0]
    total = row[1]
    
    # 排除已分析和不重要的人
    if name in already_analyzed or name in exclude_list:
        continue
    
    # 排除系统号
    if '文件传输助手' in name or '微信' in name or '支付' in name:
        continue
    
    # 只要消息量 > 200
    if total >= 200:
        remaining.append({
            'name': name,
            'total': total,
            'sent': row[2],
            'received': row[3],
            'months': row[4]
        })

print(f'待分析: {len(remaining)}人')
print()

# 显示待分析列表
print('待分析列表:')
for i, p in enumerate(remaining[:20], 1):
    print(f'{i:2}. {p["name"]:<15} {p["total"]:>5}条消息')

# 保存
with open('layer2_remaining.json', 'w', encoding='utf-8') as f:
    json.dump(remaining, f, ensure_ascii=False, indent=2)

print(f'\n已保存到 layer2_remaining.json')
