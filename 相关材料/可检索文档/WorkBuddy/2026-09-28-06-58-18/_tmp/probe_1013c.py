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

# ---------- 1) 找人 ----------
P('===== 1) 找人（李佳阳 / 徐嘉良 / 舒泽林） =====')
for kw in ('李佳阳', '徐嘉良', '舒泽林'):
    P('--- %s ---' % kw)
    rows = d.execute("select username, remark, nick_name, alias from contact where remark like ? or nick_name like ? or alias like ?",
                     ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')).fetchall()
    for r in rows[:6]:
        P('   contact:', r)
        tk = r[0]
        s = i.execute("select count(*), sum(role='me'), min(ts), max(ts) from messages where session_key=?", (tk,)).fetchone()
        P('    消息 %s 条 · 我发 %s · %s → %s' % (s[0], s[1], ts2s(s[2]) if s[2] else '—', ts2s(s[3]) if s[3] else '—'))
        if s[0]:
            for ts, role, typ, c in i.execute("select ts, role, type, content from messages where session_key=? order by ts desc limit 8", (tk,)):
                P('      [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:100]))
    # 群里也搜
    g = i.execute("select distinct session_key from messages where content like ? limit 3", ('%'+kw+'%',)).fetchall()
    if g: P('   出现在群/会话:', [x[0] for x in g])

# ---------- 2) 舒泽林 转账 ----------
P('')
P('===== 2) 舒泽林 往来（钱） =====')
for kw in ('舒泽林',):
    rows = d.execute("select username, remark, nick_name from contact where remark like ? or nick_name like ?", ('%'+kw+'%','%'+kw+'%')).fetchall()
    for r in rows[:4]:
        tk = r[0]
        P('  %s (%s)' % (r[1] or r[2], tk))
        for ts, role, typ, c in i.execute("select ts, role, type, content from messages where session_key=? and (content like '%转账%' or content like '%元' or content like '%块' or content like '%还%' or content like '%借%') order by ts desc limit 25", (tk,)):
            P('    [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:130]))

# ---------- 3) 全库搜「300」相关还钱 ----------
P('')
P('===== 3) 全库搜「还」「300」「借」近 30 天 =====')
for ts, sk, role, c in i.execute("""select ts, session_key, role, content from messages
    where ts > ? and (content like '%该还%' or content like '%还你%' or content like '%还钱%' or content like '%欠%' or content like '%借%')
    order by ts desc limit 25""", (int(datetime.datetime(2026,9,1).timestamp()),)):
    P('  [%s] %-26s %-4s %s' % (ts2s(ts), sk[:26], role, (c or '').replace('\n',' ')[:110]))

# ---------- 4) 抽烟 ----------
P('')
P('===== 4) 全库搜「烟」（本人相关） =====')
for ts, sk, role, c in i.execute("""select ts, session_key, role, content from messages
    where content like '%烟%' and role in ('me','them') order by ts desc limit 30"""):
    P('  [%s] %-24s %-4s %s' % (ts2s(ts), sk[:24], role, (c or '').replace('\n',' ')[:100]))

# ---------- 5) 徐嘉良 在群里的角色 ----------
P('')
P('===== 5) 徐嘉良 近期群内出现 =====')
for ts, sk, role, c in i.execute("""select ts, session_key, role, content from messages
    where content like '%徐嘉良%' order by ts desc limit 15"""):
    P('  [%s] %-24s %-4s %s' % (ts2s(ts), sk[:24], role, (c or '').replace('\n',' ')[:110]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1013c.txt','w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
