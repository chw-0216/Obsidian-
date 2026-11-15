import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看token使用统计
print('=== Token使用统计 ===')
c.execute('SELECT SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM contact_profiles')
row = c.fetchone()
print(f'联系人档案: 输入{row[0]}tokens, 输出{row[1]}tokens, {row[2]}条记录')

c.execute('SELECT SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM contact_timeline_summaries')
row = c.fetchone()
print(f'时间线摘要: 输入{row[0]}tokens, 输出{row[1]}tokens, {row[2]}条记录')

c.execute('SELECT COUNT(*) FROM aggressive_annotations')
total = c.fetchone()[0]
print(f'\n已标注片段: {total}个')
print(f'剩余未标注: {6303 - total}个')

# 估算当前消耗
print('\n=== 当前消耗估算 ===')
# 假设每个片段平均消耗（基于119个片段）
avg_input = 1500  # 平均输入tokens
avg_output = 2000  # 平均输出tokens
total_input = total * avg_input * 3  # 3个Pass
total_output = total * avg_output * 3
print(f'已标注{total}个片段估算:')
print(f'  输入tokens: ~{total_input:,}')
print(f'  输出tokens: ~{total_output:,}')
print(f'  总tokens: ~{total_input + total_output:,}')

# 全量估算
full_input = 6303 * avg_input * 3
full_output = 6303 * avg_output * 3
print(f'\n全量6303个片段估算:')
print(f'  输入tokens: ~{full_input:,}')
print(f'  输出tokens: ~{full_output:,}')
print(f'  总tokens: ~{full_input + full_output:,}')
print(f'  相当于当前的: {6303/total:.0f}倍')
