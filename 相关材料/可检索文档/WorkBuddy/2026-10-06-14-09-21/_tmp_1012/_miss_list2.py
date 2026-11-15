# -*- coding: utf-8 -*-
"""为 MISS 生成「手机点开清单」：带前后文 + 项目相关性标注。v2 可读性优化。"""
import json, csv, os, re, datetime, collections

JSON_P = r"C:\Users\wardc\Desktop\导_聊天记录.json"
CSV_P = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\01_定位索引.csv"
OUT = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\03_待补图片_手机点开清单.md"

# 只保留强项目词，避免「纸/光/稿」这类单字误标
STRONG = ["井邻", "工作站", "怀柔", "丝网", "版画", "洞台", "乡村美育", "中期汇报",
          "工作坊", "海报", "澜沧", "甲马", "木刻", "中期", "汇报", "布展", "展签"]

msgs = [m for m in json.load(open(JSON_P, encoding="utf-8"))
        if isinstance(m, dict) and "createTime" in m]
msgs.sort(key=lambda x: int(x["createTime"]))
by_ts = collections.defaultdict(list)
for i, m in enumerate(msgs):
    by_ts[int(m["createTime"])].append(i)

XML_RE = re.compile(r"<\?xml|&lt;\?xml")

def txt(m):
    lt = str(m.get("localType"))
    c = (m.get("content") or "").strip()
    c = re.sub(r"^\[\d{6,}\]\s*", "", c)              # 去掉 [25769803825] 这类前缀
    if lt == "3":  return "🖼 图片"
    if lt == "43": return "🎬 视频"
    if lt == "47": return "😀 表情"
    if lt == "34": return "🎤 语音"
    if lt == "49": return "↩ 引用：" + re.sub(r"\s+", " ", c)[:34]
    if lt == "10000": return "⚙ " + re.sub(r"\s+", " ", c)[:30]
    if XML_RE.search(c):
        mm = re.search(r"<title>(.*?)</title>", c)
        return "🔗 " + (mm.group(1)[:30] if mm else "卡片消息")
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?|zip|rar)$", c, re.I):
        return "📄 " + c[:34]
    if c.startswith("http"):
        return "🔗 链接"
    if lt != "1":
        return "[" + lt + "] " + re.sub(r"\s+", " ", c)[:30]
    c = re.sub(r"\s+", " ", c)
    return (c[:36] + "…") if len(c) > 36 else c

rows = list(csv.DictReader(open(CSV_P, encoding="utf-8-sig")))
miss = [r for r in rows if not r["解密产物"]]

def pick(ts):
    """优先取同一秒的图片消息本身；否则取最近的一条。"""
    for t in (ts, ts - 1, ts + 1, ts - 2, ts + 2, ts - 3, ts + 3):
        if t in by_ts:
            ids = by_ts[t]
            for j in ids:
                if str(msgs[j].get("localType")) == "3":
                    return j
            return ids[0]
    return None

def hits(idx):
    lo, hi = max(0, idx - 6), min(len(msgs), idx + 7)
    blob = " ".join((msgs[j].get("content") or "") for j in range(lo, hi))
    return [k for k in STRONG if k in blob]

L = []
A = L.append
A("# 待补图片 · 手机点开清单")
A("")
A("> 陈晔会话 **654** 张图片中，**54 张微信未落盘** —— 服务端只留了缩略图元数据，")
A("> 本地没有原始 `.dat`，脚本无法解密。**只能靠手机端点开触发下载**。")
A("")
A("| 项 | 值 |")
A("|---|---|")
A("| 生成时间 | 2026-10-14 |")
A("| 当前归档 | **600 / 654（91.7%）** |")
A("| 待补 | **54 张**（★ 项目相关 **@@STAR@@ 张**）|")
A("| 归档位置 | `Desktop\\07_聊天记录分析\\陈晔会话图片_2026-10-14\\` |")
A("| 索引文件 | `01_定位索引.csv`（654 行）|")
A("")
A("**图例**　★ = 该时段上下文出现项目关键词（井邻 / 工作站 / 丝网 / 版画 / 工作坊 …）→ **优先补**")
A("")
A("---")
A("")

g = collections.OrderedDict()
for r in miss:
    g.setdefault(r["月份"], []).append(r)

star = 0
body = []
for ym, items in g.items():
    body.append("## %s　（%d 张）" % (ym, len(items)))
    body.append("")
    body.append("| # | 时间 | 发送方 | 前后文（← 前 · **本条** · 后 →）| 项目词 |")
    body.append("|:--:|---|:--:|---|---|")
    for n, r in enumerate(items, 1):
        ts = int(datetime.datetime.strptime(r["时间"], "%Y-%m-%d %H:%M:%S").timestamp())
        idx = pick(ts)
        ctx, hs = "", []
        if idx is not None:
            lo, hi = max(0, idx - 2), min(len(msgs), idx + 3)
            parts = []
            for j in range(lo, hi):
                who = "我" if str(msgs[j].get("isSend")) == "1" else "陈"
                s = "%s %s" % (who, txt(msgs[j]))
                parts.append("**%s**" % s if j == idx else s)
            ctx = " · ".join(parts)
            hs = hits(idx)
        if hs:
            star += 1
            flag = "★ " + "／".join(hs[:3])
        else:
            flag = "—"
        body.append("| %d | %s | %s | %s | %s |" % (
            n, r["时间"], r["发送方"], ctx.replace("|", "／"), flag))
    body.append("")

L = [x.replace("@@STAR@@", str(star)) if "@@STAR@@" in x else x for x in L]
L.extend(body)
A("---")
A("")
A("## 补图操作")
A("")
A("1. 手机微信 → 与 **陈晔** 的聊天 → 按上表时间拉到对应日期")
A("2. 逐张 **点开图片**（点开即触发下载；有「查看原图」的再点一次拿 `hd`）")
A("3. 电脑上重跑（约 3 秒）：")
A("")
A("```")
A('cd "C:\\Users\\wardc\\WorkBuddy AI\\2026-10-06-14-09-21\\_tmp_1012"')
A('"C:\\Users\\wardc\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" rebuild_imgs_v2.py')
A("```")
A("")
A("4. 脚本自动补齐并重写 `01_定位索引.csv`（已归档数会同步上升）")
A("")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("写出:", OUT)
print("MISS:", len(miss), "★:", star)
