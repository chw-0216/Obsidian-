# -*- coding: utf-8 -*-
import json, io, re, urllib.request, sys, datetime
from datetime import timezone, timedelta
sys.stdout.reconfigure(encoding='utf-8')
CFG = r"C:/Users/wardc/AppData/Roaming/WeFlow/WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
CST = timezone(timedelta(hours=8))
tok = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding='utf-8').read()).group(1)
def api(p):
    r = urllib.request.Request(BASE+p, headers={"Authorization":"Bearer "+tok})
    with urllib.request.urlopen(r, timeout=90) as x: return json.loads(x.read().decode('utf-8'))
tests = [
  ('刘华赞(已知可用)', 'wxid_ltqmzbyc87cp22'),
  ('周雯娟', 'wxid_uhulgmrvfq4a12'),
  ('李博文', 'wxid_4yurl8wrbi4a22'),
  ('陈昶文', 'wxid_0gb0smyjaoyk22'),
]
for nm, wx in tests:
    try:
        d = api('/api/v1/sns/timeline?usernames=%s&limit=200&offset=0&media=1' % wx)
        tl = d.get('timeline') or []
        print('%-16s %-24s count=%-5s len=%d' % (nm, wx, d.get('count'), len(tl)))
        for p in tl[:3]:
            ts = int(p.get('createTime') or 0)
            if ts > 10**12: ts //= 1000
            print('     ', datetime.datetime.fromtimestamp(ts, CST).strftime('%Y-%m-%d %H:%M'), p.get('nickname'), (p.get('contentDesc') or '')[:60].replace('\n',' '))
    except Exception as e:
        print('%-16s FAIL %s' % (nm, e))
