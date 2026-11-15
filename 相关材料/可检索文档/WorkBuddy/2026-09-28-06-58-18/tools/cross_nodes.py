# -*- coding: utf-8 -*-
"""节点身份还原：≥5源全维节点 + 「消息0但朋友圈有互动」隐形层
"""
import sqlite3, os, io, csv, collections

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
SELF_ID = 3641
buf = io.StringIO()
def p(*a):
    buf.write(' '.join(str(x) for x in a) + '\n')

rows = list(csv.DictReader(open(os.path.join(WS, '交叉主表_2026-10-04.csv'), encoding='utf-8-sig')))
for r in rows:
    for k in ('消息数', '语音数', '共同群数', '朋友圈互动', '朋友圈动态', '加我', '转入', '转出'):
        r[k] = int(r[k] or 0)
byid = {r['wxid']: r for r in rows}

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
gname = {t: (n or t) for t, n in con.execute('select talker, display_name from sessions')}
con.close()

cc = sqlite3.connect(f'file:{os.path.join(DEC,"contact","contact.db")}?mode=ro', uri=True)
c1 = cc.cursor()
his_rooms = {r[0] for r in c1.execute('select room_id from chatroom_member where member_id=?', (SELF_ID,))}
rid2u = {i: u for i, u in c1.execute('select id, username from chat_room')}
uid2id = {}
for i, u, rm, nk in c1.execute('select id, username, remark, nick_name from contact'):
    uid2id[u] = (i, rm, nk)
cc.close()

def rooms_of(u):
    t = uid2id.get(u)
    if not t:
        return []
    pid = t[0]
    out = []
    for rid in his_rooms:
        pass
    return out

# 反向：建 person -> rooms
cc = sqlite3.connect(f'file:{os.path.join(DEC,"contact","contact.db")}?mode=ro', uri=True)
c1 = cc.cursor()
pr = collections.defaultdict(list)
for rid, mid in c1.execute('select room_id, member_id from chatroom_member'):
    if rid in his_rooms:
        pr[mid].append(rid)
cc.close()

def info_of(u):
    t = uid2id.get(u)
    if not t:
        return []
    pid, rm, nk = t
    rns = []
    for rid in pr.get(pid, []):
        nm = gname.get(rid2u.get(rid, ''), '')
        if nm:
            rns.append(nm)
    return rns

def show(u, tag):
    r = byid.get(u, {})
    rns = info_of(u)
    p(f"  [{tag}] {r.get('名称','?')}  备注={r.get('备注','')!r}")
    p(f"        消息{r.get('消息数',0)} 语音{r.get('语音数',0)} 共同群{r.get('共同群数',0)} "
      f"圈互{r.get('朋友圈互动',0)} 圈发{r.get('朋友圈动态',0)} 最后={r.get('最后消息','')}")
    p(f"        群({len(rns)})：{' ／ '.join(rns[:14])}")

def nsig(r):
    return sum([r['消息数'] > 0, r['语音数'] > 0, r['共同群数'] > 0,
                r['朋友圈互动'] > 0, r['朋友圈动态'] > 0, r['加我'] > 0, r['转入'] + r['转出'] > 0])

p('=' * 84)
p('一、★ ≥5 源全维节点 —— 身份还原')
p('=' * 84)
for r in sorted(rows, key=lambda x: (-nsig(x), -x['消息数'])):
    if nsig(r) >= 5:
        show(r['wxid'], f"{nsig(r)}源")

p('')
p('=' * 84)
p('二、★★ 「消息 0 条 但朋友圈有互动」的隐形层')
p('=' * 84)
ghost = [r for r in rows if r['消息数'] == 0 and r['朋友圈互动'] > 0]
ghost.sort(key=lambda r: -r['朋友圈互动'])
p(f'  共 {len(ghost)} 人')
for r in ghost:
    show(r['wxid'], f"圈互{r['朋友圈互动']}")

p('')
p('=' * 84)
p('三、★ 4 源节点（74 人）全名单')
p('=' * 84)
four = [r for r in rows if nsig(r) == 4]
four.sort(key=lambda r: -r['消息数'])
for r in four:
    p(f"  {r['名称'][:18]:<20} 消息{r['消息数']:>5} 语音{r['语音数']:>3} 群{r['共同群数']:>3} "
      f"圈互{r['朋友圈互动']:>2} 圈发{r['朋友圈动态']:>3} 最后={r['最后消息']}")

open(os.path.join(WS, '_tmp', 'cross_nodes.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
print(buf.getvalue()[:6000])
