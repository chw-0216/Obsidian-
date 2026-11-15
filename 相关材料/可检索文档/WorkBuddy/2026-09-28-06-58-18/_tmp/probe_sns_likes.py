# -*- coding: utf-8 -*-
import json, io, sqlite3, datetime

J = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json'
ME = 'wxid_zn4ozsnn8esr21'
PEOPLE = {'wxid_f77sxlrwo0tr12': ('李紫懿', '榕'),
          'wxid_utdeb3kw2z5j22': ('朱子涵', '001')}

out = []
def P(*a): out.append(' '.join(str(x) for x in a))
def ts2s(t):
    try: return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

posts = json.load(io.open(J, encoding='utf-8'))['posts']
P('总帖数', len(posts))

P('')
P('===== 1) 她们作为作者发的帖子（截至 2026-07-23 导出） =====')
for wx, (nm, nk) in PEOPLE.items():
    rs = [p for p in posts if p.get('username') == wx]
    P('  ★ %s: %d 帖' % (nm, len(rs)))
    for p in rs[:10]:
        P('     %s  %s  likes=%s' % (p.get('createTimeStr', ts2s(p.get('createTime', 0))),
                                     (p.get('contentDesc') or '')[:60], p.get('likes')))

P('')
P('===== 2) 他点赞过的帖子中，作者是她们的 =====')
hit = 0
for p in posts:
    lk = p.get('likes') or []
    if '蔡浩文' in lk and p.get('username') in PEOPLE:
        hit += 1
        P('   ★ %s 的帖子 · %s · %s' % (PEOPLE[p['username']][0], p.get('createTimeStr'), (p.get('contentDesc') or '')[:50]))
P('  合计:', hit)

P('')
P('===== 3) 她们点赞/评论过谁（按昵称匹配 · 有误差） =====')
for wx, (nm, nk) in PEOPLE.items():
    liked = [p for p in posts if nk in (p.get('likes') or [])]
    P('  ★ %s (昵称「%s」) 出现在 %d 帖的 likes 里' % (nm, nk, len(liked)))
    for p in liked[:8]:
        P('     %s  %s  %s' % (p.get('createTimeStr'), (p.get('nickname') or '')[:14], (p.get('contentDesc') or '')[:44]))

P('')
P('===== 4) 他的帖子 + 她们是否点赞（找他的帖） =====')
mine = [p for p in posts if p.get('username') == ME]
P('  他本人发帖 %d 条' % len(mine))
for p in sorted(mine, key=lambda x: x.get('createTime', 0), reverse=True)[:25]:
    lk = p.get('likes') or []
    flag = ''
    for wx, (nm, nk) in PEOPLE.items():
        if nk in lk: flag += ' ★%s赞了' % nm
    P('   %s  %-30s likes=%s%s' % (p.get('createTimeStr'), (p.get('contentDesc') or '')[:30], lk, flag))

P('')
P('===== 5) SnsMessage_tmp3 type 分布 =====')
d = sqlite3.connect('file:C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted/sns/sns.db?mode=ro', uri=True)
for r in d.execute("select type, count(*), sum(case when coalesce(content,'')<>'' then 1 else 0 end) from SnsMessage_tmp3 group by type"):
    P('  type=%s  %d 条  (有正文 %s)' % r)

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_sns_likes.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
