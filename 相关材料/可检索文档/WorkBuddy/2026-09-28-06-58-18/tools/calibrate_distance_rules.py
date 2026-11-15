# -*- coding: utf-8 -*-
"""
距离档「标尺」校准脚本
------------------------------------------------
思路：
  1) 从 index.sqlite 取全部私聊会话的**可量化特征**（消息量/跨度/活跃天数/我发占比/近期性）
  2) 从通讯录 CSV 取**备注**（备注 != 昵称 才算设过备注）
  3) 用已知的 29 人样本做**锚点**，校准「特征 -> 距离档」规则
  4) 规则在 29 人上跑出混淆矩阵，反复调阈值，再应用到全库 927 人

输出：
  _tmp/dist_features_29.csv   29 人特征 + 已知档位 + 规则预测
  _tmp/dist_features_all.csv  全库私聊特征 + 规则预测 + 置信度
只读索引库，不写任何原始数据。
"""
import sqlite3, csv, os, sys, re, json, collections
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
CONTACTS = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
            r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
            r'\contacts_2026-07-23T20-56-25.csv')
SAMPLE29 = os.path.join(WS, '补标_29人距离表.csv')
TMP = os.path.join(WS, '_tmp')
os.makedirs(TMP, exist_ok=True)

NOW = datetime.now().timestamp()

# ---------- 1. 通讯录：talker -> (备注, 昵称, 是否设过备注) ----------
def load_contacts():
    m = {}
    if not os.path.exists(CONTACTS):
        print('!! 通讯录不存在:', CONTACTS); return m
    with open(CONTACTS, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            u = (r.get('用户名') or '').strip()
            if not u:
                continue
            remark = (r.get('备注') or '').strip()
            nick = (r.get('昵称') or '').strip()
            disp = (r.get('显示名称') or '').strip()
            # 坑：有备注时 显示名称 == 备注；真昵称在 昵称 列
            has_remark = bool(remark) and remark != nick and remark != disp or (bool(remark) and not nick)
            m[u] = dict(remark=remark, nick=nick, disp=disp, has_remark=has_remark,
                        tags=(r.get('标签') or '').strip(),
                        region=(r.get('地区') or '').strip())
    return m

# ---------- 2. index.sqlite：会话级特征 ----------
def load_sessions():
    con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
    cur = con.cursor()
    sess = {}
    for talker, name, stype, mc, f, l in cur.execute(
            'select talker, display_name, session_type, message_count, first_ts, last_ts from sessions'):
        sess[talker] = dict(name=name or '', stype=stype or '', mc=mc or 0, f=f, l=l)
    # 逐会话：我发条数 + 活跃天数（distinct date）
    me_cnt = collections.Counter()
    days = collections.defaultdict(set)
    for sk, ts, role in cur.execute('select session_key, ts, role from messages'):
        if role == 'me':
            me_cnt[sk] += 1
        if ts:
            days[sk].add(int(ts) // 86400)   # 天粒度
    con.close()
    for sk, s in sess.items():
        s['me'] = me_cnt.get(sk, 0)
        s['active_days'] = len(days.get(sk, ()))
    return sess

# ---------- 3. 特征计算 ----------
def featurize(sk, s, ct):
    mc = s['mc'] or 0
    f, l = s['f'] or 0, s['l'] or 0
    span = max(0, (l - f)) / 86400 if f and l else 0
    active = s['active_days'] or 0
    me = s['me'] or 0
    me_ratio = (me / mc) if mc else 0
    intensity = (mc / active) if active else 0
    days_since = ((NOW - l) / 86400) if l else 99999
    c = ct.get(sk, {})
    return dict(
        talker=sk, name=s['name'], stype=s['stype'],
        mc=mc, span_days=round(span, 1), active_days=active,
        me_ratio=round(me_ratio, 3), intensity=round(intensity, 2),
        days_since_last=round(days_since, 1),
        has_remark=int(bool(c.get('has_remark'))),
        remark=c.get('remark', ''), nick=c.get('nick', ''),
        tags=c.get('tags', ''), region=c.get('region', ''),
    )

# ---------- 4. 规则（第一版 · 待校准） ----------
ZERO_WHITELIST = {'蔡峰峰', '刘丽萍', '汪伊俊'}   # 父母 + 研一室友（引擎已裁定）

def predict(feat):
    """返回 (档位, 命中规则, 置信度)"""
    name, mc = feat['name'], feat['mc']
    span, active = feat['span_days'], feat['active_days']
    me_ratio, intensity = feat['me_ratio'], feat['intensity']
    hr, remark, tags = feat['has_remark'], feat['remark'], feat['tags']
    days_since = feat['days_since_last']
    blob = f'{name} {remark} {tags}'

    # 零：同住白名单
    if name in ZERO_WHITELIST or any(z in blob for z in ZERO_WHITELIST):
        return '零', '同住白名单', '高'

    # 明确「远」的信号：服务/交易/事故/求职/物业/外包/销售/客服
    FAR_KW = ['服务', '外包', '物业', '销售', '事故', '赔偿', '租车', '家政',
              '搬家', '招聘', 'HR', '求职', '客服', '老师', '教练', '房东',
              '中介', '保险', '银行', '快递', '外卖', '代购']
    if any(k in blob for k in FAR_KW):
        return '远', '服务/交易类关键词', '中'

    # 近：极少量 —— 高消息量 + 长跨度 + 高我发占比 + 有备注
    if mc >= 2000 and span >= 300 and me_ratio >= 0.35:
        return '近', '超高频+长跨度+我主导', '中'

    # 中：有备注 + 中高消息量 + 长跨度
    if hr and mc >= 100 and span >= 180:
        return '中', '有备注+中量+长跨度', '中'
    if hr and mc >= 50 and active >= 30:
        return '中', '有备注+中量+多活跃日', '低'

    # 亲属/同学/校友/前辈/朋友 标签
    MID_KW = ['亲戚', '亲属', '表', '堂', '舅', '姨', '叔', '姑', '爷', '奶',
              '校友', '同学', '同门', '学长', '学姐', '前辈', '朋友', '世交']
    if any(k in blob for k in MID_KW):
        return '中', '关系标签类关键词', '低'

    # 其余真人私聊 -> 远
    return '远', '默认(其余真人私聊)', '低'

# ---------- 5. 主流程 ----------
def main():
    ct = load_contacts()
    sess = load_sessions()
    print(f'通讯录 {len(ct)} 人 ｜ 索引会话 {len(sess)} 个')

    # 29 人样本
    rows29 = list(csv.DictReader(open(SAMPLE29, encoding='utf-8-sig')))
    # name -> session（用 display_name 精确/包含匹配）
    by_name = {}
    for sk, s in sess.items():
        if s['stype'] == '私聊':
            by_name.setdefault(s['name'], sk)

    out29 = []
    hit = 0
    for r in rows29:
        nm = r['对话人'].strip()
        key = by_name.get(nm)
        if key is None:  # 模糊匹配
            for n2, k2 in by_name.items():
                if n2 and (nm in n2 or n2 in nm):
                    key = k2; break
        if key is None:
            out29.append(dict(对话人=nm, 已知档=r['距离半径(填:零/近/中/远)'], talker='', name='(未匹配)',
                              预测档='?', 命中规则='会话未匹配', 置信度='-', mc=0, span_days=0,
                              active_days=0, me_ratio=0, has_remark=0, remark=''))
            continue
        s = sess[key]
        feat = featurize(key, s, ct)
        p, rule, conf = predict(feat)
        known = r['距离半径(填:零/近/中/远)'].strip()
        if p == known:
            hit += 1
        out29.append(dict(对话人=nm, 已知档=known, **feat, 预测档=p, 命中规则=rule, 置信度=conf))

    print(f'\n=== 29 人校准：命中 {hit}/{len(rows29)} ===')
    cm = collections.Counter()
    for o in out29:
        cm[(o['已知档'], o['预测档'])] += 1
        flag = 'OK ' if o['已知档'] == o['预测档'] else 'XX '
        print(f"{flag}{o['对话人'][:14]:<16} 已知={o['已知档']:<2} 预测={o['预测档']:<2} "
              f"规则={o['命中规则']:<20} mc={o['mc']:<6} 跨度={o['span_days']:<7} 活跃={o['active_days']:<4} 我占比={o['me_ratio']}")
    print('\n混淆矩阵 (已知,预测):', dict(cm))

    # 全库
    allrows = []
    for sk, s in sess.items():
        if s['stype'] != '私聊':
            continue
        feat = featurize(sk, s, ct)
        p, rule, conf = predict(feat)
        allrows.append(dict(预测档=p, 命中规则=rule, 置信度=conf, **feat))
    allrows.sort(key=lambda x: (-{'零': 0, '近': 1, '中': 2, '远': 3}.get(x['预测档'], 9), -x['mc']))

    with open(os.path.join(TMP, 'dist_features_29.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out29[0].keys())); w.writeheader(); w.writerows(out29)
    with open(os.path.join(TMP, 'dist_features_all.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(allrows[0].keys())); w.writeheader(); w.writerows(allrows)

    print(f'\n全库私聊 {len(allrows)} 个 -> 分布：',
          dict(collections.Counter(x['预测档'] for x in allrows)))
    print('置信度：', dict(collections.Counter(x['置信度'] for x in allrows)))
    print('\n已写：_tmp/dist_features_29.csv / _tmp/dist_features_all.csv')

if __name__ == '__main__':
    main()
