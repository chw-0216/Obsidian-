import sqlite3, json
db = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row

print("=== 标注总量 ===")
rows = c.execute("SELECT status, COUNT(*) n FROM v3_annotations GROUP BY status").fetchall()
for r in rows:
    print(" ", r["status"], r["n"])
total_seg = c.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
done_seg = c.execute("SELECT COUNT(DISTINCT segment_id) FROM v3_annotations WHERE status='success'").fetchone()[0]
print(f"\n=== 覆盖进度: {done_seg}/{total_seg} 片段已标注 ({done_seg/total_seg:.1%}) ===")

print("\n=== 消息级标注 ===")
n = c.execute("SELECT COUNT(*) FROM v3_message_annotations").fetchone()[0]
print("  v3_message_annotations:", n)

print("\n=== 两轮运行(meta)===")
for r in c.execute("SELECT run_id, status, started_at, finished_at FROM v3_run_meta ORDER BY started_at").fetchall():
    print(" ", r["run_id"], "|", r["status"], "|", (r["started_at"] or "")[:19], "->", (r["finished_at"] or "")[:19])

print("\n=== 标注了哪些会话(TOP15,按消息标注数)===")
rows = c.execute("""
    SELECT m.display_name, COUNT(DISTINCT ma.message_id) msgs, COUNT(DISTINCT ma.segment_id) segs
    FROM v3_message_annotations ma
    LEFT JOIN conversations m ON m.id = ma.conversation_id
    GROUP BY ma.conversation_id ORDER BY msgs DESC LIMIT 15
""").fetchall()
for r in rows:
    print(f"  {r['display_name'] or '(未知会话)'}: {r['msgs']} 条消息 / {r['segs']} 片段")

print("\n=== 主题分布(TOP10,按片段 topic)===")
rows = c.execute("""
    SELECT json_extract(result_json,'$.topic') topic, COUNT(*) n
    FROM v3_annotations WHERE status='success'
    GROUP BY topic ORDER BY n DESC LIMIT 10
""").fetchall()
for r in rows:
    t = (r["topic"] or "(空)")[:30]
    print(f"  {t}: {r['n']}")

print("\n=== 实体/事件/关系信号 累计 ===")
q = c.execute("""
    SELECT
      SUM(json_array_length(result_json,'$.entities')) entities,
      SUM(json_array_length(result_json,'$.events')) events,
      SUM(json_array_length(result_json,'$.relationship_signals')) relsigs,
      SUM(json_array_length(result_json,'$.requests')) requests,
      SUM(json_array_length(result_json,'$.commitments')) commitments,
      SUM(json_array_length(result_json,'$.memory_candidates')) memcand
    FROM v3_annotations WHERE status='success'
""").fetchone()
print("  实体:", q["entities"] or 0, "| 事件:", q["events"] or 0, "| 关系信号:", q["relsigs"] or 0)
print("  请求:", q["requests"] or 0, "| 承诺:", q["commitments"] or 0, "| 记忆候选:", q["memcand"] or 0)

print("\n=== importance 分布 ===")
rows = c.execute("SELECT importance, COUNT(*) n FROM v3_annotations WHERE status='success' GROUP BY importance ORDER BY n DESC LIMIT 8").fetchall()
for r in rows:
    print("  importance =", r["importance"], ":", r["n"])

print("\n=== 高价值片段示例(TOP3 by confidence×importance)===")
rows = c.execute("""
    SELECT segment_id, confidence, importance,
           json_extract(result_json,'$.topic') topic,
           json_extract(result_json,'$.summary') summary
    FROM v3_annotations WHERE status='success' AND importance IS NOT NULL
    ORDER BY importance DESC, confidence DESC LIMIT 3
""").fetchall()
for r in rows:
    print(f"  [{r['segment_id'][:20]}...] imp={r['importance']} conf={r['confidence']} topic={r['topic']}")
    s = (r["summary"] or "")[:80]
    print(f"    摘要: {s}")
