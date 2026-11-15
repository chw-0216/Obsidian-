import sqlite3

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 检查segments表结构
print('=== segments表结构 ===')
c.execute('PRAGMA table_info(segments)')
cols = c.fetchall()
for col in cols:
    print(f'{col[1]}: {col[2]}')

print()

# 检查一些数据
print('=== segments样本数据 ===')
c.execute('SELECT * FROM segments LIMIT 3')
rows = c.fetchall()
for row in rows:
    print(row[:5], '...')
