import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看时间线摘要表结构
print('=== 时间线摘要表结构 ===')
c.execute('PRAGMA table_info(contact_timeline_summaries)')
cols = c.fetchall()
for col in cols:
    print(f'{col[1]}: {col[2]}')

print()

# 查看已有时间线摘要的联系人
print('=== 已有时间线摘要的联系人 ===')
c.execute('''
    SELECT 
        cs.display_name,
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
    summary = row[2][:80] + '...' if row[2] and len(row[2]) > 80 else row[2]
    print(f'  [{row[1]}] {summary}')

# 统计分析覆盖情况
print('\n\n=== 分析覆盖情况 ===')
c.execute('SELECT COUNT(DISTINCT display_name) FROM contact_summary WHERE contact_type = \"personal\"')
total_contacts = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM contact_profiles')
analyzed_contacts = c.fetchone()[0]

c.execute('SELECT COUNT(DISTINCT cs.display_name) FROM contact_timeline_summaries cts JOIN contact_summary cs ON cts.conversation_id = cs.conversation_id')
timeline_contacts = c.fetchone()[0]

print(f'总联系人: {total_contacts}人')
print(f'有深度档案: {analyzed_contacts}人 ({analyzed_contacts/total_contacts*100:.1f}%)')
print(f'有时间线摘要: {timeline_contacts}人 ({timeline_contacts/total_contacts*100:.1f}%)')

# 统计消息覆盖
c.execute('SELECT SUM(total_messages) FROM contact_summary WHERE contact_type = \"personal\"')
total_msgs = c.fetchone()[0]

c.execute('''
    SELECT SUM(cs.total_messages) 
    FROM contact_profiles cp
    JOIN contact_summary cs ON cp.conversation_id = cs.conversation_id
''')
analyzed_msgs = c.fetchone()[0]

print(f'\n消息覆盖:')
print(f'总消息: {total_msgs:,}条')
print(f'已分析联系人的消息: {analyzed_msgs:,}条 ({analyzed_msgs/total_msgs*100:.1f}%)')
