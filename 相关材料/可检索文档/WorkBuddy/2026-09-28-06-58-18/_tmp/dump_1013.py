# -*- coding: utf-8 -*-
import sqlite3, io, datetime

IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

TARGETS = [
    ('wxid_utdeb3kw2z5j22', '朱子涵'),
    ('wxid_f77sxlrwo0tr12', '李紫懿'),
    ('wxid_nwcwpgema4rl12', '李紫玥'),
]
for tk, nm in TARGETS:
    rows = i.execute("""select ts, time_text, role, sender, type, content
                        from messages where session_key=? order by ts""", (tk,)).fetchall()
    out = []
    out.append('===== %s (%s) 共 %d 条 =====' % (nm, tk, len(rows)))
    for ts, tt, role, sender, typ, content in rows:
        c = (content or '').replace('\n', ' / ')
        if len(c) > 400: c = c[:400] + '…'
        out.append('[%s] %-4s t%-3s %s' % (ts2s(ts), role, typ, c))
    p = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\dlg_%s.txt' % nm
    io.open(p, 'w', encoding='utf-8').write('\n'.join(out))
    print(nm, len(rows), '->', p)

# 统计李紫懿按月分布
print('\n=== 李紫懿 按月 ===')
rows = i.execute("""select substr(time_text,1,7) m, count(*), sum(role='me'), sum(role='them')
                    from messages where session_key='wxid_f77sxlrwo0tr12' and time_text<>'' group by m order by m""").fetchall()
for r in rows: print('  %s  %4d  我%-4s 她%-4s' % r)
