# -*- coding: utf-8 -*-
"""
手机能力判定（技能第 0 步）—— 一次性跑完所有探针，写报告。

用法：python tools/phone_probe.py
产出：_tmp\\phone\\probe_report.txt  +  _tmp\\phone\\probe.json

★ 一律串行（技能坑 1：adb 不可并发）。
★ 每条探针独立超时，失败不中断后面的。
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adb_run import run, ADB  # noqa: E402

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(WS, "_tmp", "phone")
REPORT = os.path.join(OUTDIR, "probe_report.txt")
JSONF = os.path.join(OUTDIR, "probe.json")

PROBES = [
    ("设备列表", ["devices", "-l"], 60),
    ("型号", ["shell", "getprop", "ro.product.model"], 30),
    ("品牌", ["shell", "getprop", "ro.product.brand"], 30),
    ("Android版本", ["shell", "getprop", "ro.build.version.release"], 30),
    ("SDK", ["shell", "getprop", "ro.build.version.sdk"], 30),
    ("序列号", ["shell", "getprop", "ro.serialno"], 30),
    ("shell身份", ["shell", "id"], 30),
    ("有无root", ["shell", "which su"], 30),
    ("/sdcard顶层", ["shell", "ls /sdcard/"], 60),
    ("通讯录", ["exec-out", "content", "query",
               "--uri", "content://com.android.contacts/contacts",
               "--projection", "display_name"], 120),
    ("短信", ["exec-out", "content", "query",
             "--uri", "content://sms", "--projection", "_id"], 120),
    ("通话记录", ["exec-out", "content", "query",
                 "--uri", "content://call_log/calls", "--projection", "_id"], 120),
    ("日历", ["exec-out", "content", "query",
             "--uri", "content://com.android.calendar/events", "--projection", "_id"], 120),
    ("媒体图片", ["exec-out", "content", "query",
                 "--uri", "content://media/external/images/media", "--projection", "_id"], 180),
    ("媒体视频", ["exec-out", "content", "query",
                 "--uri", "content://media/external/video/media", "--projection", "_id"], 180),
    ("应用数(三方)", ["shell", "pm", "list", "packages", "-3"], 60),
    ("/sdcard体积", ["shell", "cd /sdcard && du -sm * 2>/dev/null | sort -rn | head -30"], 180),
]


def nrec(txt):
    """content query 的记录数（按 Row: 前缀，技能坑 4）。"""
    return len(re.findall(r"(?:^|\n)Row: \d+ ", txt))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lines = []
    data = {}
    lines.append("手机能力判定 · %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("adb: %s" % ADB)
    lines.append("=" * 72)

    for label, args, to in PROBES:
        t0 = time.time()
        try:
            txt = run(args, timeout=to)
            err = ""
        except Exception as ex:
            txt, err = "", "%s: %s" % (type(ex).__name__, ex)
        dt = time.time() - t0

        head = txt.strip()
        if len(head) > 3000:
            head = head[:3000] + "\n... (共 %d 字符)" % len(txt)

        data[label] = {"cmd": " ".join(args), "sec": round(dt, 1),
                       "chars": len(txt), "records": nrec(txt),
                       "err": err, "head": head[:1500]}

        lines.append("")
        lines.append("### %s   (%.1fs, %d 字符%s)"
                     % (label, dt, len(txt),
                        ", %d 条" % nrec(txt) if nrec(txt) else ""))
        lines.append("$ adb " + " ".join(args))
        if err:
            lines.append("!! " + err)
        lines.append(head if head else "(空)")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(JSONF, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # 控制台只给摘要
    print("== 摘要 ==")
    for label, _a, _t in PROBES:
        d = data[label]
        print("  %-12s %6.1fs  %6d字符  %s%s"
              % (label, d["sec"], d["chars"],
                 ("%d条 " % d["records"]) if d["records"] else "",
                 ("ERR " + d["err"][:60]) if d["err"] else ""))
    print("\n报告 -> %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
