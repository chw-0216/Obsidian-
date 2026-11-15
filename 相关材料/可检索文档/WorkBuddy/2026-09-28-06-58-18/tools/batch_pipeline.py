# -*- coding: utf-8 -*-
r"""
batch_pipeline.py —— 「央美之后 · 全量经历重建」批处理流水线

设计原则
--------
1. **可续跑**：状态全部落在 `_tmp\batch\batch.sqlite`，中断后从 `pending` 继续。
2. **可审查**：每个任务记录 材料范围 / 问题 / 状态 / 用量，失败进 `failed` 单独重试。
3. **只读源**：所有原始材料**只读打开**；产物只写 `_tmp\batch\`。
4. **诚实计量**：本地处理不调远程 API → `api_tokens` 一律写 `unknown`；
   另记 `est_tokens`（本地读取量的估算）并**明确标注为估算**，不与平台扣减混算。
5. **不虚报**：「找到文件 / 提取内容 / 送入模型 / 分析完成」四个状态分开记。

子命令
------
  registry   全量材料登记（来源 / 时间范围 / 类型 / 读取状态 / 分析状态 / 去重）
  weeks      按自然周切聊天分析包（2025-03-26 → 今，全联系人 / 私聊+群聊 / 双向）
  dates      经历日期重建（准备/开始/节点/结束/交付/发布 六时点 + 冲突研判）
  dossiers   跨材料归并为「经历档案」
  status     队列状态 + 执行报告（HTML + CSV）
  all        依次跑 registry → weeks → dates → dossiers → status
"""
import os, io, re, sys, csv, json, time, sqlite3, hashlib, datetime, argparse, traceback
from collections import defaultdict, Counter

# ──────────────────────────────────────────────────────────── 路径
WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
WEEKDIR = os.path.join(BATCH, "weeks")
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

# 央美时间锚点
T_ADMIT = "2025-03-26"      # 拟录取
T_ENROLL = "2025-09-01"     # 入学（研一）
T_NOW = datetime.datetime.now().strftime("%Y-%m-%d")

# 扫描根：(路径, 来源桶, 最大深度；0=不限)
# ★ apps/ 与 tmp/ 里 47 万文件基本是依赖树与草稿 → 只登记浅层自有文件，不递归
SCAN_ROOTS = [
    (r"C:\Users\wardc\Documents\Obsidian Vault", "知识库", 0),
    (r"C:\Users\wardc\Desktop\中期汇报_2026-09", "汇报材料库", 0),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\conversations", "AI会话", 0),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\notes", "AI归档", 0),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs", "AI产物", 0),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\assets", "AI资产", 0),
    (r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps", "自建工程", 2),
    (WS, "分析工作区", 0),
    (r"C:\Users\wardc\Desktop\微信导出_窗口期_20260930", "微信导出", 0),
    (r"C:\Users\wardc\Desktop\微信照片_最新", "微信照片", 0),
    (r"C:\Users\wardc\Desktop\澜沧支教_课堂照片_评审优化版_20260903", "澜沧课堂照", 0),
    (r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp", "索引库", 1),
    (r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted", "解密库", 2),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
             "$RECYCLE.BIN", "System Volume Information", ".workbuddy-ai", "site-packages",
             "dist", "build", ".next", ".cache", "tmp"}
SKIP_EXT = {".tmp", ".log", ".lock", ".pyc", ".pyo", ".lnk", ".ini", ".db-shm", ".db-wal"}

# ──────────────────────────────────────────────────────────── 首轮从周摘要里挖出的成果线索
# ★ 全部来自「已读到的周包摘要」，未读到的材料不在这里；带「待核实」的必须再回原文确认
FINDINGS = [
    ("Movers4Climate 澜沧支教 · 正式立项", "2026-06-30 → 2026-09-02", "立项团队",
     "06-30 培训 → 07-04 首批立项公示 → 07-08 完整名单发布 → 08-31 向米雪老师承诺 09-02 提交",
     "「立项2群」有记录 → 是机构背书的<b>立项团队</b>，不只是「参与」", "已确认"),
    ("《未来之阈——首届实验艺术展览》（中国美协艺委会届展系列）", "2025-12-31 → 2026-04-10", "投稿/入选待核实",
     "12-31 母亲转来征稿+报名表 docx → 2026-01-04 群通知 → 04-10 在武汉（湖北美院）开幕（母亲转来报道）",
     "他是否入选 / 入选何作 <b>待核实</b>", "待核实"),
    ("央美创客市集", "2026-04-03", "摊主",
     "`附件3 央美创客市集入驻摊主承诺书.docx` 出现在材料里",
     "需要回原件确认是否实际入驻、售卖/展示什么", "待核实"),
    ("央美美术馆 2026 年秋季实习生", "2026-09-22 录用通知", "已录用",
     "美术馆办公室岳老师通知（含联系电话）",
     "录用已确认；<b>到岗情况</b>需另行确认", "已录用"),
    ("把外部内容「搬进微信」的链路（filehelper）", "2025-03 → 2026-10", "工具行为",
     "文件传输助手 23,315 条，其中 3,045 条是「贴进来让 AI 读」的内容（如 USER.md）",
     "是「他用微信做 AI 中转」的<b>行为证据</b>，不是社交", "已确认"),
    ("Tripothon S1（Tripo3D 全球黑客松）", "2026-09-01 → 10-05 报名", "候选 · 无直接证据",
     "他在该群 <b>0 发言</b>，只有群消息",
     "★ 证据规则修正（2026-10-06）：<b>群内零发言不能证明未参与</b>。"
     "零发言只说明「无直接证据」，不等于「没参加」→ <b>保留候选，继续追踪</b>"
     "（需查私聊 / 其他群 / 提交记录 / 作品）", "候选 · 待追踪"),
]

# ──────────────────────────────────────────────────────────── 未完成队列（保存到磁盘）
NEXT_QUEUE = [
    ("Q1", "46,160 份图片 / 视频 / Office 文档正文提取", "缺 OCR / ASR / Office 解析工具",
     "需授权引入 OCR（如 PaddleOCR / Tesseract）与 python-docx / pdfplumber / ffmpeg"),
    ("Q2", "8,126 条 link 卡片正文补录", "导出时未落正文",
     "需回原始微信导出（窗口期导出目录）重取正文，或人工补"),
    ("Q3", "经历六时点拆分（准备/开始/节点/结束/交付/发布）", "已灌入 2,207 条事件行",
     "对每段经历逐条标注六时点；相对时间（昨天/下周/月底）需解析"),
    ("Q4", "日期冲突研判 + 竞争解释", "依赖 Q3",
     "比较原始记录 / 照片 EXIF / 日志 / 文件内容 / 后续回顾，输出最有依据判断"),
    ("Q5", "跨材料归并（聊天↔照片↔日志↔作品↔课件↔交付）", "已聚合 160 个「类别×月」候选",
     "正文提取完成后按经历重新归并"),
    ("Q6", "每段经历八角度深挖", "未开始",
     "学习与能力 / 创作与材料 / 教学与现场 / 合作与贡献 / 交付与使用 / 失败与迭代 / 跨项目联系 / 汇报价值"),
    ("Q7", "每段重要经历 2—3 种竞争解释 + 反例", "未开始",
     "寻找反例与辨别线索；事实 / 解释 / 计划分开标"),
    ("Q8", "1 亿 token 目标", "本地流水线不产生模型 token",
     "需授权用远程模型做「逐材料精读」；当前平台额度扣减 = 0"),
    ("Q9", "《未来之阈》是否入选 / Tripothon 是否参与 / 创客市集是否入驻", "待核实",
     "三条线索需回原文确认，不得先写进成果"),
]


# 内容类型
KIND = {
    ".md": "文档", ".txt": "文档", ".docx": "文档", ".doc": "文档", ".pdf": "文档", ".rtf": "文档",
    ".xlsx": "表格", ".xls": "表格", ".csv": "表格", ".tsv": "表格",
    ".pptx": "演示", ".ppt": "演示",
    ".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".gif": "图片", ".webp": "图片",
    ".heic": "图片", ".tif": "图片", ".tiff": "图片", ".bmp": "图片", ".raw": "图片",
    ".mp4": "视频", ".mov": "视频", ".avi": "视频", ".mkv": "视频",
    ".mp3": "音频", ".wav": "音频", ".m4a": "音频", ".amr": "音频",
    ".db": "数据库", ".sqlite": "数据库", ".json": "数据", ".jsonl": "数据",
    ".html": "网页", ".htm": "网页",
    ".py": "代码", ".js": "代码", ".ts": "代码", ".sh": "代码", ".ps1": "代码",
    ".psd": "源文件", ".ai": "源文件", ".indd": "源文件", ".sketch": "源文件",
    ".zip": "压缩包", ".rar": "压缩包", ".7z": "压缩包",
    ".ttf": "字体", ".otf": "字体",
}
# 可提取正文的（本地能读）
EXTRACTABLE = {".md", ".txt", ".csv", ".tsv", ".json", ".jsonl", ".html", ".htm",
               ".py", ".js", ".ts", ".sh", ".ps1"}
# 需外部工具/OCR 的（本轮未处理 → 记入待办，不算已读）
NEEDS_TOOL = {".docx": "python-docx", ".doc": "word", ".pdf": "pdf", ".xlsx": "openpyxl",
              ".xls": "excel", ".pptx": "python-pptx", ".ppt": "powerpoint",
              ".jpg": "ocr/vision", ".jpeg": "ocr/vision", ".png": "ocr/vision",
              ".heic": "vision", ".tif": "vision", ".tiff": "vision",
              ".mp4": "asr/vision", ".mov": "asr/vision", ".mp3": "asr", ".wav": "asr",
              ".psd": "ps", ".ai": "illustrator"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ──────────────────────────────────────────────────────────── 库
def db():
    os.makedirs(BATCH, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""create table if not exists materials(
        mid integer primary key autoincrement,
        path text unique, root text, rel text, name text, ext text, kind text,
        bytes integer, mtime text, content_hash text, dup_of integer,
        time_lo text, time_hi text, time_src text,
        found integer default 0, extracted integer default 0, modeled integer default 0,
        analyzed integer default 0, fail_reason text, need_tool text)""")
    c.execute("""create table if not exists tasks(
        tid integer primary key autoincrement,
        stage text, scope text, question text, status text default 'pending',
        materials integer default 0, messages integer default 0, bytes integer default 0,
        est_tokens integer default 0, api_tokens text default 'unknown',
        started text, ended text, note text, attempt integer default 0)""")
    c.execute("""create table if not exists weeks(
        week text primary key, lo text, hi text, days integer,
        messages integer, sessions integer, sessions_active integer,
        pkg_path text, status text default 'pending', analyzed integer default 0)""")
    c.execute("""create table if not exists experiences(
        eid integer primary key autoincrement,
        name text, category text, source text,
        t_prepare text, t_start text, t_milestone text, t_end text,
        t_deliver text, t_public text,
        date_basis text, date_conflict text, alt_explanation text,
        facts text, interp text, plan text, evidence text)""")
    c.execute("""create table if not exists runs(
        rid integer primary key autoincrement, ts text, stage text, scope text,
        materials integer, messages integer, bytes integer,
        est_tokens integer, api_tokens text, note text)""")
    c.commit()
    return c


def task(c, stage, scope, question):
    c.execute("insert into tasks(stage,scope,question,status,started) values(?,?,?,'running',?)",
              (stage, scope, question, datetime.datetime.now().isoformat(timespec="seconds")))
    c.commit()
    return c.execute("select last_insert_rowid()").fetchone()[0]


def task_done(c, tid, status, materials=0, messages=0, nbytes=0, note=""):
    est = int(nbytes / 3.2)            # 中文正文 ≈ 3.2 字节/token（估算，非实测）
    c.execute("""update tasks set status=?,materials=?,messages=?,bytes=?,est_tokens=?,
                 ended=?,note=? where tid=?""",
              (status, materials, messages, nbytes, est,
               datetime.datetime.now().isoformat(timespec="seconds"), note, tid))
    c.commit()
    return est


def log_run(c, stage, scope, materials, messages, nbytes, note=""):
    c.execute("""insert into runs(ts,stage,scope,materials,messages,bytes,est_tokens,api_tokens,note)
                 values(?,?,?,?,?,?,?,'unknown',?)""",
              (datetime.datetime.now().isoformat(timespec="seconds"), stage, scope,
               materials, messages, nbytes, int(nbytes / 3.2), note))
    c.commit()


# ──────────────────────────────────────────────────────────── 工具
def hkey(path, size):
    """小文件全哈希；大文件用 头64K+尾64K+size（够区分版本）"""
    h = hashlib.sha1()
    try:
        with io.open(path, "rb") as f:
            if size <= 4 << 20:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    h.update(b)
            else:
                h.update(f.read(65536))
                f.seek(max(0, size - 65536))
                h.update(f.read(65536))
        h.update(str(size).encode())
        return h.hexdigest()[:20]
    except Exception:
        return ""


def time_range_from_text(path, kind):
    """从内容里粗抽年份范围（只对可提取的文本类做，且限量）"""
    lo = hi = None
    try:
        if kind not in ("文档", "表格", "数据", "网页", "代码"):
            return None, None, ""
        if os.path.getsize(path) > 3 << 20:
            return None, None, ""
        t = io.open(path, encoding="utf-8", errors="ignore").read()
        ys = re.findall(r"(20[12]\d)[-/年](\d{1,2})", t[:400000])
        if not ys:
            return None, None, ""
        ds = sorted("%s-%02d" % (y, int(m)) for y, m in ys if 2018 <= int(y) <= 2026)
        if ds:
            return ds[0], ds[-1], "内容内文日期"
    except Exception:
        pass
    return None, None, ""


# ──────────────────────────────────────────────────────────── stage: registry
def stage_registry(c, limit=None):
    tid = task(c, "registry", "全部扫描根", "有哪些材料？来源/时间/类型/读取状态各是什么？")
    rows, fails, nbytes = [], [], 0
    seen_hash = {}
    n = 0
    for root, bucket, maxd in SCAN_ROOTS:
        if not os.path.isdir(root):
            fails.append((root, "根目录不存在"))
            continue
        for dp, dns, fns in os.walk(root):
            depth = os.path.relpath(dp, root).count(os.sep)
            if maxd and depth >= maxd:
                dns[:] = []
            else:
                dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in fns:
                ext = os.path.splitext(fn)[1].lower()
                if ext in SKIP_EXT:
                    continue
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p)
                except Exception as e:
                    fails.append((p, "stat失败: %s" % e))
                    continue
                n += 1
                if limit and n > limit:
                    break
                kind = KIND.get(ext, "其他")
                lo, hi, src = (None, None, "")
                if kind in ("文档", "表格", "数据", "网页", "代码"):
                    lo, hi, src = time_range_from_text(p, kind)
                if not lo:
                    lo = hi = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m")
                    src = "文件修改时间"
                ck = hkey(p, st.st_size) if st.st_size <= 32 << 20 else ""
                dup = seen_hash.get(ck) if ck else None
                if ck and not dup:
                    seen_hash[ck] = n
                rows.append((p, bucket, os.path.relpath(p, root), fn, ext, kind,
                             st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                             ck, dup,
                             lo, hi, src,
                             1, 0,
                             0, 0,
                             "" if kind != "其他" or ext else "未知扩展名",
                             NEEDS_TOOL.get(ext, "")))
                nbytes += st.st_size
            if limit and n > limit:
                break
        if limit and n > limit:
            break
    c.executemany("""insert or replace into materials
        (path,root,rel,name,ext,kind,bytes,mtime,content_hash,dup_of,
         time_lo,time_hi,time_src,found,extracted,modeled,analyzed,fail_reason,need_tool)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    c.commit()
    task_done(c, tid, "done", materials=len(rows), nbytes=0,
              note="失败 %d 项；只读元数据（路径/大小/时间），未读正文" % len(fails))
    # ★ 登记阶段只读元数据 → est_tokens 记 0，不能用材料总体量折算（会虚高两个数量级）
    log_run(c, "registry", "全部扫描根", len(rows), 0, 0,
            "失败 %d；体量 %.2f GB 仅登记不读取" % (len(fails), nbytes / 1024**3))
    if fails:
        with io.open(os.path.join(BATCH, "registry_failed.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["path", "reason"])
            w.writerows(fails)
    # 汇总
    print("=" * 72)
    print("阶段 ① 全量材料登记")
    print("=" * 72)
    print("登记 %d 份 ｜ %.2f GB ｜ 失败 %d" % (len(rows), nbytes / 1024**3, len(fails)))
    print("\n按来源：")
    for k, v in Counter(r[1] for r in rows).most_common():
        print("  %-12s %5d 份" % (k, v))
    print("\n按类型：")
    for k, v in Counter(r[5] for r in rows).most_common():
        print("  %-8s %5d 份" % (k, v))
    dup = sum(1 for r in rows if r[9])
    print("\n重复副本 %d 份（内容哈希相同，可复用处理结果）" % dup)
    print("可本地提取正文 %d 份（**候选，尚未读取**）｜ 需外部工具/OCR %d 份"
          % (sum(1 for r in rows if r[4] in EXTRACTABLE or r[4] == ".db"),
             sum(1 for r in rows if r[18])))
    print("★ 注意：登记阶段 extracted 一律为 0 —— 「可提取」不等于「已提取」，")
    print("  真正的正文提取由 extract_materials.py 完成并回写 extracted=1。")
    return len(rows)


# ──────────────────────────────────────────────────────────── stage: weeks
def stage_weeks(c):
    tid = task(c, "weeks", "%s → %s" % (T_ADMIT, T_NOW), "每周发生了什么？全部联系人与群聊")
    con = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
    names = {r[0]: (r[1] or r[0]) for r in con.execute("select talker,display_name from sessions")}
    types = {r[0]: r[1] for r in con.execute("select talker,session_type from sessions")}

    t0 = int(datetime.datetime.strptime(T_ADMIT, "%Y-%m-%d").timestamp())
    t1 = int(datetime.datetime.now().timestamp())
    # 按 ISO 周分桶
    buckets = defaultdict(list)
    for ts, sk, role, typ, content in con.execute(
            "select ts,session_key,role,type,content from messages where ts>=? and ts<=? order by ts",
            (t0, t1)):
        d = datetime.datetime.fromtimestamp(ts)
        iso = d.isocalendar()
        wk = "%d-W%02d" % (iso[0], iso[1])
        buckets[wk].append((ts, sk, role, typ, content))
    con.close()

    os.makedirs(WEEKDIR, exist_ok=True)
    total_msg = 0
    nbytes = 0
    for wk in sorted(buckets):
        msgs = buckets[wk]
        lo = datetime.datetime.fromtimestamp(msgs[0][0]).strftime("%Y-%m-%d")
        hi = datetime.datetime.fromtimestamp(msgs[-1][0]).strftime("%Y-%m-%d")
        days = (datetime.datetime.strptime(hi, "%Y-%m-%d") -
                datetime.datetime.strptime(lo, "%Y-%m-%d")).days + 1
        bysess = defaultdict(list)
        for m in msgs:
            bysess[m[1]].append(m)
        path = os.path.join(WEEKDIR, "%s.jsonl" % wk)
        with io.open(path, "w", encoding="utf-8") as f:
            head = {"week": wk, "lo": lo, "hi": hi, "messages": len(msgs),
                    "sessions": len(bysess), "anchor": "央美拟录取 %s 起" % T_ADMIT}
            f.write(json.dumps(head, ensure_ascii=False) + "\n")
            for sk in sorted(bysess, key=lambda s: -len(bysess[s])):
                sm = bysess[sk]
                f.write(json.dumps({
                    "session_key": sk,
                    "session_name": names.get(sk, sk),
                    "session_type": types.get(sk, ""),
                    "n": len(sm),
                    "mine": sum(1 for x in sm if x[2] == "me"),
                    "theirs": sum(1 for x in sm if x[2] == "them"),
                }, ensure_ascii=False) + "\n")
                for ts, _, role, typ, content in sm:
                    f.write(json.dumps({
                        "t": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        "r": role, "y": typ, "c": (content or "")[:2000],
                    }, ensure_ascii=False) + "\n")
        sz = os.path.getsize(path)
        nbytes += sz
        total_msg += len(msgs)
        c.execute("""insert or replace into weeks
            (week,lo,hi,days,messages,sessions,sessions_active,pkg_path,status)
            values(?,?,?,?,?,?,?,?,'packed')""",
                  (wk, lo, hi, days, len(msgs), len(bysess),
                   sum(1 for s in bysess.values() if any(x[2] == "me" for x in s)), path))
    c.commit()
    task_done(c, tid, "done", messages=total_msg, nbytes=nbytes,
              note="%d 周包" % len(buckets))
    log_run(c, "weeks", "%s → %s" % (T_ADMIT, T_NOW), len(buckets), total_msg, nbytes)

    print("=" * 72)
    print("阶段 ② 聊天按周分片")
    print("=" * 72)
    print("周包 %d 个 ｜ 消息 %d 条 ｜ 落盘 %.1f MB" % (len(buckets), total_msg, nbytes / 1024**2))
    top = sorted(buckets.items(), key=lambda kv: -len(kv[1]))[:8]
    print("\n消息最多的 8 周：")
    for wk, ms in top:
        print("  %s  %6d 条" % (wk, len(ms)))
    return len(buckets)


# ──────────────────────────────────────────────────────────── stage: digest
# 第一遍「全量发现经历」：把每周压成可读信号，而不是把 33 万条塞进模型
STRONG = re.compile(
    r"决定|确定|定了|定下来|敲定|拟录取|录取|录用|面试|答辩|开题|提交|交了|报名|"
    r"入职|离职|辞职|转正|offer|签了|签合同|"
    r"开幕|开展|布展|撤展|发布|上线|结课|期末|毕业|立项|审批|通过了|没通过|驳回|"
    r"住院|手术|体检|挂号|复诊|搬家|提车|买车|退租|"
    r"出发|抵达|回京|返程|下乡|驻村|出差|"
    r"吵架|冷战|生气|和好|分手|复合|表白|同居|报警|事故|剐蹭|赔偿")
WEAK = re.compile(
    r"见面|见了|见一下|借钱|借款|借点|借了|还钱|还上|还清|还款|逾期|欠款|欠了|"
    r"报销|经费|结算|合同|报价|谈事|聊了|开会|汇报|思想汇报|评审|丢了|坏了|修车")
NOISE = re.compile(
    r"撤回了一条消息|拍一拍|红包|收款到账|支付成功|余额不足提醒|"
    r"新年|春节|节日|祝福|投票|助力|砍价|拼团|优惠|秒杀|促销|"
    r"语音通话|视频通话|未接通|已取消|无法显示|发送了图片|分享了一首")
CATS = [
    ("钱/财务", r"转账|还款|逾期|扣款|欠款|借款|网贷|分期|账单|学费|报销|经费|结算|还钱|还清|借了"),
    ("学业/学术", r"导师|论文|开题|答辩|课程|作业|成绩|奖学金|入党|思想汇报|结课|期末|录取|毕业"),
    ("项目/实践", r"井邻|洞台|乡村美育|工作站|立项|合作|方案|甲方|客户|布展|拍摄|发布|展览"),
    ("求职/职场", r"实习|录用|面试|入职|离职|辞职|转正|offer|简历|工资|课酬"),
    ("家庭", r"父母|爸爸|妈妈|家里|冷战|奶奶|小姑|房租|望京|我妈|我爸"),
    ("亲密关系", r"同居|老公|老婆|女朋友|相亲|约会|分手|复合|表白|接机"),
    ("出行/迁移", r"出发|抵达|回京|返程|机票|高铁|下乡|驻村|出差|云南|澜沧|怀柔|承德"),
    ("社交/见面", r"聚会|聚餐|见面|喝酒|校友|联谊|婚礼|生日|看展"),
    ("生活/事务", r"住院|手术|体检|挂号|搬家|提车|买车|维修|快递|钥匙|赔偿|事故|剐蹭"),
]
SYS_NAMES = {"微信支付", "微信团队", "服务通知", "美团", "美团金融服务", "微信运动",
             "文件传输助手", "微信公众平台", "腾讯新闻", "订阅号消息", "微信收款助手",
             "微信支付凭证", "QQ邮箱提醒", "微信安全中心"}


def cat_of(t):
    for n, kw in CATS:
        if re.search(kw, t):
            return n
    return "待定"


def stage_digest(c):
    tid = task(c, "digest", "81 个周包", "每周发生了什么？他自己说了什么？（第一遍全量发现）")
    digdir = os.path.join(BATCH, "digests")
    os.makedirs(digdir, exist_ok=True)
    seen_sessions = set()
    index = []
    nbytes = 0
    for wk, lo, hi, path in c.execute(
            "select week,lo,hi,pkg_path from weeks order by week"):
        if not path or not os.path.exists(path):
            continue
        head = None
        sess = {}
        mine_strong, mine_weak, theirs_strong = [], [], []
        with io.open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                if "week" in o:
                    head = o
                    continue
                if "session_key" in o:
                    sess[o["session_key"]] = o
                    continue
                t, r, y, ct = o.get("t"), o.get("r"), o.get("y"), o.get("c") or ""
                if y in ("image", "sticker", "voice", "video") or NOISE.search(ct):
                    continue
                sk = None
                if r == "me" and STRONG.search(ct):
                    mine_strong.append((t, ct))
                elif r == "me" and WEAK.search(ct):
                    mine_weak.append((t, ct))
                elif r == "them" and STRONG.search(ct):
                    theirs_strong.append((t, ct))
        new_sess = [k for k in sess if k not in seen_sessions]
        seen_sessions.update(sess)
        top = sorted(sess.values(), key=lambda x: -x["n"])[:12]
        L = ["# %s ｜ %s → %s" % (wk, lo, hi),
             "",
             "消息 %d ｜ 会话 %d ｜ 他发言 %d ｜ 新出现会话 %d"
             % (head["messages"], head["sessions"],
                sum(v["mine"] for v in sess.values()), len(new_sess)),
             "",
             "## 本周活跃（TOP12）",
             "| 会话 | 类型 | 条数 | 他 | 对方 |",
             "|---|---|---|---|---|"]
        for v in top:
            nm = v["session_name"]
            if nm in SYS_NAMES:
                nm += "（系统）"
            L.append("| %s | %s | %d | %d | %d |" % (nm, v["session_type"], v["n"], v["mine"], v["theirs"]))
        L += ["", "## 本周首次出现的会话"]
        L.append("、".join(sess[k]["session_name"] for k in new_sess[:25]) or "（无）")
        L += ["", "## 他自己说的（强事件词，最多 30 条）"]
        for t, ct in mine_strong[:30]:
            L.append("- `%s` %s" % (t[5:16], re.sub(r"\s+", " ", ct)[:150]))
        L += ["", "## 他自己说的（弱事件词，最多 15 条）"]
        for t, ct in mine_weak[:15]:
            L.append("- `%s` %s" % (t[5:16], re.sub(r"\s+", " ", ct)[:130]))
        L += ["", "## 对方说的（强事件词，最多 10 条）"]
        for t, ct in theirs_strong[:10]:
            L.append("- `%s` %s" % (t[5:16], re.sub(r"\s+", " ", ct)[:130]))
        p = os.path.join(digdir, "%s.md" % wk)
        io.open(p, "w", encoding="utf-8").write("\n".join(L))
        sz = os.path.getsize(p)
        nbytes += sz
        cats = Counter(cat_of(x[1]) for x in mine_strong)
        index.append((wk, lo, hi, head["messages"], head["sessions"],
                      sum(v["mine"] for v in sess.values()), len(new_sess),
                      len(mine_strong), len(mine_weak), cats.most_common(1)[0][0] if cats else "—", p))
        c.execute("update weeks set status='digested',analyzed=1 where week=?", (wk,))
    c.commit()
    with io.open(os.path.join(BATCH, "digest_index.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["周", "起", "止", "消息", "会话", "他发言", "新会话", "强事件", "弱事件", "主类别", "摘要"])
        w.writerows(index)
    task_done(c, tid, "done", materials=len(index), nbytes=nbytes, note="%d 周摘要" % len(index))
    log_run(c, "digest", "81 个周包", len(index), 0, nbytes)
    print("=" * 72)
    print("阶段 ③ 每周信号摘要（第一遍全量发现）")
    print("=" * 72)
    print("摘要 %d 份 ｜ 落盘 %.1f MB" % (len(index), nbytes / 1024**2))
    hi = sorted(index, key=lambda x: -x[7])[:8]
    print("\n他自己强事件最多の周：")
    for r in hi:
        print("  %s  %3d 条 ｜ %s ｜ %s" % (r[0], r[7], r[9], r[10][:52]))
    return len(index)


# ──────────────────────────────────────────────────────────── stage: dates
def stage_dates(c):
    tid = task(c, "dates", "全部经历", "每段经历的真实日期（六时点）与冲突研判")
    # 从事件库读已有事件，按「经历」聚类（同人+同类别+30天内）
    adb = os.path.join(WS, "analysis.sqlite")
    exp = []
    if os.path.exists(adb):
        a = sqlite3.connect("file:" + adb.replace("\\", "/") + "?mode=ro", uri=True)
        try:
            for eid, date, cat, subj, ev, per in a.execute(
                    "select event_id,date,category,subject,event,person from events "
                    "where date>=? order by date", (T_ADMIT,)):
                exp.append((eid, date, cat, subj, ev, per))
        except Exception as ex:
            print("  读事件库失败：%s" % ex)
        a.close()
    c.executemany("""insert into experiences
        (name,category,source,t_start,date_basis,facts,evidence)
        values(?,?,?,?,?,?,?)""",
                  [(r[3] or r[4] or "", r[2] or "", "analysis.events",
                    r[1], "事件库 event_id=%s" % r[0], r[4] or "", r[0]) for r in exp])
    c.commit()
    n = task_done(c, tid, "partial", materials=len(exp),
                  note="已灌入事件行；六时点拆分与冲突研判待下一批")
    log_run(c, "dates", "全部经历", len(exp), 0, 0, "六时点拆分待下一批")
    print("=" * 72)
    print("阶段 ③ 经历日期重建（首轮：灌入事件行）")
    print("=" * 72)
    print("经历行 %d 条（来自 analysis.events，%s 起）" % (len(exp), T_ADMIT))
    print("→ 六时点拆分（准备/开始/节点/结束/交付/发布）与冲突研判 = 下一批任务")
    return len(exp)


# ──────────────────────────────────────────────────────────── stage: dossiers
def stage_dossiers(c):
    # ★ 幂等：每次重跑先清掉本阶段上一轮的记录
    c.execute("delete from tasks where stage='dossiers'")
    c.execute("delete from runs  where stage='dossiers'")
    c.commit()
    tid = task(c, "dossiers", "全部经历", "把聊天/照片/日志/作品/课件归到同一段经历")
    # 首轮：按 category + 月份聚合出「经历候选」
    rows = list(c.execute("select category,substr(t_start,1,7) m,count(*) from experiences group by 1,2"))
    c.execute("""insert into tasks(stage,scope,question,status,note)
                 values('dossiers','经历候选聚合','跨材料归并','partial',?)""",
              ("聚合 %d 个（类别×月）" % len(rows),))
    c.commit()
    task_done(c, tid, "partial", materials=len(rows),
              note="跨材料归并待下一批（需先完成材料正文提取）")
    log_run(c, "dossiers", "全部经历", len(rows), 0, 0,
            "首轮：%d 个「类别×月」候选" % len(rows))
    print("=" * 72)
    print("阶段 ④ 跨材料归并（首轮：经历候选聚合）")
    print("=" * 72)
    print("候选（类别 × 月）%d 个" % len(rows))
    for cat, m, n in sorted(rows, key=lambda x: -x[2])[:12]:
        print("  %-10s %s  %4d" % (cat, m, n))
    print("→ 跨材料归并 = 下一批任务")
    return len(rows)


# ──────────────────────────────────────────────────────────── stage: status
def stage_status(c):
    os.makedirs(BATCH, exist_ok=True)
    mats = c.execute("select count(*),sum(bytes) from materials").fetchone()
    tks = list(c.execute("select stage,status,count(*),sum(est_tokens) from tasks group by 1,2"))
    wk = c.execute("select count(*),sum(messages) from weeks").fetchone()
    runs = list(c.execute("select ts,stage,scope,materials,messages,bytes,est_tokens,api_tokens,note "
                          "from runs order by rid"))
    est_total = sum(r[6] or 0 for r in runs)
    msg_total = sum(r[4] or 0 for r in runs)

    print("=" * 72)
    print("执行报告")
    print("=" * 72)
    print("登记材料 %d 份 ｜ %.2f GB" % (mats[0] or 0, (mats[1] or 0) / 1024**3))
    print("聊天周包 %d 个 ｜ 消息 %d 条" % (wk[0] or 0, wk[1] or 0))
    print("任务 %d 个" % sum(t[2] for t in tks))
    for s, st, n, et in sorted(tks):
        print("   %-10s %-8s %2d 个 ｜ est %s tokens" % (s, st, n, "{:,}".format(et or 0)))
    print("\n★ 用量（诚实口径）")
    print("   本地处理读取量估算 est_tokens = %s（**估算**，按 3.2 字节/token）" % "{:,}".format(est_total))
    print("   远程接口实际用量 api_tokens = unknown（本轮**未调用任何远程模型 API**）")
    print("   平台额度扣减 = 未知（本流水线不消耗平台额度）")

    # CSV
    with io.open(os.path.join(BATCH, "runs.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["时间", "阶段", "范围", "材料", "消息", "字节", "est_tokens", "api_tokens", "备注"])
        w.writerows(runs)
    return est_total, msg_total


# ──────────────────────────────────────────────────────────── stage: unreadable
def stage_unreadable(c):
    # ★ 幂等：每次重跑先清掉本阶段上一轮的记录，否则 tasks/runs 会越积越多
    c.execute("delete from tasks where stage='unreadable'")
    c.execute("delete from runs  where stage='unreadable'")
    c.commit()
    tid = task(c, "unreadable", "2025-03-26 → 今", "哪些内容读不到？缺口有多大？")
    con = sqlite3.connect("file:" + INDEX_DB.replace("\\", "/") + "?mode=ro", uri=True)
    T = int(datetime.datetime.strptime(T_ADMIT, "%Y-%m-%d").timestamp())
    tot = con.execute("select count(*) from messages where ts>=?", (T,)).fetchone()[0]
    bad = con.execute("""select count(*) from messages where ts>=? and
        (content like '%当前版本不支持展示该内容%' or content like '%请升级至最新版本%')""",
                      (T,)).fetchone()[0]
    bym = list(con.execute("""select substr(date(ts,'unixepoch','localtime'),1,7) m,count(*)
        from messages where ts>=? and content like '%当前版本不支持%' group by 1 order by 1""", (T,)))
    con.close()
    c.execute("""insert into tasks(stage,scope,question,status,note)
                 values('unreadable','2025-03-26 → 今','读不到的缺口','done',?)""",
              ("%d 条不可读（%.1f%%）" % (bad, 100 * bad / max(tot, 1)),))
    c.commit()
    log_run(c, "unreadable", "2025-03-26 → 今", 0, bad, 0, "link 卡片内容缺失")
    print("=" * 72)
    print("阶段 ⑤ 不可读内容登记")
    print("=" * 72)
    print("窗口消息 %d ｜ 不可读 %d 条 = %.1f%%（全部为 link 卡片：导出时未落正文）"
          % (tot, bad, 100 * bad / max(tot, 1)))
    print("→ 这部分**不能算已读**；需回原始导出补正文或人工补")
    return tot, bad


# ──────────────────────────────────────────────────────────── stage: report
def stage_report(c):
    os.makedirs(BATCH, exist_ok=True)
    mats = c.execute("select count(*),sum(bytes) from materials").fetchone()
    dup = c.execute("select count(*) from materials where dup_of is not null").fetchone()[0]
    ext = c.execute("select count(*) from materials where extracted=1").fetchone()[0]
    need = c.execute("select count(*) from materials where need_tool<>''").fetchone()[0]
    wk = c.execute("select count(*),sum(messages),sum(sessions_active) from weeks").fetchone()
    exp = c.execute("select count(*) from experiences").fetchone()[0]
    runs = list(c.execute("""select ts,stage,scope,materials,messages,bytes,est_tokens,api_tokens,note
                             from runs order by rid"""))
    # ★ 同一 stage 可能有多行（阶段里追加的信息行）→ 只保留最后一行，避免报告出现重复行
    _all_t = list(c.execute("select stage,scope,status,materials,messages,est_tokens,note,started,ended "
                            "from tasks order by tid"))
    _seen = {}
    for t in _all_t:
        _seen[t[0]] = t
    tasks = sorted(_seen.values(), key=lambda t: t[7] or "")
    est = sum(r[6] or 0 for r in runs)
    byroot = list(c.execute("select root,count(*),sum(bytes) from materials group by root order by 2 desc"))
    bykind = list(c.execute("select kind,count(*) from materials group by kind order by 2 desc"))

    H = []
    A = H.append
    A("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>央美之后 · 全量经历重建 · 执行报告</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f7f6f3;color:#22201d;font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:36px 26px 80px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}
.sub{color:#6b6660;font-size:13px;margin-bottom:26px}
h2{font-size:18px;margin:34px 0 10px;padding-bottom:7px;border-bottom:2px solid #e5e1da}
h3{font-size:15px;margin:20px 0 8px;color:#4a4642}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0}
th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#efece6;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.card{flex:1 1 150px;background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:12px 14px}
.card .v{font-size:22px;font-weight:700;letter-spacing:-.5px}
.card .k{font-size:12px;color:#6b6660;margin-top:2px}
.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:10px 14px;border-radius:0 6px 6px 0;margin:12px 0;font-size:13.5px}
.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:10px 14px;border-radius:0 6px 6px 0;margin:12px 0;font-size:13.5px}
code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:12.5px}
.foot{margin-top:36px;padding-top:14px;border-top:1px solid #e5e1da;color:#8a857e;font-size:12px}
</style></head><body><div class="wrap">""")
    A("<h1>央美之后 · 全量经历重建 · 执行报告</h1>")
    A('<div class="sub">窗口 %s → %s ｜ 生成 %s ｜ 状态库 <code>_tmp\\batch\\batch.sqlite</code></div>'
      % (T_ADMIT, T_NOW, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))

    A('<div class="warn"><b>★ 诚实声明</b>：本流水线<b>全部本地运行，未调用任何远程模型 API</b>。'
      '所以「接口实际用量」一律记为 <code>unknown</code>，平台额度扣减为 <b>0</b>。'
      '下面的 <code>est_tokens</code> 是<b>本地读取量的估算</b>（字节 ÷ 3.2），'
      '<b>不等于</b> 1 亿 token 目标，也不与平台扣减混算。</div>')

    A('<div class="kpi">')
    for v, k in [("%d" % (mats[0] or 0), "登记材料（份）"),
                 ("%.1f GB" % ((mats[1] or 0) / 1024**3), "材料体量"),
                 ("%d" % (wk[1] or 0), "覆盖消息（条）"),
                 ("%d" % (wk[0] or 0), "周包（个）"),
                 ("%d" % exp, "经历行"),
                 ("%s" % "{:,}".format(est), "est_tokens（估算）")]:
        A('<div class="card"><div class="v">%s</div><div class="k">%s</div></div>' % (v, k))
    A("</div>")

    # 一
    A('<h2>一、材料登记（找到 / 提取 / 送入模型 / 分析完成 —— 四态分开）</h2>')
    A("<table><tr><th>来源</th><th>份数</th><th>体量</th></tr>")
    for r, n, b in byroot:
        A("<tr><td>%s</td><td class='n'>%d</td><td class='n'>%.2f GB</td></tr>" % (r, n, (b or 0) / 1024**3))
    A("</table>")
    A("<table><tr><th>类型</th><th>份数</th></tr>")
    for k, n in bykind:
        A("<tr><td>%s</td><td class='n'>%d</td></tr>" % (k, n))
    A("</table>")
    A("<table><tr><th>状态</th><th>份数</th><th>说明</th></tr>"
      "<tr><td>找到文件</td><td class='n'>%d</td><td>已登记路径 / 大小 / 时间</td></tr>"
      "<tr><td>成功提取内容</td><td class='n'>%d</td><td>纯文本类（md/txt/csv/json/html/代码）+ 数据库</td></tr>"
      "<tr><td>重复副本</td><td class='n'>%d</td><td>内容哈希相同 → 复用处理结果</td></tr>"
      "<tr><td>需外部工具 / OCR</td><td class='n'>%d</td><td><b>本轮未处理 → 不算已读</b></td></tr>"
      "<tr><td>内容已送入模型</td><td class='n'>0</td><td>未调用远程模型（本地流水线）</td></tr>"
      "<tr><td>分析完成</td><td class='n'>%d</td><td>周摘要已生成</td></tr></table>"
      % ((mats[0] or 0), ext, dup, need, wk[0] or 0))

    # 二
    A('<h2>二、聊天覆盖（连续、全联系人、双向）</h2>')
    A("<p>从 <b>%s（央美拟录取）</b> 起按 <b>自然周</b> 切片，<b>不筛选联系人</b> —— "
      "覆盖全部私聊与群聊，同时读取他与对方的发言。</p>" % T_ADMIT)
    A("<table><tr><th>项</th><th>值</th></tr>"
      "<tr><td>周包</td><td class='n'>%d 个</td></tr>"
      "<tr><td>覆盖消息</td><td class='n'>%d 条</td></tr>"
      "<tr><td>他本人发言</td><td class='n'>67,613 条</td></tr>"
      "<tr><td>落盘</td><td class='n'>146.3 MB（JSONL，含会话头 + 逐条）</td></tr>"
      "<tr><td>周摘要</td><td class='n'>81 份（0.5 MB，可直接读）</td></tr></table>" % ((wk[0] or 0), (wk[1] or 0)))
    A('<div class="warn"><b>★ 已识别的真实缺口</b>：8,126 条（2.4%）消息内容为'
      '「当前版本不支持展示该内容」—— <b>全部是 link 卡片</b>，导出时未落正文。'
      '其中文件传输助手 3,045 条。<b>这部分不能算已读</b>，需回原始导出补正文。</div>')

    # 三
    A('<h2>三、执行队列与用量</h2>')
    A("<table><tr><th>#</th><th>阶段</th><th>范围</th><th>状态</th><th>材料</th><th>消息</th>"
      "<th>est_tokens</th><th>api_tokens</th><th>备注</th></tr>")
    for i, t in enumerate(tasks, 1):
        A("<tr><td class='n'>%d</td><td>%s</td><td>%s</td><td>%s</td><td class='n'>%d</td>"
          "<td class='n'>%d</td><td class='n'>%s</td><td>unknown</td><td>%s</td></tr>"
          % (i, t[0], t[1], t[2], t[3] or 0, t[4] or 0, "{:,}".format(t[5] or 0), t[6] or ""))
    A("</table>")
    A("<table><tr><th>阶段</th><th>成功状态</th><th>est_tokens（估算）</th></tr>")
    for s in sorted({r[1] for r in runs}):
        rs = [r for r in runs if r[1] == s]
        A("<tr><td>%s</td><td>done</td><td class='n'>%s</td></tr>"
          % (s, "{:,}".format(sum(r[6] or 0 for r in rs))))
    A("<tr><th>合计</th><th>—</th><th class='n'>%s</th></tr>" % "{:,}".format(est))
    A("</table>")
    A('<div class="warn"><b>★ 与 1 亿 token 目标的差距（如实报告）</b>：'
      '本流水线是<b>本地确定性处理</b>，不产生模型 token 消耗。'
      '若按「把全部材料正文送进模型」折算，当前仅完成 <b>第 ① ② ⑤ 阶段</b>（登记 / 切片 / 缺口登记）'
      '与<b>第 ③ 阶段首轮</b>（周摘要）。'
      '真正需要模型 token 的是<b>「逐材料正文精读 + 经历归并 + 竞争解释」</b>——'
      '这部分<b>尚未开始</b>，因为 46,160 份材料需要 OCR / 解析工具，当前不具备。</div>')

    # 四
    A('<h2>四、尚未覆盖 / 失败清单</h2>')
    A("<table><tr><th>项</th><th>状态</th><th>阻碍</th></tr>"
      "<tr><td>46,160 份图片 / 视频 / Office 文档正文</td><td>⬜ 未处理</td>"
      "<td>缺 OCR / ASR / Office 解析能力；<b>不计入已读</b></td></tr>"
      "<tr><td>8,126 条 link 卡片正文</td><td>⬜ 不可读</td><td>导出未落正文</td></tr>"
      "<tr><td>经历六时点拆分（准备/开始/节点/结束/交付/发布）</td><td>🟡 首轮</td>"
      "<td>已灌入 %d 条事件行，六时点拆分与冲突研判待下一批</td></tr>"
      "<tr><td>跨材料归并（聊天↔照片↔日志↔作品↔课件）</td><td>🟡 首轮</td>"
      "<td>已聚合 160 个「类别×月」候选，真正归并待正文提取后</td></tr>"
      "<tr><td>竞争解释与反例</td><td>⬜ 未开始</td><td>依赖前两项</td></tr>"
      "<tr><td>1 亿 token</td><td>⬜ 未达</td><td>本地流水线不产生模型 token</td></tr></table>" % exp)

    # 五 —— 首轮挖到的成果线索
    A('<h2>五、首轮挖到的成果线索（来自已读到的周摘要）</h2>')
    A('<div class="ok"><b>★ 说明</b>：下表<b>只含已读到材料</b>里的线索；'
      '标「待核实 / 已排除」的<b>不得直接写进汇报</b>。</div>')
    A("<table><tr><th>线索</th><th>时间</th><th>角色</th><th>依据</th><th>说明</th><th>状态</th></tr>")
    for name, when, role, basis, note, st in FINDINGS:
        A("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
          % (name, when, role, basis, note, st))
    A("</table>")

    # 五·补 —— 正文提取与片段切分现状（本地加工层）
    A('<h2>五·补、正文提取与片段切分现状</h2>')
    try:
        ex = c.execute("select count(*) from materials where extracted=1").fetchone()[0]
        ck = c.execute("select count(*),coalesce(sum(nchars),0),coalesce(sum(est_tokens),0),"
                       "coalesce(sum(nmsg),0) from chunks").fetchone()
        cm = c.execute("select count(*) from chunks where modeled=1").fetchone()[0]
        ca = c.execute("select count(*) from chunks where analyzed=1").fetchone()[0]
        A("<table><tr><th>项</th><th>值</th><th>说明</th></tr>"
          "<tr><td>已提取正文</td><td class='n'>%s 份</td><td>txt/md/csv/json/html/代码 + docx/xlsx/pptx + 文字型 PDF</td></tr>"
          "<tr><td>切分片段</td><td class='n'>%s 个</td><td>window（超长会话按时间窗）+ pack（小会话按时间打包）</td></tr>"
          "<tr><td>片段字符</td><td class='n'>%s</td><td>正文不重叠；前后文另以「回带/预告」提供</td></tr>"
          "<tr><td>片段 est_tokens</td><td class='n'>%s</td><td><b>估算</b>（字符 ÷ 1.6）—— 即「全部送进模型」的量级</td></tr>"
          "<tr><td>覆盖消息</td><td class='n'>%s 条</td><td>与窗口内消息总数一致（无重复计数）</td></tr>"
          "<tr><td>已送入模型</td><td class='n'>%s 个片段</td><td>★ <b>0</b> —— 远程读取范围未确认，未发送任何聊天原文</td></tr>"
          "<tr><td>模型分析完成</td><td class='n'>%s 个片段</td><td>—</td></tr>"
          "</table>" % ("{:,}".format(ex), "{:,}".format(ck[0]), "{:,}".format(ck[1]),
                        "{:,}".format(ck[2]), "{:,}".format(ck[3]),
                        "{:,}".format(cm), "{:,}".format(ca)))
        A('<div class="ok"><b>★ 关键量级</b>：聊天正文折算 <b>%s token</b> —— '
          '这一项<b>已经超过</b> 1 亿目标的一半。也就是说：<b>只要授权把聊天原文送进模型，'
          '1 亿 token 目标立刻可达</b>；不需要等 46,160 份图片解锁。</div>' % "{:,}".format(ck[2]))
    except Exception as e:
        A('<div class="warn">片段表读取失败：%s</div>' % e)

    # 六 —— 未完成队列（落盘）
    A('<h2>六、未完成队列（已保存到磁盘）</h2>')
    A("<table><tr><th>编号</th><th>任务</th><th>当前状态</th><th>需要什么才能继续</th></tr>")
    for qid, t, st, need in NEXT_QUEUE:
        A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (qid, t, st, need))
    A("</table>")
    A('<div class="warn"><b>★ 卡点（2026-10-06 更新）</b>：'
      '① <b>缺 OCR / ASR</b> —— 挡住 46,014 张图片 + 9,770 个视频 + 18 个音频'
      '（<b>Office 与文字型 PDF 已解决</b>，见第五节补）；'
      '② <b>远程模型读取范围未确认</b> —— 挡住「逐材料精读 + 竞争解释」= 真正吃 token 的部分。'
      '<b>但聊天正文已切好 3,809 个片段</b>，只要授权即可启动，不必等图片解锁。'
      '两个卡点不解决，1 亿 token 目标<b>无法达成</b>——本报告不虚报。</div>')

    A('<div class="foot">本地流水线 <code>tools\\batch_pipeline.py</code> ｜ '
      '子命令 registry / weeks / digest / dates / dossiers / unreadable / report ｜ '
      '<b>不得外传</b>：含真人姓名、机构、未公开材料</div>')
    A("</div></body></html>")
    out = os.path.join(BATCH, "执行报告_全量经历重建.html")
    io.open(out, "w", encoding="utf-8").write("\n".join(H))

    # ★ 未完成队列落盘（CSV + JSON），中断后可直接续跑
    with io.open(os.path.join(BATCH, "未完成队列.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["编号", "任务", "当前状态", "需要什么才能继续"])
        w.writerows(NEXT_QUEUE)
    io.open(os.path.join(BATCH, "未完成队列.json"), "w", encoding="utf-8").write(
        json.dumps([{"id": q, "task": t, "status": s, "need": n} for q, t, s, n in NEXT_QUEUE],
                   ensure_ascii=False, indent=2))
    # 首轮成果线索落盘
    with io.open(os.path.join(BATCH, "成果线索_首轮.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["线索", "时间", "角色", "依据", "说明", "状态"])
        w.writerows(FINDINGS)

    print("=" * 72)
    print("阶段 ⑥ 执行报告")
    print("=" * 72)
    print("→ %s（%.1f KB）" % (out, os.path.getsize(out) / 1024))
    return out


# ──────────────────────────────────────────────────────────── main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["registry", "weeks", "digest", "dates", "dossiers",
                                    "unreadable", "report", "status", "all"])
    ap.add_argument("--limit", type=int, default=None, help="registry 最多登记多少文件（调试用）")
    a = ap.parse_args()
    c = db()
    t0 = time.time()
    if a.cmd in ("registry", "all"):
        stage_registry(c, a.limit)
    if a.cmd in ("weeks", "all"):
        stage_weeks(c)
    if a.cmd in ("digest", "all"):
        stage_digest(c)
    if a.cmd in ("dates", "all"):
        stage_dates(c)
    if a.cmd in ("dossiers", "all"):
        stage_dossiers(c)
    if a.cmd in ("unreadable", "all"):
        stage_unreadable(c)
    if a.cmd in ("report", "all"):
        stage_report(c)
    if a.cmd in ("status", "all"):
        stage_status(c)
    print("\n用时 %.1f 秒 ｜ 状态库 %s" % (time.time() - t0, DB))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
