# -*- coding: utf-8 -*-
import sqlite3, datetime, io
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M')
    except Exception: return str(t)
out=[]; P=lambda *a: out.append(' '.join(str(x) for x in a))
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
D0 = int(datetime.datetime(2026,10,13,0,0).timestamp())

def dump(sk, lab, lim=60, w=150):
    P('===== %s (%s) 10-13 =====' % (lab, sk))
    rs = i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc", (sk, D0)).fetchall()
    if not rs: P('  （无）')
    for ts, role, c in rs[:lim]:
        P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:w]))
    P('')

dump('wxid_1wa75s1kze3o22', '母亲-刘丽萍')
dump('filehelper', '文件传输助手')

# 智晓律
r = i.execute("select talker, display_name from sessions where display_name like '%智晓律%' limit 3").fetchall()
P('智晓律会话候选: %s' % r)
for tk, dn in r:
    dump(tk, '智晓律')
    break

# 导！急速回
r = i.execute("select talker, display_name from sessions where display_name like '%急速回%' limit 3").fetchall()
P('「急速回」会话: %s' % r)
for tk, dn in r:
    dump(tk, dn or '急速回')
    break

# 校友会群：只看本人 + @所有人
P('===== 格拉斯哥北京校友会2026 · 10-13（本人 + @所有人） =====')
for ts, role, c in i.execute("""select ts,role,content from messages
    where session_key='25675328414@chatroom' and ts>? and (role='me' or content like '%@所有人%')
    order by ts asc""", (D0,)):
    P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:180]))
P('')
# 找校友会群 talker
r = i.execute("select talker, display_name, message_count from sessions where display_name like '%格拉斯哥北京校友会%' limit 3").fetchall()
P('校友会群: %s' % r)
for tk, dn, mc in r:
    P('  --- %s 10-13 全量前 30 ---' % dn)
    for ts, role, c in i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc limit 30", (tk, D0)):
        P('   [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:150]))
    break

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_latest2.txt','w',encoding='utf-8').write('\n'.join(out))
print('OK lines=%d' % len(out))
