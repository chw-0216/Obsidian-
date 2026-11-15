# -*- coding: utf-8 -*-
"""★★ 交叉主表：把 8 个数据源对齐到「一人一行」
   index.sqlite(消息) + contact(身份/备注) + chatroom_member(共同群) + contact_label(标签)
   + FMessageTable(谁加他) + transferTable(转账) + VoiceInfo(语音)
   + SnsMessage(朋友圈互动) + SnsTopItem(朋友圈动态)
产出：
  - 交叉主表_2026-10-04.csv
  - _tmp/cross_master.txt （重叠分析）
"""
import sqlite3, os, io, csv, datetime, collections

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
SELF = 'wxid_zn4ozsnn8esr21'

def ro(p, tf=False):
    con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
    if tf:
        con.text_factory = lambda b: b.decode('utf-8', 'ignore')
    return con

def d(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
    except Exception:
        return ''

# ---------- 1) 会话统计 ----------
con = ro(IDX)
stats = {}
for sk, n, mn, mx, me, days in con.execute("""
        select session_key, count(*), min(ts), max(ts),
               sum(case when role='me' then 1 else 0 end),
               count(distinct date(ts,'unixepoch','+8 hours'))
        from messages group by session_key"""):
    stats[sk] = dict(n=n, mn=mn, mx=mx, me=me, days=days)
sess_name = {}
for t, n in con.execute('select talker, display_name from sessions'):
    sess_name[t] = n
con.close()

# ---------- 2) contact ----------
cc = ro(os.path.join(DEC, 'contact', 'contact.db'))
c1 = cc.cursor()
info = {}
id2u = {}
for i, u, lt, al, rm, nk in c1.execute('select id, username, local_type, alias, remark, nick_name from contact'):
    info[u] = dict(id=i, lt=lt, alias=al, remark=rm, nick=nk)
    id2u[i] = u

# ---------- 3) 共同群数 ----------
gcnt = collections.Counter()
for rid, mid in c1.execute('select room_id, member_id from chatroom_member'):
    gcnt[mid] += 1

# ---------- 4) 标签映射 ----------
tabs = [r[0] for r in c1.execute("select name from sqlite_master where type='table'")]
lab_tabs = [t for t in tabs if 'label' in t.lower()]
labels = collections.defaultdict(list)
lab_cols = {}
for t in lab_tabs:
    cols = [x[1] for x in c1.execute(f'pragma table_info({t})')]
    lab_cols[t] = cols
# 尝试常见映射表
labname = {}
try:
    for n, i in c1.execute('select label_name_, label_id_ from contact_label'):
        labname[i] = n
except Exception:
    pass
for t in lab_tabs:
    cols = lab_cols[t]
    if 'label_id_' in cols and any(c in cols for c in ('contact_id_', 'username_', 'user_name_', 'id_')):
        idc = [c for c in cols if c in ('contact_id_', 'username_', 'user_name_', 'id_')][0]
        try:
            for cid, lid in c1.execute(f'select {idc}, label_id_ from {t}'):
                u = id2u.get(cid, cid if isinstance(cid, str) else None)
                if u:
                    labels[u].append(labname.get(lid, str(lid)))
        except Exception as e:
            pass

# ---------- 5) 好友申请 / 转账 ----------
gg = ro(os.path.join(DEC, 'general', 'general.db'))
g1 = gg.cursor()
apply_by = collections.defaultdict(list)
try:
    for u, ts, c, snd, sc in g1.execute('select user_name_, timestamp_, content_, is_sender_, scene_ from FMessageTable'):
        if snd == 0:
            apply_by[u].append(f'{d(ts)}:{sc}')
except Exception as e:
    pass
tin = collections.Counter(); tout = collections.Counter()
try:
    for sn, payer, recv, bt in g1.execute('select session_name, pay_payer, pay_receiver, begin_transfer_time from transferTable'):
        if recv == SELF:
            tin[payer] += 1
        elif payer == SELF:
            tout[recv] += 1
except Exception as e:
    pass
gg.close()

# ---------- 6) 语音 ----------
vcount = collections.Counter()
try:
    vm = ro(os.path.join(DEC, 'message', 'media_0.db'))
    vc = vm.cursor()
    n2id = {}
    for t in [r[0] for r in vc.execute("select name from sqlite_master where type='table'")]:
        cols = [x[1] for x in vc.execute(f'pragma table_info({t})')]
        if 'user_name' in cols and 'rowid' in [c.lower() for c in cols] + ['rowid']:
            pass
    try:
        n2id = {i: u for i, u in vc.execute('select rowid, user_name from Name2Id')}
    except Exception:
        pass
    for cn, in vc.execute('select chat_name_id from VoiceInfo'):
        u = n2id.get(cn, str(cn))
        vcount[u] += 1
    vm.close()
except Exception as e:
    pass

# ---------- 7) 朋友圈 ----------
sns_int = collections.Counter(); sns_post = collections.Counter()
try:
    sm = ro(os.path.join(DEC, 'sns', 'sns.db'), tf=True)
    sc = sm.cursor()
    for fu, in sc.execute('select from_username from SnsMessage_tmp3'):
        if fu:
            sns_int[fu] += 1
    for u, in sc.execute('select username from SnsTopItem_1'):
        if u:
            sns_post[u] += 1
    sm.close()
except Exception as e:
    pass

# ---------- 8) 预标定档 ----------
pre = {}
pcsv = os.path.join(WS, '全库距离预标定_2026-10-04.csv')
if os.path.exists(pcsv):
    with open(pcsv, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            k = r.get('wxid') or r.get('talker') or r.get('会话') or ''
            pre[k] = r

# ---------- 合并 ----------
rows = []
keys = set(stats) | set(info)
for k in keys:
    if k == SELF:
        continue
    st = stats.get(k)
    inf = info.get(k, {})
    nm = inf.get('remark') or inf.get('nick') or sess_name.get(k) or inf.get('alias') or k
    rows.append(dict(
        wxid=k, 名称=nm, 备注=inf.get('remark', ''), 类型=inf.get('lt', ''),
        消息数=st['n'] if st else 0,
        活跃天=st['days'] if st else 0,
        跨度天=((st['mx'] - st['mn']) // 86400) if st and st['mn'] and st['mx'] else 0,
        我发占比=round(st['me'] / st['n'], 3) if st and st['n'] else 0,
        最后消息=d(st['mx']) if st else '',
        语音数=vcount.get(k, 0),
        共同群数=gcnt.get(inf.get('id'), 0),
        朋友圈互动=sns_int.get(k, 0),
        朋友圈动态=sns_post.get(k, 0),
        加我=len(apply_by.get(k, [])),
        转入=tin.get(k, 0),
        转出=tout.get(k, 0),
        标签='|'.join(labels.get(k, [])),
        预标档=pre.get(k, {}).get('预测档', '') if pre else '',
    ))

rows.sort(key=lambda r: -r['消息数'])
cols = list(rows[0].keys()) if rows else []
with open(os.path.join(WS, '交叉主表_2026-10-04.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# ---------- 重叠分析 ----------
buf = io.StringIO()
def p(*a):
    buf.write(' '.join(str(x) for x in a) + '\n')

p('=' * 84)
p('★ 交叉主表：%d 行 × %d 列' % (len(rows), len(cols)))
p('=' * 84)
p('label 相关表：', lab_tabs)
for t in lab_tabs:
    p('   ', t, lab_cols[t])
p('')
p('★ 各源覆盖人数：')
p('   有消息记录会话 :', sum(1 for r in rows if r['消息数'] > 0))
p('   有语音         :', sum(1 for r in rows if r['语音数'] > 0))
p('   有共同群       :', sum(1 for r in rows if r['共同群数'] > 0))
p('   有朋友圈互动   :', sum(1 for r in rows if r['朋友圈互动'] > 0))
p('   有朋友圈动态   :', sum(1 for r in rows if r['朋友圈动态'] > 0))
p('   加过我         :', sum(1 for r in rows if r['加我'] > 0))
p('   有转账         :', sum(1 for r in rows if r['转入'] + r['转出'] > 0))
p('   有标签         :', sum(1 for r in rows if r['标签']))

# 信号数分布
def nsig(r):
    return sum([r['消息数'] > 0, r['语音数'] > 0, r['共同群数'] > 0,
                r['朋友圈互动'] > 0, r['朋友圈动态'] > 0, r['加我'] > 0,
                r['转入'] + r['转出'] > 0, bool(r['标签'])])
dist = collections.Counter(nsig(r) for r in rows)
p('')
p('★ 同时命中 k 个源的分布：')
for k in sorted(dist, reverse=True):
    p(f'   {k} 源：{dist[k]:5d} 人')

p('')
p('★ ★★ 命中 ≥5 源的人（全维节点）：')
for r in sorted(rows, key=lambda x: -nsig(x)):
    if nsig(r) >= 5:
        p(f"   [{nsig(r)}源] {r['名称'][:16]:<18} 消息{r['消息数']:>5} 语音{r['语音数']:>3} 群{r['共同群数']:>3} "
          f"圈互{r['朋友圈互动']:>2} 圈发{r['朋友圈动态']:>3} 加我{r['加我']} 转{r['转入']}/{r['转出']} 标={r['标签'][:20]}")

open(os.path.join(WS, '_tmp', 'cross_master.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('ok rows=%d' % len(rows))
print(buf.getvalue()[:3000])
