# -*- coding: utf-8 -*-
"""盘点：解密库里「还没被引擎用过」的数据源，看各库有哪些表、多少行。"""
import os
import sqlite3

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"

TARGETS = [
    "favorite/favorite.db",
    "sns/sns.db",
    "session/session.db",
    "emoticon/emoticon.db",
    "general/general.db",
    "hardlink/hardlink.db",
    "message/media_0.db",
    "message/message_resource.db",
    "contact/contact.db",
    "solitaire/solitaire.db",
    "bizchat/bizchat.db",
]

for rel in TARGETS:
    p = os.path.join(D, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print(f"\n### {rel} —— 不存在")
        continue
    print(f"\n### {rel}  ({os.path.getsize(p)/1048576:.1f} MB)")
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        tabs = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in tabs:
            try:
                n = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            except Exception:
                n = "?"
            cols = [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')]
            print(f"   {t:<34} {str(n):>9} 行   [{', '.join(cols[:9])}{'…' if len(cols) > 9 else ''}]")
        c.close()
    except Exception as e:
        print("   打开失败:", e)
