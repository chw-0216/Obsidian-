# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8')
ADB = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
ac = sqlite3.connect(ADB)
ac.row_factory = sqlite3.Row
NOW = '2026-10-11 21:30:00'

print('现有 phase 取值:', sorted({r[0] for r in ac.execute('select distinct phase from events')}))
print('2026-10-11 已有事件:', [r[0] for r in ac.execute("select event_id from events where date='2026-10-11'")])
print('周雯娟 已存在:', ac.execute("select count(*) from persons where person_id='wxid_uhulgmrvfq4a12'").fetchone()[0])

# ---------- 1) persons ----------
ac.execute("""insert or replace into persons (person_id,name,talker,relation,distance,note)
  values (?,?,?,?,?,?)""", (
    'wxid_uhulgmrvfq4a12', '周雯娟', 'wxid_uhulgmrvfq4a12',
    '本科同学（首经贸城院）', '中',
    '昵称 Sora · 微信号 sora4811 · 标签 37=城院/107=全部 · ★ 消息层 0 条（无私聊/无群发言/正文 0 命中）· '
    '朋友圈 feed 1 条（post 2026-10-11 16:16）· 定位见 05 三·补·66.3'))
ac.execute("insert or replace into aliases (alias,person_id,kind) values (?,?,?)", ('周雯娟', 'wxid_uhulgmrvfq4a12', '备注'))
ac.execute("insert or replace into aliases (alias,person_id,kind) values (?,?,?)", ('Sora', 'wxid_uhulgmrvfq4a12', '昵称'))
ac.execute("insert or replace into aliases (alias,person_id,kind) values (?,?,?)", ('sora4811', 'wxid_uhulgmrvfq4a12', '微信号'))
ac.execute("insert or replace into aliases (alias,person_id,kind) values (?,?,?)", ('周文娟', 'wxid_uhulgmrvfq4a12', '同音误写'))

# ---------- 2) events ----------
EV = [
 dict(eid='EVT-20261011-001',
   date='2026-10-11', certainty='确定', phase='P4 暑期与实习（北京台/项目）',
   level='B', score=40, subject='对方', category='生活/事务', nature='本人自述',
   event='周雯娟与李博文（本科首经贸城院同学）当天去环球影城，拍照发了朋友圈；本人给两人的帖子都点了赞。｜ ★ 证据等级：本人自述（user_report）——本地库取不到他的点赞动作，两人帖子正文亦未缓存。',
   person='周雯娟、李博文', distance='中', relation='本科同学', match_kind='本人自述',
   people='周雯娟、李博文', msg_count=0, load_rule='中', load_score=30,
   source='F·本人自述事件', review_status='待核实', note='05 三·补·66.5'),
 dict(eid='EVT-20261011-002',
   date='2026-10-11', certainty='确定', phase='P4 暑期与实习（北京台/项目）',
   level='A', score=70, subject='我', category='身份/关系机制', nature='本人自述',
   event='本人自述：「我在本科冒充过官二代，所以有些占领位置关系」→ 触发全库定位，首次识别出「本科圈（首经贸城院，114 人）」。｜ ★ 属敏感自我披露，仅留引擎层。',
   person='我', distance='—', relation='—', match_kind='本人自述',
   people='', msg_count=0, load_rule='高', load_score=60,
   source='F·本人自述事件', review_status='待核实', note='05 三·补·66.4「身份先行」'),
]
for e in EV:
    nk = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
    ac.execute("delete from events where event_id=?", (e['eid'],))
    ac.execute("""insert into events
      (event_id,natkey,date,date_certainty,phase,level,score,subject,category,nature,event,person,
       distance,relation,match_kind,people,msg_count,load_rule,load_score,load_self,mark,source,impact,
       review_status,extract_version,created_at,updated_at)
      values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
      e['eid'], nk, e['date'], e['certainty'], e['phase'], e['level'], e['score'], e['subject'],
      e['category'], e['nature'], e['event'], e['person'], e['distance'], e['relation'],
      e['match_kind'], e['people'], e['msg_count'], e['load_rule'], e['load_score'], '',
      '', e['source'], '', e['review_status'], 'v1-manual-20261011', NOW, NOW))
    print('event', e['eid'], 'ok')

# ---------- 3) evidence ----------
ac.execute("delete from evidence where event_id like 'EVT-20261011-%'")
ac.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
  values (?,?,?,?,?,?,?,?,?,?,?)""", (
   None, 'EVT-20261011-001', None, 'sns:SnsTopItem_1',
   'wxid_uhulgmrvfq4a12', '周雯娟', 1760160960,
   'SnsTopItem_1: username=wxid_uhulgmrvfq4a12, create_time=2026-10-11 16:16, is_read=1',
   'rebuilt', 0.9, '本地库实证：周雯娟当天 16:16 有发帖（正文未缓存）'))
ac.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
  values (?,?,?,?,?,?,?,?,?,?,?)""", (
   None, 'EVT-20261011-001', None, 'user:2026-10-11T21:09',
   '', '本人', 0,
   '本人 21:09 口述：「刚刚周文娟和李博文去了环球影城，拍照发了朋友圈…刚刚给她俩都点赞了」',
   'text_only', 0.5, '★ user_report：他的点赞动作本地库结构性取不到（SnsMessage_tmp3 只记别人点赞他）'))
ac.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,link_status,confidence,note)
  values (?,?,?,?,?,?,?,?,?,?,?)""", (
   None, 'EVT-20261011-002', None, 'sns:朋友圈导出_2026-07-23',
   '', '本人', 0,
   '本人 2025-04-09 朋友圈原文：「偷偷忏悔一下 路上冒犯的大叔，其实我不是学法的，但是确实下次不该这么讹你」；2026-05-01「重生之黑道班主任短期体验卡…五一假期冒名版」',
   'rebuilt', 0.9, '★ 「身份先行」模式的两个自证帖（同一导出可回链）'))
print('evidence ok')

# ---------- 4) sources ----------
ac.execute("""insert or replace into sources (source_id,kind,path,content_hash,first_seen,last_ok,privacy,note)
  values (?,?,?,?,?,?,?,?)""", (
   'SRC-WEFLOW-SNS-20260723', '朋友圈全量导出',
   r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json',
   '', '2026-10-11', '2026-10-11', 'private',
   '3,534 帖 · 2012-10-12 → 2026-07-23 · 含 likes[] → 他点赞别人的唯一可读来源'))

ac.commit()
print()
print('=== 复核 ===')
print('events 2026-10-11:', [r[0] for r in ac.execute("select event_id from events where date='2026-10-11'")])
print('persons 总数:', ac.execute('select count(*) from persons').fetchone()[0])
print('evidence 总数:', ac.execute('select count(*) from evidence').fetchone()[0])
print('events 总数:', ac.execute('select count(*) from events').fetchone()[0])
ac.close()
