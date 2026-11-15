# -*- coding: utf-8 -*-
"""利世隆打印店线 + 全部图文/快印店记录"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_jinglin"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
def show(ct):
    if not ct: return ''
    if 'poiname=' in ct:
        p = re.search(r'poiname="([^"]*)"', ct); l = re.search(r'label="([^"]*)"', ct)
        return f"〔定位〕{p.group(1) if p else '?'} ｜ {l.group(1) if l else ''}"
    if '<img' in ct: return '〔图片〕'
    if '<msg' in ct or '<appmsg' in ct:
        t = re.search(r'<title>(.*?)</title>', ct, re.S)
        return '〔卡片/文件〕' + (t.group(1)[:70] if t else '')
    return re.sub(r'\s+', ' ', ct)[:320]

lines = []
def P(*a): lines.append(" ".join(str(x) for x in a))

SHOPS = ['利世隆固话69522333留余高姐','天逸图文广告17191194223','A红太阳图文快印 15010508835',
         'A佳乐印艺 图文 快印 广告 印刷','千印百艺图文快印美院北门店','精特广告苗应建',
         'A 豫友图文广告13521586557','A0博印图文广告 199 8816 2871','A恒兴图文广告印刷15125546873',
         '星铂广告']
for s in SHOPS:
    r = c.execute("select talker,message_count,first_ts,last_ts from sessions where display_name=?", (s,)).fetchone()
    if not r: P(f"（未命中）{s}"); continue
    sk, mc, f, l = r
    P(); P("=" * 92)
    P(f"◆ {s}   |  {mc} 条  |  {fmt(f)} ~ {fmt(l)}  |  {sk}")
    P("=" * 92)
    for ts, role, ct in c.execute("select ts,role,content from messages where session_key=? order by ts", (sk,)):
        P(f"{fmt(ts)} {'【我】' if role=='me' else '对方'} {show(ct)}")

open(f"{OUT}/打印店线_全量.txt", 'w', encoding='utf-8').write("\n".join(lines))
print("SAVED ->", f"{OUT}/打印店线_全量.txt", len(lines), "行")
