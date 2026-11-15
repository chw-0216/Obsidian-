import sqlite3
import json

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 查看联系人分析
print('=== 联系人分析汇总 ===')
try:
    c.execute('SELECT * FROM contact_summary LIMIT 10')
    rows = c.fetchall()
    if rows:
        # 获取列名
        c.execute('PRAGMA table_info(contact_summary)')
        cols = [col[1] for col in c.fetchall()]
        print('列:', cols)
        for row in rows:
            print(row)
    else:
        print('暂无联系人汇总数据')
except Exception as e:
    print(f'contact_summary表查询: {e}')

print()

# 查看联系人时间线摘要
print('=== 联系人时间线摘要 ===')
try:
    c.execute('SELECT * FROM contact_timeline_summaries LIMIT 5')
    rows = c.fetchall()
    if rows:
        c.execute('PRAGMA table_info(contact_timeline_summaries)')
        cols = [col[1] for col in c.fetchall()]
        print('列:', cols)
        for row in rows:
            print(row[:5], '...')
    else:
        print('暂无时间线摘要')
except Exception as e:
    print(f'contact_timeline_summaries表查询: {e}')

print()

# 查看联系人档案
print('=== 联系人档案 ===')
try:
    c.execute('SELECT * FROM contact_profiles LIMIT 5')
    rows = c.fetchall()
    if rows:
        c.execute('PRAGMA table_info(contact_profiles)')
        cols = [col[1] for col in c.fetchall()]
        print('列:', cols)
        for row in rows:
            print(row[:5], '...')
    else:
        print('暂无联系人档案')
except Exception as e:
    print(f'contact_profiles表查询: {e}')

print()

# 查看实体类型分布
print('=== 实体类型分布 ===')
c.execute('SELECT entity_type, COUNT(*) FROM aggressive_entities GROUP BY entity_type')
for row in c.fetchall():
    print(f'{row[0]}: {row[1]}个')

print()

# 查看事件类型分布
print('=== 事件类型分布 ===')
c.execute('SELECT event_type, COUNT(*) FROM aggressive_events GROUP BY event_type')
for row in c.fetchall():
    print(f'{row[0]}: {row[1]}个')
