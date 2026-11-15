# -*- coding: utf-8 -*-
"""
idle_hours_align.py —— C3（同住挤压 → 外部补偿）的验证材料（只读）

背景：
  august_daily_align.py 已证伪 C1 / C2，且 C3 在「日级消息量」上也是负的（母亲消息 × 笑一 = -0.20）。
  但「日总量」测不出 C3 —— 同住挤压的效果不在「多聊几句」，而在「什么时候聊」。
  → 本脚本换分辨率：**时段（hour-of-day）**。

三块材料：
  A. 时段分布：笑一 / 母亲 / 导师 / 全库，按小时 × 按月（2026-06 → 10）
  B. 独处指数：笑一「深夜占比」（23:00–05:59）按月；母亲高消息日 vs 低消息日 的深夜占比
  C. 外部补偿源：朋友圈互动（SnsMessage_tmp3, is_relative_me=1）+ 搜索历史（SearchRecent）逐日

只读：index.sqlite（mode=ro）+ sns.db / general.db（mode=ro）
产出：_tmp/idle_hours.csv · _tmp/idle_hours_summary.csv · _tmp/idle_events.csv
"""
import os
import sqlite3
import datetime
from collections import defaultdict, Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
DEC = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted"

MOM = "wxid_1wa75s1kze3o22"
XY = "wxid_wdnk6ue9kiyn22"
DAO = "deerluna"

START = "2026-06-01"
END = "2026-10-06"
NIGHT = set(range(23, 24)) | set(range(0, 6))   # 23:00 – 05:59


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def d2ts(s):
    return int(datetime.datetime.strptime(s, "%Y-%m-%d").timestamp())


def ts2d(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def hour(ts):
    return datetime.datetime.fromtimestamp(ts).hour


def main():
    c = ro(INDEX_DB)
    t0, t1 = d2ts(START), d2ts(END)

    # ---------- A. 时段分布 ----------
    # 逐会话取 (ts)，本窗口内
    rows = c.execute(
        "SELECT session_key, ts FROM messages WHERE ts>=? AND ts<?", (t0, t1)
    ).fetchall()

    who = lambda sk: "笑一" if sk == XY else ("母亲" if sk == MOM else ("导师" if sk == DAO else "全库"))
    # hour_dist[标签][月][小时] = 条数
    hd = defaultdict(lambda: defaultdict(Counter))
    # daily_xy_night[日期] = 笑一深夜条数；daily_xy_all[日期] = 笑一总条数
    xy_night, xy_all = Counter(), Counter()

    for sk, ts in rows:
        lab = who(sk)
        mo = ts2d(ts)[:7]
        h = hour(ts)
        hd[lab][mo][h] += 1
        hd["全库"][mo][h] += 1
        if sk == XY:
            d = ts2d(ts)
            xy_all[d] += 1
            if h in NIGHT:
                xy_night[d] += 1

    # 写时段明细
    out = os.path.join(TMP, "idle_hours.csv")
    with open(out, "w", encoding="utf-8-sig") as f:
        f.write("对象,月份,小时,条数\n")
        for lab in ("笑一", "母亲", "导师", "全库"):
            for mo in sorted(hd[lab]):
                for h in range(24):
                    f.write("%s,%s,%d,%d\n" % (lab, mo, h, hd[lab][mo][h]))

    # 汇总：深夜占比
    sumrows = []
    for lab in ("笑一", "母亲", "导师", "全库"):
        for mo in sorted(hd[lab]):
            cnt = hd[lab][mo]
            tot = sum(cnt.values())
            night = sum(v for h, v in cnt.items() if h in NIGHT)
            if tot == 0:
                continue
            # 峰值小时
            ph = max(range(24), key=lambda h: cnt[h])
            sumrows.append((lab, mo, tot, night, night / tot * 100, ph, cnt[ph] / tot * 100))

    with open(os.path.join(TMP, "idle_hours_summary.csv"), "w", encoding="utf-8-sig") as f:
        f.write("对象,月份,总条数,深夜条数,深夜占比%,峰值小时,峰值占比%\n")
        for r in sumrows:
            f.write("%s,%s,%d,%d,%.1f,%02d,%.1f\n" % r)

    # ---------- B. 独处指数：母亲高/低消息日 的 笑一深夜占比 ----------
    mom_daily = Counter()
    for sk, ts in rows:
        if sk == MOM:
            mom_daily[ts2d(ts)] += 1

    days = sorted(set(list(mom_daily) + list(xy_all)))
    med = sorted(mom_daily.values())
    med = med[len(med) // 2] if med else 0

    hi, lo = [], []
    for d in days:
        if d not in xy_all:
            continue
        rate = (xy_night[d] / xy_all[d] * 100) if xy_all[d] else 0.0
        (hi if mom_daily[d] >= med else lo).append((d, mom_daily[d], xy_all[d], xy_night[d], rate))

    def avg(xs, i):
        return sum(x[i] for x in xs) / len(xs) if xs else 0.0

    print("=== B. 独处指数（母亲消息中位数 = %d）===" % med)
    print("  高母亲消息日 n=%d ｜ 笑一日均 %.1f 条 ｜ 深夜占比均值 %.1f%%"
          % (len(hi), avg(hi, 2), avg(hi, 4)))
    print("  低母亲消息日 n=%d ｜ 笑一日均 %.1f 条 ｜ 深夜占比均值 %.1f%%"
          % (len(lo), avg(lo, 2), avg(lo, 4)))

    # ---------- C. 外部补偿源 ----------
    ev = []   # (日期, 类型, 说明)
    try:
        s = ro(os.path.join(DEC, "sns", "sns.db"))
        for ts, typ, fn, ct in s.execute(
            "SELECT create_time,type,from_nickname,content FROM SnsMessage_tmp3 "
            "WHERE is_relative_me=1 ORDER BY create_time"
        ):
            kind = "评论" if typ == 1 else "点赞"
            ev.append((ts2d(ts), "朋友圈互动", "%s %s" % (kind, (fn or "")[:14])))
    except Exception as e:
        print("  [warn] sns:", e)

    try:
        g = ro(os.path.join(DEC, "general", "general.db"))
        for q, t in g.execute("SELECT query,last_click_time FROM SearchRecent ORDER BY last_click_time"):
            ev.append((ts2d(t), "搜索", q))
    except Exception as e:
        print("  [warn] general:", e)

    ev.sort()
    with open(os.path.join(TMP, "idle_events.csv"), "w", encoding="utf-8-sig") as f:
        f.write("日期,类型,说明\n")
        for d, k, v in ev:
            f.write("%s,%s,%s\n" % (d, k, v.replace(",", " ")))

    print()
    print("=== C. 外部补偿源（窗口内 %s → %s）===" % (START, END))
    win = [e for e in ev if START <= e[0] < END]
    print("  朋友圈互动 %d 条 ｜ 搜索 %d 条"
          % (sum(1 for e in win if e[1] == "朋友圈互动"), sum(1 for e in win if e[1] == "搜索")))
    for d, k, v in win:
        print("   ", d, k, v[:40])

    print()
    print("产出：_tmp\\idle_hours.csv · _tmp\\idle_hours_summary.csv · _tmp\\idle_events.csv")


if __name__ == "__main__":
    main()
