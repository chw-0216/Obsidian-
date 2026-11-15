# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()
def dt(ts): return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

out = []
# 2026-04-01 ~ 2026-04-30 文件传输助手里 >500 字的文本（植墨策划案期）
lo = int(datetime.datetime(2026,3,25,0,0).timestamp())
hi = int(datetime.datetime(2026,5,10,0,0).timestamp())
cur.execute("""SELECT m.ts, s.display_name, m.content FROM messages m
   LEFT JOIN sessions s ON m.session_key=s.talker
   WHERE m.ts BETWEEN ? AND ? AND length(m.content) > 500
   ORDER BY m.ts""", (lo,hi))
for ts, dn, c in cur.fetchall():
    c = str(c)
    if any(x in c for x in ['<img','<msg','<appmsg','CDATA','support.weixin']): continue
    out.append((dt(ts), dn, c))

txt = "\n\n".join(f"{'='*72}\n[{t}] {dn}\n{'='*72}\n{c}" for t,dn,c in out)
open("_tmp_jinglin/植墨_原始长文本_0325to0510.txt","w",encoding="utf-8").write(txt)
print(f"共 {len(out)} 条长文本，已写出")
for t,dn,c in out:
    print(f"  [{t}] {dn}  {len(c)} 字  开头: {c[:70].replace(chr(10),' ')}")
