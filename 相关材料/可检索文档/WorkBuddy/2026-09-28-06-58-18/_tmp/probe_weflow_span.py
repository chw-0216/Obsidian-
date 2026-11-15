# -*- coding: utf-8 -*-
"""确认 WeFlow 全量导出的时间覆盖 + 本科圈几人的实际跨度"""
import json, io, os, datetime, glob

B = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出'
out = []
def P(*a):
    t = ' '.join(str(x) for x in a); out.append(t); print(t)

def scan(fp, limit=None):
    """返回 (条数, 最早, 最晚, 样例键)"""
    try:
        with io.open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return None, None, None, 'ERR:%s' % e
    msgs = data if isinstance(data, list) else (data.get('messages') or data.get('data') or [])
    if not isinstance(msgs, list):
        return None, None, None, 'KEYS:%s' % list(data)[:8]
    ts = []
    for m in msgs:
        if not isinstance(m, dict): continue
        for k in ('createTime', 'create_time', 'time', 'timestamp', 'CreateTime', 'ts'):
            if k in m and m[k]:
                try:
                    v = int(m[k]); ts.append(v if v < 1e12 else v // 1000); break
                except Exception: pass
    if not ts: return len(msgs), None, None, 'NO_TS keys=%s' % (list(msgs[0])[:12] if msgs else [])
    return len(msgs), min(ts), max(ts), list(msgs[0])[:12]

def fmt(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M') if t else '—'

P('=== 1. 本科圈几人的 JSON ===')
for nm in ['程颂孟秋', '李博文 城市学院', '尹诗琪', '李莉丽', '肖宇']:
    fp = os.path.join(B, '私聊_%s' % nm, '私聊_%s.json' % nm)
    if not os.path.exists(fp):
        P('  %-16s 无 JSON' % nm); continue
    n, a, b, k = scan(fp)
    P('  %-16s %6s 条 | %s → %s | %s' % (nm, n, fmt(a), fmt(b), k))

P('')
P('=== 2. 周雯娟 相关文件 ===')
hits = []
for pat in ['*周雯娟*', '*Sora*', '*sora*', '*雯娟*']:
    hits += glob.glob(os.path.join(B, '**', pat), recursive=True)
P('  命中:', hits if hits else '（无）')
d = os.path.join(B, '私聊_周雯娟')
if os.path.isdir(d):
    for root, dirs, files in os.walk(d):
        P('  %s -> dirs=%s files=%s' % (root.replace(B, '.'), dirs, files))

P('')
P('=== 3. 抽样 200 个私聊 JSON，看全局时间覆盖 ===')
files = glob.glob(os.path.join(B, '私聊_*', '私聊_*.json'))
P('  私聊 JSON 总数 =', len(files))
import random
random.seed(1)
sample = random.sample(files, min(200, len(files)))
gmin, gmax, ok = None, None, 0
for fp in sample:
    n, a, b, k = scan(fp)
    if a:
        ok += 1
        gmin = a if gmin is None else min(gmin, a)
        gmax = b if gmax is None else max(gmax, b)
P('  有效样本 %d/%d' % (ok, len(sample)))
P('  全局最早 = %s' % fmt(gmin))
P('  全局最晚 = %s' % fmt(gmax))

P('')
P('=== 4. 全库最早时间（扫全部私聊 JSON 的前若干条）===')
best = None; bestf = None
for fp in files[:]:
    try:
        with io.open(fp, 'r', encoding='utf-8') as f:
            head = f.read(4000)
        i = head.find('"createTime"')
        if i < 0: continue
        j = head.find(':', i) + 1
        k = head.find(',', j)
        raw = head[j:k].strip().strip('"')
        if raw.startswith('"'):
            import re as _re
            m = _re.search(r'20\d\d-\d\d-\d\d', raw)
            if not m: continue
            v = int(datetime.datetime.strptime(m.group(0), '%Y-%m-%d').timestamp())
        else:
            v = int(raw)
            if v > 1e12: v //= 1000
        if best is None or v < best:
            best, bestf = v, os.path.basename(fp)
    except Exception:
        pass
P('  最早期的一条 = %s  (%s)' % (fmt(best), bestf))

io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\probe_weflow_span.txt', 'w', encoding='utf-8').write('\n'.join(out))
P('')
P('-> _tmp\\probe_weflow_span.txt')
