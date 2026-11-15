# -*- coding: utf-8 -*-
r"""
export_report_pack.py —— 把「央美之后 · 中期汇报」相关产物打成桌面一个包

用户要求：「桌面建立一个文件夹把相关的东西都跑一下理解放进去」

做法（只读源文件 + 复制，不改动任何原始数据）：
  1. 读主文档 HTML（build_report_materials.py 产出），把里面每一张表抽成 CSV（Excel 可直接打开，带 BOM）
  2. 把 A–H 八张表合并成一份《02_候选成果总表_全部.csv》（多一列「线」）
  3. 复制主文档 / 理解层文档 / 汇报草稿到包里
  4. 写 README.md（导航）与 04_原始材料入口.md（指向已有素材目录，不复制 385MB 照片）

产出目录：C:\Users\wardc\Desktop\中期汇报_成果与材料_2026-10-05\
"""
import io
import os
import re
import csv
import html
import shutil
import datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
MAIN_HTML = os.path.join(WS, "央美之后_中期汇报可用成果与材料_2026-10-05.html")
DESK = r"C:\Users\wardc\Desktop"
PACK = os.path.join(DESK, "中期汇报_成果与材料_2026-10-05")
SRC_REPORT_DIR = os.path.join(DESK, "中期汇报_2026-09")

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------------------------------------------------------------- 复制清单
# (源文件, 包内相对目录, 包内文件名)
COPIES = [
    (MAIN_HTML, "01_主文档", None),
    (os.path.join(WS, "自我理解引擎_统一排查台_2026-10-05.html"), "03_理解层", None),
    (os.path.join(WS, "年度事件重建_第二个我_第一轮_2026-10-05.html"), "03_理解层", None),
    (os.path.join(WS, "分析总览_全部文件地图_2026-10-04.html"), "03_理解层", None),
    (os.path.join(WS, "逐日全维整合_2024-11至2026-10_2026-10-04.html"), "03_理解层", None),
    (os.path.join(SRC_REPORT_DIR, "01_汇报正文", "中期汇报_这一年工作总结_草稿.md"), "05_汇报草稿", None),
    (os.path.join(SRC_REPORT_DIR, "00_汇报信息汇总与文件位置.md"), "05_汇报草稿", None),
]


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", " / ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def parse_blocks(txt):
    """按文档顺序返回 [(kind, title, payload)]；kind ∈ {h2, h3, table}"""
    pat = re.compile(r"<(h2|h3)\b[^>]*>(.*?)</\1>|<table\b[^>]*>(.*?)</table>", re.S | re.I)
    out = []
    for m in pat.finditer(txt):
        if m.group(1):
            out.append((m.group(1).lower(), strip_tags(m.group(2)), None))
        else:
            out.append(("table", None, m.group(3)))
    return out


def parse_table(tbl):
    """返回 (headers, rows)"""
    heads = []
    for hm in re.finditer(r"<th\b[^>]*>(.*?)</th>", tbl, re.S | re.I):
        heads.append(strip_tags(hm.group(1)))
    rows = []
    for rm in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", tbl, re.S | re.I):
        cells = [strip_tags(c) for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", rm.group(1), re.S | re.I)]
        if cells and not all(c == "" for c in cells):
            rows.append(cells)
    # 若首行与表头相同则去掉
    if rows and heads and rows[0][:len(heads)] == heads:
        rows = rows[1:]
    return heads, rows


def wcsv(path, heads, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        if heads:
            w.writerow(heads)
        for r in rows:
            w.writerow(r)
    return path


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()[:48]


# 章节 → 干净文件名前缀
H2_NAMES = {
    "一": "01_时间基线",
    "二": "02_候选成果",
    "三": "03_原清单没有的9项",
    "四": "04_今天优先讲的8项",
    "五": "05_素材索引",
    "六": "06_汇报主线四段",
    "七": "07_补充问题",
    "八": "08_口径与限制",
}


def csv_name(h2, h3, t_idx):
    key = h2[:1]
    base = H2_NAMES.get(key, "%02d_%s" % (t_idx, safe(h2)[:18]))
    if not h3:
        return base + ".csv"
    t = h3
    if key == "二":                       # A · 学习与课程（研一） → 02_候选成果_A_学习与课程
        code, _, rest = t.partition("·")
        rest = re.sub(r"（.*?）", "", rest).strip()
        return "%s_%s_%s.csv" % (base, code.strip(), safe(rest))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(.*)$", t)   # 5.1 精选图（…） → 05_素材索引_5.1_精选图
    num, t = (m.group(1), m.group(2)) if m else ("", t)
    t = re.split(r"[：:（(—]|——", t)[0]          # 砍掉冒号 / 括号 / 破折号后面的解释
    t = re.sub(r"[·\s]+", "", t).strip()
    return "%s_%s%s.csv" % (base, (num + "_") if num else "", safe(t)[:20])


def main():
    if not os.path.exists(MAIN_HTML):
        raise SystemExit("找不到主文档：%s" % MAIN_HTML)

    txt = io.open(MAIN_HTML, encoding="utf-8").read()
    blocks = parse_blocks(txt)

    csv_dir = os.path.join(PACK, "02_数据表")
    os.makedirs(csv_dir, exist_ok=True)
    # ★ 不做「先清空再写」—— 批量删除会触发本机的安全删除闸门。
    #   文件名是确定性的，直接覆盖即可；万一改了命名方案，手工清一次旧文件。
    before = set(f for f in os.listdir(csv_dir) if f.lower().endswith(".csv"))

    h2 = ""
    h3 = ""
    t_idx = 0
    written = []
    line_tables = []          # A–H 的八张表 → 合并
    for kind, title, payload in blocks:
        if kind == "h2":
            h2, h3 = title, ""
        elif kind == "h3":
            h3 = title
        else:
            t_idx += 1
            heads, rows = parse_table(payload)
            if not rows:
                continue
            sec = h2.split("、")[0] if "、" in h2 else h2[:6]
            tag = safe(h3) if h3 else ("表%d" % t_idx)
            fn = csv_name(h2, h3, t_idx)
            wcsv(os.path.join(csv_dir, fn), heads, rows)
            written.append((fn, len(rows)))
            if h2.startswith("二") and h3:
                line_tables.append((h3, heads, rows))

    # ---- 合并：候选成果总表 ----
    merged = os.path.join(csv_dir, "02_候选成果总表_全部.csv")
    n_all = 0
    with io.open(merged, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["线", "日期", "事项", "个人贡献", "具体产物", "状态", "备注"])
        for line_name, heads, rows in line_tables:
            for r in rows:
                r = (r + [""] * 6)[:6]
                w.writerow([line_name] + r)
                n_all += 1
    written.append(("02_候选成果总表_全部.csv", n_all))

    # 旧命名残留提醒（不自动删 —— 交给用户或 tools\recycle.py 走回收站）
    stale = sorted(before - set(fn for fn, _ in written))
    if stale:
        print("  ⚠️ 发现 %d 个旧文件（未删除，请自行处理）：%s" % (len(stale), "、".join(stale)))

    # ---- 复制文件 ----
    copied = []
    for src, sub, rename in COPIES:
        if not os.path.exists(src):
            print("  [跳过·不存在] %s" % src)
            continue
        d = os.path.join(PACK, sub)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, rename or os.path.basename(src))
        shutil.copy2(src, dst)
        copied.append((sub, os.path.basename(dst), os.path.getsize(dst)))

    # ---- 04 原始材料入口 ----
    entry = u"""# 原始材料入口（不复制，直接去这些目录取）

> 本包只装「结论 + 数据表 + 理解层文档」。原始素材体量大（照片 385 MB / 1,127 个文件），
> 原地保留，从这里点进去取。

## 一、中期汇报素材总库

`{src}`

| 子目录 | 内容 |
|---|---|
| `01_汇报正文\\` | 中期汇报草稿（这一年工作总结） |
| `02_材料汇总\\` | 版画学习 · 井邻领导接待等汇总 |
| `03_PPT设计\\` | PPT 版式与设计稿 |
| `04_聊天记录数据\\` | 汇报引用的聊天数据 |
| `06_PPT成品\\` | 已完成的 PPT |
| `07_照片素材\\` | **986 张**，已按 10 个主题分类（工作站现场 341 张最多） |
| `09_PPT用图\\` | **33 张语义命名精选图** —— 做 PPT 优先用这批 |
| `10_待补材料\\` | 待补材料（⚠️ `A_厦门集美学院授课\\` 目前是空文件夹） |
| `11_档案材料\\` | 证明 / 档案扫描 |
| `12_聊天分析成果\\` | 聊天分析产出 |
| `13_数字人_知津涅槃\\` | 数字人项目的评审与汇报口径 |

## 二、精选图直接点名（做 PPT 用）

`{src}\\09_PPT用图\\`

| 编号 | 用途 |
|---|---|
| `01_封面_与领导共同印制` | 封面 / 工作站那一页的主图 |
| `02_接待_领导观摩丝网` · `03–06_书记到访_*` | 8 批次接待 |
| `10–17_支教_*` | 澜沧支教（课堂 / 合影 / 证书 / 横幅） |
| `20–26_亚当斯密_*` · `25/26_大使馆电影季_*` | 校友会 / 学术活动 |
| `30–32_论坛_*` | 学术研讨会会务 |
| `40–42_开街_*` | 两次开街 |
| `50–52_木版 / 石版_*` | 技法课作品 |
| `60_厦门版画实验_1~3` | **厦门集美授课（新发现，唯一的现场照）** |

## 三、作品与工程

- `C:\\Users\\wardc\\Documents\\New project gpt\\AI-archive\\outputs\\` —— 悲鸿 YOUNG 视觉体系 v5 → v35+、机器身体、掌间乐章、layered-witness 等
- `C:\\Users\\wardc\\Documents\\New project gpt\\AI-archive\\apps\\` —— gesture-synth / handscore / hyper3d-cli / Live-Body-XRay 等自建工程
- `C:\\Users\\wardc\\Documents\\Obsidian Vault\\01_个人信息\\项目\\` —— 12 份项目笔记（最完整的项目叙事）

## 四、隐私提醒

本包与上述素材**含真人姓名、机构名、未公开材料**，仅本地使用，**不得外传**。
""".format(src=SRC_REPORT_DIR)
    io.open(os.path.join(PACK, "04_原始材料入口.md"), "w", encoding="utf-8").write(entry)

    # ---- README ----
    lines = [
        u"# 中期汇报 · 成果与材料包",
        u"",
        u"> 生成 %s ｜ 来源工作区 `%s`" % (NOW, WS),
        u"> 内容 = 「考上央美之后做过什么」的**主动搜集结果** + 支撑它的**理解层文档**。",
        u"",
        u"## 先看这个",
        u"",
        u"0. **`01_主文档\\汇报清单_首版_2026-10-06.html`** ★ —— **决定讲什么、按什么顺序讲、哪些还不能讲**。"
        u"含增量对照、%d 项成果分 8 条线、今日优先讲 8 项、待核实 / 明确排除 / 口径红线、素材索引、主线四段（附可直接念的讲述文字）、未完成队列。**先看这份。**" % n_all,
        u"1. **`01_主文档\\央美之后_中期汇报可用成果与材料_2026-10-05.html`** —— 八节，含候选成果总表 %d 项、今日优先讲 8 项、素材索引、汇报主线、5 个补充问题。**浏览器打开。**" % n_all,
        u"2. **`02_数据表\\02_候选成果总表_全部.csv`** —— %d 项拉平成一张表，Excel 可直接排序筛选。" % n_all,
        u"3. **`05_汇报草稿\\`** —— 已有的中期汇报草稿（对照用）。",
        u"",
        u"> 注：《汇报清单（首版）》与 `03_理解层\\执行报告_全量经历重建.html` 由统一管线**后置打戳**生成，"
        u"所以它们排在本 README 生成之后 —— 重跑管线会自动同步进本包。",
        u"",
        u"## 目录",
        u"",
        u"| 目录 | 放什么 |",
        u"|---|---|",
        u"| `01_主文档\\` | 本次搜集的**主交付文档**（HTML，八节） |",
        u"| `02_数据表\\` | 主文档里每一张表抽成的 **CSV**（带 BOM，Excel 中文不乱码） |",
        u"| `03_理解层\\` | 这些结论**从哪来的** —— 统一排查台 / 年度事件重建 / 分析总览 / 逐日全维 / **全量经历重建执行报告** |",
        u"| `04_原始材料入口.md` | 照片、作品、项目笔记在**哪里**（不复制，直接去取） |",
        u"| `05_汇报草稿\\` | 已有的汇报草稿与信息汇总（对照本包用） |",
        u"",
        u"## 02_数据表 里有什么",
        u"",
        u"| 文件 | 行数 |",
        u"|---|---|",
    ]
    for fn, n in written:
        lines.append(u"| `%s` | %d |" % (fn, n))
    lines += [
        u"",
        u"## 03_理解层 里有什么（「结论从哪来」）",
        u"",
        u"| 文件 | 作用 |",
        u"|---|---|",
        u"| `自我理解引擎_统一排查台_2026-10-05.html` | 本轮全部结果的合订本：已裁决结论 · 数据表全集 · 结论台账 61 条 · 遗留问题 · 红线速查 |",
        u"| `年度事件重建_第二个我_第一轮_2026-10-05.html` | 8 条生活线 × 13 个月骨架 · 178 条缺口候选 · 8 月逐日对齐 · 独处时段 |",
        u"| `分析总览_全部文件地图_2026-10-04.html` | 所有产物 / 数据表 / 引擎文件的总索引 |",
        u"| `逐日全维整合_2024-11至2026-10_2026-10-04.html` | 699 天 × 26 列逐日主表 |",
        u"",
        u"## 口径提醒（写进汇报前必读）",
        u"",
        u"- **已有事实 / 研究解释 / 未来计划要分开写**。本包总表里的都是已有事实。",
        u"- **不要把组织活动的整体成果都归到自己名下** —— 工作站 / 澜沧 / 研讨会都是团队项目。",
        u"- **数字人口径**：数据层完成 / 架构层设想 / **成品层未交付**。",
        u"- **北京台**只写自己负责的环节；**澜沧**写「澜沧第三民族中学」，课时 4 课次，问题闭环 8 项（7 已解决 + 1 跟进中）。",
        u"- **导师红线（2026-08-05）**：「井邻优惠不能写出来」—— 井邻的商业信息不进汇报。",
        u"",
        u"## 待你补的 5 个问题（详见主文档第七节）",
        u"",
        u"1. 厦门那条线去的到底是哪所学校 / 机构？上了什么课、几课时、几个学生？",
        u"2. 开题题目定了吗？中期汇报要不要交代与开题目标的关系？",
        u"3. 澜沧 35 份问卷的前后测结果出来了吗？有没有 1–2 个学生原话？",
        u"4. 工作站里哪三件事是你个人独立决定 / 完成的？",
        u"5. 汇报的日期、场地、时长确认了吗？导师有没有给过具体要求？",
        u"",
        u"---",
        u"",
        u"**不得外传**：含真人姓名、机构、未公开材料，仅本地使用。",
    ]
    io.open(os.path.join(PACK, "README.md"), "w", encoding="utf-8").write("\n".join(lines))

    # ---- 汇总 ----
    print("=" * 66)
    print("包目录 → %s" % PACK)
    print("=" * 66)
    print("CSV %d 份（含合并总表）" % len(written))
    for fn, n in written:
        print("   %-46s %3d 行" % (fn, n))
    print("复制文件 %d 份" % len(copied))
    for sub, fn, sz in copied:
        print("   %-12s %-52s %8.1f KB" % (sub, fn, sz / 1024))
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(PACK) for f in fs)
    print("包内合计 %.1f MB" % (total / 1024 / 1024))


if __name__ == "__main__":
    main()
