# -*- coding: utf-8 -*-
"""「接待前制版链」全量检索：利世隆 + 小马制版 + 硫酸纸/菲林输出"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_jinglin"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
def nm(sk):
    r = c.execute("select display_name from sessions where talker=?", (sk,)).fetchone()
    return r[0] if r else sk

def clean(ct):
    if not ct: return ''
    if '<img' in ct or '<msg' in ct:
        head = ct.split('<')[0].strip()
        return (head[:70] + ' 〔图/附件〕') if head else '〔图/附件〕'
    t = re.sub(r'<[^>]{0,4000}>', '', ct)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:300]

lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)

# ── ① 利世隆 全部命中 ──
P("=" * 92); P("① 「利世隆」全库全部命中（含定位/名片/转发）"); P("=" * 92)
for ts, sk, role, sd, ct in c.execute(
        "select ts,session_key,role,sender,content from messages where content like '%利世隆%' order by ts"):
    who = "【我】" if role == 'me' else "对方"
    txt = clean(ct)
    poi = re.search(r'poiname="([^"]*)"', ct or '')
    loc = re.search(r'label="([^"]*)"', ct or '')
    if poi: txt = f"〔定位〕{poi.group(1)}  {loc.group(1) if loc else ''}"
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {who} {txt}")

# ── ② 马慧楠会话全量（含制版/网版语境）──
P(); P("=" * 92); P("② 马慧楠（小马）会话全量 · 2026-07 起"); P("=" * 92)
mk = c.execute("select talker from sessions where display_name like '%马慧楠%'").fetchone()[0]
t0 = int(datetime.datetime.strptime('2026-07-01 00:00', '%Y-%m-%d %H:%M').timestamp())
for ts, role, sd, ct in c.execute(
        "select ts,role,sender,content from messages where session_key=? and ts>=? order by ts", (mk, t0)):
    who = "【我】" if role == 'me' else "马慧楠"
    P(f"{fmt(ts)} {who} {clean(ct)}")

# ── ③ 「硫酸纸 / 菲林 / 输出 / 打印」在导师线的语境（接待前动作）──
P(); P("=" * 92); P("③ 导师线里的「硫酸纸/菲林/打印/输出/制版」动作语境"); P("=" * 92)
dd = c.execute("select talker from sessions where display_name like '导！急速回%'").fetchone()[0]
PAT = '硫酸纸|菲林|打印|输出|制版|曝光|网版|晒图'
for ts, role, sd, ct in c.execute(
        f"select ts,role,sender,content from messages where session_key=? and content REGEXP ? order by ts", (dd, PAT)) \
        if False else c.execute(
        f"""select ts,role,sender,content from messages where session_key=? and (
            content like '%硫酸纸%' or content like '%菲林%' or content like '%制版%'
            or content like '%曝光%' or content like '%网版%' or content like '%打印%'
            or content like '%输出%' or content like '%晒图%') order by ts""", (dd,)):
    who = "【我】" if role == 'me' else "陈晔"
    P(f"{fmt(ts)} {who} {clean(ct)}")

open(f"{OUT}/接待前_制版打印链_全量.txt", 'w', encoding='utf-8').write("\n".join(lines))
print("SAVED ->", f"{OUT}/接待前_制版打印链_全量.txt", len(lines), "行")
