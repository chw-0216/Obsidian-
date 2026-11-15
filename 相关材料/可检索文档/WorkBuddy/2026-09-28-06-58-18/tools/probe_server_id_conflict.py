# -*- coding: utf-8 -*-
"""
诊断：--reconcile 每次报「新增 10 条 / 7 个会话」但并入 +0 —— 是否真丢数据？

原理：
  index-incremental.py 的去重键 = (sid, ts, text[:80], sender)
  插入用 INSERT OR IGNORE，唯一键 = ux_msg(session_key, server_id)
  → 若源库某行的 (sid, server_id) 已被索引里「另一条内容不同」的行占用，
    该行会被静默忽略（既不计入 +N，也不再出现在下轮 seen 里）。

本脚本统计：源库里同一 (sid, server_id) 出现 >1 次的情况。
  这些就是「结构性无法进索引」的行数上限。
"""
import sqlite3, hashlib, time, sys, io
from pathlib import Path
from collections import Counter

DEC_ROOT = Path(r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
DBS = ["message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"]

NOISE = {"25410000808@chatroom", "18440588614@chatroom"}

out = io.open(Path(__file__).parent / "probe_srv_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")

t0 = time.time()
cnt = Counter()          # (sid, server_id) -> 行数
total_rows = 0
no_srv_col = 0

for dbf in DBS:
    hits = list(DEC_ROOT.rglob(dbf))
    if not hits:
        continue
    p = hits[0]
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
    md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values()}
    tabs = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg\\_%' ESCAPE '\\'")]
    cols = None
    for t in tabs:
        sid = md5map.get(t[4:])
        if not sid:
            continue
        if sid in NOISE:
            continue
        try:
            if cols is None:
                cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")')]
            if "server_id" not in cols:
                no_srv_col += 1
                continue
            for (srv,) in con.execute(f'SELECT server_id FROM "{t}"'):
                cnt[(sid, int(srv or 0))] += 1
                total_rows += 1
        except Exception as e:
            continue
    con.close()
    P(f"  {dbf}: 累计 {total_rows} 行")

dups = {k: v for k, v in cnt.items() if v > 1}
extra = sum(v - 1 for v in dups.values())

P("")
P("=" * 70)
P(f"源库（排除两个噪音群）可统计行数 : {total_rows}")
P(f"无 server_id 列的表数             : {no_srv_col}")
P(f"不同 (sid, server_id) 组合数      : {len(cnt)}")
P(f"其中出现 >1 次的组合数            : {len(dups)}")
P(f"★ 因 server_id 冲突而「结构上放不进索引」的额外行数 : {extra}")
P("=" * 70)

# 按会话聚合，看集中在哪
by_sess = Counter()
for (sid, srv), v in dups.items():
    by_sess[sid] += v - 1
P("")
P("冲突最多的 15 个会话：")
for sid, v in by_sess.most_common(15):
    P(f"  {v:>6}  {sid}")

# 看 server_id 的取值分布
srv_dist = Counter()
for (sid, srv), v in dups.items():
    srv_dist[srv] += v - 1
P("")
P("冲突行按 server_id 值分布（前 10）：")
for srv, v in srv_dist.most_common(10):
    P(f"  server_id={srv:<12} {v:>6} 行")

P("")
P(f"耗时 {time.time()-t0:.1f} 秒")
out.close()
