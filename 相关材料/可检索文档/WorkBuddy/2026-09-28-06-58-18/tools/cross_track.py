# -*- coding: utf-8 -*-
"""多轮交叉：赛道 × 全维节点 × 预标档 × 桥 × 朋友圈维度独立性
"""
import sqlite3, os, io, csv, collections

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
SELF_ID = 3641
buf = io.StringIO()
def p(*a):
    buf.write(' '.join(str(x) for x in a) + '\n')

# ---- 读交叉主表 ----
rows = list(csv.DictReader(open(os.path.join(WS, '交叉主表_2026-10-04.csv'), encoding='utf-8-sig')))
for r in rows:
    for k in ('消息数', '语音数', '共同群数', '朋友圈互动', '朋友圈动态', '加我', '转入', '转出', '活跃天'):
        r[k] = int(r[k] or 0)
print('主表', len(rows))

# ---- 预标档 ----
pre = {}
pc = os.path.join(WS, '全库距离预标定_2026-10-04.csv')
if os.path.exists(pc):
    for r in csv.DictReader(open(pc, encoding='utf-8-sig')):
        pre[r.get('talker', '')] = r
    print('预标定', len(pre), '列=', list(list(pre.values())[0].keys()))

# ---- 群名 ----
con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
gname = {}
for t, n, st in con.execute('select talker, display_name, session_type from sessions'):
    gname[t] = n or t
con.close()

# ---- 共同群 ----
cc = sqlite3.connect(f'file:{os.path.join(DEC,"contact","contact.db")}?mode=ro', uri=True)
c1 = cc.cursor()
his_rooms = {r[0] for r in c1.execute('select room_id from chatroom_member where member_id=?', (SELF_ID,))}
rid2u = {i: u for i, u in c1.execute('select id, username from chat_room')}
uid2id = {u: i for i, u in c1.execute('select id, username from contact')}
person_rooms = collections.defaultdict(set)
for rid, mid in c1.execute('select room_id, member_id from chatroom_member'):
    if rid in his_rooms:
        person_rooms[mid].add(rid)
cc.close()
p('他的群 %d ｜ 群成员记录覆盖 %d 人' % (len(his_rooms), len(person_rooms)))

TRACK = [
    ('① 家教·现金流', ['家教', '老师群', '辅导', '一对一家教']),
    ('② 考研→考编', ['考研', '事业编', '备考', '考公', '国省考', '初试复试']),
    ('③ 格拉斯哥校友', ['格拉斯哥', '格拉', 'UoG', '英区', '英国', '留学', '校友会']),
    ('④ 央美研一·学业', ['花家地', '央美', '艺专', '25级', '实验艺术', '美院', '下乡']),
    ('⑤ 社会美育', ['美育', '洞台', '科技美学', '美乡', '乡村', '长城']),
    ('⑥ 入党·组织', ['积极分子', '共青团', '党支部', '党委', '党课']),
    ('兴趣·社交', ['推理', '天文', '引力圈', '桌游', '狼人', '剧本']),
    ('商业·店', ['牛排', '披萨', '咖啡', '餐', '烘焙']),
    ('家庭', ['一家亲', '家族', '亲戚']),
]

def track_of(roomnames):
    hit = set()
    for rn in roomnames:
        for name, kws in TRACK:
            if any(k in rn for k in kws):
                hit.add(name)
    return hit

# ---- 赛道统计 ----
track_stat = collections.defaultdict(lambda: dict(people=0, msgs=0, nodes=[], groups=set()))
name2row = {r['wxid']: r for r in rows}
person_track = {}
for u, inf in [(r['wxid'], r) for r in rows]:
    pid = uid2id.get(u)
    if pid is None or pid not in person_rooms:
        continue
    rns = [gname.get(rid2u.get(rid, ''), '') for rid in person_rooms[pid]]
    ts = track_of(rns)
    person_track[u] = ts
    for t in ts:
        st = track_stat[t]
        st['people'] += 1
        st['msgs'] += inf['消息数']
        st['groups'] |= {rn for rn in rns if any(k in rn for _, kws in TRACK for k in kws)}

def nsig(r):
    return sum([r['消息数'] > 0, r['语音数'] > 0, r['共同群数'] > 0,
                r['朋友圈互动'] > 0, r['朋友圈动态'] > 0, r['加我'] > 0,
                r['转入'] + r['转出'] > 0])

p('')
p('=' * 84)
p('一、★ 九条赛道：人数 / 消息量 / 群数 / 全维节点(≥4源)')
p('=' * 84)
for name, _ in TRACK:
    st = track_stat.get(name)
    if not st:
        continue
    nodes = [r for r in rows if name in person_track.get(r['wxid'], ()) and nsig(r) >= 4]
    nodes.sort(key=lambda r: -nsig(r))
    real = [r for r in rows if name in person_track.get(r['wxid'], ()) and r['消息数'] > 0]
    rmsg = sum(r['消息数'] for r in real)
    p(f"  {name:<16} {st['people']:>5} 人 ｜ 真人私聊 {len(real):>4} ｜ {rmsg:>7} 条 ｜ {len(st['groups']):>4} 群 ｜ 全维节点 {len(nodes)}")
    for r in nodes[:8]:
        p(f"        [{nsig(r)}源] {r['名称'][:14]:<16} 消息{r['消息数']:>5} 圈互{r['朋友圈互动']:>2} 圈发{r['朋友圈动态']:>3} 语音{r['语音数']:>3}")

# ---- 预标档 × 信号数 ----
p('')
p('=' * 84)
p('二、★ 预标档 × 信号数（验证「档位能否从行为推出」）')
p('=' * 84)
cross = collections.defaultdict(collections.Counter)
for r in rows:
    k = pre.get(r['wxid'], {}).get('建议档', '')
    if k:
        cross[k][nsig(r)] += 1
for k in sorted(cross):
    tot = sum(cross[k].values())
    p(f"  预标 {k}：{tot:>4} 人 ｜ 信号数分布 {dict(sorted(cross[k].items()))}")

p('')
p('★ 6/5 源节点的预标档：')
for r in sorted(rows, key=lambda x: -nsig(x))[:20]:
    p(f"  [{nsig(r)}源] {r['名称'][:16]:<18} 预标={pre.get(r['wxid'],{}).get('建议档','?'):<3} 消息{r['消息数']:>6}")

# ---- 朋友圈维度 vs 消息维度 ----
p('')
p('=' * 84)
p('三、★★ 朋友圈维度 与 消息维度 是否独立')
p('=' * 84)
top_int = sorted([r for r in rows if r['朋友圈互动'] > 0], key=lambda r: -r['朋友圈互动'])[:20]
p('  朋友圈互动 TOP20（对比其消息量）：')
for r in top_int:
    p(f"    圈互{r['朋友圈互动']:>2}  消息{r['消息数']:>6}  圈发{r['朋友圈动态']:>3}  {r['名称'][:18]}")
top_post = sorted([r for r in rows if r['朋友圈动态'] > 0], key=lambda r: -r['朋友圈动态'])[:20]
p('')
p('  朋友圈动态量 TOP20：')
for r in top_post:
    p(f"    圈发{r['朋友圈动态']:>3}  圈互{r['朋友圈互动']:>2}  消息{r['消息数']:>6}  {r['名称'][:18]}")

# ---- 桥 × 节点 ----
p('')
p('=' * 84)
p('四、★ 桥（共同群≥12）中哪些也是全维节点')
p('=' * 84)
bridges = sorted([r for r in rows if r['共同群数'] >= 12], key=lambda r: -r['共同群数'])
p(f'  共同群≥12 的共 {len(bridges)} 人')
for r in bridges[:30]:
    p(f"    群{r['共同群数']:>3} [{nsig(r)}源] 消息{r['消息数']:>5} 圈互{r['朋友圈互动']:>2}  {r['名称'][:18]}")

open(os.path.join(WS, '_tmp', 'cross_track.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('ok', len(buf.getvalue()))
print(buf.getvalue()[:5000])
