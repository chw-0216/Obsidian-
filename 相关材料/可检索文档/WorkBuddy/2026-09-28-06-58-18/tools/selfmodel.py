# -*- coding: utf-8 -*-
"""
selfmodel.py —— 「可修订的自我模型」层（analysis.sqlite 扩展 + Obsidian 视图）

设计依据：《自我理解系统深化_20261010》00_方案与研究汇总.md / 01_数据结构与更新协议.json
落地原则：
  1. **只增不改** —— 只新建 5 张表，绝不动 events / evidence / conclusions / hypotheses /
     decisions / procedures / revisions 的既有结构。
  2. **本人原话与系统推断分开字段** —— reasons_verbatim vs reasons_inferred；
     「本人认可」与「外部事实验证」分开字段（human_review vs external_verification）。
  3. **不编造** —— 每条条目必须能回到出处；理由留空的就留空，不代填。
  4. **可检查** —— render 生成的 4 个视图都能看到「依据 / 范围 / 反例 / 更新原因」。

用法：
  python tools/selfmodel.py init
  python tools/selfmodel.py import tools/selfmodel_data/seed_20261010.json
  python tools/selfmodel.py render
  python tools/selfmodel.py stats
  python tools/selfmodel.py list claims|episodes|questions|views|recs
  python tools/selfmodel.py answer <question_id> "本人原话"
  python tools/selfmodel.py review <claim_id> accepted|corrected|rejected|not_applicable ["修订原话"]
  python tools/selfmodel.py reassess <episode_id> "是否仍会这样选 + 理由"
  python tools/selfmodel.py outcome <episode_id> <stage> ["实际结果"]
  python tools/selfmodel.py stale <view_id> "原因"

  # —— 依赖链（方案 update_protocol step 6–8）——
  python tools/selfmodel.py recimport tools/selfmodel_data/recs_20261010.json
  python tools/selfmodel.py rec list
  python tools/selfmodel.py link <claim_id> <rec_id> ["依赖说明"]
  python tools/selfmodel.py impact <claim_id>            # 这条理解被改，会动到哪些建议
  python tools/selfmodel.py impact --all                 # 全库依赖链体检

  # —— 两个读取接口（方案 future_reading_interface）——
  python tools/selfmodel.py brief "临汾"                  # read_understanding：按当前问题取阅读包
  python tools/selfmodel.py changes [--since 2026-10-10] # list_changes：变化 + 受影响建议

  # —— 理解判断与校准（《长期个性化智能体》第三节「同时回答两件事」）——
  python tools/selfmodel.py predict add P-XXX "待决问题" "系统推测他会怎么选" --basis SC-XXX
  python tools/selfmodel.py predict list [--pending]     # 列出理解判断
  python tools/selfmodel.py predict resolve <id> "实际选择" "他的理由" [--match matched|partial|mismatched]
  python tools/selfmodel.py predict outcome <id> worked|failed|mixed "说明"
  python tools/selfmodel.py calibrate                    # 推测准确率 + 哪类依据更准/更不准
  ★ 推测 ≠ 建议：`predictions` 是「我猜你会怎样」，`recommendations` 是「我建议你怎样」。

  # —— 人工回写（Obsidian 手填区 → 数据库）——
  python tools/selfmodel.py reason <episode_id> "我自己的理由"   # 补「理由」这一格
  python tools/selfmodel.py sync            # 只读：列出三个视图手填区里改了什么
  python tools/selfmodel.py sync --apply    # 真写回（自动备份 + 记 revisions）
  ★ render 会**先自动跑一次 sync --apply**，所以手填区内容不会丢。
"""
import io
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

ROOT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
DB = os.path.join(ROOT, "analysis.sqlite")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
VIEW_DIR = os.path.join(VAULT, "06_自我模型")

CLAIM_TYPES = ["fact", "self_report", "preference", "constraint",
               "capability", "pattern", "mechanism", "aspiration"]
TYPE_CN = {
    "fact": "事实／身份", "self_report": "本人表述", "preference": "偏好／取舍",
    "constraint": "现实约束", "capability": "能力／资产", "pattern": "行为模式",
    "mechanism": "机制假设", "aspiration": "未来目标",
}
EPISTEMIC_CN = {
    "reported": "本人这样说过", "inferred": "系统推断", "corroborated": "有额外依据",
    "disputed": "存疑", "withdrawn": "已撤回", "superseded": "被新版本替代",
    "needs_verification": "待核实",
}
REVIEW_CN = {
    "unreviewed": "尚未看过", "accepted": "认可", "corrected": "需要修正",
    "rejected": "不认同", "not_applicable": "不适用于这件事",
}
STAGE_CN = {
    "not_started": "未开始", "preparing": "制作中", "communicated": "已经沟通",
    "made": "完成制作", "delivered": "已交付", "accepted": "已接受", "unknown": "未知",
}
IMPACT_CN = {"high": "🔴 高", "medium": "🟠 中", "low": "🟡 低"}
QSTATUS_CN = {
    "proposed": "待问", "asked": "已问", "answered": "已答",
    "deferred": "暂缓", "resolved_by_evidence": "证据已解决", "not_applicable": "不适用",
}

DDL = """
CREATE TABLE IF NOT EXISTS self_claims (
  claim_id           TEXT PRIMARY KEY,
  claim_type         TEXT NOT NULL,
  subject_id         TEXT DEFAULT 'self',
  statement          TEXT NOT NULL,
  domain             TEXT,
  project_id         TEXT,
  role               TEXT,
  conditions         TEXT,
  excluded_contexts  TEXT,
  valid_from         TEXT,
  valid_to           TEXT,
  recorded_at        TEXT,
  last_verified      TEXT,
  epistemic_status   TEXT DEFAULT 'inferred',
  human_review       TEXT DEFAULT 'unreviewed',
  evidence_status    TEXT,
  uncertainty_basis  TEXT,
  counterevidence    TEXT,
  supersedes         TEXT,
  revision           INTEGER DEFAULT 1,
  privacy_scope      TEXT DEFAULT 'private',
  created_by         TEXT,
  origin_kind        TEXT,
  note               TEXT,
  updated_at         TEXT
);
CREATE TABLE IF NOT EXISTS claim_evidence (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id              TEXT NOT NULL,
  source_id             TEXT,
  evidence_id           TEXT,
  episode_id            TEXT,
  relation              TEXT,
  quote                 TEXT,
  speaker               TEXT,
  quote_subject         TEXT,
  source_root           TEXT,
  derived_from          TEXT,
  event_time            TEXT,
  source_locator        TEXT,
  link_status           TEXT,
  external_verification TEXT
);
CREATE TABLE IF NOT EXISTS choice_episodes (
  episode_id        TEXT PRIMARY KEY,
  question          TEXT,
  event_ids         TEXT,
  time              TEXT,
  context           TEXT,
  known_options     TEXT,
  feasible_options  TEXT,
  actual_choice     TEXT,
  reasons_verbatim  TEXT,
  reasons_inferred  TEXT,
  constraints       TEXT,
  expected          TEXT,
  outcome           TEXT,
  delivery_stage    TEXT DEFAULT 'unknown',
  user_reassessment TEXT,
  new_discovery     TEXT,
  source_refs       TEXT,
  created_at        TEXT,
  updated_at        TEXT
);
CREATE TABLE IF NOT EXISTS understanding_views (
  view_id               TEXT PRIMARY KEY,
  topic                 TEXT,
  current_question      TEXT,
  current_model         TEXT,
  development_goals     TEXT,
  applied_claims        TEXT,
  source_coverage       TEXT,
  changes_since_previous TEXT,
  alternatives          TEXT,
  unknowns              TEXT,
  stale                 INTEGER DEFAULT 0,
  stale_reason          TEXT,
  generated_at          TEXT,
  version               INTEGER DEFAULT 1,
  prior_version         TEXT,
  privacy_scope         TEXT DEFAULT 'private'
);
CREATE TABLE IF NOT EXISTS learning_questions (
  question_id       TEXT PRIMARY KEY,
  title             TEXT,
  target_claims     TEXT,
  target_decision   TEXT,
  decision_impact   TEXT,
  disagreement      TEXT,
  answer_difficulty TEXT,
  prior_answer      TEXT,
  why_reask         TEXT,
  status            TEXT DEFAULT 'proposed',
  answer_verbatim   TEXT,
  answer_time       TEXT,
  resolution        TEXT,
  created_at        TEXT,
  updated_at        TEXT
);
CREATE INDEX IF NOT EXISTS ix_claim_type   ON self_claims(claim_type);
CREATE INDEX IF NOT EXISTS ix_claim_review ON self_claims(human_review);
CREATE INDEX IF NOT EXISTS ix_ce_evidence  ON claim_evidence(claim_id);
CREATE INDEX IF NOT EXISTS ix_ce_episode   ON claim_evidence(episode_id);
CREATE INDEX IF NOT EXISTS ix_lq_status    ON learning_questions(status);

-- ★ 依赖链（第 6/7 张表）：让「纠正一条理解」能真的指出「哪条建议因此改变」
CREATE TABLE IF NOT EXISTS recommendations (
  rec_id          TEXT PRIMARY KEY,
  title           TEXT NOT NULL,
  body            TEXT,
  topic           TEXT,
  status          TEXT DEFAULT 'active',   -- active / superseded / withdrawn
  impact_if_wrong TEXT,                    -- 这条建议赖以成立的理解若错了，后果是什么
  created_at      TEXT,
  updated_at      TEXT
);
CREATE TABLE IF NOT EXISTS rec_deps (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  rec_id     TEXT NOT NULL,
  claim_id   TEXT NOT NULL,
  dep_kind   TEXT DEFAULT 'assumes',  -- assumes / requires / informed_by
  note       TEXT,
  created_at TEXT,
  UNIQUE(rec_id, claim_id)
);
CREATE INDEX IF NOT EXISTS ix_rec_deps_claim ON rec_deps(claim_id);
CREATE INDEX IF NOT EXISTS ix_rec_deps_rec   ON rec_deps(rec_id);

-- ★ 第 8 张表：理解判断（预测）与校准
--   落地《长期个性化智能体》第三节「同时回答两件事」：
--     ① 理解判断 —— 系统推测「你会怎么选」+ 依据（本表 predicted_*）
--     ② 决策建议 —— 由 recommendations 承载（本表 linked_rec_id 关联）
--   实际选择 / 本人理由 / 最终结果分别回填 → ①校准理解模型 ②回流建议
CREATE TABLE IF NOT EXISTS predictions (
  pred_id          TEXT PRIMARY KEY,
  created_at       TEXT,
  question         TEXT NOT NULL,          -- 待决问题
  topic            TEXT,
  horizon          TEXT,                   -- 预测针对的时间窗
  -- ① 理解判断
  predicted_choice TEXT,                   -- 系统推测他会怎么选
  predicted_reason TEXT,                   -- 推测依据（自然语言）
  basis_claims     TEXT,                   -- 依据的 claim_id（逗号分隔，可回链）
  alt_choices      TEXT,                   -- 系统认为的其他可能
  confidence       TEXT DEFAULT 'medium',  -- high / medium / low
  -- ② 决策建议（同一决策的另一路输出）
  linked_rec_id    TEXT,                   -- → recommendations.rec_id
  -- ③ 实际（回填）
  actual_choice    TEXT,
  actual_reason    TEXT,                   -- 本人原话
  actual_time      TEXT,
  -- ④ 对照（校准理解模型）
  match_status     TEXT DEFAULT 'pending', -- pending / matched / partial / mismatched
  match_by         TEXT,                   -- auto / human
  mismatch_note    TEXT,                   -- 不一致在哪
  -- ⑤ 结果（回流建议）
  outcome          TEXT,
  outcome_verdict  TEXT,                   -- worked / failed / mixed / unknown
  outcome_note     TEXT,
  updated_at       TEXT
);
CREATE INDEX IF NOT EXISTS ix_pred_status ON predictions(match_status);
CREATE INDEX IF NOT EXISTS ix_pred_rec    ON predictions(linked_rec_id);
"""


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def conn(write=False):
    if write:
        return sqlite3.connect(DB)
    return sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)


def log_revision(c, entity_type, entity_id, field, old, new, reason):
    """写入统一修订日志（revisions 表已存在，此处扩展其覆盖面）"""
    c.execute(
        "insert into revisions(entity_type,entity_id,field,old_value,new_value,"
        "changed_at,reason) values(?,?,?,?,?,?,?)",
        (entity_type, entity_id, field, old, new, now(), reason))


def cmd_init():
    c = conn(write=True)
    c.executescript(DDL)
    c.commit()
    print("[init] 8 张表就绪：self_claims / claim_evidence / choice_episodes /"
          " understanding_views / learning_questions / recommendations / rec_deps / predictions")
    for t in ("self_claims", "claim_evidence", "choice_episodes",
              "understanding_views", "learning_questions",
              "recommendations", "rec_deps", "predictions"):
        n = c.execute("select count(*) from %s" % t).fetchone()[0]
        print("       %-22s %d 行" % (t, n))
    c.close()


def cmd_import(path):
    data = json.load(io.open(path, encoding="utf-8"))
    c = conn(write=True)
    c.executescript(DDL)
    ts = now()
    n_c = n_e = n_q = 0

    for r in data.get("self_claims", []):
        c.execute("""insert or replace into self_claims(
            claim_id,claim_type,subject_id,statement,domain,project_id,role,
            conditions,excluded_contexts,valid_from,valid_to,recorded_at,
            last_verified,epistemic_status,human_review,evidence_status,
            uncertainty_basis,counterevidence,supersedes,revision,
            privacy_scope,created_by,origin_kind,note,updated_at)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            r["claim_id"], r["claim_type"], r.get("subject_id", "self"),
            r["statement"], r.get("domain"), r.get("project_id"), r.get("role"),
            json.dumps(r.get("conditions", []), ensure_ascii=False),
            json.dumps(r.get("excluded_contexts", []), ensure_ascii=False),
            r.get("valid_from"), r.get("valid_to"), r.get("recorded_at", ts),
            r.get("last_verified"), r.get("epistemic_status", "inferred"),
            r.get("human_review", "unreviewed"), r.get("evidence_status"),
            r.get("uncertainty_basis"), r.get("counterevidence"),
            r.get("supersedes"), r.get("revision", 1),
            r.get("privacy_scope", "private"), r.get("created_by", "agent:seed"),
            r.get("origin_kind"), r.get("note"), ts))
        n_c += 1
        # ★ 幂等：重跑同一份种子时不重复堆证据（claim_evidence 无唯一键）
        c.execute("delete from claim_evidence where claim_id=? and "
                  "coalesce(source_locator,'')='' and coalesce(quote,'')<>''",
                  (r["claim_id"],))
        for ev in r.get("evidence", []):
            c.execute("""insert into claim_evidence(claim_id,source_id,evidence_id,
                episode_id,relation,quote,speaker,quote_subject,source_root,
                derived_from,event_time,source_locator,link_status,
                external_verification) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                r["claim_id"], ev.get("source_id"), ev.get("evidence_id"),
                ev.get("episode_id"), ev.get("relation", "supports"),
                ev.get("quote"), ev.get("speaker"), ev.get("quote_subject"),
                ev.get("source_root"), ev.get("derived_from"),
                ev.get("event_time"), ev.get("source_locator"),
                ev.get("link_status"), ev.get("external_verification")))
            n_e += 1

    for r in data.get("choice_episodes", []):
        c.execute("""insert or replace into choice_episodes(
            episode_id,question,event_ids,time,context,known_options,
            feasible_options,actual_choice,reasons_verbatim,reasons_inferred,
            constraints,expected,outcome,delivery_stage,user_reassessment,
            new_discovery,source_refs,created_at,updated_at)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            r["episode_id"], r.get("question"), r.get("event_ids"), r.get("time"),
            r.get("context"), r.get("known_options"), r.get("feasible_options"),
            r.get("actual_choice"), r.get("reasons_verbatim"),
            json.dumps(r.get("reasons_inferred", []), ensure_ascii=False),
            r.get("constraints"), r.get("expected"), r.get("outcome"),
            r.get("delivery_stage", "unknown"), r.get("user_reassessment"),
            r.get("new_discovery"), r.get("source_refs"), ts, ts))
        n_c += 0
        n_q += 1

    n_q = 0
    for r in data.get("learning_questions", []):
        c.execute("""insert or replace into learning_questions(
            question_id,title,target_claims,target_decision,decision_impact,
            disagreement,answer_difficulty,prior_answer,why_reask,status,
            answer_verbatim,answer_time,resolution,created_at,updated_at)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            r["question_id"], r.get("title"),
            json.dumps(r.get("target_claims", []), ensure_ascii=False),
            r.get("target_decision"), r.get("decision_impact", "medium"),
            r.get("disagreement"), r.get("answer_difficulty", "medium"),
            r.get("prior_answer"), r.get("why_reask"),
            r.get("status", "proposed"), r.get("answer_verbatim"),
            r.get("answer_time"), r.get("resolution"), ts, ts))
        n_q += 1

    for r in data.get("understanding_views", []):
        c.execute("""insert or replace into understanding_views(
            view_id,topic,current_question,current_model,development_goals,
            applied_claims,source_coverage,changes_since_previous,alternatives,
            unknowns,stale,stale_reason,generated_at,version,prior_version,
            privacy_scope) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            r["view_id"], r.get("topic"), r.get("current_question"),
            r.get("current_model"), r.get("development_goals"),
            r.get("applied_claims"), r.get("source_coverage"),
            r.get("changes_since_previous"), r.get("alternatives"),
            r.get("unknowns"), r.get("stale", 0), r.get("stale_reason"),
            ts, r.get("version", 1), r.get("prior_version"),
            r.get("privacy_scope", "private")))

    log_revision(c, "selfmodel", path, "import",
                 None, "claims+%d / episodes+%d / questions+%d" % (
                     len(data.get("self_claims", [])),
                     len(data.get("choice_episodes", [])),
                     len(data.get("learning_questions", []))),
                 "首轮导入 / 幂等更新")
    c.commit()
    print("[import] %s" % os.path.basename(path))
    print("         self_claims +%d · claim_evidence +%d · choice_episodes +%d ·"
          " learning_questions +%d" % (
              len(data.get("self_claims", [])), n_e,
              len(data.get("choice_episodes", [])), n_q))
    c.close()


# ---------------------------------------------------------------- render

def _j(s):
    try:
        v = json.loads(s) if s else []
        return v if isinstance(v, list) else [v]
    except Exception:
        return []


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    b = text.encode("utf-8")
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    return len(b)


# ==========================================================================
# 手填区：Obsidian → 数据库 的**唯一人工入口**
#   方案 synchronization_gap：render 会重写视图 → 人工填写必须先能读回，否则
#   「围绕一次真实选择补上你的理由」这条闭环是断的。
#   设计：视图末尾一段带标记的 fenced 区；render **原样保留**；sync 读回后
#   把**已入库的行移除**（未入库／写失败的行保留），因此永不丢输入。
# ==========================================================================

ZONE_BEGIN = "<!-- >>> 手填区 · render 原样保留 · 填完跑 sync --apply >>> -->"
ZONE_END = "<!-- <<< 手填区 <<< -->"
ZONE_HINT = (
    "> **直接在这里写**：一行一个字段，写成 `字段: 内容`。**空着的行不会写入**。\n"
    "> 填完二选一：① `python tools/selfmodel.py sync --apply` "
    "② 直接跑 `render`（会先自动读回）。\n"
    "> 本区**不会被 render 覆盖**；已写进库的行下次会自动消失。"
)

ZONE_EP = {
    "理由": "reasons_verbatim", "我的理由": "reasons_verbatim",
    "实际选择": "actual_choice",
    "结果": "outcome", "结果／现在还缺的是": "outcome", "还缺什么": "outcome",
    "仍会这样选": "user_reassessment", "新发现": "new_discovery",
}
ZONE_LQ = {"回答": "answer_verbatim", "答案": "answer_verbatim", "结论": "resolution"}
ZONE_CL = {"我的判断": "human_review", "判断": "human_review", "备注": "note"}
ZONE_ALL = {}
for _m in (ZONE_EP, ZONE_LQ, ZONE_CL):
    ZONE_ALL.update(_m)

REVIEW_ALIAS = {
    "认可": "accepted", "accepted": "accepted",
    "需要修正": "corrected", "要修正": "corrected", "修正": "corrected",
    "corrected": "corrected",
    "不认同": "rejected", "rejected": "rejected",
    "不适用于这件事": "not_applicable", "不适用": "not_applicable",
    "not_applicable": "not_applicable",
}


def _read_zone(path):
    """取出视图里上一次的手填区正文（不含标记）；无则 None"""
    if not os.path.exists(path):
        return None
    try:
        txt = io.open(path, encoding="utf-8").read()
    except Exception:
        return None
    i = txt.find(ZONE_BEGIN)
    if i < 0:
        return None
    j = txt.find(ZONE_END, i)
    if j < 0:
        return None
    return txt[i + len(ZONE_BEGIN):j].strip("\n")


def _split_old_blocks(zone_text):
    """手填区正文 → {ID: 原始块文本}
    ★ 只去掉**尾部的空行**，不 rstrip 内容行 —— 否则会把 `回答: ` 的尾空格吃掉，
      下次生成模板时就不再是 `回答: `，用户回填位置会跑偏。
    """
    out, cur, buf = {}, None, []
    for line in (zone_text or "").splitlines():
        m = re.match(r"^\[([A-Za-z0-9_\-]+)\]\s*$", line.strip())
        if m:
            if cur:
                while buf and not buf[-1].strip():
                    buf.pop()
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        elif cur is not None:
            if line.strip().startswith("```"):
                continue          # ★ 代码围栏不是块内容，否则每轮会累加一行
            buf.append(line)
    if cur:
        while buf and not buf[-1].strip():
            buf.pop()
        out[cur] = "\n".join(buf)
    return out


def _parse_zone(zone_text):
    """手填区正文 → {ID: {字段: 值}}；**只收非空值**"""
    out = {}
    cur = None
    for raw in (zone_text or "").splitlines():
        s = raw.strip()
        if not s or s.startswith(">") or s.startswith("#") or s.startswith("```"):
            continue
        m = re.match(r"^\[([A-Za-z0-9_\-]+)\]\s*$", s)
        if m:
            cur = m.group(1)
            out.setdefault(cur, {})
            continue
        if cur is None:
            continue
        m = re.match(r"^([^:：]+)[:：]\s*(.*)$", s)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if v:
                out[cur][k] = v
    return out


def _zone_lines(path, items):
    """生成手填区（含标记）。
    items: [(ID, stub_lines, dbvals)]；stub_lines 形如 ["我的判断: ", "备注: "]
    dbvals: {列名: 当前库值}
    规则（按**字段名**对齐）：
      · 旧内容里该字段的值 == 库值 → 说明已入库 → 用**空模板**
      · 旧内容里该字段有值但不等于库值 → 原样保留（写失败／尚未同步）
      · 旧内容里多出来的字段／自由文字 → 原样保留在末尾
    """
    old_blocks = _split_old_blocks(_read_zone(path))
    out = []
    for iid, stub, dbvals in items:
        old_by_key, extra = {}, []
        for line in (old_blocks.get(iid) or "").splitlines():
            m = re.match(r"^([^:：]+)[:：]\s*(.*)$", line.strip())
            if not m:
                if line.strip():
                    extra.append(line)
                continue
            key, val = m.group(1).strip(), m.group(2).strip()
            f = ZONE_ALL.get(key)
            if f and val:
                dbv = (dbvals.get(f, "") or "").strip()
                cmp_val = REVIEW_ALIAS.get(val, val) if f == "human_review" else val
                if cmp_val == dbv:
                    continue            # 已入库 → 丢弃，回落到空模板
            old_by_key[key] = line
        out.append("[%s]" % iid)
        used = set()
        for s in stub:
            key = s.split(":")[0].strip()
            used.add(key)
            out.append(old_by_key.get(key, s))
        for k, line in old_by_key.items():
            if k not in used:
                out.append(line)
        out.extend(extra)
        out.append("")
    return [ZONE_BEGIN, "", ZONE_HINT, "", "```input",
            "\n".join(out).rstrip("\n"), "```", "", ZONE_END]


def _claim_line(r):
    d = dict(r)
    cond = _j(d.get("conditions"))
    exc = _j(d.get("excluded_contexts"))
    out = ["| `%s` | %s | %s | %s | %s |" % (
        d["claim_id"], d["statement"],
        EPISTEMIC_CN.get(d["epistemic_status"], d["epistemic_status"]),
        REVIEW_CN.get(d["human_review"], d["human_review"]),
        ("领域：" + (d["domain"] or "—")))]
    if cond:
        out.append("| | **适用条件**：%s | | | |" % " · ".join(cond))
    if exc:
        out.append("| | ⛔ **不能扩展**：%s | | | |" % " · ".join(exc))
    if d.get("counterevidence"):
        out.append("| | ⚠️ **反例/其他解释**：%s | | | |" % d["counterevidence"])
    if d.get("uncertainty_basis"):
        out.append("| | ❓ **还缺**：%s | | | |" % d["uncertainty_basis"])
    return "\n".join(out)


def cmd_render():
    # ★ 先把三个视图的手填区读回库 —— 否则下面重写视图会丢人工输入
    try:
        cap = cmd_sync(apply=True, quiet=True)
        if cap:
            print("[render] 先读回手填区 %d 处" % len(cap))
    except Exception as e:
        print("[render] ⚠️ 手填区读回失败（不影响生成）：%s" % e)
    c = conn()
    ts = now()
    os.makedirs(VIEW_DIR, exist_ok=True)
    written = []

    # ---------- 视图 1：系统当前怎样理解我
    claims = c.execute("select * from self_claims order by claim_type,claim_id").fetchall()
    cols = [x[1] for x in c.execute("pragma table_info(self_claims)")]
    rows = [dict(zip(cols, r)) for r in claims]
    by_type = {}
    for r in rows:
        by_type.setdefault(r["claim_type"], []).append(r)

    # 手填区只列「尚未审核 **且** 确实被某条建议依赖」的理解 —— 改这些才会动到建议
    _dep_claims = set(x[0] for x in c.execute(
        "select distinct claim_id from rec_deps"))
    _cl_items = [(r["claim_id"], ["我的判断: ", "备注: "],
                  {"human_review": r["human_review"] or "",
                   "note": r["note"] or ""})
                 for r in rows
                 if r["human_review"] == "unreviewed" and r["claim_id"] in _dep_claims]

    t = ["---", "tags: [自我模型, 系统理解, 可检查]", "created: 2026-10-10",
         "updated: %s" % ts[:10], "owner: 蔡浩文", "status: 首轮基线", "---", "",
         "# 🪞 系统当前怎样理解我", "",
         "> **这一页的作用**：让系统**把「我怎么理解你」摊开给你看** —— 每条都带**依据、适用范围、反例**。",
         "> **你可以直接改**：在下面的「我的判断」栏写 `认可` / `需要修正` / `不认同` / `不适用于这件事`。",
         "> **改完会生效**：下次 render 会把你的判断带进所有视图，并标出**哪条建议因此改变**。",
         "",
         "[[🏠主页]] ｜ [[自我理解引擎·打通页]] ｜ [[我的选择与理由]] ｜ [[值得继续问的问题]] ｜ [[本周理解变化]]",
         "",
         "> **数据来源**：`analysis.sqlite` 的 `self_claims` 表（本页自动生成，**请勿手改本页正文**；",
         "> 要改请改数据库或在下表「我的判断」栏填写，然后跑 `tools/selfmodel.py render` 重新生成）。",
         "",
         "**生成时间**：%s ｜ **条目总数**：%d ｜ **本人已审核**：%d" % (
             ts, len(rows), sum(1 for r in rows if r["human_review"] != "unreviewed")),
         "", "---", ""]

    for tp in CLAIM_TYPES:
        items = by_type.get(tp, [])
        if not items:
            continue
        t += ["## %s · %s（%d 条）" % (
            {"fact": "📌", "self_report": "🗣️", "preference": "⚖️",
             "constraint": "🔒", "capability": "🛠️", "pattern": "🔁",
             "mechanism": "🧩", "aspiration": "🎯"}[tp], TYPE_CN[tp], len(items)), "",
            "| ID | 系统当前的理解 | 认识状态 | 我的判断 | 备注 |",
            "|---|---|---|---|---|"]
        for r in items:
            t.append(_claim_line(r))
        t.append("")

    t += ["---", "", "## ⚠️ 本页红线", "",
          "1. **本人表述 ≠ 系统推断 ≠ 外部核实** —— 三者分列，不得混写。",
          "2. **老师/第三人的要求**只作为**对应项目条件**保存，不得写成本人偏好。",
          "3. **反例必须保留** —— 有反例的条目不得删掉反例后当结论用。",
          "4. **缺少检索结果 ≠ 现实不存在** —— 标「覆盖缺口」，不写成「没有」。",
          "5. 本页含私密内容，**不得外传**。", "",
          "---", "", "## ✍️ 手填区 · 我的判断", "",
          "> 只列**尚未审核、且确实被某条建议依赖**的理解（%d 条）—— 改这些才会动到建议。" % len(_cl_items),
          ""]
    t += _zone_lines(os.path.join(VIEW_DIR, "系统当前怎样理解我.md"), _cl_items)
    t += ["", "---", "",
          "*由 `tools/selfmodel.py render` 自动生成 · 设计依据：《自我理解系统深化_20261010》*"]
    written.append((os.path.join(VIEW_DIR, "系统当前怎样理解我.md"), _w(
        os.path.join(VIEW_DIR, "系统当前怎样理解我.md"), "\n".join(t) + "\n")))

    # ---------- 视图 2：本周理解变化
    t = ["---", "tags: [自我模型, 变更日志]", "created: 2026-10-10",
         "updated: %s" % ts[:10], "---", "", "# 🔄 本周理解变化", "",
         "> 每次新证据或你的纠正到来，**先在这里记一行** —— 写明「原来怎么理解 / 新证据是什么 / 现在怎么改 / 哪条建议因此变」。",
         "",
         "[[系统当前怎样理解我]] ｜ [[我的选择与理由]] ｜ [[值得继续问的问题]]",
         "", "**生成时间**：%s" % ts, "", "---", "",
         "## 一、本周变化", "",
         "| 条目 | 原来的理解 | 新证据／本人纠正 | 现在怎样改 | 哪条建议因此改变 |",
         "|---|---|---|---|---|"]

    revs = c.execute("select entity_type,entity_id,field,old_value,new_value,"
                     "changed_at,reason from revisions order by rev_id desc limit 20").fetchall()
    changed = [r for r in revs if r[5] and r[5][:7] == ts[:7]]
    if changed:
        for r in changed:
            # ★ 真的算出「哪条建议因此改变」，而不是写「见下」
            if r[0] == "self_claim":
                hit = [x[0] for x in _rec_rows(c, r[1])]
                impact = ("、".join("`%s`" % h for h in hit) if hit
                          else "（不支撑任何建议）")
            elif r[0] == "choice_episode":
                impact = "（选择记录 —— 供理解层引用）"
            elif r[0] == "learning_question":
                impact = "（问题台账 —— 影响看目标理解）"
            else:
                impact = "—"
            t.append("| `%s` / %s | %s | %s | %s | %s |" % (
                r[1], r[2], r[3] or "—", r[4] or "—", r[6] or "—", impact))
    else:
        t.append("| — | — | — | — | — |")
        t += ["", "> **本周期暂无变化** —— 首轮建库，基线已建立；等**你补第一条选择理由**后，这里会出现第一行。"]
    t += ["", "## 一·补、★ 依赖链快照", "",
          "> 完整版见 [[建议与依赖链]]。这里只列**当前依赖不稳、需要重审**的建议。", "",
          "| 建议 | 依赖不稳的条数 | 不稳的是哪几条 |", "|---|---:|---|"]
    _recs_all = c.execute("select rec_id,title from recommendations order by rec_id").fetchall()
    _warn = 0
    for rid, title in _recs_all:
        bad, tot = _rec_health(c, rid)
        if bad:
            _warn += 1
            t.append("| `%s` %s | %d / %d | %s |" % (
                rid, title, len(bad), tot,
                "、".join("`%s`" % b[0] for b in bad)))
    if not _warn:
        t.append("| （无 —— 全部建议的依赖都稳定） | | |")
    t += ["", "## 二、仍然未知", ""]
    unk = c.execute("select claim_id,statement from self_claims where "
                    "uncertainty_basis is not null and trim(uncertainty_basis)<>'' "
                    "order by claim_id").fetchall()
    for u in unk:
        t.append("- `%s` %s" % (u[0], u[1]))
    if not unk:
        t.append("- （无）")
    t += ["", "## 三、继续保留的其他解释", ""]
    alt = c.execute("select claim_id,statement from self_claims where "
                    "claim_type='mechanism' order by claim_id").fetchall()
    for a in alt:
        t.append("- `%s` %s" % (a[0], a[1]))
    if not alt:
        t.append("- （无）")
    t += ["", "## 四、本周只挑少量值得补的问题", "",
          "| 问题 | 为什么会改变建议 | 已经有的答案 | 这次再问的原因 |",
          "|---|---|---|---|"]
    qs = c.execute("select question_id,title,disagreement,prior_answer,why_reask "
                   "from learning_questions where status in ('proposed','asked','deferred') "
                   "and decision_impact='high' order by question_id").fetchall()
    for q in qs:
        t.append("| %s | %s | %s | %s |" % (q[1], q[2] or "—", q[3] or "（无）", q[4] or "—"))
    if not qs:
        t.append("| （无） | | | |")
    t += ["", "---", "",
          "*由 `tools/selfmodel.py render` 自动生成*"]
    written.append((os.path.join(VIEW_DIR, "本周理解变化.md"), _w(
        os.path.join(VIEW_DIR, "本周理解变化.md"), "\n".join(t) + "\n")))

    # ---------- 视图 3：我的选择与理由
    ec = [x[1] for x in c.execute("pragma table_info(choice_episodes)")]
    eps = [dict(zip(ec, r)) for r in c.execute(
        "select * from choice_episodes order by coalesce(time,'') desc")]
    filled = sum(1 for e in eps if (e.get("reasons_verbatim") or "").strip())
    t = ["---", "tags: [自我模型, 选择, 理由]", "created: 2026-10-10",
         "updated: %s" % ts[:10], "---", "", "# ✍️ 我的选择与理由", "",
         "> **★ 这是整个系统里最有价值的新数据。**",
         "> 聊天记录只记「**你做了什么**」；这一页补的是「**你为什么这样选、当时有什么条件**」——",
         "> 而这恰恰是**从行为里推不出来**的部分。",
         "",
         "[[系统当前怎样理解我]] ｜ [[本周理解变化]] ｜ [[值得继续问的问题]]",
         "", "**生成时间**：%s ｜ **已记录 %d 个选择 ｜ 你已填理由的 %d 个**" % (
             ts, len(eps), filled),
         "", "---", "",
         "## ★ 最简写法：先写三行就够", "",
         "```text",
         "这次我选择了：",
         "我自己的理由是：",
         "结果／现在还缺的是：",
         "```",
         "",
         "> 其余字段（当时有哪些选项、什么条件限制、是否仍会这样选）**由系统从已有资料补**，",
         "> 你只补**理由**和**遗漏的条件**。不知道的就留空 —— **留空比编造好**。",
         "", "---", "",
         "## 待补理由的选择（按时间倒序）", ""]

    for e in eps:
        t += ["### `%s` %s" % (e["episode_id"], e.get("time") or ""), "",
              "**面对的问题**：%s" % (e.get("question") or "—"), ""]
        if e.get("context"):
            t.append("**系统补的背景**：%s" % e["context"])
        if e.get("known_options"):
            t.append("")
            t.append("**已知选项**：%s" % e["known_options"])
        if e.get("constraints"):
            t.append("")
            t.append("**已知限制**：%s" % e["constraints"])
        t.append("")
        t.append("| 字段 | 内容 |")
        t.append("|---|---|")
        t.append("| 实际选择 | %s |" % (e.get("actual_choice") or "⬜ **待你填**"))
        t.append("| **本人理由（原话）** | %s |" % (
            ("**" + e["reasons_verbatim"] + "**") if (e.get("reasons_verbatim") or "").strip()
            else "⬜ **待你填** —— 这是最关键的一格"))
        inf = _j(e.get("reasons_inferred"))
        t.append("| 系统候选原因（**未确认**） | %s |" % (
            " · ".join(inf) if inf else "—"))
        t.append("| 当时预期 | %s |" % (e.get("expected") or "—"))
        t.append("| 阶段 | %s |" % STAGE_CN.get(e.get("delivery_stage"), "—"))
        t.append("| 实际结果 | %s |" % (e.get("outcome") or "—"))
        t.append("| 是否仍会这样选 | %s |" % (e.get("user_reassessment") or "⬜ 待你填"))
        t.append("")
        if e.get("source_refs"):
            t.append("> 出处：%s" % e["source_refs"])
            t.append("")

    _ep_items = []
    for e in eps:
        if not (e.get("reasons_verbatim") or "").strip():
            _ep_items.append((e["episode_id"],
                              ["理由: ", "实际选择: ", "仍会这样选: "],
                              {k: (e.get(k) or "") for k in
                               ("reasons_verbatim", "actual_choice",
                                "user_reassessment", "outcome", "new_discovery")}))
    t += ["---", "", "## ⚠️ 红线", "",
          "1. **本人理由用原话**，系统推测**另列**，两者**不得混写**。",
          "2. **未发生的行动不写成已执行** —— 阶段字段要如实。",
          "3. **不得**把「可行选项」写成「他想要的」—— 能做 ≠ 想做。",
          "4. 本页含私密内容，**不得外传**。", "",
          "---", "", "## ✍️ 手填区 · 补上你的理由", "",
          "> **先填 `理由` 这一行就够** —— 它是唯一无法从行为里推出来的那一格（%d 条待补）。" % len(_ep_items),
          ""]
    t += _zone_lines(os.path.join(VIEW_DIR, "我的选择与理由.md"), _ep_items)
    t += ["", "---", "", "*由 `tools/selfmodel.py render` 自动生成*"]
    written.append((os.path.join(VIEW_DIR, "我的选择与理由.md"), _w(
        os.path.join(VIEW_DIR, "我的选择与理由.md"), "\n".join(t) + "\n")))

    # ---------- 视图 4：值得继续问的问题
    lc = [x[1] for x in c.execute("pragma table_info(learning_questions)")]
    lqs = [dict(zip(lc, r)) for r in c.execute(
        "select * from learning_questions order by case decision_impact "
        "when 'high' then 0 when 'medium' then 1 else 2 end, question_id")]
    t = ["---", "tags: [自我模型, 提问, 信息缺口]", "created: 2026-10-10",
         "updated: %s" % ts[:10], "---", "", "# ❓ 值得继续问的问题", "",
         "> **原则：少问，但问到会改变建议的地方。**",
         "> 排序看三件事：**影响当前决策的程度** · **解释之间的分歧** · **你回答的难度**。",
         "> 已经答过的带原答案；**只有情境变了或有新证据冲突才再问**。",
         "> 允许答「都重要」「取决于条件」「暂时不答」。",
         "",
         "[[系统当前怎样理解我]] ｜ [[我的选择与理由]] ｜ [[本周理解变化]] ｜ [[信息需求单_20261009]]",
         "", "**生成时间**：%s ｜ **待问 %d ｜ 已答 %d**" % (
             ts, sum(1 for q in lqs if q["status"] in ("proposed", "asked", "deferred")),
             sum(1 for q in lqs if q["status"] == "answered")),
         "", "---", ""]

    for impact in ("high", "medium", "low"):
        sel = [q for q in lqs if q["decision_impact"] == impact]
        if not sel:
            continue
        t += ["## %s 影响度（%d 条）" % (IMPACT_CN[impact], len(sel)), "",
              "| ID | 问题 | 为什么会改变建议 | 已有答案 | 再问的原因 | 难度 | 状态 |",
              "|---|---|---|---|---|---|---|"]
        for q in sel:
            t.append("| `%s` | %s | %s | %s | %s | %s | %s |" % (
                q["question_id"], q["title"], q["disagreement"] or "—",
                q["prior_answer"] or "（无）", q["why_reask"] or "—",
                {"easy": "易", "medium": "中", "hard": "难"}.get(
                    q["answer_difficulty"], "—"),
                QSTATUS_CN.get(q["status"], q["status"])))
        t.append("")

    answered = [q for q in lqs if q["status"] == "answered"]
    if answered:
        t += ["## ✅ 已答（不再重复问）", "",
              "| ID | 问题 | 你的原话 | 时间 | 因此修订了什么 |",
              "|---|---|---|---|---|"]
        for q in answered:
            t.append("| `%s` | %s | %s | %s | %s |" % (
                q["question_id"], q["title"], q["answer_verbatim"] or "—",
                q["answer_time"] or "—", q["resolution"] or "—"))
        t.append("")

    _q_items = [(q["question_id"], ["回答: "],
                 {"answer_verbatim": q["answer_verbatim"] or "",
                  "resolution": q["resolution"] or ""})
                for q in lqs if q["status"] != "answered"]
    t += ["---", "",
          "> **本页与 [[信息需求单_20261009]] 的关系**：本页是**系统侧的缺口台账**（可自动生成、可排序）；",
          "> 信息需求单是**人侧的确认单**（唯一入口）。**待问的高影响项要同步进信息需求单**。",
          "", "---", "", "## ✍️ 手填区 · 我的回答", "",
          "> 只列**尚未回答**的问题（%d 条）；不确定的可以写「暂时不答」或「取决于条件」。" % len(_q_items),
          ""]
    t += _zone_lines(os.path.join(VIEW_DIR, "值得继续问的问题.md"), _q_items)
    t += ["", "---", "", "*由 `tools/selfmodel.py render` 自动生成*"]
    written.append((os.path.join(VIEW_DIR, "值得继续问的问题.md"), _w(
        os.path.join(VIEW_DIR, "值得继续问的问题.md"), "\n".join(t) + "\n")))

    # ---------- 视图 5：建议与依赖链（方案 update_protocol step 6–8）
    recs = c.execute("select rec_id,title,body,topic,status,coalesce(impact_if_wrong,'') "
                     "from recommendations order by rec_id").fetchall()
    n_dep = c.execute("select count(*) from rec_deps").fetchone()[0]
    orphan = c.execute("select claim_id,statement from self_claims where claim_id not in "
                       "(select distinct claim_id from rec_deps) order by claim_id").fetchall()
    t = ["---", "tags: [自我模型, 建议, 依赖链]", "created: 2026-10-10",
         "updated: %s" % ts[:10], "owner: 蔡浩文", "---", "",
         "# 🔗 建议与依赖链", "",
         "> **这一页回答的是**：「系统给我的每条建议，**建立在哪些理解之上**？」",
         "> 于是当你**纠正一条理解**时，系统能直接说出**哪条建议要跟着改** —— 而不是继续拿旧建议给你。",
         "",
         "[[系统当前怎样理解我]] ｜ [[本周理解变化]] ｜ [[我的选择与理由]] ｜ [[值得继续问的问题]]",
         "",
         "**生成时间**：%s ｜ **建议 %d 条 · 依赖关系 %d 条 · 不支撑任何建议的理解 %d 条**"
         % (ts, len(recs), n_dep, len(orphan)),
         "", "---", "",
         "## 一、建议清单", ""]

    warn = 0
    for rid, title, body, topic, status, iw in recs:
        bad, tot = _rec_health(c, rid)
        if bad:
            warn += 1
        flag = ("⚠️ **%d/%d 条依赖不稳 → 需重审**" % (len(bad), tot)) if bad \
            else ("✅ %d 条依赖稳定" % tot)
        t += ["### %s · %s" % (rid, title), "",
              "- **领域**：%s ｜ **状态**：%s ｜ **依赖健康**：%s"
              % (topic or "—", REC_STATUS_CN.get(status, status), flag)]
        if body:
            t += ["- **内容**：%s" % body]
        if iw:
            t += ["- **如果所依赖的理解错了**：%s" % iw]
        deps = c.execute(
            "select d.claim_id,d.dep_kind,coalesce(d.note,''),c.statement,"
            "c.epistemic_status,c.human_review from rec_deps d "
            "join self_claims c on c.claim_id=d.claim_id where d.rec_id=? "
            "order by d.claim_id", (rid,)).fetchall()
        t += ["", "| 依赖的理解 | 方式 | 该理解现状 | 认识状态 | 我的判断 |",
              "|---|---|---|---|---|"]
        for cid, kind, note, stmt, ep, hr in deps:
            unstable = ep in UNSTABLE_EPISTEMIC or hr in UNSTABLE_REVIEW
            t.append("| `%s` | %s | %s | %s | %s |" % (
                cid, DEP_KIND_CN.get(kind, kind), (note or "—")[:26],
                EPISTEMIC_CN.get(ep, ep),
                ("⚠️ " if unstable else "") + REVIEW_CN.get(hr, hr)))
        t.append("")

    t += ["---", "", "## 二、目前不支撑任何建议的理解（%d 条）" % len(orphan), "",
          "> 这些理解**纠正了也不会改变任何建议** —— 要么是背景事实，要么说明**还缺一条建议把它用起来**。", ""]
    for cid, stmt in orphan:
        t.append("- `%s` %s" % (cid, stmt))
    if not orphan:
        t.append("- （无）")

    t += ["", "---", "", "## 三、★ 纠正会改变建议 —— 怎么用这一页", "",
          "```text",
          "① 在 [[系统当前怎样理解我]] 的「我的判断」栏写：认可 / 需要修正 / 不认同 / 不适用于这件事",
          "② 跑：python tools/selfmodel.py review <claim_id> corrected \"你的原话\"",
          "   → 系统会立刻列出「因此需要重审的建议」",
          "③ 跑：python tools/selfmodel.py impact <claim_id>   看完整依赖链",
          "④ 跑：python tools/selfmodel.py render              本页刷新为最新状态",
          "```", "",
          "**自检**：`python tools/selfmodel.py verify` —— 在数据库副本上验证「纠正 → 建议改变」是否成立。", "",
          "---", "",
          "## ⚠️ 本页红线", "",
          "1. **建议不得比它依赖的理解更确定** —— 依赖不稳的建议必须标红，不得照常给出。",
          "2. **纠正一条理解 ≠ 自动改掉建议** —— 系统只**标出需要重审**，改不改由本人定。",
          "3. **不得为了让建议好看而删掉反例或未知项**。",
          "4. 本页含私密内容，**不得外传**。", "",
          "---", "",
          "*由 `tools/selfmodel.py render` 自动生成 · 设计依据：《自我理解系统深化_20261010》update_protocol step 6–8*"]
    written.append((os.path.join(VIEW_DIR, "建议与依赖链.md"), _w(
        os.path.join(VIEW_DIR, "建议与依赖链.md"), "\n".join(t) + "\n")))

    # ---------- 视图 6：理解判断与校准
    preds = c.execute(
        "select pred_id,created_at,question,horizon,predicted_choice,predicted_reason,"
        "basis_claims,alt_choices,confidence,linked_rec_id,actual_choice,actual_reason,"
        "match_status,match_by,mismatch_note,outcome,outcome_verdict,outcome_note "
        "from predictions order by created_at desc, pred_id").fetchall()
    pending = [p for p in preds if p[12] == "pending"]
    settled = [p for p in preds if p[12] != "pending"]
    t = ["---", "tags: [自我模型, 理解判断, 校准]", "created: 2026-10-11",
         "updated: %s" % ts[:10], "owner: 蔡浩文", "status: 首轮基线", "---", "",
         "# 🎯 理解判断与校准", "",
         "> **这一页只回答第一件事**：系统**推测你会怎么选** —— 不是「我建议你怎样」。",
         "> 第二件（我建议你怎样 + 代价）在 [[建议与依赖链]]。",
         "> **你的实际选择 / 理由 / 最终结果**回填后 → 系统校准对你的理解，并回流到建议。", "",
         "[[🏠主页]] ｜ [[系统当前怎样理解我]] ｜ [[我的选择与理由]] ｜ [[建议与依赖链]] ｜ [[本周理解变化]]", "",
         "**生成时间**：%s ｜ **预测 %d 条**（待结算 %d · 已结算 %d）"
         % (ts, len(preds), len(pending), len(settled)),
         "", "---", "", "## 一、待结算（等实际发生）", ""]
    if not pending:
        t.append("- （无）")
    for p in pending:
        basis = "、".join("`%s`" % b.strip() for b in (p[6] or "").split(",") if b.strip()) or "—"
        t += ["### %s%s" % (p[0], (" · 窗口 " + p[3]) if p[3] else ""), "",
              "- **问题**：%s" % (p[2] or ""),
              "- **系统推测他会选**：%s" % (p[4] or "—"),
              "- **推测依据**：%s" % (p[5] or "—"),
              "- **依据条目**：%s" % basis,
              "- **置信度**：%s" % PRED_CONF_CN.get(p[8], p[8]),
              "- **其他可能**：%s" % (p[7] or "—"),
              "- **关联建议**：%s" % (p[9] or "—"), ""]
    t += ["---", "", "## 二、已结算（校准依据）", ""]
    if not settled:
        t.append("- （无）")
    for p in settled:
        t += ["### %s · %s" % (p[0], PRED_MATCH_CN.get(p[12], p[12])), "",
              "- **问题**：%s" % (p[2] or ""),
              "- **系统推测**：%s" % (p[4] or "—"),
              "- **实际选择**：%s" % (p[10] or "—"),
              "- **他的理由**：%s" % (p[11] or "—— 空（系统未代填）"),
              "- **判定**：%s（%s）" % (PRED_MATCH_CN.get(p[12], p[12]),
                                      "人工" if p[13] == "human" else "系统粗判")]
        if p[14]:
            t.append("- **不一致在哪**：%s" % p[14])
        if p[16]:
            t.append("- **最终结果**：%s（%s）"
                     % (PRED_VERDICT_CN.get(p[16], p[16]), p[17] or "—"))
        t.append("")
    cnt = {}
    for p in settled:
        cnt[p[12]] = cnt.get(p[12], 0) + 1
    t += ["---", "", "## 三、校准小结", ""]
    if settled:
        ok = cnt.get("matched", 0)
        t.append("- 已结算 **%d** 条 → 一致 **%d** · 部分一致 **%d** · 不一致 **%d**（命中率 **%.0f%%**）"
                  % (len(settled), ok, cnt.get("partial", 0), cnt.get("mismatched", 0),
                     100.0 * ok / len(settled)))
    else:
        t.append("- 尚无已结算预测 —— 校准要等「实际选择」回填后才开始。")
    t += ["", "---", "", "## 四、怎么用", "",
          "```text",
          "① 系统对某次待决问题给出推测：",
          "   python tools/selfmodel.py predict add P-XXXX \"问题\" \"推测的选择\" --basis SC-XXX",
          "② 你实际做了选择后回填（会列出「哪条依据需要复核」）：",
          "   python tools/selfmodel.py predict resolve P-XXXX \"实际选择\" \"你的理由\"",
          "③ 结果出来后记录（会提示关联建议该保留还是撤回）：",
          "   python tools/selfmodel.py predict outcome P-XXXX worked|failed|mixed \"说明\"",
          "④ 看系统整体准不准：python tools/selfmodel.py calibrate",
          "```", "",
          "---", "", "## ⚠️ 本页红线", "",
          "1. **推测 ≠ 建议** —— 这一页是「我猜你会怎样」，不是「我希望你怎样」，两者不得混写。",
          "2. **实际选择与本人理由必须回填后才算校准** —— 不得用系统推测冒充本人理由。",
          "3. **命中率低不等于模型错** —— 也可能是「他这次改变了」，两者要分开判断。",
          "4. 本页含私密内容，**不得外传**。", "",
          "---", "",
          "*由 `tools/selfmodel.py render` 自动生成 · 设计依据：《长期个性化智能体》第三节「同时回答两件事」*"]
    written.append((os.path.join(VIEW_DIR, "理解判断与校准.md"), _w(
        os.path.join(VIEW_DIR, "理解判断与校准.md"), "\n".join(t) + "\n")))

    # ---------- 回写 understanding_views 表
    c2 = conn(write=True)
    for vid, topic, path in (("VW-SELF", "整体", "系统当前怎样理解我.md"),
                             ("VW-CHANGES", "变更", "本周理解变化.md"),
                             ("VW-CHOICE", "选择", "我的选择与理由.md"),
                             ("VW-QUESTIONS", "提问", "值得继续问的问题.md"),
                             ("VW-RECS", "建议", "建议与依赖链.md"),
                             ("VW-PREDICT", "理解判断", "理解判断与校准.md")):
        c2.execute("""insert or replace into understanding_views(
            view_id,topic,current_question,current_model,applied_claims,
            source_coverage,changes_since_previous,alternatives,unknowns,
            stale,stale_reason,generated_at,version,prior_version,privacy_scope)
            values(?,?,?,?,?,?,?,?,?,0,NULL,?,1,NULL,'private')""", (
            vid, topic, "—", "见 Obsidian：06_自我模型/%s" % path,
            "self_claims", "analysis.sqlite · 见 meta", "见 本周理解变化.md",
            "见各条 mechanism 类条目", "见各条 uncertainty_basis", ts))
    c2.commit()
    c2.close()
    c.close()

    print("[render] 生成 %d 个视图 → %s" % (len(written), VIEW_DIR))
    for p, n in written:
        print("         %-24s %6d 字节" % (os.path.basename(p), n))


def cmd_stats():
    c = conn()
    print("=== self_claims ===")
    for r in c.execute("select claim_type,count(*) from self_claims group by 1 order by 1"):
        print("  %-14s %s" % (TYPE_CN.get(r[0], r[0]), r[1]))
    print("  %-14s %s" % ("合计", c.execute("select count(*) from self_claims").fetchone()[0]))
    print("=== 认识状态 ===")
    for r in c.execute("select epistemic_status,count(*) from self_claims group by 1 order by 2 desc"):
        print("  %-16s %s" % (EPISTEMIC_CN.get(r[0], r[0]), r[1]))
    print("=== 本人审核 ===")
    for r in c.execute("select human_review,count(*) from self_claims group by 1 order by 2 desc"):
        print("  %-16s %s" % (REVIEW_CN.get(r[0], r[0]), r[1]))
    n = c.execute("select count(*) from choice_episodes").fetchone()[0]
    f = c.execute("select count(*) from choice_episodes where trim(coalesce("
                  "reasons_verbatim,''))<>''").fetchone()[0]
    print("=== choice_episodes ===\n  合计 %d · 已填本人理由 %d" % (n, f))
    print("=== learning_questions ===")
    for r in c.execute("select status,count(*) from learning_questions group by 1 order by 2 desc"):
        print("  %-18s %s" % (QSTATUS_CN.get(r[0], r[0]), r[1]))
    print("=== claim_evidence ===\n  关联 %d 条" % c.execute(
        "select count(*) from claim_evidence").fetchone()[0])
    nrec = c.execute("select count(*) from recommendations").fetchone()[0]
    ndep = c.execute("select count(*) from rec_deps").fetchone()[0]
    orphan = c.execute(
        "select count(*) from self_claims where claim_id not in "
        "(select distinct claim_id from rec_deps)").fetchone()[0]
    print("=== 依赖链 ===\n  建议 %d 条 · 依赖关系 %d 条 · 不支撑任何建议的理解 %d 条"
          % (nrec, ndep, orphan))
    print("=== revisions（含本层）===")
    for r in c.execute("select entity_type,count(*) from revisions group by 1 order by 2 desc"):
        print("  %-16s %s" % (r[0], r[1]))
    c.close()


def cmd_list(what):
    c = conn()
    if what == "claims":
        for r in c.execute("select claim_id,claim_type,epistemic_status,"
                           "human_review,substr(statement,1,52) from self_claims "
                           "order by claim_type,claim_id"):
            print("%-16s %-12s %-18s %-12s %s" % r)
    elif what == "episodes":
        for r in c.execute("select episode_id,coalesce(time,''),delivery_stage,"
                           "case when trim(coalesce(reasons_verbatim,''))='' then '缺理由' "
                           "else '有理由' end,substr(coalesce(question,''),1,40) "
                           "from choice_episodes order by time desc"):
            print("%-24s %-12s %-12s %-6s %s" % r)
    elif what == "questions":
        for r in c.execute("select question_id,decision_impact,status,"
                           "substr(title,1,50) from learning_questions order by 2,1"):
            print("%-14s %-8s %-12s %s" % r)
    elif what == "views":
        for r in c.execute("select view_id,topic,version,stale,generated_at "
                           "from understanding_views"):
            print(r)
    elif what == "recs":
        for rid, st, tp, ti in c.execute(
                "select rec_id,status,coalesce(topic,''),title from recommendations "
                "order by rec_id"):
            print("%-14s %-10s %-10s %s" % (rid, st, tp, ti))
    else:
        print("用法：list claims|episodes|questions|views|recs")
    c.close()


def cmd_answer(qid, verbatim):
    c = conn(write=True)
    old = c.execute("select status,answer_verbatim from learning_questions where "
                    "question_id=?", (qid,)).fetchone()
    if not old:
        print("!! 未找到 %s" % qid)
        return
    c.execute("update learning_questions set status='answered',answer_verbatim=?,"
              "answer_time=?,updated_at=? where question_id=?",
              (verbatim, now(), now(), qid))
    log_revision(c, "learning_question", qid, "answer_verbatim",
                 old[1], verbatim, "本人作答")
    c.commit()
    print("[answer] %s ← %s" % (qid, verbatim))
    # ★ 依赖链：答完立刻指出这条答案会动到哪些建议
    tc = c.execute("select coalesce(target_claims,'') from learning_questions "
                   "where question_id=?", (qid,)).fetchone()
    if tc and tc[0].strip():
        print("  ★ 本问题针对的理解：%s" % tc[0])
        for cid in [x.strip() for x in tc[0].replace("，", ",").split(",") if x.strip()]:
            _report_impact(c, cid)
    c.close()
    print("         ★ 别忘了跑 render，并同步进 04_工作台\\信息需求单")


def cmd_review(cid, verdict, note=""):
    if verdict not in REVIEW_CN:
        print("!! verdict 必须是：%s" % " / ".join(REVIEW_CN))
        return
    c = conn(write=True)
    old = c.execute("select human_review,note from self_claims where claim_id=?",
                    (cid,)).fetchone()
    if not old:
        print("!! 未找到 %s" % cid)
        return
    newnote = (old[1] or "") + ("\n[%s] %s" % (now()[:10], note) if note else "")
    c.execute("update self_claims set human_review=?,note=?,revision=revision+1,"
              "updated_at=? where claim_id=?", (verdict, newnote.strip(), now(), cid))
    log_revision(c, "self_claim", cid, "human_review", old[0], verdict,
                 note or "本人审核")
    c.commit()
    print("[review] %s → %s %s" % (cid, REVIEW_CN[verdict], note))
    # ★ 依赖链：本人审核后立刻指出受影响的建议
    if verdict in UNSTABLE_REVIEW:
        _report_impact(c, cid)
    c.close()


def cmd_reassess(eid, text):
    c = conn(write=True)
    old = c.execute("select user_reassessment from choice_episodes where episode_id=?",
                    (eid,)).fetchone()
    if not old:
        print("!! 未找到 %s" % eid)
        return
    c.execute("update choice_episodes set user_reassessment=?,updated_at=? "
              "where episode_id=?", (text, now(), eid))
    log_revision(c, "choice_episode", eid, "user_reassessment", old[0], text, "本人复评")
    c.commit()
    c.close()
    print("[reassess] %s ← %s" % (eid, text))


def cmd_outcome(eid, stage, text=""):
    if stage not in STAGE_CN:
        print("!! stage 必须是：%s" % " / ".join(STAGE_CN))
        return
    c = conn(write=True)
    old = c.execute("select delivery_stage,outcome from choice_episodes where "
                    "episode_id=?", (eid,)).fetchone()
    if not old:
        print("!! 未找到 %s" % eid)
        return
    c.execute("update choice_episodes set delivery_stage=?,outcome=coalesce(nullif(?,''),"
              "outcome),updated_at=? where episode_id=?", (stage, text, now(), eid))
    log_revision(c, "choice_episode", eid, "delivery_stage", old[0], stage, text or "")
    c.commit()
    c.close()
    print("[outcome] %s → %s" % (eid, STAGE_CN[stage]))


def cmd_stale(vid, reason):
    c = conn(write=True)
    c.execute("update understanding_views set stale=1,stale_reason=?,generated_at=? "
              "where view_id=?", (reason, now(), vid))
    c.commit()
    c.close()
    print("[stale] %s ← %s" % (vid, reason))


def cmd_reason(eid, text):
    """补「本人理由（原话）」—— 方案里最关键的一格"""
    c = conn(write=True)
    old = c.execute("select reasons_verbatim from choice_episodes where episode_id=?",
                    (eid,)).fetchone()
    if not old:
        print("!! 未找到 %s" % eid)
        c.close()
        return
    c.execute("update choice_episodes set reasons_verbatim=?,updated_at=? where episode_id=?",
              (text, now(), eid))
    log_revision(c, "choice_episode", eid, "reasons_verbatim", old[0], text, "本人补理由")
    c.commit()
    c.close()
    print("[reason] %s ← %s" % (eid, text))
    print("         ★ 跑 render 刷新视图；这条理由会进 05 引擎与「本周理解变化」。")


# ==========================================================================
# 手填区回写：Obsidian → 数据库（方案 synchronization_gap 的修复）
# ==========================================================================

def _collect_sync_plan():
    """扫描三个视图的手填区 → (plans, bad)
    plans: [(entity, id, field, old, new, extra)]
    """
    plans, bad = [], []
    con = conn()

    # ---- 视图 3：我的选择与理由
    p3 = os.path.join(VIEW_DIR, "我的选择与理由.md")
    ep_cols = ["reasons_verbatim", "actual_choice", "user_reassessment",
               "outcome", "new_discovery"]
    for eid, kv in _parse_zone(_read_zone(p3)).items():
        row = con.execute("select %s from choice_episodes where episode_id=?"
                          % ",".join(ep_cols), (eid,)).fetchone()
        if row is None:
            bad.append("choice_episodes 里没有 %s" % eid)
            continue
        cur = dict(zip(ep_cols, [(x or "") for x in row]))
        for k, v in kv.items():
            f = ZONE_EP.get(k)
            if not f:
                bad.append("%s 字段「%s」不认识（可用：%s）"
                           % (eid, k, " / ".join(sorted(set(ZONE_EP)))))
                continue
            if v.strip() != cur[f].strip():
                plans.append(("choice_episode", eid, f, cur[f], v.strip(), None))

    # ---- 视图 4：值得继续问的问题
    p4 = os.path.join(VIEW_DIR, "值得继续问的问题.md")
    for qid, kv in _parse_zone(_read_zone(p4)).items():
        row = con.execute("select answer_verbatim,resolution,status from "
                          "learning_questions where question_id=?", (qid,)).fetchone()
        if row is None:
            bad.append("learning_questions 里没有 %s" % qid)
            continue
        av, res, _st = [(x or "") for x in row]
        for k, v in kv.items():
            f = ZONE_LQ.get(k)
            if not f:
                bad.append("%s 字段「%s」不认识（可用：%s）"
                           % (qid, k, " / ".join(sorted(set(ZONE_LQ)))))
                continue
            if f == "answer_verbatim":
                if v.strip() != av.strip():
                    plans.append(("learning_question", qid, "answer_verbatim",
                                  av, v.strip(), "answered"))
            elif v.strip() != res.strip():
                plans.append(("learning_question", qid, "resolution", res, v.strip(), None))

    # ---- 视图 1：系统当前怎样理解我
    p1 = os.path.join(VIEW_DIR, "系统当前怎样理解我.md")
    for cid, kv in _parse_zone(_read_zone(p1)).items():
        row = con.execute("select human_review,note from self_claims where claim_id=?",
                          (cid,)).fetchone()
        if row is None:
            bad.append("self_claims 里没有 %s" % cid)
            continue
        hr, note = [(x or "") for x in row]
        for k, v in kv.items():
            f = ZONE_CL.get(k)
            if not f:
                bad.append("%s 字段「%s」不认识（可用：%s）"
                           % (cid, k, " / ".join(sorted(set(ZONE_CL)))))
                continue
            if f == "human_review":
                nv = REVIEW_ALIAS.get(v.strip())
                if nv is None:
                    bad.append("%s 判断「%s」不合法（只能：认可 / 需要修正 / 不认同 / 不适用于这件事）"
                               % (cid, v))
                    continue
                if nv != hr:
                    plans.append(("self_claim", cid, "human_review", hr, nv, None))
            else:
                if v.strip() and v.strip() not in note:
                    plans.append(("self_claim", cid, "note", note,
                                  ((note + "\n") if note else "") + v.strip(), None))
    con.close()
    return plans, bad


def cmd_sync(apply=False, quiet=False):
    plans, bad = _collect_sync_plan()
    if not quiet:
        print("=" * 66)
        print("Obsidian 手填区 → 自我模型库   同步%s"
              % ("（真写）" if apply else "（只读预览）"))
        print("=" * 66)
        if not plans:
            print("  没有差异 —— 手填区和库里一致。")
        else:
            print("  发现 %d 处改动：" % len(plans))
            for ent, eid, f, old, new, _ in plans:
                print("    %-16s %-22s %-18s %r → %r"
                      % (ent, eid, f, (old or "")[:16], new[:26]))
        if bad:
            print()
            print("  ⚠️ %d 条跳过（字段不认识 / 值不合法 / 找不到对象）：" % len(bad))
            for b in bad[:20]:
                print("      " + b)

    if not apply:
        if not quiet:
            print()
            print("  （只读。要真写回：python tools\\selfmodel.py sync --apply）")
        return plans

    if not plans:
        return plans

    # ---- 备份 ----
    bdir = os.path.join(ROOT, "_tmp",
                        "_backup_db_" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(bdir, exist_ok=True)
    c0 = conn(write=True)
    c0.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    c0.close()
    for suf in ("", "-wal", "-shm"):
        src = DB + suf
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(bdir, os.path.basename(src)))

    # ---- 写入 ----
    c = conn(write=True)
    tbl_key = {"choice_episode": ("choice_episodes", "episode_id"),
               "learning_question": ("learning_questions", "question_id"),
               "self_claim": ("self_claims", "claim_id")}
    n, touched = 0, []
    for ent, eid, f, old, new, extra in plans:
        tbl, key = tbl_key[ent]
        sets, vals = ["%s=?" % f], [new]
        if ent == "learning_question" and extra == "answered":
            sets += ["status='answered'", "answer_time=?"]
            vals.append(now())
        if ent == "self_claim":
            sets.append("revision=revision+1")
        sets.append("updated_at=?")
        vals += [now(), eid]
        c.execute("update %s set %s where %s=?" % (tbl, ",".join(sets), key), vals)
        log_revision(c, ent, eid, f, old, new, "Obsidian 手填区")
        n += 1
        if ent == "self_claim" and f == "human_review":
            touched.append(eid)
    c.commit()
    c.close()

    if not quiet:
        print()
        print("  备份 → %s" % bdir)
        print("  ✅ 写回 %d 处，已记 revisions" % n)

    # ★ 依赖链：审核结论不稳的 → 立刻指出受影响的建议
    c = conn()
    for cid in touched:
        hr = c.execute("select human_review from self_claims where claim_id=?",
                       (cid,)).fetchone()
        if hr and hr[0] in UNSTABLE_REVIEW:
            _report_impact(c, cid)
    c.close()
    return plans


# ==========================================================================
# 依赖链：纠正一条理解 → 指出哪条建议因此改变
#   方案 01_数据结构与更新协议.json update_protocol step 6–8 +
#   proposed_pilot.completion_evidence「纠正能改变依赖它的建议」
# ==========================================================================

REC_STATUS_CN = {"active": "生效", "superseded": "已被替代", "withdrawn": "已撤回"}
DEP_KIND_CN = {"assumes": "假定", "requires": "需要", "informed_by": "依据"}
PRED_MATCH_CN = {"pending": "待结算", "matched": "一致", "partial": "部分一致",
                 "mismatched": "不一致"}
PRED_VERDICT_CN = {"worked": "有效", "failed": "无效", "mixed": "喜忧参半",
                   "unknown": "未知"}
PRED_CONF_CN = {"high": "高", "medium": "中", "low": "低"}

# 这些状态意味着「这条理解本身不稳」，依赖它的建议就该重审
UNSTABLE_EPISTEMIC = {"disputed", "withdrawn", "superseded", "needs_verification"}
UNSTABLE_REVIEW = {"corrected", "rejected", "not_applicable"}


def _rec_rows(c, claim_id):
    return c.execute(
        "select r.rec_id, r.title, r.status, d.dep_kind, coalesce(d.note,'') "
        "from rec_deps d join recommendations r on r.rec_id = d.rec_id "
        "where d.claim_id = ? order by r.rec_id", (claim_id,)).fetchall()


def _claim_state(c, claim_id):
    return c.execute(
        "select statement, claim_type, epistemic_status, human_review, "
        "coalesce(conditions,''), coalesce(excluded_contexts,''), "
        "coalesce(counterevidence,''), coalesce(uncertainty_basis,''), "
        "coalesce(valid_from,''), coalesce(valid_to,''), revision "
        "from self_claims where claim_id = ?", (claim_id,)).fetchone()


def _rec_health(c, rec_id):
    """一条建议的依赖健康度：返回 (不稳的理解列表, 总依赖数)"""
    deps = c.execute(
        "select c.claim_id, c.epistemic_status, c.human_review, c.statement "
        "from rec_deps d join self_claims c on c.claim_id = d.claim_id "
        "where d.rec_id = ?", (rec_id,)).fetchall()
    bad = [d for d in deps
           if d[1] in UNSTABLE_EPISTEMIC or d[2] in UNSTABLE_REVIEW]
    return bad, len(deps)


def cmd_recimport(path):
    """批量导入建议与依赖关系（只增不改）"""
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    c = conn(write=True)
    n_rec = n_dep = 0
    for r in data.get("recommendations", []):
        rid = r["rec_id"]
        exist = c.execute("select 1 from recommendations where rec_id=?",
                          (rid,)).fetchone()
        if exist:
            c.execute("update recommendations set title=?,body=?,topic=?,status=?,"
                      "impact_if_wrong=?,updated_at=? where rec_id=?",
                      (r.get("title", ""), r.get("body", ""), r.get("topic", ""),
                       r.get("status", "active"), r.get("impact_if_wrong", ""),
                       now(), rid))
        else:
            c.execute("insert into recommendations(rec_id,title,body,topic,status,"
                      "impact_if_wrong,created_at,updated_at) values(?,?,?,?,?,?,?,?)",
                      (rid, r.get("title", ""), r.get("body", ""), r.get("topic", ""),
                       r.get("status", "active"), r.get("impact_if_wrong", ""),
                       now(), now()))
        n_rec += 1
        for d in r.get("depends_on", []):
            cid = d["claim_id"] if isinstance(d, dict) else d
            kind = d.get("dep_kind", "assumes") if isinstance(d, dict) else "assumes"
            note = d.get("note", "") if isinstance(d, dict) else ""
            has = c.execute("select 1 from rec_deps where rec_id=? and claim_id=?",
                            (rid, cid)).fetchone()
            if has:
                c.execute("update rec_deps set dep_kind=?,note=? where rec_id=? "
                          "and claim_id=?", (kind, note, rid, cid))
            else:
                c.execute("insert into rec_deps(rec_id,claim_id,dep_kind,note,"
                          "created_at) values(?,?,?,?,?)", (rid, cid, kind, note, now()))
            n_dep += 1
    log_revision(c, "selfmodel", os.path.basename(path), "recimport",
                 "", "%d 建议 / %d 依赖" % (n_rec, n_dep), "导入建议与依赖链")
    c.commit()
    c.close()
    print("[recimport] %d 条建议 · %d 条依赖关系 ← %s" % (n_rec, n_dep, path))


def cmd_rec(sub, *rest):
    c = conn(write=True) if sub in ("add",) else conn()
    if sub == "list":
        rows = c.execute("select rec_id,status,topic,title from recommendations "
                         "order by rec_id").fetchall()
        print("=== 建议 %d 条 ===" % len(rows))
        for rid, st, tp, ti in rows:
            bad, tot = _rec_health(c, rid)
            flag = "⚠️ %d/%d 依赖不稳" % (len(bad), tot) if bad else "✅ %d 依赖" % tot
            print("  %-14s [%s] %-10s %-8s %s" % (rid, REC_STATUS_CN.get(st, st),
                                                  tp or "", flag, ti))
    elif sub == "add":
        rid, title = rest[0], rest[1]
        body = rest[2] if len(rest) > 2 else ""
        c.execute("insert or replace into recommendations(rec_id,title,body,topic,"
                  "status,created_at,updated_at) values(?,?,?,'','active',?,?)",
                  (rid, title, body, now(), now()))
        c.commit()
        print("[rec add] %s ← %s" % (rid, title))
    else:
        print("用法：rec list | rec add <rec_id> \"标题\" [\"正文\"]")
    c.close()


def cmd_link(claim_id, rec_id, note=""):
    if not _claim_state(conn(), claim_id):
        print("!! 未找到理解 %s" % claim_id)
        return
    c = conn(write=True)
    if not c.execute("select 1 from recommendations where rec_id=?", (rec_id,)).fetchone():
        print("!! 未找到建议 %s（先 rec add 或 recimport）" % rec_id)
        c.close()
        return
    c.execute("insert or replace into rec_deps(rec_id,claim_id,dep_kind,note,created_at)"
              " values(?,?,'assumes',?,?)", (rec_id, claim_id, note, now()))
    log_revision(c, "rec_dep", "%s→%s" % (claim_id, rec_id), "link", "", note,
                 "建立依赖")
    c.commit()
    c.close()
    print("[link] %s → %s  %s" % (claim_id, rec_id, note))


def cmd_impact(claim_id=None, show_all=False):
    c = conn()
    if show_all:
        rows = c.execute("select rec_id,title,status,topic from recommendations "
                         "order by rec_id").fetchall()
        print("=== 依赖链体检：%d 条建议 ===" % len(rows))
        warn = 0
        for rid, title, st, tp in rows:
            bad, tot = _rec_health(c, rid)
            if bad:
                warn += 1
                print("\n⚠️  %s  [%s] %s" % (rid, REC_STATUS_CN.get(st, st), title))
                print("    依赖 %d 条，其中 %d 条不稳：" % (tot, len(bad)))
                for bid, ep, hr, stmt in bad:
                    print("      · %-16s %s / %s — %s"
                          % (bid, EPISTEMIC_CN.get(ep, ep),
                             REVIEW_CN.get(hr, hr), stmt[:44]))
            else:
                print("  ✅ %-14s %s" % (rid, title))
        print("\n结论：%d/%d 条建议存在不稳依赖 → 需重审" % (warn, len(rows)))
        c.close()
        return

    st = _claim_state(c, claim_id)
    if not st:
        print("!! 未找到理解 %s" % claim_id)
        return
    stmt, ctype, ep, hr, cond, excl, ctr, unc, vf, vt, rev = st
    print("=== %s ===" % claim_id)
    print("  %s" % stmt)
    print("  类型：%s · 认识状态：%s · 本人审核：%s · 版本 v%d"
          % (TYPE_CN.get(ctype, ctype), EPISTEMIC_CN.get(ep, ep),
             REVIEW_CN.get(hr, hr), rev))
    if cond:
        print("  适用条件：%s" % cond)
    if excl:
        print("  不能扩展：%s" % excl)
    if ctr:
        print("  反例：%s" % ctr)
    if unc:
        print("  未知：%s" % unc)
    unstable = ep in UNSTABLE_EPISTEMIC or hr in UNSTABLE_REVIEW
    recs = _rec_rows(c, claim_id)
    print("\n  ── 依赖这条理解的建议 %d 条 ──" % len(recs))
    if not recs:
        print("  （无。→ 说明这条理解目前不影响任何建议，纠正它不会改变系统行为）")
    for rid, title, rst, kind, note in recs:
        mark = "⚠️ 需重审" if unstable else "✅ 暂不受影响"
        print("  %s %-14s [%s] %s" % (mark, rid, REC_STATUS_CN.get(rst, rst), title))
        if note:
            print("        依赖方式：%s · %s" % (DEP_KIND_CN.get(kind, kind), note))
    c.close()


def cmd_brief(topic):
    """read_understanding：按当前问题返回阅读包（方案 future_reading_interface）"""
    c = conn()
    like = "%" + topic + "%"
    print("=" * 66)
    print("阅读包 · 问题关键词「%s」" % topic)
    print("=" * 66)

    views = c.execute(
        "select view_id,topic,current_question,current_model,unknowns,stale,"
        "coalesce(stale_reason,''),version,generated_at from understanding_views "
        "where topic like ? or current_question like ? or current_model like ?",
        (like, like, like)).fetchall()
    print("\n【相关视图 %d 个】" % len(views))
    for vid, tp, q, model, unk, stale, sr, ver, gen in views:
        print("  · %s（%s · v%s · %s）%s" % (vid, tp, ver, gen,
                                            "  ⚠️ 已陈旧：" + sr if stale else ""))
        print("    问题：%s" % (q or "")[:80])
        print("    当前模型：%s" % (model or "")[:110])

    claims = c.execute(
        "select claim_id,claim_type,statement,epistemic_status,human_review,"
        "coalesce(conditions,''),coalesce(excluded_contexts,''),"
        "coalesce(counterevidence,''),coalesce(uncertainty_basis,'') "
        "from self_claims where statement like ? or coalesce(conditions,'') like ? "
        "or coalesce(excluded_contexts,'') like ? or coalesce(domain,'') like ? "
        "or coalesce(project_id,'') like ? order by claim_type,claim_id",
        (like, like, like, like, like)).fetchall()
    print("\n【相关理解 %d 条】" % len(claims))
    for cid, ctype, stmt, ep, hr, cond, excl, ctr, unc in claims:
        print("\n  %s  [%s · %s · %s]" % (cid, TYPE_CN.get(ctype, ctype),
                                          EPISTEMIC_CN.get(ep, ep), REVIEW_CN.get(hr, hr)))
        print("    %s" % stmt)
        if cond:
            print("    适用：%s" % cond)
        if excl:
            print("    ✗ 不能扩展：%s" % excl)
        if ctr:
            print("    ⚠️ 反例：%s" % ctr)
        if unc:
            print("    ? 未知：%s" % unc)
        ev = c.execute("select quote,speaker,event_time,relation,link_status "
                       "from claim_evidence where claim_id=? order by event_time",
                       (cid,)).fetchall()
        for q, sp, et, rel, ls in ev:
            print("    依据[%s] %s %s：%s" % (rel or "", et or "", sp or "", (q or "")[:70]))
        recs = _rec_rows(c, cid)
        for rid, title, rst, kind, note in recs:
            print("    → 影响建议 %s %s" % (rid, title))

    eps = c.execute(
        "select episode_id,time,question,actual_choice,reasons_verbatim,"
        "reasons_inferred,user_reassessment from choice_episodes "
        "where question like ? or coalesce(context,'') like ? "
        "or coalesce(actual_choice,'') like ? order by time desc",
        (like, like, like)).fetchall()
    print("\n【相关真实选择 %d 个】" % len(eps))
    for eid, t, q, ch, rv, ri, ra in eps:
        print("\n  %s（%s）" % (eid, t or ""))
        print("    选择：%s" % (q or "")[:80])
        print("    实际：%s" % (ch or "")[:80])
        print("    本人理由：%s" % (rv if (rv and rv.strip()) else "—— 空（系统未代填）"))
        if ri:
            print("    系统候选原因：%s" % (ri or "")[:100])
        if ra:
            print("    本人复评：%s" % (ra or "")[:100])

    preds = c.execute(
        "select pred_id,question,predicted_choice,actual_choice,match_status,"
        "basis_claims,confidence from predictions "
        "where question like ? or coalesce(topic,'') like ? "
        "or coalesce(predicted_choice,'') like ? order by created_at desc",
        (like, like, like)).fetchall()
    if preds:
        print("\n【相关理解判断（系统推测你会怎么选）%d 条】" % len(preds))
        for pid, q, pc, ac, ms, basis, conf in preds:
            print("\n  %s [%s · 置信%s]" % (pid, PRED_MATCH_CN.get(ms, ms),
                                           PRED_CONF_CN.get(conf, conf)))
            print("    问题：%s" % (q or "")[:80])
            print("    系统推测：%s" % (pc or "")[:90])
            if ac:
                print("    实际：%s" % (ac or "")[:90])
            if basis:
                print("    依据：%s" % basis)

    qs = c.execute("select question_id,decision_impact,title,status,disagreement "
                   "from learning_questions where title like ? or coalesce(disagreement,'') like ?",
                   (like, like)).fetchall()
    if qs:
        print("\n【待问的问题 %d 个】" % len(qs))
        for qid, im, ti, st, dis in qs:
            print("  %s [%s · %s] %s" % (qid, IMPACT_CN.get(im, im),
                                         QSTATUS_CN.get(st, st), ti))
            if dis:
                print("      为什么会改变建议：%s" % dis[:100])
    c.close()


def cmd_changes(since=None):
    """list_changes：返回指定版本以来的理解变化与受影响的建议"""
    c = conn()
    where = "entity_type in ('self_claim','choice_episode','learning_question',"\
            "'understanding_view','rec_dep','selfmodel','recommendation')"
    args = []
    if since:
        where += " and changed_at >= ?"
        args.append(since)
    rows = c.execute(
        "select changed_at,entity_type,entity_id,field,coalesce(new_value,''),"
        "coalesce(reason,'') from revisions where %s order by changed_at desc" % where,
        args).fetchall()
    print("=" * 66)
    print("理解变化清单%s · 共 %d 条" % ("（%s 起）" % since if since else "（全部）", len(rows)))
    print("=" * 66)
    if not rows:
        print("\n（无变化记录。→ 首轮建库后尚无新证据或本人纠正进入。）")
    touched = set()
    for at, et, eid, field, newv, reason in rows:
        print("\n%s  [%s] %s" % (at, et, eid))
        print("  字段 %s → %s" % (field, (newv or "")[:110]))
        if reason:
            print("  原因：%s" % (reason or "")[:110])
        if et == "self_claim":
            touched.add(eid)
    if touched:
        print("\n" + "-" * 66)
        print("★ 因上述理解变化而需要重审的建议：")
        any_hit = False
        for cid in sorted(touched):
            for rid, title, rst, kind, note in _rec_rows(c, cid):
                any_hit = True
                print("  %s ← %s（%s）" % (rid, cid, title))
        if not any_hit:
            print("  （无 —— 这些理解目前不支撑任何建议）")
    c.close()


def _report_impact(c, claim_id, prefix="  "):
    """review/answer 后自动提示受影响的建议"""
    recs = _rec_rows(c, claim_id)
    if not recs:
        print("%s→ 这条理解目前不支撑任何建议（纠正它暂不改变系统行为）" % prefix)
        return
    print("%s★ 因此需要重审的建议 %d 条：" % (prefix, len(recs)))
    for rid, title, rst, kind, note in recs:
        bad, tot = _rec_health(c, rid)
        print("%s  %s %s（%d/%d 条依赖不稳）" % (prefix, rid, title, len(bad), tot))


def _kv(args):
    """把 `--k v` 形式解析成 dict，其余按位置收集。"""
    pos, kv, i = [], {}, 0
    while i < len(args):
        x = args[i]
        if x.startswith("--"):
            k = x[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kv[k] = args[i + 1]
                i += 2
            else:
                kv[k] = True
                i += 1
        else:
            pos.append(x)
            i += 1
    return pos, kv


def _pred_rows(c, pending_only=False):
    w = " where match_status='pending'" if pending_only else ""
    return c.execute(
        "select pred_id,question,predicted_choice,actual_choice,match_status,"
        "confidence,basis_claims,linked_rec_id,outcome_verdict,horizon "
        "from predictions%s order by created_at desc, pred_id" % w).fetchall()


def _guess_match(pred, actual):
    """粗判预测与实际的重合度（仅作**建议值**，最终以 `--match` 人工判定为准）。"""
    if not pred or not actual:
        return "pending"
    def toks(s):
        return set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]{2,}", s or ""))
    a, b = toks(pred), toks(actual)
    if not a or not b:
        return "pending"
    j = len(a & b) / float(len(a | b))
    if j >= 0.34:
        return "matched"
    if j >= 0.12:
        return "partial"
    return "mismatched"


def cmd_predict(sub="list", *rest):
    """理解判断（预测）—— 方案「同时回答两件事」的第 ① 路输出。
    系统先推测「在当前条件下他会怎么选 + 依据」，实际发生后回填 → 校准理解模型。
    """
    if sub == "add":
        pos, kv = _kv(rest)
        if len(pos) < 3:
            print("用法：predict add <pred_id> \"<待决问题>\" \"<系统推测他会怎么选>\"")
            print("      [--basis SC-PAT-001,SC-CON-005] [--reason \"依据说明\"]")
            print("      [--alt \"其他可能\"] [--rec REC-XXX] [--conf high|medium|low]")
            print("      [--horizon 2026-10-13] [--topic 汇报]")
            return
        pid, q, pred = pos[0], pos[1], pos[2]
        basis = (kv.get("basis") or "").strip()
        c = conn(write=True)
        c.executescript(DDL)
        if basis:
            bad = [b.strip() for b in basis.split(",")
                   if not c.execute("select 1 from self_claims where claim_id=?",
                                    (b.strip(),)).fetchone()]
            if bad:
                print("!! 依据里的 claim_id 在 self_claims 中不存在，拒绝写入：%s" % ", ".join(bad))
                c.close()
                return
        c.execute("""insert or replace into predictions(
            pred_id,created_at,question,topic,horizon,predicted_choice,predicted_reason,
            basis_claims,alt_choices,confidence,linked_rec_id,updated_at)
            values(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pid, now(), q, kv.get("topic", ""), kv.get("horizon", ""),
             pred, kv.get("reason", ""), basis, kv.get("alt", ""),
             kv.get("conf", "medium"), kv.get("rec", ""), now()))
        c.commit()
        c.close()
        print("[predict] 已记录理解判断 %s" % pid)
        print("  问题      ：%s" % q)
        print("  推测他会选：%s" % pred)
        print("  置信度    ：%s" % PRED_CONF_CN.get(kv.get("conf", "medium"), "中"))
        if basis:
            print("  依据      ：%s" % basis)
        print("  → 等实际发生后：python tools/selfmodel.py predict resolve %s "
              "\"实际选择\" \"他的理由\"" % pid)

    elif sub == "list":
        c = conn()
        rows = _pred_rows(c, pending_only=("--pending" in rest))
        print("=" * 66)
        print("理解判断（预测）%d 条%s" % (len(rows), " · 仅待结算" if "--pending" in rest else ""))
        print("=" * 66)
        for pid, q, pc, ac, ms, conf, basis, rec, ov, hz in rows:
            print("\n  %s [%s · 置信%s]%s" % (pid, PRED_MATCH_CN.get(ms, ms),
                                              PRED_CONF_CN.get(conf, conf),
                                              "  → " + rec if rec else ""))
            print("    问题：%s" % (q or "")[:80])
            print("    推测：%s" % (pc or "")[:90])
            if ac:
                print("    实际：%s" % (ac or "")[:90])
            if basis:
                print("    依据：%s" % basis)
            if ov:
                print("    结果：%s" % PRED_VERDICT_CN.get(ov, ov))
        c.close()

    elif sub == "resolve":
        pos, kv = _kv(rest)
        if len(pos) < 2:
            print("用法：predict resolve <pred_id> \"<实际选择>\" [\"他的理由\"] [--match matched|partial|mismatched]")
            return
        pid, actual = pos[0], pos[1]
        reason = pos[2] if len(pos) > 2 else ""
        c = conn(write=True)
        row = c.execute("select predicted_choice,basis_claims from predictions "
                        "where pred_id=?", (pid,)).fetchone()
        if not row:
            print("!! 找不到 %s" % pid)
            c.close()
            return
        pred, basis = row
        ms = kv.get("match") or _guess_match(pred, actual)
        by = "human" if kv.get("match") else "auto"
        c.execute("update predictions set actual_choice=?,actual_reason=?,actual_time=?,"
                  "match_status=?,match_by=?,mismatch_note=?,updated_at=? where pred_id=?",
                  (actual, reason, now(), ms, by, kv.get("note", ""), now(), pid))
        c.commit()
        print("[predict] %s 结算 → %s（%s判定）"
              % (pid, PRED_MATCH_CN.get(ms, ms), "人工" if by == "human" else "系统粗判"))
        if ms in ("partial", "mismatched"):
            print("  ⚠️ 预测与实际不一致 → 下列依据需要复核：")
            for b in (basis or "").split(","):
                b = b.strip()
                if not b:
                    continue
                st = c.execute("select statement,human_review from self_claims "
                               "where claim_id=?", (b,)).fetchone()
                if st:
                    print("    %s %s（当前审核：%s）"
                          % (b, st[0][:56], REVIEW_CN.get(st[1], st[1])))
            print("  → 复核：python tools/selfmodel.py review <claim_id> corrected \"你的原话\"")
        c.close()

    elif sub == "outcome":
        pos, kv = _kv(rest)
        if len(pos) < 2:
            print("用法：predict outcome <pred_id> worked|failed|mixed|unknown [\"说明\"]")
            return
        pid, verdict = pos[0], pos[1]
        note = pos[2] if len(pos) > 2 else ""
        c = conn(write=True)
        row = c.execute("select linked_rec_id from predictions where pred_id=?",
                        (pid,)).fetchone()
        if not row:
            print("!! 找不到 %s" % pid)
            c.close()
            return
        c.execute("update predictions set outcome_verdict=?,outcome_note=?,updated_at=? "
                  "where pred_id=?", (verdict, note, now(), pid))
        c.commit()
        print("[predict] %s 结果 → %s" % (pid, PRED_VERDICT_CN.get(verdict, verdict)))
        if row[0]:
            r = c.execute("select title,status from recommendations where rec_id=?",
                          (row[0],)).fetchone()
            if r:
                print("  ★ 该决策关联建议 %s（%s · 当前 %s）"
                      % (row[0], r[0], REC_STATUS_CN.get(r[1], r[1])))
                if verdict == "failed":
                    print("    → 结果无效：建议考虑改为 withdrawn，或修正它依赖的理解")
                elif verdict == "worked":
                    print("    → 结果有效：建议保持 active")
        c.close()

    else:
        cmd_calibrate()


def cmd_calibrate():
    """校准：系统对「他会怎么选」的推测，准在哪、错在哪。"""
    from collections import Counter
    c = conn()
    rows = c.execute("select pred_id,question,predicted_choice,actual_choice,match_status,"
                     "basis_claims,confidence,outcome_verdict from predictions").fetchall()
    print("=" * 66)
    print("校准 · 系统对「你会怎么选」的推测准确度")
    print("=" * 66)
    if not rows:
        print("  尚无预测记录。先建一条：")
        print("    python tools/selfmodel.py predict add P-20261013 \"10-13 汇报呈现什么\" "
              "\"你会以过程叙事为主\" --basis SC-PAT-001")
        c.close()
        return
    settled = [r for r in rows if r[4] != "pending"]
    print("  预测总数 %d · 已结算 %d · 待结算 %d" % (len(rows), len(settled), len(rows) - len(settled)))
    if settled:
        cnt = Counter(r[4] for r in settled)
        ok = cnt.get("matched", 0)
        print("  一致 %d · 部分一致 %d · 不一致 %d → 命中率 %.0f%%"
              % (ok, cnt.get("partial", 0), cnt.get("mismatched", 0),
                 100.0 * ok / len(settled)))
        agg = {}
        for pid, q, pc, ac, ms, basis, conf, ov in settled:
            for b in (basis or "").split(","):
                b = b.strip()
                if not b:
                    continue
                t = c.execute("select claim_type from self_claims where claim_id=?",
                              (b,)).fetchone()
                t = t[0] if t else "?"
                agg.setdefault(t, [0, 0])
                agg[t][0] += 1
                if ms == "matched":
                    agg[t][1] += 1
        if agg:
            print("\n  按依据类型（哪类理解支撑的预测更准）：")
            for t, (n, k) in sorted(agg.items(), key=lambda x: -x[1][0]):
                print("    %-16s %d 次 · 命中 %d（%.0f%%）"
                      % (TYPE_CN.get(t, t), n, k, 100.0 * k / n))
        bad = [r for r in settled if r[4] in ("partial", "mismatched")]
        if bad:
            print("\n  ⚠️ 需要复核的理解（预测失准处）：")
            seen = set()
            for pid, q, pc, ac, ms, basis, conf, ov in bad:
                for b in (basis or "").split(","):
                    b = b.strip()
                    if not b or b in seen:
                        continue
                    seen.add(b)
                    st = c.execute("select statement,human_review from self_claims "
                                   "where claim_id=?", (b,)).fetchone()
                    if st:
                        print("    %s %s（%s）"
                              % (b, st[0][:56], REVIEW_CN.get(st[1], st[1])))
    print("\n  用法：")
    print("    python tools/selfmodel.py predict add <id> \"问题\" \"推测的选择\" --basis SC-XXX")
    print("    python tools/selfmodel.py predict resolve <id> \"实际选择\" \"他的理由\"")
    print("    python tools/selfmodel.py predict outcome <id> worked|failed|mixed \"说明\"")
    c.close()


def cmd_verify():
    """★ 验收自检：在数据库副本上证明「纠正一条理解 → 依赖它的建议真的改变」。
    方案 01_数据结构与更新协议.json → proposed_pilot.completion_evidence
      「纠正能改变依赖它的建议」。
    全程只动副本，真库不受影响。
    """
    import shutil
    global DB
    tmpdir = os.path.join(ROOT, "_tmp")
    os.makedirs(tmpdir, exist_ok=True)
    copy = os.path.join(tmpdir, "verify_selfmodel.sqlite")
    shutil.copy2(DB, copy)
    real_db, DB = DB, copy
    try:
        c = conn(write=True)

        CASES = [
            {
                "claim": "SC-CON-001",
                "correction": "本人纠正：「不要生成的」只针对片头，正片可用 AIGC 镜头",
                "verdict": "corrected",
                "expect_rec": "REC-VIDEO-WORKSHOP",
            },
            {
                "claim": "SC-CON-005",
                "correction": "本人纠正：周冉只审大型联合活动，日常推文我可直接发",
                "verdict": "corrected",
                "expect_rec": "REC-ALUMNI-SEND",
            },
            {
                "claim": "SC-MECH-001",
                "correction": "本人纠正：我并不是想把经济机制转成艺术，那只是别人给我的标签",
                "verdict": "rejected",
                "expect_rec": "REC-AIGC-FRAME",
            },
        ]

        print("=" * 70)
        print("验收自检：纠正 → 建议变化（在副本 %s 上运行）" % os.path.basename(copy))
        print("=" * 70)
        passed = 0
        for i, case in enumerate(CASES, 1):
            cid, rec = case["claim"], case["expect_rec"]
            before_ep, before_hr = c.execute(
                "select epistemic_status,human_review from self_claims where claim_id=?",
                (cid,)).fetchone()
            before_flag = ("⚠️ 需重审" if (before_ep in UNSTABLE_EPISTEMIC
                                          or before_hr in UNSTABLE_REVIEW)
                           else "✅ 暂不受影响")
            before_recs = [r[0] for r in _rec_rows(c, cid)]

            c.execute("update self_claims set human_review=?,note=coalesce(note,'')||?,"
                      "revision=revision+1,updated_at=? where claim_id=?",
                      (case["verdict"], "\n[verify] " + case["correction"], now(), cid))
            c.commit()

            after_ep, after_hr = c.execute(
                "select epistemic_status,human_review from self_claims where claim_id=?",
                (cid,)).fetchone()
            after_flag = ("⚠️ 需重审" if (after_ep in UNSTABLE_EPISTEMIC
                                         or after_hr in UNSTABLE_REVIEW)
                          else "✅ 暂不受影响")
            after_recs = [r[0] for r in _rec_rows(c, cid)]

            hit = rec in after_recs
            changed = before_flag != after_flag
            ok = hit and changed
            passed += 1 if ok else 0
            print("\n【用例 %d】%s" % (i, cid))
            print("  纠正：%s" % case["correction"])
            print("  审核：%s → %s" % (REVIEW_CN.get(before_hr, before_hr),
                                       REVIEW_CN.get(after_hr, after_hr)))
            print("  依赖它的建议：%s" % (", ".join(before_recs) or "无"))
            print("  该建议状态：%s → %s" % (before_flag, after_flag))
            print("  结果：%s（期望建议 %s %s）"
                  % ("✅ 建议已随纠正改变" if ok else "❌ 未改变",
                     rec, "命中" if hit else "未命中"))
        # ---- 用例 4：理解判断的校准闭环（predictions）----
        print("\n【用例 4】predictions 校准闭环（推测 → 实际 → 依据需复核）")
        c.execute("insert or replace into predictions(pred_id,created_at,question,"
                  "predicted_choice,basis_claims,confidence,match_status,updated_at) "
                  "values('P-VERIFY-4',?,?,?,?,'medium','pending',?)",
                  (now(), "verify 用：下一次任务他会怎样排期",
                   "他会按既有习惯推进", "SC-CON-001", now()))
        c.commit()
        pr = c.execute("select predicted_choice,basis_claims from predictions "
                       "where pred_id='P-VERIFY-4'").fetchone()
        actual4 = "他这次完全换了做法，先做另一件事"
        ms4 = _guess_match(pr[0], actual4)
        c.execute("update predictions set actual_choice=?,match_status=?,match_by='auto',"
                  "updated_at=? where pred_id='P-VERIFY-4'", (actual4, ms4, now()))
        c.commit()
        chain_ok = bool(c.execute("select 1 from self_claims where claim_id=?",
                                  (pr[1],)).fetchone())
        ok4 = (ms4 in ("partial", "mismatched")) and chain_ok
        print("  系统推测：%s" % pr[0])
        print("  实际选择：%s" % actual4)
        print("  自动判定：%s（期望 不一致/部分一致）" % PRED_MATCH_CN.get(ms4, ms4))
        print("  依据可回链 self_claims：%s" % ("是" if chain_ok else "否"))
        print("  结果：%s" % ("✅ 不一致能触发「依据需复核」" if ok4 else "❌ 闭环未成立"))
        passed += 1 if ok4 else 0

        print("\n" + "=" * 70)
        total = len(CASES) + 1
        print("自检结论：%d/%d 用例通过 —— 「纠正能改变依赖它的建议」"
              " + 「预测不一致能指出需复核的依据」%s"
              % (passed, total, "成立" if passed == total else "未成立"))
        print("（副本已删除，真库未受影响）")
        print("=" * 70)
        c.close()
    finally:
        DB = real_db
        try:
            os.remove(copy)
        except OSError:
            pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    a = sys.argv[1:]
    cmd = a[0]
    if cmd == "init":
        cmd_init()
    elif cmd == "import":
        cmd_import(a[1])
    elif cmd == "render":
        cmd_render()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "list":
        cmd_list(a[1] if len(a) > 1 else "claims")
    elif cmd == "answer":
        cmd_answer(a[1], a[2])
    elif cmd == "review":
        cmd_review(a[1], a[2], a[3] if len(a) > 3 else "")
    elif cmd == "reassess":
        cmd_reassess(a[1], a[2])
    elif cmd == "outcome":
        cmd_outcome(a[1], a[2], a[3] if len(a) > 3 else "")
    elif cmd == "stale":
        cmd_stale(a[1], a[2])
    elif cmd == "reason":
        cmd_reason(a[1], a[2])
    elif cmd == "sync":
        cmd_sync(apply=("--apply" in a))
    elif cmd == "recimport":
        cmd_recimport(a[1])
    elif cmd == "rec":
        cmd_rec(a[1] if len(a) > 1 else "list", *a[2:])
    elif cmd == "link":
        cmd_link(a[1], a[2], a[3] if len(a) > 3 else "")
    elif cmd == "impact":
        if len(a) > 1 and a[1] == "--all":
            cmd_impact(show_all=True)
        elif len(a) > 1:
            cmd_impact(a[1])
        else:
            cmd_impact(show_all=True)
    elif cmd == "brief":
        cmd_brief(a[1])
    elif cmd == "changes":
        since = None
        if len(a) > 2 and a[1] == "--since":
            since = a[2]
        cmd_changes(since)
    elif cmd == "predict":
        cmd_predict(a[1] if len(a) > 1 else "list", *a[2:])
    elif cmd == "calibrate":
        cmd_calibrate()
    elif cmd == "verify":
        cmd_verify()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
