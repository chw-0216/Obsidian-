# -*- coding: utf-8 -*-
"""从全量表 CSV 生成 人读清单 MD + 给 Codex 的说明"""
import os, csv, datetime, collections

OUT = r"C:\Users\wardc\Desktop\井邻_制版打印链_文件包_2026-10-06"
CSVP = os.path.join(OUT, "00_文件记录_全量表.csv")

rows = list(csv.DictReader(open(CSVP, encoding="utf-8-sig")))
for r in rows:
    r["大小"] = int(r["大小"])

def rsize(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

# 顶层目录 -> 订单批次 / 说明
tops = collections.OrderedDict()
for r in rows:
    t = r["包内相对路径"].split("/")[0]
    tops.setdefault(t, {"order": r["订单批次"], "note": r["说明"], "files": [], "size": 0})
    tops[t]["files"].append(r)
    tops[t]["size"] += r["大小"]

ORDER_TITLE = {
    "01_订单1_0724_MBTI八版首批出片": "订单 1 ｜ 2026-07-24 首批出片（MBTI 八版制版系统）",
    "02_订单2_0819_偏移四型CMYK四色": "订单 2 ｜ 2026-08-19 偏移四型 CMYK 四色（梁区长到访前夜）",
    "03_订单3_0829_黄版群青版": "订单 3 ｜ 2026-08-29 黄版 / 群青版",
    "04_订单4_1002_五图晒版正片": "订单 4 ｜ 2026-10-02 五图晒版正片（10/3 周六视察前夜）",
    "05_飞鸟两帧_孔版与纸片_v20": "现场体验 ｜ 飞鸟两帧孔版与纸片（v20）",
    "06_飞鸟_最新主视觉_v21": "最新主视觉 ｜ 飞鸟木刻语言（v21）",
    "07_工作站标识分版": "工作站标识分版",
    "08_周六视察_六块版交接包": "周六视察 · 六块版交接包",
    "09_悲鸿与历史分版汇总": "悲鸿与历史分版汇总（全部历史参考）",
}

L = []
L.append("# 井邻 · 接待前「制版—打印」链　文件包记录总表")
L.append("")
L.append(f"- 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
L.append(f"- 包内路径：`{OUT}`")
L.append(f"- 文件总数：**{len(rows)}** 个　｜　总大小：**{rsize(sum(r['大小'] for r in rows))}**")
L.append("- 机读全量表：`00_文件记录_全量表.csv`（含每个文件的 MD5、大小、修改时间）")
L.append("- 源位置：桌面 `05_井邻项目_视觉与丝网印刷\\` ＋ `Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\`")
L.append("")
L.append("---")
L.append("")
L.append("## 目录级汇总")
L.append("")
L.append("| 顶层目录 | 文件数 | 大小 | 内容 |")
L.append("|---|---:|---:|---|")
for t, v in tops.items():
    L.append(f"| `{t}/` | {len(v['files'])} | {rsize(v['size'])} | {v['note']} |")
L.append(f"| **合计** | **{len(rows)}** | **{rsize(sum(r['大小'] for r in rows))}** | |")
L.append("")
L.append("---")
L.append("")

for t, v in tops.items():
    L.append(f"## {ORDER_TITLE.get(t, t)}")
    L.append("")
    L.append(f"`{t}/`　—　{len(v['files'])} 个文件　{rsize(v['size'])}　｜　{v['note']}")
    L.append("")
    # 按二级子目录分组
    sub = collections.OrderedDict()
    for r in v["files"]:
        parts = r["包内相对路径"].split("/")
        k = "/".join(parts[1:-1]) if len(parts) > 2 else "(根)"
        sub.setdefault(k, []).append(r)
    for k, fs in sub.items():
        L.append(f"**{k}**")
        L.append("")
        L.append("| 文件名 | 大小 | MD5（前12位） |")
        L.append("|---|---:|---|")
        for r in fs:
            L.append(f"| `{r['文件名']}` | {r['大小可读']} | `{r['MD5'][:12]}` |")
        L.append("")

L.append("---")
L.append("")
L.append("## 未纳入本包的大体积目录（按需再取）")
L.append("")
L.append("| 路径 | 大小 | 说明 |")
L.append("|---|---:|---|")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\五图_A3丝网分版_45x55网框_v33\\` | 51 MB | 五图 A3 分版（45×55 网框规格），v34 的前序版本 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\五图_A4丝网分版_250目_v32\\` | 39 MB | 五图 A4 分版（250 目规格），v34 的前序版本 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿YOUNG_共印与栗影_视觉提案_v12\\` | 115 MB | 共印/栗影/布袋/明信片 主视觉 + 取材原图 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿YOUNG_央美乡村美育_学院展陈方案_v10\\` | 28 MB | 学院展陈方案 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿YOUNG_乡村美育_最新视觉方案_v9\\` | 21 MB | 视觉方案 v9 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿YOUNG_亮色丝网_艺术构成_v13\\` | 20 MB | 亮色丝网 v13 |")
L.append("| `C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿YOUNG_字标与真实印制_重做v11\\` | 18 MB | 字标重做 v11 |")
L.append("| `C:\\Users\\wardc\\Desktop\\05_井邻项目_视觉与丝网印刷\\` | 3.3 GB | 分版资产主目录（含大量摄影原片，按需取子目录） |")
L.append("| `C:\\Users\\wardc\\Desktop\\06_井邻项目_宣传申报与合作\\` | 700 MB | 宣传申报与合作材料 |")
L.append("")
L.append("> Codex 输出的**全部 26 个版本目录**见：`C:\\Users\\wardc\\Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\`")
L.append("> 分版总表（原始）：`C:\\Users\\wardc\\Desktop\\导\\分版设计清单与文件位置.md`")
L.append("")

open(os.path.join(OUT, "00_文件记录总表.md"), "w", encoding="utf-8").write("\n".join(L))
print("写入 00_文件记录总表.md，行数", len(L))
