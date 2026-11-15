# -*- coding: utf-8 -*-
import sqlite3, io, datetime

DEC = 'C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted'.replace('\\', '/')
IDX = 'C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite'
OUT = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_money2.txt', 'w', encoding='utf-8')
def P(*a):
    OUT.write(' '.join(str(x) for x in a) + '\n')

ix = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True)
cd = sqlite3.connect('file:%s/contact/contact.db?mode=ro' % DEC, uri=True)

PEOPLE = [('wxid_j5ekmvhqltug22', '程颂孟秋'), ('wxid_i2o78wu1pzgz21', '尹诗琪'),
          ('wxid_4yurl8wrbi4a22', '李博文'), ('wxid_05offrd7pvf632', '李莉丽'),
          ('wxid_zwutgxzu1ppt22', '肖宇'), ('wxid_sgzi99h3mx4n22', '李子轩'),
          ('wxid_l28x8imwmi0g21', '闻一青'), ('wxid_4x0ry32wco6212', '王婧潭'),
          ('wxid_g2k94eukarg222', '裴青青')]

P('##### 一、本科圈对话中的 转账/借贷/事故 关键词 #####')
for wx, nm in PEOPLE:
    P('===== %s =====' % nm)
    n = 0
    for ts, role, content in ix.execute(
            "select ts, role, content from messages where session_key=? and (content like '%转账%' or content like '%￥%' or content like '%借%' or content like '%欠%' or content like '%事故%' or content like '%赔%' or content like '%逾期%') order by ts", (wx,)):
        t = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        P('[%s] %-5s %s' % (t, role, (content or '').replace('\n', ' ')[:170]))
        n += 1
    P('  (共 %d 条)' % n)
    P()

P()
P('##### 二、全库搜索 厦门 / 望京 / 京密路 #####')
for kw in ('厦门', '望京', '京密路'):
    rows = ix.execute("select session_key, ts, role, substr(content,1,110) from messages where content like ? order by ts desc limit 20",
                      ('%' + kw + '%',)).fetchall()
    P('--- %s : 命中 %d 条 ---' % (kw, len(rows)))
    for r in rows:
        t = datetime.datetime.fromtimestamp(r[1]).strftime('%Y-%m-%d %H:%M')
        P('  %-24s %s %-5s %s' % (r[0][:24], t, r[2], (r[3] or '').replace('\n', ' ')))
    P()

P()
P('##### 三、三人（程颂孟秋/李博文/李莉丽）共同群 —— 验证「分圈」 #####')
def groups_of(wx):
    cid = cd.execute("select id from contact where username=?", (wx,)).fetchone()
    if not cid:
        return set()
    rids = [r[0] for r in cd.execute("select room_id from chatroom_member where member_id=?", (cid[0],))]
    out = {}
    for rid in rids:
        r = cd.execute("select username,nick_name from contact where id=?", (rid,)).fetchone()
        if r:
            out[r[0]] = r[1]
    return out

g1 = groups_of('wxid_j5ekmvhqltug22')
g2 = groups_of('wxid_4yurl8wrbi4a22')
g3 = groups_of('wxid_05offrd7pvf632')
P('程颂孟秋 %d 群 / 李博文 %d 群 / 李莉丽 %d 群' % (len(g1), len(g2), len(g3)))
for a, b, na, nb in ((g1, g2, '程颂孟秋', '李博文'), (g1, g3, '程颂孟秋', '李莉丽'), (g2, g3, '李博文', '李莉丽')):
    inter = set(a) & set(b)
    P('%s ∩ %s = %d 个: %s' % (na, nb, len(inter), ' / '.join((a[k] or k)[:20] for k in list(inter)[:12])))
OUT.close()
print('done')
