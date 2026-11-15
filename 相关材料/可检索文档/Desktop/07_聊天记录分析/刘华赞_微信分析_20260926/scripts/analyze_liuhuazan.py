# -*- coding: utf-8 -*-
"""
刘华赞 微信数据分析 —— WeFlow 采集口径统计脚本
输入：00_原始导出/*.json（由 scripts/导出-刘华赞及关联人.ps1 生成）
输出：02_结构化分析/ 下的 metrics.json / messages.csv / evidence_chain.csv / event_timeline.csv
"""
import json, csv, io, os, sys, re
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT = os.path.join(ROOT, "02_结构化分析")
os.makedirs(OUT, exist_ok=True)

CST = timezone(timedelta(hours=8))
TYPE_MAP = {1: "文本", 3: "图片", 34: "语音", 42: "名片", 43: "视频", 47: "表情",
            48: "位置", 49: "链接/卡片/文件", 50: "语音通话", 51: "视频通话", 10000: "系统"}


def load(name):
    p = os.path.join(RAW, name)
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def fmt(ts):
    return datetime.fromtimestamp(int(ts), CST).strftime("%Y-%m-%d %H:%M:%S")


def basetype(t):
    v = int(t)
    return v % 4294967296 if v > 4294967295 else v


def typelabel(t):
    b = basetype(t)
    name = TYPE_MAP.get(b, f"类型{b}")
    return ("引用·" + name) if int(t) > 4294967295 else name


def has_cjk(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def analyze(doc, label):
    msgs = sorted(doc["messages"], key=lambda m: int(m["createTime"]))
    me = [m for m in msgs if int(m["isSend"]) == 1]
    other = [m for m in msgs if int(m["isSend"]) != 1]
    text_me = [m for m in me if basetype(m["localType"]) == 1]
    text_other = [m for m in other if basetype(m["localType"]) == 1]

    def chars(ms):
        return [len(re.sub(r"\[[^\]]{1,6}\]", "", m["content"] or "")) for m in ms]

    cm, co = chars(text_me), chars(text_other)

    # 会话轮次（连续同一方视为一轮）
    turns, last = 0, None
    for m in msgs:
        s = int(m["isSend"])
        if s != last:
            turns += 1
            last = s

    # 按年 / 按月分布
    by_year, by_month, by_hour = {}, {}, {}
    for m in msgs:
        d = datetime.fromtimestamp(int(m["createTime"]), CST)
        by_year[d.year] = by_year.get(d.year, 0) + 1
        by_month[d.strftime("%Y-%m")] = by_month.get(d.strftime("%Y-%m"), 0) + 1
        by_hour[d.hour] = by_hour.get(d.hour, 0) + 1

    # 会话日（不同日期数）与会话簇
    days = sorted({datetime.fromtimestamp(int(m["createTime"]), CST).date() for m in msgs})
    clusters = []
    for d in days:
        if clusters and (d - clusters[-1][-1]).days <= 1:
            clusters[-1].append(d)
        else:
            clusters.append([d])

    # 回复时延（对方→我 / 我→对方）
    lat_other, lat_me = [], []
    for i in range(1, len(msgs)):
        a, b = msgs[i - 1], msgs[i]
        dt = int(b["createTime"]) - int(a["createTime"])
        if dt > 7 * 86400 or dt < 0:
            continue
        if int(a["isSend"]) == 0 and int(b["isSend"]) == 1:
            lat_other.append(dt)
        elif int(a["isSend"]) == 1 and int(b["isSend"]) == 0:
            lat_me.append(dt)

    def med(xs):
        if not xs:
            return None
        xs = sorted(xs)
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    emoji = {}
    for m in msgs:
        for e in re.findall(r"\[([^\]]{1,6})\]", m["content"] or ""):
            emoji[e] = emoji.get(e, 0) + 1

    m = {
        "对象": label,
        "wxid": doc["talker"],
        "关系标注": doc.get("relation", ""),
        "消息总数": len(msgs),
        "我发送": len(me),
        "对方发送": len(other),
        "文本消息_我": len(text_me),
        "文本消息_对方": len(text_other),
        "非文本消息": len(msgs) - len(text_me) - len(text_other),
        "会话轮次": turns,
        "活跃日期数": len(days),
        "会话簇数": len(clusters),
        "时间范围": f"{fmt(msgs[0]['createTime'])} ~ {fmt(msgs[-1]['createTime'])}" if msgs else "",
        "跨度天数": (datetime.fromtimestamp(int(msgs[-1]["createTime"]), CST) -
                     datetime.fromtimestamp(int(msgs[0]["createTime"]), CST)).days if msgs else 0,
        "我_平均字数": round(sum(cm) / len(cm), 1) if cm else 0,
        "我_中位字数": med(cm),
        "对方_平均字数": round(sum(co) / len(co), 1) if co else 0,
        "对方_中位字数": med(co),
        "我_回复中位秒": med(lat_me),
        "对方_回复中位秒": med(lat_other),
        "按年分布": by_year,
        "按月分布": by_month,
        "按小时分布": by_hour,
        "表情使用": dict(sorted(emoji.items(), key=lambda kv: -kv[1])),
        "会话簇": [f"{c[0]} ~ {c[-1]}（{len(c)}天）" for c in clusters],
    }
    return m, msgs


docs = [
    ("刘华赞（赞赞姐）_聊天记录.json", "刘华赞（赞赞姐）"),
    ("华天雪_聊天记录.json", "华天雪"),
]

metrics_all, rows_all = [], []
for fn, label in docs:
    if not os.path.exists(os.path.join(RAW, fn)):
        print("缺少文件:", fn)
        continue
    m, msgs = analyze(load(fn), label)
    metrics_all.append(m)
    for x in msgs:
        rows_all.append({
            "对象": label,
            "时间": fmt(x["createTime"]),
            "方向": "我→对方" if int(x["isSend"]) == 1 else "对方→我",
            "类型": typelabel(x["localType"]),
            "字数": len(x["content"] or ""),
            "内容": (x["content"] or "").replace("\n", " ")[:500],
        })
    print(f"[{label}] {m['消息总数']} 条 / 我 {m['我发送']} / 对方 {m['对方发送']} / 轮次 {m['会话轮次']} / 活跃 {m['活跃日期数']} 天")

with io.open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics_all, f, ensure_ascii=False, indent=2)

with io.open(os.path.join(OUT, "messages.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["对象", "时间", "方向", "类型", "字数", "内容"])
    w.writeheader()
    w.writerows(rows_all)

print("已写出 metrics.json / messages.csv →", OUT)
