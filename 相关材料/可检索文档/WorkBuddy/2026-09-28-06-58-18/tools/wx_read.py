# -*- coding: utf-8 -*-
"""微信索引库 · 只读读取器 —— 「五层读法」的执行工具

用法（全部只读，永不写入微信数据）：
    python wx_read.py sessions [--top 50]           # L0 清点：所有会话按条数排序
    python wx_read.py card   <名称或talker>          # L1 会话卡：条数/跨度/双方占比/高频词
    python wx_read.py search <关键词> [--top 60] [--raw]   # L2 检索（默认过滤媒体噪音）
    python wx_read.py timeline <关键词> [--top 200]        # L2 按时间列出命中
    python wx_read.py tail   <名称或talker> [--n 30]       # 看某会话最新 N 条
    python wx_read.py media                                 # 媒体构成统计

铁律：
    * `file:...?mode=ro` 只读打开
    * FTS5 trigram 要求 >=3 字；<3 字自动降级 LIKE
    * 短数字/短词（如 3500）在微信里会被 base64 / aeskey 噪音淹没 —— 默认过滤媒体占位
    * 时间戳 ts 是整数 epoch，SQL 里不要用 strftime() 去比字符串
"""
import argparse
import datetime as dt
import re
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

INDEX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'

# 媒体占位 / 二进制噪音特征
NOISE = re.compile(
    r'<(img|videomsg|voicemsg|emoji|appmsg|sysmsg|revokemsg|location|card|recorditem)\b'
    r'|aeskey|<\\?xml|1 true \d|^\d+ \d+ \d+$'
)


def conn():
    return sqlite3.connect('file:%s?mode=ro' % INDEX.replace('\\', '/'), uri=True)


def t(ts):
    if not ts:
        return '-'
    return dt.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')


def resolve(c, who):
    """把 名称 或 talker 解析成 talker（精确名 > 私聊 > 条数最多）"""
    row = c.execute('select talker from sessions where talker=?', (who,)).fetchone()
    if row:
        return row[0]
    rows = c.execute(
        'select talker, display_name, session_type, message_count from sessions '
        'where display_name = ? order by message_count desc', (who,)
    ).fetchall()
    if not rows:
        rows = c.execute(
            'select talker, display_name, session_type, message_count from sessions '
            'where display_name like ? order by (session_type=\'私聊\') desc, message_count desc',
            ('%' + who + '%',)
        ).fetchall()
    if not rows:
        print('[!] 找不到会话:', who)
        return None
    if len(rows) > 1:
        print('[i] 匹配到多个，取「私聊优先 + 条数最多」：')
        for r in rows[:8]:
            print('    %-30s %-26s %-4s %6d' % (r[0], (r[1] or '')[:24], r[2] or '', r[3]))
    return rows[0][0]


def cmd_sessions(c, a):
    print('会话总数:', c.execute('select count(*) from sessions').fetchone()[0])
    print('消息总数:', c.execute('select count(*) from messages').fetchone()[0])
    print('时间范围: %s → %s' % (
        t(c.execute('select min(ts) from messages').fetchone()[0]),
        t(c.execute('select max(ts) from messages').fetchone()[0])))
    print()
    print('%-30s %-6s %8s  %-16s %-16s' % ('会话', '类型', '条数', '首条', '末条'))
    print('-' * 92)
    for r in c.execute(
            'select display_name, session_type, message_count, first_ts, last_ts '
            'from sessions order by message_count desc limit ?', (a.top,)):
        print('%-30s %-6s %8d  %-16s %-16s' % (
            (r[0] or '?')[:28], r[1] or '', r[2], t(r[3]), t(r[4])))


def cmd_card(c, a):
    k = resolve(c, a.who)
    if not k:
        return
    s = c.execute('select display_name, session_type, message_count, first_ts, last_ts '
                  'from sessions where talker=?', (k,)).fetchone()
    print('=== 会话卡 ===')
    print('talker      :', k)
    print('display_name:', s[0])
    print('type        :', s[1])
    print('messages    :', s[2], '(索引计数)')
    print('span        : %s → %s' % (t(s[3]), t(s[4])))
    print()
    tot = c.execute('select count(*) from messages where session_key=?', (k,)).fetchone()[0]
    print('实际条数    :', tot)
    print('角色占比    :')
    for r in c.execute('select role, count(*) from messages where session_key=? '
                       'group by role order by 2 desc', (k,)):
        print('    %-8s %6d  %5.1f%%' % (r[0], r[1], 100.0 * r[1] / max(tot, 1)))
    print('类型占比    :')
    for r in c.execute('select type, count(*) from messages where session_key=? '
                       'group by type order by 2 desc limit 8', (k,)):
        print('    %-10s %6d' % (r[0], r[1]))
    print('按月分布    :')
    for r in c.execute(
            "select strftime('%Y-%m', ts, 'unixepoch', 'localtime') m, count(*) "
            'from messages where session_key=? group by m order by m desc limit 14', (k,)):
        print('    %s  %6d  %s' % (r[0], r[1], '#' * min(60, r[1] // 10)))


def cmd_search(c, a):
    kw = a.kw
    print('# 关键词: %s   (session=%s)' % (kw, a.session or '全库'))
    hits = []
    if len(kw) >= 3:
        try:
            sql = ('select m.session_key, m.ts, m.role, m.content from messages_fts f '
                   'join messages m on m.id=f.rowid where messages_fts match ?')
            args = [kw]
            if a.session:
                sql += ' and m.session_key=?'
                args.append(resolve(c, a.session))
            sql += ' order by m.ts desc limit ?'
            args.append(a.top * 6 if not a.raw else a.top)
            hits = c.execute(sql, args).fetchall()
            print('[FTS trigram]')
        except Exception as e:
            print('[FTS 失败，降级 LIKE]', e)
    if not hits:
        sql = 'select session_key, ts, role, content from messages where content like ?'
        args = ['%' + kw + '%']
        if a.session:
            sql += ' and session_key=?'
            args.append(resolve(c, a.session))
        sql += ' order by ts desc limit ?'
        args.append(a.top * 6 if not a.raw else a.top)
        hits = c.execute(sql, args).fetchall()
        print('[LIKE]')
    raw_n = len(hits)
    if not a.raw:
        hits = [h for h in hits if not NOISE.search(h[3] or '')]
    print('原始命中 %d → 过滤媒体噪音后 %d，显示前 %d' % (raw_n, len(hits), min(a.top, len(hits))))
    print()
    for k, ts, role, content in hits[:a.top]:
        name = c.execute('select display_name from sessions where talker=?', (k,)).fetchone()
        print('[%s] %-12s %-4s %s' % (t(ts), (name[0] if name else k)[:12], role,
                                      (content or '').replace('\n', ' ')[:90]))


def cmd_timeline(c, a):
    a.raw = getattr(a, 'raw', False)
    cmd_search(c, a)


def cmd_tail(c, a):
    k = resolve(c, a.who)
    if not k:
        return
    rows = c.execute('select ts, role, content from messages where session_key=? '
                     'order by ts desc limit ?', (k, a.n)).fetchall()
    for r in reversed(rows):
        print('[%s] %-4s %s' % (t(r[0]), r[1], (r[2] or '').replace('\n', ' ')[:110]))


def cmd_media(c, a):
    print('按 local type / 占位标签统计全库：')
    for pat, label in [('<img', '图片'), ('<videomsg', '视频'), ('<voicemsg', '语音'),
                       ('<emoji', '表情'), ('<appmsg', '链接/公众号'), ('<sysmsg', '系统'),
                       ('<revokemsg', '撤回'), ('aeskey', '加密媒体占位')]:
        n = c.execute('select count(*) from messages where content like ?', ('%' + pat + '%',)).fetchone()[0]
        print('    %-14s %7d' % (label, n))
    print()
    print('type 字段分布：')
    for r in c.execute('select type, count(*) from messages group by type order by 2 desc limit 15'):
        print('    %-14s %7d' % (r[0], r[1]))


def main():
    p = argparse.ArgumentParser(description='微信索引库只读读取器')
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('sessions'); s.add_argument('--top', type=int, default=50); s.set_defaults(f=cmd_sessions)
    s = sub.add_parser('card'); s.add_argument('who'); s.set_defaults(f=cmd_card)
    s = sub.add_parser('search')
    s.add_argument('kw'); s.add_argument('--top', type=int, default=60)
    s.add_argument('--session', default=None); s.add_argument('--raw', action='store_true')
    s.set_defaults(f=cmd_search)
    s = sub.add_parser('timeline')
    s.add_argument('kw'); s.add_argument('--top', type=int, default=200)
    s.add_argument('--session', default=None); s.add_argument('--raw', action='store_true')
    s.set_defaults(f=cmd_timeline)
    s = sub.add_parser('tail'); s.add_argument('who'); s.add_argument('--n', type=int, default=30); s.set_defaults(f=cmd_tail)
    s = sub.add_parser('media'); s.set_defaults(f=cmd_media)

    a = p.parse_args()
    c = conn()
    a.f(c, a)


if __name__ == '__main__':
    main()
