# -*- coding: utf-8 -*-
import sqlite3, datetime, io

IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
def ts2s(t):
    try: return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)
out=[]; P=lambda *a: out.append(' '.join(str(x) for x in a))
i = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)

# 1) 李佳杨 断点前后
P('===== 1) 李佳杨 最后 30 条（2026-04 起） =====')
tk='wxid_sdvbmvwjziaq12'
for ts,role,c in i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc", (tk, int(datetime.datetime(2026,4,1).timestamp()))):
    P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:130]))

# 2) 「李佳杨」在群里的近期（2026-09 起）
P('')
P('===== 2) 群内提到「李佳杨」2026-09 起 =====')
for ts,sk,role,c in i.execute("select ts,session_key,role,content from messages where content like ? and ts>? order by ts desc limit 20", ('%李佳杨%', int(datetime.datetime(2026,9,1).timestamp()))):
    P('  [%s] %-22s %-4s %s' % (ts2s(ts), sk[:22], role, (c or '').replace('\n',' ')[:120]))

# 3) 今日（10-13）两个班群全部消息
P('')
P('===== 3) 今日 10-13 班群消息 =====')
for g in ('57413014124@chatroom','47564321348@chatroom'):
    P('--- %s ---' % g)
    for ts,role,c in i.execute("select ts,role,content from messages where session_key=? and ts>? order by ts asc", (g, int(datetime.datetime(2026,10,13).timestamp()))):
        P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:150]))

# 4) 徐嘉良 × 朱子涵 同组证据（群 57413014124 全量 @分组 名单）
P('')
P('===== 4) 研究方向分组名单（57413014124 含"研究方向"或"@"分组） =====')
for ts,role,c in i.execute("select ts,role,content from messages where session_key=? and content like ? order by ts desc limit 6", ('57413014124@chatroom','%社会美育与乡村振兴%')):
    P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:400]))

# 5) 舒泽林 10-09 那段上下文
P('')
P('===== 5) 舒泽林 2026-10-08~10-09 全量 =====')
for ts,role,c in i.execute("select ts,role,content from messages where session_key=? and ts>? and ts<? order by ts asc", ('wxid_0ejd54z34nmv32', int(datetime.datetime(2026,10,8).timestamp()), int(datetime.datetime(2026,10,10).timestamp()))):
    P('  [%s] %-4s %s' % (ts2s(ts), role, (c or '').replace('\n',' ')[:200]))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_1013e.txt','w',encoding='utf-8').write('\n'.join(out))
print('OK lines=%d' % len(out))
