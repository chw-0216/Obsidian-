# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime

AN = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
c = sqlite3.connect(AN)
c.execute('pragma foreign_keys=off')

cols = [r[1] for r in c.execute('pragma table_info(events)')]
print('events cols:', cols)
print('sample row:', c.execute('select * from events order by date desc limit 1').fetchone())

EV = [
 dict(event_id='EVT-20261013-001', date='2026-10-13', date_certainty='确定',
   phase='P4 暑期与实习（北京台/项目）', level='B', score=55, subject='我',
   category='学业/事务', nature='已发生',
   event='研二综合测评汇报（中期汇报）于 10-13 13:00 完成；本人自评「估计给我的分还成」。｜ ★ 自评为本人估分，非官方结果（该测评涉及评奖学金）· 汇报内容已删减（见 EVT-20261013-002）。',
   person='—', distance='零', relation='—', match_kind='本人自述',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·69.2'),
 dict(event_id='EVT-20261013-002', date='2026-10-13', date_certainty='确定',
   phase='P4 暑期与实习（北京台/项目）', level='A', score=72, subject='我',
   category='身份/关系机制', nature='本人自述',
   event='中期汇报为求稳妥，导师要求删减材料 —— 「所有领导接待、北京台实习都删了」。｜ ★ 属「汇报口径收缩」（分圈版本管理的减法侧）：删的是呈现，不是事实。被删两类对应素材包 04（第五届美学与艺术研究学术研讨会会务·专家接待志愿者）与 07（北京广播电视台AIGC科研实习）。',
   person='—', distance='零', relation='—', match_kind='本人自述',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·69.3'),
 dict(event_id='EVT-20261013-003', date='2026-10-13', date_certainty='确定',
   phase='P4 暑期与实习（北京台/项目）', level='B', score=48, subject='我',
   category='情感/关系', nature='本人自述',
   event='本人主动提名两位婚恋意向对象：朱子涵（「北京出生感觉还挺有钱的，可以考虑交往，感觉有可能」）与李紫懿（「也有可能」）。｜ ★ 均为本人主观评估（「感觉」「有可能」），非关系事实。',
   person='朱子涵、李紫懿', distance='近', relation='研一同学', match_kind='本人自述',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·69.4–69.6'),
]

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
for e in EV:
    nk = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
    e2 = dict(e)
    e2['natkey'] = nk
    e2['created_at'] = now
    e2['updated_at'] = now
    e2['extract_version'] = 'v2026-10-13'
    c.execute('delete from events where event_id=?', (e['event_id'],))
    keys = [k for k in e2 if k in cols]
    c.execute('insert into events (%s) values (%s)' % (','.join(keys), ','.join('?' * len(keys))),
              [e2[k] for k in keys])
    print('event +', e['event_id'])

EVD = [
 ('EVT-20261013-001', 'user_report', None, '本人自述（2026-10-13 20:14）', 'text_only', 0.5,
  '本人：「今天中期汇报估计给我的分还成」——估分，非官方结果'),
 ('EVT-20261013-002', 'user_report', None, '本人自述（2026-10-13 20:14）', 'text_only', 0.5,
  '本人：「我中期汇报为了稳妥我老师让我删去很多东西，所有领导接待北京台实习都删了」'),
 ('EVT-20261013-002', 'raw_record', None, 'wxid_u240wu17qzc222 / 47952610494@chatroom · 2025-09-30', 'rebuilt', 0.9,
  '「你去接待深圳的李心锋老师可以吗」/「刚刚陈晔老师说你还有别的工作，让你不接待了」→ 「领导接待」＝研讨会专家接待志愿者'),
 ('EVT-20261013-003', 'user_report', None, '本人自述（2026-10-13 20:14）', 'text_only', 0.5,
  '本人：「朱子涵出生在北京感觉还挺有钱的，可以考虑交往，感觉有可能，李紫yi也有可能」'),
 ('EVT-20261013-003', 'raw_record', 'wxid_f77sxlrwo0tr12', 'index.sqlite · 李紫懿 1,146 条', 'rebuilt', 0.9,
  '李紫懿：研一同班 · 1,146 条（我发 771）· 2025-09-09 → 2026-10-08 · 她叫他「班长」· 他叫她「李姐」'),
 ('EVT-20261013-003', 'raw_record', 'wxid_utdeb3kw2z5j22', 'index.sqlite · 朱子涵 45 条', 'rebuilt', 0.9,
  '朱子涵：研一同学 · 45 条（我发 36）· 2025-11-20 → 2026-03-17 · 班级事务联络人（统计/收作业/要票）'),
]
for eid, kind, sk, ref, ls, conf, quote in EVD:
    c.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
                 values (?,?,?,?,?,?,?,?,?,?,?)""",
              (None, eid, None, ref, sk, ref, None, quote, ls, conf, '10-13 本轮'))
print('evidence +', len(EVD))

# persons 更新
c.execute("update persons set relation=?, note=? where person_id=?",
          ('研一同学 · 班级事务联络人',
           '昵称 001 · 微信号 Johanne_001 · 45 条（我发 36）· 2025-11-20 → 2026-03-17 · ★ 本人 2026-10-13 提名为婚恋意向（「北京出生/感觉有钱/可考虑交往」）· ⚠️ 性别库内未确证 → 05 三·补·69.5',
           'wxid_utdeb3kw2z5j22'))
c.execute("update persons set note=? where person_id=?",
          ('昵称 榕 · 微信号 Annyehuo3456 · ★ 研一同班班委（同学叫他「班长」）· 1,146 条（我发 771）· 2025-09-09 → 2026-10-08 · 2025-09 爆发 438 → 2026-02 断崖 · ★ 本人 2026-10-13 提名为婚恋意向 → 05 三·补·69.6',
           'wxid_f77sxlrwo0tr12'))
c.commit()
for t in ('events', 'evidence', 'persons', 'aliases'):
    print('  %-10s %d' % (t, c.execute('select count(*) from ' + t).fetchone()[0]))
c.close()
