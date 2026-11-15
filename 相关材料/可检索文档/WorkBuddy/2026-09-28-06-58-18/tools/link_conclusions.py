# -*- coding: utf-8 -*-
"""
link_conclusions.py —— 给每条结论自动匹配「支持它的证据事件」+ 标出成立时间

背景（盲测暴露的洞）：
  58 条结论里只有 **1 条**同时绑定了「支持证据的事件 ID」和「成立时间」
  → 「这条结论是什么时候、依据什么成立的」**无法自动对证**。

做法：
  结论 ←→ 事件，用 **IDF 加权的 bigram 覆盖率**匹配（不是朴素词频）。
  · 朴素覆盖率会被「收到转账 / 用户 / 对方」这类高频词灌满 → 实测噪声极大
  · IDF 把高频词压下去，稀有词（人名、项目名）抬上来 → 实测能分开

  再加两个加成：① 事件对话人是该章节的「主名」（正文出现 ≥2 次）
              ② 命中日期

过滤（宁可少报，不虚报）：
  保留 (对话人∈主名 且 分≥0.40) 或 (分≥0.65)，取前 5 条。

★ 独立于证据的「成立时间」：
  `valid_from` 由 extract_conclusions.py 从章节标题取（**不看证据**）
  → 这样「证据日期 ≤ 成立时间」才是**真检查**，不是自证。

用法：
  python tools\\link_conclusions.py            # 只读预览
  python tools\\link_conclusions.py --apply    # 写回 analysis.sqlite
"""
import os, io, re, sys, math, sqlite3, collections

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
ENGINE_MD = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\05-纠偏层.md"

TOP_K = 5
MIN_PERSON = 0.40      # 对话人是章节主名时的门槛
MIN_STRONG = 0.65      # 对话人不是主名、但文本极像时的门槛


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def bg(s):
    """中文 bigram（去空白与标点）"""
    s = re.sub(r"[\s\W_]+", "", s or "")
    return collections.Counter(s[i:i + 2] for i in range(len(s) - 1))


def load_sections():
    txt = io.open(ENGINE_MD, encoding="utf-8").read()
    parts = re.split(r"^(## .+)$", txt, flags=re.M)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def norm(s):
    """归一化标题：去空白与分隔符，避免 `二、已推翻 / 已失效清单` 对不上 `二、已推翻清单`"""
    return re.sub(r"[\s/·、．.,，()（）|｜]+", "", s or "")


def section_for(src, secs):
    key = re.sub(r"^05-纠偏层\.md · ", "", src or "").strip()
    if not key:
        return ""
    nk = norm(key)
    nsecs = {norm(h): b for h, b in secs.items()}
    # 逐级放长前缀：越短越容易命中，但要求前缀长度 ≥4 以免误撞
    for L in (len(nk), 14, 10, 6, 4):
        if L > len(nk):
            continue
        p = nk[:L]
        for nh, b in nsecs.items():
            if p and p in nh:
                return b
    return ""


def classify(body, src):
    """没匹配到事件时，判断这条结论**本来就不是**事件型的 —— 而不是「匹配失败」。
    这是本轮最重要的发现：多数结论的依据不是事件，是本人访谈或方法论。"""
    # ① 已撤回清单里的，本来就不在当前画像里
    if "已推翻" in (src or ""):
        return "已撤回（无当前效力）"
    # ② 系统 / 方法论类，依据不是事件
    if re.search(r"方法论|系统重构|元规则|失效模式|数据源盘点|使用方式|本引擎|隐私|工作台", (body or "")[:400]):
        return "方法论/系统"
    # ③ 依据是本人陈述（原话/访谈），不是聊天事件
    if re.search(r"本人(原话|指出|裁定|口述|亲口|补充|回答|说过|指令|确认)", (body or "")[:800]) \
       or re.search(r"[「『]", (body or "")[:400]):
        return "本人自述"
    return "无事件依据"


def main():
    apply = "--apply" in sys.argv
    secs = load_sections()

    con = sqlite3.connect(ANALYSIS_DB)
    # ---- 补列 ----
    cols = [r[1] for r in con.execute("pragma table_info(conclusions)")]
    for col, decl in (("evidence_events", "TEXT DEFAULT ''"),
                      ("link_score", "REAL DEFAULT 0"),
                      ("link_method", "TEXT DEFAULT ''")):
        if col not in cols:
            con.execute("ALTER TABLE conclusions ADD COLUMN %s %s" % (col, decl))
    con.commit()

    evs = con.execute("select event_id,date,person,event from events").fetchall()
    names = sorted({p for _, _, p, _ in evs if p and len(p) >= 2})

    # ---- IDF ----
    df = collections.Counter()
    for _, _, _, ev in evs:
        df.update(set(bg(ev)))
    N = max(len(evs), 1)

    def w(g):
        return math.log(1.0 + N / (1.0 + df.get(g, 0)))

    ev_bg = [(eid, d, p, bg(ev), ev) for eid, d, p, ev in evs]

    rows = con.execute("select concl_id,statement,source_doc,valid_from from conclusions "
                       "order by concl_id").fetchall()
    out, viol, no_sec = [], [], []
    for cid, stmt, src, vfrom in rows:
        body = section_for(src, secs)
        if not body:
            no_sec.append((cid, src))
            continue
        bs = bg(body)
        ppl = {n for n in names if body.count(n) >= 2}
        cand = []
        for eid, d, p, be, ev in ev_bg:
            if not be:
                continue
            den = sum(w(g) * c for g, c in be.items())
            num = sum(w(g) * min(c, bs.get(g, 0)) for g, c in be.items())
            s = (num / den) if den else 0.0
            if p and p in ppl:
                s += 0.20
            keep = (p in ppl and s >= MIN_PERSON) or s >= MIN_STRONG
            if keep:
                cand.append((round(s, 3), eid, d, p))
        cand.sort(reverse=True)
        cand = cand[:TOP_K]
        ids = " ".join(c[1] for c in cand)
        top = cand[0][0] if cand else 0.0
        out.append((cid, ids, top, "auto-idf" if cand else classify(body, src), stmt, vfrom))
        # 证据日期 ≤ 成立时间？（成立时间是独立取的，所以这是**真检查**）
        if vfrom:
            for s, eid, d, p in cand:
                if d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and d > vfrom:
                    viol.append((cid, vfrom, eid, d, p))

    hit = [o for o in out if o[1]]
    print("=" * 72)
    print("结论 ←→ 事件  自动匹配%s" % ("（真写）" if apply else "（只读预览）"))
    print("=" * 72)
    kinds = collections.Counter(o[3] for o in out)
    print("  结论 %d 条：" % len(out))
    for k, v in kinds.most_common():
        print("      %-18s %3d 条" % (k, v))
    print()
    print("  ★ 有事件证据 = %d 条（%.1f%%）—— 只有这些能「自动对证」"
          % (len(hit), len(hit) / max(len(out), 1) * 100))
    print("  ★ 有事件证据 + 有成立时间 = %d 条"
          % sum(1 for o in out if o[1] and (o[5] or "").strip()))
    if no_sec:
        print("  ⚠️ 找不到出处章节 %d 条：%s" % (len(no_sec), "、".join(c for c, _ in no_sec[:5])))
    print()
    print("  样例（前 12 条匹配结果）：")
    for cid, ids, top, m, stmt, vfrom in out[:12]:
        n = len(ids.split()) if ids else 0
        print("    %-9s %-11s 分%.3f  证据 %d 条  成立 %s" % (
            cid, (stmt or "")[:11], top, n, vfrom or "—"))
    if viol:
        print()
        print("  ⚠️ 证据日期晚于成立时间 %d 处（要么匹配错了，要么真有时间泄漏）：" % len(viol))
        for cid, vfrom, eid, d, p in viol[:10]:
            print("      %s 成立 %s 却匹配到 %s（%s %s）" % (cid, vfrom, eid, d, p))

    if not apply:
        print()
        print("  （只读。要写回：python tools\\link_conclusions.py --apply）")
        con.close()
        return 0

    con.executemany("UPDATE conclusions SET evidence_events=?, link_score=?, link_method=? "
                    "WHERE concl_id=?", [(i, t, m, c) for c, i, t, m, _, _ in out])
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    print()
    print("  ✅ 已写回 %d 条（evidence_events / link_score / link_method）" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
