# -*- coding: utf-8 -*-
"""井邻线·接待与运营 全量证据提取（只读 index.sqlite）"""
import sqlite3, os, csv, re, json
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_jinglin"
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()

NAMES = ['导！急速回，三思回得体！！！','央美美育工作站','乡村美育工作日志','洞台村装置计划',
         '洞台井邻','Jason 关宇佳','井邻 张宝🐱 24H 总管','美育张宇涵','刘丽萍','长城乡村美育实验室',
         '2025社会美育与乡村振兴','琢','韩云峰','慢D生活朱朱','刘衎婧','薛伟东烧焦一切','王华青',
         '王博','子辰','郭静秋','齐家滨','舒泽林','杜栋','马慧楠 ᥫᩣ LE HAUS版画','蒲公英','养肥','聚华13513481575']
sess = {}
for nm in NAMES:
    r = c.execute("select talker,session_type,message_count,first_ts,last_ts from sessions where display_name=?",(nm,)).fetchone()
    if r: sess[nm] = r
print("== 命中会话 ==")
for nm,(t,st,mc,f,l) in sess.items():
    print("  %-32s %-6s %5s  %s ~ %s" % (nm[:32], st, mc,
          __import__('datetime').datetime.fromtimestamp(f).strftime('%Y-%m-%d'),
          __import__('datetime').datetime.fromtimestamp(l).strftime('%Y-%m-%d')))

keys = {t:nm for nm,(t,st,mc,f,l) in sess.items()}
qs = ",".join("?"*len(keys))
rows = c.execute(f"""select session_key, ts, role, content from messages
    where session_key in ({qs}) and ts >= strftime('%s','2026-03-01') and ts < strftime('%s','2026-10-07')
    order by ts""", list(keys.keys())).fetchall()
print("\n== 井邻线窗口消息 %d 条 ==" % len(rows))

def fmt(ts): 
    import datetime; return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
who = {'me':'我','them':'对方','system':'系统'}

# 全量落盘
with open(os.path.join(OUT,'井邻线_全量_20260301_20261006.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['时间','会话','发送方','内容'])
    for sk,ts,role,ct in rows:
        w.writerow([fmt(ts), keys[sk], who.get(role,role), (ct or '').replace('\n',' ⏎ ')])

# 接待证据
PAT = re.compile(r'领导|到访|接待|参观|视察|调研|莅临|区长|书记|局长|部长|主席|委员|记者|外宾|科学家|组织部|宣传部|文旅|动漫谷|寻街|讲解|介绍|来访|参观团|考察')
hit = [(sk,ts,role,ct) for sk,ts,role,ct in rows if ct and PAT.search(ct)]
print("== 接待/运营证据命中 %d 条 ==" % len(hit))
with open(os.path.join(OUT,'接待证据_原始.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['时间','会话','发送方','内容'])
    for sk,ts,role,ct in hit:
        w.writerow([fmt(ts), keys[sk], who.get(role,role), (ct or '').replace('\n',' ⏎ ')])
print("SAVED ->", OUT)
