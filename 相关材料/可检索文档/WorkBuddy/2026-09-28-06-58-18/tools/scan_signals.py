# -*- coding: utf-8 -*-
"""
scan_signals.py — 在可读对话文本里扫描「事件信号」，快速定位发生了什么

用法：python scan_signals.py [--dir <目录>] [--cat 类别]
"""
import os
import re
import sys
import argparse
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\readable"

CATS = {
    "学业/央美": ["开题", "答辩", "导师", "陈晔", "论文", "课程", "选课", "学分", "毕设",
                  "央美", "美院", "实验艺术", "评审", "讲座", "工作坊", "汇报", "中期",
                  "研一", "研二", "硕士", "毕业", "成绩", "评奖", "奖学金"],
    "实习/工作": ["实习", "面试", "笔试", "简历", "投递", "offer", "入职", "离职", "转正",
                  "试用", "内推", "招聘", "岗位", "工资", "薪", "兼职", "家教", "上课",
                  "美术馆", "媒体部", "北京台", "井邻", "联合国", "栗壳"],
    "项目/创作": ["展览", "布展", "开幕", "策展", "作品", "拍摄", "剪辑", "装置", "放映",
                  "丝网", "版画", "印刷", "创作", "项目", "合作", "方案", "交付"],
    "金钱/债务": ["借钱", "还款", "还钱", "欠", "贷款", "网贷", "花呗", "分期", "利息",
                  "转账", "赔偿", "赔", "押金", "房租", "租金", "报销", "结算", "劳务",
                  "工资", "学费", "账单"],
    "情感/关系": ["喜欢", "爱", "分手", "复合", "女朋友", "男朋友", "对象", "约会",
                  "表白", "追", "暧昧", "结婚", "相亲", "见家长", "冷战", "吵架"],
    "家庭": ["爸", "妈", "父亲", "母亲", "家里", "回家", "姥姥", "姥爷", "奶奶", "爷爷",
              "住院", "手术", "看病", "体检"],
    "健康/状态": ["失眠", "睡不着", "焦虑", "抑郁", "累", "崩", "难受", "头疼", "生病",
                  "吃药", "医院", "精神", "状态"],
    "出行/迁移": ["机票", "航班", "高铁", "火车", "签证", "护照", "出发", "回国", "回京",
                  "出差", "搬家", "租房", "看房"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DIR)
    ap.add_argument("--cat", default=None)
    args = ap.parse_args()

    cats = {args.cat: CATS[args.cat]} if args.cat else CATS
    hits = defaultdict(list)

    for fn in sorted(os.listdir(args.dir)):
        if not fn.endswith(".txt"):
            continue
        p = os.path.join(args.dir, fn)
        who = fn[:-4]
        day = "?"
        try:
            lines = open(p, encoding="utf-8").read().split("\n")
        except Exception:
            continue
        for ln in lines:
            m = re.match(r"^═══ (.+?) ═══$", ln)
            if m:
                day = m.group(1)
                continue
            if not ln.startswith("["):
                continue
            for cat, kws in cats.items():
                for k in kws:
                    if k in ln:
                        hits[(cat, who)].append((day, ln))
                        break

    for (cat, who), rs in sorted(hits.items(), key=lambda x: (x[0][0], -len(x[1]))):
        if len(rs) < 2:
            continue
        print(f"\n【{cat}】{who}  —— {len(rs)} 处")
        seen = set()
        for day, ln in rs[:14]:
            key = ln[:40]
            if key in seen:
                continue
            seen.add(key)
            print(f"   {day}  {ln[:130]}")
        if len(rs) > 14:
            print(f"   ...（另 {len(rs)-14} 处）")


if __name__ == "__main__":
    main()
