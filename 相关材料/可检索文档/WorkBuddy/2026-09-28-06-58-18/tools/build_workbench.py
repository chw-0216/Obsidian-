# -*- coding: utf-8 -*-
"""
build_workbench.py —— Obsidian Bases 四工作视图（工作台）

思路：**把筛选条件预计算成笔记属性**（need_confirm / weak_evidence / has_counter / action），
`.base` 里只做最简单的 `x == true` 比较 —— 避免复杂表达式在不同 Obsidian 版本上失效。

产出：
  Obsidian Vault\\04_工作台\\
    ├─ ① 待本人确认.base
    ├─ ② 最近更新.base
    ├─ ③ 证据不足或矛盾.base
    ├─ ④ 当前行动.base
    ├─ 00_工作台说明.md
    ├─ 结论\\CON-xxx ….md          （57 篇）
    └─ 事件\\EVT-….md              （A 级 203 篇）

用法：
  python tools\\build_workbench.py
  python tools\\build_workbench.py --prune   # 清掉工作台里已失效的笔记
"""
import os, re, io, sys, json, sqlite3, datetime
from kb_fields import frontmatter, stable_note_path

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
WB = os.path.join(VAULT, "04_工作台")
D_CONCL = os.path.join(WB, "结论")
D_EVENT = os.path.join(WB, "事件")

STAMP = os.path.join(WS, "_tmp", "pipeline_stamp.json")

ILLEGAL = r'[\\/:*?"<>|]'
TAG_CONCL = "分析/结论"
TAG_EVENT = "分析/事件"


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def yv(v):
    return json.dumps("" if v is None else str(v), ensure_ascii=False)


TAIL = "。．，,、;；:：·-—（）()[]【】\"' "


def safe(name, maxlen=34):
    """生成安全、干净的笔记文件名（去 Windows 非法字符 / 全角竖线 / 强调符 / 成对引号）"""
    s = re.sub(ILLEGAL, "", name or "")
    for ch in "｜|「」『』“”‘’":
        s = s.replace(ch, "" if ch in "「」『』“”‘’" else " ")
    s = re.sub(r"^[\s★☆⚠️•·◆■□※→\-]+", "", s)      # 去开头强调符
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > maxlen:
        cut = s[:maxlen]
        for p in ("，", "。", "、", "；", " ", "："):
            i = cut.rfind(p)
            if i > maxlen * 0.45:
                cut = cut[:i]
                break
        s = cut
    return s.strip().strip(TAIL)


# ★★ 人工字段：只在这四个键上，笔记才是「你的」，其余全是机器生成
HUMAN_KEYS = ("verdict", "my_note", "review_status", "load_self")
VERDICTS = ("待定", "认可", "存疑", "推翻")
REVIEWS = ("待核实", "已核实", "已修正", "已撤回")


def read_human(path):
    if not os.path.exists(path):
        return {}
    fm = frontmatter(path)
    out = {k: ("" if fm[k] is None else str(fm[k])) for k in HUMAN_KEYS if k in fm}
    for key, allowed in (("verdict", VERDICTS), ("review_status", REVIEWS)):
        if key in out and out[key] not in allowed:
            raise ValueError("Invalid manual field %s in %s; preserving source" % (key, path))
    return out



def source_audit(event_id):
    p = os.path.join(WS, "_tmp", "kb_rebuild", "evidence_audit.json")
    if not os.path.exists(p):
        return "未运行来源审计"
    with io.open(p, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("events", {}).get(event_id, {}).get("summary", "未覆盖")


def evidence_quality_map(con):
    """事件 → 证据质量（高/中/低/无）"""
    q = {}
    for eid, hi, mid, lo in con.execute("""
        select event_id,
               sum(link_status='rebuilt'), sum(link_status='ambiguous'), sum(link_status='unlinked')
          from evidence group by event_id"""):
        q[eid] = "高" if hi else ("中" if mid else ("低" if lo else "无"))
    return q


def stamp_info():
    if os.path.exists(STAMP):
        d = json.load(io.open(STAMP, encoding="utf-8"))
        return d.get("run_id", ""), d.get("generated_at", ""), d.get("data_until", ""), d.get("extract_version", "")
    n = datetime.datetime.now()
    return n.strftime("%Y%m%d-%H%M%S"), n.strftime("%Y-%m-%d %H:%M:%S"), "", ""


def build_conclusion_notes(con, run_id):
    rows = con.execute("""select concl_id,statement,status,evidence_refs,counter_examples,
                                 self_confirmed,valid_from,source_doc,note,verdict,my_note,
                                 evidence_events,link_score,link_method
                            from conclusions order by concl_id""").fetchall()
    files = []
    for (cid, st, status, evs, cnt, sc, vfrom, src, note, verdict, my_note,
         eevents, lscore, lmethod) in rows:
        has_counter = bool((cnt or "").strip())
        fn = safe("%s %s" % (cid, st), 46) + ".md"
        path = stable_note_path(D_CONCL, cid, fn)
        old = read_human(path)                       # ★ 先读回你写过的批注
        if old.get("verdict") in VERDICTS:
            verdict = old["verdict"]
        if "my_note" in old:
            my_note = old["my_note"]
        verdict = (verdict or "待定").strip() or "待定"
        my_note = my_note or ""
        need_confirm = (status == "待核实") or (status == "有效" and verdict == "待定")
        fm = [
            "---",
            "type: 结论",
            "id: %s" % yv(cid),
            "status: %s" % yv(status),
            "self_confirmed: %s" % ("true" if sc else "false"),
            "verdict: %s" % yv(verdict),             # ← 人工：待定/认可/存疑/推翻
            "my_note: %s" % yv(my_note),             # ← 人工：你的补充
            "need_confirm: %s" % ("true" if need_confirm else "false"),
            "has_counter: %s" % ("true" if has_counter else "false"),
            "evidence_events: %s" % yv(eevents or ""),
            "link_method: %s" % yv(lmethod or ""),
            "source: %s" % yv(src),
            "updated: %s" % yv((vfrom or "").strip() or ""),
            "tags:",
            "  - %s" % TAG_CONCL,
            "---",
        ]
        body = ["# %s · %s" % (cid, st), ""]
        body.append("> **状态**：%s%s" % (status, "　⚠️ 已退出当前画像" if status == "已撤回" else ""))
        if evs:
            body.append("> **支持证据**：%s" % evs)
        if has_counter:
            body.append("> **反例 / 红线**：%s" % cnt)
        body.append("> **文档里本人提过**：%s　← 机器判定，别改" % ("是" if sc else "否"))
        if eevents:
            body.append("> **支持事件**：%s" % eevents)
            body.append("> **匹配分**：%s　← 文本匹配候选分，不代表证据支持或事实可信度" % (lscore or 0))
        else:
            body.append("> **支持事件**：无　← **依据不是事件**：%s" % (lmethod or "无"))
        body.append("> **成立时间**：%s" % (vfrom or "**未标**（需人工补）"))
        body.append("> **出处**：%s" % src)
        body.append("> **我的判定**：%s%s" % (
            verdict, "" if verdict != "待定" else "　← 在 frontmatter 的 `verdict:` 里改成 认可/存疑/推翻"))
        if my_note:
            body.append("> **我的补充**：%s" % my_note)
        if note:
            body.append("")
            body.append("> %s" % note)
        body += ["", "---", "",
                 "回查：`python tools\\trace.py %s`　｜　run_id `%s`" % (cid, run_id), ""]
        files.append((path, resolve_reference_links("\n".join(fm + body))))
    return files


def build_event_notes(con, run_id):
    qmap = evidence_quality_map(con)
    rows = con.execute("""select event_id,date,phase,level,subject,category,nature,event,person,
                                 distance,relation,people,msg_count,load_rule,load_score,
                                 source,impact,review_status,load_self
                            from events where level='A' order by date desc""").fetchall()
    files = []
    for (eid, date, phase, level, subject, cat, nature, ev, person, dist, rel, people,
         mcnt, lrule, lscore, src, impact, review, load_self) in rows:
        quality = qmap.get(eid, "无")
        weak = quality in ("低", "无")
        historical_plan = nature in ("计划", "进行中")
        action = False  # A historical plan is not a confirmed current action
        head = re.split(r"[｜|，。；]", ev or "")[0]          # 只取第一段，避免长标题
        path = stable_note_path(D_EVENT, eid, safe("%s %s" % (eid, head), 40) + ".md")
        old = read_human(path)                               # ★ 先读回你写过的批注
        if old.get("review_status") in REVIEWS:
            review = old["review_status"]
        if "load_self" in old:
            load_self = old["load_self"]
        review = (review or "待核实").strip() or "待核实"
        load_self = load_self or ""
        need_confirm = (review == "待核实")
        fm = [
            "---",
            "type: 事件",
            "id: %s" % yv(eid),
            "date: %s" % (date or ""),
            "level: %s" % yv(level),
            "nature: %s" % yv(nature),
            "person: %s" % yv(person or ""),
            "review_status: %s" % yv(review),          # ← 人工：待核实/已核实/已修正/已撤回
            "load_self: %s" % yv(load_self),           # ← 人工：我的真实感受（留空就是没感受）
            "evidence_quality: %s" % yv(quality),
            "need_confirm: %s" % ("true" if need_confirm else "false"),
            "weak_evidence: %s" % ("true" if weak else "false"),
            "action: false",
            "historical_plan: %s" % ("true" if historical_plan else "false"),
            "support_review: 待核验",
            "source_audit: %s" % yv(source_audit(eid)),
            "msg_count: %s" % (mcnt if mcnt is not None else 0),
            "source: %s" % yv(src),
            "updated: %s" % yv(date or ""),
            "tags:",
            "  - %s" % TAG_EVENT,
            "---",
        ]
        body = ["# %s · %s" % (eid, date or "日期不明"), "",
                "**事件**：%s" % ev, "",
                "| 项 | 值 |", "|---|---|",
                "| 层级 | %s |" % level,
                "| 性质 | %s |" % nature,
                "| 对话人 | %s |" % (person or "—"),
                "| 距离 / 关系 | %s / %s |" % (dist or "—", rel or "—"),
                "| 涉及人 | %s |" % (people or "—"),
                "| 条数 | %s |" % (mcnt if mcnt is not None else "—"),
                "| 规则评分 | %s（%s）　← 机器规则，非本人感受 |" % (lrule or "—", lscore if lscore is not None else "—"),
                "| 来源 | %s |" % (src or "—"),
                "| 原文定位等级（旧 evidence_quality） | **%s**；不等于论断已获支持 |" % quality,
                "| 来源审计 | %s；语义支持仍需复核 |" % source_audit(eid),
                ""]
        if impact:
            body += ["**影响**：%s" % impact, ""]
        body += ["## 我的批注（在 frontmatter 里改，别改上面的机器字段）", "",
                 "| 项 | 当前值 | 可填 |", "|---|---|---|",
                 "| `review_status` | %s | 待核实 / 已核实 / 已修正 / 已撤回 |" % review,
                 "| `load_self` | %s | 自由文本（你当时的真实感受） |" % (load_self or "—"),
                 "", "---", "",
                 "回查：`python tools\\trace.py %s`　｜　run_id `%s`" % (eid, run_id), ""]
        files.append((path, resolve_reference_links("\n".join(fm + body))))
    return files


# ---------------------------------------------------------------- .base 文件

BASE_CONFIRM = """filters:
  and:
    - 'need_confirm == true'
properties:
  id:
    displayName: 编号
  status:
    displayName: 状态
  verdict:
    displayName: ★ 我的判定
  self_confirmed:
    displayName: 文档提过
  person:
    displayName: 对话人
  nature:
    displayName: 性质
  evidence_quality:
    displayName: 证据
  review_status:
    displayName: ★ 我的复核
  source:
    displayName: 出处
views:
  - type: table
    name: 结论 · 待拍板
    filters:
      and:
        - 'type == "结论"'
    order:
      - file.name
      - id
      - verdict
      - status
      - self_confirmed
      - source
    sort:
      - property: status
        direction: ASC
  - type: table
    name: 事件 · 待复核（A 级）
    limit: 40
    filters:
      and:
        - 'type == "事件"'
    order:
      - file.name
      - date
      - person
      - nature
      - review_status
      - evidence_quality
    sort:
      - property: date
        direction: DESC
"""

BASE_RECENT = """filters:
  and:
    - 'type == "事件"'
properties:
  date:
    displayName: 日期
  person:
    displayName: 对话人
  level:
    displayName: 层级
  nature:
    displayName: 性质
  evidence_quality:
    displayName: 证据
  msg_count:
    displayName: 条数
views:
  - type: table
    name: 最近事件（按日期倒序）
    limit: 40
    order:
      - file.name
      - date
      - person
      - level
      - nature
      - evidence_quality
    sort:
      - property: date
        direction: DESC
  - type: table
    name: 最近改动（按修改时间）
    limit: 40
    order:
      - file.name
      - date
      - person
      - file.mtime
    sort:
      - property: file.mtime
        direction: DESC
"""

BASE_WEAK = """properties:
  id:
    displayName: 编号
  date:
    displayName: 日期
  person:
    displayName: 对话人
  evidence_quality:
    displayName: 证据质量
  weak_evidence:
    displayName: 薄弱
  has_counter:
    displayName: 有反例
  status:
    displayName: 状态
  link_method:
    displayName: 依据
  evidence_events:
    displayName: 支持事件
views:
  - type: table
    name: 证据薄弱的事件（A 级）
    order:
      - file.name
      - date
      - person
      - evidence_quality
      - nature
    filters:
      and:
        - 'type == "事件"'
        - 'weak_evidence == true'
    sort:
      - property: date
        direction: DESC
  - type: table
    name: 带反例 / 红线的结论
    filters:
      and:
        - 'type == "结论"'
        - 'has_counter == true'
    order:
      - file.name
      - id
      - status
      - source
  - type: table
    name: 结论 · 依据不是事件（本人自述 / 方法论）
    filters:
      and:
        - 'type == "结论"'
        - 'link_method != "auto-idf"'
    order:
      - file.name
      - id
      - link_method
      - status
      - source
"""

BASE_ACTION = """filters:
  and:
    - 'type == "行动"'
    - 'action_state != "完成"'
    - 'action_state != "取消"'
properties:
  id:
    displayName: 编号
  date:
    displayName: 日期
  person:
    displayName: 对话人
  nature:
    displayName: 性质
  evidence_quality:
    displayName: 证据
  source:
    displayName: 出处
views:
  - type: table
    name: 当前行动（独立行动记录；待澄清须先核实）
    order:
      - file.name
      - date
      - person
      - nature
      - evidence_quality
    sort:
      - property: date
        direction: DESC
"""

README = """---
tags:
  - 分析/工作台
---
# 04_工作台 · Obsidian Bases 四视图

> **自动生成**，请勿手改 —— 由 `tools\\build_workbench.py` 重建。
> run_id `%(run_id)s` ｜ 数据截至 `%(data_until)s` ｜ 生成 `%(generated_at)s` ｜ 版本 `%(ver)s`

## 这是什么

把分析库 `analysis.sqlite` 里的**结论**和**A 级事件**铺成 Obsidian 笔记，
再用 Obsidian 原生 **Bases**（`.base` 文件）做四个工作视图 —— 不需要任何社区插件。

## 四个视图

| 文件 | 用途 | 视图 |
|---|---|---|
| `① 待本人确认.base` | 需要你本人拍板 / 复核的 | 「结论 · 待拍板」+「事件 · 待复核（A 级）」 |
| `② 最近更新.base` | 最近发生 / 最近改动 | 「最近事件（按日期倒序）」+「最近改动（按修改时间）」 |
| `③ 证据不足或矛盾.base` | 证据链不牢的 | 「证据薄弱的事件」+「带反例 / 红线的结论」 |
| `④ 当前行动.base` | 已独立登记的行动 | 排除完成和取消；历史计划不自动进入 |

**用法**：在 Obsidian 里直接点开 `.base` 文件 → 就是一张可排序、可筛选、可导 CSV 的表。
也可以嵌进别的笔记：`![[① 待本人确认.base#结论 · 待拍板]]`

## 筛选靠的是「预计算属性」

`.base` 里只写最简单的 `x == true`，条件全部在生成时算好：

| 属性 | 含义 |
|---|---|
| `need_confirm` | 需要你本人确认（结论：待核实或有效但未确认；事件：A 级且未复核） |
| `weak_evidence` | 证据薄弱（A 级事件里证据质量为「低」或「无」） |
| `has_counter` | 结论带反例 / 红线 |
| `action` | 历史事件一律 false；当前任务用独立的行动类型登记 |
| `historical_plan` | 仅标记原事件性质，不代表现在仍待办 |
| `source_audit` | 定位审计结果，不等同于语义支持 |
| `evidence_quality` | 高 / 中 / 低 / 无（按回链结果算） |

**为什么不写复杂表达式**：Bases 的表达式语法在不同 Obsidian 版本上有差异，
预计算属性是**版本无关**的 —— 视图不会因为语法变动而失效。

## 怎么用（三步）

1. Obsidian 里打开本目录 → 点 `① 待本人确认.base` → 看到一张表
2. 点任意一行 → 进笔记 → 在 **frontmatter**（开头 `---` 之间）改**人工字段**
3. 回到对话里说一句「同步一下」→ 我跑 `sync_from_vault.py` → 你的判断进库 → 视图自动更新

## ★ 哪些字段是你的（只有这四个）

| 字段 | 在哪 | 可填 |
|---|---|---|
| `verdict` | 结论笔记 | 待定 / 认可 / 存疑 / 推翻 |
| `my_note` | 结论笔记 | 自由文本 |
| `review_status` | 事件笔记 | 待核实 / 已核实 / 已修正 / 已撤回 |
| `load_self` | 事件笔记 | 自由文本（你当时的真实感受） |

**其余字段全是机器生成**，改了下一次重建就会被覆盖。人工字段按稳定 ID 保留（重复 ID 会中止；缺字段不合成空值；明确清空保留为空）（`build_analysis_db` 的 `UPD_COLS` 不含它们；`build_workbench` 重建前会先读回旧值）。

```bash
python tools\\sync_from_vault.py          # 只读：列出你在笔记里改了什么
python tools\\sync_from_vault.py --apply  # 真写回分析库（自动备份 + 记 revisions）
```

## 重新生成

```bash
python tools\\build_workbench.py          # 重建工作台
python tools\\regenerate_all.py           # 整条管线可能改写数据库，先检查并发与备份
```

## 回查

每篇笔记底部都有回查命令：

```bash
python tools\\trace.py EVT-20260808-002   # 事件 → 证据 → 原始消息
python tools\\trace.py CON-002            # 结论 → 状态 / 反例
```

## 红线

笔记里含**真人姓名、关系判断、金额**，**不得外传**。原始聊天数据全程本地处理。
"""


def resolve_reference_links(text):
    def replace(match):
        target = match.group(1)
        cid = target.split(" ")[0]
        resolved = stable_note_path(D_CONCL, cid, "__not_found__.md")
        if not os.path.isfile(resolved):
            return match.group(0)
        relative = os.path.relpath(resolved, VAULT).replace("\\", "/")
        return "[[" + relative.removesuffix(".md") + "|" + target + "]]"
    header, separator, body = text.partition("\n---\n")
    if separator:
        return header + separator + re.sub(r"\[\[(CON-\d{3}(?: 债务全景十项)?)\]\]", replace, body)
    return re.sub(r"\[\[(CON-\d{3}(?: 债务全景十项)?)\]\]", replace, text)

def protected_note(path, text):
    if re.search("证件|医疗|症状|病理|密钥|密码|凭据|汇报|材料盘点|当前主线|今日卡|每日简报|自我理解引擎|🏠主页", path):
        return True
    old = io.open(path, encoding="utf-8-sig").read() if os.path.isfile(path) else ""
    return bool(re.search("汇报|开题", old + "\n" + text))

def main():
    prune = "--prune" in sys.argv
    if prune:
        raise ValueError("--prune is disabled: preserve original notes; review a migration manifest instead")
    run_id, gen_at, data_until, ver = stamp_info()

    os.makedirs(D_CONCL, exist_ok=True)
    os.makedirs(D_EVENT, exist_ok=True)

    con = ro(ANALYSIS_DB)
    cnotes = build_conclusion_notes(con, run_id)
    enotes = build_event_notes(con, run_id)
    con.close()

    written = set()
    for path, text in cnotes + enotes:
        if protected_note(path, text):
            print("保留保护页：" + path)
            continue
        io.open(path, "w", encoding="utf-8").write(text)
        written.add(os.path.normcase(path))

    removed = 0
    if prune:
        for d in (D_CONCL, D_EVENT):
            for fn in os.listdir(d):
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(d, fn)
                if os.path.normcase(p) not in written:
                    os.remove(p); removed += 1

    bases = {
        "① 待本人确认.base": BASE_CONFIRM,
        "② 最近更新.base": BASE_RECENT,
        "③ 证据不足或矛盾.base": BASE_WEAK,
        "④ 当前行动.base": BASE_ACTION,
    }
    for fn, txt in bases.items():
        io.open(os.path.join(WB, fn), "w", encoding="utf-8").write(txt)

    io.open(os.path.join(WB, "00_工作台说明.md"), "w", encoding="utf-8").write(
        README % {"run_id": run_id, "data_until": data_until, "generated_at": gen_at, "ver": ver})

    print("工作台 → %s" % WB)
    print("  结论笔记 %d 篇 ｜ A 级事件笔记 %d 篇%s" % (len(cnotes), len(enotes),
          ("｜ 清理失效 %d 篇" % removed) if prune else ""))
    print("  四个 .base：%s" % " · ".join(bases.keys()))
    print("  run_id %s ｜ 数据截至 %s" % (run_id, data_until))
    return 0


if __name__ == "__main__":
    sys.exit(main())
