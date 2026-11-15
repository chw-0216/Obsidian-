import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看有哪些表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('=== 数据库表 ===')
for t in tables:
    print(t[0])

print()

# 查看标注数量
for table in ['aggressive_annotations', 'aggressive_message_annotations', 'aggressive_entities', 'aggressive_events']:
    try:
        c.execute(f'SELECT COUNT(*) FROM {table}')
        count = c.fetchone()[0]
        print(f'{table}: {count} 条')
    except Exception as e:
        print(f'{table}: 不存在或错误')

print()

# 查看一些标注内容
print('=== 最近的标注样本 ===')
c.execute('SELECT segment_id, created_at FROM aggressive_annotations ORDER BY created_at DESC LIMIT 10')
rows = c.fetchall()
for row in rows:
    print(f'片段ID: {row[0][:20]}... 时间: {row[1]}')
