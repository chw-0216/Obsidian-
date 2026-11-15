# -*- coding: utf-8 -*-
import sqlite3, datetime, io

IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'

def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

out = []
def P(*a): out.append(' '.join(str(x) for x in a))

i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
d = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC.replace('\\','/'), uri=True)

# ---------- 1) 李佳杨 ----------
P('===== 1) 李佳杨（不是"阳"） =====')
for kw in ('李佳杨',):
    rows = d.execute("select username, remark, nick_name, alias from contact where remark like ? or nick_name like ? or alias like ?",
                     ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')).fetchall()
    P('  contact 命中 %d 条' % len(rows))
    for r in rows[:6]:
        P('   ', r)
        tk = r[0]
        s = i.execute("select count(*), sum(role='me'), min(ts), max(ts) from messages where session_key=?", (tk,)).fetchone()
        P('     消息 %s 条 · 我发 %s · %s → %s' % (s[0], s[1], ts2s(s[2]) if s[2] else '—', ts2s(s[3]) if s[3] else '—'))
        for ts, role, c in i.execute("select ts, role, content from messages where session_key=? order by ts desc limit 10", (tk,)):
            P('      [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:110]))
    # 群里出现
    g = i.execute("select distinct session_key from messages where content like ? limit 5", ('%'+kw+'%',)).fetchall()
    P('   出现于:', [x[0] for x in g])
    # 全库「李佳杨」消息
    n = i.execute("select count(*) from messages where content like ?", ('%李佳杨%',)).fetchone()[0]
    P('   全库提到「李佳杨」 %d 次' % n)

# ---------- 2) 徐嘉良 私聊全貌 ----------
P('')
P('===== 2) 徐嘉良 私聊全貌 =====')
tk = 'wxid_1fhmdn4x05hi11'
s = i.execute("select count(*), sum(role='me'), min(ts), max(ts) from messages where session_key=?", (tk,)).fetchone()
P('  消息 %s 条 · 我发 %s · %s → %s' % (s[0], s[1], ts2s(s[2]), ts2s(s[3])))
for ts, role, c in i.execute("select ts, role, content from messages where session_key=? order by ts asc limit 40", (tk,)):
    P('   [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:120]))

# ---------- 3) 抽烟（本人 me 全时段） ----------
P('')
P('===== 3) 抽烟（role=me 全时段） =====')
for kw in ('烟', '抽', '烟瘾', '打火机', '利群', '中华烟'):
    rows = i.execute("select ts, session_key, content from messages where role='me' and content like ? order by ts desc limit 12", ('%'+kw+'%',)).fetchall()
    if rows:
        P('  --- %s ---' % kw)
        for ts, sk, c in rows:
            P('   [%s] %-24s %s' % (ts2s(ts), sk[:24], (c or '').replace('\n',' ')[:100]))

# ---------- 4) 舒泽林 转账去重统计 ----------
P('')
P('===== 4) 舒泽林 转账（去重：同秒同内容算一笔） =====')
tk = 'wxid_0ejd54z34nmv32'
rows = i.execute("""select ts, role, content from messages where session_key=?
    and content like '%转账%' order by ts asc""", (tk,)).fetchall()
seen = set(); dedup = []
for ts, role, c in rows:
    k = (ts, (c or '').strip())
    if k in seen: continue
    seen.add(k); dedup.append((ts, role, c))
P('  原始 %d 行 → 去重 %d 笔' % (len(rows), len(dedup)))
import re
tot = 0
for ts, role, c in dedup:
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)元', c or '')
    amt = float(m.group(1)) if m else 0
    tot += amt
    P('   [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:80]))
P('  ★ 金额合计（含双计风险）: %.2f' % tot)

# ---------- 5) 群定位 ----------
P('')
P('===== 5) 相关群定位 =====')
for g in ('57413014124@chatroom', '47564321348@chatroom', '57406823059@chatroom', '4546424707@chatroom', '49693708384@chatroom'):
    r = i.execute("select display_name, message_count, first_ts, last_ts from sessions where talker=?", (g,)).fetchone()
    if r:
        P('  %s → %s · %s 条 · %s → %s' % (g, r[0], r[1], ts2s(r[2]) if r[2] else '—', ts2s(r[3]) if r[3] else '—'))
    else:
        P('  %s → (sessions 无)' % g)
    # contact 侧群名
    c = d.execute("select nick_name, remark from contact where username=?", (g,)).fetchone()
    if c: P('        contact: nick=%s remark=%s' % (c[0], c[1]))

# ---------- 6) 群里「车」「开车」「搭车」相关（近 60 天） ----------
P('')
P('===== 6) 群内「车」相关（近 60 天 · 限本人所在群） =====')
for ts, sk, role, c in i.execute("""select ts, session_key, role, content from messages
    where ts > ? and (content like '%车%') and session_key like '%chatroom'
    order by ts desc limit 25""", (int(datetime.datetime(2026,8,15).timestamp()),)):
    P('   [%s] %-24s %-4s %s' % (ts2s(ts), sk[:24], role, (c or '').replace('\n',' ')[:110]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1013d.txt','w',encoding='utf-8').write('\n'.join(out))
print('OK lines=%d' % len(out))
