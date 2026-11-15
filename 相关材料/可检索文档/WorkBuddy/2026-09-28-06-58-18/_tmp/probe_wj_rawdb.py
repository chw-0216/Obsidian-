# -*- coding: utf-8 -*-
"""在解密原始库中定位 周雯娟：Msg_<md5(talker)> 表 + session 表"""
import sqlite3, hashlib, os, io

DEC = r'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
WX = 'wxid_uhulgmrvfq4a12'
LBW = 'wxid_4yurl8wrbi4a22'
CSMQ = 'wxid_j5ekmvhqltug22'   # 程颂孟秋

out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

def tname(wx):
    return 'Msg_' + hashlib.md5(wx.encode()).hexdigest()

P('=== 目标表名 ===')
for nm, wx in [('周雯娟', WX), ('李博文', LBW), ('程颂孟秋', CSMQ)]:
    P('  %s -> %s' % (nm, tname(wx)))

P('')
P('=== 解密库目录 ===')
for d in sorted(os.listdir(DEC)):
    p = os.path.join(DEC, d)
    if os.path.isdir(p):
        P('  %-14s %s' % (d, ', '.join(sorted(os.listdir(p))[:12])))

P('')
P('=== 在 message_*.db 中找目标表 ===')
for f in ('message_0.db', 'message_1.db'):
    fp = '%s/message/%s' % (DEC, f)
    if not os.path.exists(fp):
        P('%s 不存在' % f); continue
    try:
        c = sqlite3.connect('file:%s?mode=ro' % fp, uri=True)
    except Exception as e:
        P('%s 打不开: %s' % (f, e)); continue
    tabs = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    P('%s: 共 %d 表' % (f, len(tabs)))
    for nm, wx in [('周雯娟', WX), ('李博文', LBW), ('程颂孟秋', CSMQ)]:
        t = tname(wx)
        if t in tabs:
            n = c.execute('select count(*) from "%s"' % t).fetchone()[0]
            P('   ✓ %s (%s) 存在 · %d 行' % (nm, t, n))
        else:
            P('   ✗ %s (%s) 无表' % (nm, t))
    c.close()

P('')
P('=== session 目录 ===')
sd = '%s/session' % DEC
if os.path.isdir(sd):
    for f in sorted(os.listdir(sd)):
        P('  ', f)
        fp = os.path.join(sd, f)
        if f.endswith('.db'):
            try:
                c = sqlite3.connect('file:%s?mode=ro' % fp, uri=True)
                for (n,) in c.execute("select name from sqlite_master where type='table'"):
                    cols = [x[1] for x in c.execute('pragma table_info("%s")' % n)]
                    cnt = c.execute('select count(*) from "%s"' % n).fetchone()[0]
                    P('     %-24s %7d  %s' % (n, cnt, ','.join(cols)[:100]))
                    if 'username' in cols and cnt > 0:
                        r = c.execute('select * from "%s" where username=?' % n, (WX,)).fetchone()
                        P('        -> 周雯娟: %s' % (r,))
                        r2 = c.execute('select * from "%s" where username=?' % n, (LBW,)).fetchone()
                        P('        -> 李博文: %s' % (r2,))
                c.close()
            except Exception as e:
                P('     err:', e)

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_wj_rawdb.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_wj_rawdb.txt')
