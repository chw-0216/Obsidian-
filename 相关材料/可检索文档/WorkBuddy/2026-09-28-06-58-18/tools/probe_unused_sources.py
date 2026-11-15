# -*- coding: utf-8 -*-
"""盘点未接入的数据源：朋友圈 / 收藏 / 接龙 / 表情包 / 媒体 / 头像 / 企业微信"""
import sqlite3, os, io

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
TARGETS = {
    'sns/sns.db': '朋友圈',
    'favorite/favorite.db': '收藏',
    'solitaire/solitaire.db': '群接龙',
    'emoticon/emoticon.db': '表情包',
    'message/media_0.db': '媒体资源',
    'message/message_resource.db': '消息资源',
    'message/weclaw.db': 'weclaw',
    'head_image/head_image.db': '头像',
    'hardlink/hardlink.db': '媒体硬链接',
    'bizchat/bizchat.db': '企业微信',
    'general/general.db': '通用设置',
    'contact/contact.db': '通讯录',
    'migrate/unspportmsg.db': '未支持消息',
}

out = io.StringIO()
for rel, label in TARGETS.items():
    p = os.path.join(DEC, rel.replace('/', os.sep))
    if not os.path.exists(p):
        out.write(f'\n### {label}  ({rel})  —— 文件不存在\n')
        continue
    size = os.path.getsize(p) / 1024 / 1024
    out.write(f'\n{"="*76}\n### {label}   {rel}   {size:.1f} MB\n{"="*76}\n')
    try:
        con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
        cur = con.cursor()
        tabs = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
        for t in tabs:
            if t.startswith('sqlite_') or t.endswith(('_fts', '_fts_data', '_fts_idx',
                                                      '_fts_content', '_fts_docsize', '_fts_config')):
                continue
            try:
                n = cur.execute(f'select count(*) from "{t}"').fetchone()[0]
            except Exception:
                n = '?'
            cols = [c[1] for c in cur.execute(f'pragma table_info("{t}")')]
            out.write(f'  [{t}]  {n} 行\n')
            out.write(f'      列: {", ".join(cols[:22])}\n')
        con.close()
    except Exception as e:
        out.write(f'  !! 打不开: {e}\n')

open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\unused_sources.txt',
     'w', encoding='utf-8').write(out.getvalue())
print('ok', len(out.getvalue()))
