# -*- coding: utf-8 -*-
"""为 54 条 MISS 生成「手机点开清单」：带前后文 + 项目相关性标注。"""
import json, csv, os, re, datetime, collections

JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
CSV_P = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\01_定位索引.csv"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\03_待补图片_手机点开清单.md"

KEY = ["井邻", "工作站", "怀柔", "丝网", "版画", "洞台", "乡村美育", "中期", "汇报",
       "展览", "海报", "工作坊", "美术馆", "美育", "印刷", "刮刀", "油墨", "纸",
       "澜沧", "甲马", "木刻", "材料", "装置", "光", "稿", "方案", "文献", "论文",
       "展签", "前言", "序", "厅", "布展", "拍摄", "采访"]

msgs = json.load(open(JSON_P, encoding="utf-8"))
# 只保留陈晔会话
msgs = [m for m in msgs if isinstance(m, dict) and "createTime" in m]
msgs.sort(key=lambda x: int(x["createTime"]))
by_ts = collections.defaultdict(list)
for i, m in enumerate(msgs):
    by_ts[int(m["createTime"])].append(i)

def txt(m):
    lt = str(m.get("localType"))
    c = (m.get("content") or "").strip()
    if lt == "3":
        return "[图片]"
    if lt == "49":
        return "[引用] " + re.sub(r"\s+", " ", c)[:60]
    if lt == "47":
        return "[表情]"
    if lt == "43":
        return "[视频]"
    if lt in ("34",):
        return "[语音]"
    if lt == "10000":
        return "[系统] " + re.sub(r"\s+", " ", c)[:40]
    if lt not in ("1",):
        return "[" + lt + "] " + re.sub(r"\s+", " ", c)[:50]
    return re.sub(r"\s+", " ", c)[:90]

rows = list(csv.DictReader(open(CSV_P, encoding="utf-8-sig")))
miss = [r for r in rows if not r["解密产物"]]

# 项目锚定日：±6 条窗口内出现关键词
def anchored(idx):
    lo, hi = max(0, idx - 6), min(len(msgs), idx + 7)
    blob = " ".join((msgs[j].get("content") or "") for j in range(lo, hi))
    hit = [k for k in KEY if k in blob]
    return hit

L = []
L.append("# 待补图片 · 手机点开清单")
L.append("")
L.append("> 陈晔会话 654 张图片中，**54 张微信未落盘**（服务器只存了缩略图元数据，本地无原始 `.dat`）。")
L.append("> 补法：在**手机微信**打开与陈晔的聊天，**长按 → 逐张点开**（或转发到文件传输助手），")
L.append("> 微信会把原图拉回本地 → 重跑 `rebuild_imgs_v2.py` 即自动归档。")
L.append("")
L.append("- 生成时间：2026-10-14")
L.append("- 当前归档：**600 / 654（91.7%）**")
L.append("- 待补：**54 张**")
L.append("- ★ = 该时段上下文含项目关键词（井邻 / 丝网 / 版画 / 中期汇报 …），**优先补**")
L.append("")
L.append("---")
L.append("")

# 按年月分组
g = collections.OrderedDict()
for r in miss:
    g.setdefault(r["月份"], []).append(r)

star_dates = []
for ym, items in g.items():
    L.append("## %s　（%d 张）" % (ym, len(items)))
    L.append("")
    L.append("| # | 时间 | 发送方 | 上下文（前后各 2 条） | 项目相关 |")
    L.append("|---|---|---|---|---|")
    for n, r in enumerate(items, 1):
        ts = int(datetime.datetime.strptime(r["时间"], "%Y-%m-%d %H:%M:%S").timestamp())
        # 找最接近的消息
        idx = None
        for cand in sorted(by_ts.keys(), key=lambda t: abs(t - ts)):
            if abs(cand - ts) <= 3:
                idx = by_ts[cand][0]; break
        ctx = ""
        hits = []
        if idx is not None:
            lo, hi = max(0, idx - 2), min(len(msgs), idx + 3)
            parts = []
            for j in range(lo, hi):
                who = "我" if str(msgs[j].get("isSend")) == "1" else "陈"
                mark = "**" if j == idx else ""
                parts.append("%s%s：%s%s" % (mark, who, txt(msgs[j]), mark))
            ctx = " ／ ".join(parts)
            hits = anchored(idx)
        flag = "★ " + "、".join(hits[:4]) if hits else ""
        if hits:
            star_dates.append(r["时间"])
        L.append("| %d | %s | %s | %s | %s |" % (n, r["时间"], r["发送方"], ctx.replace("|", "／"), flag))
    L.append("")

L.append("---")
L.append("")
L.append("## 补图操作步骤")
L.append("")
L.append("1. 手机微信 → 与 **陈晔** 的聊天 → 按上表时间**拉到对应日期**")
L.append("2. 逐张**点开图片**（不必保存，点开即触发下载；`hd` 原图可点「查看原图」）")
L.append("3. 回到电脑，重跑：")
L.append("")
L.append("```")
L.append("cd \"C:\\Users\\wardc\\WorkBuddy AI\\2026-10-06-14-09-21\\_tmp_1012\"")
L.append("\"C:\\Users\\wardc\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" rebuild_imgs_v2.py")
L.append("```")
L.append("")
L.append("4. 脚本会自动补齐并重写 `01_定位索引.csv`")
L.append("")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("写出:", OUT)
print("MISS:", len(miss), " 其中项目相关:", len(star_dates))
