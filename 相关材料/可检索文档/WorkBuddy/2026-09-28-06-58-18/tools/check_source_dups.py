# -*- coding: utf-8 -*-
"""确认重复来自源头（解密库）还是索引层。只读。"""
import sqlite3, os, hashlib

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
PAT = "name LIKE 'Msg\\_%' ESCAPE '\\'"

for dbf in ("message_0.db", "message_1.db", "biz_message_0.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        print(dbf, "不存在")
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    tabs = [r[0] for r in con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {PAT}")]
    tot = dup = 0
    for t in tabs:
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        d = con.execute(
            f'SELECT COUNT(*) FROM (SELECT DISTINCT create_time,real_sender_id,local_type,local_id FROM "{t}")'
        ).fetchone()[0]
        tot += n
        dup += n - d
    print(f"=== {dbf}: {len(tabs)} 张表 | 行 {tot} | 源库内重复 {dup}")
    con.close()

sid = "25410000808@chatroom"
t = "Msg_" + hashlib.md5(sid.encode()).hexdigest()
print("\n目标表:", t)
for dbf in ("message_0.db", "message_1.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        d = con.execute(
            f'SELECT COUNT(*) FROM (SELECT DISTINCT create_time,real_sender_id,local_type,local_id FROM "{t}")'
        ).fetchone()[0]
        print(f"  {dbf}: 源库总 {n} | 去重 {d} | 源库内重复 {n-d}")
    except Exception as e:
        print(f"  {dbf}: 不在该库")
    con.close()
