# -*- coding: utf-8 -*-
import sqlite3, io, os, time, json

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
SNS = os.path.join(DEC, 'sns', 'sns.db')

out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try:
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception:
        return str(t)

d = sqlite3.connect(IDX)

# ---------- A) sns.db 结构 ----------
p('#### sns.db 表 ####')
s = sqlite3.connect(SNS)
for r in s.execute("select name from sqlite_master where type='table' order by name"):
    try:
        n = s.execute('select count(*) from "%s"' % r[0]).fetchone()[0]
    except Exception:
        n = -1
    p('   %-40s %d' % (r[0], n))

for t in ('SnsTimeLine', 'SnsTopItem_1', 'SnsMessage_tmp3'):
    p()
    p('#### %s cols ####' % t)
    try:
        p('   ', [x[1] for x in s.execute('pragma table_info(%s)' % t)])
        p('   ---- 最近 12 行（按时间倒） ----')
        cols = [x[1] for x in s.execute('pragma table_info(%s)' % t)]
        tcol = 'create_time' if 'create_time' in cols else ('createTime' if 'createTime' in cols else None)
        q = 'select * from %s %s limit 12' % (t, ('order by %s desc' % tcol) if tcol else '')
        for r in s.execute(q):
            p('   ', str(r)[:300])
    except Exception as e:
        p('   ERR', e)

# ---------- B) 柯益盈 / 马思然 在 sns 的痕迹 ----------
p()
p('#### sns 里搜柯益盈/马思然/秋裤 ####')
for t in ('SnsTimeLine', 'SnsTopItem_1', 'SnsMessage_tmp3'):
    try:
        cols = [x[1] for x in s.execute('pragma table_info(%s)' % t)]
        txtcols = [c for c in cols if c.lower() in ('content', 'summary', 'from_nickname', 'to_nickname', 'nickname', 'user_name', 'username')]
        for kw in ('柯益盈', '马思然', '秋裤', '5049180491911', '6379463789322'):
            for tc in txtcols:
                try:
                    rows = s.execute('select * from %s where "%s" like ? limit 6' % (t, tc), ('%'+kw+'%',)).fetchall()
                    if rows:
                        p('   [%s.%s] %s → %d 行' % (t, tc, kw, len(rows)))
                        for r in rows:
                            p('      ', str(r)[:280])
                except Exception:
                    pass
    except Exception as e:
        p('   ERR', e)

# ---------- C) 今天（10-14）消息统计 ----------
p()
p('#### 10-14 今日消息（按会话）####')
t0 = int(time.mktime(time.strptime('2026-10-14 00:00', '%Y-%m-%d %H:%M')))
rows = d.execute("select m.session_key, s.display_name, count(*) from messages m left join sessions s on s.talker=m.session_key where m.ts>=? group by m.session_key order by count(*) desc limit 25", (t0,)).fetchall()
p('  会话数 %d' % len(rows))
for r in rows:
    p('   %s|%s %d' % ((r[0] or '')[:30], r[1], r[2]))

# ---------- D) 近 3 天 我 自己发的消息 ----------
p()
p('#### 近 3 天 我 发的消息（前 40）####')
t3 = int(time.mktime(time.strptime('2026-10-11', '%Y-%m-%d')))
rows = d.execute("select m.session_key, s.display_name, m.ts, substr(m.content,1,70) from messages m left join sessions s on s.talker=m.session_key where m.role='me' and m.ts>=? and m.session_key not like 'gh_%' order by m.ts desc limit 40", (t3,)).fetchall()
for r in rows:
    p('   %s %s|%s %s' % (ts2s(r[2]), (r[0] or '')[:24], r[1], r[3]))

# ---------- E) 柯益盈 251 条 关键节点 ----------
p()
p('#### 柯益盈 私聊 前 30 条（时间正序）####')
tal = 'wxid_5049180491911'
for r in d.execute("select ts, role, type, substr(content,1,80) from messages where session_key=? order by ts asc limit 30", (tal,)):
    p('   %s [%s/%s] %s' % (ts2s(r[0]), r[1], r[2], r[3]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014d.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
