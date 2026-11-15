# -*- coding: utf-8 -*-
"""
sync_from_vault.py —— 把 Obsidian 笔记里的**人工字段**写回 analysis.sqlite

覆盖两层：
  A. 工作台笔记（04_工作台\结论 / 事件）→ conclusions / events
  B. 自我模型视图（06_自我模型 下的 *.md 的**手填区**）→ self_claims / choice_episodes /
     learning_questions（转交 selfmodel.cmd_sync）

设计原则：
  1. **只写人工字段**：结论 `verdict` / `my_note`；事件 `review_status` / `load_self`；
     自我模型：选择 `理由` / 问题 `回答` / 理解 `我的判断`
  2. **默认只读**（列差异），`--apply` 才写
  3. 写前**自动备份**整个分析库到 _tmp/_backup_db_<ts>/
  4. 每次改动写 `revisions` 留痕（entity_type / field / old / new / reason）
  5. 值不合法（不在枚举里）→ **跳过并报警**，不写脏数据

用法：
  python tools\\sync_from_vault.py            # 只读：列出笔记里改了什么
  python tools\\sync_from_vault.py --apply    # 真写回
"""
import os, re, io, sys, shutil, sqlite3, datetime
from kb_fields import frontmatter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
WB = r"C:\Users\wardc\Documents\Obsidian Vault\04_工作台"
D_CONCL = os.path.join(WB, "结论")
D_EVENT = os.path.join(WB, "事件")

VERDICTS = ("待定", "认可", "存疑", "推翻")
REVIEWS = ("待核实", "已核实", "已修正", "已撤回")

# 人工字段 → 目标表 / 目标列
FIELDS_CONCL = {"verdict": "verdict", "my_note": "my_note"}
FIELDS_EVENT = {"review_status": "review_status", "load_self": "load_self"}
ENUM = {"verdict": VERDICTS, "review_status": REVIEWS}


def parse_note(path):
    fm = frontmatter(path)
    return fm.get("id"), {k: ("" if fm[k] is None else str(fm[k]))
                         for k in list(FIELDS_CONCL) + list(FIELDS_EVENT) if k in fm}


def collect(dirpath, fields):
    out = []
    if not os.path.isdir(dirpath):
        return out
    for fn in sorted(os.listdir(dirpath)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(dirpath, fn)
        eid, got = parse_note(p)
        if not eid:
            continue
        keep = {k: v for k, v in got.items() if k in fields}
        if keep:
            out.append((eid, keep, fn))
    return out


def main():
    apply = "--apply" in sys.argv
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    con = sqlite3.connect(ANALYSIS_DB) if apply else sqlite3.connect("file:" + ANALYSIS_DB.replace("\\", "/") + "?mode=ro", uri=True)
    diffs, bad = [], []

    plans = [
        ("conclusion", D_CONCL, FIELDS_CONCL, "conclusions", "concl_id"),
        ("event", D_EVENT, FIELDS_EVENT, "events", "event_id"),
    ]
    for etype, d, fields, tbl, keycol in plans:
        for eid, got, fn in collect(d, fields):
            row = con.execute("select %s from %s where %s=?" % (
                ",".join(fields.values()), tbl, keycol), (eid,)).fetchone()
            if row is None:
                bad.append("%s 不在库里：%s" % (eid, fn))
                continue
            cur = dict(zip(fields.values(), [(x or "") for x in row]))
            for k, col in fields.items():
                if k not in got:
                    continue
                new = (got.get(k) or "").strip()
                old = (cur.get(col) or "").strip()
                if new == old:
                    continue
                if k in ENUM and new not in ENUM[k]:
                    bad.append("%s.%s = 「%s」不合法（只能：%s）→ 已跳过" % (
                        eid, k, new, " / ".join(ENUM[k])))
                    continue
                diffs.append((etype, eid, col, old, new, fn))

    print("=" * 66)
    print("Obsidian 工作台 → 分析库   同步%s" % ("（真写）" if apply else "（只读预览）"))
    print("=" * 66)
    if not diffs:
        print("  没有差异 —— 笔记里的人工字段和库里一致。")
    else:
        print("  发现 %d 处改动：" % len(diffs))
        for etype, eid, col, old, new, fn in diffs:
            print("    %-9s %-22s %-14s %r → %r" % (etype, eid, col, old, new))
    if bad:
        print()
        print("  ⚠️ %d 条跳过（值不合法 / 找不到对象）：" % len(bad))
        for b in bad[:20]:
            print("      " + b)

    # ---- 自我模型层：06_自我模型\*.md 的手填区（选择理由 / 问题回答 / 理解判断）----
    print()
    print("-" * 66)
    try:
        sys.path.insert(0, os.path.join(WS, "tools"))
        import selfmodel as _sm
        _sm.cmd_sync(apply=apply)
    except Exception as e:
        print("  ⚠️ 自我模型层同步跳过：%s" % e)

    if not apply:
        print()
        print("  （只读。要真写回：python tools\\sync_from_vault.py --apply）")
        con.close()
        return 0

    if not diffs:
        con.close()
        return 0

    # ---- 备份 ----
    bdir = os.path.join(WS, "_tmp", "_backup_db_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(bdir, exist_ok=True)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    for suf in ("", "-wal", "-shm"):
        src = ANALYSIS_DB + suf
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(bdir, os.path.basename(src)))
    print()
    print("  备份 → %s" % bdir)

    # ---- 写入 ----
    con = sqlite3.connect(ANALYSIS_DB)
    n = 0
    for etype, eid, col, old, new, fn in diffs:
        tbl = "conclusions" if etype == "conclusion" else "events"
        keycol = "concl_id" if etype == "conclusion" else "event_id"
        con.execute("UPDATE %s SET %s=?, updated_at=? WHERE %s=?" % (tbl, col, keycol), (new, now, eid))
        con.execute("INSERT INTO revisions(entity_type,entity_id,field,old_value,new_value,changed_at,reason) "
                    "VALUES(?,?,?,?,?,?,?)", (etype, eid, col, old, new, now, "Obsidian 工作台人工批注"))
        n += 1
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    print("  ✅ 写回 %d 处，已记 revisions" % n)
    print("  下一步：python tools\\build_workbench.py  （把新状态刷回笔记）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
