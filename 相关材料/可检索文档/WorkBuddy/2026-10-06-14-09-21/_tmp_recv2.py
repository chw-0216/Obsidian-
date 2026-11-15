# -*- coding: utf-8 -*-
"""接待与运营 · 关键窗口逐条回捞（清洗版：剥离图片/XML 噪音，提取群昵称）"""
import sqlite3, os, datetime, re
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
    r = c.execute("select talker,session_type from sessions where display_name=?", (nm,)).fetchone()
    if r: sess[nm] = (r[0], r[1])
keys = {v[0]: (k, v[1]) for k, v in sess.items()}

IMG = re.compile(r'<img\b.*?(?:/>|</img>)', re.S)
XML = re.compile(r'<[^>]{0,4000}>', re.S)
AES = re.compile(r'aeskey="[^"]*"|cdnthumburl="[^"]*"|cdnbigimgurl="[^"]*"|cdnmidimgurl="[^"]*"')

def clean(ct, typ):
    if not ct: return ''
    t = ct
    if '<img' in t or '<msg' in t:
        # 群消息正文里 sender 昵称常在最前，保留前 60 字
        head = t.split('<')[0].strip()
        return (head[:60] + ' 〔图片/附件〕') if head else '〔图片/附件〕'
    t = AES.sub('', t)
    t = XML.sub('', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:300]

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')

qs = ",".join("?" * len(keys))
WINDOWS = [
    ("07-29 政协主席 + 宣传部长 + 记者", '2026-07-29 00:00', '2026-07-30 03:00'),
    ("07-31 区委组织部", '2026-07-31 00:00', '2026-08-01 03:00'),
    ("08-02 动漫谷开街", '2026-08-02 00:00', '2026-08-03 03:00'),
    ("08-03 科学城领导", '2026-08-03 00:00', '2026-08-04 03:00'),
    ("08-13~08-16 科学家 + 区委书记准备", '2026-08-13 00:00', '2026-08-17 03:00'),
    ("08-19~08-20 梁区长 + 市文旅局", '2026-08-19 00:00', '2026-08-21 03:00'),
    ("08-22 照片与汇总发出", '2026-08-22 00:00', '2026-08-23 03:00'),
    ("09-19~09-20 开街", '2026-09-19 00:00', '2026-09-21 03:00'),
]
lines = []
for title, a, b in WINDOWS:
    t0 = int(datetime.datetime.strptime(a, '%Y-%m-%d %H:%M').timestamp())
    t1 = int(datetime.datetime.strptime(b, '%Y-%m-%d %H:%M').timestamp())
    rows = c.execute(f"""select session_key, ts, role, sender, type, content from messages
        where session_key in ({qs}) and ts>=? and ts<? order by ts""", list(keys.keys()) + [t0, t1]).fetchall()
    lines.append("\n" + "=" * 88)
    lines.append(f"### {title}   （{len(rows)} 条）")
    lines.append("=" * 88)
    for sk, ts, role, sender, typ, ct in rows:
        nm, st = keys.get(sk, (sk, '?'))
        if role == 'system': continue
        who = "【我】" if role == 'me' else "对方"
        txt = clean(ct, typ)
        if not txt: continue
        lines.append(f"{fmt(ts)} {nm[:16]:<18}{who} {txt}")

out = os.path.join(OUT, '接待_关键窗口_清洗.txt')
open(out, 'w', encoding='utf-8').write("\n".join(lines))
print("SAVED ->", out)
print("lines:", len(lines))
