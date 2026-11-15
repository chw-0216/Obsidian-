import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# Layer 1: 严格筛选
print('=== Layer 1: 价值筛选 ===')
print('筛选标准: 消息>500 OR 活跃>6月 OR 双向互动')
print()

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
print(f'总联系人: {len(all_contacts)}人')

# 筛选逻辑
selected = []
excluded = []

# 已分析的人（排除）
already_analyzed = ['陈昶文', 'Eloise']

for row in all_contacts:
    name = row[0]
    total = row[1]
    sent = row[2]
    received = row[3]
    months = row[4]
    
    # 排除已分析
    if name in already_analyzed:
        excluded.append((name, '已分析'))
        continue
    
    # 排除特殊联系人
    if '文件传输助手' in name or '微信' in name or '支付' in name:
        excluded.append((name, '系统号'))
        continue
    
    # 计算双向比例
    if received > 0:
        ratio = sent / received
    else:
        ratio = float('inf')
    
    # 筛选条件（至少满足2条）
    conditions = []
    if total >= 500:
        conditions.append('消息>500')
    if months >= 6:
        conditions.append('活跃>6月')
    if 0.5 <= ratio <= 2.0:
        conditions.append('双向互动')
    
    # 家人/导师/欠钱关键词
    family_keywords = ['爸', '妈', '父', '母', '姑', '叔', '舅', '姨', '导师', '老师']
    debt_keywords = ['欠', '债', '借']
    is_special = any(kw in name for kw in family_keywords + debt_keywords)
    
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
    else:
        excluded.append((name, f'不满足条件(仅{len(conditions)}条)'))

# 按消息量排序
selected.sort(key=lambda x: x['total'], reverse=True)

# 输出结果
print(f'\n筛选通过: {len(selected)}人')
print(f'筛选排除: {len(excluded)}人')

print('\n=== 筛选通过的联系人 ===')
print(f'{"排名":<4} {"昵称":<15} {"消息":<6} {"你发":<6} {"他发":<6} {"比例":<6} {"活跃月":<6} {"筛选理由"}')
print('-' * 80)

for i, p in enumerate(selected[:30], 1):
    print(f'{i:<4} {p["name"]:<15} {p["total"]:<6} {p["sent"]:<6} {p["received"]:<6} {p["ratio"]:<6.1f} {p["months"]:<6} {", ".join(p["reasons"])}')

# 统计
print(f'\n=== 统计 ===')
total_msgs = sum(p['total'] for p in selected[:30])
print(f'前30人消息总量: {total_msgs:,}条')
print(f'占总消息比例: {total_msgs/sum(r[1] for r in all_contacts)*100:.1f}%')
