import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# Layer 1: 严格筛选（排除不重要的人）
print('=== Layer 1: 最终筛选 ===')

# 获取所有个人联系人
c.execute('''
    SELECT 
        display_name,
        total_messages,
        sent_count,
        received_count,
        active_months,
        is_bidirectional,
        avg_chars_per_message
    FROM contact_summary 
    WHERE contact_type = 'personal'
    ORDER BY total_messages DESC
''')

all_contacts = c.fetchall()

# 排除名单（用户说不重要 + 已分析）
exclude_list = [
    '陈昶文', 'Eloise',  # 已分析
    '笑一', '沐茜妍', '甘泉',  # 不重要
    '小苹果', '薛伟东', '🍬🍬', '王若彤', '杨丁懿', '金钰1500h'  # 不重要
]

# 筛选逻辑
selected = []

for row in all_contacts:
    name = row[0]
    total = row[1]
    sent = row[2]
    received = row[3]
    months = row[4]
    
    # 排除
    if name in exclude_list:
        continue
    
    # 排除特殊联系人
    if '文件传输助手' in name or '微信' in name or '支付' in name:
        continue
    
    # 计算双向比例
    if received > 0:
        ratio = sent / received
    else:
        ratio = float('inf')
    
    # 筛选条件
    conditions = []
    if total >= 500:
        conditions.append('消息>500')
    if months >= 6:
        conditions.append('活跃>6月')
    if 0.5 <= ratio <= 2.0:
        conditions.append('双向互动')
    
    # 特殊关系关键词
    special_keywords = ['爸', '妈', '父', '母', '姑', '叔', '舅', '姨', '导师', '老师', '欠', '债', '室友']
    is_special = any(kw in name for kw in special_keywords)
    
    if is_special or len(conditions) >= 2:
        selected.append({
            'name': name,
            'total': total,
            'sent': sent,
            'received': received,
            'months': months,
            'ratio': ratio,
            'reasons': conditions + (['特殊关系'] if is_special else [])
        })

# 按消息量排序
selected.sort(key=lambda x: x['total'], reverse=True)

# 输出前30人
print(f'筛选通过: {len(selected)}人')
print(f'取前30人进行轻量分析\n')

print('=== Layer 2: 待分析的30人 ===')
print(f'{"排名":<4} {"昵称":<15} {"消息":<6} {"你发":<6} {"他发":<6} {"比例":<6} {"活跃月":<6} {"筛选理由"}')
print('-' * 80)

for i, p in enumerate(selected[:30], 1):
    print(f'{i:<4} {p["name"]:<15} {p["total"]:<6} {p["sent"]:<6} {p["received"]:<6} {p["ratio"]:<6.1f} {p["months"]:<6} {", ".join(p["reasons"])}')

# 保存到文件供后续使用
import json
with open('layer1_selected.json', 'w', encoding='utf-8') as f:
    json.dump(selected[:30], f, ensure_ascii=False, indent=2)

# 统计
print(f'\n=== 统计 ===')
total_msgs = sum(p['total'] for p in selected[:30])
print(f'前30人消息总量: {total_msgs:,}条')
print(f'占总消息比例: {total_msgs/sum(r[1] for r in all_contacts)*100:.1f}%')
print(f'\n已保存到 layer1_selected.json')
