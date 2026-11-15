# -*- coding: utf-8 -*-
"""接待与运营 · 关键窗口逐条回捞（含群成员名解析）"""
import sqlite3, os, datetime
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
    if r: sess[nm] = r[0]
keys = {v: k for k, v in sess.items()}

# 联系人名解析
def load_contacts():
    d = {}
    try:
        for u, rk, nk in c.execute("select user_name, remark, nick_name from contacts"):
            d[u] = rk or nk or u
    except Exception as e:
        print("contacts err", e)
    return d
CT = load_contacts()

def sn(sd):
    if not sd: return ''
    if sd in CT: return CT[sd]
    return sd.split('@')[0]

def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')

qs = ",".join("?" * len(keys))
WINDOWS = [
    ("07-29 政协主席 + 宣传部长 + 记者", '2026-07-29 00:00', '2026-07-30 03:00'),
    ("07-31 区委组织部", '2026-07-31 00:00', '2026-08-01 03:00'),
    ("08-02 动漫谷开街", '2026-08-02 00:00', '2026-08-03 03:00'),
    ("08-03 科学城领导", '2026-08-03 00:00', '2026-08-04 03:00'),
    ("08-13~08-16 科学家 + 区委书记", '2026-08-13 00:00', '2026-08-17 03:00'),
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
    lines.append("\n" + "=" * 90)
    lines.append(f"### {title}   （{len(rows)} 条）")
    lines.append("=" * 90)
    for sk, ts, role, sender, typ, ct in rows:
        nm = keys.get(sk, sk)
        if role == 'me':
            who = "【我】"
        elif role == 'system':
            continue
        else:
            who = f"[{sn(sender) if sender else '对方'}]"
        txt = (ct or '').replace('\n', ' ⏎ ')
        if typ not in ('text', '1', None, '') and not txt:
            txt = f"<{typ}>"
        if len(txt) > 400: txt = txt[:400] + "…"
        lines.append(f"{fmt(ts)} {nm[:18]:<20}{who} {txt}")

out = os.path.join(OUT, '接待_关键窗口_逐条.txt')
open(out, 'w', encoding='utf-8').write("\n".join(lines))
print("SAVED ->", out, len("\n".join(lines)), "chars")
