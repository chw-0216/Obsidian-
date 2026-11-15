# -*- coding: utf-8 -*-
"""
build_daily_master.py —— 逐日全维整合：把「事 / 钱 / 人 / 项目 / 地 / 负荷」拉平到日期轴（只读）

背景：此前所有分析都是**按主题**组织的（事件库 / 支付流 / 井邻线 / 距离地图 / 车与家教线…），
     没有一个**按日期**的统一视图。本脚本产出「一天一行」的主表，作为所有主题分析的汇流处。

四源：
  ① 事件库.csv（2,864 条 · 阶段/层级/类别/涉及人/距离半径/情感负荷）
  ② _tmp/payment_flow.csv（2,207 条 · 金额/类型/方向/原文）
  ③ _tmp/jinglin_timeline.csv（968 条 · 井邻线）
  ④ index.sqlite（692 天消息量 · 只读）

输出：_tmp/daily_master.csv（699 天 × 23 列）
"""
import csv, io, os, re, sqlite3, datetime
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
EV = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\事件库.csv"
DIST = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\距离地图.csv"
PAY = os.path.join(WS, "_tmp", "payment_flow.csv")
JL = os.path.join(WS, "_tmp", "jinglin_timeline.csv")
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = os.path.join(WS, "_tmp", "daily_master.csv")

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def rd(p):
    return list(csv.DictReader(io.open(p, encoding="utf-8-sig")))

# ---------- 项目关键词 ----------
PROJ = [
    ("井邻",  re.compile(r"井邻|洞台|乡村美育|美育工作站|怀柔|驻村|动漫谷|渤海|植墨|碳迹|从山到城|护未|悲鸿|工作站")),
    ("澜沧",  re.compile(r"澜沧|绿墨|Movers4Climate|知行计划|普洱")),
    ("数字人", re.compile(r"数字人|数字交互|虚拟人")),
    ("车",    re.compile(r"通行费|高速费|车牌|京ACP0263|充电桩|极狐|上牌|交强险|车检|4S店|置换|试驾|购车|油费")),
    ("学业",  re.compile(r"开题|论文|课程|导师|央美|作业|毕设|答辩|讲座|研讨|党课|思想汇报")),
    ("家",    re.compile(r"妈妈|爸爸|母亲|父亲|奶奶|姥姥|家里|手术|住院|医院")),
    ("债务",  re.compile(r"月付|还款|欠款|账单|逾期|扣款|额度|分期|网贷|借款")),
    # ★ 2026-10-04 新增：按日期整合时挖出的两条此前未被识别的线
    ("校友会", re.compile(r"校友会|格拉斯哥|UoG|秀米|国富论|亚当|斯密")),
    ("教学",  re.compile(r"精华培训|家教|课时费|补课|试讲|代课|排课|备课|讲题")),
]

# ★ 专项线（有明确项目边界、非天天出现）—— 用于「四维同日」的判定
#   排除「家/学业」这类主线身份标签：它们几乎天天命中，无区分度
SPEC_PROJ = {"井邻", "澜沧", "数字人", "校友会"}
# 地理站点
SITE = re.compile(r"([\u4e00-\u9fa5]{2,7}站)")
PLATE = re.compile(r"京[A-Z][0-9A-Z]{5}")

def proj_of(text):
    hits = []
    for name, pat in PROJ:
        if pat.search(text):
            hits.append(name)
    return hits

# ---------- 1) 索引库：每日消息量 ----------
print("[1/5] 索引库每日消息量…")
con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
msgs = {}
for d, n, me, them, sess in con.execute("""
    select date(ts,'unixepoch','localtime') d,
           count(*), sum(role='me'), sum(role='them'), count(distinct session_key)
    from messages group by d"""):
    msgs[d] = {"消息总": n, "我发": me or 0, "对方发": them or 0, "会话数": sess}
con.close()
print("      %d 天" % len(msgs))

# ---------- 1b) 逐日项目识别（★ 扫索引库消息正文）----------
# 2026-10-04 新增：此前项目只从「事件摘要 + 支付原文」推，而「校友会运营」这类
# 只产生「事务确认」、不产生情感事件的线，在事件摘要里完全看不到 → 必须扫原文。
print("[1b] 索引库逐日项目识别…")
con2 = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
# ★ 排除「他 0 发言的群」——已知刷屏群（北京家教信息 25410000808@chatroom 等）
#   会污染项目词：家教单里出现「怀柔庙城」→ 被误判为井邻线；群友闲聊「格拉斯哥」→ 被误判为校友会。
active = set(sk for (sk,) in con2.execute("select distinct session_key from messages where role='me'"))
print("      他发过言的会话 %d 个" % len(active))
day_proj_db = defaultdict(set)
for d, sk, content in con2.execute(
        "select date(ts,'unixepoch','localtime'), session_key, content from messages"):
    if not content:
        continue
    if sk.endswith("@chatroom") and sk not in active:
        continue
    for name, pat in PROJ:
        if name == "校友会" and d < "2025-08-01":
            continue        # 校友会「运营线」起点 2025-08-04；此前提「格拉斯哥」是留学日常
        if name not in day_proj_db[d] and pat.search(content):
            day_proj_db[d].add(name)
con2.close()
print("      项目命中 %d 天" % len(day_proj_db))

# ---------- 2) 事件库 ----------
print("[2/5] 事件库…")
ev = rd(EV)
evd = defaultdict(list)
for r in ev:
    d = (r.get("日期") or "")[:10]
    if d:
        evd[d].append(r)
print("      %d 天" % len(evd))

# ---------- 3) 支付流 ----------
print("[3/5] 支付流…")
pay = rd(PAY)
payd = defaultdict(list)
for r in pay:
    d = (r.get("时间") or "")[:10]
    if d:
        payd[d].append(r)
print("      %d 天" % len(payd))

# ---------- 4) 井邻线 ----------
print("[4/5] 井邻线…")
jl = rd(JL)
jld = defaultdict(list)
for r in jl:
    d = (r.get("时间") or "")[:10]
    if d:
        jld[d].append(r)
print("      %d 天" % len(jld))

# ---------- 5) 距离地图 ----------
dm = rd(DIST)
DIST_OF = {}
for r in dm:
    DIST_OF[r["Name"]] = r.get("距离半径", "")

# ---------- 合并 ----------
print("[5/5] 合并…")
alld = sorted(set(msgs) | set(evd) | set(payd) | set(jld))
rows = []
for d in alld:
    try:
        dt = datetime.date(*map(int, d.split("-")))
        week = WEEK[dt.weekday()]
    except Exception:
        week = ""

    e = evd.get(d, [])
    p = payd.get(d, [])
    j = jld.get(d, [])
    m = msgs.get(d, {})

    # 阶段（取当天事件里出现最多的）
    phases = [x.get("阶段", "") for x in e if x.get("阶段")]
    phase = Counter(phases).most_common(1)[0][0] if phases else ""

    # 事件
    lvl = Counter(x.get("层级", "") for x in e)
    load = Counter(x.get("情感负荷", "") for x in e)
    A = [x for x in e if x.get("层级") == "A"]
    ppl = []
    for x in e:
        for k in (x.get("涉及人", ""), x.get("对话人", "")):
            for nm in re.split(r"[,，、/]", k or ""):
                nm = nm.strip()
                if nm and nm not in ppl and nm not in ("我", "自己"):
                    ppl.append(nm)
    # 距离档：取涉及人里最近的
    ORDER = {"零": 0, "近": 1, "中": 2, "远": 3}
    dr = ""
    for nm in ppl:
        v = DIST_OF.get(nm)
        if v and (dr == "" or ORDER.get(v, 9) < ORDER.get(dr, 9)):
            dr = v
    # A 级摘要
    def brief(x):
        s = x.get("事件", "")
        return s[:60] + ("…" if len(s) > 60 else "")
    summ = " ｜ ".join(brief(x) for x in (A or e)[:3])

    # 钱
    out_amt = sum(float(x["金额"]) for x in p if x.get("方向") == "支出" and x.get("金额"))
    in_amt = sum(float(x["金额"]) for x in p if x.get("方向") == "收入" and x.get("金额"))
    kinds = [x.get("类型", "") for x in p if x.get("类型")]
    big = [x for x in p if x.get("方向") == "支出" and x.get("金额") and float(x["金额"]) >= 500]

    # 地理
    sites, plates = [], []
    for x in p:
        t = x.get("原文", "") or ""
        sites += SITE.findall(t)
        plates += PLATE.findall(t)

    # 项目
    blob = " ".join([x.get("事件", "") for x in e] + [x.get("原文", "") for x in p] +
                    [x.get("内容", "") for x in j])
    projs = list(proj_of(blob))
    for nm, _ in PROJ:                       # ★ 并入索引库消息正文的命中
        if nm in day_proj_db.get(d, ()) and nm not in projs:
            projs.append(nm)
    if d < "2025-08-01":                     # 校友会「运营线」时间窗（对两个来源都生效）
        projs = [p for p in projs if p != "校友会"]

    rows.append({
        "日期": d, "星期": week, "阶段": phase,
        "消息总": m.get("消息总", 0), "我发": m.get("我发", 0),
        "对方发": m.get("对方发", 0), "会话数": m.get("会话数", 0),
        "事件数": len(e), "A级": lvl.get("A", 0), "B级": lvl.get("B", 0), "C级": lvl.get("C", 0),
        "高负荷": load.get("高", 0), "中负荷": load.get("中", 0), "低负荷": load.get("低", 0),
        "涉及人": "、".join(ppl[:6]), "最近距离": dr, "事件摘要": summ,
        "支出": round(out_amt, 2), "收入": round(in_amt, 2), "支付笔数": len(p),
        "大额支出": len(big), "支付类型": "、".join(sorted(set(kinds))[:5]),
        "项目": "、".join(projs), "地理": "、".join(sorted(set(sites))[:4]),
        "车牌": "、".join(sorted(set(plates))[:2]),
        "井邻线": len(j),
    })

FIELDS = list(rows[0].keys())
with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print()
print("=" * 66)
print("逐日全维主表 → %s" % OUT)
print("  %d 天  %s → %s" % (len(rows), rows[0]["日期"], rows[-1]["日期"]))
print("  有事件 %d 天 · 有钱 %d 天 · 有井邻 %d 天 · 有消息 %d 天" % (
    sum(1 for r in rows if r["事件数"]), sum(1 for r in rows if r["支付笔数"]),
    sum(1 for r in rows if r["井邻线"]), sum(1 for r in rows if r["消息总"])))
print("  ★ 事+钱同日 %d 天" % sum(1 for r in rows if r["事件数"] and r["支付笔数"]))
print("  ★ 事+钱+项目同日 %d 天" % sum(1 for r in rows if r["事件数"] and r["支付笔数"] and r["项目"]))
print("  ★ 事+钱+项目+高负荷 %d 天" % sum(
    1 for r in rows if r["事件数"] and r["支付笔数"] and r["项目"] and r["高负荷"]))
