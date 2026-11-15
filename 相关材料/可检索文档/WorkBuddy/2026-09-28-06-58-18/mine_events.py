# -*- coding: utf-8 -*-
"""
mine_events.py — 从主库全量挖掘「真实事件」（过滤系统噪音）

输入：wechat-analysis-scale.sqlite3 的 v3_annotations.result_json.events
输出：
  events_candidates.csv   —— 待人工复核的事件清单
  events_summary.md       —— 分类统计 + 主线聚类

用法：python mine_events.py
"""
import sqlite3
import sys
import json
import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3"
OUT = os.path.dirname(os.path.abspath(__file__))

# ── 系统噪音：描述命中即丢 ──────────────────────────────
NOISE = [
    "版本", "兼容", "升级提示", "撤回", "表情包", "表情互动", "拍一拍",
    "登录操作", "账号安全", "好友验证", "支付成功", "支付与收益", "收益到账",
    "还款提醒", "美团", "收款", "转账", "课程推销", "课程营销", "课程推广",
    "推销", "营销推广", "广告", "客服", "语音通话", "未接通", "无法显示",
    "无法解析", "发送图片", "分享图片", "发送表情", "分享小程序", "文件传输",
    "确认收到", "打招呼", "系统通知", "系统提示", "新年祝福", "节日祝福",
    "回放链接", "招聘信息分享", "收款到账", "内容无法显示",
    "试驾", "报价", "到店", "优惠", "团购", "下单", "发货", "物流", "退货",
    "促销", "秒杀", "拼团", "红包", "积分", "会员卡",
]
# 系统账号（不是真人）
SYS_ACCOUNTS = ["微信团队", "微信支付", "服务通知", "美团", "文件传输助手",
                "群助手", "订阅号", "公众号", "企业微信"]
# 商业/培训/推销账号（有事件也不计入「真实事件」）
BAD_ACCOUNT = re.compile(
    r"粉笔|穿透求职|慕林|法考|考研|培训|教育科技|客服|顾问|销售|体验中心|售后|"
    r"批发|建材|开锁|闲鱼|优惠券|健身|驾校|中介|极狐|汽车|保险|贷款|装饰|"
    r"图文|快印|酒店|签证|律所|巩世峰|彭于晏 AI|Jake|Jasoooon"
)

# ── 真实事件信号词：描述命中即留 ────────────────────────
SIGNAL = {
    "求职/职场": ["面试", "笔试", "复试", "简历", "投递", "offer", "入职", "离职",
                  "实习", "求职", "招聘", "岗位", "试用", "转正", "内推", "签三方"],
    "学业/学术": ["答辩", "开题", "中期", "考试", "考证", "报名", "录取", "拟录取",
                  "成绩", "选课", "课程", "讲座", "上课", "研讨会", "汇报", "评审",
                  "导师", "论文", "毕业", "学分", "毕设", "答辩会"],
    "展演/创作": ["展览", "布展", "开幕", "画展", "美术馆", "作品", "拍摄", "剪辑",
                  "放映", "策展", "装置", "演出", "音乐会", "艺博会", "创作"],
    "比赛/活动": ["比赛", "竞赛", "路演", "决赛", "初赛", "报名", "联谊", "运动会",
                  "橄榄球", "中秋", "年会", "团建", "训练营", "hackathon", "工作坊"],
    "社交/见面": ["见面", "碰头", "约见", "面谈", "聚会", "聚餐", "吃饭", "约饭",
                  "喝酒", "喝茶", "生日", "婚礼", "拜访", "看望", "拜访", "钓鱼",
                  "爬山", "出游", "旅行", "看展", "接送"],
    "生活/事务": ["搬家", "租房", "看房", "买房", "购车", "买车", "提车", "体检",
                  "就医", "看病", "手术", "住院", "挂号", "报销", "社保", "签证",
                  "护照", "公证", "盖章", "证明", "申请材料", "办证", "寄送"],
    "项目/商务": ["项目", "立项", "结项", "验收", "交付", "合作", "合同", "报价",
                  "发票", "劳务", "结算", "对接", "方案", "需求", "洽谈", "签约"],
    "出行/迁移": ["出发", "抵达", "出差", "返程", "航班", "高铁", "车站", "机场",
                  "驻村", "下乡", "回京", "飞", "到北京", "回学校"],
}


def load():
    con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro&immutable=1", uri=True)
    q = """
    SELECT a.segment_id, a.result_json, c.display_name, s.start_ts, s.end_ts
    FROM v3_annotations a
    LEFT JOIN segments s ON s.id = a.segment_id
    LEFT JOIN conversations c ON c.id = s.conversation_id
    WHERE a.status='success' AND a.event_count>0 AND a.result_json IS NOT NULL
    """
    return con.execute(q).fetchall()


def ts2s(ts):
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def classify(desc):
    """返回 (是否保留, 类别)"""
    d = desc or ""
    if any(n in d for n in NOISE):
        return False, None
    for cat, kws in SIGNAL.items():
        if any(k in d for k in kws):
            return True, cat
    return False, None


def main():
    rows = load()
    kept, cat_cnt = [], Counter()
    dropped = 0
    for seg, rj, disp, st, et in rows:
        if not disp or disp.strip() in ("我", "?"):
            continue
        if any(s in disp for s in SYS_ACCOUNTS) or BAD_ACCOUNT.search(disp):
            continue
        try:
            d = json.loads(rj)
        except Exception:
            continue
        for e in (d.get("events") or []):
            if not isinstance(e, dict):
                continue
            desc = (e.get("description") or "").strip()
            if not desc:
                continue
            ok, cat = classify(desc)
            if not ok:
                dropped += 1
                continue
            tr = str(e.get("time_reference") or "").strip()
            date = ts2s(st)
            et_ = str(e.get("event_type") or "").strip()
            nature = {"past_occurrence": "已发生", "completed": "已完成",
                      "future_plan": "计划", "planned": "计划",
                      "current_situation": "进行中", "uncertain": "不确定",
                      "cancelled": "已取消"}.get(et_, et_ or "未标")
            kept.append({
                "对话人": disp or "?",
                "日期": date,
                "时间线索": tr,
                "类别": cat,
                "性质": nature,
                "事件": desc[:120],
                "涉及人": "、".join(e.get("people_involved") or [])[:60],
                "结果": (str(e.get("outcome") or ""))[:60],
                "置信度": e.get("confidence", ""),
                "证据": (e.get("evidence_ids") or [""])[0],
            })
            cat_cnt[cat] += 1

    # 聚合成「事件」：同对话人 + 同日期 + 同类别 → 一条
    groups = defaultdict(list)
    for r in kept:
        groups[(r["对话人"], r["日期"], r["类别"])].append(r)

    events = []
    for (disp, date, cat), rs in groups.items():
        # 描述去重后取前 3 条拼接
        descs, seen_d = [], set()
        for r in rs:
            d = r["事件"][:60]
            key = d[:16]
            if key in seen_d:
                continue
            seen_d.add(key)
            descs.append(d)
            if len(descs) >= 3:
                break
        ppl = set()
        for r in rs:
            if r["涉及人"]:
                ppl.update(r["涉及人"].split("、"))
        events.append({
            "对话人": disp, "日期": date, "类别": cat,
            "事件": " ｜ ".join(descs),
            "性质": rs[0]["性质"],
            "条数": len(rs),
            "涉及人": "、".join(sorted(p for p in ppl if p)[:5]),
            "置信度": rs[0]["置信度"],
            "证据": rs[0]["证据"],
        })

    events.sort(key=lambda r: (r["日期"] or "9999", r["对话人"]))
    uniq = events

    csv_path = os.path.join(OUT, "events_candidates.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["编号", "日期", "类别", "性质", "事件", "对话人", "涉及人", "条数",
                    "置信度", "证据", "复核(确认/否定/合并)", "备注"])
        for i, r in enumerate(uniq, 1):
            w.writerow([i, r["日期"], r["类别"], r["性质"], r["事件"], r["对话人"],
                        r["涉及人"], r["条数"], r["置信度"], r["证据"], "", ""])

    print(f"过滤掉噪音：{dropped}")
    print(f"保留候选（消息级）：{len(kept)}   聚合为事件：{len(uniq)}")
    print(f"\n类别分布（事件级）：")
    for c, n in Counter(r["类别"] for r in uniq).most_common():
        print(f"  {n:>5}  {c}")

    # 主线聚类：按类别 × 月份
    print(f"\n主线（类别 × 月份，取 ≥3 条的）：")
    buckets = defaultdict(list)
    for r in uniq:
        buckets[(r["类别"], (r["日期"] or "")[:7])].append(r)
    for (cat, mon), rs in sorted(buckets.items(), key=lambda x: -len(x[1]))[:25]:
        people = Counter(x["对话人"] for x in rs).most_common(3)
        ps = "、".join(f"{p}({n})" for p, n in people)
        print(f"  {len(rs):>3}  {cat:<10} {mon or '?'}   {ps}")

    print(f"\n→ {csv_path}")


if __name__ == "__main__":
    main()
