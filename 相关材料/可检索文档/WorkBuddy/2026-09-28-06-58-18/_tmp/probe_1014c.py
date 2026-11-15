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

# ---------- A) 洪佳锐 游戏线索 ----------
p('#### 洪佳锐 全量 484 条中的「游戏/玩/打」线索 ####')
tal = 'wxid_za4h3q0orh8o22'
kws = ('游戏', '打', '开黑', '联机', 'steam', '王者', '英雄联盟', 'CS', '瓦', '永劫', '原神', '崩', '无畏', '吃鸡', '手游', '氪', '局')
rows = d.execute("select ts, role, substr(content,1,90) from messages where session_key=? order by ts asc", (tal,)).fetchall()
hit = 0
for r in rows:
    txt = r[2] or ''
    if any(k in txt for k in kws):
        hit += 1
        if hit <= 40:
            p('   %s [%s] %s' % (ts2s(r[0]), r[1], txt))
p('  → 命中 %d / %d' % (hit, len(rows)))

# ---------- B) 洪佳锐 所在的群 ----------
p()
p('#### 洪佳锐 作为 sender 出现的会话 ####')
for r in d.execute("select m.session_key, s.display_name, count(*) from messages m left join sessions s on s.talker=m.session_key where m.sender=? group by m.session_key order by count(*) desc limit 15", (tal,)):
    p('   %s | %s | %d' % (r[0], r[1], r[2]))

# ---------- C) 近 7 天全库搜「打」「昂」 ----------
t7 = int(time.mktime(time.strptime('2026-10-07', '%Y-%m-%d')))
for kw in ('打', '昂', '游戏', '滑雪', '雪'):
    p()
    p('#### 近 7 天全库搜「%s」（仅私聊/非公众号）####' % kw)
    rows = d.execute("select m.session_key, s.display_name, m.ts, m.role, substr(m.content,1,60) from messages m left join sessions s on s.talker=m.session_key where m.content like ? and m.ts>=? and m.session_key not like 'gh_%' order by m.ts desc limit 20", ('%'+kw+'%', t7)).fetchall()
    p('  命中 %d' % len(rows))
    for r in rows:
        p('   %s|%s %s [%s] %s' % ((r[0] or '')[:26], r[1], ts2s(r[2]), r[3], r[4]))

# ---------- D) sns.db ----------
p()
p('#### sns.db 位置 ####')
sns = glob.glob(os.path.join(DEC, '**', 'sns.db'), recursive=True)
for f in sns:
    p('   %s (%.1f MB)' % (f, os.path.getsize(f)/1048576.0))

# ---------- E) 朋友圈 JSON 里找 柯益盈 / 马思然 ----------
p()
p('#### 朋友圈 JSON 检索 ####')
F = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json'
try:
    j = json.load(io.open(F, 'r', encoding='utf-8'))
    posts = j.get('posts', [])
    p('  总帖 %d' % len(posts))
    keys = set()
    for po in posts[:1]:
        keys = set(po.keys())
    p('  字段: %s' % sorted(keys))
    for kw in ('柯益盈', '秋裤', '马思然', 'Marson', 'kyy'):
        n = 0
        for po in posts:
            blob = json.dumps(po, ensure_ascii=False)
            if kw in blob:
                n += 1
                if n <= 8:
                    p('   [%s] %s | %s | %s' % (kw, po.get('nickname'), po.get('createTimeStr'), (po.get('contentDesc') or '')[:80]))
        p('  「%s」命中 %d 帖' % (kw, n))
except Exception as e:
    p('  ERR %s' % e)

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1014c.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out))
