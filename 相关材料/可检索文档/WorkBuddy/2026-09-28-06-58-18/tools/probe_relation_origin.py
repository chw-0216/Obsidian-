# -*- coding: utf-8 -*-
"""
关系获取路径逆推（Relation Origin Reverse-Engineering）
================================================================
回答四个问题：
  ① 我怎么加的（谁先发起 / 通过什么渠道 / 什么时间）
  ② 对方是什么人
  ③ 当时对我有什么价值
  ④ 之后对我有什么价值

数据依据：
  · 微信 system 消息：「你已添加了X」= 我加他 ｜「X已添加你」= 他加我 ｜「你已通过X的好友验证」= 我通过
  · 会话首条消息的 role / content（打招呼内容常含渠道线索）
  · 添加时间 → 映射人生阶段
  · 消息量 / 跨度 / 距今天 → 价值演化
只读索引库。
"""
import sqlite3, csv, os, sys, re, io, collections
from datetime import datetime

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
CONTACTS = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
            r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
            r'\contacts_2026-07-23T20-56-25.csv')
OUT = os.path.join(WS, '_tmp', 'relation_origin.txt')

con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
cur = con.cursor()


def t2s(ts):
    try:
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return '?'


def clean(c):
    return re.sub(r'<[^>]+>', '', c or '').replace('\n', ' ').strip()


# ---------- 通讯录 ----------
ct = {}
with open(CONTACTS, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        u = (r.get('用户名') or '').strip()
        if u:
            ct[u] = r

# ---------- 1. 全库：谁加的谁（system 消息） ----------
PAT_ME_ADD = re.compile(r'^你已添加了(.+?)[，,]')
PAT_HE_ADD = re.compile(r'^(.+?)已添加你')
PAT_ME_PASS = re.compile(r'^你已通过(.+?)的?好友验证')
PAT_HE_PASS = re.compile(r'^(.+?)通过了你的朋友验证')

stats = collections.Counter()
origin = {}      # talker -> (方向, 原文, ts)
for sk, ts, c in cur.execute("select session_key, ts, content from messages where type='system' order by ts asc"):
    if not c:
        continue
    s = clean(c)
    m = PAT_ME_ADD.match(s)
    if m:
        origin.setdefault(sk, ('我加他', s, ts)); continue
    m = PAT_HE_ADD.match(s)
    if m:
        origin.setdefault(sk, ('他加我', s, ts)); continue
    m = PAT_ME_PASS.match(s)
    if m:
        origin.setdefault(sk, ('我通过他', s, ts)); continue
    m = PAT_HE_PASS.match(s)
    if m:
        origin.setdefault(sk, ('他通过我', s, ts)); continue

# 只统计私聊
sess = {}
for t, n, st, mc, f, l in cur.execute('select talker, display_name, session_type, message_count, first_ts, last_ts from sessions'):
    sess[t] = dict(name=n or '', st=st or '', mc=mc or 0, f=f, l=l)

for t, (d, s, ts) in origin.items():
    if sess.get(t, {}).get('st') == '私聊':
        stats[d] += 1

# ---------- 2. 近候选 + L1 详情 ----------
targets = [t for t, s in sess.items() if s['st'] == '私聊' and s['mc'] >= 1000 and s['name'] != '文件传输助手']
targets.sort(key=lambda t: -sess[t]['mc'])

buf = io.StringIO()
buf.write('=' * 78 + '\n')
buf.write('全库私聊「谁加的谁」统计（system 消息口径）\n')
buf.write('=' * 78 + '\n')
for k, v in stats.most_common():
    buf.write(f'  {k:<10} {v:>5}\n')
buf.write(f'  {"(无system消息)":<10} {sum(1 for t,s in sess.items() if s["st"]=="私聊" and t not in origin):>5}\n')
buf.write('\n')

for t in targets:
    s = sess[t]
    c = ct.get(t, {})
    remark = (c.get('备注') or '').strip()
    nick = (c.get('昵称') or '').strip()
    tags = (c.get('标签') or '').strip()
    d, txt, ts = origin.get(t, ('未知', '', s['f']))
    buf.write('=' * 78 + '\n')
    buf.write(f"### {s['name']}   {s['mc']} 条\n")
    buf.write(f"  备注={remark or nick} ｜ 标签={tags} ｜ 地区={c.get('地区','')}\n")
    buf.write(f"  首次 {t2s(s['f'])} → 末次 {t2s(s['l'])} ｜ 起点方向：{d}\n")
    buf.write(f"  system: {txt[:80]}\n")
    buf.write('  --- 最早 10 条 ---\n')
    for ts2, role, ty, cc in cur.execute(
            'select ts, role, type, content from messages where session_key=? order by ts asc limit 10', (t,)):
        buf.write(f"   [{t2s(ts2)}] {role:<6} {ty:<8} {clean(cc)[:120]}\n")
    buf.write('\n')

open(OUT, 'w', encoding='utf-8').write(buf.getvalue())
print('已写', OUT, len(buf.getvalue()), '字符')
print('谁加的谁：', dict(stats))
