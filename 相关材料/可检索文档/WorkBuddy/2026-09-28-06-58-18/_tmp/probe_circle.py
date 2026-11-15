# -*- coding: utf-8 -*-
import sqlite3, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
cc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'contact', 'contact.db').replace('\\', '/'), uri=True)
cc.row_factory = sqlite3.Row
labels = {r['label_id_']: r['label_name_'] for r in cc.execute('select * from contact_label')}
TAGRE = re.compile(rb'\xf2\x01(.)(.*?)(?=\xfa\x01|$)', re.S)
def tags_of(eb):
    b = bytes(eb or b'')
    m = TAGRE.search(b)
    if not m: return []
    ln = m.group(1)[0]
    return [x for x in m.group(2)[:ln].decode('utf-8', 'ignore').split(',') if x.strip().isdigit()]

# 已知本科相关的人 → 看他们的标签
CHECK = {
    '李紫玥': '本科同学（04 表）',
    '程颂孟秋': '前本科室友（04 表）',
    '李博文': '城市学院（04 表）',
    '周雯娟': '本轮新增',
    '王若彤': '高中同学（04 表）',
    '柯益盈': '高中同学圈（04 表）',
    '高晓斌': '初中同学（04 表）',
    '姚一行': '初中同学（04 表）',
    '马腾': '李博文聊天里提到',
    '贾甲': '李博文聊天里提到',
    '尹诗琪': '朋友圈共同点赞圈',
    '田浩然': '朋友圈共同点赞圈',
    '苏童': '朋友圈共同点赞圈',
    '王瑞霖': '朋友圈共同点赞圈',
    '谭瑶': '城院圈',
    '城市学长': '城院圈',
    '李明艺': '城院圈（备注含"城市学院 大二"）',
}
print('%-10s %-30s %-26s %-16s %s' % ('查谁', '备注', 'wxid', '昵称', '标签'))
for nm, why in CHECK.items():
    rows = list(cc.execute('select username,remark,nick_name,extra_buffer from contact where remark like ? or nick_name like ?',
                           ('%'+nm+'%', '%'+nm+'%')))
    if not rows:
        print('%-10s %-30s %s' % (nm, why, '(通讯录无)'))
        continue
    for r in rows[:2]:
        tg = ','.join('%s=%s' % (t, labels.get(int(t), '?')) for t in tags_of(r['extra_buffer']))
        print('%-10s %-30s %-26s %-16s %s' % (nm, why, r['username'], (r['nick_name'] or '')[:16], tg))

print()
print('=== 谁带「本科」字样的标签 ===')
for tid, nm in labels.items():
    if '本科' in nm or '大学' in nm or '首经' in nm:
        print('  标签', tid, nm)

print()
print('=== 搜备注含「本科」「首经」「城院」的联系人 ===')
for kw in ('本科', '首经', '城院', '城市学院', '首经贸'):
    rows = list(cc.execute('select username,remark,nick_name from contact where remark like ? or nick_name like ?', ('%'+kw+'%', '%'+kw+'%')))
    print('  「%s」-> %d' % (kw, len(rows)))
    for r in rows[:12]:
        print('     %-26s remark=%-24s nick=%s' % (r['username'], (r['remark'] or '')[:24], (r['nick_name'] or '')[:16]))
