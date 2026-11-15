# -*- coding: utf-8 -*-
"""
build_number_baseline.py —— 数字基准（与各报告同一次计算生成）

每个指标都带 **统计范围 / 去重规则 / 查询方法**，写进：
  · _tmp/number_baseline.json      （机器可读）
  · 引擎 references\\00-真相源·数字基准.md 的自动区（<!-- NB:AUTO:BEGIN --> … END）

用法：
  python tools\\build_number_baseline.py
  python tools\\build_number_baseline.py --no-write    # 只算不写引擎
"""
import os, re, io, csv, sys, json, sqlite3, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
BASELINE_DOC = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\00-真相源·数字基准.md"
OUT_JSON = os.path.join(WS, "_tmp", "number_baseline.json")

BEGIN = "<!-- NB:AUTO:BEGIN -->"
END = "<!-- NB:AUTO:END -->"


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def collect(stamp):
    m = []
    a = ro(ANALYSIS_DB)
    n_ev = a.execute("select count(*) from events").fetchone()[0]
    n_evd = a.execute("select count(*) from evidence").fetchone()[0]
    n_trace = a.execute("select count(*) from evidence where link_status in ('rebuilt','ambiguous')").fetchone()[0]
    n_ok = a.execute("select count(*) from evidence where msg_id is not null").fetchone()[0]
    cdist = dict(a.execute("select status,count(*) from conclusions group by 1"))
    n_c = sum(cdist.values())
    jl = a.execute("select count(*) from events where event like '%井邻%' or event like '%洞台%' or people like '%洞台%'").fetchone()[0]
    dmin, dmax = a.execute("select min(date), max(date) from events where date like '____-__-__'").fetchone()
    a.close()

    m.append(("事件总数", n_ev, "analysis.sqlite 全部事件（含 2023–2026）",
              "自然键 sha1(日期\\|对话人\\|事件) 去重", "select count(*) from events"))
    m.append(("证据条目", n_evd, "一事件多证据展开后",
              "按 事件×证据 展开；重复运行先删后插", "select count(*) from evidence"))
    m.append(("证据可追溯率", "%.1f%%" % (n_trace / n_evd * 100), "rebuilt + ambiguous 占全部证据",
              "msg_id 唯一", "select count(*) from evidence where link_status in ('rebuilt','ambiguous')"))
    m.append(("真实消息引用", n_ok, "能回链索引库 messages.id 的证据",
              "回链校验 100% 命中", "select count(*) from evidence where msg_id is not null"))
    m.append(("结论总数", n_c, "从 05-纠偏层.md 提取",
              "按「三·补·N」小节去重；表格逐行", "select count(*) from conclusions"))
    m.append(("结论状态", " / ".join("%s %d" % (k, v) for k, v in sorted(cdist.items(), key=lambda x: -x[1])),
              "当前有效 = 总数 − 已撤回", "v_conclusions_current 排除已撤回", "select status,count(*) from conclusions group by 1"))
    # ★ 结论 ←→ 证据绑定（可追溯性的核心指标）
    #   注意：上面的连接已 close()，这里必须**另开一个**
    try:
        a2 = ro(ANALYSIS_DB)
        n_link = a2.execute("select count(*) from conclusions where trim(evidence_events)<>''").fetchone()[0]
        n_dead = a2.execute("select count(*) from conclusions where link_method like '已撤回%'").fetchone()[0]
        dist = list(a2.execute("select link_method,count(*) from conclusions group by 1 order by 2 desc"))
        a2.close()
        act = max(n_c - n_dead, 1)
        m.append(("★ 结论有事件证据", "%d / %d（%.1f%%）" % (n_link, act, n_link / act * 100),
                  "分母 = 结论总数 − 「已推翻清单」",
                  "IDF 加权 bigram；阈值 (对话人∈章节主名 且 ≥0.40) 或 ≥0.65",
                  "select count(*) from conclusions where trim(evidence_events)<>''"))
        m.append(("结论依据分布", " / ".join("%s %d" % (k, v) for k, v in dist),
                  "auto-idf = 有事件证据", "其余为本人自述 / 方法论 / 已撤回",
                  "select link_method,count(*) from conclusions group by 1"))
    except Exception as e:
        print("  ⚠️ 结论绑定指标未取到：%s" % e)
    m.append(("井邻/洞台事件", jl, "event/people 含「井邻」或「洞台」",
              "LIKE 兜底（两字词不走 FTS）", "select count(*) from events where event like '%井邻%' ..."))
    m.append(("事件日期跨度", "%s → %s" % (dmin, dmax), "date 为完整 YYYY-MM-DD 的事件",
              "排除区间/推测日期", "select min(date),max(date) from events"))

    # 索引库
    i = ro(INDEX_DB)
    n_msg = i.execute("select count(*) from messages").fetchone()[0]
    n_sess = i.execute("select count(distinct session_key) from messages").fetchone()[0]
    imin, imax = i.execute("select min(date(ts,'unixepoch','localtime')), max(date(ts,'unixepoch','localtime')) from messages").fetchone()
    n_zero = i.execute("select count(*) from (select session_key from messages group by 1 "
                       "having sum(case when role='me' then 1 else 0 end)=0)").fetchone()[0]
    n_zero_msg = i.execute("select count(*) from messages where session_key in "
                           "(select session_key from messages group by 1 having sum(case when role='me' then 1 else 0 end)=0)").fetchone()[0]
    i.close()
    m.append(("消息总量", n_msg, "index.sqlite 全部消息（含群聊/公众号/服务号）",
              "源库 0 重复（已按 server_id 校验）", "select count(*) from messages"))
    m.append(("会话数", n_sess, "distinct session_key", "—", "select count(distinct session_key) from messages"))
    m.append(("消息时间范围", "%s → %s" % (imin, imax), "本地时区", "datetime(ts,'unixepoch','localtime')", "select min/max(...)"))
    m.append(("零发言会话", "%d 个 / %d 条（%.1f%%）" % (n_zero, n_zero_msg, n_zero_msg / n_msg * 100),
              "他从未发言的会话", "sum(role='me')=0", "group by session_key having sum(...)=0"))

    # 支付流
    pf = os.path.join(WS, "_tmp", "payment_flow.csv")
    if os.path.exists(pf):
        rows = list(csv.DictReader(io.open(pf, encoding="utf-8-sig")))
        amt = 0.0
        for r in rows:
            try: amt += float(re.sub(r"[^\d.\-]", "", (r.get("金额") or "0") or "0"))
            except Exception: pass
        m.append(("支付流条数", len(rows), "_tmp/payment_flow.csv",
                  "按 (日期,金额,摘要) 去重", "len(rows)"))
        m.append(("支付流金额", "¥%.2f" % amt, "同上", "金额列数值求和", "sum(float(金额))"))

    # 逐日主表
    dm = os.path.join(WS, "_tmp", "daily_master.csv")
    if os.path.exists(dm):
        rows = list(csv.DictReader(io.open(dm, encoding="utf-8-sig")))
        cols = len(rows[0].keys()) if rows else 0
        m.append(("逐日主表", "%d 天 × %d 列" % (len(rows), cols), "_tmp/daily_master.csv",
                  "四源汇流按日聚合", "len(rows)"))

    return m


def render_md(stamp, m):
    L = [BEGIN,
         "> 本区由 `tools/build_number_baseline.py` 自动生成，**请勿手改**（改动会在下次运行被覆盖）。",
         "",
         "| 指标 | 值 | 统计范围 | 去重规则 | 查询方法 |",
         "|---|---|---|---|---|"]
    for name, val, scope, rule, q in m:
        L.append("| %s | **%s** | %s | %s | `%s` |" % (name, val, scope, rule, q))
    L += ["",
          "**数据截至** %s ｜ **生成时间** %s ｜ **抽取版本** %s ｜ **run_id** `%s`"
          % (stamp["data_until"], stamp["generated_at"], stamp["extract_version"], stamp["run_id"]),
          "", END]
    return "\n".join(L)


def main():
    stamp = {}
    sp = os.path.join(WS, "_tmp", "pipeline_stamp.json")
    if os.path.exists(sp):
        stamp = json.load(io.open(sp, encoding="utf-8"))
    else:
        stamp = {"run_id": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
                 "data_until": "", "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "extract_version": "v1-migrate-20261004"}

    m = collect(stamp)
    io.open(OUT_JSON, "w", encoding="utf-8").write(json.dumps(
        {"stamp": stamp, "metrics": [{"name": a, "value": b, "scope": c, "rule": d, "query": e} for a, b, c, d, e in m]},
        ensure_ascii=False, indent=2))
    print("数字基准 %d 项 → %s" % (len(m), OUT_JSON))

    if "--no-write" not in sys.argv:
        if os.path.exists(BASELINE_DOC):
            txt = io.open(BASELINE_DOC, encoding="utf-8").read()
            block = render_md(stamp, m)
            if BEGIN in txt and END in txt:
                txt = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, txt, flags=re.S)
            else:
                txt = txt.rstrip() + "\n\n" + block + "\n"
            io.open(BASELINE_DOC, "w", encoding="utf-8").write(txt)
            print("已写入引擎 00-真相源·数字基准.md 自动区")
        else:
            print("⚠️ 未找到 %s" % BASELINE_DOC)
    for name, val, *_ in m:
        print("  %-14s %s" % (name, val))


if __name__ == "__main__":
    main()
