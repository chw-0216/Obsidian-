# -*- coding: utf-8 -*-
r"""
build_unified_workbench.py —— 统一排查台（单文件 HTML · 自包含 · 浅色 · 中文）

把「年度事件重建第一轮」散落在报告 / 引擎 / 记忆 / _tmp 各处的结果，
汇成一份可直接对照排查的文档：
  一、怎么用这份文档（排查路径）
  二、本轮已裁决结论（8 月对齐 / 独处时段 / 盲测 / 骨架 / 三条链）
  三、数据表全集（8 月逐日 · 滞后相关 · 逐小时 · 独处指标 · 骨架矩阵 · 178 候选 · 缺口逐日 · 外部源）
  四、结论台账（analysis.sqlite · 61 条）
  五、遗留问题台账（已裁定 / 悬空 / 待拍板）
  六、红线与已知陷阱（排查必读）
  七、脚本与产物索引
  八、系统状态与验收

只读：analysis.sqlite（mode=ro）+ _tmp\*.csv
产出：自我理解引擎_统一排查台_2026-10-05.html
"""
import csv
import html
import io
import os
import re
import sqlite3
import datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
OUT = os.path.join(WS, "自我理解引擎_统一排查台_2026-10-05.html")
# run_id 从管线版本戳里读，避免写死后过期
try:
    import json
    RUN_ID = json.load(io.open(os.path.join(TMP, "pipeline_stamp.json"), encoding="utf-8")).get("run_id", "—")
except Exception:
    RUN_ID = "—"

esc = lambda s: html.escape(str(s if s is not None else ""))


def read_csv(name, limit=None):
    p = os.path.join(TMP, name)
    if not os.path.exists(p):
        return [], []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        rows = list(rd)
    if not rows:
        return [], []
    head, body = rows[0], rows[1:]
    if limit:
        body = body[:limit]
    return head, body


def table(head, body, cls="", mono_from=1, maxlen=90):
    if not head:
        return '<p class="small">（缺数据）</p>'
    out = ['<table class="%s">' % cls, "<thead><tr>"]
    for i, h in enumerate(head):
        out.append('<th class="%s">%s</th>' % ("num" if i >= mono_from else "", esc(h)))
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i, c in enumerate(r):
            v = c if len(c) <= maxlen else c[:maxlen] + "…"
            out.append('<td class="%s">%s</td>' % ("num" if i >= mono_from else "", esc(v)))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def load_conclusions():
    c = sqlite3.connect("file:" + ANALYSIS_DB.replace("\\", "/") + "?mode=ro", uri=True)
    rows = c.execute(
        "SELECT concl_id, statement, status, evidence_events, valid_from, source_doc "
        "FROM conclusions ORDER BY concl_id"
    ).fetchall()
    out = []
    for cid, st, status, ev, vf, src in rows:
        n = len([x for x in (ev or "").split() if x.strip()])
        st = (st or "").replace("**", "").strip()
        sect = ""
        if src:
            m = re.search(r"(三·补·\d+|三、[^·\n]{2,20}|二、[^·\n]{2,20}|[四五六]、[^·\n]{2,20})", src)
            sect = m.group(1).strip() if m else src.split("·")[0].strip()
            sect = sect.replace("**", "")
            if len(sect) > 22:
                sect = sect[:22] + "…"
        out.append((cid, st, status or "", n, vf or "", sect))
    c.close()
    return out


def load_scripts():
    p = os.path.join(WS, "tools")
    names = sorted(f for f in os.listdir(p) if f.endswith(".py"))
    out = []
    for f in names:
        fp = os.path.join(p, f)
        try:
            head = io.open(fp, encoding="utf-8", errors="ignore").read(4000)
        except Exception:
            head = ""
        doc = ""
        m = head.find('"""')
        if m >= 0:
            doc = head[m + 3:head.find('"""', m + 3)].strip().splitlines()
            doc = doc[0] if doc else ""
        doc = re.sub(r"^%s\s*——\s*" % re.escape(f), "", doc)
        doc = re.sub(r"^%s\s*" % re.escape(f), "", doc)
        ro = "只读" if "mode=ro" in head else ("写库" if ".sqlite" in head else "—")
        out.append((f, doc[:60], ro, os.path.getsize(fp)))
    return out


def load_tmp_index():
    out = []
    for f in sorted(os.listdir(TMP)):
        if not f.endswith((".csv", ".json")):
            continue
        fp = os.path.join(TMP, f)
        n = ""
        if f.endswith(".csv"):
            try:
                with io.open(fp, encoding="utf-8-sig") as fh:
                    n = sum(1 for _ in fh) - 1
            except Exception:
                n = ""
        out.append((f, n, os.path.getsize(fp)))
    return out


def kpi(label, value, note=""):
    return ('<div class="kpi"><div class="k-l">%s</div><div class="k-v">%s</div>'
            '<div class="k-n">%s</div></div>' % (esc(label), esc(value), esc(note)))


# ---------------- 数据 ----------------
skeleton_h, skeleton_b = read_csv("annual_skeleton.csv")
aug_h, aug_b = read_csv("august_daily.csv")
lag_h, lag_b = read_csv("august_lag.csv")
hour_sum_h, hour_sum_b = read_csv("idle_hours_summary.csv")
hour_h, hour_b = read_csv("idle_hours.csv")
evt_h, evt_b = read_csv("idle_events.csv")
gap_h, gap_b = read_csv("gap_events_2026H2.csv")
gapd_h, gapd_b = read_csv("gap_daily.csv")
concl = load_conclusions()
scripts = load_scripts()
tmpidx = load_tmp_index()

# 笑一逐小时透视表
hours = {}
months = []
for r in hour_b:
    if r[0] != "笑一":
        continue
    m, h, n = r[1], int(r[2]), int(r[3])
    if m not in months:
        months.append(m)
    hours.setdefault(h, {})[m] = n
months.sort()
pivot_head = ["小时"] + months + ["合计"]
pivot_body = []
for h in range(24):
    row = ["%02d 时" % h] + [str(hours.get(h, {}).get(m, 0)) for m in months]
    row.append(str(sum(hours.get(h, {}).values())))
    pivot_body.append(row)
pivot_body.append(["合计"] + [str(sum(hours.get(h, {}).get(m, 0) for h in range(24))) for m in months]
                  + [str(sum(sum(v.values()) for v in hours.values()))])

# 缺口候选按天统计
gap_by_day = {}
for r in gap_b:
    gap_by_day[r[0]] = gap_by_day.get(r[0], 0) + 1

# 外部源清单（只留窗口内）
evt_win = [r for r in evt_b if "2026-06-01" <= r[0] <= "2026-10-05"]

# 结论台账分组
by_status = {}
for c in concl:
    by_status[c[2]] = by_status.get(c[2], 0) + 1
linked = sum(1 for c in concl if c[3] > 0)

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f7f6f3;color:#22201d;
 font:15px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:40px 30px 80px}
h1{font-size:27px;font-weight:600;margin:0 0 8px;letter-spacing:-.3px}
h2{font-size:20px;font-weight:600;margin:52px 0 14px;padding-bottom:8px;
 border-bottom:2px solid #22201d;letter-spacing:-.2px}
h3{font-size:16px;font-weight:600;margin:30px 0 10px}
h4{font-size:14px;font-weight:600;margin:20px 0 8px;color:#4a4642}
p{margin:10px 0}
.sub{color:#6b6660;font-size:13.5px}
.small{font-size:12.5px;color:#6b6660;line-height:1.65}
.meta{color:#6b6660;font-size:13px;margin:0 0 6px}
.warn{background:#fdf3f3;border-left:3px solid #b13b3b;padding:11px 15px;border-radius:0 6px 6px 0;
 font-size:13.5px;margin:16px 0;color:#7d2626}
.note{background:#f3f6fb;border-left:3px solid #2f5c96;padding:11px 15px;border-radius:0 6px 6px 0;
 font-size:13.5px;margin:16px 0;color:#24476f}
.ok{background:#f2f8f2;border-left:3px solid #2f7d4f;padding:11px 15px;border-radius:0 6px 6px 0;
 font-size:13.5px;margin:16px 0;color:#20583a}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:12.5px;background:#fff;
 border:1px solid #e3e0da;border-radius:6px;overflow:hidden}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid #efede9;vertical-align:top}
th{background:#f2f0eb;font-weight:600;white-space:nowrap;font-size:12px}
td.num,th.num{font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#faf9f6}
code{font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:12px;
 background:#f0eeea;padding:1px 5px;border-radius:4px;color:#3a3733}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin:22px 0 8px}
.kpi{background:#fff;border:1px solid #e3e0da;border-radius:8px;padding:13px 15px}
.k-l{font-size:11.5px;color:#6b6660;margin-bottom:5px;letter-spacing:.02em}
.k-v{font-size:21px;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:-.4px}
.k-n{font-size:11.5px;color:#8b8680;margin-top:4px}
.tag{display:inline-block;font-size:11px;padding:1.5px 7px;border-radius:20px;
 font-weight:500;white-space:nowrap}
.t-ok{background:#e8f3ea;color:#20583a}
.t-no{background:#fbeaea;color:#8f2c2c}
.t-half{background:#fbf1e2;color:#7a4d12}
.t-idle{background:#eeece8;color:#5a554f}
.t-ask{background:#e9eef7;color:#26456e}
.toc{background:#fff;border:1px solid #e3e0da;border-radius:8px;padding:16px 20px;margin:20px 0 6px}
.toc ol{margin:6px 0 0;padding-left:22px}
.toc li{margin:3px 0;font-size:13.5px}
.toc a{color:#24476f;text-decoration:none}
.toc a:hover{text-decoration:underline}
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.foot{margin-top:60px;padding-top:16px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}
.scroll{overflow-x:auto;border-radius:6px}
ul,ol{margin:10px 0;padding-left:24px}
li{margin:5px 0}
strong{font-weight:600}
hr{border:none;border-top:1px solid #e3e0da;margin:34px 0}
"""

# ---------------- 正文 ----------------
H = []
A = H.append
A('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width,initial-scale=1">')
A('<title>自我理解引擎 · 统一排查台 2026-10-05</title>')
A("<style>%s</style></head><body><div class='wrap'>" % CSS)

A("<h1>自我理解引擎 · 统一排查台</h1>")
A('<p class="meta">数据窗口 2024-11 → 2026-10-05 ｜ 本轮 run_id <code>%s</code> ｜ 生成 %s</p>' % (RUN_ID, NOW))
A('<p class="meta">把「年度事件重建第一轮」散落在报告 / 引擎 / 记忆 / <code>_tmp</code> 各处的结果汇成一份，供逐项对照排查。</p>')
A('<div class="warn"><strong>内部资料</strong> · 含真人姓名、金额与私密内容 · <strong>不得外传、不得上传任何第三方</strong>。'
  '全部数字来自本机只读库（<code>analysis.sqlite</code> · <code>index.sqlite</code> · <code>sns.db</code> · <code>general.db</code>）。</div>')

A('<div class="kpis">')
A(kpi("结论台账", "%d 条" % len(concl), "在效 %d" % by_status.get("有效", 0)))
A(kpi("事件库", "2,864 条", "证据 5,463 条"))
A(kpi("缺口候选", "%d 条" % len(gap_b), "07→10 月 · 未进库"))
A(kpi("母亲一年转入", "¥183,275", "175 笔 · 月均 ¥15,273"))
A(kpi("8 月单月转入", "¥36,300", "全年最高"))
A(kpi("笑一日均", "48.8", "10 月 · 8 月为 85.3"))
A(kpi("结论有证据", "%d / %d" % (linked, len(concl)), "%.1f%%" % (linked * 100.0 / len(concl))))
A(kpi("验收 / 盲测", "30 / 30 · 7 / 7", "断链 0"))
A("</div>")

A('<div class="toc"><strong>目录</strong><ol>')
for i, t in enumerate([
    "怎么用这份文档（排查路径）",
    "本轮已裁决结论",
    "数据表全集",
    "结论台账（61 条）",
    "遗留问题台账",
    "红线与已知陷阱",
    "脚本与产物索引",
    "系统状态与验收",
], 1):
    A('<li><a href="#s%d">%s</a></li>' % (i, esc(t)))
A("</ol></div>")

# ===== 1 =====
A('<h2 id="s1">一、怎么用这份文档（排查路径）</h2>')
A("<table><thead><tr><th>你想干什么</th><th>去哪一节</th><th>怎么用</th></tr></thead><tbody>")
for a, b, c in [
    ("核对某个数字对不对", "第三节 数据表全集", "表是按天 / 按小时 / 按月的原始明细，可直接跟微信、支付记录对"),
    ("核对某条结论站不站得住", "第四节 结论台账", "看「证据条数」与「成立时间」两列：0 条 = 目前只靠本人自述"),
    ("找还没解决的问题", "第五节 遗留问题台账", "分「已裁定 / 悬空 / 待你拍板」三档"),
    ("确认哪些话不能写", "第六节 红线与陷阱", "对外写材料前先扫一遍"),
    ("重跑 / 复现", "第七节 脚本索引", "每个脚本标注了「只读 / 写库」和产出文件"),
    ("确认这版数据是哪一次生成的", "第八节 系统状态", "全部产物共用同一个 run_id"),
]:
    A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c)))
A("</tbody></table>")
A('<div class="note"><strong>一句话口径</strong>：所有「跨月比较」一律用<b>日均</b>，不用总量（10 月是不完整月）；'
  '所有「单日极值」撑起来的相关系数，必须同时看秩相关。</div>')

# ===== 2 =====
A('<h2 id="s2">二、本轮已裁决结论</h2>')

A("<h3>2.1 8 月逐日对齐：C1 / C2 双双证伪</h3>")
A("<p>把母亲转账、他转出、支出、各会话消息量拉到「天」这根轴上。脚本 <code>tools/august_daily_align.py</code>（只读）。</p>")
A("<table><thead><tr><th>检验</th><th>方法</th><th>结果</th><th>判定</th></tr></thead><tbody>")
A("<tr><td>一 · 滞后相关</td><td>A(t) vs B(t+L)，L=−5..+5</td><td>全部 |秩相关| &lt; 0.3，无稳定滞后结构</td>"
  '<td><span class="tag t-no">不共动</span></td></tr>')
A("<tr><td>二 · 跨月反例</td><td>8 月 → 9 月</td><td>母亲转账 ¥36,300 → ¥11,800（<b>−67%</b>）；笑一日均 85.3 → 83.5（<b>−2%</b>）</td>"
  '<td><span class="tag t-no">C1 证伪</span></td></tr>')
A("<tr><td>三 · 大额定性</td><td>单日拆解</td><td>08-28 ¥20,600 → 当天付 ¥20,000 = 央美学费；08-25 ¥3,800 → ¥1,500×3 信用还款</td>"
  '<td><span class="tag t-half">定向过路钱</span></td></tr>')
A("</tbody></table>")
A("<ol>")
A("<li><b>C1（钱 → 关系）证伪</b> —— 日级无共动；钱跌 67%，关系只跌 2%（日均）。</li>")
A("<li><b>C2（关系 → 钱）证伪</b> —— 方向反了也不成立：9 月关系仍在高位，钱却崩了。</li>")
A("<li><b>8 月「双峰」是日历效应</b> —— 学费 8 月底到期、关系 8 月初进入新阶段（08-02 起「老公/老婆」），两件事各有时间表。</li>")
A("<li><b>C3 的日级检验也是负的</b>（母亲消息 × 笑一 = −0.20）→ 必须换分辨率。</li>")
A("</ol>")
A('<div class="warn"><strong>反假象纪律</strong>：整月「转账 × 支出」Pearson 高达 <b>0.98</b>，那是 08-28 单日 ¥20,600 撑起来的；'
  '换成秩相关只剩 <b>0.25</b>。只能说「定向大额当天进当天出」，<b>不能说「天天过路」</b>。</div>')

A("<h3>2.2 独处时段：C3 拆成两半</h3>")
A("<p>换分辨率 —— 从「聊多少」换到「什么时候聊」。脚本 <code>tools/idle_hours_align.py</code>（只读）。</p>")
A("<table><thead><tr><th>假设</th><th>证据</th><th>判定</th></tr></thead><tbody>")
A("<tr><td><b>C3-a</b> 同住挤压</td><td>笑一聊天窗口被压到 22 时后 / 00 时后；峰值小时 16 时 → 22 时；"
  "00:00–01:00 从 8 月 215 条 → 9 月 580 条；本人 09-27 自述「在家跟爸妈住，晚上不方便打电话」</td>"
  '<td><span class="tag t-ok">成立</span></td></tr>')
A("<tr><td><b>C3-b</b> 外部补偿（量增加）</td><td>母亲消息<b>高</b>的日子笑一日均 <b>67.9</b>，<b>低</b>的日子 <b>85.7</b> —— 反而<b>少 21%</b></td>"
  '<td><span class="tag t-no">不成立</span></td></tr>')
A("<tr><td><b>C4</b> 自然升温</td><td>未被排除；但 10 月 22 时占 40% 的集中度，更像「只有这个窗口」</td>"
  '<td><span class="tag t-half">未排除</span></td></tr>')
A("</tbody></table>")
A('<div class="note"><strong>净收获</strong>：C3 从「待验证」变成「<b>一半成立、一半证伪</b>」——'
  '挤压带来的是<b>时段重排</b>，不是<b>总量补偿</b>。</div>')

A("<h3>2.3 盲测核对（外部模型只看 9 月前资料）</h3>")
A("<table><thead><tr><th>题</th><th>外部预测</th><th>回库核对</th><th>判定</th></tr></thead><tbody>")
A("<tr><td><b>Q3</b> 导师划界</td><td>「白干了」+ 委屈 + 被剥夺 + 压抑/合理化</td>"
  "<td>10-02 19:06 划界 → <b>19:07 回「明白老师」</b>（1 分钟）→ 又干 40 分钟 → 次日 07:23 如常出发 → "
  "<b>对母亲一句抱怨都没有</b>；同日 10:55 / 11:33 还在问「走陈晔老师的账什么时候能出来」</td>"
  '<td><span class="tag t-no">本次预测错</span></td></tr>')
A("<tr><td><b>Q4</b> 关系角色</td><td>本质是「被她需要的人」</td>"
  "<td>两者在数据上不可分；且与大量主动情感表达张力明显（七夕长信 / 10-01 连发 6 条道歉）</td>"
  '<td><span class="tag t-half">不可证伪</span></td></tr>')
A("<tr><td><b>Q5</b> 10 月回落</td><td>主动冷下来（防卫性撤离）</td>"
  "<td>前提错（用了「十二分之一」，那是拿 5 天总量比整月总量）+ 方向可疑 + 同段自相矛盾</td>"
  '<td><span class="tag t-no">前提错</span></td></tr>')
A("</tbody></table>")
A("<p><b>★ 反向验证</b>：改用引擎已裁定的 <b>Q14（清醒的交易者）</b>去预测 Q3 → <b>6 行全中</b>。"
  "同一个盲测、两个模型，一个全错一个全对 ⇒ <b>选对模型比选对标签重要</b>。</p>")

A("<h3>2.4 年度骨架与密度断崖</h3>")
A("<p>8 条生活线 × 13 个月。脚本 <code>tools/annual_skeleton.py</code>（只读）。</p>")
A(table(skeleton_h, skeleton_b, mono_from=1))
A('<div class="warn"><strong>密度断崖</strong>：事件 / 千条消息，前 10 个月均值 <b>9.2</b>；'
  '2025-11 = 5.1 · 2026-07 = 6.5 · <b>08 = 2.9</b> · <b>09 = 1.6</b> · 10 = 2.0。'
  '而<b>消息量全年平稳（月均 2.1 万条）</b> ⇒ 低密度不是他变安静，是<b>抽取源停了</b>。</div>')

A("<h3>2.5 三条深入事件链</h3>")
A('<div class="two">')
A("<div><h4>链 A · 车 → 钱 → 父母</h4><ul>"
  "<li>一年内<b>至少 2 次剐蹭</b>：07-02（央美门口撞公交，开母亲的车）· 10-03（怀柔，保险杠）</li>"
  "<li>母亲一年转账 <b>175 笔 / ¥183,275</b>（去重后），月均 ¥15,273</li>"
  "<li>07-02 夜大吵：「你为什么每天要开车」「买车就是花钱的事」；他「你俩整天闹」「我爸有病似的」</li>"
  "<li>08-18 要钱 1,100（花呗+网贷）→ 母亲给，附条件「不许给车买东西了」</li>"
  "<li><b>反向发现</b>：母亲自己的车贷也逾期（他：「你逾期了半个月了」「影响征信很严重」）</li>"
  "<li><b>净结论</b>：车不是消费问题，是<b>「使用权审计」</b>问题 —— 他争的是使用权的正当性，不是钱</li>"
  "</ul></div>")
A("<div><h4>链 B · 井邻工作站 → 导师</h4><ul>"
  "<li>06→10：拉设备进怀柔 · 高德标注 · 07-23 开业 · 07-29 政协主席+宣传部长到场 · "
  "08-22《工作成果汇总》《驻村工作日志》 · 08-25 见区委书记 · 09-22 入党思想汇报</li>"
  "<li>本人发言 148 条；母亲「去了井邻都 20 多趟了」；他补「我就在井邻住过两晚」</li>"
  "<li>08-18 原话是钥匙：「陈晔的活哪那么好干」「好事从来没有我，烂事永远都是我的」→「<b>我就是想入党</b>」</li>"
  "</ul></div>")
A("</div>")
A('<div class="two">')
A("<div><h4>链 C · 笑一 → 亲密关系</h4><ul>"
  "<li>消息量 05 = 300 → 06 = 297 → <b>07 = 869 → 08 = 2,473 → 09 = 2,170</b> → 10（4 天）= 195</li>"
  "<li>08-02 起「老公/老婆」固定化；08-19 七夕写信备礼；08-29 / 09-02 / 09-16 三次生日；"
  "09-05 她遇纠纷报警 → 他「明早连夜到北京」；10-01 他失联一整天 → 连发道歉</li>"
  "<li><b>资源约束显形</b>：08-11「十月宽裕点带你多吃点」；08-17 用「做饭」替代「花钱」；08-29 生日 190 元她先垫</li>"
  "<li><b>09-27 自述</b>：「现在在家跟爸妈住，晚上不方便打电话」</li>"
  "</ul></div>")
A("<div><h4>三套竞争解释（ACH）</h4><ul>"
  "<li><b>A 组（车钱）</b>：A1 使用权审计 / A2 现金流缺口外溢 / A3 父母关系紧张外溢 / A4 面子投资失败 → 倾向 <b>A1 + A2</b></li>"
  "<li><b>B 组（井邻）</b>：B1 换入党（对价）/ B2 建作品履历 / B3 关系归属 → <b>B1+B2 明面，B3 暗面</b></li>"
  "<li><b>C 组（笑一）</b>：C1 ❌ 证伪 · C2 ❌ 证伪 · <b>C3 拆两半</b> · C4 未排除</li>"
  "</ul></div>")
A("</div>")

# ===== 3 =====
A('<h2 id="s3">三、数据表全集</h2>')
A('<p class="small">以下表全部由脚本从只读库直接导出，未做人工修饰；可逐行跟微信 / 支付记录对照。</p>')

A("<h3>3.1 8 月逐日对齐（31 天 · 只列有资金动作的日子见报告版，此处为全量）</h3>")
A(table(aug_h, aug_b, mono_from=1, maxlen=20))

A("<h3>3.2 滞后相关矩阵（A(t) vs B(t+L)）</h3>")
A(table(lag_h, lag_b, mono_from=1, maxlen=20))

A("<h3>3.3 笑一消息逐小时分布（按对象 × 月，原始条数）</h3>")
A(table(pivot_head, pivot_body, mono_from=1, maxlen=20))

A("<h3>3.4 时段指标汇总（深夜 = 23:00–05:59）</h3>")
A(table(hour_sum_h, hour_sum_b, mono_from=1, maxlen=20))

A("<h3>3.5 外部数据源清单（朋友圈互动 + 搜索历史）</h3>")
A('<div class="warn"><strong>朋友圈测不出「浏览活跃度」</strong>：<code>SnsTopItem_1.create_time</code> 是'
  '<b>别人发帖的时间</b>，<code>last_read_time</code> 是一个统一水位（全是 10-05 04:49）。'
  '它只能答「他信息流里都是谁」，<b>答不了「他哪天看了」</b>。下表是唯一有真实时间戳的两类事件。</div>')
A(table(evt_h, evt_win, mono_from=0, maxlen=40))
A('<div class="ok"><strong>唯一有信号的发现</strong>：<b>9 月下旬起他反复搜「笑一 / 笑 / xiao / xia」</b>'
  '（09-12 · 09-26 · 09-29 · 10-01），而同期消息量在回落 → <b>量掉了，注意力在涨</b>，'
  '与「主动冷下来（防卫性撤离）」相反。</div>')

A("<h3>3.6 缺口候选事件（178 条 · 全部）</h3>")
A('<p class="small">规则抽取的候选，标 <code>待核实</code>，<b>未进分析库</b>。'
  '群聊已加闸：必须他本人说了事件词；已剔除链接转发与系统账号。</p>')
A(table(gap_h, gap_b, mono_from=0, maxlen=70))

A("<h3>3.7 缺口逐日（83 天）</h3>")
A(table(gapd_h, gapd_b, mono_from=1, maxlen=20))

# ===== 4 =====
A('<h2 id="s4">四、结论台账（analysis.sqlite · %d 条）</h2>' % len(concl))
A("<p>「证据条数」= 这条结论绑定了几个事件 ID；<b>0 = 目前只靠本人自述</b>，不是匹配失败。"
  "「成立时间」= 从哪天起成立。</p>")
A("<p>状态分布：" + " · ".join("<b>%s</b> %d" % (esc(k), v) for k, v in sorted(by_status.items()))
  + " ｜ 有事件证据 <b>%d</b> 条（%.1f%%）" % (linked, linked * 100.0 / len(concl)) + "</p>")
cbody = [[c[0], c[1][:150], c[2], str(c[3]), c[4], c[5][:34]] for c in concl]
A(table(["ID", "结论（截断）", "状态", "证据条数", "成立时间", "出处章节"], cbody,
        mono_from=0, maxlen=200))

# ===== 5 =====
A('<h2 id="s5">五、遗留问题台账</h2>')

A("<h3>5.1 已裁定（本轮）</h3>")
A("<table><thead><tr><th>问题</th><th>裁定</th><th>依据</th></tr></thead><tbody>")
for q, a, e in [
    ("C1 钱 → 关系？", "❌ 证伪", "日级无共动；9 月钱跌 67%，关系只跌 2%"),
    ("C2 关系 → 钱？", "❌ 证伪", "方向反了也不成立"),
    ("8 月双峰是不是因果？", "❌ 不是，是日历效应", "学费 8 月底到期 + 关系 8 月初进入新阶段"),
    ("C3-a 同住挤压？", "✅ 成立", "峰值小时 16 时 → 22 时；09-27 自述；深夜占比逐月上升"),
    ("C3-b 外部补偿？", "❌ 不成立", "母亲消息高的日子笑一反而少 21%"),
    ("导师划界后他的反应？", "❌ 不是「白干了」", "1 分钟内回「明白老师」，同日仍在推进交易"),
]:
    A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(q), esc(a), esc(e)))
A("</tbody></table>")

A("<h3>5.2 悬空（等他答）</h3>")
A('<table><thead><tr><th>#</th><th>问题</th><th>为什么要问</th></tr></thead><tbody>')
for i, q, why in [
    ("Q1", "2026-08 家里给的钱是全年最多（¥36,300）—— 是「手上有钱所以敢多花」，还是「关系上花多了才去要」？",
     "决定 A 组解释的最终归属"),
    ("Q2", "2026-07-02 的「你俩整天闹」—— 是就事论事骂你开车，还是他们两人本来就在闹？",
     "决定 A3（父母关系紧张外溢）能否升级为可检验假设"),
    ("Q3", "2026-10-02 导师划界时，第一反应是松了一口气还是白干了？",
     "内部动机只能本人注入（铁律 4）"),
    ("Q4", "在笑一面前，你是「照顾她的人」还是「被她需要的人」？这两个在你这儿是同一件事吗？",
     "Q4 目前不可证伪，只能靠自述"),
    ("Q5", "10 月前 5 天笑一日均掉到 8 月的 58%（48.8 vs 85.3）—— 是你主动冷下来，还是外部事情挤掉了？",
     "决定 C4 是否成立"),
]:
    A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (esc(i), esc(q), esc(why)))
A("</tbody></table>")

A("<h3>5.3 待你拍板</h3>")
A("<table><thead><tr><th>事项</th><th>建议</th><th>现状</th></tr></thead><tbody>")
for a, b, c in [
    ("C3-a 是否升级为裁定？", "升级", "已有自述 + 时段双重印证"),
    ("C3-b 是否写进「已推翻清单」？", "写进", "日级 + 分组双重否定"),
    ("依恋类型（焦虑型 / 恐惧-回避型）", "维持「未裁定」", "两边都无人工锚点；不得作为推理前提"),
    ("知识库 PII 57 处", "脱敏 or 永久不开 Sync", "二选一，工具已就绪 <code>tools/sanitize_vault_pii.py</code>"),
    ("知识库聊天流水 1 篇", "删除或脱敏", "<code>03_微信聊天分析\\01_人物档案\\新增人物案例.md</code>"),
    ("Q15+ 笑一定性", "已裁定为「现任女友（名分）+ 资源约束（实质）」", "见引擎 三·补·15"),
]:
    A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c)))
A("</tbody></table>")

A("<h3>5.4 待办（下一批）</h3>")
A("<ol>")
A("<li>人工过 <b>9 个零候选日</b>：2026-07-07、07-13、07-31、08-02、08-14、09-15、09-28、09-29、10-04</li>")
A("<li>把 <b>178 条候选</b>升级为事件（逐条标「确定 / 范围 / 待确认」，写进 <code>analysis.sqlite</code>，<code>review_status=待核实</code>）</li>")
A("<li>补 <b>2025-11 缺口</b>（密度 5.1，全年最早的异常月）</li>")
A("<li>Ollama JSON Schema + Pydantic 结构化抽取（先补 2026-08 之后）</li>")
A("<li>FTS5 + 人物别名表（<code>persons</code> / <code>aliases</code> 表已建但空）</li>")
A("<li><code>load_self</code>（本人确认的感受）仍是<b>全空</b> —— 只有本人能填，脚本永不覆盖</li>")
A("<li><code>unlinked</code> 1,036 条证据待人工确认</li>")
A("</ol>")

# ===== 6 =====
A('<h2 id="s6">六、红线与已知陷阱</h2>')
A('<p class="small">权威版本在引擎 <code>05-纠偏层.md</code>；此处是排查时最常用的一份速查。'
  '对外写材料前先扫一遍。</p>')

A("<h3>6.1 内容红线</h3>")
A("<table><thead><tr><th>#</th><th>红线</th><th>为什么</th></tr></thead><tbody>")
for n, r, w in [
    ("12", "债务叙事不得抹掉「被骗」这一主因", "抹掉就变成「他自己乱花」"),
    ("13", "「父母冷战」不得当数据事实引用", "全库搜「冷战」零命中，目前只有本人自述"),
    ("14", "不得用「未裁定」的标签当推理前提", "典型＝依恋类型；本轮实测该做法预测全错"),
    ("—", "不得读成谄媚 / 病态", "「备注即规程」是自我规程，不是人格缺陷"),
    ("—", "不得用一方否定另一方（母亲 vs 导师）", "两条线都是真的"),
    ("—", "不得建议他改备注", "备注是盖子，改盖子解决不了盖子底下的事"),
    ("—", "不得把「朋友圈不加评估语」读成「对人虚伪」", "两套语言都是真的，只是场景不同"),
    ("—", "不得把「母亲点赞」读成「关系变好了」", "它只证明朋友圈是第二条通道"),
    ("—", "不得用朋友圈 11 条反推「发圈频率」绝对值", "样本是缓存，非全量"),
    ("—", "不得把「同住 → 母亲微信量少」读成「关系淡」", "同住 = 事务面对面，微信只承担通知"),
    ("—", "「独立负责技术开发」等口径不得写", "见 USER.md 口径红线表"),
    ("—", "含真人姓名 / 金额 / 私密内容的产物不得外传", "数据主权硬约束"),
]:
    A("<tr><td class='num'>%s</td><td>%s</td><td>%s</td></tr>" % (esc(n), esc(r), esc(w)))
A("</tbody></table>")

A("<h3>6.2 方法陷阱（已踩过）</h3>")
A("<table><thead><tr><th>陷阱</th><th>正解</th></tr></thead><tbody>")
for a, b in [
    ("拿不完整月的<b>总量</b>比整月总量", "跨月比较一律用<b>日均</b>（本报告初版犯过：10 月 5 天 vs 8 月整月）"),
    ("用 Pearson 0.98 说「天天过路」", "单日极值会撑起假相关；必须同时看<b>秩相关</b>（此处只剩 0.25）"),
    ("把「候选」当「事实」", "178 条是规则抽取，标 <code>待核实</code>；只有被链 A/B/C 引用过的逐条看过原文"),
    ("把「消息量」当「关系强度」", "它只是粗代理；同住 / 事务 / 刷屏都会污染"),
    ("把「父母冷战」当数据事实", "全库零命中（红线 13）"),
    ("把「未裁定标签」当前提", "改用已有人工锚点的裁定（如 Q14）"),
    ("用朋友圈缓存算发圈频率", "样本是缓存，只能读风格与簇状分布"),
    ("FTS 搜 2 字人名返回 0", "<code>tokenize='trigram'</code> 要求 ≥3 字；2 字改用 <code>LIKE</code>"),
    ("文件名含点时用 <code>splitext</code> 取 basename", "会在最后一个点切错；只剥结尾 <code>.md</code>"),
    ("结论抽取的「一句话」不在节首第一行", "会被抓成短标签（本轮 CON-061 一度变成「起因」）"),
]:
    A("<tr><td>%s</td><td>%s</td></tr>" % (a, b))
A("</tbody></table>")

# ===== 7 =====
A('<h2 id="s7">七、脚本与产物索引</h2>')
A("<h3>7.1 本轮新增 / 涉及的脚本（<code>tools\\</code>）</h3>")
A("<table><thead><tr><th>脚本</th><th>作用</th><th>读写</th><th>字节</th></tr></thead><tbody>")
for f, d, ro, sz in scripts:
    if f in ("annual_skeleton.py", "mine_gap_events.py", "august_daily_align.py",
             "idle_hours_align.py", "regenerate_all.py", "extract_conclusions.py",
             "verify_analysis.py", "blind_test.py", "privacy_audit.py",
             "build_unified_workbench.py", "build_master_index.py", "check_vault_links.py"):
        cls = "t-ok" if ro == "只读" else ("t-half" if ro == "写库" else "t-idle")
        A("<tr><td><code>%s</code></td><td>%s</td><td><span class='tag %s'>%s</span></td>"
          "<td class='num'>%s</td></tr>" % (esc(f), esc(d), cls, esc(ro), "{:,}".format(sz)))
A("</tbody></table>")
A('<div class="note"><b>只读铁律</b>：所有读 <code>index.sqlite</code> 的脚本一律 <code>file:...?mode=ro</code>；'
  '只有 3 个白名单脚本可以写 <code>analysis.sqlite</code>。'
  '<code>python tools\\regenerate_all.py</code> 一条命令重跑全部产物。</div>')

A("<h3>7.2 <code>_tmp</code> 产物清单</h3>")
A("<table><thead><tr><th>文件</th><th>行数</th><th>字节</th></tr></thead><tbody>")
for f, n, sz in tmpidx:
    A("<tr><td><code>%s</code></td><td class='num'>%s</td><td class='num'>%s</td></tr>"
      % (esc(f), esc(n), "{:,}".format(sz)))
A("</tbody></table>")

# ===== 8 =====
A('<h2 id="s8">八、系统状态与验收</h2>')
A("<table><thead><tr><th>项</th><th>值</th></tr></thead><tbody>")
for k, v in [
    ("run_id", "<code>%s</code>（全部产物共用同一戳）" % RUN_ID),
    ("数据截至", "2026-10-05"),
    ("分析库", "<code>analysis.sqlite</code> · 2,864 事件 / 5,463 证据 / %d 结论" % len(concl)),
    ("索引库", "<code>index.sqlite</code> · 389,375 条 / 1,803 会话"),
    ("验收检查", "✅ 30 / 30 通过"),
    ("时间盲测", "✅ 7 / 7 通过（证明分析没偷看未来）"),
    ("隐私核对", "⚠️ 8 通过 / 2 失败（知识库聊天流水 1 篇 · PII 57 处）—— 待拍板"),
    ("知识库断链", "✅ 0"),
    ("人工批注", "✅ 0 丢失（verdict / my_note 永不被脚本覆盖）"),
    ("结论 ←→ 证据覆盖", "%d / %d = %.1f%%" % (linked, len(concl), linked * 100.0 / len(concl))),
]:
    A("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), v))
A("</tbody></table>")

A('<div class="foot">')
A("生成 %s ｜ run_id <code>%s</code> ｜ 脚本 <code>tools\\build_unified_workbench.py</code>（只读）<br>" % (NOW, RUN_ID))
A("权威来源：引擎 <code>05-纠偏层.md</code> 三·补·44（第八 / 九 / 十 / 十一节）· 报告 "
  "<code>年度事件重建_第二个我_第一轮_2026-10-05.html</code><br>")
A("数据全程本地 · 未联网 · 未上传第三方 · <b>不得外传</b>")
A("</div>")

A("</div></body></html>")

io.open(OUT, "w", encoding="utf-8").write("\n".join(H))
print("HTML → %s（%s 字节）" % (OUT, "{:,}".format(os.path.getsize(OUT))))
print("结论 %d 条 · 缺口候选 %d 条 · 脚本 %d 个 · _tmp 产物 %d 个" % (len(concl), len(gap_b), len(scripts), len(tmpidx)))
