# -*- coding: utf-8 -*-
"""
relink_evidence.py —— 证据回链重建（只读索引库 · 写分析库）

问题：事件库「证据」列的 msg_xxx 是**孤儿 ID**（生成脚本已不存在，回链不上任何库）。
     实测 2,862 条里只有 1,108 条是这种 ID，其余 1,576 条是状态词、272 条是原文片段。

做法：用「对话人 + 日期(±1天) + 文本相似度」从索引库**重新定位**真实消息。
     命中 → evidence(msg_id=索引库 messages.id, link_status='rebuilt', confidence=相似度)

用法：
  python tools\\relink_evidence.py            # 增量（只补还没有 rebuilt 的事件）
  python tools\\relink_evidence.py --all      # 全部重算
  python tools\\relink_evidence.py --limit 100
"""
import os, re, sys, sqlite3, datetime
from collections import defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

MIN_SCORE = 0.12          # 相似度下限（低于此不记）
HI_SCORE = 0.35           # 高置信阈值（≥ 记 rebuilt，否则记 ambiguous）
MIN_OVERLAP = 2           # 至少重叠的 2-gram 数
MAX_CAND_SESSIONS = 5     # 每个对话人最多取几个候选会话


def grams(s, n=2):
    s = re.sub(r"[\s\W_]+", "", s or "")
    return set(s[i:i + n] for i in range(len(s) - n + 1))


def sim(a, b):
    """返回 (重叠数, 相似度)"""
    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0, 0.0
    ov = len(ga & gb)
    return ov, ov / max(1, min(len(ga), len(gb)))


def day_range(date):
    try:
        d0 = datetime.datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        return None
    lo = int((d0 - datetime.timedelta(days=1)).timestamp())
    hi = int((d0 + datetime.timedelta(days=2)).timestamp())
    return lo, hi


def main():
    do_all = "--all" in sys.argv
    limit = None
    for a in sys.argv:
        if a.startswith("--limit"):
            limit = int(a.split("=")[-1]) if "=" in a else None
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    ana = sqlite3.connect(ANALYSIS_DB)
    ana.execute("PRAGMA journal_mode=WAL")

    # ---- 1) 取待处理事件 ----
    if do_all:
        ana.execute("delete from evidence where link_status in ('rebuilt','ambiguous','unlinked')")
        ana.commit()
    done = set(r[0] for r in ana.execute(
        "select distinct event_id from evidence where link_status in ('rebuilt','ambiguous','unlinked')"))
    rows = list(ana.execute("""
        select event_id, date, person, event from events
        where person is not null and person!='' and date is not null and date!=''
        order by date"""))
    todo = [r for r in rows if r[0] not in done]
    if limit:
        todo = todo[:limit]
    print("事件总数 %d · 已有回链 %d · 本次处理 %d" % (len(rows), len(done), len(todo)))
    if not todo:
        print("无需处理。")
        return

    idx = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)

    # ---- 2) 对话人 → 候选会话 ----
    name2sk = defaultdict(list)
    for talker, dn, mc in idx.execute(
            "select talker, coalesce(display_name,''), coalesce(message_count,0) from sessions"):
        if dn:
            name2sk[dn].append((mc, talker))
    for k in name2sk:
        name2sk[k].sort(reverse=True)
        name2sk[k] = [sk for _, sk in name2sk[k][:MAX_CAND_SESSIONS]]

    # ---- 3) 按对话人分组，一次拉取相关日期范围的消息 ----
    by_person = defaultdict(list)
    for eid, d, p, ev in todo:
        by_person[p].append((eid, d, ev))

    hit = amb = miss = nosess = 0
    evd = []
    for pi, (person, items) in enumerate(sorted(by_person.items()), 1):
        sks = name2sk.get(person)
        if not sks:
            # 用 LIKE 兜底找一次
            for (talker,) in idx.execute(
                    "select talker from sessions where display_name like ? limit 3", ("%" + person + "%",)):
                sks = sks or []
                sks.append(talker)
        if not sks:
            nosess += len(items)
            continue

        dates = [d for _, d, _ in items if day_range(d)]
        if not dates:
            continue
        lo = min(day_range(d)[0] for d in dates)
        hi = max(day_range(d)[1] for d in dates)

        # 拉候选消息
        pool = []
        qm = ",".join("?" * len(sks))
        for mid, sk, ts, role, content in idx.execute(
                "select id, session_key, ts, role, content from messages "
                "where session_key in (%s) and ts between ? and ?" % qm,
                (*sks, lo, hi)):
            if content:
                pool.append((mid, sk, ts, role, content))

        # 逐事件匹配
        for eid, d, ev in items:
            rng = day_range(d)
            if not rng:
                continue
            lo2, hi2 = rng
            best = (0, 0.0, None)
            for mid, sk, ts, role, content in pool:
                if not (lo2 <= ts <= hi2):
                    continue
                ov, sc = sim(ev, content)
                if ov > best[0] or (ov == best[0] and sc > best[1]):
                    best = (ov, sc, (mid, sk, ts, role, content))
            if best[2] and best[0] >= MIN_OVERLAP and best[1] >= MIN_SCORE:
                mid, sk, ts, role, content = best[2]
                if best[1] >= HI_SCORE:
                    st, cf = "rebuilt", round(best[1], 3)
                    note = "按对话人+日期±1天+文本相似度回链（重叠 %d 个 2-gram）" % best[0]
                    hit += 1
                else:
                    st, cf = "ambiguous", round(best[1], 3)
                    note = "低置信候选（重叠 %d 个 2-gram · %.2f）→ 待人工确认" % (best[0], best[1])
                    amb += 1
                evd.append((eid, mid, None, sk, person, ts, content[:500], st, cf, note))
            else:
                evd.append((eid, None, None, None, person, None, None, "unlinked", 0.0,
                            "已尝试回链（对话人+日期±1天）但未找到足够相似的原文 → 需人工或语义检索"))
                miss += 1

        if pi % 200 == 0:
            print("  … 已处理 %d/%d 个对话人（命中 %d）" % (pi, len(by_person), hit))

    # ---- 4) 写回 ----
    ana.executemany("""
        INSERT INTO evidence(event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,
            link_status,confidence,note) VALUES(?,?,?,?,?,?,?,?,?,?)
    """, evd)
    ana.execute("""INSERT INTO meta(key,value) VALUES('relink_at',?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    ana.commit()
    try:
        ana.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass

    print()
    print("=" * 66)
    print("回链完成：高置信 %d · 低置信候选 %d · 未命中 %d · 对话人不在库 %d" % (hit, amb, miss, nosess))
    print()
    print("证据分级（当前）：")
    for st, n in ana.execute("select link_status, count(*) from evidence group by 1 order by 2 desc"):
        print("    %-14s %5d" % (st, n))
    tot = ana.execute("select count(*) from events").fetchone()[0]
    linked = ana.execute("select count(distinct event_id) from evidence where link_status='rebuilt'").fetchone()[0]
    ambn = ana.execute("select count(distinct event_id) from evidence where link_status='ambiguous'").fetchone()[0]
    unl = ana.execute("select count(distinct event_id) from evidence where link_status='unlinked'").fetchone()[0]
    print()
    print("★ 可追溯率（高置信）  ：%d / %d = %.1f%%" % (linked, tot, linked * 100.0 / tot))
    print("★ 可追溯率（含低置信）：%d / %d = %.1f%%" % (linked + ambn, tot, (linked + ambn) * 100.0 / tot))
    print("★ 已尝试未命中        ：%d" % unl)
    ana.close()
    idx.close()


if __name__ == "__main__":
    main()
