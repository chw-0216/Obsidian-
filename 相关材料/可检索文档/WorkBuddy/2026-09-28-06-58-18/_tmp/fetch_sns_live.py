# -*- coding: utf-8 -*-
import json, io, os, re, urllib.request, datetime
from datetime import timezone, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')

CFG = r"C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
CST = timezone(timedelta(hours=8))
tok = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding='utf-8').read()).group(1)
print('token tail:', tok[-6:])

def api(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def fmt(ts):
    ts = int(ts)
    if ts > 10**12: ts //= 1000
    return datetime.datetime.fromtimestamp(ts, CST).strftime('%Y-%m-%d %H:%M:%S')

try:
    h = api('/api/v1/health')
    print('health:', h)
except Exception as e:
    print('health FAIL:', e)

TARGETS = {
    '周雯娟': 'wxid_uhulgmrvfq4a12',
    '李博文': 'wxid_4yurl8wrbi4a22',
}
for nm, wx in TARGETS.items():
    print('\n===== %s %s =====' % (nm, wx))
    try:
        d = api('/api/v1/sns/timeline?usernames=%s&limit=50&offset=0&media=1' % wx)
    except Exception as e:
        print('  FAIL:', e); continue
    tl = d.get('timeline') or d.get('posts') or []
    print('  returned:', len(tl), '| count:', d.get('count'), '| keys:', list(d.keys())[:8])
    mine = [p for p in tl if p.get('username') == wx]
    print('  本人帖:', len(mine))
    for p in sorted(mine, key=lambda x: int(x.get('createTime') or 0))[-10:]:
        print('   [%s] type=%s media=%d' % (fmt(p['createTime']), p.get('type'), len(p.get('media') or [])))
        print('       正文:', (p.get('contentDesc') or '')[:200].replace('\n', ' '))
        if p.get('likes'): print('       点赞:', json.dumps(p['likes'], ensure_ascii=False)[:300])
        if p.get('comments'): print('       评论:', json.dumps(p['comments'], ensure_ascii=False)[:300])
        if p.get('location'): print('       位置:', json.dumps(p['location'], ensure_ascii=False)[:200])
