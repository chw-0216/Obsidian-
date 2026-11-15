# -*- coding: utf-8 -*-
"""扫群名里的「自我规程」——验证「他给自己写的规程出现在哪类关系上」。

用法: python scan_group_rules.py [--dump]
"""
import csv
import io
import re
import sys
import collections

P = (r'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理'
     r'\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出\通讯录'
     r'\contacts_2026-07-23T20-56-25.csv')

# 自我规程信号词：指向「我该怎么做 / 目标 / 自律 / 提醒」
RULE_WORDS = [
    '要', '不要', '别', '必须', '一定', '记住', '提醒', '目标', '计划', '任务',
    '每天', '每周', '每月', '今天', '明天', '周内', '月内', '前', '冲刺', '加油',
    '自律', '坚持', '恢复', '完成', '搞定', '搞定', '倒计时', 'ddl', 'deadline',
    '不能', '得', '抓紧', '开始', '戒', '早起', '打卡', '复盘', '整理', '待办',
]

# 事务/身份型群名（对照用）：机构、班级、项目、商家
ORG_WORDS = ['班', '级', '学院', '大学', '学校', '公司', '中心', '机构', '群',
             '项目', '团队', '小组', '协会', '社团', '培训', '教育']


def load():
    return list(csv.DictReader(io.open(P, encoding='utf-8-sig')))


def gname(r):
    # ⚠️ 有备注时「显示名称」==备注；群聊一般无备注，取 显示名称 优先
    return (r.get('显示名称') or r.get('昵称') or '').strip()


def main():
    rows = load()
    groups = [r for r in rows if r.get('类型') == '群聊']
    print(f"群聊总数: {len(groups)}\n")

    names = [gname(r) for r in groups]

    if '--dump' in sys.argv:
        out = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\群名全量.txt'
        with io.open(out, 'w', encoding='utf-8') as f:
            for n in sorted(names):
                f.write(n + '\n')
        print(f"已导出全部群名 -> {out}\n")

    # 命中自我规程词
    hits = []
    for r in groups:
        n = gname(r)
        ws = [w for w in RULE_WORDS if w in n]
        if ws:
            hits.append((n, ws, r.get('备注', '')))

    print(f"=== 含「规程/目标/自律」信号的群名：{len(hits)} 个 ===")
    for n, ws, bz in sorted(hits, key=lambda x: -len(x[1])):
        print(f"  [{','.join(ws[:4])}]  {n}")

    print()
    print("=== 全部群名（前 60，按名称）===")
    for n in sorted(names)[:60]:
        print('  ' + n)


if __name__ == '__main__':
    main()
