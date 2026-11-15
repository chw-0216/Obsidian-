# -*- coding: utf-8 -*-
import sqlite3, datetime, re
DB=r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con=sqlite3.connect(f"file:{DB}?mode=ro",uri=True); c=con.cursor()
NAMES=['导！急速回，三思回得体！！！','央美美育工作站','乡村美育工作日志','洞台村装置计划',
       'Jason 关宇佳','王华青','马慧楠 ᥫᩣ LE HAUS版画','刘丽萍','杜栋','韩云峰','刘衎婧','石晶']
keys={}
for nm in NAMES:
    r=c.execute("select talker from sessions where display_name=?",(nm,)).fetchone()
    if r: keys[r[0]]=nm
qs=",".join("?"*len(keys))
a=int(datetime.datetime.strptime("2026-05-01",'%Y-%m-%d').timestamp())
b=int(datetime.datetime.strptime("2026-10-07",'%Y-%m-%d').timestamp())
rows=c.execute(f"select session_key,ts,role,sender,content from messages where session_key in ({qs}) and ts>=? and ts<? order by ts",
               list(keys.keys())+[a,b]).fetchall()
TITLES=['区委书记','政协主席','区长','局长','部长','宣传部','组织部','文旅','书记','主席','委员','领导','视察','到访','接待','参观','莅临','调研','科学家','外宾','记者','寻街']
def is_named(ct):
    return any(k in ct for k in ['区委书记','政协主席','区长','市文旅','宣传部','组织部','部长','政协','梁区','科学城','科学家'])
out=[]
for sk,ts,role,sd,ct in rows:
    if not ct: continue
    if is_named(ct):
        out.append((ts,keys[sk],role,ct))
print("★ 领导称谓命中 %d 条（2026-05-01 起）"%len(out))
print("-"*100)
for ts,sess,role,ct in out:
    t=datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    ct=ct.replace('\n',' ⏎ ')
    if len(ct)>170: ct=ct[:170]+'…'
    print("%s [%-11s|%s] %s"%(t,sess[:11],'我' if role=='me' else '对方',ct))
