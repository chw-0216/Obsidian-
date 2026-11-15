# -*- coding: utf-8 -*-
import sqlite3, datetime
DB=r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con=sqlite3.connect(f"file:{DB}?mode=ro",uri=True); c=con.cursor()
NAMES=['导！急速回，三思回得体！！！','央美美育工作站','乡村美育工作日志','洞台村装置计划',
       'Jason 关宇佳','王华青','马慧楠 ᥫᩣ LE HAUS版画','刘丽萍','石晶','杜栋']
keys={}
for nm in NAMES:
    r=c.execute("select talker from sessions where display_name=?",(nm,)).fetchone()
    if r: keys[r[0]]=nm
qs=",".join("?"*len(keys))
def sn(sd):
    if not sd: return ''
    r=c.execute("select display_name from sessions where talker=?",(sd,)).fetchone()
    if r and r[0]: return r[0]
    try:
        r=c.execute("select remark,nick_name from contacts where user_name=?",(sd,)).fetchone()
        if r: return (r[0] or r[1] or sd)
    except Exception: pass
    return sd
def dump(d1,d2,label,only_kw=None):
    a=int(datetime.datetime.strptime(d1,'%Y-%m-%d').timestamp()); b=int(datetime.datetime.strptime(d2,'%Y-%m-%d').timestamp())
    rows=c.execute(f"select session_key,ts,role,sender,content from messages where session_key in ({qs}) and ts>=? and ts<? order by ts",list(keys.keys())+[a,b]).fetchall()
    print("\n"+"="*88); print("### %s (%s~%s) %d 条"%(label,d1,d2,len(rows))); print("="*88)
    for sk,ts,role,sd,ct in rows:
        ct=(ct or '')
        if only_kw and not any(k in ct for k in only_kw): continue
        t=datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
        ct=ct.replace('\n',' ⏎ ')
        if len(ct)>240: ct=ct[:240]+'…'
        tag='我' if role=='me' else ('【%s】'%sn(sd)[:10] if sk.endswith('@chatroom') else '对方')
        print("  %s [%-11s|%s] %s"%(t,keys[sk][:11],tag,ct))
dump("2026-08-13","2026-08-14","8/13 向关总自荐科学家接待", ['科学','自荐','英文','接待','关总','书记','明天'])
dump("2026-09-19","2026-09-22","9/20 正式开街")
