# -*- coding: utf-8 -*-
"""量化：索引库相对源库的覆盖率。只读。"""
import sqlite3, os, hashlib, datetime

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
PAT = "name LIKE 'Msg\\_%' ESCAPE '\\'"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

src_total = 0
src_min, src_max = None, None
per_db = []
for dbf in ("message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    tabs = [r[0] for r in con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {PAT}")]
    n = 0
    for t in tabs:
        n += con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    src_total += n
    per_db.append((dbf, len(tabs), n))
    con.close()

print("=== 源库（解密后）===")
for dbf, nt, n in per_db:
    print(f"  {dbf:<20} {nt:>5} 表  {n:>9} 行")
print(f"  {'合计':<20} {'':>5}     {src_total:>9} 行")

c = sqlite3.connect(f"file:{IDX}?mode=ro", uri=True)
cur = c.cursor()
cur.execute("SELECT COUNT(*) FROM messages")
idx_n = cur.fetchone()[0]
cur.execute("SELECT MIN(ts),MAX(ts) FROM messages")
a, b = cur.fetchone()
c.close()

print("\n=== 索引库 ===")
print(f"  {'messages':<20} {'':>5}     {idx_n:>9} 行")
print(f"  时间范围 {datetime.datetime.fromtimestamp(a)} ~ {datetime.datetime.fromtimestamp(b)}")
print(f"\n  ★ 覆盖率 = {idx_n}/{src_total} = {100.0*idx_n/src_total:.1f}%")
print(f"  ★ 未进索引 ≈ {src_total-idx_n} 行")
