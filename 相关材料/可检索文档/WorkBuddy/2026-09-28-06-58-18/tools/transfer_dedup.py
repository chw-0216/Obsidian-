# -*- coding: utf-8 -*-
r"""
transfer_dedup.py —— 转账「重复记账」核账（只读）

背景（2026-10-06 发现）：
  引擎里的「母亲两年转来 389 笔 / ¥347,550」是**双倍**的。
  微信转账在导出库里**每笔记两行**：一行 role=them、一行 role=me，
  内容完全相同（`微信转账 | 收到转账20000.00元…`），时间差通常几秒到几分钟。

  实证（2026-08-28 学费）：
    08-28 11:27:50 | them | 微信转账 | 收到转账20000.00元
    08-28 11:27:59 | me   | 微信转账 | 收到转账20000.00元      ← 9 秒后，同一笔

做法：
  1. 取某会话里所有 `收到转账` 行
  2. 按「同金额 + 时间差 ≤ WINDOW」贪心配对去重
  3. 同时给一个**只取 them 行**的对照口径（母亲转来 = them 行）
  4. 逐月列出：原始行数 / 去重笔数 / 金额

输出：_tmp/transfer_dedup.csv（逐月）+ 控制台摘要
只读 index.sqlite。
"""
import os, io, re, csv, sqlite3, datetime, sys
from collections import defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

MOM = "wxid_1wa75s1kze3o22"          # 母亲 刘丽萍
WINDOW = 24 * 3600                    # 配对窗口：24 小时（2h→209 / 12h→201 / 24h→197 / 72h→197，已收敛）

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PAT = re.compile(r"收到转账[￥¥]?([0-9]+(?:\.[0-9]+)?)元")


def month(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m")


def dedup(rows):
    """rows = [(ts, role, amount)]，按 同金额 + ≤WINDOW 贪心配对去重"""
    used = set()
    uniq = []
    for a in range(len(rows)):
        if a in used:
            continue
        used.add(a)
        uniq.append(rows[a])
        for b in range(a + 1, len(rows)):
            if b in used or rows[b][2] != rows[a][2]:
                continue
            if abs(rows[b][0] - rows[a][0]) <= WINDOW:
                used.add(b)
                break
    return uniq


def main():
    con = sqlite3.connect("file:" + INDEX.replace("\\", "/") + "?mode=ro", uri=True)
    raw = [(r[0], r[1], float(PAT.search(r[2]).group(1)))
           for r in con.execute(
               "select ts,role,content from messages where session_key=? and content like ? order by ts",
               (MOM, "%收到转账%"))]
    con.close()

    n_them = sum(1 for r in raw if r[1] == "them")
    n_me = sum(1 for r in raw if r[1] == "me")
    uniq = dedup(raw)

    print("=" * 68)
    print("母亲（刘丽萍）会话 · 转账核账")
    print("=" * 68)
    print("原始行数 %d（them %d ｜ me %d ｜ 其他 %d）"
          % (len(raw), n_them, n_me, len(raw) - n_them - n_me))
    print("① 不去重（旧口径）：%d 笔 / ¥%s" % (len(raw), "{:,.0f}".format(sum(r[2] for r in raw))))
    print("② 只取 them 行    ：%d 笔 / ¥%s"
          % (n_them, "{:,.0f}".format(sum(r[2] for r in raw if r[1] == "them"))))
    print("③ 配对去重（≤24h） ：%d 笔 / ¥%s"
          % (len(uniq), "{:,.0f}".format(sum(r[2] for r in uniq))))
    print("→ 真值取 ③；② 与 ③ 应互相印证（差 ≤2 笔才算稳）")
    print("→ ① 约为真值的 %.2f 倍（≈2 倍 = 每笔记了两行）" % (len(raw) / max(len(uniq), 1)))

    # 逐月
    m_raw = defaultdict(lambda: [0, 0.0])
    m_th = defaultdict(lambda: [0, 0.0])
    m_un = defaultdict(lambda: [0, 0.0])
    for ts, role, amt in raw:
        m_raw[month(ts)][0] += 1
        m_raw[month(ts)][1] += amt
        if role == "them":
            m_th[month(ts)][0] += 1
            m_th[month(ts)][1] += amt
    for ts, role, amt in uniq:
        m_un[month(ts)][0] += 1
        m_un[month(ts)][1] += amt

    out = os.path.join(TMP, "transfer_dedup.csv")
    with io.open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["月份", "原始行数", "原始金额", "them笔数", "them金额", "去重笔数", "去重金额"])
        for k in sorted(m_raw):
            w.writerow([k, m_raw[k][0], "%.2f" % m_raw[k][1],
                        m_th[k][0], "%.2f" % m_th[k][1],
                        m_un[k][0], "%.2f" % m_un[k][1]])

    print("\n逐月（原始 / 去重）：")
    for k in sorted(m_raw):
        print("  %s  %3d 行 ¥%9.0f  →  %3d 笔 ¥%9.0f"
              % (k, m_raw[k][0], m_raw[k][1], m_un[k][0], m_un[k][1]))

    y = "2026"
    tot = [0, 0.0]
    for k in m_un:
        if k.startswith(y) and k <= y + "-10":
            tot[0] += m_un[k][0]
            tot[1] += m_un[k][1]
    print("\n%s 年 1–10 月（去重）：%d 笔 / ¥%s" % (y, tot[0], "{:,.0f}".format(tot[1])))
    print("→ %s" % out)


if __name__ == "__main__":
    main()
