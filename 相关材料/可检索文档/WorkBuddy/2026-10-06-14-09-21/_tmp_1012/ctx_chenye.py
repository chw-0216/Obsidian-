# -*- coding: utf-8 -*-
"""陈晔会话：给 654 条图片消息配上「前后文」，输出可读索引。
用途：不逐张看图，靠对话原文判断每张图在讲什么、能补到哪一页。
"""
import json, os, re, datetime, collections, csv

JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\17_陈晔会话图片全量定位_2026-10-12"
IDX = os.path.join(OUT, "01_定位索引.csv")

msgs = json.load(open(JSON_P, encoding="utf-8"))
msgs.sort(key=lambda m: int(m["createTime"]))

def txt(m):
    """把一条消息压成一行可读文本"""
    lt = str(m.get("localType"))
    c = m.get("content") or ""
    if lt == "1":
        return re.sub(r"\s+", " ", c).strip()
    if lt == "3":
        return "[图片]"
    if lt == "43":
        return "[视频]"
    if lt == "50":
        return "[通话]"
    if lt == "47":
        return "[表情]"
    if lt == "34":
        return "[语音]"
    # appmsg 类
    t = re.search(r"<title>(.*?)</title>", c, re.S)
    if t:
        return "[链接]" + re.sub(r"\s+", " ", t.group(1)).strip()[:80]
    return "[" + lt + "]"

# 索引 CSV 的「解密产物」映射
rows = list(csv.DictReader(open(IDX, encoding="utf-8-sig")))
prod = {r["时间"]: r["解密产物"] for r in rows}
lvl = {r["时间"]: r["清晰度档"] for r in rows}

W = 3   # 前后各取 3 条
recs = []
for i, m in enumerate(msgs):
    if str(m.get("localType")) != "3":
        continue
    ts = int(m["createTime"])
    key = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    before = [txt(x) for x in msgs[max(0, i - W):i]]
    after = [txt(x) for x in msgs[i + 1:i + 1 + W]]
    recs.append({
        "时间": key,
        "发送方": "我" if str(m.get("isSend")) == "1" else "陈晔",
        "档": lvl.get(key, ""),
        "产物": prod.get(key, ""),
        "前文": " ｜ ".join(x for x in before if x),
        "后文": " ｜ ".join(x for x in after if x),
    })

print("图片条数:", len(recs))

# 1) 全量可读日志
with open(os.path.join(OUT, "02_图片上下文索引.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
    w.writeheader(); w.writerows(recs)
print("-> 02_图片上下文索引.csv")

# 2) 按月分组的可读 markdown
by = collections.defaultdict(list)
for r in recs:
    by[r["时间"][:7]].append(r)
lines = ["# 陈晔会话 · 图片上下文日志", "",
         "> 每条图片消息附前后各 3 条消息原文，用于判断该图在讲什么。", ""]
for ym in sorted(by):
    lines.append(f"## {ym}（{len(by[ym])} 张）")
    lines.append("")
    for r in by[ym]:
        lines.append(f"- **{r['时间'][11:16]}** {r['发送方']} [{r['档']}]")
        if r["前文"]:
            lines.append(f"    - 前：{r['前文'][:220]}")
        if r["后文"]:
            lines.append(f"    - 后：{r['后文'][:220]}")
    lines.append("")
open(os.path.join(OUT, "02_图片上下文日志.md"), "w", encoding="utf-8").write("\n".join(lines))
print("-> 02_图片上下文日志.md")

# 3) 关键词分类（粗筛「可作补充」的方向）
KW = {
    "井邻/工作站": ["井邻", "工作站", "洞台", "78号", "339号", "丝网", "网版", "制版", "版画", "印"],
    "澜沧/美育": ["澜沧", "支教", "美育", "课程", "课堂", "学生", "孩子", "问卷"],
    "接待/领导": ["接待", "书记", "区长", "局长", "领导", "文旅", "政协", "组织部", "宣传部", "科学家"],
    "数字人/交互": ["数字人", "交互", "手势", "mediapipe", "gesture", "ollama", "模型", "界面", "网页", "原型"],
    "材料实验": ["木版", "木刻", "石版", "蜡染", "材料实验", "冰醋酸", "四型", "悲鸿"],
    "论文/研究": ["论文", "开题", "研究", "文献", "综述", "解放军文艺"],
    "展览/活动": ["展览", "展位", "海报", "开幕", "活动", "市集", "现场"],
    "排版/设计": ["海报", "排版", "设计稿", "主视觉", "封面", "字体"],
}
cnt = collections.Counter()
hit = collections.defaultdict(list)
for r in recs:
    blob = (r["前文"] + " " + r["后文"]).lower()
    for cat, kws in KW.items():
        if any(k.lower() in blob for k in kws):
            cnt[cat] += 1
            hit[cat].append(r)
print()
print("按上下文关键词粗分类（可重叠）:")
for cat, n in cnt.most_common():
    print(f"  {cat:12s} {n:3d}")

with open(os.path.join(OUT, "03_按主题粗筛.md"), "w", encoding="utf-8") as f:
    f.write("# 陈晔会话图片 · 按上下文主题粗筛\n\n")
    f.write("> 依据每条图片消息前后各 3 条消息的原文关键词归类，**同一张可落入多类**。\n\n")
    for cat, n in cnt.most_common():
        f.write(f"## {cat}（{n} 张）\n\n")
        for r in hit[cat][:60]:
            f.write(f"- {r['时间']} {r['发送方']} [{r['档']}] — {r['前文'][:150] or r['后文'][:150]}\n")
        if len(hit[cat]) > 60:
            f.write(f"- …另 {len(hit[cat])-60} 张\n")
        f.write("\n")
print("-> 03_按主题粗筛.md")
