# -*- coding: utf-8 -*-
"""只读：从解密源库核对贺伊飞会话（绕过索引去重/角色问题）"""
import sqlite3, hashlib, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message'
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
talker = 'hyf782877122'
tbl = 'Msg_' + hashlib.md5(talker.encode()).hexdigest()
print('table =', tbl)
for db in ('message_0.db','message_1.db'):
    p = BASE + '\\' + db
    try:
        c = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
        c.execute('PRAGMA query_only=ON')
        ok = c.execute("select name from sqlite_master where type='table' and name=?", (tbl,)).fetchone()
        if not ok:
            print(db, ': 无此表')
            continue
        cols = [x[1] for x in c.execute(f'pragma table_info("{tbl}")')]
        print(db, '列:', cols)
        rows = c.execute(f'select * from "{tbl}" order by CreateTime').fetchall()
        print(db, '行数:', len(rows))
        for r in rows:
            d = dict(zip(cols, r))
            st = d.get('CreateTime')
            typ = d.get('Type'); sub = d.get('SubType'); sender = d.get('IsSender')
            content = d.get('StrContent') or d.get('DisplayContent') or d.get('CompressContent') or ''
            if isinstance(content, bytes): content = f'<blob {len(content)}>'
            content = str(content).replace('\n','\\n')
            if len(content) > 400: content = content[:400]+'…'
            print(f'[{ts(st)}] type={typ}/{sub} isSender={sender} | {content}')
    except Exception as e:
        print(db, 'ERR', e)
