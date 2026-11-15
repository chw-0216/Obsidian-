# -*- coding: utf-8 -*-
"""探查 .hevc 静帧图片：规模 + 能否用文件名/内容 md5 对上消息"""
import os, re, sys, sqlite3, hashlib, datetime, random, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
ROOTS = {
    "原图_HD": r"C:\Users\wardc\Desktop\微信照片_最新\原图_HD",
    "图片": r"C:\Users\wardc\Desktop\微信照片_最新\图片",
    "缩略图": r"C:\Users\wardc\Desktop\微信照片_最新\缩略图",
}

# ---- 1. 规模
print("="*70); print("1. .hevc 规模"); print("="*70)
allh = {}
for k, root in ROOTS.items():
    if not os.path.isdir(root): continue
    n = 0; exts = collections.Counter()
    for dp, ds, fs in os.walk(root):
        for fn in fs:
            e = os.path.splitext(fn)[1].lower()
            exts[e] += 1
            if e == ".hevc":
                n += 1
                allh[fn] = os.path.join(dp, fn)
    print("  %-8s hevc=%-6d 全部扩展名: %s" % (k, n, dict(exts.most_common(8))))

print("\n  .hevc 合计:", len(allh))

# ---- 2. 建消息 md5 索引
print("\n" + "="*70); print("2. 建消息 md5 索引（含 originsourcemd5 / md5 / cdnthumbmd5 等）"); print("="*70)
con = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
idx = collections.defaultdict(list)
pats = [r'md5="([0-9a-f]{32})"', r'originsourcemd5="([0-9a-f]{32})"',
        r'cdnthumbmd5="([0-9a-f]{32})"', r'thumbmd5="([0-9a-f]{32})"']
nmsg = 0
for ts, sk, role, content in con.execute("select ts,session_key,role,content from messages where type='image'"):
    nmsg += 1
    for p in pats:
        for h in re.findall(p, content or ""):
            idx[h].append((ts, sk, role))
con.close()
print("  图片消息 %d 条 → md5 键 %d 个" % (nmsg, len(idx)))

# ---- 3. 命中率测试：文件名 md5
print("\n" + "="*70); print("3. 命中率：.hevc 文件名（去 _1 后缀）当作 md5"); print("="*70)
keys = list(allh.keys())
random.seed(7)
samp = random.sample(keys, min(800, len(keys)))
hit = 0; hitfiles = []
for fn in samp:
    stem = os.path.splitext(fn)[0]
    stem = re.sub(r"_\d+$", "", stem)
    if stem in idx:
        hit += 1; hitfiles.append(fn)
print("  抽样 %d ｜ 命中 %d（%.1f%%）" % (len(samp), hit, 100.0*hit/len(samp)))
for fn in hitfiles[:6]:
    stem = re.sub(r"_\d+$", "", os.path.splitext(fn)[0])
    ts, sk, role = sorted(idx[stem])[0]
    print("    %s → %s | %s | %s" % (fn[:36], datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"), sk[:22], role))

# ---- 4. 内容 md5 命中率（抽 60 个）
print("\n" + "="*70); print("4. 命中率：.hevc 文件内容 md5（抽 60）"); print("="*70)
def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1<<20), b""):
            h.update(b)
    return h.hexdigest()
samp2 = random.sample(keys, min(60, len(keys)))
h2 = 0
for fn in samp2:
    try:
        if md5f(allh[fn]) in idx: h2 += 1
    except Exception: pass
print("  抽样 %d ｜ 内容 md5 命中 %d（%.1f%%）" % (len(samp2), h2, 100.0*h2/len(samp2)))

# ---- 5. 按月分布
print("\n" + "="*70); print("5. .hevc 按月分布（原图_HD）"); print("="*70)
cnt = collections.Counter()
for fn, p in allh.items():
    m = re.search(r"(20\d\d-\d\d)", p)
    if m: cnt[m.group(1)] += 1
for k in sorted(cnt): print("  %s  %d" % (k, cnt[k]))
