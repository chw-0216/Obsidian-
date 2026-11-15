# -*- coding: utf-8 -*-
import sqlite3, datetime, sys
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
NAMES = ['导！急速回，三思回得体！！！','央美美育工作站','乡村美育工作日志','洞台村装置计划',
         'Jason 关宇佳','井邻 张宝🐱 24H 总管','韩云峰','马慧楠 ᥫᩣ LE HAUS版画','刘丽萍','刘衎婧','王华青','杜栋']
keys={}
for nm in NAMES:
    r=c.execute("select talker from sessions where display_name=?",(nm,)).fetchone()
    if r: keys[r[0]]=nm
qs=",".join("?"*len(keys))
def dump(d1,d2,label):
    a=int(datetime.datetime.strptime(d1,'%Y-%m-%d').timestamp())
    b=int(datetime.datetime.strptime(d2,'%Y-%m-%d').timestamp())
    rows=c.execute(f"""select session_key,ts,role,content from messages
        where session_key in ({qs}) and ts>=? and ts<? order by ts""",list(keys.keys())+[a,b]).fetchall()
    print("\n"+"="*90); print("### %s  (%s ~ %s)  共 %d 条"%(label,d1,d2,len(rows))); print("="*90)
    who={'me':'我','them':'对方','system':'系统'}
    for sk,ts,role,ct in rows:
        t=datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
        ct=(ct or '').replace('\n',' ⏎ ')
        if len(ct)>300: ct=ct[:300]+' …'
        print("  %s [%-12s|%s] %s"%(t,keys[sk][:12],who.get(role,role),ct))
for a,b,l in [("2026-08-19","2026-08-21","8/19-8/20 梁区长+市文旅局局长"),
              ("2026-07-29","2026-07-30","7/29 政协主席/宣传部长/记者"),
              ("2026-08-15","2026-08-17","8/15 区委书记 & 8/16 科学家"),
              ("2026-08-01","2026-08-04","8/2 开街 & 8/3 科学城"),
              ("2026-09-18","2026-09-22","9/20 正式开街")]:
    dump(a,b,l)
