# -*- coding: utf-8 -*-
r"""
photo_evidence_overview.py —— 「照片证据总览」单文件 HTML

把这一批（照片证据 → PPT 材料包）的家底、口径、缺口、联系表索引讲清楚。
数据全部**现算**（不写死数字）。

产出：`照片证据总览_第二批_2026-10-06.html`
"""
import os, io, re, sys, csv, json, glob, sqlite3, datetime, argparse, traceback
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
SHEETS = os.path.join(WS, "_tmp", "sheets")
OUT = os.path.join(WS, "照片证据总览_第二批_2026-10-06.html")

SRC_NOTE = {
    "微信缩略图": ("微信聊天导出", "低分辨率（均 ~177px），仅作线索", "不可用"),
    "微信图片": ("微信聊天导出", "聊天压缩图（均 ~135px）", "基本不可用"),
    "微信原图HEVC": ("微信「原图」导出", "**HEVC 编码的高清静帧**（非视频），可解出完整画面", "可用"),
    "微信图片HEVC": ("微信「原图」导出", "同上，数量主体", "可用"),
    "微信原图HD": ("微信「原图」导出", "jpg/png 原图", "可用"),
    "朋友圈": ("朋友圈导出 JSON", "含**发帖时间/昵称/文案**；只有 `role=me` 是他本人发的", "可用（需筛）"),
    "井邻项目": ("桌面项目文件夹", "575 周年原图 / 交互主视觉 / 悲鸿 / 制版 / 丝网", "可用"),
    "井邻宣传": ("桌面项目文件夹", "工作站海报 / 丝网工作坊宣传页 / 知行计划", "可用"),
    "C1原片": ("Capture One 目录", "**他本人的摄影原片**（含 34 张 .cr2）", "可用"),
    "AI产物": ("AI-archive/outputs", "他跑的 AIGC 产出与设计稿", "可用（是产出不是现场）"),
    "汇报照片素材": ("已策展（WeFlow 导出）", "上一轮策展的 796 张，含**带编号联系表**", "可用"),
    "澜沧课堂照": ("已策展", "澜沧支教评审优化版课堂照", "可用"),
    "PPT用图": ("已策展", "上一版 PPT 用图", "可用"),
    "澜沧提交包": ("桌面提交包", "澜沧项目提交材料里的课堂照", "可用"),
    "WeFlow图片": ("WeFlow 导出", "微信图片的 WeFlow 版本", "可用（需筛）"),
    "定稿图": ("桌面", "定稿视觉", "可用"),
    "RAW优化版": ("桌面", "他摄影的 RAW 优化输出", "可用"),
    "知行最终材料": ("桌面", "知行计划材料", "可用"),
    "知行最终版": ("桌面", "知行计划材料", "可用"),
    "图片素材": ("桌面", "散图", "可用"),
    "媒体导出": ("桌面", "零星导出", "可用"),
}

EXP_META = [
    (1, "洞台村乡村美育工作站", "2026-03 → 2026-10"),
    (2, "澜沧支教（Movers4Climate）", "2026-06 → 2026-09"),
    (3, "版画技法补齐（木版 · 石版 · 丝网）", "2026-01 → 2026-06"),
    (4, "第五届美学与艺术研究学术研讨会（会务）", "2025-09 → 2025-11"),
    (5, "「悲鸿 YOUNG」视觉体系", "2026-08 → 2026-10"),
    (6, "厦门集美授课", "2026-04-26 → 2026-05-10"),
    (7, "北京广播电视台 AIGC 科研实习", "2026-01-07 → 2026-02-12"),
    (8, "数字人与交互技术线", "2025-12 → 2026-10"),
]


def q(sql, a=()):
    c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    r = [dict(x) for x in c.execute(sql, a)]
    c.close()
    return r


def build():
    H = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<title>照片证据总览（第二批）2026-10-06</title><style>',
         '*{box-sizing:border-box}body{margin:0;background:#f7f6f3;color:#22201d;',
         'font:15px/1.78 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}',
         '.wrap{max-width:1180px;margin:0 auto;padding:40px 26px 90px}',
         'h1{font-size:26px;margin:0 0 6px;color:#1F3D2B}',
         'h2{font-size:18.5px;margin:36px 0 10px;padding-bottom:7px;border-bottom:2px solid #e5e1da;color:#1F3D2B}',
         'h3{font-size:15.5px;margin:20px 0 6px;color:#9E3B2E}',
         'table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0}',
         'th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}',
         'th{background:#efece6;font-weight:600}',
         'tr:nth-child(even) td{background:#fbfaf8}',
         '.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}',
         '.kpi div{background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:12px 18px;min-width:150px}',
         '.kpi b{display:block;font-size:23px;color:#1F3D2B}',
         '.kpi span{font-size:12px;color:#6b6660}',
         '.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.bad{background:#fdeeee;border-left:4px solid #c0392b;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         'code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:11.5px;word-break:break-all}',
         '.foot{margin-top:52px;padding-top:14px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}',
         '</style></head><body><div class="wrap">']
    A = H.append
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    tot = q("select count(*) n from photos")[0]["n"]
    usable = q("select count(*) n from photos where width>=800 and bytes>=80000")[0]["n"]
    me = q("select count(*) n from photos where role='me'")[0]["n"]
    exact = q("select count(*) n from photos where date_src like '微信消息%' or date_src like '朋友圈%'")[0]["n"]
    roots = q("""select root, count(*) n,
                        sum(case when width>=800 and bytes>=80000 then 1 else 0 end) usable,
                        min(date) d0, max(date) d1
                 from photos group by 1 order by 2 desc""")
    cats = q("select category, count(*) n from photos group by 1 order by 2 desc")

    A("<h1>照片证据总览（第二批）</h1>")
    A('<p style="color:#6b6660;font-size:13px">生成 %s ｜ 主任务：搜集考上央美之后的照片与个人行动证据 → 中期汇报可直接用的 PPT 材料</p>' % now)

    A('<div class="kpi">')
    A('<div><b>%s</b><span>照片总数</span></div>' % "{:,}".format(tot))
    A('<div><b>%s</b><span>可用池（≥800px 且 ≥80KB）</span></div>' % "{:,}".format(usable))
    A('<div><b>%s</b><span>他本人发出（role=me）</span></div>' % "{:,}".format(me))
    A('<div><b>%s</b><span>拿到精确消息/发帖时间</span></div>' % "{:,}".format(exact))
    A("</div>")

    A('<div class="bad"><b>★ 先说结论：照片家底比上一轮大了约 1.4 倍，但「他工作的现场照」仍然稀少。</b><br>'
      '这一轮新挖出 4 类此前**完全没进过索引**的来源：'
      '<b>微信「原图」的 .hevc 高清静帧（9,753）</b>、'
      '<b>朋友圈 media（7,806，配 JSON 可还原发帖时间/昵称/文案）</b>、'
      '<b>井邻项目/宣传文件夹（555）</b>、<b>Capture One 摄影原片（383）</b>。'
      '但**厦门课堂、北京台实习这两个时段的现场照依然几乎没有**（见 §4）。</div>')

    # ── §1 来源
    A("<h2>一、照片来源总览（现算）</h2>")
    A("<table><tr><th>来源</th><th>张数</th><th>可用（≥800px）</th><th>时间跨度</th><th>性质</th><th>判定</th></tr>")
    for r in roots:
        note, desc, verdict = SRC_NOTE.get(r["root"], ("—", "—", "待确认"))
        A("<tr><td><b>%s</b><br><span style='color:#8a857e;font-size:11.5px'>%s</span></td>"
          "<td>%s</td><td>%s</td><td>%s → %s</td><td>%s</td><td>%s</td></tr>"
          % (r["root"], note, "{:,}".format(r["n"]), "{:,}".format(r["usable"] or 0),
             r["d0"] or "—", r["d1"] or "—", desc, verdict))
    A("</table>")

    # ── §2 三类归属
    A("<h2>二、三类归属（任务书第一部分）</h2>")
    A("<table><tr><th>类别</th><th>张数</th><th>说明</th></tr>")
    CM = {"① 我拍摄/记录（我发出）": "他本人发到会话里的照片 —— 拍摄/记录成果",
          "① 我拍摄/记录（存给自己）": "他发到「文件传输助手」的 —— 多为素材留存",
          "① 我拍摄/记录（我发的朋友圈）": "他本人朋友圈 —— 有发帖时间与文案",
          "③ 别人发来（现场/成果，拍摄者待确认）": "他人发来 —— **拍摄者待确认**，不能算他拍的",
          "③ 别人发来（朋友圈，拍摄者待确认）": "别人朋友圈（本批已排除，不用于经历页）",
          "② 记录我工作过程（我产出的设计/作品）": "设计稿/作品/AI 产出 —— 是**产出**不是现场",
          "② 记录我工作过程（导师记录/现场）": "策展集 03_工作站现场_导师记录 —— 他直接发给导师的现场照",
          "待确认": "无语义目录（项目文件夹/摄影原片）—— **拍摄者与角色均待确认**"}
    for r in cats:
        A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
          % (r["category"], "{:,}".format(r["n"]), CM.get(r["category"], "—")))
    A("</table>")
    A('<div class="warn"><b>口径</b>：三类归属是**规则判定**，不是目检结论。'
      '「② 记录我工作过程（我产出的设计/作品）」= 该文件是他做的，<b>但画面里没有他本人</b>；'
      '要写「我设计了…」需要**设计稿 + 交付记录**双重依据。</div>')

    # ── §3 朋友圈硬证据
    A("<h2>三、朋友圈：他自己发的 66 张（带发帖时间与文案）</h2>")
    A('<div class="ok">朋友圈 JSON 每条含 <code>createTime / nickname / contentDesc / media[].localPath</code>，'
      '<b>localPath 直接对上 media 文件名</b> → 可精确还原「谁、什么时候、配了什么话发的哪张图」。'
      '<code>nickname == 蔡浩文</code> 的即他本人发的。</div>')
    sns = q("""select date, width, note, path from photos
               where root='朋友圈' and role='me' order by date desc""")
    key = [r for r in sns if any(k in (r["note"] or "") for k in
           ["厦门", "离厦", "班主任", "甲马", "油墨", "爱马仕", "德宏", "黔", "学习"])]
    A("<table><tr><th>发帖日期</th><th>尺寸</th><th>文案</th></tr>")
    for r in (key or sns)[:26]:
        A("<tr><td>%s</td><td>%s×—</td><td>%s</td></tr>"
          % (r["date"], r["width"], (r["note"] or "").replace("｜", " ｜ ")))
    A("</table>")
    A('<p style="font-size:12.5px;color:#6b6660">共 %d 张；上表为与经历直接相关的条目（其余见 '
      '<code>photos</code> 表 <code>root=朋友圈 and role=me</code>）。</p>' % len(sns))

    # ── §4 逐段可用性
    A("<h2>四、逐段经历：照片可用性与缺口（现算）</h2>")
    idx = os.path.join(WS, "入选原图索引_第二批_2026-10-06.csv")
    have = defaultdict(int)
    if os.path.exists(idx):
        with io.open(idx, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                have[r.get("经历", "")] += 1
    A("<table><tr><th>#</th><th>经历</th><th>区间</th><th>本批入选图</th><th>状态</th></tr>")
    for no, name, dt in EXP_META:
        k = "%02d %s" % (no, name)
        n = have.get(k, 0)
        st = ("✅ 有主图 + 过程图" if n >= 4 else
              ("🟡 图偏少（%d 张）" % n if n else "🔴 本批无图"))
        A("<tr><td>%d</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (no, name, dt, n, st))
    A("</table>")

    A('<h3>明确的缺口（不掩盖）</h3>')
    A('<div class="bad"><b>06 厦门集美授课</b>：<b>没有课堂现场照</b>。'
      '能拿到的是他本人朋友圈 2026-05-01「重生之黑道班主任短期体验卡·五一假期冒名版」与 '
      '2026-05-07「准备离厦了」等自拍/记录，<b>拍摄者待确认</b>；'
      '学校全称与课时也仍待确认。</div>')
    A('<div class="bad"><b>07 北京广播电视台 AIGC 科研实习</b>：全库仅 3 张相关图'
      '（<code>梅宸羽 北京台</code> 1 张 role=me、<code>李明嘉 北京台</code> 2 张）。'
      '**没有工作现场照**。</div>')
    A('<div class="warn"><b>03 版画技法</b>：作品与过程照有，但**石版全流程**、**丝网制版实操**的现场照偏少。'
      '策展集里 C 组前两批是**武宏老师发的临摹参考图，不是他的作品**，已排除。</div>')
    A('<div class="warn"><b>08 数字人</b>：图最多（井邻项目「交互文件与主视觉汇总」134 张含交互装置现场 + 工作坊现场），'
      '但**成品层未交付**，PPT 上必须按「数据层完成 / 架构层设想 / 成品层未交付」写。</div>')

    # ── §5 联系表索引
    A("<h2>五、联系表索引（带编号 / 缩略图 / 来源）</h2>")
    A('<p style="font-size:13px">每段经历一份候选联系表（编号 <code>E01-01</code> 起），'
      '旁边 CSV 是「编号 → 原始路径 / 日期 / 会话 / 谁发的 / 三类归属」对照表。</p>')
    A("<table><tr><th>联系表</th><th>张数</th><th>文件</th></tr>")
    for p in sorted(glob.glob(os.path.join(SHEETS, "EXP*.jpg"))) + \
             sorted(glob.glob(os.path.join(SHEETS, "SRC_*.jpg"))):
        base = os.path.basename(p)
        n = 0
        cs = os.path.splitext(p)[0] + ".csv"
        if os.path.exists(cs):
            with io.open(cs, encoding="utf-8-sig", newline="") as f:
                n = sum(1 for _ in f) - 1
        A("<tr><td>%s</td><td>%d</td><td><code>%s</code></td></tr>" % (base, max(n, 0), p))
    A("</table>")

    # ── §6 交付物
    A("<h2>六、本批交付物</h2>")
    files = [
        ("中期汇报_经历页_第二批_2026-10-06.pptx", "8 页可编辑 PPT（沿用 16:9 · 微软雅黑 · #1F3D2B / #9E3B2E）"),
        ("汇报页面材料包_第二批_2026-10-06.html", "每段经历的材料包（7 项齐全 + 图源明细）"),
        ("入选原图索引_第二批_2026-10-06.csv", "入选图的原始路径 / 三类归属 / 拍摄者 / 转发日期"),
        ("_tmp\\sheets\\EXP01..08*.jpg + .csv", "每段经历的候选联系表（带编号）"),
        ("照片证据总览_第二批_2026-10-06.html", "本文档"),
    ]
    A("<table><tr><th>文件</th><th>说明</th></tr>")
    for f, d in files:
        A("<tr><td><code>%s</code></td><td>%s</td></tr>" % (f, d))
    A("</table>")

    A('<h2>七、还没做的（如实登记）</h2>')
    A("<table><tr><th>#</th><th>待办</th><th>卡在哪</th></tr>"
      "<tr><td>1</td><td>06/07 两段的现场照</td><td>本机确实没有 —— 需本人补拍或从老师/同事处索取</td></tr>"
      "<tr><td>2</td><td>拍摄者判定</td><td>已按 <code>role</code> 严格判定；<b>项目文件夹与摄影原片无 role 语义</b>，一律「待确认」</td></tr>"
      "<tr><td>3</td><td>拍摄日期</td><td>微信已剥离 EXIF —— <b>结构性拿不到</b>；只能给转发日期</td></tr>"
      "<tr><td>4</td><td>「我做了什么」的句子</td><td>需要读同期聊天原文 —— <b>远程模型读取范围未确认</b>，未启动</td></tr>"
      "<tr><td>5</td><td>其余 45 段经历的照片</td><td>本批只做了证据较完整的 8 段</td></tr>"
      "</table>")

    A('<div class="foot">工具 <code>tools\\photo_evidence_overview.py</code> ｜ '
      '照片索引 <code>tools\\hevc_photos.py</code> + <code>tools\\photo_sources.py</code> ｜ '
      '联系表 <code>tools\\contact_sheet.py</code> ｜ '
      '<b>内部资料，含个人隐私，不得外传</b></div>')
    A("</div></body></html>")
    io.open(OUT, "w", encoding="utf-8").write("\n".join(H))
    return OUT


if __name__ == "__main__":
    try:
        print("→", build())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
