# -*- coding: utf-8 -*-
"""
用 ChatTrace 实时索引（index.sqlite）为刘华赞做分析数据导出 —— WeFlow 的替代口径。

与旧口径的对应关系：
  WeFlow  /api/v1/messages?talker=<wxid>   →  index.sqlite  messages WHERE session_key=<wxid>
  联系人卡片 /api/v1/contacts               →  contact.db（本脚本不依赖）
  共同群   /api/v1/group-members            →  sessions/messages 的 @chatroom 反查

输出（与既有目录结构一致，便于脚本复用）：
  00_原始导出/实时_<显示名>_聊天记录.json | .md | .txt
  02_结构化分析/messages_live.csv
  02_结构化分析/metrics_live.json
"""
from __future__ import annotations
import json, csv, io, os, re, sqlite3, sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT2 = os.path.join(ROOT, "02_结构化分析")
CST = timezone(timedelta(hours=8))

TARGETS = [
    ("wxid_ltqmzbyc87cp22", "刘华赞（赞赞姐）", "从小认识的朋友，母亲华天雪是刘丽萍的老朋友"),
    ("wxid_jycd1ii1qxro22", "华天雪", "刘华赞的母亲，刘丽萍的老朋友"),
]

TYPE_CN = {"text": "文本", "image": "图片", "voice": "语音", "card": "名片", "video": "视频",
           "sticker": "表情", "location": "位置", "link": "链接/卡片/文件",
           "voicecall": "语音通话", "videocall": "视频通话", "system": "系统",
           "文本消息": "文本", "图片消息": "图片", "语音消息": "语音", "视频消息": "视频",
           "动画表情": "表情", "链接消息": "链接/卡片/文件", "系统消息": "系统",
           "其他消息": "其他", "引用消息": "引用"}


def fmt(ts):
    return datetime.fromtimestamp(int(ts), CST).strftime("%Y-%m-%d %H:%M:%S") if ts else ""


def med(xs):
    if not xs:
        return None
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
metrics = []
csv_rows = []

for wxid, label, relation in TARGETS:
    rows = list(con.execute(
        """select id, ts, time_text, role, sender, type, content
           from messages where session_key=? order by ts, id""", (wxid,)))
    # 同 (ts, content) 只保留一条，避免索引残留重复影响统计
    seen_key, msgs = set(), []
    for r in rows:
        k = (r[1], (r[6] or "")[:120])
        if k in seen_key:
            continue
        seen_key.add(k)
        msgs.append(r)

    print(f"[{label}] 原始 {len(rows)} 行 → 去重 {len(msgs)} 条")

    me = [m for m in msgs if m[3] == "me"]
    them = [m for m in msgs if m[3] == "them"]
    text_me = [m for m in me if m[5] in ("text", "文本消息")]
    text_them = [m for m in them if m[5] in ("text", "文本消息")]

    def chars(ms):
        return [len(re.sub(r"\[[^\]]{1,6}\]", "", m[6] or "")) for m in ms]

    cm, co = chars(text_me), chars(text_them)
    turns, last = 0, None
    for m in msgs:
        s = m[3]
        if s != last:
            turns += 1
            last = s

    days = sorted({datetime.fromtimestamp(m[1], CST).date() for m in msgs if m[1]})
    lat_me, lat_them = [], []
    for i in range(1, len(msgs)):
        a, b = msgs[i - 1], msgs[i]
        if not a[1] or not b[1]:
            continue
        dt = int(b[1]) - int(a[1])
        if dt < 0 or dt > 7 * 86400:
            continue
        if a[3] == "them" and b[3] == "me":
            lat_them.append(dt)
        elif a[3] == "me" and b[3] == "them":
            lat_me.append(dt)

    emoji = {}
    for m in msgs:
        for e in re.findall(r"\[([^\]]{1,6})\]", m[6] or ""):
            emoji[e] = emoji.get(e, 0) + 1

    metrics.append({
        "对象": label, "wxid": wxid, "关系标注": relation, "数据源": "ChatTrace index.sqlite（WeFlow 替代口径）",
        "消息总数": len(msgs), "索引原始行数": len(rows), "重复行数": len(rows) - len(msgs),
        "我发送": len(me), "对方发送": len(them),
        "文本消息_我": len(text_me), "文本消息_对方": len(text_them),
        "非文本消息": len(msgs) - len(text_me) - len(text_them),
        "会话轮次": turns, "活跃日期数": len(days),
        "时间范围": f"{fmt(msgs[0][1])} ~ {fmt(msgs[-1][1])}" if msgs else "",
        "跨度天数": (datetime.fromtimestamp(msgs[-1][1]) - datetime.fromtimestamp(msgs[0][1])).days if msgs else 0,
        "我_平均字数": round(sum(cm) / len(cm), 1) if cm else 0, "我_中位字数": med(cm),
        "对方_平均字数": round(sum(co) / len(co), 1) if co else 0, "对方_中位字数": med(co),
        "我_回复中位秒": med(lat_me), "对方_回复中位秒": med(lat_them),
        "按年分布": {str(datetime.fromtimestamp(m[1], CST).year): 0 for m in msgs if m[1]} and
                    {y: sum(1 for m in msgs if m[1] and datetime.fromtimestamp(m[1], CST).year == int(y))
                     for y in sorted({str(datetime.fromtimestamp(m[1], CST).year) for m in msgs if m[1]})},
        "按月分布": {k: sum(1 for m in msgs if m[1] and datetime.fromtimestamp(m[1], CST).strftime("%Y-%m") == k)
                     for k in sorted({datetime.fromtimestamp(m[1], CST).strftime("%Y-%m") for m in msgs if m[1]})},
        "表情使用": dict(sorted(emoji.items(), key=lambda kv: -kv[1])),
    })

    # ---- 写原始档（json / md / txt）----
    obj = {
        "talker": wxid, "displayName": label, "relation": relation,
        "source": "ChatTrace realtime index (index.sqlite)", "exportedAt": datetime.now(CST).isoformat(),
        "totalCount": len(msgs),
        "messages": [{"id": m[0], "createTime": m[1], "formattedTime": m[2] or fmt(m[1]),
                      "role": m[3], "sender": m[4], "localType": m[5], "content": m[6]} for m in msgs],
    }
    with io.open(os.path.join(RAW, f"实时_{label}_聊天记录.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

    md = [f"# 与「{label}」的聊天记录（ChatTrace 实时口径）\n",
          f"- 对方 wxid：`{wxid}`", f"- 关系：{relation}",
          f"- 消息总数：{len(msgs)}", f"- 导出时间：{datetime.now(CST):%Y-%m-%d %H:%M:%S}"]
    if msgs:
        md.append(f"- 时间范围：{fmt(msgs[0][1])} ~ {fmt(msgs[-1][1])}")
    md += ["", "---", ""]
    txt = [f"与「{label}」的聊天记录（共 {len(msgs)} 条）", "=" * 50, ""]
    for m in msgs:
        who = "我" if m[3] == "me" else label
        c = (m[6] or "").strip() or "[空]"
        md.append(f"**[{fmt(m[1])}] {who}：** {c}\n")
        txt.append(f"[{fmt(m[1])}] {who}：{c}")
        csv_rows.append({"对象": label, "时间": fmt(m[1]), "方向": "我→对方" if m[3] == "me" else "对方→我",
                         "类型": TYPE_CN.get(m[5], m[5]), "内容": c.replace("\n", " ")[:500]})
    with io.open(os.path.join(RAW, f"实时_{label}_聊天记录.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with io.open(os.path.join(RAW, f"实时_{label}_聊天记录.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(txt))

with io.open(os.path.join(OUT2, "metrics_live.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)
with io.open(os.path.join(OUT2, "messages_live.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["对象", "时间", "方向", "类型", "内容"])
    w.writeheader()
    w.writerows(csv_rows)

print("\n已写出 metrics_live.json / messages_live.csv 与 实时_*_聊天记录.{json,md,txt}")
for m in metrics:
    print(f"  {m['对象']}: {m['消息总数']} 条（我 {m['我发送']} / 对方 {m['对方发送']}）"
          f" 重复行 {m['重复行数']} | {m['时间范围']}")
