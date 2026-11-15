# -*- coding: utf-8 -*-
"""检查分片间 local_id / server_id 是否可作稳定唯一键。只读。"""
import sqlite3, os, hashlib

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
SID = "25410000808@chatroom"
T = "Msg_" + hashlib.md5(SID.encode()).hexdigest()

for dbf in ("message_0.db", "message_1.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        n, lo, hi, sni, sxid = con.execute(
            f'SELECT COUNT(*), MIN(local_id), MAX(local_id), SUM(CASE WHEN server_id IS NULL OR server_id=0 THEN 1 ELSE 0 END), COUNT(DISTINCT server_id) FROM "{T}"'
        ).fetchone()
    except Exception as e:
        print(dbf, "无表", e); con.close(); continue
    print(f"{dbf}: 行 {n} | local_id {lo}..{hi} | server_id 为空 {sni} | 不同 server_id {sxid}")
    d = con.execute(f'SELECT COUNT(*) FROM (SELECT DISTINCT local_id FROM "{T}")').fetchone()[0]
    print(f"   local_id 唯一值 {d}  → {'local_id 可作键' if d == n else 'local_id 有重复（不可单独作键）'}")
    d2 = con.execute(f'SELECT COUNT(*) FROM (SELECT DISTINCT server_id FROM "{T}" WHERE server_id IS NOT NULL AND server_id<>0)').fetchone()[0]
    print(f"   server_id 非空唯一值 {d2}")
    con.close()
