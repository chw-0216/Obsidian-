# -*- coding: utf-8 -*-
"""
build_master_index.py —— 分析总览：一个页面找到全部分析产物（只读扫描 + 生成索引）

产出：
  WS\分析总览_全部文件地图_2026-10-04.html        —— 可点击打开本地文件
  Obsidian\03_微信聊天分析\🗺️分析总览·全部文件地图.md —— wikilink 版
"""
import io, os, glob, urllib.parse

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
OUT_HTML = os.path.join(WS, "分析总览_全部文件地图_2026-10-04.html")
OUT_MD = os.path.join(VAULT, "03_微信聊天分析", "🗺️分析总览·全部文件地图.md")
ENGINE = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine"

def size_of(p):
    try: return os.path.getsize(p)
    except Exception: return 0
def kb(n):
    return "%.0f KB" % (n / 1024) if n < 1024*1024 else "%.1f MB" % (n / 1024 / 1024)

# ============================================================
# 一、HTML 清单 —— 按主题分组 + 一句话
# ============================================================
GROUPS = [
 ("0", "★ 系统地基 · 可追溯层", "「这条结论的依据是什么」—— 一切分析的地基，先看这一组", [
  ("系统重构_第一轮_证据与更新机制_2026-10-04.html", "系统重构第一轮 🧱", "永久事件 ID 2,864 · 证据回链 0%→51.4% · 结论 57 条（已撤回 8 退出画像）· 30 份产物同一版本戳 · 22 项验收全过"),
  ("第二轮_工作台_盲测_隐私核对_2026-10-05.html", "第二轮：工作台 · 盲测 · 隐私 🗃️", "Obsidian Bases 四视图（262 篇 = 59 结论 + 203 事件 + 4 个 .base）· 盲测 7/7（79 人名×203 组零时间倒流）· 隐私 9 项（Ollama 监听地址已修 · 知识库 57 处 PII 待拍板）"),
  ("第三方报告审读_行为动力学预测_2026-10-05.html", "第三方报告审读 🔍", "30 项逐条回库核对：19 项准确（照抄引擎）· 3 冲突 · 5 越红线 · 3 不支撑 · 4 预测（P2/P4/P5 未校准）· ★ 归档「对外不可用样本」"),
 ]),
 ("A", "时间轴 · 年度 · 钱", "「什么时候发生了什么」—— 先看这一组", [
  ("自我理解引擎_统一排查台_2026-10-05.html", "统一排查台 🧰", "★ 一份文档装下本轮全部结果：已裁决结论 · 数据表全集（8月逐日 / 滞后相关 / 逐小时 / 骨架矩阵 / 178 候选 / 外部源）· 结论台账 61 条 · 遗留问题台账 · 红线与陷阱速查 · 脚本与产物索引 · 系统状态"),
  ("年度事件重建_第二个我_第一轮_2026-10-05.html", "年度事件重建 · 第一轮 🧭", "8 条生活线 × 13 个月骨架 · 补 178 条缺口候选 · 三条深入链（车钱父母 / 井邻导师 / 笑一）· 三套竞争解释 · 五个待补问题 · 盲测核对 · **8 月逐日对齐：C1/C2 双双证伪** · **独处时段：C3 拆两半（挤压成立 / 补偿不成立）**"),
  ("这两年重要的事_2024-11至2026-10_2026-10-04.html", "两年时间轴", "六个阶段 · 十件重要的事 · 五条新发现"),
  ("这一年_大胆猜测_2025-10至2026-10_2026-10-04.html", "这一年：钱是主线", "钱 → 自述 → 关系结构（母亲转账 389 笔 / 347,550 元）"),
  ("这一年_车与家教线_2026-10-04.html", "车 · 家教线 · 清理", "车定案（极狐 αT5 · 132,050）· 家教线 21,979 条 / 他 0 条 · 清理 48%"),
  ("最近68天事件梳理_2026-07-24至09-29.html", "最近 68 天事件流", "暑期段的逐日事件（研一→研二转折期）"),
  ("支付流打通_微信支付与美团_2026-10-04.html", "支付流：微信支付 × 美团", "2,207 条支付流 · 美团月付扣款失败「余额不足」· 央美学费 ¥20,000 · 云南铁证"),
  ("支付流×事件库_深度打通_2026-10-04.html", "钱 × 事件打通", "事件库 2,686→2,813 · 大额日空白 57%→4% · 修 110 条日期年份错"),
  ("井邻_洞台村_全打通_2026-10-04.html", "井邻主线全打通 🌰", "515 条 / 99 会话 · 井邻事件 0→51 条 · 距离地图 82→98 人 · 三线并行 · 三句话张力"),
  ("逐日全维整合_2024-11至2026-10_2026-10-04.html", "逐日全维整合 🗓️", "699 天 × 26 列 · 四源汇流 · 10 天四维同日 · 月度三轴不同步 · ★ 校友会运营线"),
 ]),
 ("B", "贯通与真相源", "「所有东西怎么连起来」—— 引擎侧的入口", [
  ("总贯通_全层打通_2026-10-04.html", "总贯通：七层打通 🌐", "七层检修 + 校表 · 距离地图 53→82 人 · 建立单一真相源"),
  ("Obsidian打通与进度盘点_2026-09-29.html", "Obsidian 打通与进度盘点", "知识库接口与进度总盘点"),
  ("自我理解引擎_v1_说明书.html", "引擎 v1 说明书", "自我理解引擎的第一版说明"),
  ("自我理解引擎_v2_事件层整合.html", "引擎 v2 事件层整合", "把事件层并入引擎"),
  ("自我理解引擎_本轮裁定汇总_2026-09-29.html", "本轮裁定汇总", "2026-09-29 一轮的裁定记录"),
 ]),
 ("C", "多轮交叉与访谈", "「问过什么 · 答过什么 · 还差什么」", [
  ("多轮交叉分析_八个源全跑通_2026-10-04.html", "8 源对齐", "42,717 人 × 18 列 · 八个数据源全跑通"),
  ("本轮访谈与裁定汇总_2026-10-04.html", "访谈与裁定汇总", "本轮全部问答与裁定"),
  ("已答与未答对照表_2026-10-04.html", "已答 / 未答对照表", "一条一条列清哪些答了、哪些悬空"),
  ("待本人补全台账_2026-10-04.html", "待本人补全台账", "只有他本人能回答的清单"),
  ("遗留问题台账_2026夏5问_2026-10-04.html", "2026 夏 5 问台账", "来源：最近 68 天报告第六节"),
 ]),
 ("D", "关系与距离", "「谁离我多近」—— 距离地图的三次标定", [
  ("29人距离标定完成_2026-10-04.html", "29 人距离标定", "第二锚点（补标）完成记录"),
  ("全库距离档预标定方案_2026-10-04.html", "全库距离档预标定 ★", "★ 铁律：距离档不可自动推断，只能人工锚点"),
  ("关系起点逆推_18人深度分析_2026-10-04.html", "关系起点逆推（18 人）", "从最早消息倒推关系怎么开始的"),
  ("渠道与场景逆推_2026-10-04.html", "渠道与场景逆推", "在哪认识的 · 什么场景"),
  ("同门与现金流_四条裁定后的深度分析_2026-10-04.html", "同门与现金流", "四条裁定后的深度分析"),
  ("安奇线裁定_侯安琪跑博士与坝上资源_2026-10-04.html", "安奇线裁定", "侯安琪跑博士与坝上资源"),
 ]),
 ("E", "数据治理与清理", "「数据本身可靠吗」—— 去重 / 覆盖 / 清理", [
  ("去重处置与索引重建_2026-10-04.html", "去重与索引重建", "server_id 去重 · index_v2 · 真重复归零"),
  ("全量语料重跑与清理_2026-10-04.html", "全量语料重跑", "1,802 会话 / 388,366 条导出核验"),
  ("数据源全景与深度分析路线图_2026-10-04.html", "数据源全景与路线图", "有哪些源 · 下一步往哪走"),
  ("最近一年覆盖体检_2026-09-29.html", "最近一年覆盖体检", "覆盖率 34% 的假警报澄清（缺口在 2 个刷屏群）"),
  ("聊天记录分析_文件盘点与清理建议_2026-09-30.html", "聊天记录文件盘点", "三档清理建议（保守 / 中等 / 彻底）"),
  ("WeFlow替代流程_速查卡_2026-10-04.html", "WeFlow 替代流程速查卡", "ChatTrace 三层链路的操作卡"),
 ]),
 ("F", "深度理解与理论", "「他为什么是这样」—— 解释层", [
  ("深度理解盘点_全维度_2026-10-04.html", "深度理解盘点（全维度）", "全维度理解度自测"),
  ("深度理解_加速清单.html", "深度理解加速清单", "还差什么、怎么补"),
  ("深度破解_我执的投射几何.html", "我执的投射几何", "核心人格的几何化解释"),
  ("唯识架构×微信数据_深度结合突破报告.html", "唯识 × 微信数据", "理论框架与数据的结合"),
  ("宗教化意识分层_理论溯源研究.html", "宗教化意识分层溯源", "理论溯源研究"),
 ]),
 ("G", "前史与工具", "「2017 之前 + 本机工具」", [
  ("P0前史_2017-2024_并入报告.html", "P0 前史 2017–2024", "转专业起点在 2021（剑桥版画展翻译志愿者）"),
  ("P0事件级_可行性验证_本机文件扫描.html", "P0 事件级可行性验证", "本机文件扫描结论：P0 事件级 ≈ 0%"),
  ("事件复核台.html", "事件复核台", "人工过一遍事件库"),
  ("C盘空间清理方案_2026-10-01.html", "C 盘清理方案", "十维空间盘点 + 清理方案"),
  ("C盘清理执行报告_2026-10-01.html", "C 盘清理执行报告", "净释放 23.8 GB（9.0 → 32.8 GB）"),
 ]),
 ("H", "对外产出 · 汇报材料", "「考上央美之后我做过什么」—— 面向中期汇报的成果与素材", [
  ("央美之后_中期汇报可用成果与材料_2026-10-05.html", "中期汇报可用成果与材料 📋", "★ 四入口广搜（事件库 / 项目文件 / 照片作品 / 公开报道）→ 候选成果总表 46 项 · 8 条线（学习 / 工作站 / 澜沧 / 学术会务 / 实习教学 / 组织活动 / 研究实验 / 摄影影像）· 原清单没有的 9 项 · 今日优先讲 8 项 · 素材索引 · 汇报主线「学→用→教→研」+ 每项两三句话 · 5 个补充问题 · 口径与限制"),
 ]),
]

# ============================================================
# 二、CSV 数据表
# ============================================================
CSV_TABLE = [
 ("events_merged.csv", "事件库源（工作区版）", "事件抽取的合并源，喂给引擎 build_event_layer.py"),
 ("events_candidates.csv", "事件候选", "抽取出的候选事件"),
 ("events_review.csv", "事件复核", "人工复核用"),
 ("交叉主表_2026-10-04.csv", "8 源交叉主表", "42,717 人 × 18 列"),
 ("全库距离预标定_2026-10-04.csv", "全库距离预标定", "1,792 行（预标定，非裁定）"),
 ("补标_29人距离表.csv", "★ 第二锚点", "29 人人工标定 —— 距离地图的裁定依据"),
 ("补标_井邻线距离表.csv", "★ 第三锚点", "井邻线 16 人人工标定"),
 ("距离档复核清单_2026-10-04.csv", "距离档复核清单", "待人工复核项"),
 ("file_density.csv", "文件密度扫描", "本机文件按目录密度"),
 ("personal_density.csv", "个人消息密度", "按人消息量密度"),
 ("vault_link_report.csv", "Obsidian 断链报告", "check_vault_links.py 产出"),
]

# ============================================================
# 三、引擎（裁定层 · 数字唯一出处）
# ============================================================
ENGINE_REF = [
 ("00-真相源·数字基准.md", "★ 数字唯一真相源", "所有数字必须从这里引用（加载协议第 ⓪ 位）"),
 ("01-人格核心.md", "人格核心", "我执 / 三态 / 距离定律"),
 ("02-读人协议.md", "读人协议", "怎么判一个人的距离与性质"),
 ("03-读对话协议.md", "读对话协议", "怎么读一段对话"),
 ("04-人际地图.md", "人际地图", "54 人距离地图说明"),
 ("05-纠偏层.md", "★★ 纠偏层（唯一裁定记录处）", "所有裁定写这里；引用前必读"),
 ("06-理解度自测.md", "理解度自测", "读到什么程度算读懂"),
 ("07-事件档案.md", "事件档案", "2,864 事件 / 5 阶段 / 9 条因果链"),
 ("08-读事件协议.md", "读事件协议", "怎么读一个事件"),
 ("09-无人时档案.md", "无人时档案", "朋友圈 / 搜索 / 收藏"),
 ("事件库.csv", "★ 事件库", "2,864 条"),
 ("距离地图.csv", "★ 距离地图", "98 人（三锚点合成）"),
 ("距离地图_全库.csv", "距离地图（全库）", "1,792 行"),
]

# ============================================================
# 四、Obsidian 分区
# ============================================================
VAULT_AREAS = [
 ("01_个人信息", "个人档案 · 画像 · 打通页", 21),
 ("02_文件名录", "本机文件位置清单", 13),
 ("03_微信聊天分析/01_人物档案", "458 人画像", 458),
 ("03_微信聊天分析/02_情感线", "情感线总谱 · 关系熵", 6),
 ("03_微信聊天分析/03_事件库", "事件库笔记 + 逐日全维（25 篇）", 11 + 25),
 ("03_微信聊天分析/04_方法论", "方法总览 · 三态 · 五层结构", 9),
 ("03_微信聊天分析/05_资产与管道", "数据源 · 流水线 · 复刻手册", 13),
 ("03_微信聊天分析/06_待办与风险", "噪音群 · Agent 通道 · 失效模式", 4),
 ("03_微信聊天分析/07_贯通与觉悟", "八源闭环 · 总贯通 · 三点一觉悟", 3),
 ("03_微信聊天分析/_附件", "49 份 HTML 报告副本", 49),
]

# ============================================================
# 生成
# ============================================================
def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def furl(p):
    return "file:///" + urllib.parse.quote(p.replace("\\", "/"))

# ---- 统计 ----
htmls = sorted(glob.glob(os.path.join(WS, "*.html")))
csvs = sorted(glob.glob(os.path.join(WS, "*.csv")))
pys_root = sorted(glob.glob(os.path.join(WS, "*.py")))
pys_tools = sorted(glob.glob(os.path.join(WS, "tools", "*.py")))
tmp_files = sorted(glob.glob(os.path.join(WS, "_tmp", "*")))
eng_files = sorted(glob.glob(os.path.join(ENGINE, "references", "*")))

H = []
A = H.append
A('''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>分析总览 · 全部文件地图</title><style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1e;--ink2:#4a4a4f;--ink3:#8a8a90;--line:#e5e5e2;
--red:#c0392b;--blue:#1f5c8b;--green:#1e7a52;--amber:#9a6b00;--purple:#5b4b8a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:48px 28px 80px}
h1{font-size:30px;line-height:1.3;margin:0 0 6px;letter-spacing:-.4px}
.sub{color:var(--ink3);font-size:13.5px;margin-bottom:30px}
h2{font-size:20px;margin:44px 0 8px;padding-bottom:9px;border-bottom:2px solid var(--ink)}
h3{font-size:15px;margin:24px 0 8px;color:var(--ink2)}
p{margin:10px 0}
.lead{background:var(--card);border-left:4px solid var(--red);border-radius:0 10px 10px 0;padding:18px 22px;margin:20px 0 26px}
.lead b{color:var(--red)}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi .n{font-size:23px;font-weight:700;letter-spacing:-.5px}
.kpi .l{font-size:12px;color:var(--ink3);margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}
th{text-align:left;background:#fafaf8;color:var(--ink2);font-weight:600;padding:8px 9px;border-bottom:2px solid var(--line);white-space:nowrap}
td{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
a{color:var(--blue);text-decoration:none;border-bottom:1px solid #cddced}
a:hover{background:#eff5fa}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink3);font-size:12px}
.gtitle{font-size:17px;font-weight:700;margin:32px 0 4px;letter-spacing:-.2px}
.gsub{font-size:13px;color:var(--ink3);margin-bottom:10px}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}
.t-red{background:#fdf2f0;color:var(--red)}.t-blue{background:#eff5fa;color:var(--blue)}
.t-green{background:#eef7f2;color:var(--green)}.t-amber{background:#fdf6e6;color:var(--amber)}
.t-purple{background:#f2effa;color:var(--purple)}.t-gray{background:#f0f0ee;color:var(--ink3)}
.warn{background:#fdf6e6;border:1px solid #f0e0b0;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.warn b{color:var(--amber)}
.foot{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink3);font-size:12.5px}
code{background:#f0f0ee;padding:1px 5px;border-radius:4px;font-size:12.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:12px 0}
@media(max-width:760px){.grid4{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="wrap">''')

A('<h1>分析总览 · 全部文件地图</h1>')
A('<div class="sub">一处找到所有分析产物 ｜ 2026-10-04 ｜ 工作区 · Obsidian · 引擎 三层全清单</div>')

A('''<div class="lead"><b>怎么用这一页：</b>三类找法 ——<br>
① <b>按主题找报告</b> → 第一~七节（40 份 HTML，<b>点标题直接打开</b>）<br>
② <b>按知识库找笔记</b> → 第八节（Obsidian 9 个分区）<br>
③ <b>找数字的出处</b> → 第九节（引擎 references，<b>所有数字只能从这里引用</b>）<br><br>
<b>⚠️ 红线：</b>本页所列文件含<b>真人姓名与金额</b>，<b>仅本机留存，不得外传</b>。</div>''')

A('<div class="grid4">')
for n, l in [("%d" % len(htmls), "HTML 报告"),
              ("%d" % (len(csvs) + 3), "CSV 数据表"),
              ("%d" % len(eng_files), "引擎文件"),
              ("%d" % 25, "逐日全维分册")]:
    A('<div class="kpi"><div class="n">%s</div><div class="l">%s</div></div>' % (n, l))
A('</div>')

# ---- 一~七：HTML 分组 ----
A('<h2>一 ~ 七、40 份 HTML 报告（按主题）</h2>')
A('<p>全部位于 <code>%s</code>。点标题直接打开。</p>' % esc(WS))
for gi, (code, title, sub, items) in enumerate(GROUPS, 1):
    A('<div class="gtitle">%s. %s <span class="tag t-gray">%d 份</span></div>' % (code, esc(title), len(items)))
    A('<div class="gsub">%s</div>' % esc(sub))
    A('<table><tr><th style="width:34%">报告</th><th style="width:22%">一句话</th><th>内容</th><th class="num">大小</th></tr>')
    for fn, name, desc in items:
        p = os.path.join(WS, fn)
        sz = kb(size_of(p)) if os.path.exists(p) else "缺失"
        A('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td class="num">%s</td></tr>'
          % (furl(p), esc(name), esc(desc), esc(fn), sz))
    A('</table>')

# ---- 八：CSV ----
A('<h2>八、CSV 数据表（%d 份）</h2>' % len(CSV_TABLE))
A('<table><tr><th style="width:30%">文件</th><th style="width:22%">作用</th><th>说明</th><th class="num">大小</th></tr>')
for fn, name, desc in CSV_TABLE:
    p = os.path.join(WS, fn)
    A('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td class="num">%s</td></tr>'
      % (furl(p), esc(name), esc(desc), esc(fn), kb(size_of(p))))
A('</table>')

# ---- 九：引擎 ----
A('<h2>九、引擎（裁定层 · 数字唯一出处）</h2>')
A('<p>路径 <code>%s</code>。★ 规矩：<b>所有数字只能从 <code>00-真相源·数字基准.md</code> 引用；'
  '所有裁定只能写进 <code>05-纠偏层.md</code>。</b></p>' % esc(ENGINE))
A('<table><tr><th style="width:32%">文件</th><th style="width:26%">作用</th><th>说明</th><th class="num">大小</th></tr>')
for fn, name, desc in ENGINE_REF:
    p = os.path.join(ENGINE, "references", fn)
    A('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td class="num">%s</td></tr>'
      % (furl(p), esc(name), esc(desc), esc(fn), kb(size_of(p))))
A('</table>')
A('<h3>引擎脚本</h3><ul>')
for s, d in [("scripts/build_event_layer.py", "事件 × 距离 × 阶段 × 负荷"),
             ("scripts/rebuild_distance_map.py", "重建 98 人距离地图（三锚点 × 实时数据）"),
             ("scripts/understand.py", "实时判读"),
             ("SKILL.md", "引擎总说明（加载协议）")]:
    p = os.path.join(ENGINE, s.replace("/", os.sep))
    A('<li><a href="%s">%s</a> —— %s</li>' % (furl(p), esc(s), esc(d)))
A('</ul>')

# ---- 十：Obsidian ----
A('<h2>十、Obsidian 知识库（9 个分区）</h2>')
A('<p>路径 <code>%s</code>。入口：<code>🏠主页.md</code> · <code>03_微信聊天分析/🎯成果总索引.md</code></p>' % esc(VAULT))
A('<table><tr><th style="width:40%">分区</th><th>内容</th><th class="num">篇数</th></tr>')
for path, desc, n in VAULT_AREAS:
    full = os.path.join(VAULT, path.replace("/", os.sep))
    A('<tr><td><a href="%s">%s</a></td><td>%s</td><td class="num">%s</td></tr>'
      % (furl(full), esc(path), esc(desc), n))
A('</table>')

# ---- 十一：脚本与临时数据 ----
A('<h2>十一、脚本与中间数据</h2>')
A('<h3>工作区根目录脚本（%d）</h3><ul>' % len(pys_root))
for p in pys_root:
    A('<li><a href="%s">%s</a></li>' % (furl(p), esc(os.path.basename(p))))
A('</ul>')
A('<h3>tools/ 脚本（%d）</h3><ul>' % len(pys_tools))
for p in pys_tools:
    A('<li><a href="%s">%s</a></li>' % (furl(p), esc(os.path.basename(p))))
A('</ul>')
A('<h3>_tmp/ 中间数据（%d 个文件）</h3>' % len(tmp_files))
A('<p>关键中间产物：</p><ul>')
for k, d in [("daily_master.csv", "★ 逐日全维主表（699 天 × 26 列）"),
             ("payment_flow.csv", "支付流 2,207 条"),
             ("jinglin_timeline.csv", "井邻线 515 条"),
             ("readable_full/", "可读文本 752 份"),
             ("readable/", "可读文本 91 份（旧）")]:
    p = os.path.join(WS, "_tmp", k.rstrip("/"))
    A('<li><a href="%s">%s</a> —— %s</li>' % (furl(p), esc(k), esc(d)))
A('</ul>')

# ---- 十二：三种找法 ----
A('''<h2>十二、三种找法（速查）</h2>
<div class="card">
<b>① 我想知道「某天发生了什么」</b><br>
→ 打开 <code>_tmp\\daily_master.csv</code> 查对应行；或看 Obsidian <code>03_事件库\\逐日全维\\YYYY-MM.md</code>
</div>
<div class="card">
<b>② 我想知道「某个主题的分析在哪」</b><br>
→ 第一~七节按主题分组；Obsidian 侧看 <code>🎯成果总索引.md</code>
</div>
<div class="card">
<b>③ 我想引用一个数字（写材料 / 做判断）</b><br>
→ 必须查引擎 <code>00-真相源·数字基准.md</code>，并跑它给的复算命令。禁止从旧 HTML 复制数字。
</div>
<div class="warn"><b>两条维护规矩：</b>
<ol style="margin:6px 0 0;padding-left:20px">
<li><b>新增报告 → 同步三处</b>：本页 + <code>🗂️事件库总索引.md</code> + <code>🎯成果总索引.md</code></li>
<li><b>数字变了 → 先改引擎真相源</b>，再往下改（顺序：引擎 → SKILL → 04/07 → CSV → Obsidian → HTML）</li>
</ol></div>''')

# ---- 十三：给任何 AI 的接入 ----
A('<h2>十三、给任何 AI 的接入（别的 harness 也能读）</h2>')
A('''<p>这套体系的文件全是<b>纯 markdown / CSV</b> —— <b>任何能读本地文件的 AI 都能接</b>
（Claude Code / Cursor / Windsurf / Cline / Roo / Codex CLI / Aider / 本地 Ollama）。缺的只是一份「接入说明」。</p>
<div class="card"><b>📄 接入说明文件</b><br>
· Obsidian：<code>🤖AI接入说明.md</code>（Vault 根目录）<br>
· 工作区：<code>AI接入说明.md</code><br>
内容：三层路径 + 读取顺序（3 梯队）+ <b>五条硬规则</b> + <b>可直接粘贴的提示词</b> + 各 harness 接法</div>
<div class="card"><b>可粘贴提示词（Claude Code / Cursor / Cline）</b>
<pre style="background:#f7f7f5;border:1px solid var(--line);border-radius:6px;padding:12px;font-size:12.5px;overflow-x:auto;margin:8px 0">请先按顺序读这三个文件，读完再回答我：
1. C:\\Users\\wardc\\Documents\\Obsidian Vault\\01_个人信息\\⭐个人使用画像.md
2. C:\\Users\\wardc\\.workbuddy-ai\\skills\\self-understanding-engine\\references\\00-真相源·数字基准.md
3. C:\\Users\\wardc\\.workbuddy-ai\\skills\\self-understanding-engine\\references\\05-纠偏层.md

规则：所有数字只能从第 2 个文件引用；所有结论先查第 3 个文件；
聊天内容不得上传到任何服务器。</pre></div>
<div class="warn"><b>为什么别的 harness 读不到引擎</b>：引擎在 <code>~/.workbuddy-ai\\skills\\</code> 下，
是 WorkBuddy 专属路径，别的工具<b>不会自动扫</b>。两条路：<br>
① <b>手动给路径</b>（最简单，见上面提示词）<br>
② <b>建目录联接</b>把引擎挂进 Vault（一次命令永久生效）：<br>
<code>mklink /J "C:\\Users\\wardc\\Documents\\Obsidian Vault\\00_引擎镜像" "C:\\Users\\wardc\\.workbuddy-ai\\skills\\self-understanding-engine\\references"</code></div>
<div class="warn"><b>⚠️ 网页版 AI（ChatGPT / Claude 网页）绝对不要上传聊天原文</b> ——
只上传 <code>⭐个人使用画像.md</code>（不含聊天内容）和需要引用的具体报告。</div>''')

A('''<div class="foot">
本页含真人姓名与金额，<b>不得外传</b>。原始数据全程本地处理（索引库 <code>mode=ro</code> 只读）。<br>
生成：<code>tools\\build_master_index.py</code>（只读扫描）｜ Obsidian 版：<code>03_微信聊天分析\\🗺️分析总览·全部文件地图.md</code>
</div></div></body></html>''')

io.open(OUT_HTML, "w", encoding="utf-8").write("\n".join(H))
print("HTML → %s（%d 字节）" % (OUT_HTML, os.path.getsize(OUT_HTML)))

# ============================================================
# Obsidian 版（wikilink）
# ============================================================
L = []
B = L.append
B("---")
B("tags: [索引, 总览, 导航]")
B("created: 2026-10-04")
B("updated: 2026-10-04")
B("priority: 高")
B("---")
B("")
B("# 🗺️ 分析总览 · 全部文件地图")
B("")
B("> **为什么有这一页**：产物散在三处（工作区 HTML / 本库笔记 / 引擎 references），")
B("> 没有一个**能一处找全**的入口。本页就是那个入口。")
B("")
B("[[🎯成果总索引]] ｜ [[00_微信聊天分析总览]] ｜ [[自我理解引擎·打通页]] ｜ [[🗂️事件库总索引]]")
B("")
B("---")
B("")
B("## 一、40 份 HTML 报告（工作区）")
B("")
B("路径：`C:\\Users\\wardc\\WorkBuddy AI\\2026-09-28-06-58-18\\`")
B("")
for code, title, sub, items in GROUPS:
    B("### %s. %s（%d 份）" % (code, title, len(items)))
    B("")
    B("> %s" % sub)
    B("")
    B("| 报告 | 一句话 |")
    B("|---|---|")
    for fn, name, desc in items:
        B("| `%s` | **%s** —— %s |" % (fn, name, desc))
    B("")
B("---")
B("")
B("## 二、CSV 数据表")
B("")
B("| 文件 | 作用 | 说明 |")
B("|---|---|---|")
for fn, name, desc in CSV_TABLE:
    B("| `%s` | %s | %s |" % (fn, name, desc))
B("")
B("---")
B("")
B("## 三、引擎（裁定层 · 数字唯一出处）")
B("")
B("路径：`C:\\Users\\wardc\\.workbuddy-ai\\skills\\self-understanding-engine\\references\\`")
B("")
B("| 文件 | 作用 | 说明 |")
B("|---|---|---|")
for fn, name, desc in ENGINE_REF:
    B("| `%s` | %s | %s |" % (fn, name, desc))
B("")
B("**★ 两条铁律**：① 数字只从 `00-真相源·数字基准.md` 出 ② 裁定只写进 `05-纠偏层.md`")
B("")
B("---")
B("")
B("## 四、本库分区（9 个）")
B("")
B("| 分区 | 内容 | 篇数 |")
B("|---|---|---:|")
for path, desc, n in VAULT_AREAS:
    B("| `%s` | %s | %s |" % (path, desc, n))
B("")
B("---")
B("")
B("## 五、三种找法")
B("")
B("1. **「某天发生了什么」** → `_tmp\\daily_master.csv` ｜ 或 [[逐日全维/00_逐日全维整合·总索引\\|逐日全维]] 的 `YYYY-MM.md`")
B("2. **「某主题的分析在哪」** → 本页第一节 ｜ 或 [[🎯成果总索引]]")
B("3. **「引用一个数字」** → 必须查引擎 `00-真相源·数字基准.md` + 跑复算命令，**禁止从旧 HTML 复制**")
B("")
B("---")
B("")
B("## 六、给任何 AI 的接入（别的 harness）")
B("")
B("文件全是**纯 markdown / CSV** → **任何能读本地文件的 AI 都能接**"
  "（Claude Code / Cursor / Cline / Codex CLI / Aider / 本地 Ollama）。")
B("")
B("**完整说明 → [[🤖AI接入说明]]**（Vault 根目录；工作区另有 `AI接入说明.md`）")
B("")
B("| 项 | 内容 |")
B("|---|---|")
B("| 第一梯队（必读） | `⭐个人使用画像.md` · 引擎 `00-真相源·数字基准.md` · 引擎 `05-纠偏层.md` |")
B("| 第二梯队（按需） | 引擎 `01-人格核心` · `04-人际地图` · `07-事件档案` · `09-无人时档案` |")
B("| 第三梯队（找东西） | [[🗺️分析总览·全部文件地图]] · [[🏠主页]] · [[🎯成果总索引]] |")
B("")
B("**★ 注意**：引擎在 `~/.workbuddy-ai\\skills\\` 下，**别的 harness 不会自动扫** —— 需手动给路径，或建目录联接。")
B("")
B("---")
B("")
B("## 七、维护规矩")
B("")
B("1. **新增报告 → 同步三处**：本页 + [[🗂️事件库总索引]] + [[🎯成果总索引]]")
B("2. **数字变了 → 先改引擎真相源**，顺序：引擎 → SKILL → 04/07 → CSV → Obsidian → HTML")
B("3. **报告不得外传**（含真人姓名与金额）")
B("")
B("---")
B("")
B("> 生成：`tools\\build_master_index.py`（只读扫描）｜ HTML 版：`分析总览_全部文件地图_2026-10-04.html`")

io.open(OUT_MD, "w", encoding="utf-8").write("\n".join(L))
print("Obsidian → %s" % OUT_MD)
