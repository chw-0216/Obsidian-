# -*- coding: utf-8 -*-
"""合并探查：把要写进报告/引擎的剩余数字一次取全。"""
import datetime
import os
import re
import sqlite3
from collections import Counter

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
ME = "wxid_zn4ozsnn8esr21"


def conn(rel):
    return sqlite3.connect(f"file:{os.path.join(D, rel.replace('/', os.sep))}?mode=ro", uri=True)


def d(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d") if t else "-"


print("=" * 78)
print("A. 收藏 favorite.db —— 全表 + 按类型 + 时间范围")
print("=" * 78)
c = conn("favorite/favorite.db")
tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
print("  表:", tabs)
for t in tabs:
    n = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f"   {t:<28} {n} 行")
cols = [r[1] for r in c.execute("PRAGMA table_info(fav_db_item)")]
print("  fav_db_item 列:", cols)
tc = Counter()
for (ty,) in c.execute("SELECT type FROM fav_db_item"):
    tc[ty] += 1
names = {1: "文本/链接", 2: "图片", 3: "语音", 4: "视频", 5: "文章", 6: "位置", 7: "音乐", 8: "文件", 14: "小程序", 18: "?", 19: "?"}
print("  类型分布:", [(f"{k}={names.get(k,'?')}", v) for k, v in sorted(tc.items(), key=lambda x: -x[1])])
times = [t for (t,) in c.execute("SELECT update_time FROM fav_db_item") if t]
print(f"  时间范围: {d(min(times))} ~ {d(max(times))}  (n={len(times)})")
c.close()

print()
print("=" * 78)
print("B. 转账 transferTable / 红包 redEnvelopeTable —— 聚合")
print("=" * 78)
c = conn("general/general.db")
n = c.execute("SELECT COUNT(*) FROM transferTable").fetchone()[0]
print(f"  转账 {n} 笔")
rows = c.execute("SELECT session_name,pay_payer,pay_receiver,begin_transfer_time FROM transferTable ORDER BY begin_transfer_time").fetchall()
for sn, pp, pr, ts in rows[:20]:
    who = "我转出" if pp and ME in str(pp) else ("我收到" if pr and ME in str(pr) else "?")
    print(f"   {d(ts)}  {who:<6} 会话={str(sn)[:30]}")
n = c.execute("SELECT COUNT(*) FROM redEnvelopeTable").fetchone()[0]
print(f"\n  红包 {n} 个")
for sn, sd, st, ty in c.execute("SELECT session_name,sender_user_name,hb_status,hb_type FROM redEnvelopeTable"):
    who = "我发的" if ME in str(sd) else "别人发的"
    print(f"   {who:<6} 会话={str(sn)[:30]} status={st} type={ty}")
print("\n  搜索历史全部:")
for k, t in c.execute("SELECT query,last_click_time FROM SearchRecent ORDER BY last_click_time DESC"):
    print(f"   {d(t)}  {k!r}")
c.close()

print()
print("=" * 78)
print("C. 文件 hardlink —— 扩展名分布")
print("=" * 78)
c = conn("hardlink/hardlink.db")
ext = Counter()
for (fn,) in c.execute("SELECT file_name FROM file_hardlink_info_v4"):
    e = os.path.splitext(str(fn))[1].lower() or "(无)"
    ext[e] += 1
for e, k in ext.most_common(20):
    print(f"   {e:<12} {k}")
c.close()

print()
print("=" * 78)
print("D. 会话 session.db —— 未读 TOP + 总数")
print("=" * 78)
c = conn("session/session.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(SessionTable)")]
print("  SessionTable 列:", cols)
tot = c.execute("SELECT SUM(unread_count) FROM SessionTable").fetchone()[0]
print(f"  未读合计 {tot}")
for r in c.execute("SELECT username,unread_count,last_timestamp FROM SessionTable ORDER BY unread_count DESC LIMIT 12"):
    print(f"   {str(r[0])[:34]:<34} 未读={r[1]:>6}  最后={d(r[2])}")
c.close()
