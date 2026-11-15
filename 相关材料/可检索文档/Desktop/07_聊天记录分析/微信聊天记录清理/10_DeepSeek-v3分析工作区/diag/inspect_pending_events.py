import sqlite3, sys, json
db = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\wechat-analysis-v3.sqlite3"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
rows = c.execute("SELECT event_id, source_candidate_ids, title, keep_recommendation FROM _v3_event_judgments WHERE event_id LIKE 'evs_%'").fetchall()
for r in rows:
    print(r["event_id"], "| src=", r["source_candidate_ids"], "| keep=", r["keep_recommendation"], "|", (r["title"] or "")[:40])
print("---- candidates referenced ----")
for r in rows:
    ids = json.loads(r["source_candidate_ids"] or "[]")
    for cid in ids:
        row = c.execute("SELECT 1 FROM _v3_event_candidates WHERE candidate_id=?", (cid,)).fetchone()
        print("  ", cid, "-> exists in candidates:", bool(row))
