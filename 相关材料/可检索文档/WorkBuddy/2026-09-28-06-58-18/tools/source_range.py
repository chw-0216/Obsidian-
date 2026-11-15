# -*- coding: utf-8 -*-
"""源库时间范围抽样 + 索引覆盖缺口定位。只读。"""
import sqlite3, os, hashlib, datetime, json

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
PAT = "name LIKE 'Msg\\_%' ESCAPE '\\'"

def ts(x):
    try:
        return datetime.datetime.fromtimestamp(int(x)).strftime("%Y-%m-%d")
    except Exception:
        return "?"

gmin, gmax = None, None
big = []
for dbf in ("message_0.db", "message_1.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    tabs = [r[0] for r in con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {PAT}")]
    for t in tabs:
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        if n < 500:
            continue
        mn, mx = con.execute(f'SELECT MIN(create_time),MAX(create_time) FROM "{t}"').fetchone()
        big.append((t, n, mn, mx))
        if mn and (gmin is None or mn < gmin): gmin = mn
        if mx and (gmax is None or mx > gmax): gmax = mx
    con.close()

print("=== 源库整体时间范围 ===")
print(f"  {ts(gmin)}  ~  {ts(gmax)}")

big.sort(key=lambda x: -x[1])
print(f"\n=== 源库最大 15 张表（>=500 行）===")
for t, n, mn, mx in big[:15]:
    sid = "?"
    print(f"  {t[:22]}  {n:>7} 行   {ts(mn)} ~ {ts(mx)}")

c = sqlite3.connect(f"file:{IDX}?mode=ro", uri=True)
cur = c.cursor()
cur.execute("SELECT session_key, COUNT(*) FROM messages GROUP BY session_key")
idx = dict(cur.fetchall())
c.close()

print(f"\n=== 源库 vs 索引（大表对照）===")
print(f"  {'表':<24}{'源库':>9}{'索引':>9}{'缺失':>9}")
for t, n, mn, mx in big[:15]:
    sid = None
    # 反查：表的 md5 后缀对应哪个会话
    con = None
    key = t[4:]
    # 用 Name2Id 反查太慢，直接扫索引的 session_key 做 md5 匹配
    for k in idx:
        if hashlib.md5(k.encode()).hexdigest() == key:
            sid = k
            break
    got = idx.get(sid, 0) if sid else 0
    print(f"  {(sid or t)[:24]:<24}{n:>9}{got:>9}{n-got:>9}")
