# -*- coding: utf-8 -*-
"""制版链 · 全量实例汇总（跨会话）"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
OUT = r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21/_tmp_jinglin"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
def nm(sk):
    r = c.execute("select display_name from sessions where talker=?", (sk,)).fetchone()
    return r[0] if r else sk
def show(ct):
    if not ct: return ''
    if 'poiname=' in ct:
        p = re.search(r'poiname="([^"]*)"', ct); l = re.search(r'label="([^"]*)"', ct)
        return f"〔定位〕{p.group(1) if p else '?'} ｜ {l.group(1) if l else ''}"
    if '<img' in ct: return '〔图片〕'
    if '<msg' in ct or '<appmsg' in ct:
        t = re.search(r'<title>(.*?)</title>', ct, re.S)
        return '〔卡片〕' + (t.group(1)[:60] if t else '')
    return re.sub(r'\s+', ' ', ct)[:280]

lines = []
def P(*a): lines.append(" ".join(str(x) for x in a))

P("=" * 92); P("① 「澜花语岸 / 潞苑 / 通州」定位与地址线索"); P("=" * 92)
for ts, sk, role, ct in c.execute("""select ts,session_key,role,content from messages
    where content like '%澜花语岸%' or content like '%潞苑%' order by ts"""):
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {'【我】' if role=='me' else '对方'} {show(ct)}")

P(); P("=" * 92); P("② 全库「制版」逐条（跨全部会话，按时间）"); P("=" * 92)
for ts, sk, role, ct in c.execute("select ts,session_key,role,content from messages where content like '%制版%' order by ts"):
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {'【我】' if role=='me' else '对方'} {show(ct)}")

P(); P("=" * 92); P("③ 全库「菲林」逐条"); P("=" * 92)
for ts, sk, role, ct in c.execute("select ts,session_key,role,content from messages where content like '%菲林%' order by ts"):
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {'【我】' if role=='me' else '对方'} {show(ct)}")

P(); P("=" * 92); P("④ 全库「硫酸纸」逐条"); P("=" * 92)
for ts, sk, role, ct in c.execute("select ts,session_key,role,content from messages where content like '%硫酸纸%' order by ts"):
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {'【我】' if role=='me' else '对方'} {show(ct)}")

P(); P("=" * 92); P("⑤ 全库「曝光台 / 烘干箱」逐条"); P("=" * 92)
for ts, sk, role, ct in c.execute("""select ts,session_key,role,content from messages
    where content like '%曝光台%' or content like '%烘干箱%' order by ts"""):
    P(f"{fmt(ts)} [{nm(sk)[:18]:<20}] {'【我】' if role=='me' else '对方'} {show(ct)}")

open(f"{OUT}/制版链_全量实例.txt", 'w', encoding='utf-8').write("\n".join(lines))
print("SAVED ->", f"{OUT}/制版链_全量实例.txt", len(lines), "行")
