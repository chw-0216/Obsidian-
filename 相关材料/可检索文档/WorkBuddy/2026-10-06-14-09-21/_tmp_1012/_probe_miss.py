# -*- coding: utf-8 -*-
"""抽查 MISS：这些图在微信缓存里到底有没有对应 .dat？"""
import json, os, re, struct, datetime, collections

ROOT = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach"
JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
CACHE = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\_dat_index.json"

recs = json.load(open(CACHE, encoding="utf-8"))
by_dec = collections.defaultdict(list)
for r in recs:
    by_dec[r["dec"]].append(r)

msgs = json.load(open(JSON_P, encoding="utf-8"))
targets = ["2026-07-05 13:06:58", "2026-07-05 14:02:58", "2026-07-07 20:27:07",
           "2026-08-01 10:46:16", "2026-10-02 19:17:38", "2026-06-12 14:24:53"]

for m in msgs:
    if str(m.get("localType")) != "3":
        continue
    ts = int(m["createTime"])
    dt = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    if dt not in targets:
        continue
    ct = m.get("content") or ""
    gi = lambda k: (re.search(rf'\b{k}="(\d+)"', ct) or [None, None])[1]
    print("=" * 90)
    print(dt, "isSend=", m.get("isSend"))
    print("  md5      =", gi("md5"))
    print("  length   =", gi("length"), " (mid)")
    print("  hdlength =", gi("hdlength"))
    print("  thumblen =", gi("cdnthumblength"))
    print("  tw/th    =", gi("cdnthumbwidth"), "/", gi("cdnthumbheight"))
    print("  aeskey   =", (gi("aeskey") or "")[:16])
    for k, lbl in (("hdlength", "hd"), ("length", "mid"), ("cdnthumblength", "thumb")):
        v = gi(k)
        if v and int(v) > 0:
            hits = by_dec.get(int(v), [])
            print("   按 %-6s(%s) 命中 %d 个 .dat" % (lbl, v, len(hits)))
            for h in hits[:3]:
                print("        %s | %s | %s" % (h["ym"], h["name"], h["conv"][:20]))
