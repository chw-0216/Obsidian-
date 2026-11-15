# -*- coding: utf-8 -*-
"""
去重诊断：把 2,506 条重复的「性质」查清楚，再决定怎么处理。
只读 index.sqlite。
"""
import sqlite3
from collections import Counter, defaultdict

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = c.cursor()

print("=" * 72)
print("A. 重复的总体规模")
print("=" * 72)
cur.execute("SELECT COUNT(*) FROM messages")
tot = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT session_key,ts,content FROM messages)")
k1 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT session_key,ts,role,sender,type,content FROM messages)")
k2 = cur.fetchone()[0]
print(f"  原始              {tot:>7}")
print(f"  按 (ts,content)   {k1:>7}   去重 {tot-k1}")
print(f"  按 (+role+sender+type) {k2:>7}   去重 {tot-k2}")
print(f"  → 两个键差 {k2-k1} 条 = 「同一秒同一内容但发送方/类型不同」")

print()
print("=" * 72)
print("B. 重复是否集中在特定来源？（sessions.source_file）")
print("=" * 72)
cur.execute("""
SELECT s.source_file, COUNT(*) AS dup
FROM messages m JOIN sessions s ON s.talker = m.session_key
WHERE EXISTS (
  SELECT 1 FROM messages m2
  WHERE m2.session_key = m.session_key AND m2.ts = m.ts AND m2.content = m.content AND m2.id <> m.id
)
GROUP BY s.source_file
""")
agg = Counter()
for sf, n in cur.fetchall():
    if not sf: agg["(空)"] += n
    elif "07_WeFlow原始导出" in sf: agg["07导出"] += n
    elif "09_WeFlow增量" in sf: agg["09导出"] += n
    else: agg["解密库直读"] += n
for k, v in agg.most_common():
    print(f"  {k:<14} {v:>6}")

print()
print("=" * 72)
print("C. 重复最多的会话（前 12）")
print("=" * 72)
cur.execute("""
SELECT session_key,
       COUNT(*) AS n,
       COUNT(*) - COUNT(DISTINCT ts||'|'||content) AS dup
FROM messages GROUP BY session_key HAVING dup > 0 ORDER BY dup DESC LIMIT 12
""")
rows = cur.fetchall()
for k, n, d in rows:
    print(f"  {k:<40} 总 {n:>6}  重复 {d:>5}  ({100.0*d/n:>5.1f}%)")

print()
print("=" * 72)
print("D. ★ 关键：重复的两条，发送方/类型是否也相同？（判「真重复」还是「误杀」）")
print("=" * 72)
cur.execute("""
SELECT COUNT(*) FROM (
  SELECT session_key, ts, content, COUNT(DISTINCT sender||'#'||type||'#'||role) AS variants
  FROM messages GROUP BY session_key, ts, content HAVING COUNT(*) > 1
) WHERE variants > 1
""")
v = cur.fetchone()[0]
print(f"  「同秒同内容但发送方或类型不同」的组数：{v}")
print(f"  → 这些组是**可能被 (ts,content) 误杀**的对象（群里两人同秒发同样的话）")
cur.execute("""
SELECT COUNT(*) FROM (
  SELECT session_key, ts, content FROM messages GROUP BY session_key, ts, content HAVING COUNT(*) > 1
)
""")
print(f"  重复组总数：{cur.fetchone()[0]}")

print()
print("=" * 72)
print("E. 被误杀风险的实际样本（同秒同内容、发送方不同）")
print("=" * 72)
cur.execute("""
SELECT session_key, ts, content, GROUP_CONCAT(DISTINCT sender) AS senders, COUNT(*) n
FROM messages
GROUP BY session_key, ts, content
HAVING COUNT(DISTINCT sender) > 1
ORDER BY n DESC LIMIT 8
""")
for k, ts, ct, sn, n in cur.fetchall():
    print(f"  [{k[:28]}] n={n} senders={sn[:60]}")
    print(f"      content={(ct or '')[:80]}")

print()
print("=" * 72)
print("F. 有没有「同一条消息但内容略有差异」的漏网？（同会话 同秒 不同内容）")
print("=" * 72)
cur.execute("""
SELECT COUNT(*) FROM (
  SELECT session_key, ts FROM messages GROUP BY session_key, ts HAVING COUNT(DISTINCT content) > 1
)
""")
print(f"  同会话同秒但内容不同的时间点：{cur.fetchone()[0]} 个")
cur.execute("""
SELECT COUNT(*) FROM (
  SELECT session_key, ts, content FROM messages
  WHERE length(trim(content)) = 0 GROUP BY session_key, ts, content HAVING COUNT(*) > 1
)
""")
print(f"  其中内容是空白的重复组：{cur.fetchone()[0]}")

print()
print("=" * 72)
print("G. 时间分布：重复落在哪个时间段？")
print("=" * 72)
cur.execute("""
SELECT strftime('%Y-%m', ts, 'unixepoch', 'localtime') AS ym, COUNT(*) 
FROM messages m
WHERE EXISTS (SELECT 1 FROM messages m2 WHERE m2.session_key=m.session_key AND m2.ts=m.ts AND m2.content=m.content AND m2.id<>m.id)
GROUP BY ym ORDER BY ym
""")
for ym, n in cur.fetchall():
    print(f"  {ym}  {n:>6}")

c.close()
