# -*- coding: utf-8 -*-
"""生成「批次时间对照表」：Codex出图 → 利世隆打印 → 小马制版 → 次日现场"""
import os, csv, datetime

OUT = r"C:\Users\wardc\Desktop\井邻_制版打印链_文件包_2026-10-06"

# (批次, 环节, 日期, 时间, 内容, 微信检索)
BATCHES = [
    dict(
        id="A", name="07-24 → 07-25 ｜ 工作站开业（MBTI 八版制版系统）",
        note="★ 一切的原点：首次形成「分版 → 打印 → 制版 → 次日现场」这条链",
        rows=[
            ("分版出图", "2026-07-24", "04:01–07:41", "偏移四型现场预览 04:01 → MBTI 活体原型 06:51 → **制版正片 07:41**", "本地文件夹 mtime"),
            ("分版出图", "2026-07-24", "09:23–09:39", "位图 09:23 → 悲鸿 4 色 09:28 → 井邻风景 09:35", "本地文件夹 mtime"),
            ("出发", "2026-07-24", "08:08", "我→马慧楠「马姐我们已经出发」", "马慧楠 08:08"),
            ("小马 · 到场", "2026-07-24", "09:05", "「马姐我们到了」「在门口」→ 借曝光台 + 烘干箱", "马慧楠 09:05"),
            ("小马 · 引荐打印店", "2026-07-24", "09:52 / 09:54", "连发两个定位：澜花语岸 → **利世隆大图复印**", "马慧楠 09:52"),
            ("利世隆 · 打印", "2026-07-24", "10:06–10:13", "首开户 + 首批出片（250×271mm / 7.6×6.4cm）；金额未记录", "利世隆 10:06"),
            ("小马 · 制版", "2026-07-24", "白天", "完成 **3 块网版**曝光", "马慧楠 09:05–"),
            ("现场", "2026-07-25", "—", "**井邻工作站开业**", "—"),
        ],
        files=["Desktop\\05_井邻项目_视觉与丝网印刷\\制版\\02-eight-plates\\",
               "Desktop\\05_井邻项目_视觉与丝网印刷\\位图\\",
               "Desktop\\05_井邻项目_视觉与丝网印刷\\悲鸿\\",
               "Desktop\\05_井邻项目_视觉与丝网印刷\\交互文件与主视觉汇总\\视觉_06_MBTI八版制版系统\\"],
        pack="01_订单1_0724_MBTI八版首批出片/",
    ),
    dict(
        id="B", name="08-14 → 08-15 ｜ 怀柔区委书记到访",
        note="唯一没有新分版的一次 —— 直接借 7/24 的旧版，技师现场检查重制",
        rows=[
            ("借版", "2026-08-14", "20:48", "我→马慧楠「上次的版有还没洗的吗」「明天用一天我立马给送回来」", "马慧楠 20:48"),
            ("小马 · 回复", "2026-08-14", "20:49", "马慧楠「**有的有的，上回寄回来我还没拆封呢**」→ 约定放门口，次日清早自取", "马慧楠 20:49"),
            ("小马 · 制版", "2026-08-15", "05:30", "马慧楠「把上次的**菲林底片**拿着…让技师帮你看网版还能用么，**不能用就让他给你重新做一下版**」", "马慧楠 05:30"),
            ("到场", "2026-08-15", "05:53", "我「我晚了感谢马姐」", "马慧楠 05:53"),
            ("归还", "2026-08-16", "19:46–19:54", "「马姐在家吗」→「感谢马姐」", "马慧楠 19:46"),
            ("现场", "2026-08-15", "—", "**怀柔区委书记到访**", "—"),
        ],
        files=["（无新分版，沿用 07-24 网版）",
               "照片：工作日志 J18A1922.CR2 ~ J18A1983.CR2（EXIF 2026-08-15 17:53 → 08-16 01:18）"],
        pack="（无独立目录）",
    ),
    dict(
        id="C", name="08-19 → 08-20 ｜ 梁区长 + 北京市文旅局局长到访　★最典型",
        note="★ 从收到通知到制版完成不足 2 小时 35 分钟，全程夜里跑完",
        rows=[
            ("通知", "2026-08-19", "17:52", "群（美育工作站）关宇佳「陈老师，浩文。**明天梁区长和市文旅局局长来**，所有店铺开业」", "群 53074549232 / 17:52"),
            ("通知", "2026-08-19", "18:36 / 18:47", "王华青「提前到九点哈」→ 关宇佳「明天领导提前了 9:00到」", "群 18:36 / 18:47"),
            ("★ 主动请缨", "2026-08-19", "18:41", "我→陈晔「…**今晚要不要先去把版制了，明天直接用**。您看怎么安排」", "陈晔 18:41"),
            ("借板", "2026-08-19", "19:07–19:11", "我→马慧楠「上次那几块板还在吗」「**区长明天上午来**」→ 马「不用费用，没事儿，你过来拿吧，在的」", "马慧楠 19:07"),
            ("分版出图", "2026-08-19", "19:59–20:17", "偏移四型 CMYK 四色 A4 硫酸纸分版 **19:59** → A4 满版竖构图 **20:08–20:17**", "本地文件夹 mtime"),
            ("利世隆 · 发文件", "2026-08-19", "19:50–20:21", "4×CMYK 1200dpi TIF + 4×A4 竖向满版 TIF + 3 PDF；「6 个版每个打两份」", "利世隆 19:50"),
            ("利世隆 · 报价付款", "2026-08-19", "20:22 / 20:28", "高姐「12」→ 发红包 12 元 → 20:29 领取", "利世隆 20:22"),
            ("利世隆 · 取件", "2026-08-19", "21:27", "我「**哥我到了**」「看到了感谢」← 取到硫酸纸", "利世隆 21:27"),
            ("小马 · 制版", "2026-08-19", "21:42–22:24", "我「马姐我刚到」→ 21:47 转 **40 元** → 22:24「**就这个搞定了我撤了老师**」", "马慧楠 21:42"),
            ("途中", "2026-08-20", "06:59", "我「老师我可能晚了点发生了点剐蹭」→ 07:30 陈晔「安全第一」", "陈晔 06:59"),
            ("到岗", "2026-08-20", "08:49", "我「老师我已到达」", "陈晔 08:49"),
            ("现场", "2026-08-20", "09:00", "**梁区长 + 北京市文旅局局长到访**", "—"),
        ],
        files=["Desktop\\05_井邻项目_视觉与丝网印刷\\偏移四型CMYK四色A4硫酸纸分版_原Codex主视觉_20260819\\",
               "Desktop\\05_井邻项目_视觉与丝网印刷\\偏移四型A4满版竖构图_CMYK四色硫酸纸_原Codex主视觉_20260819\\"],
        pack="02_订单2_0819_偏移四型CMYK四色/",
    ),
    dict(
        id="D", name="08-29 ｜ 黄版 / 群青版",
        note="刘丽萍教授直接找马慧楠协调网板 → 说明这条渠道被家庭与项目共同认可",
        rows=[
            ("借版", "2026-08-29", "19:20", "马慧楠「浩文，下午**刘老师给我打电话说你还要拿网板**，还拿么，你今天大概什么时候来工作室？」", "马慧楠 19:20"),
            ("利世隆 · 发文件", "2026-08-29", "19:58–20:42", "黄版 + 群青版 A3→A4 各 2 张（共 4 张）；V2 红/黄双色正片 2 张", "利世隆 19:58"),
            ("利世隆 · 报价付款", "2026-08-29", "20:25 / 20:42", "「8元，红包一下吧」→ 再「6元」；合计 **14 元**", "利世隆 20:25"),
            ("利世隆 · 取件", "2026-08-29", "20:50", "高姐「**放电车里了**」", "利世隆 20:50"),
            ("小马 · 制版", "2026-08-29", "22:13", "我「马老师我错了」← 当晚到场制版", "马慧楠 22:13"),
        ],
        files=["Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿为主_分版资料汇总_20260930\\03_其他分版参考\\07_绿墨护未_黄群青实色版\\"],
        pack="03_订单3_0829_黄版群青版/",
    ),
    dict(
        id="E", name="09-30 → 10-01 ｜ Codex 分版资产大整理（无打印/制版）",
        note="纯整理与重做：把历史分版收拢成册，为 10/3 视察做准备",
        rows=[
            ("整理", "2026-09-30", "17:39–17:41", "悲鸿为主_分版资料汇总_20260930（全部历史分版收拢）", "本地文件夹 mtime"),
            ("方案", "2026-09-30", "20:45", "井邻_整体视觉策划_井邻专版_v3", "本地文件夹 mtime"),
            ("标识分版", "2026-10-01", "04:04–04:08", "乡村美育工作站_标识文件_20261001（单色/黑字/RYB三色+黑）", "本地文件夹 mtime"),
            ("方案", "2026-10-01", "20:35–20:58", "视察准备 v2 / 影像版画 v4 / 单色 v5 / v6 / v7", "本地文件夹 mtime"),
            ("过程稿", "2026-10-01", "21:04–21:22", "过程稿_井邻文旅_单色_v5", "本地文件夹 mtime"),
        ],
        files=["Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\悲鸿为主_分版资料汇总_20260930\\",
               "Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\乡村美育工作站_标识文件_20261001\\"],
        pack="09_悲鸿与历史分版汇总/ ＋ 07_工作站标识分版/",
    ),
    dict(
        id="F", name="10-02 → 10-03 ｜ 周六视察　★主交付",
        note="★ 一整天连轴：凌晨出方案 → 中午起出正片 → 夜里打印 + 制版 → 次日视察",
        rows=[
            ("分版出图（凌晨）", "2026-10-02", "04:43–08:00", "栗林新绘 04:43 → v9 04:52 → v10 04:57 → v11 05:07 → v12 05:25 → v13 05:30 → v15 05:33 → v16 05:40 → v17 05:45 → v18 05:52 → v19 05:59 → v20 06:23 → **v21 06:20–08:00**", "本地文件夹 mtime"),
            ("出片（白天）", "2026-10-02", "11:20–20:43", "v32/v33/v34 开始 11:20 → **v31 窗外栗蓬 19:43** → v32 完成 20:23 → v33 20:39 → **v34 20:43**", "本地文件夹 mtime"),
            ("利世隆 · 联系", "2026-10-02", "20:17–20:20", "「现在能打印吗」→ 高姐「**硫酸纸用完了**」→「我给您买点硫酸纸呢」→「**菲林的打不了**」", "利世隆 20:17"),
            ("利世隆 · 自购纸", "2026-10-02", "20:21–20:43", "外卖下单 **70 余元**硫酸纸加急配送到店（黑钻加急）", "利世隆 20:21"),
            ("利世隆 · 发文件", "2026-10-02", "20:47–20:59", "高姐「机器坏了，打不了」→ 我「哥我都买了 70 多块钱硫酸纸了」→ 发 `01_晒版正片_A3大图_A4飞鸟_6页.pdf`，「4张A3」「两张A4」", "利世隆 20:47"),
            ("打印店专用拆分", "2026-10-02", "21:06", "打印店专用_4张A3_2张A4_v35（A3 纵向 4 页 / A4 横向 2 页）", "本地文件夹 mtime"),
            ("利世隆 · 报价付款", "2026-10-02", "21:09–21:10", "高姐「**A3打印5元一张，A4的3元**」→ 4×5 + 2×3 = **26 元**，发红包", "利世隆 21:09"),
            ("小马 · 制版", "2026-10-02", "当晚", "我→马慧楠 23:43「**感谢马姐**」← 连夜制版", "马慧楠 23:43"),
            ("现场", "2026-10-03", "—", "**周六视察**", "—"),
        ],
        files=["Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\五图_晒版正片_A3大图_A4飞鸟_v34\\",
               "Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\打印店专用_4张A3_2张A4_v35\\",
               "Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\窗外栗蓬_单色制版_v31\\",
               "Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\五图_A3丝网分版_45x55网框_v33\\（未入包 51MB）",
               "Documents\\Codex\\2026-09-30\\new-chat-6\\outputs\\五图_A4丝网分版_250目_v32\\（未入包 39MB）"],
        pack="04_订单4_1002_五图晒版正片/",
    ),
]

# ---------- CSV ----------
csvp = os.path.join(OUT, "00_批次时间对照表.csv")
with open(csvp, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["批次", "批次名称", "环节", "日期", "时间", "内容", "微信检索", "对应文件包目录", "源文件位置"])
    for b in BATCHES:
        for r in b["rows"]:
            w.writerow([b["id"], b["name"], r[0], r[1], r[2], r[3].replace("**", ""), r[4], b["pack"], " ｜ ".join(b["files"])])
print("CSV:", csvp)

# ---------- MD ----------
L = []
L.append("# 井邻 · 批次时间对照表　Codex 出图 → 利世隆打印 → 小马制版 → 次日现场")
L.append("")
L.append(f"- 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
L.append("- 用途：**按日期反查**——某天做了什么、对应哪些文件、去哪段微信里搜")
L.append("- 机读版：`00_批次时间对照表.csv`")
L.append("- 时间来源：① 本地文件 mtime（Codex/分版输出）；② 微信消息时间戳。两者交叉验证")
L.append("")
L.append("## 一图看懂规律")
L.append("")
L.append("```")
L.append("白天/凌晨  Codex 做方案 + 出彩色图片 + 分版")
L.append("     ↓")
L.append("当  夜     利世隆打印硫酸纸正片（多为 19:50–21:30）")
L.append("     ↓")
L.append("同  夜     小马 LEHAUS 借曝光台制版（多为 21:30–23:00）")
L.append("     ↓")
L.append("次  日     带版回洞台村，接待 / 工作坊直接用")
L.append("```")
L.append("")
L.append("---")
L.append("")
for b in BATCHES:
    L.append(f"## 批次 {b['id']}　{b['name']}")
    L.append("")
    L.append(f"> {b['note']}")
    L.append("")
    L.append("| 环节 | 日期 | 时间 | 内容 | 微信检索 |")
    L.append("|---|---|---|---|---|")
    for r in b["rows"]:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` |")
    L.append("")
    L.append(f"**对应文件包目录**：`{b['pack']}`")
    L.append("")
    L.append("**源文件位置**：")
    for fp in b["files"]:
        L.append(f"- `{fp}`")
    L.append("")
    L.append("---")
    L.append("")

L.append("## 微信检索速查（会话 → 关键词）")
L.append("")
L.append("| 会话 | wxid / 标识 | 关键词 |")
L.append("|---|---|---|")
L.append("| 小马 · 马慧楠 LEHAUS | `wxid_8081720817911` | 制版 / 借版 / 曝光台 / 烘干箱 / 菲林底片 / 网板 |")
L.append("| 利世隆大图复印 高姐 | `wxid_hcj7u0b7rbnu12` | 硫酸纸 / 打印 / 红包 / 放门口 / 电动车 |")
L.append("| 陈晔（导师） | `deerluna` | 制版 / 请缨 / 已到达 / 剐蹭 |")
L.append("| 央美美育工作站群 | `53074549232@chatroom` | 领导到访 / 提前 / 视察 |")
L.append("| 索引库 | `C:\\Users\\wardc\\Desktop\\_im_tmp\\wechat-mcp\\index.sqlite` | 全库 391,315 条 |")
L.append("")
open(os.path.join(OUT, "00_批次时间对照表.md"), "w", encoding="utf-8").write("\n".join(L))
print("MD 行数:", len(L))

# ---------- HTML ----------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rich(s):
    s = esc(s)
    while "**" in s:
        s = s.replace("**", "<b>", 1)
        if "**" in s:
            s = s.replace("**", "</b>", 1)
    return s

H = []
H.append('''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>井邻 · 批次时间对照表</title><style>
:root{--ink:#16181d;--ink2:#3c4148;--ink3:#6b7280;--ink4:#9aa1ab;--line:#e3e6ea;--line2:#eef1f4;
--bg:#fff;--bg2:#f7f8fa;--bg3:#f2f4f7;--red:#c0392b;--redbg:#fdf4f3;--redline:#f0d5d1;
--blue:#1f4e79;--bluebg:#f2f6fa;--blueline:#d3e0ec;--green:#1e7a5a;--greenbg:#f1f8f5;--greenline:#cfe6dd;
--amber:#8a5a00;--amberbg:#fdf8ee;--amberline:#ecdcb8;--mono:"SFMono-Regular",Consolas,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg2);color:var(--ink);font-size:14px;line-height:1.75;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.page{max-width:1120px;margin:0 auto;background:var(--bg);box-shadow:0 1px 3px rgba(16,24,40,.06),0 8px 32px rgba(16,24,40,.05)}
.hero{padding:44px 52px 34px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fbfcfd,#fff)}
.kicker{font-size:11.5px;letter-spacing:.22em;color:var(--ink4);font-weight:600}
.hero h1{margin:13px 0 8px;font-size:29px;letter-spacing:-.02em;font-weight:700;line-height:1.3}
.hero h1 em{font-style:normal;color:var(--red)}
.hero .sub{color:var(--ink3);font-size:14px;max-width:820px}
section{padding:34px 52px;border-bottom:1px solid var(--line2)}
h2{font-size:19px;margin:0 0 6px;display:flex;align-items:baseline;gap:10px}
h2 .id{font-family:var(--mono);font-size:12px;background:var(--ink);color:#fff;border-radius:5px;padding:2px 8px}
h2 .id.key{background:var(--red)}
.note{background:var(--bg3);border-left:3px solid var(--ink4);padding:9px 14px;margin:10px 0 18px;
font-size:13px;color:var(--ink2);border-radius:0 6px 6px 0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-weight:600;color:var(--ink3);font-size:11.5px;letter-spacing:.05em;
padding:8px 10px;border-bottom:1.5px solid var(--line);background:var(--bg3);white-space:nowrap}
td{padding:9px 10px;border-bottom:1px solid var(--line2);vertical-align:top}
tr:last-child td{border-bottom:none}
td.t{font-family:var(--mono);font-size:11.5px;color:var(--ink2);white-space:nowrap;font-variant-numeric:tabular-nums}
td.s{font-family:var(--mono);font-size:11.5px;color:var(--ink4);white-space:nowrap}
td.st{font-weight:600;white-space:nowrap;color:var(--ink2)}
tr.hot td{background:var(--redbg)}
tr.hot td.st{color:var(--red)}
.tbl-wrap{border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:16px}
.files{font-size:12px;color:var(--ink3);margin:0 0 4px}
.files code{font-family:var(--mono);font-size:11px;background:var(--bg3);padding:1px 5px;border-radius:3px}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch;margin:8px 0}
.step{flex:1 1 160px;border:1px solid var(--line);border-radius:8px;padding:10px 13px}
.step .n{font-size:10.5px;font-family:var(--mono);color:var(--ink4);letter-spacing:.06em}
.step .t{font-weight:650;font-size:13.5px;margin-top:2px}
.step .d{font-size:11.5px;color:var(--ink3);margin-top:3px}
.step.hot{border-color:var(--redline);background:var(--redbg)}
.ar{align-self:center;color:var(--ink4)}
.foot{padding:22px 52px 36px;color:var(--ink4);font-size:11.5px;background:var(--bg3)}
.foot b{color:var(--ink3)}
@media print{body{background:#fff;font-size:11px}.page{box-shadow:none;max-width:none}
section{padding:16px 0}.tbl-wrap{page-break-inside:avoid}}
@media(max-width:780px){.hero,section,.foot{padding-left:18px;padding-right:18px}}
</style></head><body><div class="page">
<div class="hero"><div class="kicker">洞台村乡村美育工作站 · 井邻章</div>
<h1>批次时间对照表　<em>Codex 出图 → 打印 → 制版</em></h1>
<div class="sub">按日期反查：某天做了什么、对应哪批文件、去哪段微信里搜。时间来自本地文件 mtime 与微信时间戳交叉验证。</div></div>''')

H.append('''<section><h2>规律</h2>
<div class="flow">
<div class="step"><div class="n">STEP 1</div><div class="t">Codex 做方案</div><div class="d">彩色图片 + 分版（白天或凌晨）</div></div>
<div class="ar">→</div>
<div class="step hot"><div class="n">STEP 2</div><div class="t">利世隆打印</div><div class="d">当晚 19:50–21:30 居多</div></div>
<div class="ar">→</div>
<div class="step hot"><div class="n">STEP 3</div><div class="t">小马制版</div><div class="d">同晚 21:30–23:00 居多</div></div>
<div class="ar">→</div>
<div class="step"><div class="n">STEP 4</div><div class="t">次日现场</div><div class="d">带版回洞台村直接用</div></div>
</div></section>''')

for b in BATCHES:
    key = " key" if "★" in b["name"] else ""
    H.append(f'<section><h2><span class="id{key}">{b["id"]}</span>{esc(b["name"].split("｜",1)[1].strip())}</h2>')
    H.append(f'<div class="note">{rich(b["note"])}</div>')
    H.append('<div class="tbl-wrap"><table><thead><tr><th style="width:104px">环节</th><th style="width:88px">日期</th><th style="width:104px">时间</th><th>内容</th><th style="width:150px">微信检索</th></tr></thead><tbody>')
    for r in b["rows"]:
        cls = ' class="hot"' if r[0].startswith("★") else ""
        H.append(f'<tr{cls}><td class="st">{esc(r[0])}</td><td class="t">{r[1][5:]}</td><td class="s">{esc(r[2])}</td><td>{rich(r[3])}</td><td class="s">{esc(r[4])}</td></tr>')
    H.append('</tbody></table></div>')
    H.append(f'<p class="files"><b>文件包目录</b>　<code>{esc(b["pack"])}</code></p>')
    for fp in b["files"]:
        H.append(f'<p class="files">　<code>{esc(fp)}</code></p>')
    H.append('</section>')

H.append('''<div class="foot"><b>数据源</b>　本地文件 mtime ＋ ChatTrace 索引库 <code>index.sqlite</code>（2026-10-06 13:18 更新）<br>
<b>会话</b>　小马 <code>wxid_8081720817911</code> ｜ 利世隆 <code>wxid_hcj7u0b7rbnu12</code> ｜ 陈晔 <code>deerluna</code> ｜ 美育工作站群 <code>53074549232@chatroom</code><br>
<b>生成</b>　2026-10-06　｜　每个时间点都可用文件 mtime 或微信时间戳回查</div>
</div></body></html>''')

hp = os.path.join(OUT, "00_批次时间对照表.html")
open(hp, "w", encoding="utf-8").write("\n".join(H))
print("HTML:", hp, len("".join(H)), "字节")
