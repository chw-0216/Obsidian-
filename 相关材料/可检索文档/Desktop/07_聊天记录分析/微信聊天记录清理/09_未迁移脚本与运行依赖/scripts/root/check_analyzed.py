import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看已有档案的联系人
print('=== 已有深度档案的联系人 ===')
c.execute('''
    SELECT 
        cp.display_name,
        cp.relationship_type,
        cp.closeness_score,
        cp.communication_style,
        cs.total_messages
    FROM contact_profiles cp
    JOIN contact_summary cs ON cp.conversation_id = cs.conversation_id
    ORDER BY cs.total_messages DESC
''')

rows = c.fetchall()
print(f'共 {len(rows)} 人有深度档案:\n')

for row in rows:
    print(f'【{row[0]}】')
    print(f'  消息量: {row[4]}条')
    print(f'  关系类型: {row[1]}')
    print(f'  亲密度: {row[2]}/10')
    print(f'  沟通风格: {row[3][:50]}...' if row[3] and len(row[3]) > 50 else f'  沟通风格: {row[3]}')
    print()

# 查看已有时间线摘要的联系人
print('\n=== 已有时间线摘要的联系人 ===')
c.execute('''
    SELECT 
        cts.display_name,
        cts.time_layer,
        cts.summary,
        cs.total_messages
    FROM contact_timeline_summaries cts
    JOIN contact_summary cs ON cts.conversation_id = cs.conversation_id
    ORDER BY cs.total_messages DESC, cts.time_layer
''')

rows = c.fetchall()
print(f'共 {len(rows)} 条时间线摘要:\n')

current_name = None
for row in rows:
    if row[0] != current_name:
        current_name = row[0]
        print(f'\n【{row[0]}】')
    print(f'  [{row[1]}] {row[2][:80]}...' if row[2] and len(row[2]) > 80 else f'  [{row[1]}] {row[2]}')

# 统计分析覆盖情况
print('\n\n=== 分析覆盖情况 ===')
c.execute('SELECT COUNT(DISTINCT display_name) FROM contact_summary WHERE contact_type = \"personal\"')
total_contacts = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM contact_profiles')
analyzed_contacts = c.fetchone()[0]

c.execute('SELECT COUNT(DISTINCT display_name) FROM contact_timeline_summaries')
timeline_contacts = c.fetchone()[0]

print(f'总联系人: {total_contacts}人')
print(f'有深度档案: {analyzed_contacts}人 ({analyzed_contacts/total_contacts*100:.1f}%)')
print(f'有时间线摘要: {timeline_contacts}人 ({timeline_contacts/total_contacts*100:.1f}%)')
