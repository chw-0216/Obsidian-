# -*- coding: utf-8 -*-
"""精确核验：父母会话唯一性 + 父亲/母亲断点 + 关键人最后一条"""
import sqlite3, time

IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
c = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)

def fmt(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

print("=" * 90)
print("A. display_name 含关键字的全部 session（查是否有重名/多会话）")
print("=" * 90)
for kw in ["刘丽萍", "蔡峰峰", "琢", "养肥", "王博", "笑一", "安奇"]:
    rows = list(c.execute(
        "select talker, display_name, session_type, message_count, first_ts, last_ts "
        "from sessions where display_name like ? order by message_count desc", (f"%{kw}%",)))
    print(f"\n  【{kw}】命中 {len(rows)} 个 session")
    for tk, dn, st, mc, f, l in rows[:6]:
        print(f"    {mc:>6} 条 | {st} | 首={fmt(f) if f else '?'} 末={fmt(l) if l else '?'} | {dn}  [{tk[:28]}]")

print()
print("=" * 90)
print("B. 父亲 / 母亲 · 最后 5 条与时间断层")
print("=" * 90)
for nm in ["蔡峰峰", "刘丽萍"]:
    tk = list(c.execute("select talker from sessions where display_name=? order by message_count desc limit 1", (nm,)))
    if not tk: 
        print(f"  {nm}: 无"); continue
    tk = tk[0][0]
    print(f"\n  【{nm}】session={tk[:40]}")
    for ts, role, ct in c.execute(
        "select ts, role, content from messages where session_key=? order by ts desc limit 5", (tk,)):
        print(f"    末条 {fmt(ts)} [{role}] {(ct or '')[:70]}")
    # 找最大断层
    prev = None; gaps = []
    for (ts,) in c.execute("select ts from messages where session_key=? order by ts", (tk,)):
        if prev and ts - prev > 20 * 86400:
            gaps.append((prev, ts, (ts - prev) / 86400))
        prev = ts
    gaps.sort(key=lambda x: -x[2])
    print(f"    ★ 最大 3 个断层（>20 天）:")
    for a, b, d in gaps[:3]:
        print(f"       {fmt(a)[:10]} → {fmt(b)[:10]}  空 {d:.0f} 天")

print()
print("=" * 90)
print("C. 关键人 · 最后一条消息（谁在什么时候真正停止）")
print("=" * 90)
NAMES = ["陈昶文", "甘泉", "小苹果", "🍬🍬", "Eloise", "沐茜妍", "琢", "养肥", "王博",
         "安奇", "杨丁懿", "子辰", "李紫玥", "汪伊俊", "舒泽林", "Parapluie", "文件传输助手"]
for nm in NAMES:
    r = list(c.execute(
        "select ts, role, content from messages where session_key in "
        "(select talker from sessions where display_name=?) order by ts desc limit 1", (nm,)))
    if r:
        ts, role, ct = r[0]
        print(f"  {nm:<12} 最后 = {fmt(ts)}  [{role}] {(ct or '')[:50]}")
    else:
        print(f"  {nm:<12} 无")
print()
print("ok")
