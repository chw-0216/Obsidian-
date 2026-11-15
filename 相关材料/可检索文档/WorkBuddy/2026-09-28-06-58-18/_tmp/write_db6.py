# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime

AN = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
c = sqlite3.connect(AN)
cols = [r[1] for r in c.execute('pragma table_info(events)')]
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

e = dict(event_id='EVT-20261013-006', date='2026-10-13', date_certainty='确定',
  phase='P4 暑期与实习（北京台/项目）', level='B', score=50, subject='我',
  category='情感/关系', nature='本人自述',
  event='本人状态切换：①「再说吧」→ 李紫懿/朱子涵线暂搁（≠放弃）；②「我最近没事了」→ 与 10-13 中期汇报结束吻合；③ 计划找笑一（原话「可以找笑一释放性欲了关心一下她」）。｜ ★ 「释放性欲」表述与 `04` Q15（2026-10-04「名分是女友、实质是资源约束」）完全同型 → 印证既有裁定。★ ⚠️ 「关心一下」若停在口头＝10-07 笑一核心不满（「你说话做不到」「见不到任何行动的」）的原样重演。',
  person='笑一', distance='近', relation='现任女友（Q15 口径）', match_kind='本人自述',
  source='F·本人自述事件', review_status='待核实', note='05 三·补·71')

nk = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
e['natkey'] = nk; e['created_at'] = now; e['updated_at'] = now
e['extract_version'] = 'v2026-10-13c'
c.execute('delete from events where event_id=?', (e['event_id'],))
keys = [k for k in e if k in cols]
c.execute('insert into events (%s) values (%s)' % (','.join(keys), ','.join('?'*len(keys))),
          [e[k] for k in keys])
print('event +', e['event_id'])

EVD = [
 ('EVT-20261013-006', 'user_report', None, '本人自述（2026-10-13 20:54）', 'text_only', 0.5,
  '本人：「再说吧我最近没事了可以找笑一释放性欲了关心一下她」'),
]
for eid, kind, sk, ref, ls, conf, quote in EVD:
    c.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
                 values (?,?,?,?,?,?,?,?,?,?,?)""",
              (None, eid, None, ref, sk, ref, None, quote, ls, conf, '10-13 状态切换'))
print('evidence +', len(EVD))
c.commit()
for t in ('events','evidence'): print(' ', t, c.execute('select count(*) from '+t).fetchone()[0])
c.close()
