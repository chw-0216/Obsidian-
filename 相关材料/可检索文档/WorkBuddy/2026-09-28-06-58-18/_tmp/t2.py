# -*- coding: utf-8 -*-
import json, io, re, urllib.request, datetime, sys
from datetime import timezone, timedelta
sys.stdout.reconfigure(encoding='utf-8')
CFG = r"C:/Users/wardc/AppData/Roaming/WeFlow/WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
CST = timezone(timedelta(hours=8))
tok = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding='utf-8').read()).group(1)
def api(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))
def fmt(ts):
    ts=int(ts)
    if ts>10**12: ts//=1000
    return datetime.datetime.fromtimestamp(ts,CST).strftime('%Y-%m-%d %H:%M')
for q in ['/api/v1/sns/timeline?limit=20',
          '/api/v1/sns/timeline?limit=20&media=1',
          '/api/v1/sessions?limit=3']:
    print('---', q)
    try:
        d = api(q)
        print('  keys:', list(d.keys()) if isinstance(d,dict) else type(d))
        tl = d.get('timeline') if isinstance(d,dict) else None
        print('  count:', d.get('count') if isinstance(d,dict) else '-', '| len:', len(tl) if tl is not None else '-')
        if tl:
            for p in tl[:6]:
                print('   ', fmt(p.get('createTime',0)), '|', p.get('nickname'), '|', (p.get('contentDesc') or '')[:60].replace('\n',' '), '| likes:', json.dumps(p.get('likes') or [], ensure_ascii=False)[:120])
        elif isinstance(d,dict) and d.get('sessions'):
            for s in d['sessions'][:3]: print('   ', s.get('name') or s.get('displayName'), s.get('id'))
    except Exception as e:
        print('  FAIL:', e)
