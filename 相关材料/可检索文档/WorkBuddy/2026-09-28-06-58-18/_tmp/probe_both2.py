# -*- coding: utf-8 -*-
import sqlite3, os, datetime, io, json, re
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
M = 1 << 64
WEN = 'wxid_uhulgmrvfq4a12'; LI = 'wxid_4yurl8wrbi4a22'; ME = 'wxid_zn4ozsnn8esr21'
def fmt(t):
    try: return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

cc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'contact', 'contact.db').replace('\\', '/'), uri=True)
cc.row_factory = sqlite3.Row
labels = {r['label_id_']: r['label_name_'] for r in cc.execute('select * from contact_label')}
print('=== contact_label 全表 (%d) ===' % len(labels))
for k in sorted(labels):
    print('   %-4s %s' % (k, labels[k]))

print()
print('=== 李博文 extra_buffer 里的标签 ID 49,37,107 ===')
for i in (49, 37, 107):
    print('   %s -> %s' % (i, labels.get(i, '(无)')))

print()
print('=== 李博文 备注/签名 完整 ===')
r = cc.execute('select remark,nick_name,alias,description,extra_buffer from contact where username=?', (LI,)).fetchone()
eb = bytes(r['extra_buffer'])
txt = eb.decode('utf-8', 'ignore')
print('  remark:', r['remark'], '| nick:', r['nick_name'], '| alias:', r['alias'])
print('  extra 可读串:', re.sub(r'[^\u4e00-\u9fffA-Za-z0-9,:/.\-]', ' ', txt)[:300])

print()
print('=== 周雯娟 完整 ===')
r = cc.execute('select remark,nick_name,alias,description,extra_buffer from contact where username=?', (WEN,)).fetchone()
print('  remark:', r['remark'], '| nick:', r['nick_name'], '| alias:', r['alias'])
eb = bytes(r['extra_buffer'])
print('  extra len:', len(eb), '| 可读:', re.sub(r'[^\u4e00-\u9fffA-Za-z0-9,:/.\-]', ' ', eb.decode('utf-8', 'ignore'))[:300])

print()
print('=== 朋友圈导出 JSON (9-22) ===')
p = r'C:\Users\wardc\Desktop\07_聊天记录分析\weflow_extract\sns_export\朋友圈导出_2026-09-22T05-52-11.json'
if os.path.exists(p):
    j = json.load(io.open(p, encoding='utf-8'))
    print('  type:', type(j).__name__, '| len:', len(j) if hasattr(j, '__len__') else '-')
    print('  raw head:', json.dumps(j, ensure_ascii=False)[:900])

print()
print('=== 大导出 JSON 是否含 李博文/周雯娟/环球 ===')
p2 = r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\朋友圈\朋友圈导出_2026-07-23T20-36-32.json'
if os.path.exists(p2):
    raw = io.open(p2, encoding='utf-8', errors='ignore').read()
    print('  size', len(raw))
    for kw in ('李博文', '周雯娟', 'bownbown', 'sora4811', '环球'):
        print('   %-8s -> %d' % (kw, raw.count(kw)))
    j = json.loads(raw)
    print('  entries:', len(j) if hasattr(j, '__len__') else '?')
    if isinstance(j, list) and j:
        print('  sample keys:', list(j[0].keys()))
        print('  sample:', json.dumps(j[0], ensure_ascii=False)[:400])

print()
print('=== SnsTimeLine 我本人帖子 ===')
sc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'sns', 'sns.db').replace('\\', '/'), uri=True)
sc.row_factory = sqlite3.Row
mine = list(sc.execute('select tid,user_name,content from SnsTimeLine where user_name=?', (ME,)))
print('  count:', len(mine))
for r in sorted(mine, key=lambda x: ((x['tid'] % M) >> 23))[-6:]:
    print('  ', fmt(((r['tid'] % M) >> 23) / 1000), (r['content'] or '')[:120].replace('\n', ' '))
print()
print('=== SnsTimeLine 全部 304 条里，最新 12 条（不论谁） ===')
allr = sorted(list(sc.execute('select tid,user_name,content from SnsTimeLine')), key=lambda x: ((x['tid'] % M) >> 23))
for r in allr[-12:]:
    c = (r['content'] or '')
    m = re.search(r'<username>(.*?)</username>', c)
    d = re.search(r'<contentDesc>(.*?)</contentDesc>', c, re.S)
    print('  %s | %-24s | %s' % (fmt(((r['tid'] % M) >> 23) / 1000), (m.group(1) if m else r['user_name']), (d.group(1)[:60].replace('\n', ' ') if d else '')))
