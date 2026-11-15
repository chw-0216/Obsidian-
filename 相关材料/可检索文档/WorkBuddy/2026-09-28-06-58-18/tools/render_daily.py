# -*- coding: utf-8 -*-
"""
render_daily.py —— 逐日全维整合：出 HTML 报告 + Obsidian 分册（只读 daily_master.csv）

输入：_tmp/daily_master.csv（699 天 × 26 列）
输出：
  WS\逐日全维整合_2024-11至2026-10_2026-10-04.html
  Obsidian\03_微信聊天分析\03_事件库\逐日全维\00_逐日全维整合·总索引.md
  Obsidian\03_微信聊天分析\03_事件库\逐日全维\YYYY-MM.md（按月分册）
"""
import csv, io, os, html
from collections import defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault\03_微信聊天分析\03_事件库\逐日全维"
SRC = os.path.join(WS, "_tmp", "daily_master.csv")
OUT_HTML = os.path.join(WS, "逐日全维整合_2024-11至2026-10_2026-10-04.html")

def f(x):
    try: return float(x or 0)
    except Exception: return 0.0
def i(x):
    try: return int(x or 0)
    except Exception: return 0

rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))
# 只保留 2024-11 起（索引库真实起点；之前是事件库越界残留）
rows = [r for r in rows if r["日期"] >= "2024-11-01"]

# ---------- 聚合 ----------
SPEC = {"井邻", "澜沧", "数字人", "校友会"}
def has_spec(r):
    return [p for p in (r["项目"] or "").split("、") if p in SPEC]

mo = defaultdict(lambda: {"天":0,"事":0,"A":0,"高":0,"支出":0.0,"消息":0,
                          "井邻":0,"澜沧":0,"数字人":0,"校友会":0})
for r in rows:
    v = mo[r["日期"][:7]]
    v["天"]+=1; v["事"]+=i(r["事件数"]); v["A"]+=i(r["A级"]); v["高"]+=i(r["高负荷"])
    v["支出"]+=f(r["支出"]); v["消息"]+=i(r["消息总"]); v["井邻"]+=i(r["井邻线"])
    for p in has_spec(r):
        v[p]+=1

hot4 = [r for r in rows if i(r["事件数"]) and i(r["支付笔数"]) and has_spec(r) and i(r["高负荷"])]
hot4.sort(key=lambda x: x["日期"])
top_ev = sorted(rows, key=lambda x: -i(x["事件数"]))[:12]
top_pay = sorted(rows, key=lambda x: -f(x["支出"]))[:12]
top_msg = sorted(rows, key=lambda x: -i(x["消息总"]))[:12]

def money(v):
    return "¥%s" % format(v, ",.0f")

def cell(x):
    return ('<span class="tag t-red">%d</span>' % x) if x else '<span style="color:#ccc">·</span>'

# ============================================================
# HTML
# ============================================================
maxev = max(v["事"] for v in mo.values()) or 1
maxpay = max(v["支出"] for v in mo.values()) or 1
maxmsg = max(v["消息"] for v in mo.values()) or 1

def bar(v, mx, cls=""):
    w = int(v / mx * 100) if mx else 0
    return '<div class="bar"><i class="%s" style="width:%d%%"></i></div>' % (cls, w)

H = []
A = H.append
A('''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>逐日全维整合 · 2024-11 → 2026-10</title><style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1e;--ink2:#4a4a4f;--ink3:#8a8a90;--line:#e5e5e2;
--red:#c0392b;--red-bg:#fdf2f0;--blue:#1f5c8b;--blue-bg:#eff5fa;--green:#1e7a52;--green-bg:#eef7f2;
--amber:#9a6b00;--amber-bg:#fdf6e6;--purple:#5b4b8a;--purple-bg:#f2effa}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:48px 28px 80px}
h1{font-size:30px;line-height:1.3;margin:0 0 6px;letter-spacing:-.4px}
.sub{color:var(--ink3);font-size:13.5px;margin-bottom:34px}
h2{font-size:20px;margin:44px 0 14px;padding-bottom:9px;border-bottom:2px solid var(--ink)}
h3{font-size:15.5px;margin:26px 0 10px;color:var(--ink2)}
p{margin:10px 0}
.lead{background:var(--card);border-left:4px solid var(--red);border-radius:0 10px 10px 0;padding:18px 22px;margin:20px 0 30px}
.lead b{color:var(--red)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}
table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}
th{text-align:left;background:#fafaf8;color:var(--ink2);font-weight:600;padding:8px 9px;border-bottom:2px solid var(--line);white-space:nowrap}
td{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.bar{height:7px;background:#eee;border-radius:4px;overflow:hidden;min-width:40px}
.bar i{display:block;height:100%;background:var(--blue)}
.bar i.r{background:var(--red)}.bar i.g{background:var(--green)}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}
.t-red{background:var(--red-bg);color:var(--red)}.t-blue{background:var(--blue-bg);color:var(--blue)}
.t-green{background:var(--green-bg);color:var(--green)}.t-amber{background:var(--amber-bg);color:var(--amber)}
.t-purple{background:var(--purple-bg);color:var(--purple)}.t-gray{background:#f0f0ee;color:var(--ink3)}
.hotday{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--red);border-radius:0 10px 10px 0;padding:14px 18px;margin:12px 0}
.hotday .d{font-size:15px;font-weight:700;letter-spacing:-.2px}
.hotday .meta{font-size:12px;color:var(--ink3);margin:3px 0 7px}
.hotday .ev{font-size:13px;color:var(--ink2);margin:3px 0}
.hotday .pl{font-size:12.5px;color:var(--ink3);margin-top:5px}
.warn{background:var(--amber-bg);border:1px solid #f0e0b0;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.warn b{color:var(--amber)}
.foot{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink3);font-size:12.5px}
code{background:#f0f0ee;padding:1px 5px;border-radius:4px;font-size:12.5px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi .n{font-size:23px;font-weight:700;letter-spacing:-.5px}
.kpi .l{font-size:12px;color:var(--ink3);margin-top:2px}
@media(max-width:700px){.grid4{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="wrap">''')

A('<h1>逐日全维整合 · 2024-11 → 2026-10</h1>')
A('<div class="sub">把此前所有「按主题」做的分析，全部拉平到「具体日期」这一条轴上 ｜ 2026-10-04 ｜ 699 天 × 26 列</div>')

A('''<div class="lead"><b>一句话：</b>此前的事件库、支付流、井邻线、距离地图、车与家教线都是<b>按主题</b>组织的，
彼此之间要靠人脑去对日期。本报告把它们<b>汇流到「一天一行」</b>，于是「钱与事不同步」这类结构，
第一次可以在<b>每一天</b>的层面直接看见。<br><br>
<b>汇流四源：</b>事件库 2,864 条 · 支付流 2,207 条 · 井邻线 515 条 · 索引库 692 天消息量。
<br><b>本轮新挖出：</b>信息密度最高的 <b>%d 天「四维同日」</b>（事＋钱＋专项项目＋高负荷），
以及一条此前完全没被识别的身份线 —— <b>格拉斯哥校友会运营者</b>。</div>''' % len(hot4))

A('<div class="grid4">')
for n, l in [("%d" % len(rows), "天（2024-11 起）"),
              ("%d" % sum(1 for r in rows if i(r["事件数"])), "有事件的天"),
              ("%d" % sum(1 for r in rows if i(r["支付笔数"])), "有钱的天"),
              ("%d" % len(hot4), "四维同日")]:
    A('<div class="kpi"><div class="n">%s</div><div class="l">%s</div></div>' % (n, l))
A('</div>')

# ---- 一、月度矩阵 ----
A('<h2>一、月度矩阵（29 个月）</h2>')
A('<p>每一行是一个月。三根条分别是<b>事件数 / 支出 / 消息量</b>。可以直接看出「哪个月事多、哪个月钱多、哪个月话多」三者并不同步。</p>')
A('<table><tr><th>月份</th><th class="num">天</th><th>事件</th><th class="num">A级</th><th class="num">高负荷</th>'
  '<th>支出</th><th>消息</th><th class="num">井邻</th><th class="num">澜沧</th>'
  '<th class="num">数字人</th><th class="num">校友会</th></tr>')
for k in sorted(mo):
    v = mo[k]
    A('<tr><td><b>%s</b></td><td class="num">%d</td>'
      '<td>%d %s</td><td class="num">%d</td><td class="num">%s</td>'
      '<td>%s %s</td><td>%d %s</td><td class="num">%s</td><td class="num">%s</td>'
      '<td class="num">%s</td><td class="num">%s</td></tr>' % (
        k, v["天"], v["事"], bar(v["事"], maxev), v["A"],
        ('<span class="tag t-red">%d</span>' % v["高"]) if v["高"] else "0",
        money(v["支出"]), bar(v["支出"], maxpay, "r"),
        v["消息"], bar(v["消息"], maxmsg, "g"),
        cell(v["井邻"]), cell(v["澜沧"]), cell(v["数字人"]), cell(v["校友会"])))
A('</table>')
A('<p style="font-size:12.5px;color:var(--ink3)">后四列 = 该月<b>有该专项线消息的天数</b>。'
  '四条线并不同步出现 —— 这正是「多线并行」在日期轴上的样子。</p>')

A('''<div class="warn"><b>三条读法：</b>
<ol style="margin:6px 0 0;padding-left:20px">
<li><b>2026-04 事最多（245）、2026-08 钱最多（¥28,418）</b> —— 两者几乎不相交。事多＝人在社交场；钱多＝人在生存场。</li>
<li><b>2024-11 → 2025-07 支出全为 ¥0</b> —— 不是没花钱，是<b>支付流起点在 2025-08-01</b>。这 9 个月是支付盲区。</li>
<li><b>井邻线 2025-10 起跳（106）、2026-07 峰值（137）</b> —— 与「驻村 → 开街」的节奏完全对应。</li>
</ol></div>''')

# ---- 二、13 天四维同日 ----
A('<h2>二、%d 天「四维同日」—— 信息密度最高</h2>' % len(hot4))
A('<p>筛选条件：<b>当天同时有事件 + 有支出 + 有专项项目（井邻/澜沧/数字人/校友会）+ 有高负荷事件</b>。'
  '全库 699 天里只有 %d 天满足 —— 这几天值得逐日精读。</p>' % len(hot4))
for r in hot4:
    sp = "、".join(has_spec(r))
    A('<div class="hotday"><div class="d">%s <span class="tag t-gray">%s</span> <span class="tag t-blue">%s</span></div>'
      '<div class="meta">事 %d（A %d / 高 %d） · 支出 %s（%d 笔） · 专项线 %s</div>'
      '<div class="ev">%s</div>'
      '<div class="pl">涉及：%s ｜ 最近距离：%s%s</div></div>' % (
        r["日期"], r["星期"], (r["阶段"] or "")[:10],
        i(r["事件数"]), i(r["A级"]), i(r["高负荷"]),
        money(f(r["支出"])), i(r["支付笔数"]), html.escape(sp or "—"),
        html.escape(r["事件摘要"][:200] or "—"),
        html.escape(r["涉及人"][:60] or "—"), r["最近距离"] or "—",
        (" ｜ 地：" + html.escape(r["地理"])) if r["地理"] else ""))

# ---- 三、TOP 榜 ----
A('<h2>三、TOP 榜</h2>')
A('<h3>事件最多 · 12 天</h3><table><tr><th>日期</th><th>星期</th><th class="num">事件</th><th class="num">A</th>'
  '<th class="num">高</th><th class="num">消息</th><th class="num">支出</th><th>项目</th></tr>')
for r in top_ev:
    A('<tr><td>%s</td><td>%s</td><td class="num"><b>%d</b></td><td class="num">%d</td><td class="num">%d</td>'
      '<td class="num">%d</td><td class="num">%s</td><td>%s</td></tr>' % (
        r["日期"], r["星期"], i(r["事件数"]), i(r["A级"]), i(r["高负荷"]),
        i(r["消息总"]), money(f(r["支出"])), html.escape(r["项目"][:26])))
A('</table>')

A('<h3>支出最高 · 12 天</h3><table><tr><th>日期</th><th>星期</th><th class="num">支出</th><th class="num">笔数</th>'
  '<th class="num">大额</th><th class="num">事件</th><th>摘要</th></tr>')
for r in top_pay:
    A('<tr><td>%s</td><td>%s</td><td class="num"><b>%s</b></td><td class="num">%d</td><td class="num">%d</td>'
      '<td class="num">%d</td><td>%s</td></tr>' % (
        r["日期"], r["星期"], money(f(r["支出"])), i(r["支付笔数"]), i(r["大额支出"]),
        i(r["事件数"]), html.escape(r["事件摘要"][:80])))
A('</table>')

A('<h3>消息最多 · 12 天</h3><table><tr><th>日期</th><th>星期</th><th class="num">消息</th><th class="num">我发</th>'
  '<th class="num">对方发</th><th class="num">会话数</th><th class="num">事件</th><th class="num">支出</th></tr>')
for r in top_msg:
    A('<tr><td>%s</td><td>%s</td><td class="num"><b>%d</b></td><td class="num">%d</td><td class="num">%d</td>'
      '<td class="num">%d</td><td class="num">%d</td><td class="num">%s</td></tr>' % (
        r["日期"], r["星期"], i(r["消息总"]), i(r["我发"]), i(r["对方发"]),
        i(r["会话数"]), i(r["事件数"]), money(f(r["支出"]))))
A('</table>')

# ---- 四、新发现 ----
A('<h2>四、★ 按日期整合挖出的两条新发现</h2>')
A('''<h3>发现 1｜2026-04-02 是他「校友会运营者」身份的集中爆发日</h3>
<div class="card">
<b>单日 77 事件 / 1,762 条消息 / 311 个会话 —— 全库最高密度日，是第二名的 2.5 倍。</b>
<p>把当天 77 条事件摊开看，其中 <b>约 70 条是同一件事</b>：格拉斯哥大学北京校友会
<b>《国富论》出版 250 周年经济思想史研讨会（4 月 7 日 · 北京大学）</b>的报名统筹 ——
「XX 已报名」「通过校友群添加好友」「确认入群」「填写问卷」。</p>
<ul style="margin:8px 0;padding-left:20px">
<li>核心协作方 <b>Sīrius R（周冉）</b> 当日 228 条（他发 101）—— 深夜密集沟通</li>
<li>事件原话：「在群通知中引导报名者主动添加微信，而非在报名表中收集微信号」（他在设计流程）</li>
<li>同日他还在：改井邻 PPT（导师否掉「社交货币」方案）· 与 Pink 谈贷款 · 约周末看极狐车</li>
</ul>
<p><b>此前所有分析都没识别出这条线</b> —— 因为它<b>不产生情感事件</b>，只产生「事务确认」，
而事件抽取源天然偏向有情绪落点的句子。</p>
</div>

<h3>发现 2｜「格拉斯哥校友会运营」是一条完整主线（2025-08 起）</h3>
<div class="card">
<dl style="margin:0;display:grid;grid-template-columns:130px 1fr;gap:5px 14px;font-size:13.5px">
<dt style="color:var(--ink3)">起点</dt><dd>2025-08-04 —— Sīrius R 一次性把他拉进「格拉斯哥大学北京校友会 1–7」<b>7 个群</b></dd>
<dt style="color:var(--ink3)">他的活</dt><dd><b>公众号运营（秀米）</b>：「我今晚就秀米把公众号信息做一版然后明天发学姐秀米」</dd>
<dt style="color:var(--ink3)">核心协作</dt><dd>Sīrius R <b>1,237 条</b>（他称「学姐」）· 格拉斯哥北京校友会 2026 群 1,304 条</dd>
<dt style="color:var(--ink3)">规模</dt><dd>「校友会」819 条 · 「格拉斯哥」1,160 条 · 7 个分会群 + 2026 群 + AI 校友会（4,400 条）</dd>
<dt style="color:var(--ink3)">峰值</dt><dd>2026-04-02（报名总协调）· 2026-04-07（北大研讨会）</dd>
</dl>
</div>
<p>这解释了此前的一个悬空判断 —— 「格拉斯哥北京校友会 9 个分群 = 唯一稳定归属」。
更准确的读法是：<b>他不在这些群里「找归属」，他在这些群里「干活」</b>。
这是一条<b>可运营的公共身份</b>，和井邻（学术项目）、澜沧（公益项目）并列，但性质不同：前两者有导师/母亲托底，这一条<b>是他自己接的活</b>。</p>''')

# ---- 五、边界 ----
A('''<h2>五、结构与边界</h2>
<div class="warn"><b>四条边界（不先排除会误读）：</b>
<ol style="margin:6px 0 0;padding-left:20px">
<li><b>2024-11 → 2025-07 支出为 ¥0 不是事实</b> —— 是支付流起点（2025-08-01）造成的盲区。</li>
<li><b>「事件数」不等于「当天的重要性」</b> —— 2026-04-02 有 77 条，但其中 70 条是同一件事的报名确认。
事件数测的是<b>人际接触面</b>，不是<b>事件权重</b>。</li>
<li><b>「有事件的天」只有 548/699</b> —— 剩下 151 天不是空白，是<b>抽取源没覆盖</b>（源 A/B 只跑到 2026-07）。</li>
<li><b>项目词是启发式命中，且已剔除刷屏群</b> —— 「他 0 发言的群」被排除。
实测：北京家教信息群里家教单的【地点】含「怀柔」→ 会被误判成井邻线，
<b>此项修正把井邻线从 968 条降到 515 条（−47%）</b>。同理「澜沧」曾误命中「二十届三中全会」。</li>
</ol></div>

<h3>怎么用这张表</h3>
<ul>
<li><b>想知道「某天发生了什么」</b> → 直接查 <code>_tmp\\daily_master.csv</code> 对应行</li>
<li><b>想找「信息密度最高的日子」</b> → 筛「四维同日」那 13 天</li>
<li><b>想验证某个结构</b> → 用月度矩阵看三根条是否同步</li>
<li><b>Obsidian 侧</b> → <code>03_微信聊天分析/03_事件库/逐日全维/</code>（总索引 + 按月分册）</li>
</ul>''')

A('''<div class="foot">
本报告含真人姓名与金额，<b>不得外传</b>。原始数据全程本地处理（索引库 <code>mode=ro</code> 只读）。
<br>主表：<code>_tmp/daily_master.csv</code>（699 天 × 26 列）｜ 脚本：<code>tools/build_daily_master.py</code> · <code>tools/render_daily.py</code>
<br>Obsidian：<code>03_微信聊天分析/03_事件库/逐日全维/</code>
</div></div></body></html>''')

io.open(OUT_HTML, "w", encoding="utf-8").write("\n".join(H))
print("HTML → %s（%d 字节）" % (OUT_HTML, os.path.getsize(OUT_HTML)))

# ============================================================
# Obsidian：总索引 + 按月分册
# ============================================================
os.makedirs(VAULT, exist_ok=True)

def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")

# 总索引
L = []
A2 = L.append
A2("---")
A2("tags: [事件库, 逐日, 整合, 索引]")
A2("created: 2026-10-04")
A2("updated: 2026-10-04")
A2("priority: 高")
A2("---")
A2("")
A2("# 🗓️ 逐日全维整合 · 总索引")
A2("")
A2("> **为什么有这一页**：事件库 / 支付流 / 井邻线 / 距离地图此前都是**按主题**组织的，")
A2("> 彼此要靠人脑对日期。本页把它们**汇流到「一天一行」** —— 于是「钱与事不同步」这类结构，")
A2("> 第一次能在**每一天**的层面直接看见。")
A2("")
A2("[[🗂️事件库总索引|← 事件库总索引]] ｜ [[🎯成果总索引]] ｜ [[井邻·洞台村·全打通 2026-10-04]] ｜ [[钱×事件·深度打通 2026-10-04]]")
A2("")
A2("---")
A2("")
A2("## 一、汇流四源")
A2("")
A2("| 源 | 量 | 粒度 |")
A2("|---|---|---|")
A2("| 事件库.csv | 2,864 条 | 548 天 |")
A2("| _tmp/payment_flow.csv | 2,207 条 | 297 天 |")
A2("| _tmp/jinglin_timeline.csv | 515 条 | 154 天 |")
A2("| index.sqlite 消息量 | 388,712 条 | 692 天 |")
A2("| **并集** | — | **699 天**（2023-10 越界 6 天已剔） |")
A2("")
A2("**主表**：`_tmp/daily_master.csv`（699 天 × 26 列）")
A2("**列**：日期 / 星期 / 阶段 / 消息总·我发·对方发·会话数 / 事件数·A级·B级·C级 / 高·中·低负荷 / 涉及人 / 最近距离 / 事件摘要 / 支出·收入·支付笔数·大额支出·支付类型 / 项目 / 地理 / 车牌 / 井邻线")
A2("")
A2("---")
A2("")
A2("## 二、月度矩阵")
A2("")
A2("| 月份 | 天 | 事件 | A级 | 高负荷 | 支出 | 消息 | 井邻 | 澜沧 | 数字人 | 校友会 |")
A2("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k in sorted(mo):
    v = mo[k]
    A2("| [[%s]] | %d | %d | %d | %d | %s | %s | %d | %d | %d | %d |" % (
        k, v["天"], v["事"], v["A"], v["高"], money(v["支出"]), format(v["消息"], ","),
        v["井邻"], v["澜沧"], v["数字人"], v["校友会"]))
A2("")
A2("> 后四列 = 该月**有该专项线消息的天数**。四条线并不同步出现 —— 这正是「多线并行」在日期轴上的样子。")
A2("")
A2("> ⚠️ 2024-11 → 2025-07 支出 ¥0 = **支付流盲区**（起点 2025-08-01），不是没花钱。")
A2("")
A2("---")
A2("")
A2("## 三、%d 天「四维同日」（事＋钱＋专项项目＋高负荷）" % len(hot4))
A2("")
A2("全库 699 天里只有 **%d 天**同时满足四个条件 —— **信息密度最高，值得逐日精读**。" % len(hot4))
A2("")
A2("| 日期 | 星期 | 事(A/高) | 支出 | 项目 | 事件摘要 |")
A2("|---|---|---|---:|---|---|")
for r in hot4:
    A2("| **%s** | %s | %d(%d/%d) | %s | %s | %s |" % (
        r["日期"], r["星期"], i(r["事件数"]), i(r["A级"]), i(r["高负荷"]),
        money(f(r["支出"])), esc(r["项目"])[:22], esc(r["事件摘要"])[:70]))
A2("")
A2("---")
A2("")
A2("## 四、TOP 榜")
A2("")
A2("### 事件最多 · 12 天")
A2("")
A2("| 日期 | 星期 | 事件 | A | 高 | 消息 | 支出 | 项目 |")
A2("|---|---|---:|---:|---:|---:|---:|---|")
for r in top_ev:
    A2("| %s | %s | **%d** | %d | %d | %s | %s | %s |" % (
        r["日期"], r["星期"], i(r["事件数"]), i(r["A级"]), i(r["高负荷"]),
        format(i(r["消息总"]), ","), money(f(r["支出"])), esc(r["项目"])[:22]))
A2("")
A2("### 支出最高 · 12 天")
A2("")
A2("| 日期 | 星期 | 支出 | 笔数 | 大额 | 事件 | 摘要 |")
A2("|---|---|---:|---:|---:|---:|---|")
for r in top_pay:
    A2("| %s | %s | **%s** | %d | %d | %d | %s |" % (
        r["日期"], r["星期"], money(f(r["支出"])), i(r["支付笔数"]), i(r["大额支出"]),
        i(r["事件数"]), esc(r["事件摘要"])[:60]))
A2("")
A2("### 消息最多 · 12 天")
A2("")
A2("| 日期 | 星期 | 消息 | 我发 | 对方发 | 会话 | 事件 | 支出 |")
A2("|---|---|---:|---:|---:|---:|---:|---:|")
for r in top_msg:
    A2("| %s | %s | **%s** | %s | %s | %d | %d | %s |" % (
        r["日期"], r["星期"], format(i(r["消息总"]), ","), format(i(r["我发"]), ","),
        format(i(r["对方发"]), ","), i(r["会话数"]), i(r["事件数"]), money(f(r["支出"]))))
A2("")
A2("---")
A2("")
A2("## 五、★ 按日期整合挖出的两条新发现")
A2("")
A2("### 发现 1｜2026-04-02 = 校友会报名总协调日（全库最高密度）")
A2("")
A2("**单日 77 事件 / 1,762 条消息 / 311 个会话 —— 第二名的 2.5 倍。**")
A2("")
A2("其中约 70 条是同一件事：格拉斯哥大学北京校友会 **《国富论》出版 250 周年经济思想史研讨会**（4 月 7 日 · 北京大学）的报名统筹。")
A2("")
A2("- 核心协作方 **Sīrius R（周冉）** 当日 228 条（他发 101）")
A2("- 事件原话：「在群通知中引导报名者主动添加微信，而非在报名表中收集微信号」（他在设计流程）")
A2("- 同日他还在：改井邻 PPT（导师否掉「社交货币」方案）· 与 Pink 谈贷款 · 约周末看极狐车")
A2("")
A2("→ **此前所有分析都没识别出这条线**，因为它**不产生情感事件**，只产生「事务确认」。")
A2("")
A2("### 发现 2｜「格拉斯哥校友会运营」是一条完整主线（2025-08 起）")
A2("")
A2("| 项 | 内容 |")
A2("|---|---|")
A2("| 起点 | 2025-08-04 —— Sīrius R 一次性把他拉进「格拉斯哥大学北京校友会 1–7」**7 个群** |")
A2("| 他的活 | **公众号运营（秀米）** |")
A2("| 核心协作 | Sīrius R **1,237 条**（他称「学姐」）· 北京校友会 2026 群 1,304 条 |")
A2("| 规模 | 「校友会」819 条 · 「格拉斯哥」1,160 条 · 7 分会群 + 2026 群 + AI 校友会 4,400 条 |")
A2("| 峰值 | 2026-04-02（报名总协调）· 2026-04-07（北大研讨会） |")
A2("")
A2("→ 修正此前判断：**他不是在这些群里「找归属」，他在这些群里「干活」**。")
A2("这是一条**可运营的公共身份** —— 与井邻（学术项目）、澜沧（公益项目）并列，但**前两者有导师/母亲托底，这一条是他自己接的活**。")
A2("")
A2("---")
A2("")
A2("## 六、边界（不先排除会误读）")
A2("")
A2("1. **2024-11 → 2025-07 支出 ¥0 不是事实** —— 是支付流起点（2025-08-01）造成的盲区。")
A2("2. **「事件数」≠「当天重要性」** —— 2026-04-02 有 77 条，但 70 条是同一件事的报名确认。事件数测的是**人际接触面**，不是**事件权重**。")
A2("3. **「有事件的天」只有 548/699** —— 剩下 151 天不是空白，是**抽取源没覆盖**（源 A/B 只跑到 2026-07）。")
A2("")
A2("---")
A2("")
A2("> ⚠️ 本页含真人姓名与金额，**仅本机**。")
A2("> 报告：`逐日全维整合_2024-11至2026-10_2026-10-04.html` ｜ 主表：`_tmp/daily_master.csv`")
A2("> 脚本：`tools/build_daily_master.py` · `tools/render_daily.py`（全只读）")

io.open(os.path.join(VAULT, "00_逐日全维整合·总索引.md"), "w", encoding="utf-8").write("\n".join(L))
print("Obsidian 总索引 → 00_逐日全维整合·总索引.md")

# 按月分册
bymonth = defaultdict(list)
for r in rows:
    bymonth[r["日期"][:7]].append(r)

cnt = 0
for k, rs in sorted(bymonth.items()):
    M = []
    B = M.append
    B("---")
    B("tags: [事件库, 逐日, %s]" % k)
    B("created: 2026-10-04")
    B("---")
    B("")
    B("# 🗓️ %s · 逐日全维" % k)
    B("")
    v = mo[k]
    B("> 天数 %d ｜ 事件 %d（A %d）｜ 高负荷 %d ｜ 支出 %s ｜ 消息 %s ｜ 井邻线 %d" % (
        v["天"], v["事"], v["A"], v["高"], money(v["支出"]), format(v["消息"], ","), v["井邻"]))
    B("")
    B("[[00_逐日全维整合·总索引|← 总索引]]")
    B("")
    B("| 日期 | 星期 | 事(A/高) | 支出 | 消息 | 项目 | 事件摘要 |")
    B("|---|---|---|---:|---:|---|---|")
    for r in sorted(rs, key=lambda x: x["日期"]):
        if not (i(r["事件数"]) or i(r["支付笔数"]) or r["井邻线"]):
            continue
        B("| %s | %s | %d(%d/%d) | %s | %s | %s | %s |" % (
            r["日期"][5:], r["星期"], i(r["事件数"]), i(r["A级"]), i(r["高负荷"]),
            money(f(r["支出"])) if f(r["支出"]) else "—",
            format(i(r["消息总"]), ",") if i(r["消息总"]) else "—",
            esc(r["项目"])[:20] or "—", esc(r["事件摘要"])[:80] or "—"))
    B("")
    B("> 数据：`_tmp/daily_master.csv` ｜ 总索引：[[00_逐日全维整合·总索引]]")
    io.open(os.path.join(VAULT, "%s.md" % k), "w", encoding="utf-8").write("\n".join(M))
    cnt += 1

print("Obsidian 按月分册 → %d 篇" % cnt)
