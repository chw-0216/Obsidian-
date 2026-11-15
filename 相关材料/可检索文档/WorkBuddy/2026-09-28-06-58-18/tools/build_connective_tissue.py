# -*- coding: utf-8 -*-
r"""
build_connective_tissue.py —— 阶段B：建「结缔组织」表 + 回填 persons/aliases/sources

设计原则：
  1. 只新增，不删不改原表（events/evidence/conclusions 一律不动）
  2. 幂等：新表用 INSERT OR REPLACE；重跑只覆盖自己写的行
  3. 人工锚点优先：人际网络标注.csv > 距离地图.csv > 距离地图_全库.csv > Obsidian 档案
  4. 执行前自动备份 analysis.sqlite

产物：
  analysis.sqlite 新增 4 表：sources / hypotheses / decisions / procedures
  回填：persons / aliases
"""
import os, sys, io, csv, re, json, sqlite3, shutil, datetime, glob

WS   = r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18"
DB   = WS + "/analysis.sqlite"
ENG  = r"C:/Users/wardc/.workbuddy-ai/skills/self-understanding-engine/references"
VAULT= r"C:/Users/wardc/Documents/Obsidian Vault"
ARCH = VAULT + "/03_微信聊天分析/01_人物档案"
ANNO = r"C:/Users/wardc/Desktop/07_聊天记录分析/微信聊天记录清理/05_人工报告与人工标注/人际网络标注.csv"
OVR  = ENG + "/人物补充锚点.csv"
DEC  = r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozzszn8esr21_db45/decrypted"
DEC2 = r"C:/Users/wardc/AppData/Local/ChatTrace/accounts/wxid_zn4ozsnn8esr21_db45/decrypted"

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
TS  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

log = []
def P(*a):
    s = " ".join(str(x) for x in a)
    log.append(s)
    print(s)

# ============================================================ 0. 备份
def backup():
    d = os.path.join(WS, "_tmp", "_backup_db_" + TS)
    os.makedirs(d, exist_ok=True)
    shutil.copy2(DB, os.path.join(d, "analysis.sqlite"))
    P("[备份] %s  (%d bytes)" % (os.path.join(d, "analysis.sqlite"), os.path.getsize(os.path.join(d, "analysis.sqlite"))))
    return d

# ============================================================ 1. 建表
DDL = {
"sources": """
create table if not exists sources(
  source_id    text primary key,
  kind         text,      -- wechat|obsidian|engine|file|csv|web|photo
  path         text,
  content_hash text,
  first_seen   text,
  last_ok      text,      -- ★ 最后成功读取时间
  privacy      text,      -- local_only | masked_ok
  note         text
)""",
"hypotheses": """
create table if not exists hypotheses(
  hyp_id             text primary key,
  statement          text,
  about_event        text,
  supports           text,
  counters           text,   -- ★ 反证（必填）
  discriminating_obs text,   -- ★ 判别观测
  status             text default 'open',  -- open|supported|refuted|merged
  cross_domains      text,   -- 跨域覆盖
  source_doc         text,
  created_at text, updated_at text
)""",
"decisions": """
create table if not exists decisions(
  dec_id     text primary key,
  question   text,
  goal       text,
  options    text,
  chosen     text,
  why        text,
  expected   text,
  outcome    text,   -- ★ 实际结果（回填）
  status     text default 'open',  -- open|decided|reviewed
  decided_at text,
  reviewed_at text,
  created_at text, updated_at text
)""",
"procedures": """
create table if not exists procedures(
  proc_id  text primary key,
  trigger  text,
  steps    text,
  source   text,   -- 人工|复盘|论文
  note     text,
  applied  integer default 0,
  success  integer default 0,
  created_at text, updated_at text
)""",
}
IDX = [
 "create index if not exists ix_persons_talker on persons(talker)",
 "create index if not exists ix_persons_name   on persons(name)",
 "create index if not exists ix_alias_pid      on aliases(person_id)",
 "create index if not exists ix_sources_kind   on sources(kind)",
 "create index if not exists ix_hyp_status     on hypotheses(status)",
 "create index if not exists ix_dec_status     on decisions(status)",
]

def create_tables(con):
    for n, s in DDL.items():
        con.execute(s)
        P("[建表] %-12s ✓" % n)
    # 轻量迁移：缺列就补（幂等）
    want = {"procedures": [("note","text")]}
    for t, cols in want.items():
        have = {r[1] for r in con.execute("pragma table_info(%s)" % t)}
        for cn, ct in cols:
            if cn not in have:
                con.execute("alter table %s add column %s %s" % (t, cn, ct))
                P("[迁移] %s 补列 %s" % (t, cn))
    for s in IDX:
        con.execute(s)
    P("[建表] 6 个索引 ✓")

# ============================================================ 2. 读 CSV
def rd_csv(p):
    if not os.path.exists(p):
        P("[警告] 缺文件: %s" % p); return []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

# ============================================================ 3. 读 Obsidian frontmatter
def read_archive():
    out = {}
    if not os.path.isdir(ARCH):
        P("[警告] 档案目录不存在"); return out
    for fn in os.listdir(ARCH):
        if not fn.endswith(".md"): continue
        name = fn[:-3]
        try:
            s = io.open(os.path.join(ARCH, fn), encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        fm = {}
        m = re.search(r"^---\s*\n(.*?)\n---", s, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip("[]")
        # 摘要首句
        ab = ""
        ma = re.search(r"##\s*摘要\s*\n+(.{0,120})", s, re.S)
        if ma: ab = re.sub(r"\s+", " ", ma.group(1)).strip()
        out[name] = {
            "importance": fm.get("importance", ""),
            "messages":   fm.get("messages", ""),
            "role":       fm.get("role", ""),
            "tags":       fm.get("tags", ""),
            "abstract":   ab,
            "mtime":      datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(ARCH, fn))).strftime("%Y-%m-%d"),
        }
    return out

# ============================================================ 3.5 读 contact.db（别名金矿）
def read_contacts():
    """username -> {remark, nick, alias}；用于批量补别名，治「检索盲区」"""
    dec = DEC2 if os.path.isdir(DEC2) else DEC
    p = os.path.join(dec, "contact", "contact.db")
    if not os.path.exists(p):
        P("[警告] contact.db 不存在"); return {}
    con = sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)
    out = {}
    for r in con.execute("select username, remark, nick_name, alias from contact"):
        out[r[0]] = {"remark": r[1] or "", "nick": r[2] or "", "alias": r[3] or ""}
    con.close()
    P("[读入] contact.db %d 个联系人" % len(out))
    return out

# ============================================================ 4. 合并 → persons
def build_persons(con):
    allq  = rd_csv(ENG + "/距离地图_全库.csv")   # 1792 行，含 talker
    dist  = rd_csv(ENG + "/距离地图.csv")        # 98 人工锚点
    anno  = rd_csv(ANNO)                          # 53 最权威人工锚点
    ovr   = rd_csv(OVR)                           # ★ 人工补充锚点（最高优先级）
    arch  = read_archive()
    cont  = read_contacts()
    P("[读入] 全库 %d 行 · 距离地图 %d 行 · 人际标注 %d 行 · 补充锚点 %d 行 · Obsidian 档案 %d 份"
      % (len(allq), len(dist), len(anno), len(ovr), len(arch)))

    name2talker, talker2row = {}, {}
    for r in allq:
        nm = (r.get("name") or "").strip()
        tk = (r.get("talker") or "").strip()
        if nm and tk:
            name2talker.setdefault(nm, tk)
            talker2row[tk] = r

    persons = {}   # person_id -> dict
    aliases = {}   # alias -> (person_id, kind)

    def pid_for(name, talker=""):
        tk = talker or name2talker.get(name, "")
        return tk if tk else "name:" + name

    def put(pid, name, force_name=False, **kw):
        d = persons.setdefault(pid, {"person_id": pid, "name": name, "talker": "", "relation": "", "distance": "", "note": ""})
        if force_name or not d["name"]: d["name"] = name
        if kw.get("talker"):   d["talker"]   = kw["talker"]
        if kw.get("relation"): d["relation"] = kw["relation"]
        if kw.get("distance"): d["distance"] = kw["distance"]
        if kw.get("note"):     d["note"]     = (d["note"] + "；" + kw["note"]).strip("；") if d["note"] else kw["note"]
        if name: aliases.setdefault(name, (pid, "备注"))
        return d

    # ---- 层1：全库（打底，1792 人）
    for r in allq:
        nm = (r.get("name") or "").strip(); tk = (r.get("talker") or "").strip()
        if not nm: continue
        note = "n=%s me_pct=%s last=%s" % (r.get("n",""), r.get("me_pct",""), r.get("last",""))
        put(pid_for(nm, tk), nm, talker=tk, note=note)

    # ---- 层2：距离地图（98 人工锚点，覆盖）
    for r in dist:
        nm = (r.get("Name") or "").strip()
        if not nm: continue
        put(pid_for(nm), nm,
            distance=(r.get("距离半径") or "").strip(),
            relation=(r.get("Relation") or "").strip(),
            note="锚点 %s | %s | %s" % (r.get("Detail",""), r.get("Category",""), r.get("Status","")))

    # ---- 层3：人际网络标注（53，最高权威）
    for r in anno:
        nm = (r.get("Name") or "").strip()
        if not nm: continue
        put(pid_for(nm), nm,
            relation=(r.get("Relation") or "").strip(),
            note="★人工标注 %s | %s | %s" % (r.get("Detail",""), r.get("Category",""), r.get("Status","")))

    # ---- 层0：人工补充锚点（最高优先级，覆盖上面全部）
    for r in ovr:
        nm = (r.get("name") or "").strip()
        if not nm: continue
        tk = (r.get("talker") or "").strip()
        pid = pid_for(nm, tk)
        put(pid, nm, force_name=True, talker=tk,
            relation=(r.get("relation") or "").strip(),
            distance=(r.get("distance") or "").strip(),
            note=(r.get("note") or "").strip())
        for a in (r.get("aliases") or "").split("|"):
            a = a.strip()
            if a: aliases[a] = (pid, "昵称")

    # ---- 层4：Obsidian 档案（补充 role / importance；先查别名，避免建重复人）
    hit = 0
    for nm, meta in arch.items():
        pid = aliases[nm][0] if nm in aliases else pid_for(nm)
        if pid in persons:
            if meta["role"] and not persons[pid]["relation"]:
                persons[pid]["relation"] = meta["role"]
            if meta["importance"]:
                persons[pid]["note"] = (persons[pid]["note"] + "；档案 imp=%s" % meta["importance"]).strip("；")
            hit += 1
        else:
            put(pid, nm, relation=meta["role"], note="仅档案 imp=%s" % meta["importance"])
    P("[合并] persons %d 人（其中 %d 人有 Obsidian 档案）· aliases %d 条" % (len(persons), hit, len(aliases)))

    # ---- 层5：contact.db 批量补别名（治检索盲区：备注名/昵称/微信号都能搜到）
    added = 0
    for pid, d in persons.items():
        tk = d["talker"]
        if not tk or tk not in cont: continue
        c = cont[tk]
        for a, kind in ((c["nick"], "昵称"), (c["alias"], "微信号"), (c["remark"], "备注名")):
            if a and a != d["name"] and a not in aliases:
                aliases[a] = (pid, kind); added += 1
    P("[别名] contact.db 补入 %d 条别名（昵称/微信号/备注名）" % added)

    # ---- 写库
    con.execute("delete from persons")
    con.execute("delete from aliases")
    con.executemany("insert or replace into persons(person_id,name,talker,relation,distance,note) values(?,?,?,?,?,?)",
        [(d["person_id"], d["name"], d["talker"], d["relation"], d["distance"], d["note"][:500]) for d in persons.values()])
    con.executemany("insert or replace into aliases(alias,person_id,kind) values(?,?,?)",
        [(a, pid, k) for a, (pid, k) in aliases.items()])
    P("[写库] persons %d · aliases %d" % (len(persons), len(aliases)))
    return persons

# ============================================================ 5. sources 登记
def build_sources(con):
    rows = []
    def add(sid, kind, path, privacy="local_only", note=""):
        ok = ""
        if os.path.exists(path):
            ok = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
        rows.append((sid, kind, path, "", NOW, ok, privacy, note))

    # 微信解密库
    dec = DEC2 if os.path.isdir(DEC2) else DEC
    if os.path.isdir(dec):
        for sub in sorted(os.listdir(dec)):
            p = os.path.join(dec, sub)
            if os.path.isdir(p):
                add("wechat:" + sub, "wechat", p, "local_only", "微信解密库")
        mp = os.path.join(dec, "message")
        if os.path.isdir(mp):
            for f in sorted(os.listdir(mp)):
                if f.endswith(".db"):
                    add("wechat:message/" + f, "wechat", os.path.join(mp, f), "local_only", "微信消息库")
    # 索引库
    for p in [r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"]:
        add("wechat:index.sqlite", "wechat", p, "local_only", "实时索引库")
    # 引擎
    for f in sorted(os.listdir(ENG)):
        add("engine:" + f, "engine", os.path.join(ENG, f), "local_only", "自我理解引擎")
    # Obsidian
    add("obsidian:vault", "obsidian", VAULT, "local_only", "Obsidian 知识库")
    # 人工标注
    add("csv:人际网络标注", "csv", ANNO, "local_only", "最权威人工锚点")
    # 本库自身
    add("db:analysis.sqlite", "file", DB, "local_only", "结缔组织库")

    con.execute("delete from sources")
    con.executemany("insert or replace into sources(source_id,kind,path,content_hash,first_seen,last_ok,privacy,note) values(?,?,?,?,?,?,?,?)", rows)
    P("[写库] sources %d 条" % len(rows))

# ============================================================ 6. procedures 种子
def seed_procedures(con):
    P_ = [
      ("proc:read-person", "要判断一个人是谁 / 什么关系",
       "1 读 01人格核心 2 读 04人际地图 3 读 05纠偏层对应条目 4 查 persons/aliases 5 输出：距离半径/关系性质/结向/我执投射空间/建议姿态",
       "人工", "来自引擎 02-读人协议"),
      ("proc:read-dialog", "要判断一句话什么意思 / 该回什么",
       "1 三态诊断(绿/黄/红) 2 红线检查(12 条) 3 一句话建议 4 标注风险与备选",
       "人工", "来自引擎 03-读对话协议"),
      ("proc:read-event", "要回答「我经历过什么」",
       "1 先定链(9 条因果链) 2 阶段底色 3 影响评估(距离×负荷×链) 4 回原始证据",
       "人工", "来自引擎 08-读事件协议"),
      ("proc:abduce", "要做一个重要决策",
       "1 定目标(单一) 2 我执检索(四根轴) 3 生成≥3互斥假设 4 每条挂反证+判别观测 5 三档方案 6 最小信息行动 7 结果回填 decisions",
       "人工", "溯因引擎 §5"),
      ("proc:dedup-source", "统计「有多少条证据」",
       "1 按 content_hash 去重 2 同一原文被 N 个报告引用仍算 1 个独立来源 3 检查 source_root",
       "复盘", "来源唯一原则"),
      ("proc:verify-number", "引用任何数字",
       "1 回 00-真相源·数字基准 2 现算不写死 3 标注数据截止时间 4 过期快照不得引用",
       "人工", "引擎加载协议 ⓪"),
    ]
    con.execute("delete from procedures")
    con.executemany("insert or replace into procedures(proc_id,trigger,steps,source,note,applied,success,created_at,updated_at) values(?,?,?,?,?,0,0,?,?)",
        [(a,b,c,d,e,NOW,NOW) for a,b,c,d,e in P_])
    P("[写库] procedures %d 条" % len(P_))

# ============================================================ 7. hypotheses 种子
def seed_hypotheses(con):
    H = [
      ("hyp:materials-untapped",
       "已有部分项目材料尚未转化成可清楚展示、复用、对外介绍的成果，所以继续开新项目的边际收益可能偏低。",
       "batch.sqlite: materials 64,109 / experiences 2,207 vs 成果线索_首轮.csv 条目少",
       "原料多、成品少",
       "近 3 个月重心在央美美术馆实习（新项目）——若这条本身是主线，则不成立",
       "数「能直接进作品集的完整案例」有几个；≥3 个则本假设证伪",
       "学业+创作+现金流", "open", "方案书 §5.4"),
      ("hyp:multi-line-defense",
       "多线并行（多个项目/多条关系同时推进）是防御装置，不是缺陷——拆之前他还没有别的出口。",
       "01人格核心·三态 / 距离定律",
       "本人自述与行为一致",
       "若某条线已能独立提供稳定现金流与身份确认，则防御功能可被替代",
       "观察：当出现一条能同时给钱+给身份确认的主线时，他是否自发收缩其他线",
       "关系+现金流+学业", "supported", "01-人格核心"),
      ("hyp:jinglin-mainline",
       "读研真正主线是井邻·洞台村工作站（515 条/99 会话/18 个月），导师划界、母亲兜底、他淡化三者并存，不构成对立。",
       "05-纠偏层 三·补·38",
       "515 条/99 会话/18 个月",
       "若近 3 个月该线消息量持续为 0，则「当前主线」表述需下调为「已完成阶段」",
       "查 2026-07 之后井邻相关消息量是否归零",
       "学业+关系", "open", "05-纠偏层 三·补·38"),
    ]
    # ★ 只删「种子表里列出的 id」——原写法 `like 'hyp:%'` 会把人工/增量写入的假设一起抹掉
    con.executemany("delete from hypotheses where hyp_id=?", [(h[0],) for h in H])
    # ★ 种子元组顺序为 (..., cross_domains, status, source_doc)，与列清单必须一致
    con.executemany("insert or replace into hypotheses(hyp_id,statement,about_event,supports,counters,discriminating_obs,cross_domains,status,source_doc,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)",
        [(a,b,c,d,e,f,g,h,i,NOW,NOW) for a,b,c,d,e,f,g,h,i in H])
    P("[写库] hypotheses %d 条" % len(H))

# ============================================================ 8. decisions 种子
def seed_decisions(con):
    D = [
      ("dec:20261007-shuzelin", "舒泽林 10-07 10:34「来看吗二爷」+ 一张竖长条图，怎么回？", "关系（维持对价结构）",
       "A 直接去 / B 问清楚再定 / C 不回", "", "", "看他图是什么；若是他组局则去", "", "open", "", "", NOW, NOW),
      ("dec:20261007-keqiying", "柯益盈线（251 条止于 2025-11-08，空窗 11 个月）是否重启？", "关系",
       "A 重启（中性事务切入）/ B 不重启 / C 观察", "", "", "重启后 30 天内是否有回应", "", "open", "", "", NOW, NOW),
      ("dec:20261007-wangyi", "给王义（安鹏·天津）发消息问三笔事故返款（已卡 11 天）", "现金流",
       "A 今天发 / B 再等 / C 直接找安鹏", "", "", "三笔返款是否到账", "", "open", "", "", NOW, NOW),
    ]
    # ★ 只删种子 id（原写法 `like 'dec:%'` 会抹掉人工新增的决策）
    con.executemany("delete from decisions where dec_id=?", [(d[0],) for d in D])
    con.executemany("insert or replace into decisions(dec_id,question,goal,options,chosen,why,expected,outcome,status,decided_at,reviewed_at,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [tuple(x) for x in D])
    P("[写库] decisions %d 条" % len(D))

# ============================================================ main
def main():
    P("=" * 78); P("结缔组织构建 · " + NOW); P("=" * 78)
    bd = backup()
    con = sqlite3.connect(DB, timeout=30)
    try:
        create_tables(con)
        build_persons(con)
        build_sources(con)
        seed_procedures(con)
        seed_hypotheses(con)
        seed_decisions(con)
        con.commit()
        P("-" * 78)
        P("[复核] 表行数：")
        for t in ["persons","aliases","sources","hypotheses","decisions","procedures","events","evidence","conclusions"]:
            c = con.execute("select count(*) from %s" % t).fetchone()[0]
            P("   %-14s %8d" % (t, c))
    finally:
        con.close()
    P("=" * 78); P("完成 · 备份在 " + bd)
    io.open(os.path.join(WS, "_tmp", "connective_build.out"), "w", encoding="utf-8").write("\n".join(log))

if __name__ == "__main__":
    main()
