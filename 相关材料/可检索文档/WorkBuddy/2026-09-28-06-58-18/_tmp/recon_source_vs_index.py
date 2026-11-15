# -*- coding: utf-8 -*-
"""源库(解密) vs 索引库 逐会话对账 —— 找漏条。

输出：
  1) 每个会话：源库行数 / 索引行数 / 差
  2) 索引缺失的 (session, server_id) 样本
  3) 索引缺失消息的 create_time 分布（判断是否集中在某时段）
"""
import hashlib
import sqlite3
import sys
import time
from pathlib import Path

DEC_ROOT = Path(r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted")
INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
DBS = ["message_0.db", "message_1.db", "biz_message_0.db", "biz_message_1.db", "biz_message_2.db"]

OUT = Path(r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\recon_out.txt")
lines = []


def log(s=""):
    print(s)
    lines.append(str(s))


# ---------- 1. 读索引 ----------
idx = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
idx_cnt = {}
idx_srv = {}   # sid -> set(server_id)
idx_ts = {}    # sid -> set(create_time)
for sid, n in idx.execute("select session_key, count(*) from messages group by 1"):
    idx_cnt[sid] = n
for sid, srv in idx.execute("select session_key, server_id from messages"):
    idx_srv.setdefault(sid, set()).add(srv)
for sid, ts in idx.execute("select session_key, ts from messages"):
    idx_ts.setdefault(sid, set()).add(ts)
log("索引库会话数 = %d, 消息 = %d" % (len(idx_cnt), sum(idx_cnt.values())))

# ---------- 2. 扫源库 ----------
src_cnt = {}
src_srv = {}
src_ts = {}
src_maxts = {}
missing_rows = []      # (sid, ts, server_id, local_id, local_type)
t0 = time.time()
for dbf in DBS:
    hits = list(DEC_ROOT.rglob(dbf))
    if not hits:
        log("  源库不存在: %s" % dbf)
        continue
    p = hits[0]
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
    md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values()}
    tabs = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg\\_%' ESCAPE '\\'")]
    n_tab = 0
    n_row = 0
    for t in tabs:
        sid = md5map.get(t[4:])
        if not sid:
            continue
        n_tab += 1
        try:
            rows = con.execute(
                'SELECT create_time, server_id, local_id, local_type FROM "%s"' % t).fetchall()
        except Exception:
            continue
        n_row += len(rows)
        src_cnt[sid] = src_cnt.get(sid, 0) + len(rows)
        s1 = src_srv.setdefault(sid, set())
        s2 = src_ts.setdefault(sid, set())
        mx = src_maxts.get(sid, 0)
        for ct, srv, lid, lt in rows:
            if srv:
                s1.add(srv)
            s2.add(ct)
            if ct > mx:
                mx = ct
        src_maxts[sid] = mx
    con.close()
    log("  %-20s 表 %d / 行 %d" % (dbf, n_tab, n_row))
log("源库扫描耗时 %.1f 秒" % (time.time() - t0))

# ---------- 3. 对比 ----------
log()
log("=" * 78)
log("一、逐会话行数对比（只列有差异的）")
log("=" * 78)
diffs = []
for sid, n in sorted(src_cnt.items(), key=lambda kv: -(kv[1] - idx_cnt.get(kv[0], 0))):
    m = idx_cnt.get(sid, 0)
    d = n - m
    if d != 0:
        diffs.append((d, sid, n, m))
for d, sid, n, m in diffs:
    log("  差 %+6d | 源 %7d | 索引 %7d | %s" % (d, n, m, sid))
log("  有差异会话数 = %d / 源库会话数 = %d" % (len(diffs), len(src_cnt)))

# ---------- 4. server_id 差集 ----------
log()
log("=" * 78)
log("二、索引缺失的 server_id（源库有、索引无）")
log("=" * 78)
tot_missing = 0
for sid in sorted(src_srv, key=lambda s: -len(src_srv[s] - idx_srv.get(s, set()))):
    miss = src_srv[sid] - idx_srv.get(sid, set())
    miss.discard(0)
    if not miss:
        continue
    tot_missing += len(miss)
    log("  %-34s 缺失 server_id = %d" % (sid, len(miss)))
log("  合计缺失 server_id = %d" % tot_missing)

# ---------- 5. ts 差集 ----------
log()
log("=" * 78)
log("三、索引缺失的 create_time（源库有、索引无）")
log("=" * 78)
tot_missts = 0
rows_missts = []
for sid in sorted(src_ts, key=lambda s: -len(src_ts[s] - idx_ts.get(s, set()))):
    miss = src_ts[sid] - idx_ts.get(sid, set())
    if not miss:
        continue
    tot_missts += len(miss)
    rows_missts.append((len(miss), sid, min(miss), max(miss)))
for c, sid, lo, hi in rows_missts[:40]:
    log("  %-34s 缺失时间戳 %5d 条 | %s ~ %s" % (
        sid, c,
        time.strftime('%Y-%m-%d %H:%M', time.localtime(lo)),
        time.strftime('%Y-%m-%d %H:%M', time.localtime(hi))))
log("  合计缺失时间戳 = %d" % tot_missts)

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n写出:", OUT)
