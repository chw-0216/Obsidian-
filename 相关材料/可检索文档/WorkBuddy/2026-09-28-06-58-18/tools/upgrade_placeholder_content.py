# -*- coding: utf-8 -*-
"""
升级索引库中的「占位符内容」。

背景（2026-10-09 排查）：
  索引里 content 形如 `[type244813135921]` 的行，是**旧版解码器**写入的：
  当时 decode/clean_xml 解不出文本 → 落到 `placeholder or f"[type{lt}]"`。
  后来解码逻辑升级，现在能解出真实文本（如笑一「跟家人就是这样的 | 我也有情绪问题」），
  但 (session_key, server_id) 唯一键让 INSERT OR IGNORE 永远修不上 → 内容永久停在占位符。
  → 症状：每次 --reconcile 都报「新增 N 条 / 并入 +0」。

本脚本：按 (sid, server_id) 从源库重算文本，对「新文本有实质内容」的行执行 UPDATE。
  同时更新 messages 与 messages_fts（rowid 已验证 65/65 对齐）。

用法：
  python upgrade_placeholder_content.py            # dry-run
  python upgrade_placeholder_content.py --apply    # 落库（先自动备份）
"""
import sqlite3, hashlib, time, io, json, sys, re, importlib.util
from pathlib import Path

SPEC = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index-incremental.py"
spec = importlib.util.spec_from_file_location("idxinc", SPEC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

DEC_ROOT, INDEX, DBS = m.DEC_ROOT, m.INDEX, m.DBS
NOISE, MY_ROOT, MY = m.NOISE_SESSIONS, m.MY_ROOT, m.MY

APPLY = "--apply" in sys.argv
HERE = Path(__file__).parent

log = io.open(HERE / "upgrade_placeholder_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); log.write(s + "\n")

t0 = time.time()
idx = sqlite3.connect(str(INDEX))

# ---------- 1) 取目标行 ----------
targets = idx.execute(
    "SELECT rowid, session_key, server_id, ts, content, COALESCE(sender,''), type "
    "FROM messages WHERE content LIKE '[type%]'").fetchall()
P(f"目标行（content 形如 [type...]）: {len(targets)}")

by_sid = {}
for rid, sid, srv, ts, old, sender, typ in targets:
    by_sid.setdefault(sid, []).append((rid, srv, ts, old, sender, typ))

# ---------- 2) 扫源库，按 (sid, server_id) 重算文本 ----------
fresh = {}      # (sid, srv) -> text
for dbf in DBS:
    hits = list(DEC_ROOT.rglob(dbf))
    if not hits:
        continue
    con = sqlite3.connect(f"file:{hits[0]}?mode=ro", uri=True)
    idmap = {r[0]: r[1] for r in con.execute("SELECT rowid, user_name FROM Name2Id")}
    md5map = {hashlib.md5(n.encode()).hexdigest(): n for n in idmap.values()}
    tabs = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg\\_%' ESCAPE '\\'")]
    for t in tabs:
        sid = md5map.get(t[4:])
        if not sid or sid not in by_sid or sid in NOISE:
            continue
        want = {x[1] for x in by_sid[sid]}
        is_group = sid.endswith("@chatroom")
        try:
            rows = con.execute(
                f'SELECT create_time, real_sender_id, local_type, message_content, server_id '
                f'FROM "{t}"').fetchall()
        except Exception:
            continue
        for ts, rsid, ltype, blob, srv in rows:
            srv = int(srv or 0)
            if srv not in want:
                continue
            lt = int(ltype or 0)
            wf_type, placeholder = m.map_type(lt)
            text = m.clean_xml(m.decode_content(blob))
            if not m.printable(text):
                text = ""
            if not text:
                text = placeholder or f"[type{lt}]"
            if is_group:
                mm = m.SENDER_PREFIX.match(text)
                if mm:
                    text = text[mm.end():].strip() or text
            fresh[(sid, srv)] = (ts, lt, text)
    con.close()

P(f"源库匹配到 {len(fresh)} 条")

# ---------- 3) 比对 ----------
plan = []
skip_same = skip_empty = skip_dirty = 0
for sid, items in by_sid.items():
    for rid, srv, ts, old, sender, typ in items:
        got = fresh.get((sid, srv))
        if not got:
            continue
        nts, nlt, ntext = got
        if nts != ts:
            continue                       # ts 不一致，保守跳过
        if ntext == old:
            skip_same += 1
            continue
        if ntext.startswith("[type") or not ntext.strip():
            skip_empty += 1
            continue                       # 新版也解不出 → 保持占位符
        # ★ 2026-10-09：这类消息源库开头带「转发元数据前缀」，clean_xml 因不以 <msg/<?xml
        #   开头而未走 XML 分支 → 解出的是垃圾（`... false -1 -1 3 ... &lt;?xml versi`）。
        #   与其用垃圾覆盖占位符，不如保留原样。
        if re.search(r"&(?:lt|gt|amp|quot|#\d+);", ntext):
            skip_dirty += 1
            continue
        plan.append((rid, sid, srv, ts, old, ntext, sender))

P(f"")
P(f"可升级 : {len(plan)} 条")
P(f"新文本与旧相同（新版也解不出）: {skip_same} 条")
P(f"新文本仍是占位符/空        : {skip_empty} 条")
P(f"新文本含未洗净的 XML 实体（跳过，保留原占位符）: {skip_dirty} 条")
P("")
for rid, sid, srv, ts, old, ntext, sender in sorted(plan, key=lambda x: x[3]):
    P(f"  [{time.strftime('%m-%d %H:%M', time.localtime(ts))}] {sid}")
    P(f"      {old}  ->  {ntext[:110]}")

# ---------- 4) 备份 + 落库 ----------
if not APPLY:
    P("")
    P("（dry-run，未落库；加 --apply 执行）")
else:
    bkdir = HERE / ("placeholder_backup_" + time.strftime("%Y%m%d_%H%M%S"))
    bkdir.mkdir(parents=True, exist_ok=True)
    with io.open(bkdir / "rows.jsonl", "w", encoding="utf-8") as f:
        h = hashlib.sha256()
        for rid, sid, srv, ts, old, ntext, sender in plan:
            line = json.dumps({"rowid": rid, "session_key": sid, "server_id": srv, "ts": ts,
                               "old_content": old, "new_content": ntext, "sender": sender},
                              ensure_ascii=False)
            f.write(line + "\n"); h.update(line.encode())
    (bkdir / "manifest.json").write_text(json.dumps({
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rows": len(plan), "sha256_of_jsonl": h.hexdigest(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    P("")
    P(f"备份 -> {bkdir}  ({len(plan)} 行, sha256={h.hexdigest()[:16]}...)")

    cur = idx.cursor()
    for rid, sid, srv, ts, old, ntext, sender in plan:
        cur.execute("UPDATE messages SET content=? WHERE rowid=?", (ntext, rid))
        cur.execute("UPDATE messages_fts SET content=? WHERE rowid=?", (ntext, rid))
    idx.commit()
    P(f"已更新 {len(plan)} 行（messages + messages_fts）")

idx.close()
P("")
P(f"耗时 {time.time()-t0:.1f} 秒")
log.close()
