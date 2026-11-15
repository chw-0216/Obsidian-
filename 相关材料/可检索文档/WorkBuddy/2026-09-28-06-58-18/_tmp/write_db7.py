# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime

AN = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
c = sqlite3.connect(AN)
cols = [r[1] for r in c.execute('pragma table_info(events)')]
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
PH = 'P4 暑期与实习（北京台/项目）'

EV = [
 dict(event_id='EVT-20261013-007', date='2026-10-13', date_certainty='确定', phase=PH,
   level='A', score=72, subject='我', category='人际/结构', nature='数据实测',
   event='★★★ 徐嘉良＝朱子涵的「同研究方向搭档」：班群 57413014124（2026-05-09 13:16）研究方向分组名单显示，31 人中「影像叙事与空间表达」仅徐嘉良、朱子涵两人；而本人方向「社会美育与乡村振兴」是全组独苗。→ 「她们坐徐嘉良的车」＝分组结构的产物，非「选择/偏好」信号。★ 本人读法（「她们选了他 → 我被排除」）与结构读法（同方向搭档 + 有车）不同。',
   person='徐嘉良', distance='中', relation='研一同班 · 洞台村项目参与者', match_kind='数据实测',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·72.2/72.3'),

 dict(event_id='EVT-20261013-008', date='2026-10-13', date_certainty='确定', phase=PH,
   level='B', score=54, subject='我', category='人际/关系', nature='本人自述+数据实测',
   event='★ 李佳杨线（本人写作「李佳阳」）：wxid_sdvbmvwjziaq12 · 780 条 · 我发 489（63%）· 2024-12-17 → 2026-05-21。★ 私聊最后两条 2026-05-21 23:07「今天主要喷我。。。」「佳杨拉我一个」→ 此后 4 个月 22 天零消息。→ 本人「不理我」在数据侧成立；但「老式表现对我很烦」是本人解读，数据只能证明「没联系」，不能证明「烦」。',
   person='李佳杨', distance='中', relation='研一同班 · 研究方向「光艺术」', match_kind='数据实测',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·72.4'),

 dict(event_id='EVT-20261013-009', date='2026-10-13', date_certainty='确定', phase=PH,
   level='A', score=66, subject='我', category='金钱/债务', nature='数据实测',
   event='★ 欠舒泽林 ¥300（方向已确认）：2026-10-08 16:52 我「想借 200 明天还能成吗」→ 16:53 舒泽林转账 300（同一笔双行记录）→ 我「明天还」。承诺 10-09 还，截至 10-13 逾期 4 天。★ 与舒泽林完整往来（去重 14 笔）：2026-07-18 500 / 07-29 借500 / 08-04 我还 520（多还 20＝自己加利息，舒「你咋还有利息呢」）/ 08-18 借100 → 08-19 还 / 10-08 借300。模式＝小额·高频·常逾期·自己加利息·舒从不拒绝。',
   person='舒泽林', distance='近', relation='高层人脉圈介绍人 · 兜底型资源', match_kind='数据实测',
   source='F·本人自述事件', review_status='已核实', note='05 三·补·72.5 · CON-064 延伸'),

 dict(event_id='EVT-20261013-010', date='2026-10-13', date_certainty='确定', phase=PH,
   level='A', score=70, subject='我', category='机会/人脉', nature='数据实测',
   event='★★ 错过「央视导演」引荐：2026-10-08 16:51-16:53 舒泽林要给他引荐一位央视导演（「这个是央视一导演」），因他回复太晚（舒「靠，二爷你回复也太晚啦」「来不及啦」「以后回消息及时点哈，这玩意又不逼着你去」）而错过。★ 舒泽林主动给资源、他接不住 —— 与决策中枢「机会线」同型。',
   person='舒泽林', distance='近', relation='高层人脉圈介绍人', match_kind='数据实测',
   source='F·本人自述事件', review_status='已核实', note='05 三·补·72.5'),

 dict(event_id='EVT-20261013-011', date='2026-10-13', date_certainty='确定', phase=PH,
   level='A', score=68, subject='我', category='行为模式', nature='数据实测',
   event='★★★ 跨关系共性「回复不及时」：① 2026-10-07 笑一「你说话做不到」「见不到任何行动的」；② 2026-10-08 舒泽林「你回复也太晚啦」「以后回消息及时点哈」；③ 陈晔 2026-10-08 22:06 的 AIGC 问题至今未回；④ 2026-10-13 本人自述「李佳杨不理我」。→ 同一个人在三个不同关系里被指出同一问题：响应延迟 → 被读成「不重视」→ 关系降温。★ 非人格评价，是可核对的行为模式。',
   person='（跨关系）', distance='—', relation='—', match_kind='数据实测',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·72.6'),

 dict(event_id='EVT-20261013-012', date='2026-10-13', date_certainty='确定', phase=PH,
   level='B', score=48, subject='我', category='状态/健康', nature='数据实测',
   event='★ 抽烟：全库（39.3 万条）搜 role=me +「烟/抽/烟瘾/打火机/利群/中华烟」→ 零条真实抽烟记录（命中全是[烟花]祝福/转述他人/油烟机/作品文件名）。→ 「抽了两根」很可能是压力性单次行为，非长期习惯。⚠️ 不得推断为烟民、不得建议戒烟。附带：2026-10-09 22:14 笑一问「今天心脏那边还抽着疼吗」（仅记录，不推断因果）。',
   person='我', distance='—', relation='—', match_kind='数据实测',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·72.7'),
]

EVD = [
 ('EVT-20261013-007', 'grp_57413014124', '2026-05-09 13:16 研究方向分组名单',
  '班群 57413014124：@徐嘉良 影像叙事与空间表达 @朱子涵 影像叙事与空间表达 @蔡浩文 社会美育与乡村振兴 …（31 人名单）', 0.9),
 ('EVT-20261013-008', 'wxid_sdvbmvwjziaq12', '私聊末条 2026-05-21 23:07',
  '本人：「今天主要喷我。。。」「佳杨拉我一个」', 0.9),
 ('EVT-20261013-009', 'wxid_0ejd54z34nmv32', '2026-10-08 16:52-16:53',
  '本人：「想借 200 明天还能成吗[捂脸]」→ 微信转账 300.00 元 → 本人：「明天还」', 0.95),
 ('EVT-20261013-010', 'wxid_0ejd54z34nmv32', '2026-10-08 16:52-16:53',
  '舒泽林：「靠，二爷你回复也太晚啦」「来不及啦」「这个是央视一导演」「以后回消息及时点哈，这玩意又不逼着你去」', 0.95),
 ('EVT-20261013-011', 'wxid_0ejd54z34nmv32', '2026-10-08 16:53',
  '舒泽林：「以后回消息及时点哈，这玩意又不逼着你去」', 0.85),
 ('EVT-20261013-012', 'FULL_SCAN', '全库扫描',
  'role=me +「烟」全时段：0 条真实抽烟记录', 0.8),
]

for e in EV:
    e['natkey'] = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
    e['created_at'] = now; e['updated_at'] = now; e['extract_version'] = 'v2026-10-13d'
    c.execute('delete from events where event_id=?', (e['event_id'],))
    keys = [k for k in e if k in cols]
    c.execute('insert into events (%s) values (%s)' % (','.join(keys), ','.join('?'*len(keys))),
              [e[k] for k in keys])
    print('event +', e['event_id'], e['level'], e['score'])

for eid, sk, ref, quote, conf in EVD:
    c.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
                 values (?,?,?,?,?,?,?,?,?,?,?)""",
              (None, eid, None, ref, sk, ref, None, quote, 'text_only', conf, '10-13 下午口述'))
print('evidence +', len(EVD))
c.commit()
for t in ('events', 'evidence'):
    print(' ', t, c.execute('select count(*) from ' + t).fetchone()[0])
c.close()
