# -*- coding: utf-8 -*-
import io, json, datetime, sys, os, collections
sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json'
j = json.loads(io.open(P, encoding='utf-8', errors='ignore').read())
posts = j['posts']
print('帖子总数:', len(posts), '| 导出:', j.get('exportTime'))

ME = '蔡浩文'
liked = [p for p in posts if ME in (p.get('likes') or [])]
print('我点赞过的帖子:', len(liked), '(%.1f%%)' % (100*len(liked)/len(posts)))

# 我点赞率按月
by = collections.Counter()
tot = collections.Counter()
for p in posts:
    d = datetime.datetime.fromtimestamp(p['createTime']).strftime('%Y-%m')
    tot[d] += 1
    if ME in (p.get('likes') or []): by[d] += 1
print('\n按月：我点赞数 / 当月总帖数（点赞率）')
for k in sorted(tot):
    if tot[k] >= 10:
        print('  %s  %4d / %4d  = %5.1f%%' % (k, by[k], tot[k], 100*by[k]/tot[k]))

print('\n=== 我点赞最多的作者 TOP20 ===')
c = collections.Counter(p.get('nickname') for p in liked)
for nm, n in c.most_common(20):
    print('  %-24s %d' % (nm, n))

print('\n=== 帖子里出现过「蔡浩文」点赞的所有人（去重）===')
print('  作者数:', len(set(p.get('nickname') for p in liked)), '| 总帖数:', len(posts))

# 谁点赞过我？(在他自己发的帖子里找)
mine = [p for p in posts if p.get('username') == 'wxid_zn4ozsnn8esr21' or p.get('nickname') == ME]
print('\n=== 导出里他本人发的帖子:', len(mine), '===')
for p in sorted(mine, key=lambda x: x['createTime']):
    print('  %s | %s | media=%d | likes=%s | comments=%d' % (
        p.get('createTimeStr'), (p.get('contentDesc') or '')[:50].replace('\n',' '),
        len(p.get('media') or []), json.dumps(p.get('likes') or [], ensure_ascii=False)[:120],
        len(p.get('comments') or [])))

# 本科圈（城院）作者在我点赞名单里的占比
CHENGYUAN = ['田浩然','尹诗琪','苏童','王瑞霖','谭瑶','马腾','贾甲','周雯娟','程思卓','裴青青','朱冰淇','李坤琪','顾家麟','邱凡峻','饶明','黄倩','许佳诺','任绍铭','苗成','任婷婷','李莉丽','王雪媛','朱荩臣','陈嘉豪','闫家睿','李博文']
n_cy = sum(1 for p in liked if p.get('nickname') in CHENGYUAN)
print('\n我点赞的帖子里，城院圈作者的:', n_cy)
for p in liked:
    if p.get('nickname') in CHENGYUAN:
        print('   %s | %-10s | %s' % (p.get('createTimeStr'), p.get('nickname'), (p.get('contentDesc') or '')[:60].replace('\n',' ')))
