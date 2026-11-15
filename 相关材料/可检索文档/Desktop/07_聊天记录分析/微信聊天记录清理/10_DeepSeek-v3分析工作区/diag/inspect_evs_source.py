import sqlite3
db = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\wechat-analysis-v3.sqlite3"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row
# 1) 这 2 个 evs 的时间窗
for evs in ("evs_31ee09e464ed1148", "evs_36fb1961def13dc1"):
    j = c.execute("SELECT event_id, start_ts, end_ts, title FROM _v3_event_judgments WHERE event_id=?", (evs,)).fetchone()
    print(evs, "| window:", j["start_ts"], "->", j["end_ts"], "|", j["title"])
# 2) 候选表里 title 含"舒哥"且含"聚/约"、或含"机票/托运/跨国"的候选
print("---- candidates 含 舒哥+聚会/约 ----")
rows = c.execute("SELECT candidate_id, title, start_ts, end_ts, status FROM _v3_event_candidates WHERE title LIKE '%舒哥%' AND (title LIKE '%聚%' OR title LIKE '%约%' OR title LIKE '%见面%')").fetchall()
for r in rows:
    print("  ", r["candidate_id"], "|", r["title"], "|", r["start_ts"], "->", r["end_ts"], "|", r["status"])
print("---- candidates 含 机票/托运/跨国 ----")
rows = c.execute("SELECT candidate_id, title, start_ts, end_ts, status FROM _v3_event_candidates WHERE title LIKE '%机票%' OR title LIKE '%托运%' OR title LIKE '%跨国%'").fetchall()
for r in rows:
    print("  ", r["candidate_id"], "|", r["title"], "|", r["start_ts"], "->", r["end_ts"], "|", r["status"])
# 3) review 表里有没有这 2 个事件的记录
print("---- _v3_event_review 里候选分布 ----")
rows = c.execute("SELECT candidate_id, user_verdict, COUNT(*) n FROM _v3_event_review GROUP BY candidate_id ORDER BY candidate_id").fetchall()
for r in rows:
    print("  ", r["candidate_id"], "|", r["user_verdict"], "| n=", r["n"])
