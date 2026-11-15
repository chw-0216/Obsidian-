# -*- coding: utf-8 -*-
"""验证四条裁定：① 同门坑过 ② 陈昶文「没时间泡」 ③ 王雪纯路人 ④ 留学中介群
"""
import sqlite3, os, io, datetime, collections

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
buf = io.StringIO()
def p(*a):
    buf.write(' '.join(str(x) for x in a) + "\n")

def ts(t):
    try:
        return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return '?'

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c = con.cursor()

# ---------- 0. 找人 ----------
name2k = {}
for t, n in c.execute('select talker, display_name from sessions'):
    name2k.setdefault(n or t, t)
def find(kw):
    out = []
    for n, t in name2k.items():
        if kw in n:
            out.append((n, t))
    return out

TARGETS = ['琢', '养肥', '王博', '陈昶文', '王雪纯']
p('=' * 84)
p('〇、目标定位')
p('=' * 84)
tid = {}
for k in TARGETS:
    rs = [r for r in find(k) if not r[1].endswith('@chatroom')]
    p(f'  {k}: {rs[:4]}')
    if rs:
        tid[k] = rs[0][1]

# ---------- 1. ★ 「A钱群」 ----------
p('')
p('=' * 84)
p('一、★★ 「A钱群」是什么（出现在 琢 / 养肥 的共同群）')
p('=' * 84)
for n, t in find('A钱'):
    p(f'  群名={n}  talker={t}')
    rows = list(c.execute("select ts, role, sender, content from messages where session_key=? order by ts", (t,)))
    p(f'  共 {len(rows)} 条 ｜ 时间 {ts(rows[0][0])} → {ts(rows[-1][0])}' if rows else '  （无消息）')
    for r in rows[:80]:
        ct = (r[3] or '').replace('\n', ' ')[:90]
        p(f'    [{ts(r[0])}] {r[1]:<7}{str(r[2])[:14]:<16}{ct}')
    if len(rows) > 80:
        p(f'    …… 余 {len(rows)-80} 条')

# ---------- 2. 同门三人私聊样本 ----------
p('')
p('=' * 84)
p('二、★ 琢 / 养肥 / 王博 —— 私聊全量（找「坑」的证据）')
p('=' * 84)
for k in ['琢', '养肥', '王博']:
    t = tid.get(k)
    if not t:
        p(f'  {k}: 未找到会话'); continue
    rows = list(c.execute("select ts, role, content from messages where session_key=? order by ts", (t,)))
    p('')
    p(f'  ── {k}（{t}）共 {len(rows)} 条 ｜ {ts(rows[0][0])} → {ts(rows[-1][0])}' if rows else f'  ── {k} 无')
    for r in rows:
        ct = (r[2] or '').replace('\n', ' ')[:100]
        p(f'    [{ts(r[0])}] {r[1]:<5}{ct}')

# ---------- 3. 陈昶文 按月 ----------
p('')
p('=' * 84)
p('三、★ 陈昶文「没时间泡」验证：他本人的整体消息量 vs 陈昶文会话')
p('=' * 84)
t = tid.get('陈昶文')
if t:
    bym = collections.Counter()
    for (tt,) in c.execute('select ts from messages where session_key=?', (t,)):
        bym[datetime.datetime.fromtimestamp(int(tt)).strftime('%Y-%m')] += 1
    p('  陈昶文会话 按月：')
    for k in sorted(bym):
        p(f'    {k}  {"█"*max(1,bym[k]//20)} {bym[k]}')
p('')
p('  ★ 他的全部消息 按月（含所有会话）：')
allm = collections.Counter()
for (tt,) in c.execute('select ts from messages'):
    allm[datetime.datetime.fromtimestamp(int(tt)).strftime('%Y-%m')] += 1
for k in sorted(allm):
    p(f'    {k}  {"█"*max(1,allm[k]//2000)} {allm[k]}')
p('')
p('  ★ 他的消息 按周（2026-05 → 2026-10）：')
wk = collections.Counter()
for (tt,) in c.execute("select ts from messages where ts >= ?", (int(datetime.datetime(2026,5,1).timestamp()),)):
    d0 = datetime.datetime.fromtimestamp(int(tt))
    wk[d0.strftime('%Y-%m-%d')[:10]] += 1
# 按周聚合
wk2 = collections.Counter()
for (tt,) in c.execute("select ts from messages where ts >= ?", (int(datetime.datetime(2026,5,1).timestamp()),)):
    d0 = datetime.datetime.fromtimestamp(int(tt))
    y, w, _ = d0.isocalendar()
    wk2[f'{y}-W{w:02d}'] += 1
for k in sorted(wk2):
    p(f'    {k}  {"█"*max(1,wk2[k]//500)} {wk2[k]}')

# ---------- 4. 关键词搜「坑/借/还/骗」 ----------
p('')
p('=' * 84)
p('四、★ 全库关键词扫描（私聊+群聊）')
p('=' * 84)
for kw in ['坑', '借我', '还我', '还钱', '骗', '拉黑', '互删']:
    rows = list(c.execute("select session_key, ts, role, content from messages where content like ? order by ts desc limit 12", (f'%{kw}%',)))
    n = c.execute("select count(*) from messages where content like ?", (f'%{kw}%',)).fetchone()[0]
    p(f'  ── 「{kw}」命中 {n} 条，最近 12：')
    for sk, t2, rl, ct in rows:
        nm = dict(c.execute('select talker, display_name from sessions')).get(sk, sk)
        p(f'    [{ts(t2)}] {str(nm)[:14]:<16}{rl:<5}{(ct or "").replace(chr(10)," ")[:80]}')

# ---------- 5. 央美赛道「断联」名单 ----------
p('')
p('=' * 84)
p('五、★ 央美相关会话的最后消息时间（看谁已经断了）')
p('=' * 84)
rows = list(c.execute("""select talker, display_name, message_count, last_ts from sessions
                         where session_type='私聊' and message_count >= 100 order by last_ts desc"""))
for sk, dn, mc, lt in rows[:80]:
    p(f"  {ts(lt)[:10]}  {mc:>5} 条  {str(dn)[:26]}")

con.close()
open(os.path.join(WS, '_tmp', 'tongmen.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
print(buf.getvalue()[:2500])
