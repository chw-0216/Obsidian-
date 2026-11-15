# -*- coding: utf-8 -*-
"""
新数据源深挖包 A：谁加他 / 金钱流向 / 红包
==========================================================
数据源：general.db (FMessageTable / transferTable / redEnvelopeTable)
       contact.db (contact / contact_label)
修正：上一轮结论「微信不记录别人加他」= 错。FMessageTable 里有 31 条 is_sender_=0。
"""
import sqlite3, os, io, datetime, collections, csv

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'

SELF = 'wxid_zn4ozsnn8esr21'
MOTHER = 'wxid_1wa75s1kze3o22'      # 刘丽萍
XIAOYI = 'wxid_wdnk6ue9kiyn22'      # 笑一
SHUZELIN = 'wxid_0ejd54z34nmv32'    # 舒泽林


def t2s(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return str(ts)


# ---------- 名字映射：contact.db + 索引库 ----------
name = {}
con = sqlite3.connect(f'file:{os.path.join(DEC, "contact", "contact.db")}?mode=ro', uri=True)
cur = con.cursor()
for u, rm, nk, al in cur.execute('select username, remark, nick_name, alias from contact'):
    name[u] = rm or nk or al or u
con.close()

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
for t, n in con.execute('select talker, display_name from sessions'):
    name.setdefault(t, n or t)
con.close()


def nm(x):
    if x == SELF:
        return '【我】'
    return name.get(x, x)


out = io.StringIO()

# ================= 1. 好友申请 =================
con = sqlite3.connect(f'file:{os.path.join(DEC, "general", "general.db")}?mode=ro', uri=True)
cur = con.cursor()
rows = list(cur.execute('select user_name_, timestamp_, content_, is_sender_, scene_, remark_ '
                        'from FMessageTable order by timestamp_ desc'))

out.write('=' * 84 + '\n')
out.write('一、★ 好友申请 FMessageTable —— 谁加他（共 %d 条）\n' % len(rows))
out.write('=' * 84 + '\n')
SCENE = {1: '微信号搜索', 3: '手机号', 6: '群聊', 10: '名片', 14: '通讯录',
         15: '扫码', 17: '名片/推荐', 30: '手机号/其他', 8: '群聊', 13: '附近的人'}
by_me = [r for r in rows if r[3] == 1]
by_them = [r for r in rows if r[3] == 0]
out.write(f'别人加他（is_sender_=0）：{len(by_them)} 条 ｜ 他发出（is_sender_=1）：{len(by_me)} 条\n\n')
out.write(f'{"时间":<17}{"方向":<8}{"申请人":<20}{"来源":<12}打招呼内容\n')
out.write('-' * 84 + '\n')
for u, ts, c, snd, sc, rk in rows:
    d = '他→对方' if snd == 1 else '对方→他'
    out.write(f'{t2s(ts):<17}{d:<8}{nm(u)[:18]:<20}{SCENE.get(sc, str(sc)):<12}{(c or "")[:40]}\n')

sc_cnt = collections.Counter(r[4] for r in rows)
out.write(f'\n来源分布：{ {SCENE.get(k, k): v for k, v in sc_cnt.most_common()} }\n')

# ================= 2. 转账 =================
tr = list(cur.execute('select transfer_id, session_name, pay_payer, pay_receiver, '
                      'begin_transfer_time, last_update_time from transferTable order by begin_transfer_time desc'))
out.write('\n' + '=' * 84 + '\n')
out.write('二、★ 转账 transferTable（共 %d 条）\n' % len(tr))
out.write('=' * 84 + '\n')
out.write(f'{"时间":<17}{"方向":<12}{"对象":<22}{"场景"}\n')
out.write('-' * 84 + '\n')
inflow = collections.Counter()
outflow = collections.Counter()
for tid, sn, payer, recv, bt, lu in tr:
    if recv == SELF:
        d, other = '收到 ←', payer
        inflow[other] += 1
    elif payer == SELF:
        d, other = '支出 →', recv
        outflow[other] += 1
    else:
        d, other = '他人间', f'{payer}→{recv}'
    scene = '群' if sn.endswith('@chatroom') else '私聊'
    out.write(f'{t2s(bt):<17}{d:<12}{nm(other)[:20]:<22}{scene}\n')

out.write(f'\n★ 他收到（按人，共 {sum(inflow.values())} 笔）：\n')
for k, v in inflow.most_common(15):
    out.write(f'   {v:>3} 笔  {nm(k)}\n')
out.write(f'\n★ 他支出（按人，共 {sum(outflow.values())} 笔）：\n')
for k, v in outflow.most_common(15):
    out.write(f'   {v:>3} 笔  {nm(k)}\n')

# 母亲转账按月分布
mom = [r for r in tr if r[2] == MOTHER or r[3] == MOTHER]
bym = collections.Counter(t2s(r[4])[:7] for r in mom)
out.write(f'\n★ 与母亲（刘丽萍）转账 {len(mom)} 笔，按月：\n')
for k in sorted(bym):
    out.write(f'   {k}  {"█" * bym[k]} {bym[k]}\n')

# ================= 3. 红包 =================
hb = list(cur.execute('select message_server_id, session_name, sender_user_name, '
                      'hb_status, hb_type, receive_status from redEnvelopeTable'))
out.write('\n' + '=' * 84 + '\n')
out.write(f'三、红包 redEnvelopeTable（共 {len(hb)} 条）\n')
out.write('=' * 84 + '\n')
for mid, sn, snd, st, ty, rs in hb:
    who = nm(snd) if snd != SELF else '【我发的】'
    scene = '群' if sn.endswith('@chatroom') else nm(sn)
    out.write(f'   {who[:20]:<22} 场景={scene[:24]:<26} hb_status={st} receive={rs}\n')
con.close()

# ================= 4. 标签定义 =================
con = sqlite3.connect(f'file:{os.path.join(DEC, "contact", "contact.db")}?mode=ro', uri=True)
labs = list(con.execute('select label_name_, label_id_ from contact_label order by sort_order_'))
out.write('\n' + '=' * 84 + '\n')
out.write(f'四、通讯录标签定义（共 {len(labs)} 个）\n')
out.write('=' * 84 + '\n')
out.write('   ' + ' · '.join(l[0] for l in labs) + '\n')
con.close()

open(os.path.join(WS, '_tmp', 'goldmine_A.txt'), 'w', encoding='utf-8').write(out.getvalue())
print('ok', len(out.getvalue()))
print('别人加他', len(by_them), '｜他发出', len(by_me), '｜转账', len(tr), '｜红包', len(hb))
