# -*- coding: utf-8 -*-
"""把井邻 10-03 素材相关的「字段」全部列出来：
   1) 图片 EXIF / 文件属性字段
   2) 微信 index.sqlite 表结构字段
   3) 微信 .dat 加密头字段
   4) 批次时间对照表 CSV 字段
"""
import os, csv, datetime, sqlite3
from pathlib import Path

try:
    from PIL import Image, ExifTags
    PIL_OK = True
except Exception as e:
    PIL_OK = False
    print("PIL 缺失:", e)

print("#" * 72)
print("# 1. 图片：EXIF 字段 + 文件属性")
print("#" * 72)

DIRS = [
    Path(r"C:\Users\wardc\Desktop\中期汇报_2026-09\14_10-03现场与参与者回声_2026-10-09"),
    Path(r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_jinglin\chenye_1003"),
    Path(r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_jinglin\wumanman_1003"),
]

for d in DIRS:
    print("=" * 72)
    print("###", d)
    if not d.is_dir():
        print("   (不存在)")
        continue
    for f in sorted(d.iterdir()):
        if f.is_dir():
            continue
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        st = f.stat()
        mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print("-" * 64)
        print(f"  {f.name}")
        print(f"    大小 {st.st_size:,} B | 修改时间 {mt}")
        if not PIL_OK:
            continue
        try:
            im = Image.open(f)
            print(f"    尺寸 {im.size} {im.mode} {im.format}")
            ex = im.getexif()
            if ex:
                for k, v in ex.items():
                    print(f"    EXIF {ExifTags.TAGS.get(k, k)} = {str(v)[:80]}")
            else:
                print("    EXIF 空（微信传输已剥离元数据）")
            info = {k: str(v)[:50] for k, v in (im.info or {}).items()}
            if info:
                print(f"    info {info}")
        except Exception as e:
            print("    读取失败:", e)

print()
print("#" * 72)
print("# 2. 微信 index.sqlite 表结构字段")
print("#" * 72)
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
if os.path.exists(DB):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    for name, sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        print("-" * 64)
        print(sql)
    print("-" * 64)
    print("-- 各表实际行数 --")
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM \"{name}\"").fetchone()[0]
            print(f"   {name:<20} {n:,}")
        except Exception as e:
            print(f"   {name:<20} (err {e})")
else:
    print("   不存在:", DB)

print()
print("#" * 72)
print("# 3. 微信 .dat V2 加密头字段（15 字节）")
print("#" * 72)
print("  偏移  长度  字段名        说明")
print("  0-5    6    magic        = 07 08 56 32 08 07")
print("  6-9    4    aes_size     uint32 LE，AES 加密段长度")
print("  10-13  4    xor_size     uint32 LE，XOR 尾段长度")
print("  14     1    reserved     保留位")
print()
print("  密钥派生：AES_KEY = md5( code + wxid )[:16]   （实测 code = 2562432481）")
print("  XOR_KEY = code & 0xFF")
print()
print("  原始 .dat 文件清单：")
for base in ["f0cec7ff81016605a8cefc84c48e0b5b", "f349341f7efaa6679217d8c436e64d91"]:
    d = Path(r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\attach") / base / "2026-10" / "Img"
    print("-" * 64)
    print("  ", base, "->", "存在" if d.is_dir() else "不存在")
    if d.is_dir():
        for f in sorted(d.iterdir()):
            st = f.stat()
            mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M:%S")
            print(f"     {f.name:<44} {st.st_size:>9,} B  {mt}")

print()
print("#" * 72)
print("# 4. 批次时间对照表 CSV 字段")
print("#" * 72)
p = Path(r"C:\Users\wardc\Desktop\井邻_制版打印链_文件包_2026-10-06\00_批次时间对照表.csv")
if p.exists():
    with open(p, encoding="utf-8-sig", errors="ignore") as fh:
        for i, row in enumerate(csv.reader(fh)):
            print("  ", row)
            if i >= 8:
                print("   ...")
                break
else:
    print("   不存在:", p)
