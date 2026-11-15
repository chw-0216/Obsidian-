# -*- coding: utf-8 -*-
import sqlite3, io, os, time, json, glob

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

# ---------- A) contact 表清单 ----------
p('== contact.db 表 ==')
for r in c.execute("select name from sqlite_master where type='table'"):
    p('   ', r[0])

# ---------- B) 洪佳锐 最近 50 条 ----------
p()
p('#### 洪佳锐 私聊最近 50 条 ####')
tal = 'wxid_za4h3q0orh8o22'
rows = d.execute("select ts, role, type, substr(content,1,90) from messages where session_key=? order by ts desc limit 50", (tal,)).fetchall()
for r in rows:
    p('   %s [%s/%s] %s' % (ts2s(r[0]), r[1], r[2], r[3]))
p('  ---- 洪佳锐 最早 5 条 ----')
for r in d.execute("select ts, role, type, substr(content,1,80) from messages where session_key=? order by ts asc limit 5", (tal,)):
    p('   %s [%s/%s] %s' % (ts2s(r[0]), r[1], r[2], r[3]))

# ---------- C) 洪佳锐 按月 ----------
p()
p('#### 洪佳锐 按月 ####')
for r in d.execute("select substr(time_text,1,7) mm, count(*) from messages where session_key=? and time_text<>'' group by mm order by mm", (tal,)):
    p('   ', r)

# ---------- D) 全库搜「昂」不限时间 ----------
p()
p('#### 全库搜「昂」（不限时间）####')
rows = d.execute("select session_key, ts, role, substr(content,1,60) from messages where content like '%昂%' order by ts desc limit 40").fetchall()
p('  命中 %d' % len(rows))
for r in rows:
    p('   %s %s [%s] %s' % (r[0][:28], ts2s(r[1]), r[2], r[3]))

# ---------- E) 马思然 / 柯益盈 在群里的痕迹 ----------
for kw, tal2 in (('马思然', 'wxid_6379463789322'), ('柯益盈', 'wxid_5049180491911')):
    p()
    p('#### %s 作为 sender 出现的群 ####' % kw)
    rows = d.execute("select session_key, count(*) from messages where sender=? group by session_key order by count(*) desc limit 10", (tal2,)).fetchall()
    for r in rows:
        p('   ', r)
    p('#### %s 在消息正文被 @ 或提及（不限时间，前 15）####' % kw)
    rows = d.execute("select session_key, ts, role, substr(content,1,70) from messages where content like ? order by ts desc limit 15", ('%'+kw+'%',)).fetchall()
    for r in rows:
        p('   %s %s [%s] %s' % (r[0][:28], ts2s(r[1]), r[2], r[3]))

# ---------- F) 朋友圈导出文件 ----------
p()
p('#### 朋友圈导出文件 ####')
for f in glob.glob(r'C:\Users\wardc\Desktop\07_聊天记录分析\**\朋友圈*.json', recursive=True):
    p('   %s  (%.1f MB)' % (f, os.path.getsize(f)/1048576.0))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014b.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
