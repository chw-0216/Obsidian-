# -*- coding: utf-8 -*-
"""
捞实 --reconcile 每次报的「新增 10 条 / 7 个会话」到底是什么。

做法：完全复现 index-incremental.py 的 reconcile 判定
  1) 预载 seen = (session_key, ts, substr(content,1,80), sender)
  2) 扫源库，找 key not in seen 的行 → 这就是被计入「新增」的
  3) 对每条，查索引里 (session_key, server_id) 已有的行 → 对比内容，判断是不是内容漂移
"""
import sqlite3, hashlib, time, io, importlib.util
from pathlib import Path

SPEC = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index-incremental.py"
spec = importlib.util.spec_from_file_location("idxinc", SPEC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

DEC_ROOT, INDEX, DBS = m.DEC_ROOT, m.INDEX, m.DBS
NOISE = m.NOISE_SESSIONS
MY_ROOT = m.MY_ROOT

out = io.open(Path(__file__).parent / "probe_reconcile10_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")

t0 = time.time()
idx = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)

# ---- 1) 预载 seen（reconcile 模式：全量）----
seen = set()
for sk, ts, ct, sd in idx.execute(
        "SELECT session_key, ts, substr(content,1,80), COALESCE(sender,'') FROM messages"):
    seen.add((sk, ts, ct, sd))
P(f"预载 seen: {len(seen)} 条")

# ---- 2) 扫源库找差异 ----
gaps = []
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
    for t in tabs:
        sid = md5map.get(t[4:])
        if not sid or sid in NOISE:
            continue
        is_group = sid.endswith("@chatroom")
        try:
            rows = con.execute(
                f'SELECT create_time, real_sender_id, local_type, message_content, local_id, server_id '
                f'FROM "{t}"').fetchall()
        except Exception:
            continue
        for r in rows:
            ts, rsid, ltype, blob = r[0], r[1], r[2], r[3]
            lid = int(r[4] or 0); srv = int(r[5] or 0)
            lt = int(ltype or 0)
            wf_type, placeholder = m.map_type(lt)
            text = m.clean_xml(m.decode_content(blob))
            if not m.printable(text):
                text = ""
            if not text:
                text = placeholder or f"[type{lt}]"
            sender = ""
            if is_group:
                mm = m.SENDER_PREFIX.match(text)
                if mm:
                    sender = mm.group(1); text = text[mm.end():].strip() or text
                elif rsid and (idmap.get(rsid) or "").startswith(MY_ROOT):
                    sender = "我"
            else:
                who = (idmap.get(rsid) or "") if rsid else ""
                if who.startswith(MY_ROOT) or who == m.MY:
                    sender = "我"
                elif who and not who.endswith("@chatroom"):
                    sender = who
                else:
                    sender = sid
            key = (sid, ts, text[:80], sender)
            if key not in seen:
                gaps.append((dbf, sid, ts, lt, sender, srv, lid, text))
    con.close()

P(f"")
P(f"★ key not in seen 的行数 : {len(gaps)}")
P("")

for i, (dbf, sid, ts, lt, sender, srv, lid, text) in enumerate(gaps, 1):
    P("=" * 74)
    P(f"[{i}] {dbf}  sid={sid}")
    P(f"    ts={ts}  ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))})  local_type={lt}  sender={sender}")
    P(f"    server_id={srv}  local_id={lid}")
    P(f"    text[:80]={text[:80]!r}")
    # 查索引里同 (sid, server_id)
    row = idx.execute(
        "SELECT ts, role, sender, type, substr(content,1,120), local_id FROM messages "
        "WHERE session_key=? AND server_id=?", (sid, srv)).fetchone()
    if row:
        P(f"    ★ 索引里已占位: ts={row[0]} role={row[1]} sender={row[2]} type={row[3]} local_id={row[5]}")
        P(f"        content={row[4]!r}")
        same_ts = (row[0] == ts)
        P(f"        → 同 ts? {same_ts}   （同 ts = 内容漂移；不同 ts = 真·两条消息撞同一 server_id）")
    else:
        P(f"    ★ 索引里无同 (sid, server_id) 的行 → 插入本应成功，需查其它原因")

P("")
P(f"耗时 {time.time()-t0:.1f} 秒")
out.close()
