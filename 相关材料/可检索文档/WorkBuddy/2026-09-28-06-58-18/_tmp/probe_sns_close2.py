# -*- coding: utf-8 -*-
import sqlite3, datetime, io

DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'
SNS = DEC + '/sns/sns.db'
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'

def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

PEOPLE = [('wxid_f77sxlrwo0tr12', '李紫懿'), ('wxid_utdeb3kw2z5j22', '朱子涵'),
          ('wxid_uhulgmrvfq4a12', '周雯娟(对照)')]
out = []
def P(*a): out.append(' '.join(str(x) for x in a))

d = sqlite3.connect('file:%s?mode=ro' % SNS, uri=True)

for t in ('SnsUserTimeLineBreakFlagV2', 'SnsMainTimeLineBreakFlag', 'SnsIgnoredDataItem'):
    cols = [r[1] for r in d.execute('pragma table_info("%s")' % t)]
    n = d.execute('select count(*) from "%s"' % t).fetchone()[0]
    P('===== %s  rows=%d =====' % (t, n))
    P('  cols:', cols)
    # 全表前 30 行
    for r in d.execute('select * from "%s" limit 30' % t):
        P('   ', [ts2s(v) if isinstance(v, int) and v > 1e9 else v for v in r])
    # 按人查
    for wx, nm in PEOPLE:
        for c in cols:
            if 'user' in c.lower() or 'name' in c.lower():
                try:
                    rs = d.execute('select * from "%s" where "%s"=?' % (t, c), (wx,)).fetchall()
                    if rs:
                        P('  ★ %s 命中 %s.%s (%d):' % (nm, t, c, len(rs)))
                        for r in rs[:5]:
                            P('     ', [ts2s(v) if isinstance(v, int) and v > 1e9 else v for v in r])
                except Exception:
                    pass
    P('')

# SnsMessage_tmp3 里朱子涵那条
P('===== SnsMessage_tmp3 朱子涵那条 =====')
cols = [r[1] for r in d.execute('pragma table_info("SnsMessage_tmp3")')]
for r in d.execute("select * from SnsMessage_tmp3 where from_username='wxid_utdeb3kw2z5j22'"):
    for k, v in zip(cols, r):
        if v not in (None, '', 0, b''):
            P('   %-24s %r' % (k, v if not isinstance(v, bytes) else v[:80]))

# 对照：SnsMessage_tmp3 全部 from_username 分布（谁点赞/评论过他）
P('')
P('===== 谁点赞/评论过他（SnsMessage_tmp3 from_username TOP） =====')
for r in d.execute("""select from_username, from_nickname, count(*) c, min(create_time), max(create_time)
                      from SnsMessage_tmp3 group by from_username order by c desc limit 25"""):
    P('   %-26s %-14s %3d  %s → %s' % (r[0], (r[1] or '')[:12], r[2], ts2s(r[3]), ts2s(r[4])))

# SnsTimeLine 里搜这两人的任何痕迹
P('')
P('===== SnsTimeLine 搜两人 =====')
for wx, nm in PEOPLE[:2]:
    for r in d.execute("select tid, user_name, content from SnsTimeLine where user_name=? or content like ?", (wx, '%' + wx + '%')):
        P('  ', nm, r[0], (r[2] or '')[:70])

# 消息里搜"朋友圈""屏蔽""拉黑"
P('')
P('===== 消息里搜「朋友圈/屏蔽/拉黑/仅三天」 =====')
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
for kw in ('屏蔽', '拉黑', '仅三天', '三天可见', '朋友圈'):
    rows = i.execute("select ts, session_key, role, content from messages where content like ? order by ts limit 8", ('%' + kw + '%',)).fetchall()
    P('  【%s】%d 条（显示前 8）' % (kw, len(rows)))
    for ts, sk, role, c in rows:
        P('     [%s] %-24s %-4s %s' % (ts2s(ts), sk[:24], role, (c or '').replace('\n', ' ')[:90]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_sns_close2.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
