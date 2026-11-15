# -*- coding: utf-8 -*-
"""
build_analysis_db.py —— 建分析库 analysis.sqlite（幂等 · 可追溯）

解决三个实际问题：
  ① 事件表「编号」列全空 → 建立**永久事件 ID**（自然键去重 + 代理键持久化）
  ② 「证据」列 62% 不是证据、且真 ID 回链不上 → 证据**分级 + 标记**
  ③ 缺复核状态 / 抽取版本 → 全部补上

设计原则：
  · **永久 ID**：`EVT-YYYYMMDD-NNN`。自然键 = sha1(日期|对话人|事件全文)；
    重跑时按自然键复用旧 ID。**改日期**时按 (对话人|事件) 二次匹配复用旧 ID，
    并把「旧日期 → 新日期」写进 revisions（**日期修改保留历史**）。
  · **人工字段不覆盖**：`load_self`（本人确认的感受）与人工复核状态永不被 CSV 覆盖。
  · **原始库只读**：index.sqlite 一律 `file:...?mode=ro`。
  · **每次运行写 meta**（版本 / 数据截至 / 生成时间）。

用法：
  python tools\\build_analysis_db.py                          # 迁移 + 增量（幂等）
  python tools\\build_analysis_db.py --rebuild                # 删库重建（⚠️ 丢 revisions）
  python tools\\build_analysis_db.py --db X --csv Y --quiet   # 供验收/回归测试用
"""
import csv, io, os, re, sys, json, sqlite3, hashlib, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ENGINE = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references"
EV_CSV = os.path.join(ENGINE, "事件库.csv")
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

EXTRACT_VERSION = "v1-migrate-20261004"

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS meta(
  key   TEXT PRIMARY KEY,
  value TEXT
);

-- ★ 事件主表（永久 ID）
CREATE TABLE IF NOT EXISTS events(
  event_id        TEXT PRIMARY KEY,      -- EVT-YYYYMMDD-NNN · 一旦分配永不改变
  natkey          TEXT UNIQUE,           -- 自然键（去重依据）
  date            TEXT,                  -- 事件发生时间（推断）
  date_certainty  TEXT DEFAULT '确定',    -- 确定 / 区间 / 推测
  phase           TEXT,
  level           TEXT,                  -- A / B / C
  score           INTEGER,
  subject         TEXT,                  -- 单方 / 双方
  category        TEXT,
  nature          TEXT,                  -- 已发生 / 计划 / 待核实
  event           TEXT NOT NULL,
  person          TEXT,                  -- 对话人
  distance        TEXT,                  -- 距离档
  relation        TEXT,
  match_kind      TEXT,                  -- 标注 / 画像
  people          TEXT,                  -- 涉及人
  msg_count       INTEGER,
  load_rule       TEXT,                  -- ★ 规则评分（原「情感负荷」，非本人感受）
  load_score      INTEGER,
  load_self       TEXT DEFAULT '',       -- ★ 本人确认的感受（空 = 未确认）
  mark            TEXT,
  source          TEXT,                  -- A/B/C/D/E 类
  impact          TEXT,
  review_status   TEXT DEFAULT '待核实',  -- 待核实 / 已核实 / 已修正 / 已撤回
  extract_version TEXT,
  created_at      TEXT,
  updated_at      TEXT
);

-- ★ 证据表（一事件多证据）
CREATE TABLE IF NOT EXISTS evidence(
  evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id    TEXT NOT NULL,
  msg_id      INTEGER,                   -- 索引库 messages.id（真实引用）
  legacy_ref  TEXT,                      -- 旧 msg_xxx（孤儿 ID）
  session_key TEXT,
  talker_name TEXT,
  ts          INTEGER,
  quote       TEXT,                      -- 原文片段
  link_status TEXT,                      -- ok / orphan / rebuilt / ambiguous / not_evidence / text_only
  confidence  REAL,
  note        TEXT,
  FOREIGN KEY(event_id) REFERENCES events(event_id)
);

-- ★ 结论状态表
CREATE TABLE IF NOT EXISTS conclusions(
  concl_id         TEXT PRIMARY KEY,
  statement        TEXT NOT NULL,
  status           TEXT DEFAULT '待核实', -- 待核实 / 有效 / 已修正 / 已撤回
  evidence_refs    TEXT,                 -- 支持证据（事件 ID / 报告 / 原话）
  counter_examples TEXT,                 -- 反例
  self_confirmed   INTEGER DEFAULT 0,    -- 机器判定：引擎文档里本人是否提过
  valid_from       TEXT,
  valid_to         TEXT,
  source_doc       TEXT,                 -- 原出处（如 05-纠偏层 三·补·38）
  note             TEXT,
  verdict          TEXT DEFAULT '待定',  -- ★ 人工字段：待定 / 认可 / 存疑 / 推翻（只在 Obsidian 笔记里改）
  my_note          TEXT DEFAULT '',      -- ★ 人工字段：我对这条结论的补充
  created_at       TEXT,
  updated_at       TEXT
);

-- 人物与别名（供 FTS 短词检索）
CREATE TABLE IF NOT EXISTS persons(
  person_id TEXT PRIMARY KEY,
  name      TEXT,
  talker    TEXT,
  relation  TEXT,
  distance  TEXT,
  note      TEXT
);
CREATE TABLE IF NOT EXISTS aliases(
  alias     TEXT PRIMARY KEY,
  person_id TEXT,
  kind      TEXT                          -- 备注 / 昵称 / 群名 / 旧名
);

-- ★ 变更历史（可追溯）
CREATE TABLE IF NOT EXISTS revisions(
  rev_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT,                       -- event / conclusion
  entity_id   TEXT,
  field       TEXT,
  old_value   TEXT,
  new_value   TEXT,
  changed_at  TEXT,
  reason      TEXT
);

-- ★ 当前画像视图：已撤回的结论**不得**出现
CREATE VIEW IF NOT EXISTS v_conclusions_current AS
  SELECT concl_id, statement, status, evidence_refs, counter_examples,
         self_confirmed, valid_from, valid_to, source_doc, note
    FROM conclusions
   WHERE status <> '已撤回';

CREATE INDEX IF NOT EXISTS idx_ev_date   ON events(date);
CREATE INDEX IF NOT EXISTS idx_ev_person ON events(person);
CREATE INDEX IF NOT EXISTS idx_ev_status ON events(review_status);
CREATE INDEX IF NOT EXISTS idx_ev_nature ON events(nature);
CREATE INDEX IF NOT EXISTS idx_evd_event ON evidence(event_id);
CREATE INDEX IF NOT EXISTS idx_evd_msg   ON evidence(msg_id);
"""

# 非证据词（原「证据」列里混进来的状态词）
NOT_EVIDENCE = {"正常", "待定", "ts转换", "补日", "无", "-", "空"}

EV_COLS = ("event_id,natkey,date,date_certainty,phase,level,score,subject,category,"
           "nature,event,person,distance,relation,match_kind,people,msg_count,load_rule,"
           "load_score,load_self,mark,source,impact,review_status,extract_version,"
           "created_at,updated_at")

# 可被 CSV 覆盖的列（人工字段 load_self / review_status 不在其中）
UPD_COLS = ("date=:date, date_certainty=:date_certainty, phase=:phase, level=:level, "
            "score=:score, category=:category, nature=:nature, event=:event, "
            "person=:person, distance=:distance, relation=:relation, "
            "msg_count=:msg_count, load_rule=:load_rule, load_score=:load_score, "
            "source=:source, impact=:impact, updated_at=:updated_at")


def natkey(date, person, event):
    s = "%s|%s|%s" % (date or "", person or "", (event or "").strip())
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def certainty(date):
    d = (date or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return "确定"
    if not d:
        return "推测"
    return "区间"          # 2026-07 / 2026-07-24至09-29 之类


def split_evidence(raw):
    """把「证据」列拆成若干条，并分级。"""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[|;]", raw) if p.strip()]
    out = []
    for p in parts:
        if re.fullmatch(r"msg_[0-9a-f]{6,}", p):
            out.append(("legacy", p))                     # 旧哈希 ID（孤儿）
        elif p in NOT_EVIDENCE:
            out.append(("not_evidence", p))               # 状态词，不是证据
        else:
            out.append(("text_only", p))                  # 原文片段（转账/通知等）
    return out


def ev_dict(eid, nk, r, now):
    def i(x):
        try: return int(x)
        except Exception: return None
    date = (r.get("日期") or "").strip()
    return dict(
        event_id=eid, natkey=nk, date=date or None, date_certainty=certainty(date),
        phase=(r.get("阶段") or "").strip(), level=(r.get("层级") or "").strip(),
        score=i(r.get("分")), subject=(r.get("主体") or "").strip(),
        category=(r.get("类别") or "").strip(),
        nature=(r.get("性质") or "").strip() or "待核实",
        event=(r.get("事件") or "").strip(),
        person=(r.get("对话人") or "").strip() or None,
        distance=(r.get("距离半径") or "").strip(), relation=(r.get("关系") or "").strip(),
        match_kind=(r.get("匹配") or "").strip(), people=(r.get("涉及人") or "").strip(),
        msg_count=i(r.get("条数")), load_rule=(r.get("情感负荷") or "").strip(),
        load_score=i(r.get("负荷分")), mark=(r.get("标记") or "").strip(),
        source=(r.get("来源") or "").strip(), impact=(r.get("影响") or "").strip(),
        extract_version=EXTRACT_VERSION, created_at=now, updated_at=now,
    )


def arg(flag, default):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main():
    global ANALYSIS_DB, EV_CSV
    ANALYSIS_DB = arg("--db", ANALYSIS_DB)
    EV_CSV = arg("--csv", EV_CSV)
    quiet = "--quiet" in sys.argv
    rebuild = "--rebuild" in sys.argv
    # 统一管线会透传生成时间，保证所有产物同一时间戳
    NOW = arg("--now", "") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if rebuild and os.path.exists(ANALYSIS_DB):
        for suffix in ("", "-wal", "-shm"):
            try: os.remove(ANALYSIS_DB + suffix)
            except Exception: pass
        if not quiet: print("⚠️ 已删除旧分析库，重建中…")

    con = sqlite3.connect(ANALYSIS_DB)
    con.executescript(SCHEMA)

    # ---- ★ 人工字段迁移（老库补列；新库建表时已有）----
    # 原则：**人工字段永不被脚本覆盖**，所以加列用 ADD COLUMN（保留已有值）
    HUMAN_COLS = [("conclusions", "verdict", "TEXT DEFAULT '待定'"),
                  ("conclusions", "my_note", "TEXT DEFAULT ''"),
                  ("events", "load_self", "TEXT DEFAULT ''"),
                  ("events", "review_status", "TEXT DEFAULT '待核实'")]
    for tbl, col, decl in HUMAN_COLS:
        cols = [r[1] for r in con.execute("pragma table_info(%s)" % tbl)]
        if col not in cols:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (tbl, col, decl))
            if not quiet:
                print("  ＋ 补人工字段 %s.%s" % (tbl, col))
    con.commit()

    # ---- 载入已有（幂等基础 + 日期修订基础）----
    have = {}        # natkey -> eid
    by_pe = {}       # (对话人, 事件) -> [eid, ...]
    maxseq = {}
    for eid, nk, person, event in con.execute("select event_id,natkey,person,event from events"):
        have[nk] = eid
        by_pe.setdefault(((person or "").strip(), (event or "").strip()), []).append(eid)
        m = re.match(r"EVT-([\dA-Z]+)-(\d+)$", eid)
        if m:
            d, n = m.group(1), int(m.group(2))
            maxseq[d] = max(maxseq.get(d, 0), n)
    if not quiet:
        print("已有事件 %d 条" % len(have))

    # ---- 读事件库 CSV ----
    rows = list(csv.DictReader(io.open(EV_CSV, encoding="utf-8-sig")))
    if not quiet:
        print("CSV 事件 %d 条" % len(rows))

    ins_ev = upd_ev = date_rev = 0
    ev_ins, ev_upd = [], []
    rev_rows, ev_evd_rows = [], []

    for r in rows:
        date = (r.get("日期") or "").strip()
        person = (r.get("对话人") or "").strip()
        event = (r.get("事件") or "").strip()
        nk = natkey(date, person, event)

        if nk in have:
            eid = have[nk]
            upd_ev += 1
            ev_upd.append(ev_dict(eid, nk, r, NOW))
        else:
            cand = by_pe.get((person, event), [])
            if len(cand) == 1:
                # ★ 日期修改：复用旧 ID，写 revisions
                eid = cand[0]
                old_date = con.execute("select date from events where event_id=?", (eid,)).fetchone()
                old_date = (old_date[0] if old_date else "") or ""
                if old_date != (date or ""):
                    rev_rows.append((eid, old_date, date or ""))
                    date_rev += 1
                have[nk] = eid
                upd_ev += 1
                ev_upd.append(ev_dict(eid, nk, r, NOW))
            else:
                d8 = date.replace("-", "") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else "UNDATED"
                maxseq[d8] = maxseq.get(d8, 0) + 1
                eid = "EVT-%s-%03d" % (d8, maxseq[d8])
                have[nk] = eid
                by_pe.setdefault((person, event), []).append(eid)
                ins_ev += 1
                ev_ins.append(ev_dict(eid, nk, r, NOW))

        # 证据
        for kind, val in split_evidence(r.get("证据")):
            if kind == "legacy":
                ev_evd_rows.append((eid, None, val, None, None, None, None, "orphan", 0.0,
                                    "旧版 msg_ 哈希 · 生成脚本已不存在 · 无法回链"))
            elif kind == "not_evidence":
                ev_evd_rows.append((eid, None, None, None, None, None, None, "not_evidence", 0.0,
                                    "原「证据」列填的是状态词「%s」，非证据" % val))
            else:
                ev_evd_rows.append((eid, None, None, None, None, None, val[:500], "text_only", 0.3,
                                    "原「证据」列为原文片段，未关联到消息 ID"))

    # ---- 落盘 ----
    if ev_ins:
        con.executemany("INSERT INTO events(%s) VALUES(:event_id,:natkey,:date,:date_certainty,"
                        ":phase,:level,:score,:subject,:category,:nature,:event,:person,:distance,"
                        ":relation,:match_kind,:people,:msg_count,:load_rule,:load_score,"
                        ":load_self,:mark,:source,:impact,:review_status,:extract_version,"
                        ":created_at,:updated_at)" % EV_COLS,
                        [dict(d, load_self="", review_status="待核实") for d in ev_ins])
    if ev_upd:
        con.executemany("UPDATE events SET natkey=:natkey, %s WHERE event_id=:event_id" % UPD_COLS, ev_upd)

    for eid, old_d, new_d in rev_rows:
        con.execute("INSERT INTO revisions(entity_type,entity_id,field,old_value,new_value,changed_at,reason) "
                    "VALUES('event',?,?,?,?,?,?)",
                    (eid, "date", old_d, new_d, NOW, "CSV 日期修订 · 保留原事件 ID"))

    con.execute("delete from evidence where link_status in ('orphan','not_evidence','text_only')")
    con.executemany("INSERT INTO evidence(event_id,msg_id,legacy_ref,session_key,talker_name,ts,quote,"
                    "link_status,confidence,note) VALUES(?,?,?,?,?,?,?,?,?,?)", ev_evd_rows)

    # ---- meta ----
    idx_cut = ""
    try:
        ic = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
        idx_cut = list(ic.execute("select max(date(ts,'unixepoch','localtime')) from messages"))[0][0] or ""
        ic.close()
    except Exception:
        pass

    meta = {
        "schema_version": "1",
        "extract_version": EXTRACT_VERSION,
        "data_until": idx_cut,
        "generated_at": NOW,
        "source_events_csv": EV_CSV,
        "source_index_db": INDEX_DB,
        "event_count": str(con.execute("select count(*) from events").fetchone()[0]),
        "evidence_count": str(con.execute("select count(*) from evidence").fetchone()[0]),
        "revision_count": str(con.execute("select count(*) from revisions").fetchone()[0]),
    }
    for k, v in meta.items():
        con.execute("INSERT INTO meta(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))

    con.commit()
    try:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass

    if not quiet:
        print()
        print("=" * 66)
        print("分析库 → %s（%.1f MB）" % (ANALYSIS_DB, os.path.getsize(ANALYSIS_DB) / 1024 / 1024))
        print("  本次：新增 %d · 更新 %d · 日期修订 %d" % (ins_ev, upd_ev, date_rev))
        print("  事件 %s · 证据 %s" % (meta["event_count"], meta["evidence_count"]))
        print()
        print("  证据分级：")
        for st, n in con.execute("select link_status, count(*) from evidence group by 1 order by 2 desc"):
            print("    %-14s %5d" % (st, n))
        print()
        print("  数据截至 %s ｜ 生成 %s ｜ 版本 %s" % (meta["data_until"], NOW, EXTRACT_VERSION))
        print("  样例 ID：", ", ".join(r[0] for r in con.execute("select event_id from events limit 5")))
    con.close()
    return {"insert": ins_ev, "update": upd_ev, "date_rev": date_rev, "meta": meta}


if __name__ == "__main__":
    main()
