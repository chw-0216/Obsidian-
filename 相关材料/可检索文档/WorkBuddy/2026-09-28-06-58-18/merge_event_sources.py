# -*- coding: utf-8 -*-
"""merge_event_sources.py — 合并两个事件源，产出统一事件表。

源 A：v3_annotations.result_json.events  → events_review.csv（1,111 条，已过滤分级）
源 B：deep_contact_analysis.json.key_events → 1,577 条（逐联系人策展，带 impact 标签）

产出：events_merged.csv（统一字段 + 来源标记 + 去重）
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(os.path.expanduser("~"), "WorkBuddy AI", "2026-09-28-06-58-18")
SRC_A = os.path.join(WS, "events_review.csv")
SRC_B = os.path.join(
    os.path.expanduser("~"), "Desktop", "07_聊天记录分析", "微信聊天记录清理",
    "10_DeepSeek-v3分析工作区", "runs", "deep_contact_analysis",
    "deep_contact_analysis.json")
OUT = os.path.join(WS, "events_merged.csv")

# ---------- 类别推断（源 B 没有类别字段） ----------
CAT_KW = [
    ("学业/学术", r"课|论文|开题|答辩|毕业|导师|作业|成绩|考试|录取|报名|工作坊|讲座|研讨会|学位|证明"),
    ("求职/职场", r"面试|简历|offer|实习|转正|入职|招聘|试用|工资|课酬|编制|岗位"),
    ("项目/商务", r"项目|合同|合作|立项|报价|结算|客户|甲方|方案|宣发|海报|招商"),
    ("展演/创作", r"展览|作品|布展|开幕|画展|创作|拍摄|设计|作品集"),
    ("生活/事务", r"手术|住院|体检|医院|搬家|租房|购车|提车|维修|快递|钥匙|赔偿|事故"),
    ("出行/迁移", r"出差|回京|返程|抵达|机票|航班|出发|旅行|下乡|驻村"),
    ("比赛/活动", r"比赛|路演|舞会|活动|赛事|联谊|校友会"),
    ("社交/见面", r"见面|约|吃饭|聚会|喝酒|打球|看展|咖啡"),
]
IMPACT_NAT = {"正面": "已发生", "中性": "已发生", "负面": "已发生"}


def cat_of(text):
    for c, pat in CAT_KW:
        if re.search(pat, text):
            return c
    return "社交/见面"


def norm(s):
    return re.sub(r"[\s｜|,，。.、；;：:（）()\[\]【】\"'‘’“”\-—~～]", "", str(s or ""))


def fix_date(raw):
    """源 B 的 date 字段混杂：正常日期 / 10 位 Unix 时间戳 / 自由文本。"""
    s = str(raw or "").strip()
    if not s:
        return "", "无日期"
    # 10 位 Unix 时间戳
    if re.fullmatch(r"\d{10}", s):
        import datetime
        try:
            return datetime.datetime.fromtimestamp(int(s)).strftime("%Y-%m-%d"), "ts转换"
        except (ValueError, OSError, OverflowError):
            return "", "ts异常"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0), "正常"
    m = re.match(r"(\d{4})-(\d{2})$", s)
    if m:
        return s + "-01", "补日"
    m = re.match(r"(\d{4})年(\d{1,2})月", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-01", "中文日期"
    return "", "待定"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-a", default=SRC_A)
    ap.add_argument("--src-b", default=SRC_B)
    a = ap.parse_args()

    rows = []

    # ---- 源 A ----
    if os.path.exists(a.src_a):
        for r in csv.DictReader(open(a.src_a, encoding="utf-8-sig")):
            rows.append({
                "来源": "A·标注事件", "日期": r["日期"], "类别": r["类别"],
                "性质": r["性质"], "事件": r["事件"], "对话人": r["对话人"],
                "涉及人": r.get("涉及人", ""), "主体": r.get("主体", ""),
                "层级": r.get("层级", ""), "分": r.get("分", ""),
                "影响": "", "条数": r.get("条数", "1"), "证据": r.get("证据", ""),
            })
    n_a = len(rows)

    # ---- 源 B ----
    n_b = 0
    if os.path.exists(a.src_b):
        d = json.load(open(a.src_b, encoding="utf-8"))
        for x in d.get("ranking", []):
            who = x.get("contact_name", "")
            an = (x.get("analysis") or {}).get("analysis") or {}
            for k in (an.get("key_events") or []):
                ev = k.get("event", "")
                imp = str(k.get("impact", "") or "")
                d, dhow = fix_date(k.get("date"))
                rows.append({
                    "来源": "B·画像事件", "日期": d,
                    "类别": cat_of(ev), "性质": IMPACT_NAT.get(imp, "已发生"),
                    "事件": ev, "对话人": who, "涉及人": "",
                    "主体": "", "层级": "", "分": "",
                    "影响": imp, "条数": "1", "证据": dhow,
                })
                n_b += 1

    # ---- 去重：同日期 + 同对话人 + 归一化文本互相包含 ----
    seen = {}
    keep = []
    dup = 0
    for r in rows:
        key = (r["日期"][:10], norm(r["对话人"])[:4])
        t = norm(r["事件"])
        bucket = seen.setdefault(key, [])
        hit = False
        for i, ex in enumerate(bucket):
            if t in ex or ex in t or (len(t) > 12 and len(ex) > 12 and t[:12] == ex[:12]):
                hit = True
                # 优先保留源 B（带 impact 标签）
                if r["来源"].startswith("B") and not keep[i]["来源"].startswith("B"):
                    keep[i] = r
                break
        if hit:
            dup += 1
            continue
        bucket.append(t)
        keep.append(r)

    cols = ["来源", "日期", "类别", "性质", "事件", "对话人", "涉及人", "主体",
            "层级", "分", "影响", "条数", "证据"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(keep)

    print(f"→ {OUT}")
    print(f"  源 A {n_a} + 源 B {n_b} = {len(rows)}；去重剔除 {dup}；合并后 {len(keep)}")
    print("  来源分布：", dict(Counter(r["来源"] for r in keep)))
    print("  类别分布：", dict(Counter(r["类别"] for r in keep).most_common()))
    print("  impact 分布：", dict(Counter(r["影响"] for r in keep if r["影响"])))
    print("  日期处理：", dict(Counter(r["证据"] for r in keep if r["来源"].startswith("B"))))
    yr = Counter((r["日期"] or "?")[:4] for r in keep)
    print("  年份分布：", dict(sorted(yr.items())))

    # 只出现在源 B 的高价值事件（源 A 漏掉的）
    only_b = [r for r in keep if r["来源"].startswith("B")]
    print(f"\n★ 仅源 B 独有 {len(only_b)} 条，其中负面 {sum(1 for r in only_b if '负面' in r['影响'])} 条")


if __name__ == "__main__":
    main()
