# -*- coding: utf-8 -*-
import json, io, re, urllib.request, datetime, sys, os
from datetime import timezone, timedelta
sys.stdout.reconfigure(encoding='utf-8')
CFG = r"C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
CST = timezone(timedelta(hours=8))
tok = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding='utf-8').read()).group(1)
def api(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))
def fmt(ts):
    ts = int(ts)
    if ts > 10**12: ts //= 1000
    return datetime.datetime.fromtimestamp(ts, CST).strftime('%Y-%m-%d %H:%M')

allp, off = [], 0
for page in range(30):
    try:
        d = api('/api/v1/sns/timeline?limit=200&offset=%d&media=1' % off)
    except Exception as e:
        print('page%d FAIL %s' % (page, e)); break
    tl = d.get('timeline') or []
    if not tl: break
    allp += tl
    print('  page%d off=%d -> %d 条 (count=%s)' % (page, off, len(tl), d.get('count')))
    if len(tl) < 200: break
    off += len(tl)

seen, uniq = set(), []
for p in allp:
    k = p.get('id') or p.get('tid') or (p.get('username'), p.get('createTime'))
    if k in seen: continue
    seen.add(k); uniq.append(p)
uniq.sort(key=lambda p: int(p.get('createTime') or 0))
print('\n去重后 %d 条 · %s -> %s' % (len(uniq), fmt(uniq[0]['createTime']) if uniq else '-', fmt(uniq[-1]['createTime']) if uniq else '-'))

os.makedirs(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\sns_live', exist_ok=True)
json.dump(uniq, io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\sns_live\timeline_all.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved.')

print('\n=== 关键词定位 ===')
for kw in ('周雯娟', 'Sora', 'sora4811', '李博文', 'bownbown', '环球', '影城', '哈利'):
    hits = [p for p in uniq if kw in json.dumps(p, ensure_ascii=False)]
    print('  %-10s -> %d' % (kw, len(hits)))
    for p in hits[:6]:
        print('      [%s] %s | %s' % (fmt(p['createTime']), p.get('nickname'), (p.get('contentDesc') or '')[:80].replace('\n', ' ')))
        if p.get('likes'): print('          点赞:', json.dumps(p['likes'], ensure_ascii=False)[:200])

print('\n=== 我(蔡浩文)点赞过的最近 20 条 ===')
liked = [p for p in uniq if '蔡浩文' in (p.get('likes') or [])]
print('  合计:', len(liked))
for p in liked[-20:]:
    print('  [%s] %-16s | %s' % (fmt(p['createTime']), p.get('nickname'), (p.get('contentDesc') or '')[:70].replace('\n', ' ')))
