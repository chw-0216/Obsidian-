# -*- coding: utf-8 -*-
r"""
recheck_stale.py —— 失效触发：找出「需要重审」的结论 / 假设 / 决策 / 数据源

对应方案书 §3「双时态」与 §7「阶段二·更新对」：
  一处信息变化后，相关结论能进入重审队列。

触发规则：
  R1 结论 status ∈ {待核实} 且 超过 N 天未动
  R2 结论 valid_to 已过期（或 valid_to < 今天）
  R3 结论 无反证（counter_examples 空）→ 不合格结论，需补反证
  R4 结论 未经本人确认（self_confirmed=0）却被当作事实引用
  R5 假设 status=open 且超过 N 天未动
  R6 决策 status=open（未决）
  R7 数据源 last_ok 超过 N 天（数据陈旧警告）
  R8 事件层最后一条日期 vs 索引库最新日期 → 覆盖缺口

产物：重审队列_YYYY-MM-DD.md（工作区）
"""
import os, io, sqlite3, datetime, argparse

WS  = r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18"
DB  = WS + "/analysis.sqlite"
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
TODAY = datetime.date.today()
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def d(s):
    if not s: return None
    s = str(s)[:10]
    for f in ("%Y-%m-%d", "%Y/%m/%d", "%y-%m-%d"):
        try: return datetime.datetime.strptime(s, f).date()
        except Exception: pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=30, help="多少天未动算陈旧")
    ap.add_argument("--src-days",   type=int, default=7,  help="数据源多少天未读算陈旧")
    a = ap.parse_args()

    con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    L = []
    def P(s=""):
        L.append(s); print(s)

    P("# 重审队列 · %s" % TODAY)
    P()
    P("> 生成时间 %s ｜ 规则 R1–R8 ｜ 陈旧阈值 %d 天 ｜ 数据源阈值 %d 天" % (NOW, a.stale_days, a.src_days))
    P()

    n_total = 0

    # ---- R2/R1/R3/R4 结论
    P("## 一、结论（conclusions）")
    P()
    rows = con.execute("select * from conclusions").fetchall()
    stale, expired, no_counter, unconfirmed = [], [], [], []
    for r in rows:
        upd = d(r["updated_at"]) or d(r["created_at"])
        if r["valid_to"] and (d(r["valid_to"]) or TODAY) < TODAY:
            expired.append(r)
        elif (r["status"] or "") == "待核实" and upd and (TODAY - upd).days > a.stale_days:
            stale.append(r)
        if not (r["counter_examples"] or "").strip():
            no_counter.append(r)
        if not r["self_confirmed"] and (r["status"] or "") not in ("已撤回",):
            unconfirmed.append(r)
    P("- 结论总数 **%d**" % len(rows))
    P("- R2 已过期（valid_to < 今天）：**%d**" % len(expired))
    for r in expired[:10]:
        P("  - `%s` %s ｜ valid_to=%s" % (r["concl_id"], (r["statement"] or "")[:56], r["valid_to"]))
    P("- R1 待核实且 >%d 天未动：**%d**" % (a.stale_days, len(stale)))
    for r in stale[:10]:
        P("  - `%s` %s" % (r["concl_id"], (r["statement"] or "")[:56]))
    P("- R3 无反证（counter_examples 为空）：**%d / %d** ← 不合格结论" % (len(no_counter), len(rows)))
    P("- R4 未经本人确认（self_confirmed=0）：**%d / %d**" % (len(unconfirmed), len(rows)))
    P()
    n_total += len(expired) + len(stale)

    # ---- R5 假设
    P("## 二、假设（hypotheses）")
    P()
    hs = con.execute("select * from hypotheses").fetchall()
    hopen = [r for r in hs if (r["status"] or "open") == "open"]
    P("- 假设总数 **%d** ｜ open **%d**" % (len(hs), len(hopen)))
    for r in hs:
        flag = "🟡open" if (r["status"] or "open") == "open" else ("✅" + r["status"])
        P("  - %s `%s` %s" % (flag, r["hyp_id"], (r["statement"] or "")[:60]))
        P("      反证：%s" % ((r["counters"] or "（空）")[:70]))
        P("      判别观测：%s" % ((r["discriminating_obs"] or "（空）")[:70]))
    P()
    n_total += len(hopen)

    # ---- R6 决策
    P("## 三、决策（decisions）")
    P()
    ds = con.execute("select * from decisions").fetchall()
    dopen = [r for r in ds if (r["status"] or "open") == "open"]
    P("- 决策总数 **%d** ｜ 未决 **%d**" % (len(ds), len(dopen)))
    for r in dopen:
        P("  - ⬜ `%s` %s" % (r["dec_id"], (r["question"] or "")[:70]))
        P("      目标=%s ｜ 选项=%s ｜ 预期=%s" % (r["goal"], (r["options"] or "")[:50], (r["expected"] or "")[:40]))
    P()
    n_total += len(dopen)

    # ---- R7 数据源陈旧
    P("## 四、数据源新鲜度（sources）")
    P()
    srcs = con.execute("select * from sources order by last_ok").fetchall()
    olds = []
    for r in srcs:
        lo = d(r["last_ok"])
        age = (TODAY - lo).days if lo else 9999
        if age > a.src_days:
            olds.append((age, r))
    P("- 数据源总数 **%d** ｜ 超过 %d 天未读 **%d**" % (len(srcs), a.src_days, len(olds)))
    for age, r in sorted(olds, key=lambda x: -x[0])[:12]:
        P("  - ⚠️ %-34s %-8s %s 天前" % (r["source_id"][:34], r["kind"], age))
    P()
    n_total += len(olds)

    # ---- R8 覆盖缺口（事件层 vs 索引库）
    P("## 五、覆盖缺口（事件层 ↔ 索引库）")
    P()
    try:
        ev_max = con.execute("select max(date) from events").fetchone()[0]
        ev_n   = con.execute("select count(*) from events").fetchone()[0]
        P("- 事件层：%d 条 ｜ 最新日期 **%s**" % (ev_n, ev_max))
        if os.path.exists(IDX):
            c2 = sqlite3.connect("file:" + IDX + "?mode=ro", uri=True)
            mx = c2.execute("select max(ts) from messages").fetchone()[0]
            nm = c2.execute("select count(*) from messages").fetchone()[0]
            idx_max = datetime.datetime.fromtimestamp(mx).strftime("%Y-%m-%d %H:%M") if mx else "-"
            P("- 索引库：%d 条 ｜ 最新消息 **%s**" % (nm, idx_max))
            gap = (TODAY - d(idx_max)).days if d(idx_max) else None
            if gap is not None and gap > 0:
                P("- 🔴 **缺口：索引库最新消息比今天早 %d 天** → 需先刷新实时数据" % gap)
        else:
            P("- ⚠️ 索引库不存在：%s" % IDX)
    except Exception as e:
        P("- 检查失败：%s" % e)
    P()

    # ---- 汇总
    P("## 六、汇总")
    P()
    P("| 类别 | 待处理 |")
    P("|---|---|")
    P("| 结论（过期/陈旧） | %d |" % (len(expired) + len(stale)))
    P("| 结论（无反证·不合格） | %d |" % len(no_counter))
    P("| 假设（open） | %d |" % len(hopen))
    P("| 决策（未决） | %d |" % len(dopen))
    P("| 数据源（陈旧） | %d |" % len(olds))
    P()
    P("**下一步**：优先处理「无反证结论」与「未决决策」——这两类直接拉低分析质量。")

    out = os.path.join(WS, "重审队列_%s.md" % TODAY)
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print()
    print("=" * 70)
    print("已写出：%s" % out)

if __name__ == "__main__":
    main()
