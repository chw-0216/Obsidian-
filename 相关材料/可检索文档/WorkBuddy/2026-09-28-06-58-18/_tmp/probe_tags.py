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
    s = m.group(2)[:ln]
    return [x for x in s.decode('utf-8', 'ignore').split(',') if x.strip().isdigit()]

rows = list(cc.execute("select username,remark,nick_name,alias,extra_buffer from contact"))
print('通讯录总数:', len(rows))
byt = {}
for r in rows:
    for t in tags_of(r['extra_buffer']):
        byt.setdefault(t, []).append(r)

for tid in ('37', '49'):
    nm = labels.get(int(tid), '?')
    grp = byt.get(tid, [])
    print('\n===== 标签 %s「%s」 共 %d 人 =====' % (tid, nm, len(grp)))
    for r in grp:
        print('   %-26s remark=%-18s nick=%-16s alias=%s' % (
            r['username'], (r['remark'] or '')[:18], (r['nick_name'] or '')[:16], r['alias']))

print('\n===== 同时带 37(城院) 的人 =====')
both = [r for r in rows if '37' in tags_of(r['extra_buffer'])]
for r in both:
    print('   %-26s remark=%-18s nick=%-16s tags=%s' % (
        r['username'], (r['remark'] or '')[:18], (r['nick_name'] or '')[:16], tags_of(r['extra_buffer'])))

print('\n===== 朋友圈共同点赞圈的人（田浩然/苏童/杨浩诚/王瑞霖/刘嘉怡/尹诗琪）=====')
for nm in ('田浩然', '苏童', '杨浩诚', '王瑞霖', '刘嘉怡', '尹诗琪'):
    rr = list(cc.execute('select username,remark,nick_name,alias,extra_buffer from contact where remark like ? or nick_name like ?',
                         ('%'+nm+'%', '%'+nm+'%')))
    for r in rr:
        print('   %-8s -> %-26s remark=%-16s nick=%-14s tags=%s' % (nm, r['username'], r['remark'], r['nick_name'], tags_of(r['extra_buffer'])))
    if not rr:
        print('   %-8s -> (通讯录无)' % nm)
