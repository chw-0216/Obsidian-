# -*- coding: utf-8 -*-
import sqlite3, datetime, re
DB=r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con=sqlite3.connect(f"file:{DB}?mode=ro",uri=True); c=con.cursor()
# 1) 刘衎婧 8/24-8/26
r=c.execute("select talker from sessions where display_name='刘衎婧'").fetchone()
a=int(datetime.datetime.strptime("2026-08-24",'%Y-%m-%d').timestamp()); b=int(datetime.datetime.strptime("2026-08-27",'%Y-%m-%d').timestamp())
print("### 刘衎婧 8/24-8/26")
for sk,ts,role,ct in c.execute("select session_key,ts,role,content from messages where session_key=? and ts>=? and ts<? order by ts",(r[0],a,b)):
    print("  %s [%s] %s"%(datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M'),'我' if role=='me' else '对方',(ct or '')[:250]))
# 2) 乡村美育工作日志 全量（找接待/领导）
r2=c.execute("select talker from sessions where display_name='乡村美育工作日志'").fetchone()
print("\n### 乡村美育工作日志 中所有含 接待/领导/书记/参观 的段落")
for sk,ts,role,ct in c.execute("select session_key,ts,role,content from messages where session_key=? order by ts",(r2[0],)):
    if not ct: continue
    if any(k in ct for k in ['接待','领导','书记','参观','视察','政协','区长','来访','到访']):
        print("\n--- %s [%s] len=%d ---"%(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M'),'我' if role=='me' else '对方',len(ct)))
        # 找含关键词的行
        for line in ct.split('\n'):
            if any(k in line for k in ['接待','领导','书记','参观','视察','政协','区长','来访','到访','日期']):
                print("     "+line[:200])
