# -*- coding: utf-8 -*-
import io, json, os, re
p2 = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json'
raw = io.open(p2, encoding='utf-8', errors='ignore').read()
j = json.loads(raw)
print('top keys:', list(j.keys()) if isinstance(j, dict) else type(j))
posts = j.get('posts') if isinstance(j, dict) else j
print('posts:', len(posts))
print('post0 keys:', list(posts[0].keys()))
print()

def show(kw):
    print('=== 命中「%s」 ===' % kw)
    for i, po in enumerate(posts):
        blob = json.dumps(po, ensure_ascii=False)
        if kw in blob:
            print('  [%d] %s | %s | %s' % (i, po.get('nickname'), po.get('createTimeStr'), (po.get('contentDesc') or '')[:120].replace('\n', ' ')))
            print('       likes=%s media=%d' % (po.get('likes'), len(po.get('media') or [])))

for kw in ('周雯娟', '环球'):
    show(kw)

print()
print('=== 该导出里 蔡浩文 点过赞的帖子 ===')
n = 0
for i, po in enumerate(posts):
    if '蔡浩文' in (po.get('likes') or []):
        n += 1
        if n <= 20:
            print('  %s | %-14s | %s' % (po.get('createTimeStr'), po.get('nickname'), (po.get('contentDesc') or '')[:70].replace('\n', ' ')))
print('  合计我点赞过的帖子:', n, '/', len(posts))

print()
print('=== 导出覆盖时间范围 ===')
ts = [po.get('createTime') for po in posts if po.get('createTime')]
import datetime
print('  ', datetime.datetime.fromtimestamp(min(ts)).strftime('%Y-%m-%d'), '->', datetime.datetime.fromtimestamp(max(ts)).strftime('%Y-%m-%d'))
