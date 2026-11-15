# -*- coding: utf-8 -*-
"""朋友圈统计：发布节奏、内容分类、互动、主题频次 → 02_结构化分析/moments_stats.json + 报告表格"""
import json, io, os, sys, re
from datetime import datetime, timedelta, timezone
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT2 = os.path.join(ROOT, "02_结构化分析")
CST = timezone(timedelta(hours=8))
posts = json.load(io.open(os.path.join(RAW, "朋友圈_刘华赞_raw.json"), encoding="utf-8"))["timeline"]


def fmt(ts):
    return datetime.fromtimestamp(int(ts), CST)


THEMES = {
    "古建/历史建筑": ["云博", "金殿", "筇竹寺", "长春电影制片厂", "伪满", "中央银行", "神武堂", "八大部", "松苑", "法衙"],
    "旅行/城市漫步": ["斗南花市", "海埂大坝", "在夏天到来之前", "长春", "平行世界"],
    "艺术展览/艺术资讯": ["八大山人", "圣家堂", "高迪", "霍克尼", "波点", "国家画院", "悉尼", "海纳百川", "R.I.P."],
    "美食": ["吃郎"],
    "音乐/短视频": ["COMPLICATED", "FLASHLIGHT"],
    "节日/生活情绪": ["中秋快乐", "平行世界", "彩色的波点"],
}

rows, theme_ct = [], Counter()
for p in posts:
    d = fmt(p["createTime"])
    txt = p.get("contentDesc") or ""
    tags = [t for t, kws in THEMES.items() if any(k in txt for k in kws)]
    if p.get("type") in (7, 15):
        tags.append("视频")
    for t in tags:
        theme_ct[t] += 1
    likes = p.get("likes") or []
    cmts = p.get("comments") or []
    rows.append({
        "发布时间": d.strftime("%Y-%m-%d %H:%M:%S"),
        "星期": "一二三四五六日"[d.weekday()],
        "时段": d.strftime("%H:%M"),
        "类型": {1: "图文", 3: "文章/链接卡片", 7: "视频", 15: "小视频"}.get(p.get("type"), str(p.get("type"))),
        "正文": txt.replace("\n", " ⏎ "),
        "媒体数": len(p.get("media") or []),
        "点赞数": len(likes),
        "点赞人": "、".join(likes),
        "评论数": len(cmts),
        "评论": "；".join(f"{c.get('nickname')}：{c.get('content')}" for c in cmts),
        "标签": "/".join(dict.fromkeys(tags)),
    })

rows.sort(key=lambda r: r["发布时间"])
counts = Counter(r["类型"] for r in rows)
hours = Counter(int(r["时段"][:2]) for r in rows)
weeks = Counter(r["星期"] for r in rows)
months = Counter(r["发布时间"][:7] for r in rows)
like_people, cmt_people = Counter(), Counter()
for p in posts:
    like_people.update(p.get("likes") or [])
    cmt_people.update(c.get("nickname") for c in (p.get("comments") or []))

total_media = sum(r["媒体数"] for r in rows)
stats = {
    "统计时间": "2026-09-26",
    "对象": "刘华赞（赞赞姐）wxid_ltqmzbyc87cp22",
    "动态总数": len(rows),
    "时间范围": f"{rows[0]['发布时间']} ~ {rows[-1]['发布时间']}",
    "跨度天数": (fmt(posts[-1]["createTime"]) - fmt(posts[0]["createTime"])).days,
    "月均条数": round(len(rows) / max(1, ((fmt(posts[-1]["createTime"]) - fmt(posts[0]["createTime"])).days / 30.4)), 2),
    "类型分布": dict(counts),
    "月度分布": dict(sorted(months.items())),
    "发布时间小时分布": dict(sorted(hours.items())),
    "星期分布": dict(weeks),
    "媒体总量": total_media,
    "带图动态": sum(1 for r in rows if r["媒体数"] > 0),
    "零互动动态": sum(1 for r in rows if r["点赞数"] == 0 and r["评论数"] == 0),
    "点赞人榜": dict(like_people.most_common()),
    "评论人榜": dict(cmt_people.most_common()),
    "主题频次": dict(theme_ct.most_common()),
    "我给她点赞次数": like_people.get("蔡浩文", 0),
    "母亲给她点赞次数": like_people.get("刘丽萍", 0),
    "母亲给她评论次数": cmt_people.get("刘丽萍", 0),
    "她给我点赞次数": 0,
    "她给母亲点赞次数": 0,
    "她点赞/评论他人次数": 0,
    "明细": rows,
}

with io.open(os.path.join(OUT2, "moments_stats.json"), "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

import csv
with io.open(os.path.join(OUT2, "moments_刘华赞.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(json.dumps({k: v for k, v in stats.items() if k != "明细"}, ensure_ascii=False, indent=2))
