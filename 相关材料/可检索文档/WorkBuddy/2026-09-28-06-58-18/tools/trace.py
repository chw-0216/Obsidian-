# -*- coding: utf-8 -*-
"""
trace.py —— 从任何一条结论 / 事件，回查全部依据（只读）

用户验收标准：「从任何一条结论回查依据，修正一次就让所有当前视图同步更新。」

用法：
  python tools\\trace.py EVT-20260504-001        # 查事件：证据 → 原文 → 修订史
  python tools\\trace.py CON-003                 # 查结论：状态 → 关联事件
  python tools\\trace.py --search 井邻           # 按关键词找事件（两字词也支持）
  python tools\\trace.py --list-concl 已撤回     # 按状态列结论
"""
import os, re, sys, sqlite3, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def show_event(eid):
    a = ro(ANALYSIS_DB)
    r = a.execute("select * from events where event_id=?", (eid,)).fetchone()
    if not r:
        print("未找到事件 %s" % eid); return
    cols = [c[1] for c in a.execute("pragma table_info(events)")]
    d = dict(zip(cols, r))
    print("=" * 70)
    print("事件 %s" % eid)
    print("=" * 70)
    print("  日期      %s（%s）" % (d["date"], d["date_certainty"]))
    print("  事件      %s" % d["event"])
    print("  对话人    %s ｜ 距离 %s ｜ 关系 %s" % (d["person"], d["distance"], d["relation"]))
    print("  性质      %s ｜ 层级 %s ｜ 来源 %s ｜ 复核 %s" % (d["nature"], d["level"], d["source"], d["review_status"]))
    print("  规则评分  %s（负荷分 %s）   ← 机器规则，非本人感受" % (d["load_rule"], d["load_score"]))
    print("  本人感受  %s" % (d["load_self"] or "（未确认）"))
    print("  抽取版本  %s ｜ 自然键 %s" % (d["extract_version"], (d["natkey"] or "")[:12]))

    ev = a.execute("select msg_id,legacy_ref,quote,session_key,ts,link_status,confidence,note "
                   "from evidence where event_id=? order by confidence desc", (eid,)).fetchall()
    print("\n  证据 %d 条：" % len(ev))
    ic = ro(INDEX_DB)
    for msg_id, legacy, quote, sk, ts, st, conf, note in ev:
        print("    [%-12s] %s" % (st, (quote or legacy or "")[:60]))
        if msg_id:
            m = ic.execute("select time_text,role,content from messages where id=?", (msg_id,)).fetchone()
            if m:
                print("        → #%d %s [%s] %s" % (msg_id, m[0] or "", m[1], (m[2] or "")[:90].replace("\n", " ")))
    ic.close()

    rev = a.execute("select field,old_value,new_value,changed_at,reason from revisions "
                    "where entity_id=? order by rev_id", (eid,)).fetchall()
    if rev:
        print("\n  修订史 %d 条：" % len(rev))
        for f, o, n, t, why in rev:
            print("    %s：%s → %s（%s · %s）" % (f, o, n, t, why))
    a.close()


def show_concl(cid):
    a = ro(ANALYSIS_DB)
    r = a.execute("select * from conclusions where concl_id=?", (cid,)).fetchone()
    if not r:
        print("未找到结论 %s" % cid); return
    cols = [c[1] for c in a.execute("pragma table_info(conclusions)")]
    d = dict(zip(cols, r))
    print("=" * 70)
    print("结论 %s" % cid)
    print("=" * 70)
    print("  陈述      %s" % d["statement"])
    print("  状态      %s%s" % (d["status"], "   ← 已退出当前画像" if d["status"] == "已撤回" else ""))
    print("  本人确认  %s" % ("是" if d["self_confirmed"] else "否"))
    print("  文档引用  %s" % (d.get("evidence_refs") or "—"))
    print("  反例      %s" % (d.get("counter_examples") or "—"))
    print("  成立时间  %s" % (d.get("valid_from") or "**未标**"))
    print("  出处      %s" % d["source_doc"])
    if d.get("link_method"):
        print("  依据      %s%s" % (d["link_method"],
              ("　匹配分 %.3f" % (d.get("link_score") or 0)) if d.get("evidence_events") else ""))

    # ★ 支持事件（link_conclusions 自动匹配的）
    ids = re.findall(r"EVT-\d{8}-\d{3}|EVT-UNDATED-\d{3}", d.get("evidence_events") or "")
    if ids:
        q = ",".join("?" * len(ids))
        rows = a.execute("select event_id,date,person,substr(event,1,44) from events "
                         "where event_id in (%s) order by date" % q, ids).fetchall()
        print("\n  ★ 支持事件 %d 条（自动匹配）：" % len(rows))
        for eid, dt, p, ev in rows:
            late = "  ⚠️晚于成立时间" if (d.get("valid_from") and dt and dt > d["valid_from"]) else ""
            print("    %s  %s  %-10s %s%s" % (eid, dt, (p or "")[:10], ev, late))
    elif d.get("link_method"):
        print("\n  ★ 无事件证据 —— 依据是「%s」，不由聊天事件支撑。" % d["link_method"])

    # 关键词兜底（自动匹配没命中时）
    if not ids:
        kw = re.sub(r"[^\w\u4e00-\u9fff]", "", d["statement"])[:4]
        if kw:
            hits = a.execute("select event_id,date,substr(event,1,46) from events where event like ? limit 6",
                             ("%" + kw + "%",)).fetchall()
            if hits:
                print("\n  可能相关事件（关键词「%s」，仅供参考）：" % kw)
                for eid, dt, ev in hits:
                    print("    %s  %s  %s" % (eid, dt, ev))
    a.close()


def search(kw):
    a = ro(ANALYSIS_DB)
    like = "%" + kw + "%"
    rows = a.execute("select event_id,date,person,substr(event,1,60) from events "
                     "where event like ? or person like ? or people like ? or relation like ? "
                     "order by date desc limit 25", (like, like, like, like)).fetchall()
    print("关键词「%s」命中 %d 条（显示前 25）" % (kw, len(rows)))
    for eid, dt, p, ev in rows:
        print("  %s  %-10s %-12s %s" % (eid, dt, (p or "")[:12], ev))
    a.close()


def list_concl(status=None):
    a = ro(ANALYSIS_DB)
    if status:
        rows = a.execute("select concl_id,status,substr(statement,1,70) from conclusions where status=? order by concl_id",
                         (status,)).fetchall()
    else:
        rows = a.execute("select concl_id,status,substr(statement,1,70) from conclusions order by concl_id").fetchall()
    print("结论 %d 条%s：" % (len(rows), ("（状态=%s）" % status) if status else ""))
    for cid, st, s in rows:
        print("  %-8s %-6s %s" % (cid, st, s))
    a.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "--search":
        search(args[1])
    elif args[0] == "--list-concl":
        list_concl(args[1] if len(args) > 1 else None)
    elif args[0].startswith("CON-"):
        show_concl(args[0])
    else:
        show_event(args[0])
