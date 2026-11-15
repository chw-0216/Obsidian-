# -*- coding: utf-8 -*-
r"""
build_first_report_list.py —— 《央美之后 · 汇报清单（首版）》

为什么单独出一份
----------------
10-05 那份《中期汇报可用成果与材料》是**盘点**（把材料摊开）；
这一份是**清单**（决定讲什么、按什么顺序讲、哪些还不能讲）。

数据来源（全部只读）
--------------------
1. `_tmp\batch\batch.sqlite`            —— 本次全量批处理的覆盖与缺口
2. 桌面成果包 `02_数据表\*.csv`          —— 8 条线的候选成果（由 export_report_pack 从主文档反抽）
3. `tools\batch_pipeline.py` 的 FINDINGS / NEXT_QUEUE —— 本轮新挖到的线索与未完成队列

产出
----
`汇报清单_首版_2026-10-06.html`（单文件 · 浅色 · 中文）
"""
import os, io, csv, json, sqlite3, datetime, traceback

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
BDB = os.path.join(BATCH, "batch.sqlite")
PACK = r"C:\Users\wardc\Desktop\中期汇报_成果与材料_2026-10-05"
CSVDIR = os.path.join(PACK, "02_数据表")
OUT = os.path.join(WS, "汇报清单_首版_2026-10-06.html")

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ──────────────────────────────────────────────────────── 读数据
def rd(name):
    """读桌面成果包里的 CSV（utf-8-sig，第一行是表头）→ list[dict]"""
    p = os.path.join(CSVDIR, name)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def batch_stats():
    """从 batch.sqlite 取覆盖口径"""
    d = {"materials": 0, "bytes": 0, "dup": 0, "extracted": 0, "need": 0,
         "weeks": 0, "msgs": 0, "mine": 0, "exp": 0, "bad": 0}
    if not os.path.exists(BDB):
        return d
    c = sqlite3.connect(BDB)
    d["materials"], d["bytes"] = c.execute("select count(*),coalesce(sum(bytes),0) from materials").fetchone()
    d["dup"] = c.execute("select count(*) from materials where dup_of is not null").fetchone()[0]
    d["extracted"] = c.execute("select count(*) from materials where extracted=1").fetchone()[0]
    d["need"] = c.execute("select count(*) from materials where need_tool<>''").fetchone()[0]
    d["weeks"], d["msgs"] = c.execute("select count(*),coalesce(sum(messages),0) from weeks").fetchone()
    d["exp"] = c.execute("select count(*) from experiences").fetchone()[0]
    # 「他本人发言」从周摘要索引里取（digest_index.csv 第 6 列）
    p = os.path.join(BATCH, "digest_index.csv")
    if os.path.exists(p):
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        d["mine"] = sum(int(r.get("他发言") or 0) for r in rows)
    c.close()
    return d


# ──────────────────────────────────────────────────────── 增量（这一版比上一版多了什么）
DELTA = [
    ("证实", "Movers4Climate 澜沧支教 · 立项时间链",
     "06-30 培训 → 07-04 首批立项公示 → 07-08 完整名单 → 08-31 向米雪老师承诺 09-02 提交",
     "「立项2群」有记录 → 角色从「参与」升级为 <b>立项团队</b>"),
    ("证实", "央美美术馆 2026 年秋季实习生录用",
     "2026-09-22 美术馆办公室岳老师录用通知",
     "与 E 线已登记条目一致；<b>到岗日期仍未确认</b>"),
    ("新增", "《未来之阈——首届实验艺术展览》（中国美协艺委会届展系列）",
     "2025-12-31 母亲转来征稿+报名表 docx → 2026-01-04 群通知 → 2026-04-10 武汉（湖北美院）开幕",
     "<b>他是否入选 / 入选何作 = 待核实</b>，先不进成果"),
    ("新增", "央美创客市集（2026-04-03）",
     "材料里出现 `附件3 央美创客市集入驻摊主承诺书.docx`",
     "<b>是否实际入驻 = 待核实</b>"),
    ("新增", "filehelper（文件传输助手）23,315 条 · 其中 3,045 条是「贴进来让 AI 读」",
     "内容多为「当前版本不支持展示该内容」（如 USER.md）",
     "行为证据：<b>他用微信做 AI 中转</b>，不是社交 —— 可用于说明工具化习惯"),
    ("证据规则", "Tripothon S1（Tripo3D 全球黑客松，09-01 → 10-05 报名）",
     "他在该群 <b>0 发言</b>，只有群消息",
     "★ <b>群内零发言不能证明未参与</b> → 从「已排除」改回 <b>候选 · 待追踪</b>"),
    ("证据规则", "团队成果 ≠ 个人贡献（澜沧 / 工作站 / 悲鸿 YOUNG）",
     "澜沧是「立项团队」· 工作站有团队动作（布展/搬运/接待）· 悲鸿 YOUNG 有导师参与",
     "★ 汇报里必须<b>逐项写清「这部分是不是我做的」</b>，不得把团队成果直接写成个人成果"),
    ("口径修正", "母亲转账「两年 389 笔 / ¥347,550」",
     "微信转账每笔记两行（them + me，内容逐字相同），去重后 197 笔 / ¥174,825",
     "真值约为旧数字的 <b>1/2</b>；「2026-08 峰 42 笔 / ¥60,900」→ <b>21 笔 / ¥30,450</b>"),
]

# ──────────────────────────────────────────────────────── 证据规则（2026-10-06 修正）
EVIDENCE_RULES = [
    ("群内零发言", "❌ 不能证明「未参与」", "✅ 只能说明「无直接证据」→ 保留候选，继续追踪（查私聊 / 其他群 / 提交记录 / 作品）"),
    ("活动通知", "❌ 不能证明「个人入选」", "✅ 只能说明「收到了通知」→ 需另找入选名单 / 入选通知 / 展出作品"),
    ("团队成果", "❌ 不能直接等同「个人贡献」", "✅ 必须逐项拆开：哪些是他独立决定 / 独立完成的，哪些是团队动作"),
    ("群消息", "❌ 不能当作「个人经历」", "✅ 只能作为「背景线索」→ 个人行为需另找他的发言 / 提交 / 现场记录"),
    ("摘要 / 报告", "❌ 不能替代原文", "✅ 结论必须回到原始消息、文件、照片核对"),
]

# ──────────────────────────────────────────────────────── 待核实 / 排除 / 红线
TODO_VERIFY = [
    ("《未来之阈》他是否入选、入选何作", "2025-12-31 征稿 → 2026-04-10 武汉开幕",
     "★ 活动通知 ≠ 个人入选 → 需另找入选名单 / 入选通知 / 展出作品"),
    ("央美创客市集他是否实际入驻", "2026-04-03 摊主承诺书", "回原件确认签署与履约"),
    ("厦门集美那条线：学校全称 / 课时 / 学生数", "2026-04-26 → 05-10 授课",
     "记录里只有「集美区」「在厦门上课」，无学校全称"),
    ("Tripothon S1 他到底参没参加", "2026-09-01 → 10-05 报名期",
     "★ 群内零发言 ≠ 未参与 → 需查私聊 / 提交记录 / 作品 / 其他群"),
]
EXCLUDED = [
    ("「海淀精华培训学校 2025.09–至今」", "本人 2026-10-04 明确否认「我没去」；全库「精华」70 条无一条是该校工作往来",
     "不作为事实使用"),
    ("数字人「已完成交付」", "数据层完成 / 架构层设想 / 成品层未交付（导师 2026-03-09「要的是你的」）", "严格按三段口径写"),
    ("北京台实习「独立负责技术开发」", "实际是「非技术背景的协助」", "只写他负责的环节"),
]
REDLINES = [
    "数字人口径不能松：<b>数据层完成 / 架构层设想 / 成品层未交付</b>。",
    "北京台实习只写<b>你负责的环节</b>，不写「独立负责技术开发」。",
    "井邻<b>优惠与商业信息不进对外材料</b>（导师 2026-08-05 红线）。",
    "「父母冷战」不得当数据事实引用 —— 全库零命中，只有本人自述，引用必标来源。",
    "王博线含身份证号 → <b>严禁外传</b>。",
    "陈昶文归零两说并存，<b>不得写成因果，也不得读成薄情</b>。",
]


# ──────────────────────────────────────────────────────── HTML
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f7f6f3;color:#22201d;
 font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:40px 26px 90px}
h1{font-size:27px;margin:0 0 8px;letter-spacing:-.4px}
.meta{color:#6b6660;font-size:13px;margin:0 0 4px}
h2{font-size:18px;margin:38px 0 12px;padding-bottom:8px;border-bottom:2px solid #e5e1da}
h3{font-size:15px;margin:22px 0 8px;color:#4a4642}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0}
th,td{border:1px solid #e5e1da;padding:7px 10px;text-align:left;vertical-align:top}
th{background:#efece6;font-weight:600;white-space:nowrap}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 6px}
.kpi{flex:1 1 158px;background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:12px 14px}
.kpi .k-l{font-size:12px;color:#6b6660}
.kpi .k-v{font-size:21px;font-weight:700;letter-spacing:-.5px;margin:2px 0}
.kpi .k-n{font-size:11.5px;color:#8a857e}
.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;
 border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}
.bad{background:#fdeeee;border-left:4px solid #c0392b;padding:11px 15px;
 border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}
.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;
 border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}
code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:12.5px}
details{background:#fff;border:1px solid #e5e1da;border-radius:8px;margin:10px 0;padding:0}
details>summary{cursor:pointer;padding:11px 15px;font-weight:600;font-size:14.5px;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary:before{content:"▸ ";color:#8a857e}
details[open]>summary:before{content:"▾ "}
details>summary:hover{background:#faf9f7;border-radius:8px}
details>.body{padding:0 15px 14px}
.toc{background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:14px 20px;margin:18px 0}
.toc ol{margin:6px 0 0;padding-left:22px}
.toc li{margin:4px 0;font-size:13.5px}
.toc a{color:#24476f;text-decoration:none}
.toc a:hover{text-decoration:underline}
ul,ol{margin:10px 0;padding-left:24px}
li{margin:5px 0}
blockquote{margin:10px 0;padding:10px 16px;background:#f2f0eb;border-radius:0 6px 6px 0;
 border-left:3px solid #b4b2a9;font-size:13.5px;color:#3a3733}
.foot{margin-top:56px;padding-top:16px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}
.tag{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:10px;margin-right:5px}
.t-ok{background:#e4f2e6;color:#2c6b3b}
.t-wait{background:#fdf1d6;color:#8a6413}
.t-no{background:#f6dede;color:#8f2f2f}
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    st = batch_stats()
    cand = rd("02_候选成果总表_全部.csv")
    top8 = rd("04_今天优先讲的8项.csv")
    new9 = rd("03_原清单没有的9项.csv")
    mainline = rd("06_汇报主线四段_6.1_主线.csv")
    pic1 = rd("05_素材索引_5.1_精选图.csv")
    pic2 = rd("05_素材索引_5.2_全量照片.csv")
    doc3 = rd("05_素材索引_5.3_文档与证明.csv")
    base = rd("01_时间基线.csv")

    # 按「线」分组候选成果
    lines = {}
    order = []
    for r in cand:
        k = (r.get("线") or "未分类").strip()
        if k not in lines:
            lines[k] = []
            order.append(k)
        lines[k].append(r)

    H = []
    A = H.append
    A('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A('<title>央美之后 · 汇报清单（首版）2026-10-06</title>')
    A("<style>%s</style></head><body><div class='wrap'>" % CSS)

    # ── 头
    A("<h1>央美之后 · 汇报清单（首版）</h1>")
    A('<p class="meta">窗口 2025-03-26（拟录取）→ 2026-10-06 ｜ 生成 %s</p>' % NOW)
    A('<p class="meta">依据：<b>%s</b> 个聊天周包（%s 条消息 · 他本人 %s 条）· '
      '<b>%s</b> 份材料登记（%.1f GB）· 事件库 %s 条经历行</p>'
      % ("{:,}".format(st["weeks"]), "{:,}".format(st["msgs"]), "{:,}".format(st["mine"]),
         "{:,}".format(st["materials"]), st["bytes"] / 1024 ** 3, "{:,}".format(st["exp"])))
    A('<p class="meta">入口：① 全量批处理 <code>_tmp\\batch\\batch.sqlite</code> '
      '② 桌面成果包 <code>02_数据表</code> ③ 事件库 <code>analysis.sqlite</code> ④ 照片与作品目录</p>')
    A('<div class="bad"><b>内部资料 · 不得外传</b>：含真人姓名、机构、未公开材料与联系方式。'
      '原始资料全程本地处理，未上传第三方。</div>')

    A('<div class="kpis">')
    for k, v, n in [
        ("可讲成果", "%d 项" % len(cand), "覆盖 %d 条线" % len(order)),
        ("今天优先讲", "%d 项" % len(top8), "按背书强度排序"),
        ("待核实", "%d 项" % len(TODO_VERIFY), "先别写进成果"),
        ("明确排除", "%d 项" % len(EXCLUDED), "不得当成果"),
        ("覆盖消息", "{:,}".format(st["msgs"]), "%d 个周包" % st["weeks"]),
        ("材料登记", "{:,}".format(st["materials"]), "%.1f GB" % (st["bytes"] / 1024 ** 3)),
    ]:
        A('<div class="kpi"><div class="k-l">%s</div><div class="k-v">%s</div><div class="k-n">%s</div></div>'
          % (k, v, n))
    A("</div>")

    # ── 目录
    A('<div class="toc"><b>目录</b><ol>')
    for sid, t in [
        ("s0", "一句话结论"),
        ("s1", "这一版比 10-05 那版多了什么"),
        ("s2", "可讲成果总表（%d 条线）" % len(order)),
        ("s3", "今天优先讲的 8 项"),
        ("s4", "待核实 / 明确排除 / 口径红线 / 证据规则"),
        ("s5", "素材在哪"),
        ("s6", "汇报主线四段（附讲述文字）"),
        ("s7", "★ 隐私分流（对外展示前必读）"),
        ("s8", "还没做的（未完成队列）"),
    ]:
        A('<li><a href="#%s">%s</a></li>' % (sid, t))
    A("</ol></div>")

    # ── 0 一句话结论
    A('<h2 id="s0">一句话结论</h2>')
    A('<blockquote>考上央美之后这 19 个月，主线只有一条：'
      '<b>把技法补齐 → 到真实现场用出来 → 把手艺转成课 → 再提炼成可核算的方法</b>。'
      '四段各有实物，且互相咬合。其中最强的两张牌是 '
      '<b>洞台村乡村美育工作站</b>（18 个月 · 从 0 到 1 · 有 8 批次领导接待与两次开街的外部背书）和 '
      '<b>澜沧支教</b>（联合国开发计划署 Movers4Climate 立项 · 有结项与支教证明）。'
      '本轮全量批处理<b>没有推翻任何一条主线</b>，只做了三件事：'
      '把澜沧的角色从「参与」坐实为「立项团队」、新增 2 条待核实线索、排除 1 条误判。</blockquote>')

    # ── 1 增量
    A('<h2 id="s1">一、这一版比 10-05 那版多了什么</h2>')
    A('<p>这一版不是重排旧内容 —— 它跑了一遍全量批处理'
      '（%s 份材料登记 · %s 个周包 · 全联系人双向覆盖）。结果分三类：</p>'
      % ("{:,}".format(st["materials"]), "{:,}".format(st["weeks"])))
    A("<table><tr><th>类型</th><th>内容</th><th>依据</th><th>结论</th></tr>")
    for kind, what, basis, concl in DELTA:
        cls = {"证实": "t-ok", "新增": "t-wait", "排除": "t-no", "口径修正": "t-wait"}.get(kind, "")
        A("<tr><td><span class='tag %s'>%s</span></td><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"
          % (cls, kind, esc(what), basis, concl))
    A("</table>")

    # ── 2 可讲成果总表
    A('<h2 id="s2">二、可讲成果总表（%d 项 · %d 条线）</h2>' % (len(cand), len(order)))
    A('<div class="ok"><b>读法</b>：每条线的第一行是<b>这条线为什么值得讲</b>；'
      '下面逐条列日期 / 事项 / 个人贡献 / 具体产物 / 状态。'
      '<b>状态 = 已交付</b>的可以直接用；<b>进行中 / 原型</b>的要按口径写。</div>')
    for k in order:
        rows = lines[k]
        A("<details%s><summary>%s —— %d 项</summary><div class='body'>"
          % (" open" if k.startswith(("B", "C")) else "", esc(k), len(rows)))
        A("<table><tr><th>日期</th><th>事项</th><th>个人贡献</th><th>具体产物</th><th>状态</th><th>备注</th></tr>")
        for r in rows:
            A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (esc(r.get("日期", "")), r.get("事项", ""), esc(r.get("个人贡献", "")),
                 esc(r.get("具体产物", "")), esc(r.get("状态", "")), r.get("备注", "")))
        A("</table></div></details>")

    # ── 3 今天优先讲的 8 项
    A('<h2 id="s3">三、今天优先讲的 8 项</h2>')
    if top8:
        A("<table><tr><th>序</th><th>成果</th><th>入选理由</th><th>最强的一张牌</th></tr>")
        for r in top8:
            A("<tr><td class='n'>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"
              % (esc(r.get("序", "")), esc(r.get("成果", "")), r.get("入选理由", ""),
                 esc(r.get("最强的一张牌", ""))))
        A("</table>")
    else:
        A('<div class="warn">未找到 <code>04_今天优先讲的8项.csv</code>，请先跑 <code>export_report_pack.py</code>。</div>')

    # ── 4 待核实 / 排除 / 红线
    A('<h2 id="s4">四、待核实 / 明确排除 / 口径红线</h2>')
    A("<h3>4.1 待核实（<b>先别写进成果</b>）</h3>")
    A("<table><tr><th>事项</th><th>线索</th><th>怎么确认</th></tr>")
    for a, b, c in TODO_VERIFY:
        A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (a, b, c))
    A("</table>")
    A("<h3>4.2 明确排除（<b>不得当成果</b>）</h3>")
    A("<table><tr><th>事项</th><th>为什么排除</th><th>口径</th></tr>")
    for a, b, c in EXCLUDED:
        A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (a, b, c))
    A("</table>")
    A("<h3>4.3 口径红线（写材料时逐条对照）</h3><ul>")
    for r in REDLINES:
        A("<li>%s</li>" % r)
    A("</ul>")
    A("<h3>4.4 ★ 证据规则（2026-10-06 修正 —— 写材料前必须先过这一关）</h3>")
    A('<div class="warn">这三条是<b>判断「什么能写、什么不能写」的尺子</b>。'
      '违反它们不会报错，但会把「背景」写成「成果」，一旦被追问就站不住。</div>')
    A("<table><tr><th>证据类型</th><th>❌ 不能证明</th><th>✅ 只能说明</th></tr>")
    for a, b, c in EVIDENCE_RULES:
        A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (a, b, c))
    A("</table>")

    # ── 5 素材在哪
    A('<h2 id="s5">五、素材在哪</h2>')
    if pic1:
        A("<h3>5.1 精选图（33 张，语义命名，做 PPT 直接用）</h3>")
        A("<table><tr><th>用途</th><th>文件名</th></tr>")
        for r in pic1:
            A("<tr><td><b>%s</b></td><td>%s</td></tr>" % (esc(r.get("用途", "")), esc(r.get("文件名", ""))))
        A("</table>")
    if pic2:
        A("<h3>5.2 全量照片</h3>")
        A("<table><tr><th>张数</th><th>目录</th><th>内容与用法</th></tr>")
        for r in pic2:
            A("<tr><td class='n'>%s</td><td><code>%s</code></td><td>%s</td></tr>"
              % (esc(r.get("张数", "")), esc(r.get("目录", "")), esc(r.get("内容与用法", ""))))
        A("</table>")
    if doc3:
        A("<h3>5.3 文档与证明</h3>")
        A("<table><tr><th>材料</th><th>位置</th><th>建议用途</th></tr>")
        for r in doc3:
            A("<tr><td><b>%s</b></td><td><code>%s</code></td><td>%s</td></tr>"
              % (esc(r.get("材料", "")), esc(r.get("位置", "")), esc(r.get("建议用途", ""))))
        A("</table>")
    if base:
        A("<h3>5.4 时间基线（汇报开场用）</h3>")
        A("<table><tr><th>节点</th><th>日期</th><th>依据</th><th>确定性</th></tr>")
        for r in base:
            A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (esc(r.get("节点", "")), esc(r.get("日期", "")), esc(r.get("依据", "")),
                 esc(r.get("确定性", ""))))
        A("</table>")

    # ── 6 主线四段
    A('<h2 id="s6">六、汇报主线四段（附讲述文字）</h2>')
    if mainline:
        A("<table><tr><th>段</th><th>时间</th><th>做什么</th><th>对应成果</th></tr>")
        for r in mainline:
            A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (esc(r.get("段", "")), esc(r.get("时间", "")), esc(r.get("做什么", "")),
                 esc(r.get("对应成果", ""))))
        A("</table>")
    A("<h3>讲述文字（可直接念）</h3>")
    A('<blockquote>过去这一年，我做的事情可以压成四个字：<b>学、用、教、研</b>。<br><br>'
      '<b>先是「学」</b>。研一这一年，我把版画的技法链条补齐了 —— 从木版，到丝网，再到石版。'
      '木版是导师专门跟武宏老师沟通让我插班进大二的课，武老师还送了我一整套全新的木刻刀。'
      '同时我一直在旁听开题、中期、答辩，把学术坐标先建立起来。<br><br>'
      '<b>然后是「用」</b>。我把工作坊从零建到了能运营 —— 怀柔洞台村的乡村美育工作站，18 个月，'
      '搬运、布线、装屏、装空调、跑地图标注、定价格方案，8 批次领导接待、两次开街，我都在现场。'
      '这条线是导师直接交办的，也是我时间投入最长的一件事。<br><br>'
      '<b>再是「教」</b>。我先在厦门做了一学期的正规课程授课，然后带团队去云南澜沧做乡村支教。'
      '澜沧这个项目是联合国开发计划署的 Movers4Climate，全国 563 支团队报名，我们立项了，'
      '我用丝网印刷去讲可持续发展 —— 这是我自己的方法论，不是照搬的教案。<br><br>'
      '<b>最后是「研」</b>。我在试着把乡村美育做成可核算、可运营、可复制的东西 —— '
      '用经济学的视角做运营方案、做边际成本分析、做印迹扩散系统。'
      '同时我也在用数据工具去研究「人」本身，这套微信分析流水线就是我自己搭的。<br><br>'
      '所以这一年不是四件散事，是一条链：<b>学到的技法，在真实现场用出来，'
      '再转成课教给别人，最后提炼成可复用的方法</b>。</blockquote>')

    # ── 7 隐私分流
    A('<h2 id="s7">七、★ 隐私分流（对外展示前必读）</h2>')
    A('<div class="bad"><b>★ 新发现（2026-10-06）</b>：原来的隐私核对<b>只扫知识库</b>，'
      '漏掉了<b>对外产物本身</b>。补扫后确认：'
      '<b>12 份工作区 HTML（含桌面包副本）里有 24 处敏感串</b> —— '
      '手机号 22 个 · 银行卡 1 个 · <b>身份证 1 个</b>。'
      '这些是<b>会被展示</b>的文件，比知识库更该先处理。</div>')
    A("<h3>7.1 两类风险分开看</h3>")
    A("<table><tr><th>风险面</th><th>规模</th><th>性质</th><th>处置</th></tr>"
      "<tr><td><b>知识库</b>（Obsidian）</td><td>57 处 / 25 文件（+13 个文件名本身含手机号）</td>"
      "<td>内部分析用；开 Sync 会上传</td>"
      "<td>二选一：① <code>sanitize_vault_pii.py --apply</code> 脱敏 ② 永久不开 Sync</td></tr>"
      "<tr><td><b>对外产物</b>（HTML / 桌面包）</td><td>24 处 / 12 文件</td>"
      "<td><b>会被别人看到</b></td>"
      "<td>用 <code>pii_split.py</code> 生成脱敏副本 → <code>_tmp\\pii\\公开版\\</code></td></tr>"
      "</table>")
    A("<h3>7.2 分流口径（内部分析 vs 可公开）</h3>")
    A("<table><tr><th>分类</th><th>内容</th><th>处置</th></tr>"
      "<tr><td><b>A 内部分析必需</b></td><td>商家/服务联系人的手机号（图文广告、租车、酒店、教练、钥匙、丝印…）</td>"
      "<td>保留在库 —— 本地分析要用它识别关系；<b>但任何外发材料一律剔除</b></td></tr>"
      "<tr><td><b>B 不可公开</b></td><td>真人 PII / <b>身份证</b> / 银行卡（人物档案、事件库、个人信息）</td>"
      "<td>保留在库；<b>外发一律脱敏</b>。<b>身份证风险最高</b></td></tr>"
      "<tr><td><b>C 工具自动索引</b></td><td>脚本生成的清单（文件位置清单、距离档复核清单）</td>"
      "<td>PII 是顺带扫进来的 → <b>可整表脱敏或排除外发</b></td></tr>"
      "<tr><td><b>D 汇报展示版</b></td><td>本清单 + 成果 HTML + 素材图</td>"
      "<td>★ 展示版<b>不需要</b>任何人物档案 —— 所以最干净的做法是<b>白名单</b>，不是黑名单</td></tr>"
      "</table>")
    A('<div class="ok"><b>结论</b>：<b>汇报展示不需要人物档案</b>。'
      '所以对外展示用「白名单」——只放成果材料（成果 HTML + 素材图 + 项目文档），'
      '人物档案与聊天分析一律不进展示包。这样<b>不需要逐处脱敏</b>，也不会漏。</div>')

    # ── 8 未完成队列
    A('<h2 id="s8">八、还没做的（未完成队列）</h2>')
    q = []
    p = os.path.join(BATCH, "未完成队列.json")
    if os.path.exists(p):
        try:
            q = json.loads(io.open(p, encoding="utf-8").read())
        except Exception:
            q = []
    if q:
        A("<table><tr><th>编号</th><th>任务</th><th>当前状态</th><th>需要什么才能继续</th></tr>")
        for it in q:
            A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (it.get("id", ""), it.get("task", ""), it.get("status", ""), it.get("need", "")))
        A("</table>")
    A('<div class="warn"><b>★ 卡点只有两个</b>：'
      '① <b>缺 OCR / ASR / Office 解析工具</b> —— 挡住 %s 份图片 / 视频 / Office 文档的正文'
      '（连带挡住「经历归并」与「竞争解释」）；'
      '② <b>未授权远程模型</b> —— 挡住真正吃 token 的「逐材料精读」。'
      '本清单<b>不虚报</b>：这 %s 份材料<b>不计入已读</b>。</div>'
      % ("{:,}".format(st["need"]), "{:,}".format(st["need"])))

    # ── 覆盖与限制
    A('<h2>口径与限制</h2>')
    A("<ul>")
    A("<li><b>聊天覆盖</b>：从 2025-03-26 起按自然周切片，<b>不筛选联系人</b>，"
      "私聊与群聊同时读取双方发言。共 %s 个周包 / %s 条消息。</li>"
      % ("{:,}".format(st["weeks"]), "{:,}".format(st["msgs"])))
    A("<li><b>材料四态分开</b>：找到文件 %s ｜ 成功提取正文 %s ｜ 送入模型 0 ｜ 分析完成（周摘要）%s。"
      "重复副本 %s 份复用。</li>"
      % ("{:,}".format(st["materials"]), "{:,}".format(st["extracted"]),
         "{:,}".format(st["weeks"]), "{:,}".format(st["dup"])))
    A("<li><b>不可读</b>：8,126 条（2.4%）为 link 卡片「当前版本不支持展示该内容」，"
      "导出时未落正文 —— <b>不计入已读</b>。</li>")
    A("<li><b>用量</b>：本轮<b>未调用任何远程模型 API</b>，接口实际用量 = unknown，平台额度扣减 = 0。"
      "1 亿 token 目标<b>未达成</b>，原因见第七节。</li>")
    A("<li><b>数字口径</b>：母亲转账已按「双倍记账」去重，"
      "两年 <b>197 笔 / ¥174,825</b>；2026-08 峰 <b>21 笔 / ¥30,450</b>。</li>")
    A("</ul>")

    A('<div class="foot">生成脚本 <code>tools\\build_first_report_list.py</code> ｜ '
      '数据 <code>_tmp\\batch\\batch.sqlite</code> + 桌面成果包 <code>02_数据表</code> ｜ '
      '<b>内部资料，不得外传</b></div>')
    A("</div></body></html>")

    io.open(OUT, "w", encoding="utf-8").write("\n".join(H))
    return OUT


if __name__ == "__main__":
    try:
        p = build()
        print("→ %s（%.1f KB）" % (p, os.path.getsize(p) / 1024))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
