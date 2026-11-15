# -*- coding: utf-8 -*-
"""
blind_test.py —— 时间盲测：只给截至某日的资料，检验有没有「偷看未来」

四道自动检查（全量 · 只读）：
  ① 结论 ← 证据：结论的「成立时间」不得早于它引用的证据日期（否则是事后诸葛亮）
  ② 事件 ← 消息：事件的日期与它引用的消息时间必须落在同一窗口（±3 天）
  ③ 产物 ← 库：报告的数据截至时间不得早于库内最新事件（否则报告比数据旧）
  ④ 时间可定位率：无日期 / 只有区间的占比（越高说明越多东西「漂浮在时间外」）

抽样人工盲测：
  python tools\\blind_test.py --case CON-xxx     # 导出「只看截止日之前」的资料包

用法：
  python tools\\blind_test.py
  python tools\\blind_test.py --json out.json
"""
import os, io, re, sys, json, sqlite3, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
TMP = os.path.join(WS, "_tmp")

WINDOW_DAYS = 3          # 事件 ↔ 消息允许的最大偏移

results = []


def check(name, ok, detail="", warn=False):
    results.append({"name": name, "ok": bool(ok), "warn": bool(warn and not ok), "detail": str(detail)})
    tag = "PASS" if ok else ("WARN" if warn else "FAIL")
    print("  [%s] %s" % (tag, name))
    if detail:
        for ln in str(detail).splitlines():
            print("        " + ln)
    return ok


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def h1(t):
    print("\n" + "=" * 70); print(t); print("=" * 70)


# ① 结论 ← 证据
def t1(con):
    h1("① 结论 ← 证据：有没有「事后诸葛亮」")
    rows = con.execute("""select concl_id, valid_from, evidence_events, link_method
                            from conclusions
                           where evidence_events is not null and trim(evidence_events)<>''""").fetchall()
    if not rows:
        check("可检验的结论（绑定了证据事件 + 成立时间）", False,
              "0 条 —— 结论层没有绑定「支持证据的事件 ID」\n"
              "→ 跑 python tools\\link_conclusions.py --apply", warn=True)
        return {"checked": 0}

    leak, nodate, badid = [], 0, 0
    for cid, vfrom, refs, _m in rows:
        evs = re.findall(r"EVT-\d{8}-\d{3}|EVT-UNDATED-\d{3}", refs or "")
        if not evs:
            continue
        q = ",".join("?" * len(evs))
        got = con.execute("select event_id, date from events where event_id in (%s)" % q, evs).fetchall()
        badid += len(evs) - len(got)                    # 引用了不存在的事件 ID
        if not vfrom:
            nodate += 1
            continue
        mx = max([g[1] for g in got if g[1]] or [""])
        if mx and mx > vfrom:
            leak.append((cid, vfrom, mx))
    check("结论引用的证据事件 ID 都真实存在", badid == 0, "悬空引用 %d 个" % badid)
    check("结论的成立时间 ≥ 其引用证据的日期（不是事后诸葛亮）", not leak,
          "可检验 %d 条 ｜ 时间倒流 %d 条%s" % (len(rows) - nodate, len(leak),
          ("：" + "；".join("%s（成立 %s 却引用 %s）" % x for x in leak[:3])) if leak else ""))

    # 覆盖率：分母 = **不在「已推翻清单」里的**结论（那些本来就不在当前画像里）
    total = con.execute("select count(*) from conclusions").fetchone()[0]
    dead = con.execute("select count(*) from conclusions "
                       "where link_method like '已撤回%'").fetchone()[0]
    active = total - dead
    cov = len(rows) / active * 100 if active else 0
    kinds = dict(con.execute("select link_method, count(*) from conclusions group by 1"))
    print("        依据分布：%s" % " ｜ ".join("%s %d" % (k, v) for k, v in
          sorted(kinds.items(), key=lambda x: -x[1])))
    check("★ 在效结论中「有事件证据」的占比 ≥ 50%", cov >= 50,
          "%d / %d（「已推翻清单」%d 条不计）= %.1f%%\n"
          "       其余为「本人自述 / 方法论」—— **本来就不由事件支撑**，不是匹配失败。"
          % (len(rows), active, dead, cov), warn=True)
    return {"checked": len(rows), "leak": len(leak), "coverage": round(cov, 1)}


# ② 事件 ← 消息
def t2(con):
    h1("② 事件 ← 消息：事件日期与原始消息时间是否同窗口（±%d 天）" % WINDOW_DAYS)
    rows = con.execute("""
        select v.event_id, v.date, date(e.ts,'unixepoch','localtime') as md,
               abs(julianday(date(e.ts,'unixepoch','localtime')) - julianday(v.date)) as dd
          from evidence e join events v on v.event_id = e.event_id
         where e.ts is not null and v.date is not null""").fetchall()
    out = [r for r in rows if r[3] is not None and r[3] > WINDOW_DAYS]
    dist = {}
    for r in rows:
        d = int(r[3]) if r[3] is not None else -1
        dist[d] = dist.get(d, 0) + 1
    for d in sorted(dist)[:6]:
        print("        ±%d 天：%d 条" % (d, dist[d]))
    check("全部证据消息都落在事件日期的 ±%d 天窗口内" % WINDOW_DAYS, not out,
          "共 %d 条证据 ｜ 越窗 %d 条%s" % (len(rows), len(out),
          ("：" + "；".join("%s 事件 %s / 消息 %s" % (a, b, c) for a, b, c, _ in out[:3])) if out else ""))
    return {"checked": len(rows), "out_of_window": len(out), "dist": dist}


# ③ 产物 ← 库
def t3(con):
    h1("③ 产物 ← 库：报告的数据截至时间 vs 库内最新事件")
    mx = con.execute("select max(date) from events where date like '____-__-__'").fetchone()[0]
    stamp_p = os.path.join(TMP, "pipeline_stamp.json")
    if not os.path.exists(stamp_p):
        check("存在统一版本戳", False, "未找到 pipeline_stamp.json（先跑 regenerate_all.py）", warn=True)
        return {}
    st = json.load(io.open(stamp_p, encoding="utf-8"))
    ok = (st.get("data_until") or "") >= (mx or "")
    check("报告数据截至 ≥ 库内最新事件", ok, "报告 %s ｜ 库内最新事件 %s" % (st.get("data_until"), mx))
    return {"data_until": st.get("data_until"), "max_event": mx}


# ④ 时间可定位率
def t4(con):
    h1("④ 时间可定位率：有多少东西「漂浮在时间外」")
    tot = con.execute("select count(*) from events").fetchone()[0]
    by = dict(con.execute("select date_certainty, count(*) from events group by 1"))
    nodate = con.execute("select count(*) from events where date is null or trim(date)=''").fetchone()[0]
    rng = by.get("区间", 0)
    ok = (nodate / tot) < 0.05
    for k, v in sorted(by.items(), key=lambda x: -x[1]):
        print("        %-6s %5d（%.1f%%）" % (k, v, v / tot * 100))
    check("无日期事件 < 5%", ok, "无日期 %d / %d = %.2f%% ｜ 区间 %d" % (nodate, tot, nodate / tot * 100, rng),
          warn=True)
    return {"total": tot, "no_date": nodate, "range": rng}


ENGINE_MD = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\05-纠偏层.md"


# ⑤ 人名首现时间 vs 结论成立时间
def t5(con):
    h1("⑤ 抽样盲测：结论里提到的人，在聊天数据里是什么时候第一次出现的")
    if not os.path.exists(ENGINE_MD):
        check("能找到引擎纠偏层", False, ENGINE_MD, warn=True); return {}
    txt = io.open(ENGINE_MD, encoding="utf-8").read()
    parts = re.split(r"^(## .+)$", txt, flags=re.M)
    secs = {}
    for i in range(1, len(parts) - 1, 2):
        secs[parts[i].strip()] = parts[i + 1]

    names = [n for (n,) in con.execute(
        "select person from events where person is not null and length(person)>=2 group by person")]
    rows = con.execute("""select concl_id, valid_from, source_doc from conclusions
                           where valid_from is not null and trim(valid_from)<>''""").fetchall()

    use = {}          # name -> [(concl_id, valid_from)]
    for cid, vfrom, src in rows:
        key = re.sub(r"^05-纠偏层\.md · ", "", src or "").strip()[:14]
        body = next((b for h, b in secs.items() if key and key in h), "")
        if not body:
            continue
        for n in names:
            if n in body:
                use.setdefault(n, []).append((cid, vfrom))
    if not use:
        check("能从结论出处里认出人名", False, "0 个", warn=True); return {}

    ic = ro(INDEX_DB)
    leak, known = [], 0
    for n, refs in sorted(use.items()):
        row = ic.execute("select min(ts), max(ts) from messages where content like ?",
                         ("%" + n + "%",)).fetchone()
        first = row[0]
        if not first:
            continue
        fd = datetime.datetime.fromtimestamp(first).strftime("%Y-%m-%d")
        for cid, vfrom in refs:
            if fd > vfrom:
                leak.append((cid, n, fd, vfrom))
            else:
                known += 1
    ic.close()
    print("        认出人名 %d 个 ｜ 比对 (结论×人名) %d 对" % (len(use), sum(len(v) for v in use.values())))
    check("结论提到的人，都在结论成立之前就出现过", not leak,
          "时间倒流 %d 对%s" % (len(leak),
          ("：" + "；".join("%s 提到「%s」但其首现是 %s（结论成立于 %s）" % x for x in leak[:4])) if leak else
          "　→ 无「未来人物」泄漏"))
    return {"names": len(use), "pairs": sum(len(v) for v in use.values()), "leak": len(leak)}


def _section_text(title):
    """从 05-纠偏层.md 取出 source_doc 指向的那一节正文"""
    if not os.path.exists(ENGINE_MD):
        return ""
    txt = io.open(ENGINE_MD, encoding="utf-8").read()
    parts = re.split(r"^(## .+)$", txt, flags=re.M)
    key = re.sub(r"^05-纠偏层\.md · ", "", title or "").strip()[:24]
    for i in range(1, len(parts) - 1, 2):
        if key and key[:14] in parts[i]:
            return parts[i + 1]
    return ""


def case(cid):
    con = ro(ANALYSIS_DB)
    r = con.execute("select concl_id,statement,status,valid_from,evidence_refs,counter_examples,source_doc "
                    "from conclusions where concl_id=?", (cid,)).fetchone()
    if not r:
        print("未找到 %s" % cid); return
    cid, stmt, status, vfrom, refs, cnt, src = r
    print("=" * 70)
    print("盲测资料包 · %s" % cid)
    print("=" * 70)
    print("  结论      %s" % stmt)
    print("  状态      %s" % status)
    print("  成立时间  %s" % (vfrom or "（未标）"))
    print("  出处      %s" % src)
    print()

    # 从出处章节里认人（拿全库对话人名去匹配）
    sec = _section_text(src)
    people = []
    if sec:
        names = [n for (n,) in con.execute(
            "select distinct person from events where person is not null and length(person)>=2")]
        for n in names:
            if n in sec:
                people.append(n)
        people = sorted(set(people), key=lambda x: -sec.count(x))[:6]
    print("  涉及人    %s" % ("、".join(people) if people else "（未能从出处章节认出人）"))
    print()

    if not vfrom:
        print("  ⚠️ 该结论没标「成立时间」，无法做时间盲测 —— 需人工补 valid_from。")
        con.close(); return

    print("  ── 只看 %s 之前的资料（截止日之后的一律不出现）──" % vfrom)
    n = 0
    if people:
        q = ",".join("?" * len(people))
        rows = con.execute("""select event_id,date,person,substr(event,1,64) from events
                               where date <= ? and person in (%s)
                               order by date desc limit 14""" % q, [vfrom] + people).fetchall()
        for eid, d, p, ev in rows:
            n += 1
            print("    %s  %s  %-10s %s" % (eid, d, (p or "")[:10], ev))
    if n == 0:
        print("    （截止日之前，这些人的事件为空）")
    print()
    print("  ── 反例 / 红线（若成立，该结论就该被推翻）──")
    print("    %s" % (cnt or "—"))
    print()
    print("  ★ 盲测问法：**只看上面这些 %s 之前的资料**，能不能独立得出这条结论？" % vfrom)
    print("     必须用到 %s 之后的信息才能成立 → **时间泄漏**。" % vfrom)
    print("     把结论的原话（含推理）贴出来对比，可人工判定：")
    print("     %s" % (stmt[:200]))
    con.close()


def main():
    if "--case" in sys.argv:
        case(sys.argv[sys.argv.index("--case") + 1]); return 0
    print("时间盲测 · %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    con = ro(ANALYSIS_DB)
    a = t1(con); b = t2(con); c = t3(con); d = t4(con); e = t5(con)
    con.close()
    h1("汇总")
    npass = sum(1 for r in results if r["ok"])
    nfail = sum(1 for r in results if not r["ok"] and not r["warn"])
    nwarn = sum(1 for r in results if not r["ok"] and r["warn"])
    print("  通过 %d ｜ 失败 %d ｜ 警告 %d" % (npass, nfail, nwarn))
    for r in results:
        if not r["ok"]:
            print("    %s %s" % ("[WARN]" if r["warn"] else "[FAIL]", r["name"]))
    payload = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "summary": {"pass": npass, "fail": nfail, "warn": nwarn}, "checks": results}
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
        print("  JSON → %s" % out)
    return nfail


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
