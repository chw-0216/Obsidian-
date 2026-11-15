# -*- coding: utf-8 -*-
"""制版-打印链 深挖：7/24 全时段 + 通州/打印店 + 支付记录"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
def T(s): return int(datetime.datetime.strptime(s, '%Y-%m-%d %H:%M').timestamp())
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
        return '〔卡片/链接〕' + (t.group(1)[:60] if t else '')
    return re.sub(r'\s+', ' ', ct)[:260]

print("=" * 90)
print("① 马慧楠线 · 2026-07-24 全天（制版当日）")
print("=" * 90)
mk = c.execute("select talker from sessions where display_name like '%马慧楠%'").fetchone()[0]
for ts, role, ct in c.execute("select ts,role,content from messages where session_key=? and ts>=? and ts<? order by ts",
                              (mk, T('2026-07-24 00:00'), T('2026-07-25 00:00'))):
    print(f"{fmt(ts)} {'【我】' if role=='me' else '马慧楠'} {show(ct)}")

print()
print("=" * 90)
print("② 全库「通州」+ 打印/复印/硫酸纸/菲林 语境")
print("=" * 90)
for ts, sk, role, ct in c.execute("""select ts,session_key,role,content from messages
    where content like '%通州%' and (content like '%打印%' or content like '%复印%'
      or content like '%硫酸纸%' or content like '%菲林%' or content like '%制版%' or content like '%曝光%')
    order by ts"""):
    print(f"{fmt(ts)} [{nm(sk)[:16]:<18}] {'【我】' if role=='me' else '对方'} {show(ct)}")

print()
print("=" * 90)
print("③ 支付/账单里的「复印/打印/图文/利世隆」")
print("=" * 90)
for ts, sk, role, ct in c.execute("""select ts,session_key,role,content from messages
    where (content like '%复印%' or content like '%图文%' or content like '%快印%' or content like '%打印店%')
      and (content like '%元%' or content like '%支付%' or content like '%收款%' or content like '%转账%')
    order by ts limit 40"""):
    print(f"{fmt(ts)} [{nm(sk)[:16]:<18}] {'【我】' if role=='me' else '对方'} {show(ct)}")

print()
print("=" * 90)
print("④ 全库「晒图」命中（可能是另一家输出店）")
print("=" * 90)
for ts, sk, role, ct in c.execute("select ts,session_key,role,content from messages where content like '%晒图%' order by ts limit 25"):
    print(f"{fmt(ts)} [{nm(sk)[:16]:<18}] {'【我】' if role=='me' else '对方'} {show(ct)}")
