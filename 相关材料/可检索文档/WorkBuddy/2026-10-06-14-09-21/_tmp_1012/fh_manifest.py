# -*- coding: utf-8 -*-
"""重建桌面导出目录的完整清单 CSV。"""
import os, csv, datetime

OUT = r"C:\Users\wardc\Desktop\文件传输助手_导出_2026-10-12"
IMG_ROOT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\18_文件传输助手_1012全批次"

rows = []

# 图片：带消息时间与配文
IMG_META = {
    "01_OPC参展方": ("2026-10-12 11:11", "全球 opc 大会参展方"),
    "02_福州大学厦门工艺美术学院_教学现场": ("2026-10-12 11:13", "福建大学工艺美术学院（口述，实为福州大学厦门工艺美术学院）"),
    "03_福州大学厦门工艺美术学院_版画机工作室": ("2026-10-12 11:30", "（无配文，同批）"),
    "04_★校园临时通行证_福州大学厦门工艺美术学院": ("2026-10-12 11:30 / 11:34", "福州大学工艺美术学院工作证"),
    "05_木刻材料实验": ("2026-10-12 11:15", "木刻材料实验"),
    "06_石板材料实验": ("2026-10-12 11:17", "石板材料实验"),
    "07_四型材料实验": ("2026-10-12 11:18", "四型材料实验"),
    "08_蜡染材料实验": ("2026-10-12 11:19", "蜡染材料实验"),
    "09_冰醋酸材料实验": ("2026-10-12 11:19", "冰醋酸材料实验"),
    "10_材料实验_展场": ("2026-10-12 11:19", "材料实验"),
}

def walk(base, kind, rel_prefix, orig):
    for dp, dns, fs in os.walk(base):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            sub = os.path.relpath(p, OUT) if p.startswith(OUT) else os.path.join(rel_prefix, os.path.relpath(p, base))
            rows.append({"类别": kind, "文件名": f, "桌面相对位置": sub,
                         "大小": os.path.getsize(p), "原始来源": orig, "微信配文／时间": ""})

# 1 图片
for folder in sorted(os.listdir(IMG_ROOT)):
    sp = os.path.join(IMG_ROOT, folder)
    if not os.path.isdir(sp):
        continue
    meta = IMG_META.get(folder, ("", ""))
    for f in sorted(os.listdir(sp)):
        p = os.path.join(sp, f)
        rows.append({"类别": "图片", "文件名": f,
                     "桌面相对位置": os.path.join("01_图片_2026-10-12", folder, f),
                     "大小": os.path.getsize(p),
                     "原始来源": r"微信缓存 …\msg\attach\9e20f478899dc29eb19741386f9343c8\2026-10\Img（.dat 解密）",
                     "微信配文／时间": f"{meta[0]}　{meta[1]}"})

# 2 文件
FMETA = {
    "01_两块网版-印出一场行动-知行计划澜沧丝网实践课.pptx": "2026-09-02 19:01",
    "02_成员信息表_绿墨护未.xlsx": "2026-09-03 17:30",
    "03_支教证明-Movers.docx": "2026-09-03 18:18",
    "04_支教证明-Movers.docx": "2026-09-03 18:49",
    "05_中央美术学院美术馆实习生申请表2025.pdf": "2026-09-15 17:37",
}
d = os.path.join(OUT, "02_文件_2026-09")
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    rows.append({"类别": "文件", "文件名": f, "桌面相对位置": os.path.join("02_文件_2026-09", f),
                 "大小": os.path.getsize(p),
                 "原始来源": r"微信缓存 …\msg\file\2026-09（filehelper 文件消息）",
                 "微信配文／时间": FMETA.get(f, "")})

# 3 视频
d = os.path.join(OUT, "03_视频_2026-09至10")
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    t = f[:15].replace("_", " ")
    rows.append({"类别": "视频", "文件名": f, "桌面相对位置": os.path.join("03_视频_2026-09至10", f),
                 "大小": os.path.getsize(p),
                 "原始来源": r"微信缓存 …\msg\video（filehelper 视频消息，按字节数匹配）",
                 "微信配文／时间": t})

csvp = os.path.join(OUT, "00_全部文件清单.csv")
with open(csvp, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["类别", "文件名", "桌面相对位置", "大小", "原始来源", "微信配文／时间"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

from collections import Counter
c = Counter(r["类别"] for r in rows)
print("清单已生成:", csvp)
print("条目:", len(rows), dict(c))
print("总大小: %.1f MB" % (sum(r["大小"] for r in rows) / 1048576))
