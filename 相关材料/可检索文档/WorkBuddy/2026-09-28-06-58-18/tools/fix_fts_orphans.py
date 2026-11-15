# -*- coding: utf-8 -*-
"""
清理 messages_fts 中的孤儿行（rowid 在 messages 里不存在）。

来源：index-incremental.py 的历史缺陷 —— ins_msg 用 INSERT OR IGNORE，
      而 ins_fts 无条件 executemany。当「解码升级导致 key 变化」时，
      messages 被唯一键 IGNORE，fts 却插入了新行 → 累积孤儿。
      （2026-10-09 实测 33 条，与历次 --reconcile 报告吻合）

先备份，再删除。孤儿行不影响检索正确性（messages 里无对应行），但会造成重复结果。
"""
import sqlite3, io, json, time, hashlib, sys
from pathlib import Path

INDEX = Path(r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite")
HERE = Path(__file__).parent
APPLY = "--apply" in sys.argv

log = io.open(HERE / "fix_fts_orphans_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); log.write(s + "\n")

con = sqlite3.connect(str(INDEX))
orphans = con.execute(
    "SELECT f.rowid, f.session_key, f.sender, f.content "
    "FROM messages_fts f LEFT JOIN messages m ON m.rowid = f.rowid "
    "WHERE m.rowid IS NULL").fetchall()
P(f"fts 孤儿行 : {len(orphans)}")
P("")
for rid, sid, sender, content in orphans[:40]:
    P(f"  rowid={rid:<8} {sid:<28} {str(content)[:60]!r}")

if not APPLY:
    P("")
    P("（dry-run；加 --apply 执行）")
else:
    bkdir = HERE / ("fts_orphan_backup_" + time.strftime("%Y%m%d_%H%M%S"))
    bkdir.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with io.open(bkdir / "orphans.jsonl", "w", encoding="utf-8") as f:
        for rid, sid, sender, content in orphans:
            line = json.dumps({"rowid": rid, "session_key": sid, "sender": sender,
                               "content": content}, ensure_ascii=False)
            f.write(line + "\n"); h.update(line.encode())
    (bkdir / "manifest.json").write_text(json.dumps({
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rows": len(orphans), "sha256_of_jsonl": h.hexdigest(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    P("")
    P(f"备份 -> {bkdir}  ({len(orphans)} 行, sha256={h.hexdigest()[:16]}...)")

    cur = con.cursor()
    cur.execute("DELETE FROM messages_fts WHERE rowid IN "
                "(SELECT f.rowid FROM messages_fts f LEFT JOIN messages m ON m.rowid=f.rowid "
                " WHERE m.rowid IS NULL)")
    P(f"已删除 {cur.rowcount} 行")
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    P("")
    P("复校：")
    P("  messages :", con.execute("select count(*) from messages").fetchone()[0])
    P("  fts      :", con.execute("select count(*) from messages_fts").fetchone()[0])
    P("  孤儿     :", con.execute("select count(*) from messages_fts f left join messages m on m.rowid=f.rowid where m.rowid is null").fetchone()[0])
    P("  内容不同 :", con.execute("select count(*) from messages m join messages_fts f on f.rowid=m.rowid where f.content<>m.content").fetchone()[0])

con.close()
log.close()
