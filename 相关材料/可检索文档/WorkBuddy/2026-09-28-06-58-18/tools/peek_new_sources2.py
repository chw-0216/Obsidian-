# -*- coding: utf-8 -*-
"""探矿 2：他自己的朋友圈 / 转账记录 / 搜索历史 / 收发文件清单"""
import datetime
import os
import re
import sqlite3

D = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"
ME = "wxid_zn4ozsnn8esr21"


def dec(b):
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
    return raw.decode("utf-8", "ignore")


def txt(s, n=3, w=100):
    out = re.findall(r"[\u4e00-\u9fff][\u4e00-\u9fff\w\s，。！？、：；“”‘’（）\-—·…]{5,}", s)
    r, seen = [], set()
    for t in out:
        t = t.strip()
        if t and t not in seen:
            seen.add(t); r.append(t[:w])
        if len(r) >= n:
            break
    return r


f = lambda t: datetime.datetime.fromtimestamp(t or 0).strftime("%Y-%m-%d") if t else "-"

print("=" * 78)
print("A. 朋友圈里「他自己发的」")
print("=" * 78)
c = sqlite3.connect(f"file:{os.path.join(D,'sns','sns.db')}?mode=ro", uri=True)
rows = c.execute("SELECT user_name, content FROM SnsTimeLine WHERE user_name LIKE ?", (ME + "%",)).fetchall()
print("  他自己发的条数:", len(rows))
for un, ct in rows[:6]:
    got = txt(dec(ct), n=4)
    print(f"   [{un}] {' | '.join(got)[:170]}")
print("\n  朋友圈里出现最多的人（前 12）:")
for un, n in c.execute("SELECT user_name, COUNT(*) FROM SnsTimeLine GROUP BY user_name ORDER BY 2 DESC LIMIT 12"):
    print(f"   {n:>4}  {(un or '')[:34]}")
c.close()

print()
print("=" * 78)
print("B. 转账记录 transferTable")
print("=" * 78)
c = sqlite3.connect(f"file:{os.path.join(D,'general','general.db')}?mode=ro", uri=True)
cols = [r[1] for r in c.execute("PRAGMA table_info(transferTable)")]
print("  列:", cols)
for r in c.execute("SELECT * FROM transferTable LIMIT 6"):
    d = dict(zip(cols, r))
    print(f"   {f(d.get('begin_transfer_time'))}  会话={str(d.get('session_name'))[:26]}  "
          f"payer={str(d.get('pay_payer'))[:24]} receiver={str(d.get('pay_receiver'))[:24]}  sub={d.get('pay_sub_type')}")
print("\n  红包 redEnvelopeTable:")
for r in c.execute("SELECT session_name, sender_user_name, hb_status, hb_type FROM redEnvelopeTable LIMIT 6"):
    print("   ", r)
print("\n  搜索历史 SearchRecent:")
for k, t in c.execute("SELECT query, last_click_time FROM SearchRecent ORDER BY last_click_time DESC LIMIT 12"):
    print(f"   {f(t)}  {k}")
print("\n  好友申请 FMessageTable（前 8）:")
for r in c.execute("SELECT user_name_, timestamp_, content_, is_sender_ FROM FMessageTable ORDER BY timestamp_ DESC LIMIT 8"):
    print(f"   {f(r[1])}  {str(r[0])[:26]:<26} 发={r[3]}  {(dec(r[2]) or '')[:60]}")
c.close()

print()
print("=" * 78)
print("C. 实际收发过的文件（hardlink）")
print("=" * 78)
c = sqlite3.connect(f"file:{os.path.join(D,'hardlink','hardlink.db')}?mode=ro", uri=True)
for t, lab in (("file_hardlink_info_v4", "文件"), ("video_hardlink_info_v4", "视频"), ("image_hardlink_info_v4", "图片")):
    n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {lab}: {n} 个")
print("\n  -- 文件名样本（按修改时间倒序 18 个）--")
for fn, sz, mt in c.execute("SELECT file_name, file_size, modify_time FROM file_hardlink_info_v4 ORDER BY modify_time DESC LIMIT 18"):
    print(f"   {f(mt)}  {(sz or 0)/1024:>9.0f} KB  {str(fn)[:70]}")
c.close()
