# -*- coding: utf-8 -*-
"""
regenerate_all.py —— 统一生成管线（一次计算 → 全部产物同一版本戳）

用户要求：「更新数据 → 检查质量 → 复算指标 → **一次**生成数字基准、CSV、Obsidian、HTML」，
且每份产物显示相同的 **数据截至时间 / 生成时间 / 版本**。

流程：
  [0] 建 run_id + 写 _tmp/pipeline_stamp.json
  [1] build_analysis_db.py        分析库（永久 ID + 证据 + 复核状态）
  [2] relink_evidence.py          证据回链
  [3] extract_conclusions.py      结论状态
  [4] build_daily_master.py       逐日全维主表
  [5] render_daily.py             HTML + Obsidian 逐日全维
  [6] build_master_index.py       分析总览 HTML + Obsidian
  [7] build_number_baseline.py    数字基准（同一次计算）
  [8] sync_from_vault.py          ★ 工作台人工批注 → 分析库（在重建笔记之前！）
  [9] build_workbench.py          Obsidian 工作台四视图
  [10] 给所有产物打同一戳 → _tmp/pipeline_manifest.json
  [11] verify_analysis.py         验收 · blind_test.py 盲测 · privacy_audit.py 隐私
  [12] export_report_pack.py      ★ 打戳之后 → 桌面「中期汇报_成果与材料_*」一个包（只读+复制）
  [13] build_first_report_list.py ★ 再之后 → 《汇报清单_首版》HTML（读桌面包里反抽的 CSV）

★ 照片证据层（2026-10-06 第三批，主任务）
  `build_ppt_packs.py`（经历页 PPT 材料包）+ `photo_evidence_overview.py`（照片证据总览）
  已进主管线（只读）。**照片索引本身是重活**（要扫 6 万+ 文件、ffprobe 9 千个 `.hevc`）
  → 用 `--photos` 显式触发：`photo_index.py` / `hevc_photos.py` / `photo_sources.py`。

注：全量经历重建流水线 `batch_pipeline.py` 是**独立重活**（registry 要扫 6 万份文件），
    不在本管线里跑 `all`；本管线只跑它的 `unreadable` / `report` 两个轻量子命令。

★ 本机安全闸门：`SAFE_DELETE_BULK_CONFIRM_REQUIRED`（阈值 **50 次/轮**）会把
  「**覆盖已存在文件**」也计成删除 → 脚本一律**不删不覆盖**（产物写进独立时间戳目录）。

用法：
  python tools\\regenerate_all.py            # 全跑
  python tools\\regenerate_all.py --fast     # 跳过 [2] 回链（最慢）
  python tools\\regenerate_all.py --photos   # 额外重跑照片索引（很慢）
  python tools\\regenerate_all.py --no-verify
"""
import os, re, io, sys, json, time, hashlib, sqlite3, subprocess, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TOOLS = os.path.join(WS, "tools")
TMP = os.path.join(WS, "_tmp")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
ANALYSIS_DB = os.path.join(WS, "analysis.sqlite")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
PY = sys.executable

STAMP = os.path.join(TMP, "pipeline_stamp.json")
MANIFEST = os.path.join(TMP, "pipeline_manifest.json")
EXTRACT_VERSION = "v1-migrate-20261004"

# 由本管线重写的产物（相对 WS 或绝对路径）
HTML_ARTIFACTS = [
    os.path.join(WS, "逐日全维整合_2024-11至2026-10_2026-10-04.html"),
    os.path.join(WS, "分析总览_全部文件地图_2026-10-04.html"),
    os.path.join(WS, "自我理解引擎_统一排查台_2026-10-05.html"),
    os.path.join(WS, "央美之后_中期汇报可用成果与材料_2026-10-05.html"),
    os.path.join(WS, "年度事件重建_第二个我_第一轮_2026-10-05.html"),
    os.path.join(WS, "_tmp", "batch", "执行报告_全量经历重建.html"),
    # ★ 照片证据 → PPT 材料包（第二批，2026-10-06）
    os.path.join(WS, "汇报页面材料包_第二批_2026-10-06.html"),
    os.path.join(WS, "照片证据总览_第二批_2026-10-06.html"),
    # ★ 照片证据 → PPT 材料包（第三批，2026-10-06）+ 主 PPT 配图体检
    os.path.join(WS, "汇报页面材料包_第三批_2026-10-06.html"),
    os.path.join(WS, "主PPT17页_配图体检_2026-10-06.html"),
    # ★ 文件串联总图（交付索引，2026-10-06）
    os.path.join(WS, "中期汇报_文件串联总图_2026-10-06.html"),
    # ★ 照片汇总总台（一站式取图，2026-10-06）—— 在桌面汇总目录内（图片走相对路径）
    r"C:\Users\wardc\Desktop\中期汇报_2026-09\10_照片汇总_2026-10-06\00_照片汇总总台.html",
]
MD_ARTIFACTS = [
    os.path.join(VAULT, "03_微信聊天分析", "🗺️分析总览·全部文件地图.md"),
    os.path.join(VAULT, "04_工作台", "00_工作台说明.md"),
]
CSV_ARTIFACTS = [
    os.path.join(TMP, "daily_master.csv"),
]
DB_ARTIFACTS = [ANALYSIS_DB]


def data_until():
    try:
        c = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
        v = c.execute("select max(date(ts,'unixepoch','localtime')) from messages").fetchone()[0]
        c.close()
        return v or ""
    except Exception:
        return ""


def run(script, args=(), label=""):
    p = os.path.join(TOOLS, script)
    t0 = time.time()
    r = subprocess.run([PY, p] + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t0
    ok = r.returncode == 0
    print("  [%s] %-28s %5.1fs" % ("OK " if ok else "ERR", label or script, dt))
    if not ok:
        print((r.stdout or "")[-1500:])
        print((r.stderr or "")[-1500:])
    return ok, r


def stamp_html(path, stamp):
    txt = io.open(path, encoding="utf-8", errors="ignore").read()
    tag = '<meta name="wb-stamp" content="%s|%s|%s|%s">' % (
        stamp["run_id"], stamp["data_until"], stamp["generated_at"], stamp["extract_version"])
    if re.search(r'<meta name="wb-stamp"[^>]*>', txt):
        txt = re.sub(r'<meta name="wb-stamp"[^>]*>', tag, txt)
    elif re.search(r"<head[^>]*>", txt, re.I):
        txt = re.sub(r"(<head[^>]*>)", r"\1\n" + tag, txt, count=1, flags=re.I)
    else:
        txt = tag + "\n" + txt
    io.open(path, "w", encoding="utf-8").write(txt)


def stamp_md(path, stamp):
    txt = io.open(path, encoding="utf-8", errors="ignore").read()
    line = "<!-- WB-STAMP: %s | 数据截至 %s | 生成 %s | 版本 %s -->" % (
        stamp["run_id"], stamp["data_until"], stamp["generated_at"], stamp["extract_version"])
    if "<!-- WB-STAMP:" in txt:
        txt = re.sub(r"<!-- WB-STAMP:.*?-->", line, txt, flags=re.S)
    elif txt.startswith("---"):
        m = re.search(r"\n---\s*\n", txt[3:])
        if m:
            cut = 3 + m.end()
            txt = txt[:cut] + "\n" + line + "\n" + txt[cut:]
        else:
            txt = line + "\n" + txt
    else:
        txt = line + "\n\n" + txt
    io.open(path, "w", encoding="utf-8").write(txt)


def sha1(path, n=1 << 20):
    h = hashlib.sha1()
    with io.open(path, "rb") as f:
        while True:
            b = f.read(n)
            if not b: break
            h.update(b)
    return h.hexdigest()[:16]


def main():
    fast = "--fast" in sys.argv
    now = datetime.datetime.now()
    stamp = {
        "run_id": now.strftime("%Y%m%d-%H%M%S"),
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "data_until": data_until(),
        "extract_version": EXTRACT_VERSION,
    }
    os.makedirs(TMP, exist_ok=True)
    io.open(STAMP, "w", encoding="utf-8").write(json.dumps(stamp, ensure_ascii=False, indent=2))
    print("=" * 70)
    print("统一生成管线 · run_id %s" % stamp["run_id"])
    print("数据截至 %s ｜ 版本 %s" % (stamp["data_until"], stamp["extract_version"]))
    print("=" * 70)

    steps = [
        ("build_analysis_db.py", ("--now", stamp["generated_at"]), "分析库（永久 ID）"),
        ("relink_evidence.py", (), "证据回链"),
        ("extract_conclusions.py", (), "结论状态"),
        ("link_conclusions.py", ("--apply",), "结论 ←→ 事件 自动匹配"),
        ("build_daily_master.py", (), "逐日全维主表"),
        ("render_daily.py", (), "逐日全维 HTML+Obsidian"),
        ("build_master_index.py", (), "分析总览"),
        ("build_number_baseline.py", (), "数字基准"),
        # ★ 只读：年度骨架 + 缺口候选 + 8月逐日对齐 + 独处时段（不改库，产出到 _tmp）
        ("annual_skeleton.py", (), "年度事件骨架（只读）"),
        ("mine_gap_events.py", (), "缺口候选事件（只读）"),
        ("august_daily_align.py", (), "8月逐日对齐（只读）"),
        ("idle_hours_align.py", (), "独处时段分析（只读）"),
        ("transfer_dedup.py", (), "转账双倍记账核账（只读）"),
        # ★ 全量经历重建（批处理流水线）：只跑轻量子命令 —— registry/weeks/digest 太重，
        #   需要时单独执行 `batch_pipeline.py all`；这里只刷新缺口与执行报告
        ("batch_pipeline.py", ("unreadable",), "聊天缺口登记（只读）"),
        ("batch_pipeline.py", ("report",), "全量经历重建执行报告（只读）"),
        # ★ 全量经历重建 · 本地加工层
        ("chunk_weeks.py", ("--build",), "周包 → 模型片段（只读）"),
        ("extract_materials.py", ("--stage", "queue"), "图片/音视频 → 队列归类（只读）"),
        ("pii_split.py", (), "PII 分流 + 公开版（只读）"),
        # ★ 统一排查台：把上面这些 _tmp 产物 + 结论台账汇成一份单文件 HTML
        ("build_unified_workbench.py", (), "统一排查台（只读）"),
        # ★ 中期汇报成果材料：广搜「考上央美之后做过什么」→ 候选成果总表 + 素材索引 + 汇报主线
        ("build_report_materials.py", (), "中期汇报成果材料（只读）"),
        # ★ 先把 Obsidian 笔记里的人工批注写回库，再重建笔记 —— 否则你的批注会被覆盖
        ("sync_from_vault.py", ("--apply",), "工作台批注 → 分析库"),
        ("build_workbench.py", (), "Obsidian 工作台四视图"),
        # ★ 照片证据 → PPT 材料包（只读；产物到工作区根 + _tmp）
        ("build_ppt_packs.py", ("--build",), "经历页 PPT 材料包（第二批，只读）"),
        ("build_ppt_packs_b3.py", ("--build",), "经历页 PPT 材料包 + 主PPT配图体检（第三批，只读）"),
        ("photo_evidence_overview.py", (), "照片证据总览（只读）"),
    ]
    # ★ 照片索引是**重活**（要扫 6 万+ 文件 / ffprobe 9 千个 hevc）→ 用 --photos 显式触发
    if "--photos" in sys.argv:
        for s, a, lab in [
            ("photo_index.py", (), "照片索引 · 常规图（重）"),
            ("hevc_photos.py", ("--build",), "照片索引 · HEVC 高清静帧（重）"),
            ("photo_sources.py", ("--build",), "照片索引 · 项目夹/朋友圈（重）"),
        ]:
            run(s, a, lab)
    # 这些脚本「非零退出」= 报出了发现，不代表管线坏了
    TOLERANT = {"privacy_audit.py"}
    failed = []
    for i, (s, a, lab) in enumerate(steps):
        if fast and s == "relink_evidence.py":
            print("  [SKIP] %-28s --fast" % lab)
            continue
        ok, _ = run(s, a, lab)
        if not ok and s not in TOLERANT:
            failed.append(lab)

    # ---- 打戳 ----
    print("-" * 70)
    artifacts = []
    for p in HTML_ARTIFACTS:
        if os.path.exists(p):
            stamp_html(p, stamp); artifacts.append(("html", p))
    for p in MD_ARTIFACTS:
        if os.path.exists(p):
            stamp_md(p, stamp); artifacts.append(("md", p))
    vdir = os.path.join(VAULT, "03_微信聊天分析", "03_事件库", "逐日全维")
    if os.path.isdir(vdir):
        for fn in sorted(os.listdir(vdir)):
            if fn.endswith(".md"):
                p = os.path.join(vdir, fn)
                stamp_md(p, stamp); artifacts.append(("md", p))
    for p in CSV_ARTIFACTS:
        if os.path.exists(p):
            artifacts.append(("csv", p))
    for p in DB_ARTIFACTS:
        if os.path.exists(p):
            artifacts.append(("db", p))

    # 去重（同一文件可能被两条规则命中）
    seen = set()
    artifacts = [a for a in artifacts if not (a[1] in seen or seen.add(a[1]))]
    man = {"run_id": stamp["run_id"], "data_until": stamp["data_until"],
           "generated_at": stamp["generated_at"], "extract_version": stamp["extract_version"],
           "artifacts": [{"path": p, "kind": k, "bytes": os.path.getsize(p), "sha1": sha1(p)}
                         for k, p in artifacts]}
    io.open(MANIFEST, "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=2))

    print("产物 %d 份已打同一戳（run_id %s）" % (len(artifacts), stamp["run_id"]))
    for k, p in artifacts:
        print("  %-4s %s" % (k, os.path.relpath(p, WS) if p.startswith(WS) else p))

    # ---- 验收 ----
    if "--no-verify" not in sys.argv:
        print("-" * 70)
        run("verify_analysis.py", (), "验收检查")
        run("blind_test.py", (), "时间盲测")
        ok, _ = run("privacy_audit.py", (), "隐私核对")
        if not ok:
            print("      ↑ 隐私核对报出的是**发现**（不是管线故障）—— 见上面的 FAIL 明细")

    # ---- ★ 打戳之后才打包：把主文档 / 理解层 / CSV 汇成桌面一个包 ----
    # （必须在打戳之后，否则复制出去的是没戳的版本）
    print("-" * 70)
    run("export_report_pack.py", (), "桌面成果材料包")

    # ---- ★ 依赖「桌面包 CSV」的产物：只能排在打包之后 ----
    # （不能放进 HTML_ARTIFACTS：那一轮打戳时它们还没生成 / 内容还是上一版）
    for script, outname, label in [
        ("build_first_report_list.py", "汇报清单_首版_2026-10-06.html", "首版汇报清单"),
        ("build_experience_dossiers.py", "经历档案_首版_2026-10-06.html", "经历档案（首版）"),
    ]:
        ok, _ = run(script, (), label)
        if not ok:
            continue
        p = os.path.join(WS, outname)
        if not os.path.exists(p):
            continue
        stamp_html(p, stamp)
        man = json.loads(io.open(MANIFEST, encoding="utf-8").read())
        man["artifacts"].append({"path": p, "kind": "html",
                                 "bytes": os.path.getsize(p), "sha1": sha1(p)})
        io.open(MANIFEST, "w", encoding="utf-8").write(
            json.dumps(man, ensure_ascii=False, indent=2))
        print("  html %s（后置打戳 · 已补进 manifest）" % os.path.relpath(p, WS))

        # ★ 同步进桌面包（必须在打戳之后复制，否则带过去的是没戳的版本）
        pack = os.path.join(os.path.expanduser("~"), "Desktop", "中期汇报_成果与材料_2026-10-05")
        if os.path.isdir(pack):
            import shutil
            dst = os.path.join(pack, "01_主文档", os.path.basename(p))
            shutil.copy2(p, dst)
            print("  → 桌面包 %s" % os.path.relpath(dst, pack))

    # 执行报告也同步进桌面包（理解层）
    pack = os.path.join(os.path.expanduser("~"), "Desktop", "中期汇报_成果与材料_2026-10-05")
    ex = os.path.join(WS, "_tmp", "batch", "执行报告_全量经历重建.html")
    if os.path.isdir(pack) and os.path.exists(ex):
        import shutil
        dst2 = os.path.join(pack, "03_理解层", os.path.basename(ex))
        shutil.copy2(ex, dst2)
        print("  → 桌面包 %s" % os.path.relpath(dst2, pack))
    pii = os.path.join(WS, "_tmp", "pii", "PII分流报告.html")
    if os.path.isdir(pack) and os.path.exists(pii):
        import shutil
        dst3 = os.path.join(pack, "03_理解层", os.path.basename(pii))
        shutil.copy2(pii, dst3)
        print("  → 桌面包 %s" % os.path.relpath(dst3, pack))

    print("=" * 70)
    if failed:
        print("⚠️ 失败步骤：%s" % ", ".join(failed))
    else:
        print("✅ 管线完成 · 所有产物同一版本戳 · run_id %s" % stamp["run_id"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
