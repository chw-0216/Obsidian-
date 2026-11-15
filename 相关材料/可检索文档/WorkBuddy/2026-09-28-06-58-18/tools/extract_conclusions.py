# -*- coding: utf-8 -*-
"""
extract_conclusions.py —— 从 05-纠偏层.md 提取结论 → conclusions 表（幂等）

结论状态四档：待核实 / 有效 / 已修正 / 已撤回
每条记录：statement · 支持证据 · 反例/红线 · 本人确认 · 适用时间 · 原出处

用法：
  python tools\\extract_conclusions.py
  python tools\\extract_conclusions.py --db <路径>    # 对副本跑（验收用）
"""
import io, os, re, sys, sqlite3, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ENGINE = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references"
SRC = os.path.join(ENGINE, "05-纠偏层.md")
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 不入表的章节：
#  · 「四、使用方式」「五、一条元规则」= 操作说明
#  · 「一、十一种已知失效模式」= **容器章节**（11 条失效模式各自才是结论，容器本身不是）
SKIP_TITLES = ("四、使用方式", "五、一条元规则", "一、十一种已知失效模式")


def clean(s):
    s = re.sub(r"^[>\s]+", "", s or "", flags=re.M)
    s = re.sub(r"\*\*", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pick_one_liner(block):
    """取块里的「一句话」或首个引用句"""
    m = re.search(r"\*\*一句话\*\*[：:]\s*(.+?)(?:\n\s*\n|\n#|\Z)", block, re.S)
    if not m:
        m = re.search(r"^>\s*\*\*(.+?)\*\*", block, re.M | re.S)
    if not m:
        m = re.search(r"^>\s*(.+?)(?:\n\s*\n|\Z)", block, re.M | re.S)
    return clean(m.group(1))[:900] if m else ""


def pick_redlines(block):
    """取红线 / 不得读成 / 反例（★ 跳过 Markdown 表格行，否则表头会被当成红线）"""
    out = []
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("|") or set(s) <= set("-: "):     # 表格行 / 分隔线
            continue
        if not re.search(r"红线|不得读成|不得当|反例|已推翻|已撤回|失效", s):
            continue
        t = clean(s)
        if 6 < len(t) < 300:
            out.append(t)
    return " ｜ ".join(out[:4])[:900]


def guess_status(title, block):
    if re.search(r"已推翻|已失效|已撤回", title):
        return "已撤回"
    if re.search(r"修正|推翻", title):
        return "已修正"
    if re.search(r"待验证假设|未证实|待核实|假设", block[:1200]):
        return "待核实"
    return "有效"


def main():
    global ANALYSIS_DB
    if "--db" in sys.argv:
        ANALYSIS_DB = sys.argv[sys.argv.index("--db") + 1]
    con = sqlite3.connect(ANALYSIS_DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS conclusions(
          concl_id TEXT PRIMARY KEY, statement TEXT NOT NULL, status TEXT DEFAULT '待核实',
          evidence_refs TEXT, counter_examples TEXT, self_confirmed INTEGER DEFAULT 0,
          valid_from TEXT, valid_to TEXT, source_doc TEXT, note TEXT,
          verdict TEXT DEFAULT '待定', my_note TEXT DEFAULT '',
          created_at TEXT, updated_at TEXT);
    """)
    # 老库补人工字段（新库建表时已有）
    for col, decl in (("verdict", "TEXT DEFAULT '待定'"), ("my_note", "TEXT DEFAULT ''")):
        if col not in [r[1] for r in con.execute("pragma table_info(conclusions)")]:
            con.execute("ALTER TABLE conclusions ADD COLUMN %s %s" % (col, decl))

    # ★★ 全量重建前，先把**人工字段**捞出来 —— 否则你的批注会被 delete 抹掉
    human = {cid: (v or "待定", n or "") for cid, v, n in
             con.execute("select concl_id, verdict, my_note from conclusions")}

    con.execute("delete from conclusions")   # 全量重建（幂等）

    txt = io.open(SRC, encoding="utf-8").read()
    blocks = []
    parts = re.split(r"^(## .+)$", txt, flags=re.M)
    # parts: [前言, 标题1, 正文1, 标题2, 正文2, ...]
    for i in range(1, len(parts) - 1, 2):
        blocks.append((parts[i].strip(), parts[i + 1]))

    rows = []
    n = 0
    for title_line, block in blocks:
        title = title_line[2:].strip()
        if any(s in title for s in SKIP_TITLES):
            continue

        # ★ 特判：「已推翻 / 已失效清单」是表格 → 逐行提取，每行一条「已撤回/已修正」结论
        if "已推翻" in title and "清单" in title:
            for line in block.splitlines():
                m = re.match(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
                if not m:
                    continue
                c0, st0, why = (x.strip() for x in m.groups())
                if c0 in ("结论",) or set(c0) <= set("-: "):
                    continue
                n += 1
                status0 = "已撤回" if re.search(r"已废|已否决|已剔除|已卡死|已废止", st0) else "已修正"
                ds0 = re.findall(r"(20\d\d-\d\d-\d\d)", st0 or "")   # 撤回理由里若带日期，用它当成立时间
                rows.append(("CON-%03d" % n, c0[:1200], status0, "", why[:900], 0,
                             ds0[-1] if ds0 else "", "", "05-纠偏层.md · 二、已推翻清单", st0, NOW, NOW))
            continue

        n += 1
        cid = "CON-%03d" % n

        # ★ 成立时间：标题里**最后一个**日期
        #   （「（2026-09-30 立题 · 2026-10-04 裁定）」→ 取裁定日 10-04，不是立题日）
        #   标题没有日期时，退一步看正文开头 3 行（章节导语常带日期）
        ds = re.findall(r"(20\d\d-\d\d-\d\d)", title)
        if not ds:
            head = "\n".join([l for l in (block or "").splitlines() if l.strip()][:3])
            ds = re.findall(r"(20\d\d-\d\d-\d\d)", head)
        vfrom = ds[-1] if ds else ""

        status = guess_status(title, block)
        one = pick_one_liner(block)
        statement = one or clean(title)
        note0 = "" if one else "⚠️ 待补充一句话（原块无「一句话」引用）"
        # 支持证据：块里出现的 三·补·N / 事件 ID / 报告名
        evs = sorted(set(re.findall(r"EVT-\d{8}-\d{3}", block)))
        evs += sorted(set(re.findall(r"三·补·\d+", block)))
        self_conf = 1 if re.search(r"本人(指出|裁定|确认|补裁定|指令|说过|原话)", title + block[:600]) else 0

        rows.append((
            cid, statement[:1200], status,
            "、".join(evs[:20]), pick_redlines(block), self_conf,
            vfrom, "", "05-纠偏层.md · " + title[:120], note0,
            NOW, NOW,
        ))

    con.executemany("""
        INSERT INTO conclusions(concl_id,statement,status,evidence_refs,counter_examples,
            self_confirmed,valid_from,valid_to,source_doc,note,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(concl_id) DO UPDATE SET
            statement=excluded.statement, status=excluded.status,
            evidence_refs=excluded.evidence_refs, counter_examples=excluded.counter_examples,
            self_confirmed=excluded.self_confirmed, valid_from=excluded.valid_from,
            source_doc=excluded.source_doc, updated_at=excluded.updated_at
    """, rows)
    # ★ 恢复人工字段（`delete from` 之后的补回；不存在的 ID 自动 no-op）
    if human:
        con.executemany("UPDATE conclusions SET verdict=?, my_note=? WHERE concl_id=?",
                        [(v, n, cid) for cid, (v, n) in human.items()])

    con.execute("""INSERT INTO meta(key,value) VALUES('conclusions_at',?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""", (NOW,))
    con.commit()
    try:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass

    print("结论 → %d 条" % len(rows))
    print()
    print("状态分布：")
    for st, c in con.execute("select status, count(*) from conclusions group by 1 order by 2 desc"):
        print("    %-8s %3d" % (st, c))
    print()
    print("样例：")
    for r in con.execute("select concl_id, status, substr(statement,1,64) from conclusions limit 6"):
        print("    %s [%s] %s" % r)
    con.close()


if __name__ == "__main__":
    main()
