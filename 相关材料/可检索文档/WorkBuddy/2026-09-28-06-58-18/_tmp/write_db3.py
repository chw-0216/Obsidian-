# -*- coding: utf-8 -*-
import sqlite3, hashlib, datetime

DB = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
ac = sqlite3.connect(DB)
ac.execute('PRAGMA foreign_keys=ON')

ev_cols = [r[1] for r in ac.execute("pragma table_info(events)")]
evd_cols = [r[1] for r in ac.execute("pragma table_info(evidence)")]
print('events cols:', ev_cols)
print('evidence cols:', evd_cols)

PH = 'P4 暑期与实习（北京台/项目）'

EV = [
    dict(
        event_id='EVT-20261012-001', date='2026-10-12', date_certainty='确定',
        phase=PH, level='A', score=72, subject='对方', category='关系结构',
        nature='分析结论',
        event='本科圈（城院∪3班 117 人）功能解剖：13 个「有消息」的人实为四种功能 —— ①债务线 2 人（程颂孟秋 ¥2000 / 尹诗琪英国欠款）②事务置换线 3 人（李博文拉人头 / 李莉丽科研助理内推 / 肖宇北大进校名额）③节日祝福线 6 人（李子轩/闻一青/蔡静文/李澳/张学鹏/陈飞，全年仅节日一次）④一次性事件线 2 人（王婧潭 2025-01-19 被删 / 裴青青急救问候）。真正有实质往来的仅 5 人。',
        person='程颂孟秋、尹诗琪、李博文、李莉丽、肖宇、李子轩、闻一青、王婧潭、裴青青、蔡静文、李澳、张学鹏、陈飞',
        distance='中', relation='本科同学', match_kind='分析结论',
        source='A·分析库', review_status='待核实',
        note='05 三·补·68.2 / 68.5'),
    dict(
        event_id='EVT-20261012-002', date='2026-10-12', date_certainty='确定',
        phase=PH, level='A', score=75, subject='我', category='身份/关系机制',
        nature='分析结论',
        event='「身份先行 · 分圈版本管理」：同一时期（2024-12→2025-12）他对本科圈至少给出 6 个身份版本 —— 李莉丽「北京国企/社保类」· 李子轩「国企综办」· 程颂孟秋「就在央美（读博）」· 李博文「有个备选学位」· 肖宇「我帮你走关系央选」· 尹诗琪「有点房租收入」。★ 其中「央美读博」是他本人先说的，为 USER.md「不得写博士在读」口径红线的源头之一。机制不是物理隔离（三人有 4-7 个共同群），是「没人会主动核对」。',
        person='程颂孟秋、李博文、李莉丽、李子轩、肖宇、尹诗琪',
        distance='中', relation='本科同学', match_kind='分析结论',
        source='A·分析库', review_status='待核实',
        note='05 三·补·68.3'),
    dict(
        event_id='EVT-20261012-003', date='2026-05-20', date_certainty='确定',
        phase=PH, level='B', score=55, subject='我', category='金钱/债务',
        nature='本人自述',
        event='厦门租车事故被索赔 ¥10,000（本人自述：私人租车 · 无保险 · 未及时报警 · 私了 · 对方车辆为宝马）。发生在与程颂孟秋的对话中，用以解释无法还款。★ 与「京密路」无关（全库「京密路」6 条无事故记录）。',
        person='程颂孟秋', distance='中', relation='本科同学', match_kind='本人自述',
        source='F·本人自述事件', review_status='待核实',
        note='05 三·补·68.4 A9'),
]

EVD = [
    dict(event_id='EVT-20261012-001', legacy_ref='idx:wxid_j5ekmvhqltug22',
         session_key='wxid_j5ekmvhqltug22', talker_name='程颂孟秋', ts=1767741720,
         quote='[2026-01-07] me 微信转账|收到转账￥2000.00元 / [2026-05-10] them 大哥，你是不是还欠我两千哦',
         link_status='rebuilt', confidence=0.9,
         note='程颂孟秋线：¥2,000 债务 2026-01→2026-09 未清（方向文本不唯一）'),
    dict(event_id='EVT-20261012-001', legacy_ref='idx:wxid_i2o78wu1pzgz21',
         session_key='wxid_i2o78wu1pzgz21', talker_name='尹诗琪', ts=1765109520,
         quote='[2025-12-07 20:13] me 也没少拖欠你钱在英国 / 几万的交情了',
         link_status='rebuilt', confidence=0.9,
         note='尹诗琪线：英国时期欠款，金额未明'),
    dict(event_id='EVT-20261012-001', legacy_ref='idx:wxid_sgzi99h3mx4n22',
         session_key='wxid_sgzi99h3mx4n22', talker_name='李子轩', ts=1738056120,
         quote='[2025-01-28] them 咱们这个聊天一年一次',
         link_status='rebuilt', confidence=0.95,
         note='节日祝福线自证：全年一次'),
    dict(event_id='EVT-20261012-001', legacy_ref='idx:wxid_4x0ry32wco6212',
         session_key='wxid_4x0ry32wco6212', talker_name='脾气不好的王婧潭', ts=1737227700,
         quote='[2025-01-19 03:15] system O.o开启了朋友验证，你还不是他（她）朋友',
         link_status='rebuilt', confidence=0.95,
         note='本科圈唯一明确的关系终止'),
    dict(event_id='EVT-20261012-002', legacy_ref='idx:wxid_j5ekmvhqltug22',
         session_key='wxid_j5ekmvhqltug22', talker_name='程颂孟秋', ts=1743045120,
         quote='[2025-03-27] them 大哥，你现在读博去了吗 / me 考上了算吧 / me 就在央美 / me 没去北师',
         link_status='rebuilt', confidence=0.95,
         note='★ USER.md「央美博士在读」口径红线的源头：他本人先说的'),
    dict(event_id='EVT-20261012-002', legacy_ref='idx:wxid_05offrd7pvf632',
         session_key='wxid_05offrd7pvf632', talker_name='李莉丽', ts=1735016700,
         quote='[2024-12-24] me 我也做行政类了 / 办公室一个北京国企 / 社保类的 / 全靠副总脸色活',
         link_status='rebuilt', confidence=0.9,
         note='「身份先行」版本之一，待本人核实'),
    dict(event_id='EVT-20261012-003', legacy_ref='idx:wxid_j5ekmvhqltug22',
         session_key='wxid_j5ekmvhqltug22', talker_name='程颂孟秋', ts=1779286800,
         quote='[2026-05-20] me 之前厦门的事故 / 在厦门发生的事故 / 私人租的 / 1万r / 被讹了一笔',
         link_status='rebuilt', confidence=0.9,
         note='厦门事故 ¥10,000（本人自述）'),
]

for e in EV:
    nk = hashlib.sha1(('%s|%s|%s' % (e['date'], e['person'], e['event'])).encode('utf-8')).hexdigest()
    e['natkey'] = nk
    e['people'] = e.get('people', e['person'])
    e['msg_count'] = e.get('msg_count', 0)
    e['impact'] = e.get('impact', '')
    e['mark'] = e.get('mark', '')
    e['extract_version'] = 'v3-20261012'
    e['created_at'] = e['updated_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    ac.execute('delete from events where event_id=?', (e['event_id'],))
    cols = [c for c in e if c in ev_cols]
    ac.execute('insert into events (%s) values (%s)' % (','.join(cols), ','.join('?' * len(cols))),
               [e[c] for c in cols])

for d in EVD:
    d['confidence'] = float(d['confidence'])
    d['msg_id'] = None
    cols = [c for c in d if c in evd_cols]
    ac.execute('insert into evidence (%s) values (%s)' % (','.join(cols), ','.join('?' * len(cols))),
               [d[c] for c in cols])

ac.commit()
for t in ('events', 'evidence', 'persons', 'sources'):
    print(t, ac.execute('select count(*) from ' + t).fetchone()[0])
print('新增事件 3 · 证据 7')
