# -*- coding: utf-8 -*-
import sqlite3, io, os, time

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
CON = os.path.join(DEC, 'contact', 'contact.db')

out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try:
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(int(t)))
    except Exception:
        return str(t)

d = sqlite3.connect(IDX)
c = sqlite3.connect(CON)

# ---------- A) 澜沧 全库 ----------
p('#### 全库搜「澜沧」（不限时间）####')
rows = d.execute("select session_key, ts, role, substr(content,1,80) from messages where content like '%澜沧%' order by ts desc limit 40").fetchall()
p('  命中 %d' % len(rows))
for r in rows:
    p('   %s %s [%s] %s' % ((r[0] or '')[:26], ts2s(r[1]), r[2], r[3]))

# ---------- B) 笑一 最近 40 条 ----------
tal = 'wxid_wdnk6ue9kiyn22'
p()
p('#### 笑一 最近 40 条 ####')
for r in d.execute("select ts, role, type, substr(content,1,90) from messages where session_key=? order by ts desc limit 40", (tal,)):
    p('   %s [%s/%s] %s' % (ts2s(r[0]), r[1], r[2], r[3]))

# ---------- C) 笑一 搜「汇报/PPT/澜沧」 ----------
p()
p('#### 笑一 会话内搜「汇报 / ppt / 澜沧 / 展」 ####')
for kw in ('汇报', 'ppt', 'PPT', '澜沧', '展'):
    rows = d.execute("select ts, role, substr(content,1,80) from messages where session_key=? and content like ? order by ts desc limit 12", (tal, '%'+kw+'%')).fetchall()
    p('  --- %s: %d 条 ---' % (kw, len(rows)))
    for r in rows:
        p('   %s [%s] %s' % (ts2s(r[0]), r[1], r[2]))

# ---------- D) 朱子涵 最近 20 条 ----------
p()
p('#### 朱子涵 最近 20 条 ####')
for r in d.execute("select ts, role, type, substr(content,1,90) from messages where session_key='wxid_utdeb3kw2z5j22' order by ts desc limit 20"):
    p('   %s [%s/%s] %s' % (ts2s(r[0]), r[1], r[2], r[3]))

# ---------- E) 朱子涵 搜 ppt/汇报 ----------
p()
p('#### 朱子涵 搜「ppt/汇报/作业」 ####')
for kw in ('ppt', 'PPT', '汇报', '作业'):
    rows = d.execute("select ts, role, substr(content,1,80) from messages where session_key='wxid_utdeb3kw2z5j22' and content like ? order by ts desc limit 10", ('%'+kw+'%',)).fetchall()
    p('  --- %s: %d ---' % (kw, len(rows)))
    for r in rows:
        p('   %s [%s] %s' % (ts2s(r[0]), r[1], r[2]))

# ---------- F) 班群里 ppt / 汇报 ----------
p()
p('#### 班群搜「ppt/汇报」（近 60 天）####')
t60 = int(time.mktime(time.strptime('2026-08-15', '%Y-%m-%d')))
for kw in ('ppt', 'PPT', '汇报'):
    rows = d.execute("select session_key, ts, role, substr(content,1,70) from messages where content like ? and ts>=? and session_key like '%@chatroom' order by ts desc limit 15", ('%'+kw+'%', t60)).fetchall()
    p('  --- %s: %d ---' % (kw, len(rows)))
    for r in rows:
        p('   %s %s [%s] %s' % ((r[0] or '')[:26], ts2s(r[1]), r[2], r[3]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014f.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
