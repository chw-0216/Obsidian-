# -*- coding: utf-8 -*-
import sqlite3, datetime, os, re, io
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

def dt(ts):
    try: return datetime.datetime.fromtimestamp(int(ts))
    except: return None

# 全库统计
cur.execute("SELECT COUNT(*) FROM messages")
print("全库条数:", cur.fetchone()[0])

# 时间范围
cur.execute("SELECT MIN(ts), MAX(ts) FROM messages")
mn, mx = cur.fetchone()
print("时间范围:", dt(mn), "→", dt(mx))

# 拉 10-02 ~ 10-04 全部消息
lo = int(datetime.datetime(2026,10,2,0,0).timestamp())
hi = int(datetime.datetime(2026,10,4,23,59).timestamp())
cur.execute("""SELECT m.ts, s.display_name, s.talker, m.role, m.content
               FROM messages m LEFT JOIN sessions s ON m.session_key = s.talker
               WHERE m.ts BETWEEN ? AND ? ORDER BY m.ts""", (lo, hi))
rows = cur.fetchall()
print("10-02~10-04 条数:", len(rows))

def clean(c):
    if not c: return ""
    c = str(c)
    if '<img' in c or '<msg' in c or '<appmsg' in c:
        head = c.split('<')[0][:200]
        return head + " 〔图/附件〕"
    if '<location' in c:
        m = re.search(r'poiname="([^"]*)"', c); l = re.search(r'label="([^"]*)"', c)
        return "〔位置〕" + (m.group(1) if m else "") + " " + (l.group(1) if l else "")
    return c[:400]

with open("_tmp_jinglin/1003_全量_1002to1004.txt", "w", encoding="utf-8") as f:
    for ts, dn, tk, role, content in rows:
        t = dt(ts).strftime("%m-%d %H:%M:%S")
        f.write(f"[{t}] {dn or tk} | {role}: {clean(content)}\n")
print("已写出 1003_全量_1002to1004.txt")
