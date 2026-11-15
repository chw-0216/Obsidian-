# -*- coding: utf-8 -*-
"""抽取三条关键会话的转折片段，用于「价值为什么变」的归因"""
import sqlite3, re, io, datetime, os

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
cur = con.cursor()


def t2s(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return '?'


def clean(c):
    return re.sub(r'<[^>]+>', '', c or '').replace('\n', ' ').strip()


def find(nm):
    for t, n in cur.execute("select talker, display_name from sessions where session_type='私聊'"):
        if n == nm:
            return t
    return None


def dump(out, label, talker, start=None, end=None, limit=None):
    out.write('\n' + '=' * 76 + '\n### ' + label + '\n' + '=' * 76 + '\n')
    q = 'select ts, role, type, content from messages where session_key=?'
    a = [talker]
    if start:
        q += ' and ts>=?'; a.append(start)
    if end:
        q += ' and ts<=?'; a.append(end)
    q += ' order by ts' + (f' limit {limit}' if limit else '')
    for ts, role, ty, c in cur.execute(q, a):
        out.write(f"[{t2s(ts)}] {role:<5} {ty:<7} {clean(c)[:150]}\n")


def ts(y, m, d):
    return int(datetime.datetime(y, m, d).timestamp())


out = io.StringIO()
e = find('Eloise')
out.write(f'Eloise talker={e}\n')
dump(out, 'Eloise · 2026 全年（原 2025 年 4099 条 → 2026 仅 156 条）', e, start=ts(2026, 1, 1))

c = find('陈昶文')
out.write(f'\n陈昶文 talker={c}\n')
dump(out, '陈昶文 · 2026-06-20 至 06-27（6,275 条后彻底断）', c, start=ts(2026, 6, 20), end=ts(2026, 6, 28))

m = find('沐茜妍')
out.write(f'\n沐茜妍 talker={m}\n')
dump(out, '沐茜妍 · 2026-09-10 至 09-16（他主动切断）', m, start=ts(2026, 9, 10), end=ts(2026, 9, 17))

x = find('王若彤')
out.write(f'\n王若彤 talker={x}\n')
dump(out, '王若彤 · 最近 40 条（215 天前断）', x, limit=None)
# 取尾部
rows = list(cur.execute('select ts,role,type,content from messages where session_key=? order by ts desc limit 30', (x,)))
out.write('\n--- 王若彤 最后 30 条（倒序） ---\n')
for ts2, role, ty, cc in rows:
    out.write(f"[{t2s(ts2)}] {role:<5} {ty:<7} {clean(cc)[:140]}\n")

open(os.path.join(WS, '_tmp', 'key_segments.txt'), 'w', encoding='utf-8').write(out.getvalue())
print('ok', len(out.getvalue()))
