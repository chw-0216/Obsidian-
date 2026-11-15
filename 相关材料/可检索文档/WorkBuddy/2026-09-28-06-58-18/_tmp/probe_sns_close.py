# -*- coding: utf-8 -*-
import sqlite3, datetime, io, os

IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
SNS = DEC + '/sns/sns.db'

def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

PEOPLE = [('wxid_f77sxlrwo0tr12', '李紫懿'), ('wxid_utdeb3kw2z5j22', '朱子涵')]
out = []
def P(*a): out.append(' '.join(str(x) for x in a))

# ---------- 1) index.sqlite: 消息 ----------
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
P('===== 1) 消息往来 =====')
for wx, nm in PEOPLE:
    rows = i.execute("select ts, role, type, content from messages where session_key=? order by ts", (wx,)).fetchall()
    P('--- %s  共 %d 条 ---' % (nm, len(rows)))
    if rows:
        P('  首: %s  %s' % (ts2s(rows[0][0]), (rows[0][3] or '')[:70]))
        P('  末: %s  %s' % (ts2s(rows[-1][0]), (rows[-1][3] or '')[:70]))
        # 最后 12 条
        P('  【最后 12 条】')
        for ts, role, typ, c in rows[-12:]:
            P('    [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n', ' ')[:95]))
        # 按年统计
        from collections import OrderedDict
        d = OrderedDict()
        for ts, role, typ, c in rows:
            k = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m')
            d.setdefault(k, [0, 0]); d[k][0] += 1
            if role == 'me': d[k][1] += 1
        P('  按月: ' + ' · '.join('%s:%d(我%d)' % (k, v[0], v[1]) for k, v in d.items()))

# ---------- 2) sns.db ----------
P('')
P('===== 2) sns.db（朋友圈本地痕迹） =====')
try:
    d = sqlite3.connect('file:%s?mode=ro' % SNS, uri=True)
    tabs = [r[0] for r in d.execute("select name from sqlite_master where type='table'")]
    P('  tables:', tabs)
    for wx, nm in PEOPLE:
        P('--- %s (%s) ---' % (nm, wx))
        for t in tabs:
            cols = [r[1] for r in d.execute('pragma table_info("%s")' % t)]
            hit = [c for c in cols if 'user' in c.lower() or 'name' in c.lower()]
            for c in hit:
                try:
                    n = d.execute('select count(*) from "%s" where "%s"=?' % (t, c), (wx,)).fetchone()[0]
                    if n:
                        P('    %s.%s = %d 条' % (t, c, n))
                        if t == 'SnsTopItem_1':
                            for r in d.execute('select create_time, last_read_time, is_read, summary from SnsTopItem_1 where "%s"=? order by create_time' % c, (wx,)):
                                P('       create=%s read=%s isread=%s summary=%r' % (
                                    ts2s(r[0]) if r[0] else '—',
                                    ts2s(r[1]) if r[1] else '—',
                                    r[2], (r[3] or '')[:40]))
                        if t == 'SnsTimeLine':
                            for r in d.execute('select tid, content, pack_info_buf from SnsTimeLine where "%s"=? limit 5' % c, (wx,)):
                                P('       tid=%s content=%r' % (r[0], (r[1] or '')[:60]))
                except Exception as e:
                    pass
    # SnsMessage_tmp3 全表看结构
    if 'SnsMessage_tmp3' in tabs:
        cols = [r[1] for r in d.execute('pragma table_info("SnsMessage_tmp3")')]
        P('  SnsMessage_tmp3 cols:', cols)
        n = d.execute('select count(*) from SnsMessage_tmp3').fetchone()[0]
        P('  SnsMessage_tmp3 rows:', n)
        for wx, nm in PEOPLE:
            for c in cols:
                if 'user' in c.lower():
                    try:
                        n2 = d.execute('select count(*) from SnsMessage_tmp3 where "%s"=?' % c, (wx,)).fetchone()[0]
                        if n2: P('    %s.%s = %d' % ('SnsMessage_tmp3', c, n2))
                    except Exception: pass
except Exception as e:
    P('  sns ERR', e)

# ---------- 3) contact 字段 ----------
P('')
P('===== 3) contact 里的字段（找朋友圈可见性痕迹） =====')
DECU = DEC.replace('\\', '/')
try:
    d2 = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DECU, uri=True)
    cols = [r[1] for r in d2.execute('pragma table_info(contact)')]
    P('  contact cols:', cols)
    for wx, nm in PEOPLE:
        r = d2.execute('select * from contact where username=?', (wx,)).fetchone()
        if r:
            P('--- %s ---' % nm)
            for k, v in zip(cols, r):
                if k in ('username',): continue
                if v in (None, '', 0, b''): continue
                P('    %-22s %r' % (k, v if not isinstance(v, bytes) else v[:60]))
except Exception as e:
    P('  ERR', e)

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_sns_close.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
