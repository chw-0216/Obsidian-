# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); c=con.cursor()
NAMES=['导！急速回，三思回得体！！！','央美美育工作站','乡村美育工作日志','洞台村装置计划',
       'Jason 关宇佳','王华青','马慧楠 ᥫᩣ LE HAUS版画','刘丽萍','杜栋','韩云峰','刘衎婧']
keys={}
for nm in NAMES:
    r=c.execute("select talker from sessions where display_name=?",(nm,)).fetchone()
    if r: keys[r[0]]=nm
# 群成员名映射（群聊里 sender 是 wxid，需查 contact）
def sender_name(sk, sender):
    if not sender: return ''
    r=c.execute("select display_name from sessions where talker=?",(sender,)).fetchone()
    if r and r[0]: return r[0]
    try:
        r=c.execute("select remark,nick_name from contacts where user_name=?",(sender,)).fetchone()
        if r: return (r[0] or r[1] or sender)
    except Exception: pass
    return sender
qs=",".join("?"*len(keys))
def dump(d1,d2,label):
    a=int(datetime.datetime.strptime(d1,'%Y-%m-%d').timestamp()); b=int(datetime.datetime.strptime(d2,'%Y-%m-%d').timestamp())
    rows=c.execute(f"select session_key,ts,role,sender,content from messages where session_key in ({qs}) and ts>=? and ts<? order by ts",list(keys.keys())+[a,b]).fetchall()
    print("\n"+"="*88); print("### %s  (%s ~ %s)  %d 条"%(label,d1,d2,len(rows))); print("="*88)
    who={'me':'我','them':'对方','system':'系统'}
    for sk,ts,role,sd,ct in rows:
        t=datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
        ct=(ct or '').replace('\n',' ⏎ ')
        if len(ct)>260: ct=ct[:260]+' …'
        tag=who.get(role,role)
        if sk.endswith('@chatroom') and role=='them':
            tag='【%s】'%sender_name(sk,sd)[:10]
        print("  %s [%-11s|%s] %s"%(t,keys[sk][:11],tag,ct))
dump("2026-08-22","2026-08-23","8/22 发区委书记到访照片给导师")
dump("2026-08-01","2026-08-04","8/2 开街 & 8/3 科学城")
dump("2026-09-19","2026-09-21","9/20 正式开街")
