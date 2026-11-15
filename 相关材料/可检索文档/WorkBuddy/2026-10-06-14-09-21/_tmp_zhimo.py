# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

def clean(c):
    if not c: return ""
    c = str(c)
    if '<img' in c or '<msg' in c or '<appmsg' in c:
        return c.split('<')[0][:400] + " 〔图/附件〕"
    return c

KW = ["植墨","三间房","五感","感官","断点","房1","房2","房3","栗壳","百年栗","香薰"]
seen = set()
rows = []
for kw in KW:
    cur.execute("""SELECT m.ts, s.display_name, m.role, m.content FROM messages m
                   LEFT JOIN sessions s ON m.session_key = s.talker
                   WHERE m.content LIKE ? ORDER BY m.ts""", ('%'+kw+'%',))
    for ts, dn, role, c in cur.fetchall():
        k = (ts, str(c)[:50])
        if k in seen: continue
        seen.add(k)
        rows.append((int(ts), dn, role, clean(c)))

rows.sort()
out = []
for ts, dn, role, c in rows:
    t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    who = "我" if role == "me" else "对方"
    out.append(f"[{t}] {dn} | {who}:\n{c}\n" + "-"*70)

txt = "\n".join(out)
open("_tmp_jinglin/植墨三间房_五感策划案_全量.txt", "w", encoding="utf-8").write(txt)
print(f"共 {len(rows)} 条，已写出 _tmp_jinglin/植墨三间房_五感策划案_全量.txt")
print("="*70)
# 只打印含「植墨」「三间房」「五感」的核心条
core = [r for r in rows if any(k in str(r[3]) for k in ["植墨","三间房","五感"])]
print(f"核心条 {len(core)}：")
for ts, dn, role, c in core:
    t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    print(f"\n[{t}] {dn} | {'我' if role=='me' else '对方'}:")
    print(c[:1500])
