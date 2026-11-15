# -*- coding: utf-8 -*-
"""
august_daily_align.py —— 2026 年 8 月逐日对齐（解决 C1「钱→关系」 vs C2「关系→钱」）

把四类数据拉到「天」这根轴上：
  ① 母亲 → 他 的转账（笔数 / 金额）
  ② 他 → 外部 的转账（含给笑一）
  ③ 他的支出（微信支付 / 美团 / 支付宝，来自 _tmp/payment_flow.csv）
  ④ 各会话消息量：笑一 / 母亲 / 导师 / 井邻相关

然后做**滞后相关**（lag −5 … +5 天），看谁先动。

输出：
  _tmp/august_daily.csv     —— 逐日对齐表
  _tmp/august_lag.csv       —— 滞后相关系数矩阵
只读 index.sqlite + payment_flow.csv。用法：python tools\\august_daily_align.py
"""
import os, io, re, csv, sqlite3, sys, datetime
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
PAY = os.path.join(TMP, "payment_flow.csv")

MOM = "wxid_1wa75s1kze3o22"
XY = "wxid_wdnk6ue9kiyn22"          # 笑一
DAO = "deerluna"                     # 导师（备注名）
YEAR, MON = 2026, 8

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def pearson(a, b):
    n = len(a)
    if n < 3:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va == 0 or vb == 0:
        return 0.0
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    return cov / (va ** 0.5 * vb ** 0.5)


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    return pearson(rank(a), rank(b))


def main():
    t0 = int(datetime.datetime(YEAR, MON, 1).timestamp())
    t1 = int(datetime.datetime(YEAR, MON + 1, 1).timestamp())
    days = []
    d = datetime.date(YEAR, MON, 1)
    while d.month == MON:
        days.append(d.strftime("%Y-%m-%d"))
        d += datetime.timedelta(days=1)
    idx = {dd: i for i, dd in enumerate(days)}

    mom_amt = [0.0] * len(days)      # 母亲→他 金额
    mom_cnt = [0] * len(days)
    out_amt = [0.0] * len(days)      # 他→别人 金额（微信转账通知）
    xy_n = [0] * len(days)
    mom_n = [0] * len(days)
    dao_n = [0] * len(days)
    all_n = [0] * len(days)

    con = ro(INDEX)
    # ---- 逐条消息 ----
    seen_tr = set()
    for sk, ts, role, content in con.execute(
            "select session_key,ts,role,content from messages where ts>=? and ts<?", (t0, t1)):
        day = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        i = idx.get(day)
        if i is None:
            continue
        all_n[i] += 1
        if sk == XY:
            xy_n[i] += 1
        elif sk == MOM:
            mom_n[i] += 1
        elif sk == DAO:
            dao_n[i] += 1
        # 转账通知
        m = re.search(r"收到转账([\d.]+)元", content or "")
        if m:
            v = float(m.group(1))
            k = (sk, int(v * 100), ts // 120)
            if k not in seen_tr:
                seen_tr.add(k)
                if sk == MOM:
                    mom_amt[i] += v
                    mom_cnt[i] += 1
                else:
                    out_amt[i] += v
    con.close()

    # ---- 支出（支付流）----
    spend = [0.0] * len(days)
    if os.path.exists(PAY):
        for r in csv.DictReader(io.open(PAY, encoding="utf-8-sig")):
            dd = (r.get("时间") or "")[:10]
            i = idx.get(dd)
            if i is None:
                continue
            if r.get("方向") == "支出":
                try:
                    spend[i] += float(r.get("金额") or 0)
                except ValueError:
                    pass

    # ---- 写表 ----
    rows = []
    for i, dd in enumerate(days):
        rows.append({
            "日期": dd, "星期": "一二三四五六日"[datetime.date(YEAR, MON, int(dd[-2:])).weekday()],
            "母亲转账_金额": round(mom_amt[i], 2), "母亲转账_笔数": mom_cnt[i],
            "他转出_金额": round(out_amt[i], 2),
            "支出_总额": round(spend[i], 2),
            "笑一消息": xy_n[i], "母亲消息": mom_n[i], "导师消息": dao_n[i],
            "全库消息": all_n[i],
        })
    with io.open(os.path.join(TMP, "august_daily.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- 滞后相关 ----
    series = {
        "母亲转账金额": mom_amt,
        "他转出金额": out_amt,
        "支出总额": spend,
        "笑一消息": [float(x) for x in xy_n],
        "母亲消息": [float(x) for x in mom_n],
        "导师消息": [float(x) for x in dao_n],
        "全库消息": [float(x) for x in all_n],
    }
    lags = list(range(-5, 6))
    pairs = [
        ("母亲转账金额", "笑一消息"),   # C1 方向：钱先 → 关系后
        ("笑一消息", "母亲转账金额"),   # C2 方向：关系先 → 钱后
        ("他转出金额", "笑一消息"),     # 直接投入
        ("笑一消息", "他转出金额"),
        ("支出总额", "笑一消息"),
        ("母亲转账金额", "支出总额"),   # 过路钱？
        ("母亲消息", "笑一消息"),       # C3：家里压力 → 外部补偿？
        ("导师消息", "笑一消息"),       # 工作压力 → 外部补偿？
        ("全库消息", "笑一消息"),       # 整体活跃度（共同驱动？）
    ]
    lag_rows = []
    for a, b in pairs:
        row = {"A": a, "B": b}
        for L in lags:
            xa, xb = [], []
            for i in range(len(days)):
                j = i + L
                if 0 <= j < len(days):
                    xa.append(series[a][i])
                    xb.append(series[b][j])
            row["L%+d" % L] = round(pearson(xa, xb), 3)
        row["同秩(L0)"] = round(spearman(series[a], series[b]), 3)
        lag_rows.append(row)
    with io.open(os.path.join(TMP, "august_lag.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lag_rows[0].keys()))
        w.writeheader()
        w.writerows(lag_rows)

    # 稳健性：剔除「学费日」（单日支出 > 1 万）后重算
    keep = [i for i in range(len(days)) if spend[i] < 10000]
    robust = []
    for a, b in pairs:
        robust.append((a, b, round(spearman([series[a][i] for i in keep],
                                            [series[b][i] for i in keep]), 3)))

    # ---- 控制台 ----
    print("2026 年 8 月逐日对齐（节选有资金动作的日子）")
    print("%-11s %-3s %10s %4s %9s %9s %6s %6s %6s" %
          ("日期", "周", "母亲转账", "笔", "他转出", "支出", "笑一", "母亲", "导师"))
    for r in rows:
        mark = " ★" if (r["母亲转账_金额"] > 0 or r["他转出_金额"] > 0) else ""
        print("%-11s %-3s %10.0f %4d %9.0f %9.0f %6d %6d %6d%s" % (
            r["日期"], r["星期"], r["母亲转账_金额"], r["母亲转账_笔数"],
            r["他转出_金额"], r["支出_总额"], r["笑一消息"], r["母亲消息"], r["导师消息"], mark))

    print("\n合计：母亲转账 ¥%.0f / %d 笔 ｜ 他转出 ¥%.0f ｜ 支出 ¥%.0f ｜ 笑一 %d 条" % (
        sum(mom_amt), sum(mom_cnt), sum(out_amt), sum(spend), sum(xy_n)))

    print("\n★ 滞后相关（A(t) vs B(t+L)；L>0 = B 在后，即 A 先动）")
    print("%-16s %-10s %s  %s" % ("A", "B", "  ".join("L%+d" % L for L in lags), "秩相关"))
    for r in lag_rows:
        print("%-16s %-10s %s  %5.2f" % (r["A"], r["B"],
                                         "  ".join("%5.2f" % r["L%+d" % L] for L in lags),
                                         r["同秩(L0)"]))
    print("\n★ 稳健性：剔除「学费日」（单日支出 > ¥1 万）后的秩相关")
    for a, b, v in robust:
        print("   %-14s × %-12s  %5.2f" % (a, b, v))
    print("\n→ _tmp\\august_daily.csv / august_lag.csv")


if __name__ == "__main__":
    main()
