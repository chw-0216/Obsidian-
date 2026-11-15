# -*- coding: utf-8 -*-
"""建「井邻_制版打印链_文件包」：按四次下单组织，复制实体文件 + 生成清单"""
import os, shutil, hashlib, csv, datetime

DESK = r"C:\Users\wardc\Desktop"
CODEX = r"C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs"
S5 = os.path.join(DESK, "05_井邻项目_视觉与丝网印刷")
OUT = os.path.join(DESK, "井邻_制版打印链_文件包_2026-10-06")

# (源绝对路径, 包内相对目录, 订单批次, 用途说明)
PLAN = [
    # 订单 1 —— 2026-07-24 首批出片（MBTI 八版）
    (os.path.join(S5, "位图"), "01_订单1_0724_MBTI八版首批出片/位图", "订单1 / 07-24", "8×POSITIVE-300dpi.bmp + 印刷说明.txt + 文件校验.csv"),
    (os.path.join(S5, "制版"), "01_订单1_0724_MBTI八版首批出片/制版", "订单1 / 07-24", "02-eight-plates 正片 PNG + README + 8版现场操作与套准说明"),
    (os.path.join(S5, "交互文件与主视觉汇总", "视觉_06_MBTI八版制版系统"), "01_订单1_0724_MBTI八版首批出片/视觉_06_MBTI八版制版系统", "订单1 / 07-24", "MBTI 八版制版系统完整源"),
    # 订单 2 —— 2026-08-19 偏移四型 CMYK 四色（梁区长到访前夜）
    (os.path.join(S5, "偏移四型A4满版竖构图_CMYK四色硫酸纸_原Codex主视觉_20260819"),
     "02_订单2_0819_偏移四型CMYK四色/A4满版竖构图", "订单2 / 08-19", "4×CMYK 1200dpi 正片 + 硫酸纸打印与制版说明"),
    (os.path.join(S5, "偏移四型CMYK四色A4硫酸纸分版_原Codex主视觉_20260819"),
     "02_订单2_0819_偏移四型CMYK四色/CMYK四色A4硫酸纸分版", "订单2 / 08-19", "A4 竖向满版四色分版"),
    # 订单 3 —— 2026-08-29 黄版 / 群青版
    (os.path.join(CODEX, "悲鸿为主_分版资料汇总_20260930", "03_其他分版参考", "07_绿墨护未_黄群青实色版"),
     "03_订单3_0829_黄版群青版/绿墨护未_黄群青实色版", "订单3 / 08-29", "黄版/群青版 1:1 PDF+SVG"),
    # 订单 4 —— 2026-10-02 五图晒版正片（10/3 周六视察前夜）
    (os.path.join(CODEX, "五图_晒版正片_A3大图_A4飞鸟_v34"),
     "04_订单4_1002_五图晒版正片/五图_晒版正片_v34", "订单4 / 10-02", "★ 主交付：6页晒版正片 PDF + 正片PNG/TIFF + 印刷店必读 + 制版交接说明 + 制作源.py"),
    (os.path.join(CODEX, "打印店专用_4张A3_2张A4_v35"),
     "04_订单4_1002_五图晒版正片/打印店专用_v35", "订单4 / 10-02", "给打印店的拆分 PDF（A3纵向4页 / A4横向2页）+ 说明"),
    (os.path.join(CODEX, "窗外栗蓬_单色制版_v31"),
     "04_订单4_1002_五图晒版正片/窗外栗蓬_单色制版_v31", "订单4 / 10-02", "栗蓬窗景 单色 1200ppi 正片 + A3 100% PDF"),
    # 现场体验 / 最新主视觉
    (os.path.join(CODEX, "悲鸿YOUNG_飞鸟两帧_新增孔版_v20"),
     "05_飞鸟两帧_孔版与纸片_v20", "现场体验", "两帧黑正片 + 纸片模板PDF + 动画GIF + 现场预览"),
    (os.path.join(CODEX, "悲鸿YOUNG_飞鸟木刻语言_新标修订_v21"),
     "06_飞鸟_最新主视觉_v21", "最新主视觉", "飞鸟主视觉/设计语言/布面应用 + 单帧矢量原稿"),
    # 标识
    (os.path.join(CODEX, "乡村美育工作站_标识文件_20261001"),
     "07_工作站标识分版", "标识", "单色 / 黑字轮廓 / RYB三色+黑字 分色稿"),
    # 视察交接
    (os.path.join(CODEX, "井邻_周六视察与六块版交接_20261003"),
     "08_周六视察_六块版交接包", "交接", "交接文档 docx/pdf + 现场速用卡 + 已有印版 + 校验清单"),
    # 历史分版汇总
    (os.path.join(CODEX, "悲鸿为主_分版资料汇总_20260930"),
     "09_悲鸿与历史分版汇总", "参考", "悲鸿4色 / 工作站橙黑 / 井邻风景 / 偏移四型 / 绿墨护未 全部历史分版"),
]

def md5(p, chunk=1 << 20):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def rsize(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"

os.makedirs(OUT, exist_ok=True)
rows = []
missing = []

for src, rel, order, note in PLAN:
    if not os.path.exists(src):
        missing.append(src)
        print("MISS", src)
        continue
    dst = os.path.join(OUT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print("OK  ", rel)

# 遍历包内所有文件，生成记录
for root, dirs, files in os.walk(OUT):
    dirs.sort(); files.sort()
    for fn in files:
        p = os.path.join(root, fn)
        if os.path.basename(root) == "" :
            pass
        st = os.stat(p)
        rel = os.path.relpath(p, OUT).replace(os.sep, "/")
        top = rel.split("/")[0]
        order = next((o for _, r, o, _ in PLAN if r.split("/")[0] == top), "")
        note = next((n for _, r, o, n in PLAN if r.split("/")[0] == top), "")
        rows.append({
            "包内相对路径": rel,
            "订单批次": order,
            "文件名": fn,
            "大小": st.st_size,
            "大小可读": rsize(st.st_size),
            "修改时间": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "MD5": md5(p),
            "说明": note,
        })

with open(os.path.join(OUT, "00_文件记录_全量表.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print("\n文件总数:", len(rows))
print("总大小:", rsize(sum(r["大小"] for r in rows)))
if missing:
    print("缺失:", missing)
