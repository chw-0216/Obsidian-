# -*- coding: utf-8 -*-
"""把 filehelper 的新发内容导出到桌面（图片 + 文件 + 视频），并生成清单。"""
import os, re, json, shutil, sqlite3, glob, datetime, csv

DESK = r"C:\Users\wardc\Desktop"
OUT = os.path.join(DESK, "文件传输助手_导出_2026-10-12")
IMG_SRC = os.path.join(DESK, "中期汇报_2026-09", "18_文件传输助手_1012全批次")
MSGFILE = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\file"
MSVIDEO = r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\video"
DEC = os.path.expandvars(r"%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message")
TABLE = "Msg_9e20f478899dc29eb19741386f9343c8"
SINCE = int(datetime.datetime(2026, 9, 1).timestamp())

manifest = []

# ---------- 1. 图片（19 张，从 18_ 复制，保留主题目录） ----------
dst_img = os.path.join(OUT, "01_图片_2026-10-12")
for folder in sorted(os.listdir(IMG_SRC)):
    sp = os.path.join(IMG_SRC, folder)
    if not os.path.isdir(sp):
        continue
    dp = os.path.join(dst_img, folder)
    os.makedirs(dp, exist_ok=True)
    for f in sorted(os.listdir(sp)):
        shutil.copy2(os.path.join(sp, f), os.path.join(dp, f))
        manifest.append({
            "类别": "图片", "时间": "2026-10-12 11:11–11:34", "文件名": f,
            "桌面位置": os.path.relpath(os.path.join(dp, f), OUT),
            "原始来源": "微信缓存 attach/9e20f478899dc29eb19741386f9343c8/2026-10/Img（.dat 解密）",
            "大小": os.path.getsize(os.path.join(dp, f)),
        })

# ---------- 2. 文件（5 份，从 msg/file 复制） ----------
TARGETS = [
    ("两块网版-印出一场行动-知行计划澜沧丝网实践课.pptx", 33770817),
    ("成员信息表_绿墨护未.xlsx", 7252),
    ("支教证明-Movers.docx", 75317),
    ("支教证明-Movers.docx", 75129),
    ("中央美术学院美术馆实习生申请表2025.pdf", 117344),
]
dst_file = os.path.join(OUT, "02_文件_2026-09")
os.makedirs(dst_file, exist_ok=True)
pool = {}
for m in ("2026-09", "2026-10"):
    d = os.path.join(MSGFILE, m)
    if os.path.isdir(d):
        for f in os.listdir(d):
            pool.setdefault((f, os.path.getsize(os.path.join(d, f))), os.path.join(d, f))

used = set()
for i, (title, size) in enumerate(TARGETS, 1):
    src = pool.get((title, size))
    if not src:
        # 放宽：同名同大小带 (n) 后缀
        cand = [v for k, v in pool.items() if k[0].startswith(os.path.splitext(title)[0]) and k[1] == size]
        src = cand[0] if cand else None
    if not src or src in used:
        print("未找到:", title, size); continue
    used.add(src)
    dst = os.path.join(dst_file, f"{i:02d}_{os.path.basename(src)}")
    shutil.copy2(src, dst)
    manifest.append({
        "类别": "文件", "时间": "", "文件名": os.path.basename(src),
        "桌面位置": os.path.relpath(dst, OUT), "原始来源": src,
        "大小": os.path.getsize(dst),
    })

# ---------- 3. 视频（按 aeskey/md5 匹配 msg/video） ----------
def dec(blob, ctype):
    try:
        import zstandard as zstd
        _Z = zstd.ZstdDecompressor()
    except ImportError:
        _Z = None
    if blob is None: return ""
    if isinstance(blob, str): return blob
    raw = bytes(blob)
    if not raw: return ""
    if ctype == 4 and _Z is not None:
        try: return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
        except Exception: pass
    try: return raw.decode("utf-8")
    except Exception:
        if _Z is not None:
            try: return _Z.decompress(raw, max_output_size=1 << 26).decode("utf-8", "replace")
            except Exception: return ""
        return ""

vid_msgs = []
for p in sorted(glob.glob(os.path.join(DEC, "message_*.db"))):
    c = sqlite3.connect(p)
    try:
        cur = c.execute(f"select create_time, message_content, compress_content, WCDB_CT_message_content "
                        f"from {TABLE} where create_time>=? and local_type=43 order by create_time", (SINCE,))
    except sqlite3.OperationalError:
        continue
    for ts, mc, cc, ct in cur:
        s = dec(mc, ct) or dec(cc, 4)
        vid_msgs.append((ts, s))
    c.close()

dst_vid = os.path.join(OUT, "03_视频_2026-09至10")
os.makedirs(dst_vid, exist_ok=True)
vpool = {}
for m in ("2026-09", "2026-10"):
    d = os.path.join(MSVIDEO, m)
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith(".mp4") and "_raw" not in f:
                vpool[f[:-4]] = os.path.join(d, f)

for ts, s in vid_msgs:
    t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    ak = re.search(r'aeskey="([0-9a-f]+)"', s)
    md5 = re.search(r'md5="([0-9a-f]+)"', s)
    src = None
    for key in filter(None, [md5.group(1) if md5 else None, ak.group(1) if ak else None]):
        if key in vpool:
            src = vpool[key]; break
    if src:
        dst = os.path.join(dst_vid, f"{t[:10]}_{t[11:16].replace(':','')}_{os.path.basename(src)}")
        shutil.copy2(src, dst)
        manifest.append({
            "类别": "视频", "时间": t, "文件名": os.path.basename(src),
            "桌面位置": os.path.relpath(dst, OUT), "原始来源": src,
            "大小": os.path.getsize(dst),
        })
    else:
        print("视频未匹配:", t, (md5.group(1) if md5 else ak.group(1) if ak else "?")[:16])

# ---------- 4. 清单 CSV ----------
csvp = os.path.join(OUT, "00_全部文件清单.csv")
with open(csvp, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["类别", "时间", "文件名", "桌面位置", "原始来源", "大小"])
    w.writeheader()
    for r in manifest:
        w.writerow(r)

print(f"\n导出完成：{len(manifest)} 个文件")
from collections import Counter
print("分类:", dict(Counter(r["类别"] for r in manifest)))
print("总大小: %.1f MB" % (sum(r["大小"] for r in manifest) / 1048576))
print("输出目录:", OUT)
for dp, dns, fs in os.walk(OUT):
    lv = dp.replace(OUT, "").count(os.sep)
    if lv <= 1:
        print("  " * lv + os.path.basename(dp) + ("/" if dns else ""), f"({len(fs)})" if fs else "")
