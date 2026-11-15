# -*- coding: utf-8 -*-
"""把 18_ 全批次按主题重建归档（保留全部 19 张唯一图）。"""
import os, shutil

BASE = r"C:\Users\wardc\Desktop\中期汇报_2026-09\18_文件传输助手_1012全批次"
SRC = BASE

PLAN = {
    "01_OPC参展方": [
        ("111142_01_hevc_mid_size.png", "01_OPC现场_参展商胸牌_全身.png"),
        ("111146_02_hevc_mid_size.png", "02_OPC现场_参展商胸牌_半身.png"),
    ],
    "02_福州大学厦门工艺美术学院_教学现场": [
        ("111337_03_hevc_mid_size.png", "01_教室_四人围坐_材料台.png"),
        ("111402_04_hevc_mid_size.png", "02_教室_全景_学生作业中.png"),
        ("111406_05_hevc_mid_size.png", "03_教室_另一角度.png"),
    ],
    "03_福州大学厦门工艺美术学院_版画机工作室": [
        ("113031_17_hevc_mid_size.png", "01_版画机工作室_全景_1920x1080.png"),
        ("113038_18_hevc_mid_size.png", "02_版画机工作室_另一角度_1440x648.png"),
    ],
    "04_★校园临时通行证_福州大学厦门工艺美术学院": [
        ("113048_19_hevc_mid_size.png", "01_通行证_蔡浩文_外聘授课_2026-04-20至07-10.png"),
    ],
    "05_木刻材料实验": [
        ("111527_06_hevc_mid_size.png", "01_木刻工作台_刀法练习与红板.png"),
        ("111617_07_hevc_mid_size.png", "02_木刻作品_红黑人物.png"),
        ("111620_08_hevc_mid_size.png", "03_木刻作品_红黑人物_刻板正面.png"),
        ("111639_09_hevc_mid_size.png", "04_木刻印品_龙纹_一.png"),
        ("111646_10_hevc_mid_size.png", "05_木刻印品_龙纹_二.png"),
    ],
    "06_石板材料实验": [
        ("111744_11_hevc_mid_size.png", "01_石版石_两块置于木桌.png"),
        ("111756_12_hevc_mid_size.png", "02_丝网印刷参考截图.png"),
    ],
    "07_四型材料实验": [
        ("111816_13_hevc_mid_size.png", "01_四型_缩略图_原图未完整下载.png"),
    ],
    "08_蜡染材料实验": [
        ("111911_14_hevc_mid_size.png", "01_蜡染_蓝白纹样布.png"),
    ],
    "09_冰醋酸材料实验": [
        ("111938_15_hevc_mid_size.png", "01_作品参考图_流光化石等三件2024.png"),
    ],
    "10_材料实验_展场": [
        ("111947_16_hevc_mid_size.png", "01_工艺展场_宣纸与拓印体验.png"),
    ],
}

moved = 0
for folder, items in PLAN.items():
    d = os.path.join(BASE, folder)
    os.makedirs(d, exist_ok=True)
    for src, dst in items:
        p = os.path.join(SRC, src)
        if os.path.exists(p):
            shutil.move(p, os.path.join(d, dst))
            moved += 1
        else:
            print("缺:", src)

# 重复项：113410 与 113048 同源，单独留档说明
dup = os.path.join(SRC, "113410_20_hevc_mid_size.png")
if os.path.exists(dup):
    d = os.path.join(BASE, "04_★校园临时通行证_福州大学厦门工艺美术学院")
    shutil.move(dup, os.path.join(d, "_重复发送_同一张_113410.png"))
    moved += 1

print("已归档", moved, "个文件")
for dp, dns, fs in os.walk(BASE):
    lv = dp.replace(BASE, "").count(os.sep)
    if lv <= 1:
        print("  " * lv + os.path.basename(dp) + "/", f"({len(fs)} 文件)" if fs else "")
