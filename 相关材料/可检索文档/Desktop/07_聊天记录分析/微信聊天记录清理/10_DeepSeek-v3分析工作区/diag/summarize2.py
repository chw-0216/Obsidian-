import sqlite3, json
db = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
c.row_factory = sqlite3.Row

print("=== 标注了哪些会话(TOP15,按片段数,经 segments 关联) ===")
rows = c.execute("""
    SELECT cv.display_name, COUNT(DISTINCT a.segment_id) segs
    FROM v3_annotations a
    JOIN segments s ON s.id = a.segment_id
    LEFT JOIN conversations cv ON cv.id = s.conversation_id
    WHERE a.status='success'
    GROUP BY s.conversation_id ORDER BY segs DESC LIMIT 15
""").fetchall()
for r in rows:
    print(f"  {r['display_name'] or chr(40)+'未知'+chr(41)}: {r['segs']} 片段")

print("\n=== 主题分布 TOP10 ===")
rows = c.execute("""
    SELECT json_extract(result_json,'$.topic') topic, COUNT(*) n
    FROM v3_annotations WHERE status='success'
    GROUP BY topic ORDER BY n DESC LIMIT 10
""").fetchall()
for r in rows:
    print(f"  {(r['topic'] or '(空)')[:36]}: {r['n']}")

print("\n=== 消息级标注维度分布 ===")
for col in ("content_function", "intent", "is_request", "is_commitment", "is_boundary"):
    rows = c.execute(f"SELECT {col} v, COUNT(*) n FROM v3_message_annotations GROUP BY v ORDER BY n DESC LIMIT 5").fetchall()
    label = {"content_function":"内容功能","intent":"意图","is_request":"是否请求","is_commitment":"是否承诺","is_boundary":"是否边界"}[col]
    top = ", ".join(f"{r['v']}={r['n']}" for r in rows)
    print(f"  {label}: {top}")

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

print("\n=== 高重要度片段示例 TOP3 ===")
rows = c.execute("""
    SELECT a.segment_id, a.importance, a.confidence,
           json_extract(a.result_json,'$.topic') topic,
           json_extract(a.result_json,'$.summary') summary
    FROM v3_annotations a WHERE a.status='success' AND a.importance IS NOT NULL
    ORDER BY a.importance DESC, a.confidence DESC LIMIT 3
""").fetchall()
for r in rows:
    print(f"  imp={r['importance']} conf={r['confidence']} topic={(r['topic'] or '')[:24]}")
    print(f"    摘要: {(r['summary'] or '')[:76]}")

print("\n=== Token 消耗(按 run)===")
rows = c.execute("SELECT run_id, COUNT(*) calls, SUM(in_tokens) it, SUM(out_tokens) ot FROM v3_call_log WHERE status='ok' GROUP BY run_id").fetchall()
for r in rows:
    print(f"  {r['run_id']}: ok调用={r['calls']} in={r['it']:,} out={r['ot']:,}")

print("\n=== JSONL 产物(run 目录)===")
import os
runs_dir = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs"
for run in ("pilot_v3_20260828_012424", "pilot_v3_20260828_014554"):
    d = os.path.join(runs_dir, run)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isfile(p):
                print(f"  {run}\\{f}: {os.path.getsize(p)//1024} KB")
