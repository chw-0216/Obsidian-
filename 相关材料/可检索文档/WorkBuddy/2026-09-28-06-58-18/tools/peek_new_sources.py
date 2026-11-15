# -*- coding: utf-8 -*-
"""探矿：favorite（收藏）/ sns（朋友圈）/ session（草稿·未读）里到底有什么。"""
import os
import re
import sqlite3

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"


def decode_content(b):
    """收藏/朋友圈的 content 是 zstd 或 protobuf，尽力取出可读片段"""
    if b is None:
        return ""
    if isinstance(b, str):
        return b
    raw = bytes(b)
    try:
        import zstandard as zstd
        raw = zstd.ZstdDecompressor().decompress(raw, max_output_size=1 << 22)
    except Exception:
        pass
    try:
        s = raw.decode("utf-8")
    except Exception:
        s = raw.decode("utf-8", "ignore")
    return s


def texts(s, n=3, w=110):
    out = re.findall(r"[\u4e00-\u9fff][\u4e00-\u9fff\w\s，。！？、：；""''（）\-—·…]{6,}", s)
    seen, res = set(), []
    for t in out:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            res.append(t[:w])
        if len(res) >= n:
            break
    return res


print("=" * 78)
print("A. 微信收藏 favorite.db —— 230 条")
print("=" * 78)
p = os.path.join(D, "favorite", "favorite.db")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
print("  type 分布:", c.execute("SELECT type, COUNT(*) FROM fav_db_item GROUP BY type ORDER BY 2 DESC").fetchall())
print("  标签:", c.execute("SELECT name FROM fav_tag_db_item").fetchall())
for i, (t, ut, src, content) in enumerate(
        c.execute("SELECT type, update_time, source_id, content FROM fav_db_item ORDER BY update_time DESC LIMIT 10"), 1):
    import datetime
    ts = datetime.datetime.fromtimestamp(ut or 0).strftime("%Y-%m-%d")
    got = texts(decode_content(content))
    print(f"  {i:>2}. [{ts}] type={t} src={(src or '')[:26]}")
    for g in got:
        print(f"       · {g}")
c.close()

print()
print("=" * 78)
print("B. 朋友圈 sns.db")
print("=" * 78)
p = os.path.join(D, "sns", "sns.db")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
print("  SnsTimeLine 行数:", c.execute("SELECT COUNT(*) FROM SnsTimeLine").fetchone()[0])
print("  SnsTopItem_1 行数:", c.execute("SELECT COUNT(*) FROM SnsTopItem_1").fetchone()[0])
print("\n  -- SnsTopItem_1 摘要样本（10 条）--")
for un, sm, ct in c.execute("SELECT username, summary, create_time FROM SnsTopItem_1 ORDER BY create_time DESC LIMIT 10"):
    import datetime
    ts = datetime.datetime.fromtimestamp(ct or 0).strftime("%Y-%m-%d")
    print(f"   [{ts}] {(un or '')[:24]:<24} {(sm or '')[:70]}")
print("\n  -- SnsTimeLine 里能解出的文本（5 条）--")
for un, content in c.execute("SELECT user_name, content FROM SnsTimeLine LIMIT 5"):
    got = texts(decode_content(content), n=4)
    print(f"   [{(un or '')[:24]}]")
    for g in got:
        print(f"       · {g}")
c.close()

print()
print("=" * 78)
print("C. 会话 session.db —— 草稿 / 隐藏 / 未读")
print("=" * 78)
p = os.path.join(D, "session", "session.db")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
print("  SessionTable 行数:", c.execute("SELECT COUNT(*) FROM SessionTable").fetchone()[0])
print("  隐藏会话:", c.execute("SELECT COUNT(*) FROM SessionTable WHERE is_hidden=1").fetchone()[0])
d = c.execute("SELECT COUNT(*) FROM SessionTable WHERE draft IS NOT NULL AND draft<>'' AND draft<>x''").fetchone()[0]
print("  带草稿的会话:", d)
if d:
    for u, dr in c.execute("SELECT username, draft FROM SessionTable WHERE draft IS NOT NULL AND draft<>'' AND draft<>x'' LIMIT 10"):
        got = texts(decode_content(dr), n=2)
        print(f"   [{u[:24]}] {' / '.join(got)[:110]}")
print("  未读总数:", c.execute("SELECT SUM(unread_count) FROM SessionTable").fetchone()[0])
print("\n  -- 未读最多的 8 个会话 --")
for u, n, su in c.execute("SELECT username, unread_count, summary FROM SessionTable ORDER BY unread_count DESC LIMIT 8"):
    print(f"   {n:>5} 条  {u[:30]:<30} {(su or '')[:44]}")
c.close()
