# -*- coding: utf-8 -*-
"""
cross_jinglin.py —— 井邻线三线交叉（只读）

五段：
  A 井邻线事件 × 人生阶段
  B 井邻线人物 × 距离半径（谁在场 / 谁只出现一次）
  C 钱 ↔ 地 ↔ 事：高速通行费（宽沟站=怀柔）↔ 井邻事件日
  D 三线并行：井邻 / 澜沧（绿墨护未）/ 数字人 —— 母亲线与导师线各自的承载
  E 张力检测：导师「划界」语 vs 母亲「支持」语

产出：_tmp/jinglin_cross.txt
"""
import csv, io, os, re, sqlite3, datetime
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
EV = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\事件库.csv"
PAY = os.path.join(WS, "_tmp", "payment_flow.csv")
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = os.path.join(WS, "_tmp", "jinglin_cross.txt")

L = []
def P(s=""): L.append(s)

# ============ A 井邻线事件 × 阶段 ============
evs = list(csv.DictReader(io.open(EV, encoding="utf-8-sig")))
jl = [e for e in evs if e.get("来源") == "E·井邻项目事件"]
P("井邻线三线交叉报告")
P("=" * 70)
P()
P("【A】井邻线事件 %d 条 × 人生阶段" % len(jl))
P("-" * 70)
for k, v in sorted(Counter(e["阶段"] for e in jl).items()):
    P("  %-26s %d" % (k, v))
P()
P("  按类别:")
for k, v in Counter(e["类别"] for e in jl).most_common():
    P("    %-12s %d" % (k, v))
P()
P("  按影响:")
for k, v in Counter(e["影响"] for e in jl).most_common():
    P("    %-12s %d" % (k, v))
P()
P("  A 级（人生节点级）逐条:")
for e in sorted([x for x in jl if x["层级"] == "A"], key=lambda x: x["日期"]):
    P("    %s  %s" % (e["日期"], e["事件"][:78]))

# ============ B 人物 × 距离 ============
P()
P("【B】井邻线人物 × 距离半径（距离地图 98 行中命中者）")
P("-" * 70)
DIST = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\距离地图.csv"
dm = list(csv.DictReader(io.open(DIST, encoding="utf-8-sig")))
JL_PPL = ["陈晔", "刘丽萍", "张宝", "关宇佳", "王华青", "韩云峰", "郭静秋", "马慧楠",
          "王博", "徐嘉良", "杜清轩", "安逸", "桃餮", "罗文迪", "净", "jt", "石晶",
          "齐家滨", "刘衎婧", "薛伟东", "子辰", "琢", "李彦樵", "杨丁懿", "廖宇卓"]
for r in dm:
    nm = r["Name"]
    if any(k in nm or nm in k for k in JL_PPL) or r.get("来源") == "补标井邻":
        P("  %-22s | %-4s | %6s 条 | %-14s | %s" % (
            nm[:22], r["距离半径"], r["Messages"], r["Relation"][:14], (r["Detail"] or "")[:52]))
P()
P("  ⚠️ 导师（导！急速回...）距离半径 = 中 —— 但井邻线命中 113 条，是最大私聊承载者")

# ============ C 钱 ↔ 地 ↔ 事 ============
P()
P("【C】钱 ↔ 地 ↔ 事：高速通行费（宽沟站 = 京承高速怀柔出口）")
P("-" * 70)
pays = list(csv.DictReader(io.open(PAY, encoding="utf-8-sig")))
toll = [r for r in pays if "宽沟站" in (r.get("原文") or "")]
P("  宽沟站相关通行费 %d 笔（全部车牌京ACP0263）" % len(toll))
P()
P("  逐笔:")
for r in toll:
    m = re.search(r"(\S+站)\s*-\s*(\S+站)", r.get("原文", ""))
    leg = ("%s → %s" % (m.group(1), m.group(2))) if m else "?"
    P("    %s  ¥%-6s  %s" % (r["时间"][:16], r["金额"], leg))
P()
jl_days = {e["日期"] for e in jl}
toll_days = {r["时间"][:10] for r in toll}
P("  ★ 通行费日 ∩ 井邻事件日 = %s" % sorted(toll_days & jl_days))
P("  ★ 通行费日（无对应井邻事件）= %s" % sorted(toll_days - jl_days))
P()
P("  ⚠️ 边界：通行费最早 2026-08-04 —— 但他 2026-08-18 自述「去了井邻都 20 多趟了」")
P("     → 2026-08 之前的往返未被推送记录（非「没去」）")

# ============ D 三线并行 ============
P()
P("【D】三线并行：井邻 / 澜沧（绿墨护未）/ 数字人")
P("-" * 70)
con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
q = con.cursor()
def cnt(kw, sk=None):
    if sk:
        return list(q.execute("select count(*) from messages where session_key=? and content like ?",
                              (sk, "%" + kw + "%")))[0][0]
    return list(q.execute("select count(*) from messages where content like ?",
                          ("%" + kw + "%",)))[0][0]
MOM = "wxid_1wa75s1kze3o22"
TUT = list(q.execute("select talker from sessions where display_name like '%导！急速回%' limit 1"))[0][0]
LINES = ["井邻", "洞台", "乡村美育", "澜沧", "绿墨", "数字人", "植墨", "碳迹"]
P("  %-10s %8s %10s %10s" % ("词", "全库", "母亲线", "导师线"))
for k in LINES:
    P("  %-10s %8d %10d %10d" % (k, cnt(k), cnt(k, MOM), cnt(k, TUT)))
con.close()

# ============ E 张力检测 ============
P()
P("【E】张力检测：导师「划界」语 vs 母亲「支持」语")
P("-" * 70)
QUOTES = [
    ("2025-10-15", "导师", "也别发井邻"),
    ("2026-08-05", "导师", "井邻优惠不能写出来啊 / 这个挺好，但井邻的不要写"),
    ("2026-10-02", "导师", "你不需要给井邻做广告"),
    ("2026-06-08", "导师", "乡村美育工作站的边际成本和边际效益你还是要想啊！"),
    ("2026-07-21", "母亲", "井邻很难搞"),
    ("2026-08-08", "母亲", "他们以为我帮陈晔在井邻，以为能挣钱。其实我帮我儿子。"),
    ("2026-08-18", "本人", "去了井邻都 20 多趟了 / 我就在井邻住过两晚"),
    ("2026-08-25", "本人→刘衎婧", "只是正好最近怀柔有项目哈哈哈"),
    ("2026-09-19", "本人→关宇佳", "配合井邻的活动一直显得力不从心和没有真正开展"),
]
for d, who, s in QUOTES:
    P("  %s  [%s]  %s" % (d, who, s))
P()
P("  ★ 读法：导师在「划界」（项目归央美，不为商业方背书）；")
P("    母亲在「兜底」（她做的是帮儿子，不是帮陈晔）；")
P("    他本人在「淡化」（对刘衎婧说「只是正好」）。三方对同一件事三种表述。")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
print("\n→ %s" % OUT)
