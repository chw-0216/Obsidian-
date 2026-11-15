# -*- coding: utf-8 -*-
"""
build_readable.py — 把 09 导出的原始 JSON 转成「可读对话文本」

输出：_tmp/readable/<会话名>.txt
格式：按天分组，每行 [HH:MM] 我/TA: 内容
     非文本消息折叠成 [图片]/[表情]/[语音] 等标记，连续重复合并计数
用法：
  python build_readable.py                 # 全部会话
  python build_readable.py --min 20        # 只转消息数 >= 20 的会话
  python build_readable.py --since 1784822400   # 只要 2026-07-24 之后
"""
import json
import os
import re
import sys
import time
import argparse
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\09_WeFlow增量导出_2026-09-29\01_WeFlow可读导出"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\readable"

TYPE_LABEL = {
    1: None, 47: "[表情]", 3: "[图片]", 34: "[语音]", 43: "[视频]",
    42: "[名片]", 48: "[位置]", 49: "[文件]", 50: "[通话]",
    10000: "[系统]", 10002: "[系统]",
}
SYS_TEXTS = ("我通过了你的朋友验证请求", "以上是打招呼的消息", "撤回了一条消息",
             "你已添加了", "开启了朋友验证", "现在可以开始聊天了")


def clean(m):
    """把一条消息转成一行文本；返回 None 表示丢弃"""
    lt = m.get("localType")
    c = (m.get("content") or "").strip()
    if not c:
        return None

    if lt == 1:
        pass
    elif lt == 244813135921:      # 引用回复
        pass
    elif lt in TYPE_LABEL:
        return TYPE_LABEL[lt]
    else:
        # appmsg：尽量抽 title
        t = re.search(r"<title>(.*?)</title>", m.get("rawContent") or "", re.S)
        if t and t.group(1).strip():
            return "[链接] " + re.sub(r"<[^>]+>", "", t.group(1))[:60]
        return "[其他]"

    if any(s in c for s in SYS_TEXTS):
        return None
    # 去掉 XML 残留
    if c.startswith("<") and ">" in c:
        t = re.search(r"<title>(.*?)</title>", c, re.S)
        if t:
            c = re.sub(r"<[^>]+>", "", t.group(1)).strip()
        else:
            return "[其他]"
    c = c.replace("\n", " ").strip()
    return c or None


def who(m, is_group):
    if not is_group:
        return "我" if m.get("isSend") else "TA"
    return "我" if m.get("isSend") else "群友"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=0)
    ap.add_argument("--since", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    files = []
    for d in os.listdir(BASE):
        p = os.path.join(BASE, d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if fn.endswith(".json"):
                files.append(os.path.join(p, fn))

    done = 0
    for fp in files:
        try:
            j = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        ms = j.get("messages") or []
        if args.since:
            ms = [m for m in ms if (m.get("createTime") or 0) >= args.since]
        if len(ms) < args.min or not ms:
            continue
        ms.sort(key=lambda m: (m.get("createTime") or 0, m.get("sortSeq") or 0))
        name = j.get("displayName") or os.path.basename(fp)[:-5]
        is_group = (j.get("sessionType") == "group") or ("@chatroom" in (j.get("talker") or ""))

        lines = [f"# {name}   共 {len(ms)} 条   "
                 f"{time.strftime('%Y-%m-%d', time.localtime(ms[0]['createTime']))} ~ "
                 f"{time.strftime('%Y-%m-%d', time.localtime(ms[-1]['createTime']))}", ""]
        cur_day = None
        prev = None
        repeat = 0

        def flush():
            nonlocal prev, repeat
            if prev is not None:
                lines.append(prev + (f"   ×{repeat}" if repeat > 1 else ""))
            prev, repeat = None, 0

        for m in ms:
            t = m.get("createTime") or 0
            day = time.strftime("%Y-%m-%d", time.localtime(t))
            if day != cur_day:
                flush()
                lines.append("")
                lines.append(f"═══ {day} ═══")
                cur_day = day
            txt = clean(m)
            if not txt:
                continue
            line = f"[{time.strftime('%H:%M', time.localtime(t))}] {who(m, is_group)}: {txt}"
            # 连续重复折叠
            if txt.startswith("[") and prev and prev.endswith(txt):
                repeat += 1
                continue
            flush()
            prev = line
            repeat = 1
        flush()

        safe = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip()[:60]
        out = os.path.join(OUT, f"{safe}.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        done += 1
        print(f"  {len(ms):>6} 条 → {safe}.txt")

    print(f"\n共写出 {done} 个文本文件 → {OUT}")


if __name__ == "__main__":
    main()
