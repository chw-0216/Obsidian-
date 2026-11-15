# -*- coding: utf-8 -*-
"""按会话计算「源库 vs 索引」缺口，判断缺口是否集中在少数大群。只读。"""
import sqlite3, os, hashlib, datetime

DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
PAT = "name LIKE 'Msg\\_%' ESCAPE '\\'"

src = {}          # session_id -> 行数
name2id = {}      # md5 -> session_id

for dbf in ("message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"):
    p = os.path.join(DEC, dbf)
    if not os.path.exists(p):
        continue
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        for rid, un in con.execute("SELECT rowid, user_name FROM Name2Id"):
            if un:
                name2id[hashlib.md5(un.encode()).hexdigest()] = un
    except Exception:
        pass
    tabs = [r[0] for r in con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {PAT}")]
    for t in tabs:
        sid = name2id.get(t[4:])
        if not sid:
            continue
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        src[sid] = src.get(sid, 0) + n
    con.close()

c = sqlite3.connect(f"file:{IDX}?mode=ro", uri=True)
idx = dict(c.execute("SELECT session_key, COUNT(*) FROM messages GROUP BY session_key").fetchall())
c.close()

def kind(k):
    if k.endswith("@chatroom"): return "群聊"
    if k.startswith("gh_"): return "公众号"
    if k.endswith("@openim"): return "企业微信"
    if k == "filehelper": return "filehelper"
    return "私聊"

rows = []
for sid, n in src.items():
    g = idx.get(sid, 0)
    rows.append((sid, kind(sid), n, g, n - g))
rows.sort(key=lambda x: -x[4])

src_tot = sum(r[2] for r in rows)
idx_tot = sum(r[3] for r in rows)
gap_tot = sum(r[4] for r in rows)
print(f"源库(可映射) {src_tot} 行 | 索引(这些会话) {idx_tot} 行 | 缺口 {gap_tot} 行")
print(f"覆盖率 {100.0*idx_tot/max(src_tot,1):.1f}%")
print()
print("=== 缺口最大的 12 个会话 ===")
print(f"  {'会话':<30}{'类型':<8}{'源库':>9}{'索引':>9}{'缺口':>9}{'占缺口':>8}")
for sid, kd, n, g, d in rows[:12]:
    print(f"  {sid[:30]:<30}{kd:<8}{n:>9}{g:>9}{d:>9}{100.0*d/gap_tot:>7.1f}%")
print()
top2 = sum(r[4] for r in rows[:2])
top10 = sum(r[4] for r in rows[:10])
print(f"★ 前 2 个会话占全部缺口 {100.0*top2/gap_tot:.1f}%")
print(f"★ 前 10 个会话占全部缺口 {100.0*top10/gap_tot:.1f}%")
print()
print("=== 按类型汇总 ===")
agg = {}
for sid, kd, n, g, d in rows:
    a = agg.setdefault(kd, [0, 0])
    a[0] += n; a[1] += g
for kd, (n, g) in sorted(agg.items(), key=lambda x: -x[1][0]):
    print(f"  {kd:<10} 源库 {n:>8}  索引 {g:>8}  覆盖 {100.0*g/max(n,1):>5.1f}%")
print()
print("=== 剔除前 2 大群后 ===")
rest_src = src_tot - rows[0][2] - rows[1][2]
rest_idx = idx_tot - rows[0][3] - rows[1][3]
print(f"  源库 {rest_src} | 索引 {rest_idx} | 覆盖 {100.0*rest_idx/max(rest_src,1):.1f}%")
