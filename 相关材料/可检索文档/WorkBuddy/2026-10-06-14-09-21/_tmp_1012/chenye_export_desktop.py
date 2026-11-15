# -*- coding: utf-8 -*-
"""导出陈晔（deerluna）会话全量聊天记录 → 桌面，格式对齐 2026-09-15 旧导出。
输入: _chenye_all.jsonl
输出目录: Desktop\中期汇报_2026-09\04_聊天记录数据\陈晔导师聊天记录_2026-10-12导出\
"""
import json, os, re, datetime

TMP = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\04_聊天记录数据\陈晔导师聊天记录_2026-10-12导出"
os.makedirs(OUT, exist_ok=True)

rows = [json.loads(l) for l in open(os.path.join(TMP, "_chenye_all.jsonl"), encoding="utf-8")]
rows.sort(key=lambda r: r["t"])

# ---------- 类型标签 ----------
def label(lt):
    main = lt & 0xFFFFFFFF
    sub = lt >> 32
    if main == 1:   return "文字"
    if main == 42:  return "名片"
    if main == 48:  return "位置"
    if main == 50:  return "通话"
    if main == 3:   return "图片"
    if main == 34:  return "语音"
    if main == 43:  return "视频"
    if main == 47:  return "表情"
    if main == 10000: return "系统"
    if main == 49:
        return {5: "链接", 6: "文件", 51: "视频号", 57: "引用", 33: "小程序",
                36: "小程序", 87: "群公告", 2000: "转账", 2001: "红包"}.get(sub, "应用消息(%d)" % sub)
    return "类型%d" % lt

# ---------- 实质性判定（去掉「收到老师」这类空转） ----------
FLUFF = re.compile(r"^(好的?|收到|明白|嗯+|哦+|是的?|对|谢谢|感谢老师|好的老师|收到老师|明白老师|好|OK|ok)[！!。，,\s]*$")

def substantive(r):
    b = r["body"].strip()
    if r["type"] != 1:
        return True                      # 媒体类都保留
    if len(b) < 8:
        return False
    if FLUFF.match(b):
        return False
    cjk = len(re.findall(r"[\u4e00-\u9fff]", b))
    return cjk / max(len(b), 1) > 0.35

# ---------- 1) JSON ----------
js = {
    "talker": "deerluna",
    "displayName": "导师陈晔",
    "remark": "导！急速回，三思回得体！！！",
    "myWxid": "wxid_zn4ozsnn8esr21",
    "exportedAt": datetime.datetime.now().astimezone().isoformat(),
    "source": "ChatTrace 解密库 message_0.db / message_1.db",
    "totalCount": len(rows),
    "rangeStart": rows[0]["dt"],
    "rangeEnd": rows[-1]["dt"],
    "messages": [{
        "createTime": r["t"],
        "datetime": r["dt"],
        "localType": r["type"],
        "typeLabel": label(r["type"]),
        "sender": r["who"],
        "senderId": r["sender"],
        "srcDb": r["src"],
        "content": r["body"],
    } for r in rows],
}
p_json = os.path.join(OUT, "陈晔_导师_聊天记录_2026-10-12.json")
json.dump(js, open(p_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 2) TXT ----------
tl = ["与「导师陈晔」的聊天记录（共 %d 条）" % len(rows),
      "时间范围：%s ~ %s" % (rows[0]["dt"], rows[-1]["dt"]),
      "导出时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "来源：ChatTrace 解密库（message_0.db / message_1.db）",
      "=" * 50, ""]
for r in rows:
    body = r["body"].replace("\n", " ⏎ ").strip()
    if r["type"] != 1:
        body = "［%s］%s" % (label(r["type"]), body or "(无文本)")
    tl.append("[%s] %s：%s" % (r["dt"], "导师陈晔" if r["who"] == "陈晔" else "我", body))
open(os.path.join(OUT, "陈晔_导师_聊天记录_2026-10-12.txt"), "w", encoding="utf-8").write("\n".join(tl))

# ---------- 3) MD ----------
md = ["# 与「导师陈晔」的聊天记录（2026-10-12 导出）", "",
      "- 对方 wxid：`deerluna`　备注：导！急速回，三思回得体！！！",
      "- 消息总数：**%d**" % len(rows),
      "- 时间范围：%s ~ %s" % (rows[0]["dt"], rows[-1]["dt"]),
      "- 导出时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "- 来源：ChatTrace 解密库 `message_0.db`（6,495 条）+ `message_1.db`（792 条）",
      "", "---", ""]
for r in rows:
    body = r["body"].replace("\n", " ⏎ ").strip()
    if r["type"] != 1:
        body = "［%s］%s" % (label(r["type"]), body or "(无文本)")
    md.append("**[%s] %s：** %s" % (r["dt"], "导师陈晔" if r["who"] == "陈晔" else "我", body))
open(os.path.join(OUT, "陈晔_导师_聊天记录_2026-10-12.md"), "w", encoding="utf-8").write("\n\n".join(md))

# ---------- 4) 实质性消息摘要 ----------
sub = [r for r in rows if substantive(r)]
sl = ["# 实质性消息摘要（去掉寒暄空转，共 %d / %d 条）" % (len(sub), len(rows)),
      "# 时间范围：%s ~ %s" % (rows[0]["dt"], rows[-1]["dt"]),
      "# 规则：文字 <8 字或纯应答（收到/好的/明白…）剔除；媒体类全部保留",
      "=" * 60, ""]
for r in sub:
    body = r["body"].replace("\n", " ⏎ ").strip()
    if r["type"] != 1:
        body = "［%s］%s" % (label(r["type"]), body or "(无文本)")
    sl.append("[%s] %s | %s" % (r["dt"][:16], "陈" if r["who"] == "陈晔" else "我", body))
open(os.path.join(OUT, "_实质性消息摘要.txt"), "w", encoding="utf-8").write("\n".join(sl))

# ---------- 5) 井邻相关全量 ----------
ANCHOR = ["井邻", "洞台", "渤海镇", "工作站", "怀柔", "乡村美育", "开街", "低碳", "王总", "关总", "王华青"]
jing = [r for r in rows if any(k in r["body"] for k in ANCHOR)]
jl = ["# 井邻（乡村美育工作站）相关消息 · 项目锚定口径", "",
      "- 命中 **%d 条**，覆盖 **%d 天**" % (len(jing), len({r["day"] for r in jing})),
      "- 锚定词：井邻 / 洞台 / 渤海镇 / 工作站 / 怀柔 / 乡村美育 / 开街 / 低碳 / 王总 / 关总 / 王华青",
      "", "---", ""]
cur = None
for r in jing:
    if r["day"] != cur:
        cur = r["day"]; jl.append("\n## %s\n" % cur)
    body = r["body"].replace("\n", " ⏎ ").strip()
    if r["type"] != 1:
        body = "［%s］%s" % (label(r["type"]), body or "(无文本)")
    jl.append("- `%s` **[%s]** %s" % (r["dt"][11:16], "陈" if r["who"] == "陈晔" else "我", body))
open(os.path.join(OUT, "井邻相关_项目锚定_%d条.md" % len(jing)), "w", encoding="utf-8").write("\n".join(jl))

# ---------- 6) 统计 ----------
from collections import Counter
print("总条数:", len(rows))
print("范围:", rows[0]["dt"], "→", rows[-1]["dt"])
print("谁说的:", Counter(r["who"] for r in rows))
print("类型:", Counter(label(r["type"]) for r in rows))
print("实质性:", len(sub))
print("井邻锚定:", len(jing), "条 /", len({r["day"] for r in jing}), "天")
for f in sorted(os.listdir(OUT)):
    print("  %-52s %10d B" % (f, os.path.getsize(os.path.join(OUT, f))))
