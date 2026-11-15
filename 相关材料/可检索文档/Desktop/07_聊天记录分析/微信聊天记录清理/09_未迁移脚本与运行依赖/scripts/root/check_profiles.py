import sqlite3
import json

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看完整的联系人档案
print('=== 详细联系人档案 ===')
c.execute('SELECT display_name, relationship_type, closeness_score, communication_style, sentiment_balance, dominant_topics, core_tensions, shared_history, growth_trajectory FROM contact_profiles ORDER BY closeness_score DESC LIMIT 15')
rows = c.fetchall()
for row in rows:
    print(f'\n【{row[0]}】')
    print(f'  关系类型: {row[1]}')
    print(f'  亲密度: {row[2]}/10')
    print(f'  沟通风格: {row[3]}')
    print(f'  情感平衡: {row[4]}')
    print(f'  主要话题: {row[5]}')
    print(f'  核心张力: {row[6]}')
    print(f'  共同经历: {row[7]}')
    print(f'  成长轨迹: {row[8]}')

print('\n\n=== 沟通模式总结 ===')
c.execute('SELECT communication_style, COUNT(*) FROM contact_profiles GROUP BY communication_style')
for row in c.fetchall():
    print(f'{row[0]}: {row[1]}人')

print('\n=== 情感平衡分布 ===')
c.execute('SELECT sentiment_balance, COUNT(*) FROM contact_profiles GROUP BY sentiment_balance')
for row in c.fetchall():
    print(f'{row[0]}: {row[1]}人')
