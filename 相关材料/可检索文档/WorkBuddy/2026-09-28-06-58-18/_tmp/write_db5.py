# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime

AN = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
c = sqlite3.connect(AN)
cols = [r[1] for r in c.execute('pragma table_info(events)')]
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

EV = [
 dict(event_id='EVT-20261013-004', date='2026-10-13', date_certainty='确定',
   phase='P4 暑期与实习（北京台/项目）', level='B', score=52, subject='我',
   category='情感/关系', nature='本人自述',
   event='本人明确表达追求意图：「我想泡李紫yi还有朱子涵」，并陈述新事实「她们都把我朋友圈关了」。｜ ★ 「想泡」＝意图（此前只记「意向」）· ★ 「朋友圈关了」是本人自述，本地库无字段可证（微信「不让他看我的朋友圈」纯服务端设置，不落地本地库）。',
   person='朱子涵、李紫懿', distance='近', relation='研一同学', match_kind='本人自述',
   source='F·本人自述事件', review_status='待核实', note='05 三·补·70.1–70.2'),
 dict(event_id='EVT-20261013-005', date='2026-10-13', date_certainty='确定',
   phase='P4 暑期与实习（北京台/项目）', level='A', score=68, subject='第三方',
   category='情感/关系', nature='分析结论',
   event='朋友圈互动实测（朋友圈全量导出 3,534 帖 + SnsMessage_tmp3）：① 他点赞她们 6 次（李紫懿 5 帖 / 朱子涵 1 帖），她们点赞他 0 次（44 条帖子 likes 无「榕」「001」）→ 完全单向；② 唯一例外＝朱子涵 2026-08-27 23:50 主动点赞他一次；③ 两人发帖极少且 2025-12 后停止（李紫懿 8 帖/末 2025-12-03；朱子涵 3 帖/末 2025-12-23）→ 「关了朋友圈」信息量小于直觉；④ 李紫懿窗口曾在 2025-10~12 打开（6 帖/3 月，他全赞）。',
   person='朱子涵、李紫懿', distance='近', relation='研一同学', match_kind='分析结论',
   source='A·分析库', review_status='待核实', note='05 三·补·70.3'),
]

for e in EV:
    nk = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
    e2 = dict(e); e2['natkey'] = nk; e2['created_at'] = now; e2['updated_at'] = now
    e2['extract_version'] = 'v2026-10-13b'
    c.execute('delete from events where event_id=?', (e['event_id'],))
    keys = [k for k in e2 if k in cols]
    c.execute('insert into events (%s) values (%s)' % (','.join(keys), ','.join('?' * len(keys))),
              [e2[k] for k in keys])
    print('event +', e['event_id'])

EVD = [
 ('EVT-20261013-004', 'user_report', None, '本人自述（2026-10-13 20:48）', 'text_only', 0.5,
  '本人：「我想泡李紫yi还有朱子涵，但是她们都把我朋友圈关了怎么办」'),
 ('EVT-20261013-005', 'raw_record', None, '朋友圈全量导出_2026-07-23T20-36-32.json（3,534 帖）', 'rebuilt', 0.95,
  '他 44 条帖子 likes 中「榕」0 次 /「001」0 次；他点赞李紫懿 5 帖（2025-10-10/10-26/11-15/11-22/12-03）· 朱子涵 1 帖（2025-09-20）'),
 ('EVT-20261013-005', 'raw_record', 'wxid_utdeb3kw2z5j22', 'sns.db · SnsMessage_tmp3', 'rebuilt', 0.95,
  '朱子涵 2026-08-27 23:50:15 点赞他（from=wxid_utdeb3kw2z5j22 → to=本人 · type=1 · comment_id=1027 · feed_id=-3449326860963794147）'),
 ('EVT-20261013-005', 'raw_record', None, 'sns.db · contact.extra_buffer', 'rebuilt', 0.9,
  '李紫懿/朱子涵/周雯娟 三人 extra_buffer 权限字段完全相同（field10=4294967295）→ 本地库零区分度，无法判定「谁屏蔽了我」'),
]
for eid, kind, sk, ref, ls, conf, quote in EVD:
    c.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
                 values (?,?,?,?,?,?,?,?,?,?,?)""",
              (None, eid, None, ref, sk, ref, None, quote, ls, conf, '10-13 朋友圈实测'))
print('evidence +', len(EVD))
c.commit()
for t in ('events', 'evidence', 'persons'):
    print('  %-10s %d' % (t, c.execute('select count(*) from ' + t).fetchone()[0]))
c.close()
