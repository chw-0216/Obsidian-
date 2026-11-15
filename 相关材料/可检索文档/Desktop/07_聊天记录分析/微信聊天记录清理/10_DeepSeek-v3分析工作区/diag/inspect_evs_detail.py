import sqlite3
db = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\wechat-analysis-v3.sqlite3"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
for evs in ("evs_31ee09e464ed1148", "evs_36fb1961def13dc1"):
    print("=" * 60)
    print(evs)
    j = c.execute("SELECT * FROM _v3_event_judgments WHERE event_id=?", (evs,)).fetchone()
    if j:
        print("  judgment keys:", [k for k in j.keys()])
        print("  title:", j["title"])
        print("  roles_json:", j["roles_json"])
        print("  note:", j["note"])
    ev = c.execute("SELECT COUNT(*) n FROM _v3_event_evidence WHERE candidate_id=?", (evs,)).fetchone()["n"]
    ct = c.execute("SELECT COUNT(*) n FROM _v3_event_contacts WHERE candidate_id=?", (evs,)).fetchone()["n"]
    print("  evidence rows for", evs, ":", ev)
    print("  contacts rows for", evs, ":", ct)
    # 是否有别的候选指向这个事件的标题/内容？
    print("  all evidence candidate_ids containing 'evs':")
    rows = c.execute("SELECT DISTINCT candidate_id FROM _v3_event_evidence WHERE candidate_id LIKE 'evs_%'").fetchall()
    print("   ", [r["candidate_id"] for r in rows])
    print("  all contacts candidate_ids containing 'evs':")
    rows = c.execute("SELECT DISTINCT candidate_id FROM _v3_event_contacts WHERE candidate_id LIKE 'evs_%'").fetchall()
    print("   ", [r["candidate_id"] for r in rows])
