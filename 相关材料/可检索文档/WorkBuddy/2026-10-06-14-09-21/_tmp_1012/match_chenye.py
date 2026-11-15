# -*- coding: utf-8 -*-
"""陈晔会话：654 张图片 → 本地 .dat 全量定位匹配。
原理：XML 的 length / cdnthumblength / hdlength 精确等于本地 .dat 的「解密后字节数」
      (= aes_size + xor_size，即文件大小 − 15 头 − 16 AES 填充)。
"""
import json, os, re, struct, datetime, collections

JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
ATTACH = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach\f349341f7efaa6679217d8c436e64d91"

def dec_size(p):
    """从 .dat 头 15 字节读出解密后字节数"""
    with open(p, "rb") as f:
        h = f.read(15)
    if len(h) < 14 or h[:6] != bytes.fromhex("070856320807"):
        return None
    _, aes_size, xor_size = struct.unpack_from("<6sLL", h)
    return aes_size + xor_size

# ---------- 1. 解析 654 条图片消息 ----------
msgs = json.load(open(JSON_P, encoding="utf-8"))
imgs = []
for m in msgs:
    if str(m.get("localType")) != "3":
        continue
    ct = m.get("content") or ""
    g = lambda k: (re.search(rf'\b{k}="(\d+)"', ct) or [None, None])[1]
    imgs.append({
        "ts": int(m["createTime"]),
        "date": datetime.datetime.fromtimestamp(int(m["createTime"])).strftime("%Y-%m-%d"),
        "ym": datetime.datetime.fromtimestamp(int(m["createTime"])).strftime("%Y-%m"),
        "isSend": str(m.get("isSend")),
        "md5": (re.search(r'\bmd5="([0-9a-f]+)"', ct) or [None, None])[1],
        "aeskey": (re.search(r'\baeskey="([0-9a-f]+)"', ct) or [None, None])[1],
        "length": g("length"),
        "thumblen": g("cdnthumblength"),
        "hdlen": g("hdlength"),
    })
print(f"图片消息: {len(imgs)} 条")

# ---------- 2. 索引本地文件 ----------
files = []          # (path, ym, stem, size, decsize)
for ym in sorted(os.listdir(ATTACH)):
    d = os.path.join(ATTACH, ym, "Img")
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if not f.endswith(".dat"):
            continue
        p = os.path.join(d, f)
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        files.append({"path": p, "ym": ym, "name": f, "stem": f[:-4], "size": sz,
                      "dec": dec_size(p)})
print(f"本地 .dat: {len(files)} 个")

by_stem = {}
by_dec = collections.defaultdict(list)
for r in files:
    by_stem.setdefault(r["stem"], r)
    if r["dec"]:
        by_dec[r["dec"]].append(r)

# ---------- 3. 匹配 ----------
stat = collections.Counter()
hits = []
for m in imgs:
    hit = None
    how = None
    # (a) 文件名 = XML md5
    if m["md5"] and m["md5"] in by_stem:
        hit, how = by_stem[m["md5"]], "md5"
    # (b) 按解密后字节数匹配 length（中图）
    if not hit and m["length"]:
        cands = [r for r in by_dec.get(int(m["length"]), []) if r["ym"] == m["ym"]]
        if cands:
            hit, how = cands[0], "length"
    # (c) 按 cdnthumblength 匹配 _t.dat
    if not hit and m["thumblen"]:
        cands = [r for r in by_dec.get(int(m["thumblen"]), []) if r["ym"] == m["ym"] and r["name"].endswith("_t.dat")]
        if cands:
            hit, how = cands[0], "thumb"
    # (d) 按 hdlength 匹配 _h.dat
    if not hit and m["hdlen"] and int(m["hdlen"]) > 0:
        cands = [r for r in by_dec.get(int(m["hdlen"]), []) if r["ym"] == m["ym"]]
        if cands:
            hit, how = cands[0], "hd"
    m["hit"] = hit
    m["how"] = how
    stat[how or "MISS"] += 1
    if hit:
        hits.append(m)

print()
print("匹配方式统计:", dict(stat))
print(f"命中 {len(hits)} / {len(imgs)} = {len(hits)/len(imgs)*100:.1f}%")
print()
print("按年月命中分布:")
c = collections.Counter((m["ym"], m["how"] or "MISS") for m in imgs)
for k in sorted(c):
    print(f"  {k[0]}  {k[1]:7s} {c[k]}")

# ---------- 4. 存匹配表 ----------
out = []
for m in imgs:
    out.append({
        "时间": datetime.datetime.fromtimestamp(m["ts"]).strftime("%Y-%m-%d %H:%M:%S"),
        "发送方": "我" if m["isSend"] == "1" else "陈晔",
        "md5": m["md5"], "length": m["length"], "thumblen": m["thumblen"], "hdlen": m["hdlen"],
        "匹配方式": m["how"] or "", "本地文件": m["hit"]["path"] if m["hit"] else "",
    })
dst = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\chenye_img_match.json"
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print()
print("匹配表 ->", dst)
