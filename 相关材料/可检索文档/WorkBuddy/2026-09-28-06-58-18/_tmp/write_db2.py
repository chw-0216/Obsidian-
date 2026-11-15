# -*- coding: utf-8 -*-
"""analysis.sqlite：周雯娟改档 + 本科班级结构事件"""
import sqlite3, hashlib, io

DB = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite'
WX = 'wxid_uhulgmrvfq4a12'
ac = sqlite3.connect(DB)
cur = ac.cursor()

def cnt(t):
    return cur.execute('select count(*) from %s' % t).fetchone()[0]

before = {t: cnt(t) for t in ('persons', 'aliases', 'events', 'evidence', 'sources')}
print('before', before)

# --- 1) 周雯娟 改档 ---
cur.execute("""update persons set relation=?, distance=?, note=?
               where person_id=?""", (
    '本科同班同学（城院 · 公管三班）', '中',
    '昵称 Sora · 微信号 sora4811 · 标签 37=城院/107=全部（★ 未打 49=3班，但人在「17级公管三班通知群」）· '
    '★ 24 个本科群（17级公管三班通知群 / 17区经2班 / 三班候选群 / 公管三，四班计算机 / 城市学院学生会13.0 等）· '
    '★ 私聊 0 条（原始库无 Msg_ 表 · SessionTable 无行 · 索引库 0 · WeFlow 无 JSON）· '
    '★ 口径＝2024-11-10 之后；本科时期（2017–2021）本地不可知 · 朋友圈 2026-10-11 16:16 有帖。'
    '｜ 本人 2026-10-11 确认「本科同班同学」→ 05 三·补·67', WX))
print('persons updated:', cur.rowcount)

# --- 2) 新事件：本科班级结构 ---
EV = dict(
    eid='EVT-20261011-003',
    date='2026-10-11',
    certainty='确定',
    phase='P4 暑期与实习（北京台/项目）',
    level='A', score=75, subject='我',
    category='身份/关系机制', nature='数据实证',
    event='本科班级结构首次确定：城院（首都经济贸易大学城市经济与公共管理学院）标签 114 人；'
          '公管三班 群 29 人 / 标签「3班」24 人；区经2班 群 24 人。验证链＝标签3班 24 人 ∩ 公管三班群 29 人 = 22 人。'
          '周雯娟与李博文均为公管三班同班同学。本科圈 117 人里 104 人（89%）在 2024-11-10 之后零消息；'
          '12 个班群 2 年内 0 条、他 0 发言 → 本科圈是「沉在通讯录里的历史层」，不是活跃社交资产。'
          '｜ ★ 数据源时间下限实测＝2024-11-10（索引库 04:12 / WeFlow 全量导出 16:52），本科时期记录本地不存在。',
    person='周雯娟、李博文、程颂孟秋',
    distance='中', relation='本科同班同学',
    match_kind='数据实证',
    source='E·群成员与标签实证',
    review_status='已核实',
    note='05 三·补·67',
)
nk = hashlib.sha1(('%s|%s|%s' % (EV['date'], EV['person'], EV['event'])).encode('utf-8')).hexdigest()
cur.execute('delete from events where event_id=?', (EV['eid'],))
cur.execute("""insert into events
 (event_id,natkey,date,date_certainty,phase,level,score,subject,category,nature,event,person,
  distance,relation,match_kind,people,msg_count,load_rule,load_score,load_self,mark,source,impact,
  review_status,extract_version,created_at,updated_at)
 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
    EV['eid'], nk, EV['date'], EV['certainty'], EV['phase'], EV['level'], EV['score'], EV['subject'],
    EV['category'], EV['nature'], EV['event'], EV['person'], EV['distance'], EV['relation'],
    EV['match_kind'], EV['person'], 0, '', 0, 0, '', EV['source'], '',
    EV['review_status'], 'v1-manual-20261011', '2026-10-11', '2026-10-11'))
print('event inserted')

# --- 3) 证据 ---
EVD = [
    ('EVT-20261011-003', 'contact.db:chatroom_member+contact_label',
     '标签「3班」(49)=24 人 ∩ 17级公管三班通知群(29 人) = 22 人；周雯娟/李博文/蔡浩文均在该群',
     'rebuilt', 0.95, '群成员与标签交叉验证 → 公管三班'),
    ('EVT-20261011-003', 'contact.db:chatroom_member',
     '周雯娟所在 24 个群：17级公管三班通知群 / 17区经2班 / 三班候选群 / 公管三，四班计算机 / 城市学院学生会13.0 / 2021届城院毕业生通知群 …',
     'rebuilt', 0.95, '她在 24 个本科群'),
    ('EVT-20261011-003', 'index.sqlite:sessions',
     '本科班群 2 年内条数：17区经2班 4 · 2021届城院毕业生通知群 44 · 其余 12 群 0；他发言 0',
     'rebuilt', 0.9, '班群静音'),
    ('EVT-20261011-003', 'index.sqlite:min(ts)/WeFlow 导出',
     '索引库最早 2024-11-10 04:12 · WeFlow 全量导出最早 2024-11-10 16:52 → 数据下限一致',
     'rebuilt', 0.95, '本科时期记录本地不存在'),
]
for ev, sk, q, ls, cf, nt in EVD:
    cur.execute("""insert into evidence (evidence_id,event_id,msg_id,legacy_ref,session_key,
                    talker_name,ts,quote,link_status,confidence,note)
                   values (?,?,?,?,?,?,?,?,?,?,?)""", (
        None, ev, None, sk, WX, '周雯娟', 1791720000, q, ls, cf, nt))
print('evidence inserted:', len(EVD))

ac.commit()
after = {t: cnt(t) for t in ('persons', 'aliases', 'events', 'evidence', 'sources')}
print('after ', after)
ac.close()
