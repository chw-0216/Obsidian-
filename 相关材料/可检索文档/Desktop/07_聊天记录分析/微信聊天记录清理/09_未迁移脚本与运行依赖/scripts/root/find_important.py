import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 获取所有联系人统计
print('=== 重要联系人目录（按消息量排序）===')
c.execute('''
    SELECT 
        display_name,
        total_messages,
        sent_count,
        received_count,
        active_months,
        is_bidirectional,
        avg_chars_per_message,
        contact_type
    FROM contact_summary 
    WHERE contact_type = 'personal'
    ORDER BY total_messages DESC
    LIMIT 50
''')

rows = c.fetchall()
print(f'\n共找到 {len(rows)} 个重要联系人:\n')

# 分类输出
categories = {
    'core': [],      # >1000条
    'important': [], # 500-1000条
    'regular': [],   # 200-500条
    'light': []      # 100-200条
}

for row in rows:
    name = row[0]
    total = row[1]
    sent = row[2]
    received = row[3]
    months = row[4]
    bidirectional = row[5]
    avg_chars = row[6]
    
    entry = {
        'name': name,
        'total': total,
        'sent': sent,
        'received': received,
        'months': months,
        'bidirectional': bidirectional,
        'avg_chars': avg_chars
    }
    
    if total >= 1000:
        categories['core'].append(entry)
    elif total >= 500:
        categories['important'].append(entry)
    elif total >= 200:
        categories['regular'].append(entry)
    else:
        categories['light'].append(entry)

# 输出各类别
print('【核心圈层】>1000条消息')
print('-' * 60)
for p in categories['core']:
    ratio = p['sent']/p['received'] if p['received'] > 0 else float('inf')
    print(f"{p['name']:15} | {p['total']:5}条 | 你发{p['sent']:4} 他发{p['received']:4} | 比例{ratio:.1f}:1 | 活跃{p['months']}月")

print('\n【重要联系人】500-1000条消息')
print('-' * 60)
for p in categories['important']:
    ratio = p['sent']/p['received'] if p['received'] > 0 else float('inf')
    print(f"{p['name']:15} | {p['total']:5}条 | 你发{p['sent']:4} 他发{p['received']:4} | 比例{ratio:.1f}:1 | 活跃{p['months']}月")

print('\n【常联系人】200-500条消息')
print('-' * 60)
for p in categories['regular']:
    ratio = p['sent']/p['received'] if p['received'] > 0 else float('inf')
    print(f"{p['name']:15} | {p['total']:5}条 | 你发{p['sent']:4} 他发{p['received']:4} | 比例{ratio:.1f}:1 | 活跃{p['months']}月")

print('\n【轻度联系人】100-200条消息')
print('-' * 60)
for p in categories['light']:
    ratio = p['sent']/p['received'] if p['received'] > 0 else float('inf')
    print(f"{p['name']:15} | {p['total']:5}条 | 你发{p['sent']:4} 他发{p['received']:4} | 比例{ratio:.1f}:1 | 活跃{p['months']}月")

# 统计摘要
print('\n\n=== 统计摘要 ===')
print(f'核心圈层: {len(categories["core"])}人')
print(f'重要联系人: {len(categories["important"])}人')
print(f'常联系人: {len(categories["regular"])}人')
print(f'轻度联系人: {len(categories["light"])}人')

# 计算消息集中度
total_msgs = sum(p['total'] for p in categories['core'])
print(f'\n核心圈层消息占比: {total_msgs}/{sum(r[1] for r in rows)} = {total_msgs/sum(r[1] for r in rows)*100:.1f}%')
