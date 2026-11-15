# -*- coding: utf-8 -*-
import sqlite3, io, os, time

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
CON = os.path.join(DEC, 'contact', 'contact.db')

out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))

d = sqlite3.connect(IDX)
c = sqlite3.connect(CON)

p('== sessions cols ==')
p([r[1] for r in d.execute('pragma table_info(sessions)')])
p('== messages cols ==')
p([r[1] for r in d.execute('pragma table_info(messages)')])
p()
p('== sessions 样例 ==')
for r in d.execute('select * from sessions limit 3'):
    p('   ', r)
p('== messages 样例 ==')
for r in d.execute('select * from messages order by ts desc limit 3'):
    p('   ', r)

# ---------- 1) 找人 ----------
for kw in ('马思然', '洪佳锐', '洪佳睿', '昂鲁', '柯益盈'):
    p()
    p('#### 找人: %s ####' % kw)
    rows = c.execute("select username, remark, nick_name, alias, local_type from contact where remark like ? or nick_name like ? or alias like ?",
                     ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')).fetchall()
    p('  contact 命中 %d' % len(rows))
    for r in rows[:10]:
        p('   ', r)
    rows2 = d.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where display_name like ? or talker like ?",
                      ('%'+kw+'%', '%'+kw+'%')).fetchall()
    p('  sessions 命中 %d' % len(rows2))
    for r in rows2[:10]:
        p('   ', r)

# ---------- 2) 柯益盈 最近消息 ----------
p()
p('#### 柯益盈 私聊最近 20 条 ####')
tal = 'wxid_5049180491911'
for r in d.execute("select ts, time_text, role, sender, type, substr(content,1,80) from messages where session_key like ? order by ts desc limit 20", ('%'+tal+'%',)):
    p('   ', r)
p()
p('#### 柯益盈 sessions 行 ####')
for r in d.execute("select * from sessions where talker like ?", ('%'+tal+'%',)):
    p('   ', r)

# ---------- 3) 全库搜关键词（近 90 天） ----------
t0 = int(time.mktime(time.strptime('2026-07-01', '%Y-%m-%d')))
for kw in ('滑雪', '马思然', '昂鲁', '洪佳锐', '洪佳睿'):
    p()
    p('#### 全库搜「%s」（ts>=2026-07-01）####' % kw)
    rows = d.execute("select m.session_key, s.display_name, m.ts, m.time_text, m.role, substr(m.content,1,70) from messages m left join sessions s on s.talker=m.session_key where m.content like ? and m.ts>=? order by m.ts desc limit 25",
                     ('%'+kw+'%', t0)).fetchall()
    p('  命中 %d（显示前 25）' % len(rows))
    for r in rows:
        p('   ', r)

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014a.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
