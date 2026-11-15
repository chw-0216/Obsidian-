# -*- coding: utf-8 -*-
"""检索「接待前制版链」：小马(马慧楠)制版 + 利世隆打印"""
import sqlite3, datetime, re
DB = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
c = con.cursor()
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
def nm(sk):
    r = c.execute("select display_name from sessions where talker=?", (sk,)).fetchone()
    return r[0] if r else sk

print("=" * 80)
print("① 「利世隆」及全部近似写法 —— 全库命中")
print("=" * 80)
for kw in ['利世隆','立世隆','力世隆','丽世隆','利世龙','立世龙','世隆','利世']:
    n = c.execute("select count(*) from messages where content like ?", (f'%{kw}%',)).fetchone()[0]
    print(f"  {kw:<8} {n} 条")
    if n:
        for ts, sk, role, sd, ct in c.execute(
            "select ts,session_key,role,sender,content from messages where content like ? order by ts limit 60",
            (f'%{kw}%',)):
            txt = re.sub(r'\s+', ' ', (ct or ''))[:200]
            print(f"     {fmt(ts)} [{nm(sk)[:16]:<18}] {role:<5} {txt}")
        break

print()
print("=" * 80)
print("② 「马慧楠」会话定位")
print("=" * 80)
row = c.execute("select talker,session_type,message_count,first_ts,last_ts from sessions where display_name like '%马慧楠%'").fetchall()
for t, st, mc, f, l in row:
    print(f"  {t}  {st}  {mc} 条  {fmt(f)} ~ {fmt(l)}")

print()
print("=" * 80)
print("③ 全库「制版 / 网版 / 曝光 / 菲林 / 硫酸纸」相关（含打印店线索）")
print("=" * 80)
PAT = ['制版','网版','曝光','菲林','硫酸纸','感光胶','刮板','烘干','印版','制网','洗版','晒版']
res = {}
for kw in PAT:
    n = c.execute("select count(*) from messages where content like ?", (f'%{kw}%',)).fetchone()[0]
    res[kw] = n
print("  命中量：", "  ".join(f"{k}={v}" for k, v in res.items()))

print()
print("=" * 80)
print("④ 全库「打印 / 图文 / 复印 / 输出」+ 店名线索")
print("=" * 80)
for kw in ['打印店','图文','复印','快印','输出店','打印','晒图','装订']:
    n = c.execute("select count(*) from messages where content like ?", (f'%{kw}%',)).fetchone()[0]
    print(f"  {kw:<8} {n} 条")
