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

# ---------- A) 高晓斌 / 李博文 找人 ----------
for kw in ('高晓斌', '高晓彬', '高小斌', '李博文'):
    p()
    p('#### 找人: %s ####' % kw)
    rows = c.execute("select username, remark, nick_name, alias from contact where remark like ? or nick_name like ? or alias like ?",
                     ('%'+kw+'%', '%'+kw+'%', '%'+kw+'%')).fetchall()
    p('  contact 命中 %d' % len(rows))
    for r in rows[:10]:
        p('   ', r)
    rows2 = d.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where display_name like ? or talker like ?",
                      ('%'+kw+'%', '%'+kw+'%')).fetchall()
    p('  sessions 命中 %d' % len(rows2))
    for r in rows2[:10]:
        p('   ', r)
    p('  ---- 消息正文提及（不限时间，前 12）----')
    for r in d.execute("select session_key, ts, role, substr(content,1,70) from messages where content like ? order by ts desc limit 12", ('%'+kw+'%',)):
        p('   %s %s [%s] %s' % ((r[0] or '')[:26], ts2s(r[1]), r[2], r[3]))

# ---------- B) 减肥 / 鲁肽 相关 ----------
for kw in ('减肥', '鲁肽', '司美', '打针', '瘦', '体重', '斤', '胖'):
    p()
    p('#### 全库搜「%s」（不限时间，前 20）####' % kw)
    rows = d.execute("select session_key, ts, role, substr(content,1,70) from messages where content like ? and session_key not like 'gh_%' order by ts desc limit 20", ('%'+kw+'%',)).fetchall()
    p('  命中 %d' % len(rows))
    for r in rows:
        p('   %s %s [%s] %s' % ((r[0] or '')[:26], ts2s(r[1]), r[2], r[3]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014e.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
