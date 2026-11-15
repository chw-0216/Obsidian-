# -*- coding: utf-8 -*-
"""只读补齐2：filehelper / 未知新群 / 今日 me 消息中的请假与自述"""
import sqlite3, datetime, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
c = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
TZ = datetime.timezone(datetime.timedelta(hours=8))
def ts(t): return datetime.datetime.fromtimestamp(int(t), tz=TZ).strftime('%Y-%m-%d %H:%M:%S')
def day(s): return int(datetime.datetime.strptime(s,'%Y-%m-%d').replace(tzinfo=TZ).timestamp())
D22 = day('2026-10-22'); D23 = day('2026-10-23')

def show(talker, title, since, limit=400):
    print(f'\n===== {title} | {talker} =====')
    for i, r in enumerate(c.execute('select ts, role, type, sender, content from messages where session_key=? and ts>=? order by ts', (talker, since))):
        if i >= limit: print('...[limit]'); break
        content = (r[4] or '').replace('\n', ' ')
        if len(content) > 500: content = content[:500] + '…'
        print(f'[{ts(r[0])}] {r[1]}/{r[2]} | {content}')

show('filehelper', '文件传输助手 10-22 起', D22)
show('44223351827@chatroom', '新群A 44223351827（10-22 22:19 建）', D22, 60)
show('19944550391@chatroom', '新群B 19944550391（10-22 10:19）', D22, 60)
show('45490054651@chatroom', '未知群 45490054651（10-23 活跃）', D22, 60)

print('\n===== 10-22 起「我」发的消息里含 请假/抱歉/老师/馆 的（跨会话） =====')
n=0
for r in c.execute("""select m.session_key, s.display_name, m.ts, m.content from messages m
                      left join sessions s on s.talker=m.session_key
                      where m.ts>=? and m.role='me' and m.type='text'
                        and (m.content like '%请假%' or m.content like '%抱歉%' or m.content like '%不好意思%'
                             or m.content like '%馆%' or m.content like '%开幕式%' or m.content like '%发布会%'
                             or m.content like '%读书周%' or m.content like '%留%')
                      order by m.ts""", (D22,)):
    content=(r[3] or '').replace('\n',' ')
    if len(content)>260: content=content[:260]+'…'
    print(f'[{ts(r[2])}] {r[0]} | {r[1]} | {content}')
    n+=1
    if n>=120: break

print('\n===== 贺伊飞语音/通话明细（体积、时长） =====')
import re
for r in c.execute("select ts, type, content from messages where session_key='hyf782877122' order by ts"):
    if r[1] in ('voice','voicecall','video'):
        m = re.search(r'voicelength="(\d+)"', r[2] or '')
        v = re.search(r'playlength="(\d+)"', r[2] or '')
        print(ts(r[0]), r[1], '语音毫秒=' + (m.group(1) if m else '-'), '视频秒=' + (v.group(1) if v else '-'))
