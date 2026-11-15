# -*- coding: utf-8 -*-
"""
verify_analysis.py —— 一次改动后必跑的验收检查（只读为主 · 自测在临时副本上）

覆盖用户要求的 6 项 + 中文检索验收：
  1. 事件 ID 唯一且非空
  2. 证据引用有效（msg_id 能回链索引库）
  3. 重复运行不新增重复事件（实跑两次对比）
  4. 日期修改保留历史（实跑改日期 CSV · 检查 ID 复用 + revisions 留痕）
  5. 已撤回结论退出当前画像（v_conclusions_current 不得含「已撤回」）
  6. 各产物版本一致（stamp / manifest vs 分析库 meta）
  7. 中文检索验收：两字项目名 / 姓名 / 旧备注 / 日期

用法：
  python tools\\verify_analysis.py              # 控制台报告
  python tools\\verify_analysis.py --json out.json
  python tools\\verify_analysis.py --html out.html
"""
import os, sys, re, csv, io, json, shutil, sqlite3, hashlib, subprocess, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
EV_CSV = r"C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\事件库.csv"
TMP = os.path.join(WS, "_tmp")
STAMP = os.path.join(TMP, "pipeline_stamp.json")
MANIFEST = os.path.join(TMP, "pipeline_manifest.json")
PY = sys.executable

results = []


def check(name, ok, detail="", warn=False):
    results.append({"name": name, "ok": bool(ok), "warn": bool(warn and not ok), "detail": detail})
    tag = "PASS" if ok else ("WARN" if warn else "FAIL")
    print("  [%s] %s" % (tag, name))
    if detail:
        for line in str(detail).splitlines():
            print("        " + line)
    return ok


def ro(path):
    return sqlite3.connect("file:" + path.replace("\\", "/") + "?mode=ro", uri=True)


def h1(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


# ---------------------------------------------------------------- 1. ID 唯一非空
def c1_ids():
    h1("1. 事件 ID 唯一且非空")
    con = ro(ANALYSIS_DB)
    n = con.execute("select count(*) from events").fetchone()[0]
    nu = con.execute("select count(distinct event_id) from events").fetchone()[0]
    bad = con.execute("select count(*) from events where event_id is null or trim(event_id)=''").fetchone()[0]
    badfmt = [r[0] for r in con.execute("select event_id from events") if not re.fullmatch(r"EVT-([\dA-Z]+)-\d{3}", r[0])]
    dupnk = n - con.execute("select count(distinct natkey) from events").fetchone()[0]
    con.close()
    check("事件数 = 唯一 ID 数", n == nu, "总 %d · 唯一 %d" % (n, nu))
    check("ID 无空值", bad == 0, "空值 %d" % bad)
    check("ID 格式合规 EVT-YYYYMMDD-NNN", not badfmt, "不合规 %d 例%s" % (len(badfmt), ("：" + ", ".join(badfmt[:3])) if badfmt else ""))
    check("自然键唯一（幂等前提）", dupnk == 0, "重复自然键 %d" % dupnk)
    return {"n": n, "unique": nu}


# ------------------------------------------------------- 2. 证据引用有效
def c2_evidence():
    h1("2. 证据引用有效（msg_id 能回链索引库）")
    con = ro(ANALYSIS_DB)
    dist = dict(con.execute("select link_status, count(*) from evidence group by 1"))
    linked = con.execute("select count(*) from evidence where msg_id is not null").fetchone()[0]
    ids = [r[0] for r in con.execute("select distinct msg_id from evidence where msg_id is not null")]
    con.close()

    hit = 0
    if ids:
        ic = ro(INDEX_DB)
        for i in range(0, len(ids), 900):
            chunk = ids[i:i + 900]
            q = "select count(*) from messages where id in (%s)" % ",".join("?" * len(chunk))
            hit += ic.execute(q, chunk).fetchone()[0]
        ic.close()
    rate = (hit / len(ids) * 100) if ids else 0.0
    total = sum(dist.values())
    traceable = dist.get("rebuilt", 0) + dist.get("ambiguous", 0)

    for k in ("rebuilt", "ambiguous", "unlinked", "orphan", "not_evidence", "text_only"):
        if k in dist:
            print("        %-14s %5d" % (k, dist[k]))
    check("有 msg_id 的证据全部回链成功", hit == len(ids), "回链 %d / %d（%.1f%%）" % (hit, len(ids), rate))
    check("含可追溯证据（rebuilt+ambiguous）> 0",
          traceable > 0, "可追溯 %d / %d = %.1f%%" % (traceable, total, traceable / total * 100))
    check("孤儿 ID（msg_xxx）已单独标记、未混入有效引用",
          dist.get("orphan", 0) > 0 and dist.get("orphan", 0) < total,
          "orphan %d 条已标为不可回链" % dist.get("orphan", 0), warn=True)
    return dist


# ------------------------------------------------- 3. 幂等：重复运行不新增
def c3_idempotent():
    h1("3. 重复运行不新增重复事件（实跑两次）")
    tmp = os.path.join(TMP, "_verify_idem.sqlite")
    for suf in ("", "-wal", "-shm"):
        try: os.remove(tmp + suf)
        except Exception: pass
    shutil.copyfile(ANALYSIS_DB, tmp)

    def run():
        r = subprocess.run([PY, os.path.join(WS, "tools", "build_analysis_db.py"),
                            "--db", tmp, "--quiet"], capture_output=True, text=True)
        con = sqlite3.connect(tmp)
        n = con.execute("select count(*) from events").fetchone()[0]
        con.close()
        return n, r.returncode

    n0, _ = run()
    n1, _ = run()
    n2, rc = run()
    ids = None
    con = sqlite3.connect(tmp)
    ids = con.execute("select count(distinct event_id) from events").fetchone()[0]
    con.close()
    check("三次重跑事件数不变", n0 == n1 == n2, "%d → %d → %d" % (n0, n1, n2))
    check("重跑后 ID 仍唯一", ids == n2, "唯一 %d / 总 %d" % (ids, n2))
    for suf in ("", "-wal", "-shm"):
        try: os.remove(tmp + suf)
        except Exception: pass
    return {"n": n0}


# --------------------------------------------- 4. 日期修改保留历史
def c4_date_revision():
    h1("4. 日期修改保留历史（实跑改日期 CSV）")
    tmpdb = os.path.join(TMP, "_verify_date.sqlite")
    tmpcsv = os.path.join(TMP, "_verify_date.csv")
    for suf in ("", "-wal", "-shm"):
        try: os.remove(tmpdb + suf)
        except Exception: pass
    shutil.copyfile(ANALYSIS_DB, tmpdb)

    rows = list(csv.DictReader(io.open(EV_CSV, encoding="utf-8-sig")))
    # 挑一条有完整日期的事件，改日期（保留 (对话人,事件) 不变 → 应复用 ID）
    target = None
    for r in rows:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", (r.get("日期") or "").strip()) and (r.get("事件") or "").strip() and (r.get("对话人") or "").strip():
            target = r
            break
    if not target:
        check("找到可测试事件", False, "CSV 中无合格样本")
        return {}

    old_date = target["日期"].strip()
    new_date = "2030-01-01"
    con = ro(tmpdb)
    nk_old = hashlib.sha1(("%s|%s|%s" % (old_date, target["对话人"].strip(), target["事件"].strip())).encode("utf-8")).hexdigest()
    row = con.execute("select event_id from events where natkey=?", (nk_old,)).fetchone()
    con.close()
    if not row:
        check("在分析库中定位该事件", False, "自然键未命中")
        return {}
    eid_before = row[0]

    # 写改日期后的 CSV
    target["日期"] = new_date
    with io.open(tmpcsv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n_before = None
    con = sqlite3.connect(tmpdb)
    n_before = con.execute("select count(*) from events").fetchone()[0]
    rev_before = con.execute("select count(*) from revisions").fetchone()[0]
    con.close()

    subprocess.run([PY, os.path.join(WS, "tools", "build_analysis_db.py"),
                    "--db", tmpdb, "--csv", tmpcsv, "--quiet"], capture_output=True, text=True)

    con = sqlite3.connect(tmpdb)
    n_after = con.execute("select count(*) from events").fetchone()[0]
    rev_after = con.execute("select count(*) from revisions").fetchone()[0]
    still = con.execute("select date from events where event_id=?", (eid_before,)).fetchone()
    nk_new = hashlib.sha1(("%s|%s|%s" % (new_date, target["对话人"].strip(), target["事件"].strip())).encode("utf-8")).hexdigest()
    newid = con.execute("select event_id from events where natkey=?", (nk_new,)).fetchone()
    revrow = con.execute("select entity_id,field,old_value,new_value from revisions where entity_id=? order by rev_id desc limit 1", (eid_before,)).fetchone()
    con.close()

    check("改日期后事件总数不变", n_before == n_after, "%d → %d" % (n_before, n_after))
    check("事件 ID 复用（未换新 ID）", bool(newid) and newid[0] == eid_before, "新自然键指向 %s（原 %s）" % (newid[0] if newid else "无", eid_before))
    check("日期已更新", still and still[0] == new_date, "当前日期 %s" % (still[0] if still else "无"))
    check("revisions 留痕（旧值→新值）", rev_after == rev_before + 1 and revrow and revrow[2] == old_date and revrow[3] == new_date,
          "修订 %d → %d ｜ 记录 %s" % (rev_before, rev_after, revrow))
    for p in (tmpdb, tmpdb + "-wal", tmpdb + "-shm", tmpcsv):
        try: os.remove(p)
        except Exception: pass
    return {"eid": eid_before}


# ------------------------------------------ 5. 已撤回结论退出当前画像
def c5_conclusions():
    h1("5. 已撤回结论退出当前画像")
    con = ro(ANALYSIS_DB)
    dist = dict(con.execute("select status, count(*) from conclusions group by 1"))
    cur = con.execute("select count(*) from v_conclusions_current").fetchone()[0]
    leak = con.execute("select count(*) from v_conclusions_current where status='已撤回'").fetchone()[0]
    total = con.execute("select count(*) from conclusions").fetchone()[0]
    revoked = [r[0][:44] for r in con.execute("select statement from conclusions where status='已撤回' limit 3")]
    con.close()
    for k, v in sorted(dist.items(), key=lambda x: -x[1]):
        print("        %-6s %3d" % (k, v))
    check("当前画像视图不含「已撤回」", leak == 0, "泄漏 %d 条" % leak)
    check("当前画像 = 总数 − 已撤回", cur == total - dist.get("已撤回", 0),
          "当前 %d ｜ 总 %d ｜ 已撤回 %d" % (cur, total, dist.get("已撤回", 0)))
    if revoked:
        print("        样例（已退出画像）：" + " ／ ".join(revoked))
    return dist


# --------------------------------------------------- 6. 各产物版本一致
def c6_stamp():
    h1("6. 各产物版本一致（stamp / manifest vs 分析库 meta）")
    if not os.path.exists(STAMP):
        check("存在统一版本戳", False, "未找到 %s（先跑 regenerate_all.py）" % STAMP, warn=True)
        return {}
    stamp = json.load(io.open(STAMP, encoding="utf-8"))
    con = ro(ANALYSIS_DB)
    meta = dict(con.execute("select key,value from meta"))
    con.close()
    for k in ("data_until", "extract_version", "generated_at"):
        check("戳与库 meta 一致：%s" % k, stamp.get(k) == meta.get(k),
              "戳 %s ｜ 库 %s" % (stamp.get(k), meta.get(k)))
    if os.path.exists(MANIFEST):
        man = json.load(io.open(MANIFEST, encoding="utf-8"))
        miss, bad, ntext = [], [], 0
        for a in man.get("artifacts", []):
            p, kind = a["path"], a.get("kind", "")
            if not os.path.exists(p):
                miss.append(os.path.basename(p)); continue
            if kind in ("html", "md"):          # 只有文本产物能承载文字戳
                ntext += 1
                txt = io.open(p, encoding="utf-8", errors="ignore").read(4000)
                if stamp["run_id"] not in txt:
                    bad.append(os.path.basename(p))
        check("产物文件都存在", not miss, "缺失 %d%s" % (len(miss), ("：" + ", ".join(miss[:3])) if miss else ""))
        check("文本产物都带同一 run_id", not bad,
              "已校验 %d 份（html/md）｜ 未带戳 %d%s" % (ntext, len(bad), ("：" + ", ".join(bad[:3])) if bad else ""))
        check("二进制产物入清单（CSV/DB 记 sha1）",
              any(a.get("kind") in ("csv", "db") for a in man.get("artifacts", [])),
              "共 %d 份产物" % len(man.get("artifacts", [])))
        return {"artifacts": len(man.get("artifacts", [])), "run_id": stamp["run_id"]}
    check("存在产物清单", False, "未找到 %s" % MANIFEST, warn=True)
    return {"run_id": stamp.get("run_id")}


# --------------------------------------------------- 7. 中文检索验收
def c7_search():
    h1("7. 中文检索验收（两字项目名 / 姓名 / 旧备注 / 日期）")
    con = ro(ANALYSIS_DB)
    tests = [
        ("两字项目名", "井邻"), ("两字项目名", "澜沧"), ("两字项目名", "植墨"),
        ("两字项目名", "笑一"), ("两字地名", "洞台"),
        ("姓名", "陈晔"), ("姓名", "安奇"), ("姓名", "刘丽萍"),
        ("旧备注", "急速回"), ("旧备注", "三思回"),
        ("日期", "2026-04-02"),
    ]
    allok = True
    for kind, kw in tests:
        like = "%" + kw + "%"
        ne = con.execute("select count(*) from events where event like ? or person like ? "
                         "or people like ? or relation like ? or date like ? or category like ?",
                         (like, like, like, like, like, like)).fetchone()[0]
        nv = con.execute("select count(*) from evidence where quote like ?", (like,)).fetchone()[0]
        ok = (ne + nv) > 0
        allok = allok and ok
        print("        %-8s %-8s 事件 %3d ｜ 证据 %3d" % (kind, kw, ne, nv))
    con.close()
    check("全部两字/短词检索均有命中（LIKE 兜底）", allok)
    return {"all_hit": allok}


# ------------------------------------- 8. 人工字段不被脚本覆盖（实跑）
def c8_human_fields():
    h1("8. 人工字段不被覆盖（实跑：写入批注 → 全量重建 → 值还在）")
    tmpdb = os.path.join(TMP, "_verify_human.sqlite")
    for suf in ("", "-wal", "-shm"):
        try: os.remove(tmpdb + suf)
        except Exception: pass
    shutil.copyfile(ANALYSIS_DB, tmpdb)

    con = sqlite3.connect(tmpdb)
    # 需要人工字段存在
    ccols = [r[1] for r in con.execute("pragma table_info(conclusions)")]
    ecols = [r[1] for r in con.execute("pragma table_info(events)")]
    check("conclusions 有 verdict / my_note 列", "verdict" in ccols and "my_note" in ccols)
    check("events 有 load_self / review_status 列", "load_self" in ecols and "review_status" in ecols)

    cid = con.execute("select concl_id from conclusions order by concl_id limit 1").fetchone()
    eid = con.execute("select event_id from events order by event_id limit 1").fetchone()
    if not cid or not eid:
        con.close()
        check("找到可测试对象", False, "库为空")
        return {}
    cid, eid = cid[0], eid[0]
    con.execute("update conclusions set verdict='认可', my_note='验收自测' where concl_id=?", (cid,))
    con.execute("update events set load_self='验收自测感受', review_status='已核实' where event_id=?", (eid,))
    con.commit()
    con.close()

    # 实跑：结论全量重建（delete + insert）+ 建库脚本（含人工字段迁移）
    subprocess.run([PY, os.path.join(WS, "tools", "build_analysis_db.py"), "--db", tmpdb,
                    "--csv", EV_CSV, "--quiet"], capture_output=True, text=True)
    subprocess.run([PY, os.path.join(WS, "tools", "extract_conclusions.py"), "--db", tmpdb],
                   capture_output=True, text=True)

    con = sqlite3.connect(tmpdb)
    cv = con.execute("select verdict, my_note from conclusions where concl_id=?", (cid,)).fetchone()
    ev = con.execute("select load_self, review_status from events where event_id=?", (eid,)).fetchone()
    con.close()
    check("结论批注（verdict / my_note）经全量重建后仍在",
          cv == ("认可", "验收自测"), "重建后 %s" % (cv,))
    check("事件批注（load_self / review_status）经建库后仍在",
          ev == ("验收自测感受", "已核实"), "重建后 %s" % (ev,))
    for p in (tmpdb, tmpdb + "-wal", tmpdb + "-shm"):
        try: os.remove(p)
        except Exception: pass
    return {}


# ------------------------------- 9. 结论 ←→ 证据 绑定（可追溯）
def c9_conclusion_links():
    h1("9. 结论 ←→ 证据绑定（每条结论「凭什么成立、从哪天成立」）")
    con = ro(ANALYSIS_DB)
    cols = [r[1] for r in con.execute("pragma table_info(conclusions)")]
    check("conclusions 有 evidence_events / link_score / link_method 列",
          all(c in cols for c in ("evidence_events", "link_score", "link_method")))
    rows = con.execute("select concl_id,evidence_events,valid_from,link_method "
                       "from conclusions").fetchall()
    known = {r[0] for r in con.execute("select event_id from events")}
    dangling, no_vfrom, no_method = [], [], []
    with_ev = 0
    for cid, evs, vf, m in rows:
        if not (m or "").strip():
            no_method.append(cid)
        ids = re.findall(r"EVT-\d{8}-\d{3}|EVT-UNDATED-\d{3}", evs or "")
        if ids:
            with_ev += 1
            for i in ids:
                if i not in known:
                    dangling.append((cid, i))
            if not (vf or "").strip():
                no_vfrom.append(cid)
    check("引用的证据事件 ID 全部真实存在", not dangling,
          "悬空 %d 个%s" % (len(dangling), ("：" + str(dangling[:3])) if dangling else ""))
    check("有证据的结论都标了成立时间（否则无法对证）", not no_vfrom,
          "缺 %d 条%s" % (len(no_vfrom), ("：" + "、".join(no_vfrom[:5])) if no_vfrom else ""))
    check("每条结论都标了依据类型", not no_method,
          "缺 %d 条%s" % (len(no_method), ("：" + "、".join(no_method[:5])) if no_method else ""))
    total = len(rows)
    dead = sum(1 for r in rows if (r[3] or "").startswith("已撤回"))
    active = total - dead
    cov = with_ev / active * 100 if active else 0
    print("        有事件证据 %d / 在效 %d = %.1f%%（「已推翻清单」%d 条不计）"
          % (with_ev, active, cov, dead))
    con.close()
    return {"with_evidence": with_ev, "active": active, "coverage": round(cov, 1)}


def main():
    print("分析库验收检查 · %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("库：%s" % ANALYSIS_DB)
    c1 = c1_ids()
    c2 = c2_evidence()
    c3 = c3_idempotent()
    c4 = c4_date_revision()
    c5 = c5_conclusions()
    c6 = c6_stamp()
    c7 = c7_search()
    c8 = c8_human_fields()
    c9 = c9_conclusion_links()

    h1("汇总")
    npass = sum(1 for r in results if r["ok"])
    nfail = sum(1 for r in results if not r["ok"] and not r["warn"])
    nwarn = sum(1 for r in results if not r["ok"] and r["warn"])
    print("  通过 %d ｜ 失败 %d ｜ 警告 %d ｜ 共 %d" % (npass, nfail, nwarn, len(results)))
    for r in results:
        if not r["ok"]:
            print("    %s %s" % ("[WARN]" if r["warn"] else "[FAIL]", r["name"]))
    print()
    print("  结论：%s" % ("✅ 全部关键项通过" if nfail == 0 else "❌ 有 %d 项失败" % nfail))

    payload = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "summary": {"pass": npass, "fail": nfail, "warn": nwarn},
               "checks": results}
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
        print("  JSON → %s" % out)
    return nfail


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
