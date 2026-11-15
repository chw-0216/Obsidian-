# -*- coding: utf-8 -*-
"""refine_events.py — 清洗 + 重要性分级，产出 events_review.csv（复核台数据源）。

清洗项：
  1) 对话人昵称归一（导师乱码昵称、机构号标记）
  2) 明显非事件/含糊句打标（不删，降级为 C，便于复核时快速跳过）
  3) 重要性打分 → A/B/C 三级
"""
import csv
import os
import re
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "events_candidates.csv")
OUT = os.path.join(HERE, "events_review.csv")

# ---------- 1) 昵称归一 ----------
ALIAS = {
    "导！急速回，三思回得体！！！": "导师 陈晔",
    "K*上门家教辅导补习中心*罗老师": "家教中介号（噪音）",
    "小杨老师": "小杨老师（家教中介）",
}

# ---------- 2) 降级标记 ----------
VAGUE = re.compile(r"某件事|待定|不确定|含糊|未知|尚未结束")
META = re.compile(r"^(行业|市场中|目前|当前|总体来说)")  # 陈述性观察，非事件
SYS_ACCT = re.compile(r"中介|辅导中心|补习中心|教育科技|招聘|助手|客服|团队|官方|小助手")

# ---------- 3) 重要性 ----------
HIGH_KW = ["录取", "offer", "录用", "入职", "转正", "面试", "笔试", "答辩", "开题",
           "毕业", "学位", "论文", "签约", "合同", "立项", "投资", "融资", "合作",
           "创业", "注册", "公司", "出版", "个展", "联展", "获奖", "入选", "中标",
           "手术", "住院", "体检", "搬家", "租房", "买房", "购车", "提车", "签证",
           "出国", "留学", "驻村", "下乡", "非遗", "劳务", "课酬", "工资", "奖学金",
           "评选", "评优", "报名", "录用", "录取通知", "项目", "立案", "开庭", "离婚"]
NAT_SCORE = {"已完成": 26, "已发生": 24, "已取消": 14, "进行中": 18,
             "计划": 8, "不确定": 5, "未标": 4}
CAT_SCORE = {"学业/学术": 15, "求职/职场": 15, "项目/商务": 13, "展演/创作": 13,
             "生活/事务": 11, "比赛/活动": 11, "出行/迁移": 7, "社交/见面": 7}


def tier_of(score, flags):
    if flags:
        return "C"
    if score >= 58:
        return "A"
    if score >= 38:
        return "B"
    return "C"


# ---------- 4) 主体判定：这条事件是「我」的还是「对方」的 ----------
SELF = re.compile(r"我|蔡浩文|自己|本人")
OTHER = re.compile(r"对方|他|她|该求职者|求职者|学员|学生")


def subject_of(ev):
    me = bool(SELF.search(ev))
    ot = bool(OTHER.search(ev))
    if me and ot:
        return "双方"
    if me:
        return "我"
    if ot:
        return "对方"
    return "第三方"


rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
out = []
for r in rows:
    who = r["对话人"].strip()
    who = ALIAS.get(who, who)
    ev = r["事件"].strip()
    n = int(r["条数"] or 1)
    nat = r["性质"] or "未标"
    cat = r["类别"]

    flags = []
    if VAGUE.search(ev):
        flags.append("含糊")
    if META.search(ev):
        flags.append("非事件")
    if SYS_ACCT.search(who):
        flags.append("系统号")

    score = min(n, 6) * 8 + NAT_SCORE.get(nat, 4) + CAT_SCORE.get(cat, 6)
    hit = sum(1 for k in HIGH_KW if k in ev)
    score += min(hit, 3) * 10
    if n >= 4:
        score += 8
    subj = subject_of(ev)
    if subj == "我":
        score += 6
    tier = tier_of(score, flags)

    out.append({
        "编号": r["编号"], "层级": tier, "分": score, "主体": subj,
        "日期": r["日期"], "年份": (r["日期"] or "?")[:4],
        "类别": cat, "性质": nat, "事件": ev,
        "对话人": who, "涉及人": r["涉及人"], "条数": n,
        "置信度": r["置信度"], "证据": r["证据"],
        "标记": "/".join(flags), "复核": "", "备注": "",
    })

out.sort(key=lambda x: (-x["分"], x["日期"]))

cols = ["编号", "层级", "分", "主体", "日期", "年份", "类别", "性质", "事件",
        "对话人", "涉及人", "条数", "置信度", "证据", "标记", "复核", "备注"]
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(out)

print(f"→ {OUT}")
print("层级：", dict(Counter(r["层级"] for r in out)))
print("主体：", dict(Counter(r["主体"] for r in out)))
print("标记：", dict(Counter(r["标记"] for r in out if r["标记"])))
print("年份：", dict(sorted(Counter(r["年份"] for r in out).items())))
print("Top10 分值事件：")
for r in out[:10]:
    print(f'  [{r["分"]}][{r["层级"]}][{r["日期"]}][{r["类别"]}] {r["事件"][:60]}')
