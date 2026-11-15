# -*- coding: utf-8 -*-
"""
全库距离档「预标定 + 分层复核」生成脚本
================================================================
背景（29 人标尺实测结论）：
  · 消息量 / 跨度 / 活跃天数 / 我发占比 / 对价词 / 亲属词 —— 六项特征**全部无法区分「中」与「远」**
  · 距离档是「关系性质判断」（对价 / 血缘 / 婚恋），不在可观测行为里
  · 因此本脚本**不试图自动定档**，只做两件事：
      ① 分类：群聊 / 公众号 / 私聊真人
      ② 分层：把 1,004 个私聊按「他本人留下的线索」排成复核优先级
          线索来源 = 他自己的微信标签（态度词 / 学缘 / 项目）+ 备注
  产出：
     全库距离预标定_2026-10-04.csv      1,004 行，含建议档 + 置信度 + 层级
     距离档复核清单_2026-10-04.csv      需人工念的，按优先级排序
只读索引库与通讯录，不写任何原始数据。
"""
import sqlite3, csv, os, sys, re, collections
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
CONTACTS = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
            r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
            r'\contacts_2026-07-23T20-56-25.csv')
NOW = datetime.now().timestamp()

ZERO_WL = {'蔡峰峰', '刘丽萍', '汪伊俊'}          # 引擎已裁定：父亲 / 母亲 / 研一室友

# 他本人留下的「态度标签」——权重最高
L1_ATT = {'高', '大佬', '无关', '垃圾', '脏', '叛徒', '严肃', '蹭饭', '该死的烂叛徒'}
# 学缘标签
L2_SCH = {'城院', '美术', '实验研一', '初中', '3班', '福州大学', '美术', '实验式',
          'maclay', 'maclay1', '格21', '格22', '格拉', '英国', '格服务'}
# 项目 / 组织标签
L4_PROJ = {'hcare', '国富论', '国富论250', 'kp sicco', '金展', '国药', '星愿',
           '画班', 'card', '代写'}
DEFAULT_TAG = {'全部', 'o', 'ing', '。', '。。。', '。。。。', 'g4人', '2-2'}


def core(s):
    return re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9]', '', s or '')


def split_tags(t):
    return [x.strip() for x in re.split(r'[，,｜|;；]', t or '') if x.strip()]


def load_contacts():
    m = {}
    with open(CONTACTS, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            u = (r.get('用户名') or '').strip()
            if u:
                m[u] = r
    return m


def main():
    ct = load_contacts()
    con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
    cur = con.cursor()

    # ---- 会话级原始数据 ----
    raw = {}
    for t, n, st, mc, f, l in cur.execute(
            'select talker,display_name,session_type,message_count,first_ts,last_ts from sessions'):
        raw[t] = dict(name=n or '', st=st or '', mc=mc or 0, f=f, l=l)

    # ---- 我发条数 / 活跃天数 ----
    me_cnt = collections.Counter()
    days = collections.defaultdict(set)
    for sk, ts, role in cur.execute('select session_key, ts, role from messages'):
        if role == 'me':
            me_cnt[sk] += 1
        if ts:
            days[sk].add(int(ts) // 86400)
    con.close()

    rows = []
    for t, s in raw.items():
        if s['st'] != '私聊':
            continue
        mc = s['mc']
        f, l = s['f'] or 0, s['l'] or 0
        span = round((l - f) / 86400) if f and l else 0
        active = len(days.get(t, ()))
        me_ratio = round(me_cnt.get(t, 0) / mc, 3) if mc else 0
        days_since = round((NOW - l) / 86400) if l else 9999

        c = ct.get(t, {})
        remark = (c.get('备注') or '').strip()
        nick = (c.get('昵称') or '').strip()
        disp = (c.get('显示名称') or '').strip()
        tags_raw = (c.get('标签') or '').strip()
        tags = split_tags(tags_raw)
        real_tags = [x for x in tags if x not in DEFAULT_TAG]
        has_remark = bool(remark) and remark != nick
        in_contacts = bool(c)

        # ---- 分层 ----
        if s['name'] in ZERO_WL or (remark in ZERO_WL):
            layer, clue, pred, conf = 'L0', '同住白名单（引擎已裁定）', '零', '高'
        elif any(x in L1_ATT for x in real_tags):
            layer = 'L1'
            clue = '态度标签：' + '｜'.join(x for x in real_tags if x in L1_ATT)
            pred, conf = '?', '待裁定'
        elif any(x in L2_SCH for x in real_tags):
            layer = 'L2'
            clue = '学缘标签：' + '｜'.join(x for x in real_tags if x in L2_SCH)
            pred, conf = '?', '待裁定'
        elif has_remark:
            layer, clue, pred, conf = 'L3', f'有备注：{remark}', '?', '待裁定'
        elif any(x in L4_PROJ for x in real_tags):
            layer = 'L4'
            clue = '项目标签：' + '｜'.join(x for x in real_tags if x in L4_PROJ)
            pred, conf = '远', '低'
        else:
            layer = 'L5'
            clue = '无标签无备注' if in_contacts else '不在通讯录（公众号/服务号/已删）'
            pred = '远'
            conf = '中' if mc >= 300 else '低'

        # 「近」候选：超高互动（29 人表里「近」=0，是因为那 29 人来自事件库而非互动量）
        near_cand = '★' if (mc >= 1000 and layer != 'L0') else ''

        rows.append(dict(
            talker=t, 名称=s['name'], 备注=remark or nick, 标签=tags_raw,
            消息量=mc, 跨度天=span, 活跃天数=active, 我发占比=me_ratio, 距今天数=days_since,
            层级=layer, 线索=clue, 建议档=pred, 置信度=conf, 近候选=near_cand,
            需人工复核='是' if conf == '待裁定' or near_cand else '',
        ))

    order = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3, 'L4': 4, 'L5': 5}
    rows.sort(key=lambda r: (order[r['层级']], -r['消息量']))

    out1 = os.path.join(WS, '全库距离预标定_2026-10-04.csv')
    with open(out1, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # ---- 复核清单：有线索的 + 高互动 ----
    review = [r for r in rows
              if r['层级'] in ('L0', 'L1', 'L2', 'L3') or r['近候选'] or r['消息量'] >= 100]
    out2 = os.path.join(WS, '距离档复核清单_2026-10-04.csv')
    with open(out2, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(review)

    # ---- 控制台摘要 ----
    print(f'私聊会话 {len(rows)} 个')
    print('分层：', dict(collections.Counter(r["层级"] for r in rows)))
    print('建议档：', dict(collections.Counter(r["建议档"] for r in rows)))
    print('近候选（>=1000 条）：', sum(1 for r in rows if r['近候选']))
    print(f'复核清单：{len(review)} 人')
    print()
    print('=== 近候选（消息量>=1000）===')
    for r in rows:
        if r['近候选']:
            print(f"  {r['消息量']:>6}  {r['名称'][:20]:<22} 距今天 {r['距今天数']:>4}  {r['线索'][:34]}")
    print()
    print('=== L1 态度标签（必念）===')
    for r in rows:
        if r['层级'] == 'L1':
            print(f"  {r['消息量']:>6}  {r['名称'][:20]:<22} {r['线索']}")
    print()
    print('已写：', os.path.basename(out1), '/', os.path.basename(out2))


if __name__ == '__main__':
    main()
