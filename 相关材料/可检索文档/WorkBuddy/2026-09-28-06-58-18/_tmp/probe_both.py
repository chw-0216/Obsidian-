# -*- coding: utf-8 -*-
import sqlite3, os, datetime, io, json, glob
base = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
M = 1 << 64
WEN = 'wxid_uhulgmrvfq4a12'
LI = 'wxid_4yurl8wrbi4a22'
def fmt(t):
    try: return datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
    except Exception: return str(t)

ic = sqlite3.connect('file:%s?mode=ro' % IDX, uri=True); ic.row_factory = sqlite3.Row

print('=== 周雯娟 是否出现在任何群 / 任何消息 ===')
n = ic.execute("select count(*) from messages where session_key=?", (WEN,)).fetchone()[0]
print('  私聊消息:', n)
n2 = ic.execute("select count(*) from messages where sender=?", (WEN,)).fetchone()[0]
print('  作为 sender(群内发言):', n2)
n3 = ic.execute("select count(*) from messages where content like ?", ('%'+WEN+'%',)).fetchone()[0]
print('  正文提及 wxid:', n3)
for r in ic.execute("select session_key,count(*) c,min(ts) a,max(ts) b from messages where sender=? group by session_key", (WEN,)):
    print('   群 %s  %d 条  %s .. %s' % (r['session_key'], r['c'], fmt(r['a']), fmt(r['b'])))

print()
print('=== 李博文 是否出现在群 ===')
for r in ic.execute("select session_key,count(*) c,min(ts) a,max(ts) b from messages where sender=? group by session_key order by c desc limit 15", (LI,)):
    sk = r['session_key']
    nm = ic.execute("select display_name from sessions where talker=?", (sk,)).fetchone()
    print('   %-34s %-22s %5d 条  %s .. %s' % (sk, (nm['display_name'] if nm else '')[:20], r['c'], fmt(r['a']), fmt(r['b'])))

print()
print('=== 通讯录：两人的标签 / 详情 ===')
cc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'contact', 'contact.db').replace('\\', '/'), uri=True)
cc.row_factory = sqlite3.Row
for wx in (WEN, LI):
    r = cc.execute('select * from contact where username=?', (wx,)).fetchone()
    if r:
        d = dict(r)
        print('  %s | remark=%s | nick=%s | alias=%s | local_type=%s | flag=%s | desc=%s' % (
            wx, d['remark'], d['nick_name'], d['alias'], d['local_type'], d['flag'], (d['description'] or '')[:60]))
    lab = list(cc.execute('select * from contact_label limit 1'))
    if lab:
        print('  contact_label cols:', [k for k in dict(lab[0]).keys()])
        for l in cc.execute('select * from contact_label where username=?', (wx,)):
            print('     label:', dict(l))

print()
print('=== 朋友圈导出 JSON 结构（9-22 小文件）===')
p = r'C:\Users\wardc\Desktop\07_聊天记录分析\weflow_extract\sns_export\朋友圈导出_2026-09-22T05-52-11.json'
if os.path.exists(p):
    j = json.load(io.open(p, encoding='utf-8'))
    print('  type:', type(j).__name__, 'len:', len(j) if hasattr(j, '__len__') else '-')
    s = json.dumps(j, ensure_ascii=False)[:1200]
    print('  head:', s)

print()
print('=== SnsTimeLine 里 我本人 发的帖子 ===')
sc = sqlite3.connect('file:%s?mode=ro' % os.path.join(base, 'sns', 'sns.db').replace('\\', '/'), uri=True)
sc.row_factory = sqlite3.Row
ME = 'wxid_zn4ozsnn8esr21'
mine = list(sc.execute('select tid,user_name,content from SnsTimeLine where user_name=?', (ME,)))
print('  count:', len(mine))
for r in sorted(mine, key=lambda x: ((x['tid'] % M) >> 23))[-5:]:
    print('  ', fmt(((r['tid'] % M) >> 23) / 1000), (r['content'] or '')[:150].replace('\n', ' '))
