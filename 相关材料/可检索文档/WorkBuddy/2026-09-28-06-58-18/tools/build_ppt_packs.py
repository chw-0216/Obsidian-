# -*- coding: utf-8 -*-
r"""
build_ppt_packs.py v2 —— 每段经历 → 一页可直接用的 PPT 材料包

任务书（2026-10-06 主任务）要求每包含 7 项：
  ① 经历名称 / 日期 / 地点
  ② 我的具体贡献及成果
  ③ 一张主图 + 2–4 张过程/细节图
  ④ 每张图的原始路径 / 拍摄者信息 / 简短说明
  ⑤ 可直接放进 PPT 的标题与两三句正文
  ⑥ 一段可直接念的讲述文字
  ⑦ 一页可编辑 PPT 草稿

并且明确要求：
  · 照片分三类：① 我拍摄的摄影/记录成果 ② 记录我实际工作过程的照片 ③ 项目整体现场及成果
  · 拍摄者暂不明确的**保留待确认**
  · 日期区分：**拍摄日期 / 转发日期 / 文件修改日期 / 事件日期**
  · 过程图尽量按「准备 — 行动 — 成果」排序
  · 每批同时交出**照片联系表 + 入选原图索引 + 贡献文字 + PPT 草稿**
  · **沿用已有汇报视觉风格**

视觉规范（从 `中期汇报_2026-09\06_PPT成品\*.pptx` 反解）
  16:9 (13.333×7.5in) · 微软雅黑 · 主色 #1F3D2B · 强调 #9E3B2E · 正文 #5A5A5A
  内页标题 29pt bold · 副标题 13pt · 小标题 16pt bold 强调色 · 正文 12.5pt
  页脚「蔡浩文 · 12250300012 · 社会美育与乡村振兴」10.5pt + 右下页码 11pt bold

★ 诚实边界（写进产物，不隐藏）
  · **拍摄日期拿不到** —— 微信把 EXIF 全剥了；只能给「转发日期（消息时间）」
  · 拍摄者只在有依据时标注：`我发出`(role=me) / `他人发来`(role=them) / **`拍摄者待确认`**
  · 群内零发言 ≠ 没参加；活动通知 ≠ 个人入选；团队成果 ≠ 个人贡献

用法
----
  python tools\build_ppt_packs.py --build
  python tools\build_ppt_packs.py --build --no-deck
"""
import os, io, re, csv, json, math, shutil, sqlite3, argparse, datetime, traceback, subprocess
from collections import defaultdict, Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
# ★ 每次运行写进**独立时间戳目录** —— 本机 SAFE_DELETE_BULK_CONFIRM_REQUIRED 会把
#   「覆盖已存在文件」计成删除，阈值 50/轮；不做覆盖就永远不触发。
RUNSTAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(WS, "_tmp", "ppt_packs", RUNSTAMP)
SHEETS = os.path.join(WS, "_tmp", "sheets")
CACHE = os.path.join(WS, "_tmp", "hevc_cache")

CUR = r"C:\Users\wardc\Desktop\中期汇报_2026-09\07_照片素材"
CUR_IDX = os.path.join(CUR, "照片索引.csv")
CUR_DIRS = {
    "01": os.path.join(CUR, "01_工作站与领导接待"),
    "02": os.path.join(CUR, "02_版画技法_木版与石版"),
    "03": os.path.join(CUR, "03_工作站现场_导师记录"),
    "04": os.path.join(CUR, "04_澜沧支教"),
    "05": os.path.join(CUR, "05_学术会务_论坛"),
    "06": os.path.join(CUR, "06_区委书记到访_导师聊天_2026-08-22"),
    "07": os.path.join(CUR, "07_英国大使馆与亚当斯密活动"),
    "08": os.path.join(CUR, "08_英国校友会活动"),
}
PPT_DIR = r"C:\Users\wardc\Desktop\中期汇报_2026-09\09_PPT用图"
LANG_CANG = r"C:\Users\wardc\Desktop\澜沧支教_课堂照片_评审优化版_20260903"
AI_OUT = r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs"

DECK = os.path.join(WS, "中期汇报_经历页_第二批_2026-10-06.pptx")
PREVIEW = os.path.join(WS, "汇报页面材料包_第二批_2026-10-06.html")
INDEX_CSV = os.path.join(WS, "入选原图索引_第二批_2026-10-06.csv")

FONT = "微软雅黑"
C_MAIN = "1F3D2B"; C_ACC = "9E3B2E"; C_BODY = "5A5A5A"
FOOTER = "蔡浩文 · 12250300012 · 社会美育与乡村振兴"

# ── 经历清单（第二批扩到 12 段；roots=数据库桶，cur=策展目录，kw=关键词）──
EXPERIENCES = [
    dict(no=1, name="洞台村乡村美育工作站", date="2026-03 → 2026-10", place="北京市怀柔区渤海镇洞台村 78 号",
         lo="2026-03-01", hi="2026-10-06",
         roots=["井邻宣传", "井邻项目", "汇报照片素材", "微信原图HD", "朋友圈"],
         cur=["01", "03", "06"], kw=["工作站", "接待", "开街", "书记", "领导", "井邻", "Logo", "标识"],
         title="实践主线：洞台村乡村美育工作站",
         sub="2026年3月—10月 · 驻村建设并运营 · 从 0 到 1",
         body=["我负责工作站的现场建设与运营：三间屋整体规划、显示屏检查更换上墙、路由器与投屏联动、导轨射灯对接安装、空调多方协调。",
               "我完成三平台地图登记（腾讯/高德/百度，含经纬度与门牌号 78 号），并设计工作坊定价方案。",
               "我撰写了《乡村美育驻村工作日志》（33 个工作日逐日记录 + 8 项问题闭环表），获导师认可。",
               "我设计并迭代了「乡村美育工作站 Rural Aesthetic Lab」标识系统，对外服务 8 批次领导接待，负责现场讲解与提前制版。"],
         narration="这条线是我投入时间最长的。工作站原本只是一间村屋，我从零把它建到了能开门运营——"
                   "搬电视、装屏、布线、装空调、跑地图标注、定价格方案，标识系统也是我一版一版做出来的。"
                   "7 月到 8 月，我在这里接待了 8 批次来访，包括区政协主席、区委宣传部长、"
                   "区委组织部和市文旅局。领导来了，版画和丝网这块我能讲清楚。"),

    dict(no=2, name="澜沧支教（Movers4Climate）", date="2026-06 → 2026-09", place="云南省普洱市澜沧拉祜族自治县第三民族中学",
         lo="2026-06-01", hi="2026-09-30",
         roots=["澜沧提交包", "知行最终材料", "知行最终版", "朋友圈"],
         cur=["04"],
         dirs=[(os.path.join(LANG_CANG, "01_优先推荐"), "澜沧课堂照（成品集）"),
               (os.path.join(LANG_CANG, "02_可用备选"), "澜沧课堂照（成品集）")],
         kw=["澜沧", "支教", "知行", "绿墨", "课堂", "Movers"],
         title="社会服务：知行计划 · 澜沧支教",
         sub="第三届 Movers4Climate 绿色乡村青年行动 · 2026年8月31日—9月4日 · 澜沧县第三民族中学",
         body=["我是队长，负责项目申报书撰写与结项报告；项目已完成立项与结项。",
               "我独立研发了「植物里的颜色——澜沧的调色盘」讲课 PPT，含前后测问卷包（16 题 / 打印 35 份）。",
               "我现场授课并组织招募，从物理晚自习「抢」来 20 余名学生，当地艺术老师带绝版木刻学生参与。",
               "★ 口径：这是**立项团队**成果；我个人的部分是申报、课件研发、授课与组织。"],
         narration="澜沧这个项目是联合国开发计划署的 Movers4Climate，全国 563 支团队报名。"
                   "我是队长，从写申报书到结项报告都由我负责。"
                   "我最大的贡献是课程设计——我用丝网印刷去讲可持续发展，"
                   "把「植物里的颜色」做成了一套能落地的课，还配了前后测问卷。"
                   "现场我从物理晚自习里把学生「抢」过来，最后招到 20 多人。"),

    dict(no=3, name="版画技法补齐（木版 · 石版 · 丝网）", date="2026-01 → 2026-06", place="中央美术学院",
         lo="2026-01-15", hi="2026-06-30",
         roots=["井邻项目"], cur=["02"],
         kw=["版画", "木版", "石版", "武宏", "木刻", "丝网", "制版", "甲马", "油墨"],
         title="技法支撑：版画三技 · 木版与石版",
         sub="2026年3月—6月 · 导师专门沟通插班大二 · 武宏老师赠一整套全新木刻刀",
         body=["我插班进入大二木版技法课（导师陈晔专门与武宏老师沟通安排），完成木刻创作并以 PDF 提交。",
               "我完成石版技法初步全流程（磨版 / 药墨 / 转印），由刘启光老师主讲。",
               "我积累木版刻版与作品照 89 张，并完成丝网制版实操，形成「木版 → 丝网 → 石版」完整技法链条。",
               "★ 口径：技法课是**课程作业**，不是对外交付；我的产出是作品与过程记录。"],
         narration="这一年我把版画的技法链条补齐了。木版是导师专门跟武宏老师沟通让我插班进大二的课，"
                   "武老师还送了我一整套全新的木刻刀。后来丝网课老师没空，武老师又主动给我安排了石版。"
                   "从磨版、上药墨到转印，全流程我自己走了一遍。"),

    dict(no=4, name="第五届美学与艺术研究学术研讨会（会务）", date="2025-09 → 2025-11", place="中央美术学院",
         lo="2025-09-01", hi="2025-11-30",
         roots=["汇报照片素材", "朋友圈"], cur=["05"],
         kw=["论坛", "会务", "美学", "会场", "研讨会"],
         title="学术会务：第五届美学与艺术研究学术研讨会",
         sub="2025年10月12日 · 中华美学学会 × 中央美术学院联合主办",
         body=["我负责会务执行全流程：预算套表、37 项倒计时任务清单、差旅与报账。",
               "我完成 9 小时录音转写、圆桌文字整理与新闻稿初稿。",
               "论坛当天我负责现场执行：工作餐引导、录音、场地维护、会场布置与复原。",
               "★ 口径：会务是**支撑性工作**，成果是流程文件与会议记录，不是学术产出。"],
         narration="这场论坛是中华美学学会和央美联合主办的。我负责的是会务执行——"
                   "从预算表、37 项倒计时任务清单，到当天的录音、场地维护、会场布置与复原。"
                   "会后我把 9 小时的录音全部转写整理，还写了新闻稿初稿。"),

    dict(no=5, name="「悲鸿 YOUNG」视觉体系", date="2026-08 → 2026-10", place="洞台村「洞见温度」艺术计划",
         lo="2026-08-01", hi="2026-10-06",
         roots=["井邻项目", "井邻宣传", "AI产物"], cur=[],
         kw=["悲鸿", "YOUNG", "主视觉", "展陈", "标识融合"],
         title="设计实践：「悲鸿 YOUNG」视觉体系",
         sub="2026年8月—10月 · 主视觉迭代 v5 → v35+ · 已实际印刷使用",
         body=["我独立设计该品牌主视觉，累计迭代 35 版以上，并完成展陈方案与标识融合。",
               "我输出打印交付版 v35，并配套动态双帧设计。",
               "★ 这是**设计能力的量化证据**——一个品牌主视觉迭代 35 版，且已实际印刷。",
               "★ 口径：设计稿是个人产出；印刷与落地由团队协同完成。"],
         narration="「悲鸿 YOUNG」是洞台村艺术计划的公众号品牌。主视觉是我一个人做的，"
                   "前后迭代了 35 版以上——从字体、配色到标识融合，一版一版改到能印刷。"
                   "这比说「我会设计」要有力得多：35 版迭代本身就是证据。"),

    dict(no=6, name="厦门集美授课", date="2026-04-26 → 2026-05-10", place="福建省厦门市集美区",
         lo="2026-04-18", hi="2026-05-31",
         roots=["微信图片HEVC", "微信原图HD", "朋友圈", "C1原片"], cur=[],
         kw=["厦门", "集美", "版画实验", "上课", "授课", "学生", "离厦", "班主任"],
         title="教学现场：厦门集美授课",
         sub="2026年4月26日—5月10日 · 一个学期的正规课程授课（学校全称待确认）",
         body=["我承担该课程授课，完成版画实验教学；本人朋友圈 2026-05-01 自述「重生之黑道班主任短期体验卡·五一假期冒名版」。",
               "本人原话链完整：2025-12-20 母亲「让你去厦门当我助教」→ 2026-03-02「我是去厦门教课」"
               "→ 04-26「我给五一出趟差去厦门讲课」→ 05-01「我在厦门上课」→ 05-07 朋友圈「准备离厦了」→ 06-12「在厦门上课一个学期已结束」。",
               "⚠️ 学校全称与课时**待确认** —— 记录里只有「集美区」，没有学校全称。",
               "⚠️ 现有照片来自**本人朋友圈自拍/记录**（拍摄者待确认）；**课堂现场照尚缺** —— 已在「待补清单」登记。"],
         narration="除了澜沧的乡村支教，我还在厦门做过一整个学期的正规课程授课。"
                   "这跟支教不一样——这是在真实的教学体系里带课。"
                   "我做的还是版画实验教学，把技法拆成学生能上手的步骤。"),

    dict(no=7, name="北京广播电视台 AIGC 科研实习", date="2026-01-07 → 2026-02-12", place="北京广播电视台 AI 实验室",
         lo="2026-01-01", hi="2026-02-28",
         roots=["微信图片HEVC", "微信原图HD"], cur=[],
         kw=["北京台", "广播", "短剧", "AIGC", "数字人播报", "智能体", "李明嘉", "梅宸羽"],
         title="技术实习：北京广播电视台 AIGC 科研实习",
         sub="2026年1月7日—2月12日 · AI 实验室 · 智能体架构与数字人播报",
         body=["我参与智能体（Agent）架构设计、新闻情报自动抓取与结构化摘要。",
               "我参与数字人播报系统研发与 AI 短剧制作流程设计。",
               "我输出 6 个课件 / 方案（AI 内容生产 · AI 短剧七环节 · AIGC 协同创作工具 · 校服设计）。",
               "★ 口径：我是**非技术背景的协助**，只写我负责的环节。",
               "⚠️ **照片缺口**：全库仅 3 张该时段图（`梅宸羽 北京台` 1 张 role=me、`李明嘉 北京台` 2 张），"
               "**没有工作现场照** —— 需本人补拍或向同事索取。"],
         narration="寒假我在北京广播电视台的 AI 实验室做了两个月科研实习。"
                   "我做的是智能体架构设计和新闻情报的自动抓取，还有数字人播报系统的部分环节。"
                   "我不是技术出身，所以我是以「内容+流程」的角度参与的，"
                   "最后交付了 6 个课件和方案。"),

    dict(no=8, name="数字人与交互技术线", date="2025-12 → 2026-10", place="中央美术学院 / 洞台村",
         lo="2025-12-01", hi="2026-10-06",
         roots=["井邻项目", "井邻宣传", "AI产物"], cur=[],
         kw=["数字人", "知津", "Hyper3D", "交互", "MediaPipe", "偏移四型", "MBTI", "活体", "投影"],
         title="技术探索：数字人与交互技术线",
         sub="2025年12月—至今 · 数据层完成 / 架构层设想 / 成品层未交付",
         body=["我设计了数字人「知津—识流—涅槃」五层次克隆标注框架与 5 份数字分身提示词。",
               "我独立开发可运行的交互工程：双手成曲 Gesture Synth（MediaPipe）、朗园 mediapipe_td、扫码 MBTI 活体原型。",
               "我完成「偏移四型」MediaPipe 交互版与丝网印刷结合的原型，输出多版视觉与现场预览。",
               "★ 口径必须严格：**数据层完成 / 架构层设想 / 成品层未交付**（导师 2026-03-09「要的是你的」）。"],
         narration="技术这条线，我做到的是「把概念跑成原型」——"
                   "扫码 MBTI 的丝网互动原型可以当场演示，手势交互的工程能跑起来，版印肖像有 3D 模型。"
                   "但要如实说：数字人目前是数据层完成、架构层有设想，完整的成品还没有交付。"),
]

CAT = {
    "01_工作站与领导接待": "01", "02_版画技法_木版与石版": "02",
    "03_工作站现场_导师记录": "03", "04_澜沧支教": "04",
    "05_学术会务_论坛": "05", "06_区委书记到访_导师聊天_2026-08-22": "06",
    "07_英国大使馆与亚当斯密活动": "07", "08_英国校友会活动": "08",
}


# ═══════════════════════════════ 取图
def _conn():
    c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def decode_hevc(p, key):
    if not p.lower().endswith(".hevc"):
        return p
    os.makedirs(CACHE, exist_ok=True)
    o = os.path.join(CACHE, key + ".jpg")
    if not os.path.exists(o):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p, "-frames:v", "1", "-q:v", "3", o],
                       capture_output=True)
    return o if os.path.exists(o) else None


def blank_check(jp):
    try:
        from PIL import Image, ImageStat
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(jp) as im:
            return ImageStat.Stat(im.convert("L").resize((64, 64))).stddev[0] < 3.0
    except Exception:
        return False


def photographer(role, session_name, source):
    """★ 严格基于 role，不猜"""
    if role == "me":
        return "我发出（微信消息 MD5 匹配确认 role=me）"
    if role == "them":
        return "他人发来（role=them，拍摄者待确认）"
    if source == "策展集":
        return "拍摄者待确认（策展集无 role 语义）"
    return "拍摄者待确认"


def three_class(role, root, category_db, session_name):
    """三类归属：① 我拍摄/记录成果  ② 记录我工作过程  ③ 项目现场与成果"""
    if category_db and category_db.startswith("①"):
        if root in ("AI产物", "井邻项目", "井邻宣传", "定稿图"):
            return "② 记录我工作过程（我产出的设计/作品）"
        return "① 我拍摄/记录成果"
    if category_db and category_db.startswith("③"):
        return "③ 项目整体现场与成果"
    if root in ("AI产物", "井邻项目", "井邻宣传", "定稿图", "RAW优化版", "C1原片"):
        return "② 记录我工作过程（我产出的设计/作品）"
    return "待确认"


# ★ 库内不重复取的 root：策展集 / PPT 用图 / 澜沧课堂照 —— 它们已在 `cur` / 专线里
DB_EXCLUDE = {"汇报照片素材", "PPT用图", "澜沧课堂照", "微信缩略图"}
# ★ 只有「弱日期」的 root（mtime）—— 必须关键词命中才收，否则会跨窗口污染
WEAK_DATE_ROOTS = {"AI产物", "井邻项目", "井邻宣传", "定稿图", "图片素材",
                   "RAW优化版", "媒体导出", "知行最终材料", "知行最终版",
                   "C1原片", "WeFlow图片", "澜沧提交包"}


def gather(exp, limit_per_root=40):
    """多源取图 → 统一条目（含 md5 去重、三类归属、拍摄者、日期）"""
    kws = exp.get("kw") or []
    items, seen = [], set()
    # ---- 1) 数据库桶（朋友圈单列，最后按需补）
    c = _conn()
    sns_pool = []
    if exp.get("roots"):
        roots = [r for r in exp["roots"] if r not in DB_EXCLUDE]
        w = ["root in (%s)" % ",".join("?" * len(roots))]
        a = list(roots)
        if exp.get("lo"):
            w.append("date>=?"); a.append(exp["lo"])
        if exp.get("hi"):
            w.append("date<=?"); a.append(exp["hi"])
        sql = "select * from photos where " + " and ".join(w) + " order by width desc limit 3000"
        for r in c.execute(sql, a):
            blob = (r["path"] or "") + " " + (r["session_name"] or "") + " " + (r["note"] or "")
            hit = sum(1 for k in kws if k in blob) if kws else 0
            if r["root"] == "朋友圈":
                # ★ 朋友圈只取**他本人发的**；先按关键词筛，不够再放宽（见下）
                if r["role"] == "me":
                    sns_pool.append((hit, r))
                continue
            if r["md5"] in seen:
                continue
            # ★ 非朋友圈 root 必须关键词命中
            if kws and hit == 0:
                continue
            # ★ 弱日期 root（mtime）→ 必须有关键词命中，否则视为跨窗口污染
            if r["root"] in WEAK_DATE_ROOTS and (not kws or hit == 0):
                continue
            seen.add(r["md5"])
            items.append(dict(
                path=r["path"], root=r["root"], md5=r["md5"], w=r["width"] or 0, h=r["height"] or 0,
                bytes=r["bytes"] or 0, role=r["role"], session=r["session_name"] or "",
                stype=r["session_type"] or "",
                date_msg=(r["date"] if (r["date_src"] or "").startswith(("微信消息", "朋友圈")) else ""),
                date_dir=(r["date"] if (r["date_src"] or "").startswith("目录") else ""),
                date_mtime="", date_src=r["date_src"] or "",
                note=r["note"] or "", kw_hit=hit, source="数据库",
                cat3=three_class(r["role"], r["root"], r["category"], r["session_name"]),
                who=photographer(r["role"], r["session_name"], "数据库")))
    c.close()
    # ---- 1b) 直扫目录（策展成品集，不入库）
    for dpath, dlabel in (exp.get("dirs") or []):
        if not os.path.isdir(dpath):
            continue
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".hevc"}
        for dp, ds, fs in os.walk(dpath):
            for fn in fs:
                if os.path.splitext(fn)[1].lower() not in exts:
                    continue
                p = os.path.join(dp, fn)
                try:
                    if os.path.getsize(p) < 40000:
                        continue
                except Exception:
                    continue
                key = "DIR:" + p
                if key in seen:
                    continue
                seen.add(key)
                try:
                    from PIL import Image
                    Image.MAX_IMAGE_PIXELS = None
                    with Image.open(p) as im:
                        w, h = im.size
                except Exception:
                    w = h = 0
                items.append(dict(
                    path=p, root=dlabel, md5=key, w=w, h=h, bytes=os.path.getsize(p),
                    role=None, session=dlabel, stype="", date_msg="", date_dir="",
                    date_mtime="", date_src="策展成品集（无日期语义）", note="",
                    kw_hit=0, source="成品集",
                    cat3="③ 项目整体现场与成果",
                    who="拍摄者待确认（策展成品集无 role 语义）"))

    # ---- 2) 策展集（07_照片素材）
    if exp.get("cur") and os.path.exists(CUR_IDX):
        with io.open(CUR_IDX, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                k = CAT.get((r.get("分类") or "").strip())
                if k not in exp["cur"]:
                    continue
                p = os.path.join(CUR_DIRS.get(k, ""), r.get("文件名") or "")
                if not os.path.exists(p):
                    continue
                blob = (r.get("来源会话") or "") + (r.get("消息内容") or "") + (r.get("文件名") or "")
                hit = sum(1 for kk in kws if kk in blob) if kws else 0
                key = "CUR:" + p
                if key in seen:
                    continue
                seen.add(key)
                try:
                    from PIL import Image
                    Image.MAX_IMAGE_PIXELS = None
                    with Image.open(p) as im:
                        w, h = im.size
                except Exception:
                    w = h = 0
                items.append(dict(
                    path=p, root="策展集", md5=key, w=w, h=h,
                    bytes=os.path.getsize(p), role=None, session=r.get("来源会话") or "",
                    stype="", date_msg=r.get("日期") or "", date_dir="", date_mtime="",
                    date_src="策展索引", note=(r.get("消息内容") or "")[:80],
                    kw_hit=hit, source="策展集",
                    cat3=("② 记录我工作过程（导师记录/现场）" if k == "03" else "③ 项目整体现场与成果"),
                    who=photographer(None, r.get("来源会话") or "", "策展集")))

    # ---- 3) 朋友圈（他本人发的）——先按关键词；若该经历整体候选 < 4，才放宽补入
    def add_sns(rows):
        for _hit, r in rows:
            if r["md5"] in seen:
                continue
            seen.add(r["md5"])
            items.append(dict(
                path=r["path"], root="朋友圈", md5=r["md5"], w=r["width"] or 0, h=r["height"] or 0,
                bytes=r["bytes"] or 0, role="me", session="朋友圈（本人）", stype="朋友圈",
                date_msg=r["date"] or "", date_dir="", date_mtime="", date_src=r["date_src"] or "",
                note=r["note"] or "", kw_hit=_hit, source="朋友圈",
                cat3="① 我拍摄/记录（我发的朋友圈）",
                who="我发出（朋友圈本人发帖）"))
    if sns_pool:
        hit_rows = [(h, r) for h, r in sns_pool if h > 0]
        add_sns(hit_rows)
        if len(items) < 4:                      # ★ 只有整体证据不足时才放宽
            add_sns(sns_pool)
    return items


def pick(items, min_w=700, min_bytes=40000):
    """主图 1 张 + 过程图 3 张（按「准备—行动—成果」排序）"""
    good = [it for it in items if it["w"] >= min_w and it["bytes"] >= min_bytes]
    if len(good) < 2:
        good = [it for it in items if it["w"] >= 500]
    if not good:
        return None, [], []
    # 主图：分辨率最高（且优先「我产出/我拍摄」）
    pri = {"② 记录我工作过程（我产出的设计/作品）": 0, "① 我拍摄/记录成果": 1,
           "② 记录我工作过程（导师记录/现场）": 2, "③ 项目整体现场与成果": 3}
    good.sort(key=lambda x: (pri.get(x["cat3"], 9), -x["w"]))
    main = good[0]
    rest = [it for it in good[1:]]
    # 过程图：优先不同三类，按日期排（准备→行动→成果）
    def dkey(x):
        return x["date_msg"] or x["date_dir"] or "9999"
    rest.sort(key=dkey)
    steps, used_cat = [], Counter()
    for it in rest:
        if used_cat[it["cat3"]] >= 2:
            continue
        steps.append(it); used_cat[it["cat3"]] += 1
        if len(steps) >= 3:
            break
    if len(steps) < 3:
        for it in rest:
            if it not in steps:
                steps.append(it)
            if len(steps) >= 3:
                break
    return main, steps[:3], good


def contact_sheet(items, out_jpg, prefix, title, cols=8, cell=300):
    import contact_sheet as CS
    return CS.build_sheet(items, out_jpg, prefix, title, cols, cell, True)


# ═══════════════════════════════ 构建材料包
def build_packs():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SHEETS, exist_ok=True)
    packs, all_rows = [], []
    for exp in EXPERIENCES:
        items = gather(exp)
        main, steps, good = pick(items)
        d = os.path.join(OUT, "%02d_%s" % (exp["no"], re.sub(r"[^\w\u4e00-\u9fff]", "", exp["name"])[:20]))
        # ★ 不删除（本机 SAFE_DELETE_BULK_CONFIRM_REQUIRED 阈值 50/轮）→ 一律确定性覆盖
        os.makedirs(d, exist_ok=True)

        # ---- 复制入选图（HEVC 先解码）
        caps = []
        for i, it in enumerate(([main] if main else []) + steps):
            src = it["path"]
            jp = decode_hevc(src, it["md5"].split(":")[-1] if it["md5"] else "x")
            if not jp or not os.path.exists(jp):
                continue
            if blank_check(jp):
                continue
            # ★ 一律存成 imgN.jpg（稳定文件名 → 覆盖写，不产生垃圾）
            dst = os.path.join(d, "img%d.jpg" % (i + 1))
            try:
                from PIL import Image
                Image.MAX_IMAGE_PIXELS = None
                with Image.open(jp) as im:
                    im.convert("RGB").save(dst, quality=88)
            except Exception:
                try:
                    shutil.copy2(jp, dst)
                except Exception:
                    continue
            caps.append(dict(n=i + 1, role=("主图" if i == 0 else "过程图 %d" % i),
                             src=src, dst=dst, w=it["w"], h=it["h"],
                             date_msg=it["date_msg"], date_dir=it["date_dir"],
                             date_ev=exp["date"], date_mtime=it["date_mtime"], date_src=it["date_src"],
                             session=it["session"], stype=it["stype"],
                             who=it["who"], cat3=it["cat3"], root=it["root"],
                             note=it["note"]))
            all_rows.append(dict(经历="%02d %s" % (exp["no"], exp["name"]), 用途=caps[-1]["role"],
                                 三类归属=it["cat3"], 拍摄者=it["who"], 来源桶=it["root"],
                                 转发日期=it["date_msg"] or "", 目录日期=it["date_dir"] or "",
                                 事件日期=exp["date"], 拍摄日期="待确认（微信剥离 EXIF）",
                                 日期依据=it["date_src"], 会话=it["session"], 宽=it["w"], 高=it["h"],
                                 原始路径=src, 消息备注=it["note"]))

        # ---- 联系表（候选全量，不只入选）
        sheet = None
        cand = sorted(good, key=lambda x: -x["w"])[:64]
        if cand:
            sheet_items = [dict(path=it["path"],
                                date=(it["date_msg"] or it["date_dir"] or ("事件期 " + exp["date"].split("→")[0].strip())),
                                date_src=it["date_src"], category=it["cat3"], role=it["role"],
                                session_name=it["session"] or it["root"], session_type=it["stype"],
                                width=it["w"], height=it["h"], note=it["note"], md5=it["md5"])
                           for it in cand]
            try:
                j, _ = contact_sheet(sheet_items, os.path.join(SHEETS, "EXP%02d_%s.jpg" % (
                    exp["no"], re.sub(r"[^\w\u4e00-\u9fff]", "", exp["name"])[:16])),
                    "E%02d" % exp["no"], "E%02d %s ｜ 候选 %d 张" % (exp["no"], exp["name"], len(cand)))
                sheet = j
            except Exception:
                traceback.print_exc()

        io.open(os.path.join(d, "captions.json"), "w", encoding="utf-8").write(
            json.dumps({"经历": exp["name"], "日期": exp["date"], "地点": exp["place"],
                        "标题": exp["title"], "副标题": exp["sub"], "正文": exp["body"],
                        "讲述文字": exp["narration"], "图": caps,
                        "候选总数": len(items), "可用候选": len(good)},
                       ensure_ascii=False, indent=2))
        packs.append(dict(exp=exp, main=caps[0] if caps else None, steps=caps[1:],
                          caps=caps, dir=d, sheet=sheet, n_cand=len(items), n_good=len(good)))
        print("  %02d %-26s 候选 %-4d 可用 %-4d → 入选 %d（主图%s）"
              % (exp["no"], exp["name"], len(items), len(good), len(caps),
                 "有" if caps else "★无"))
    with io.open(INDEX_CSV, "w", encoding="utf-8-sig", newline="") as f:
        if all_rows:
            wr = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            wr.writeheader(); wr.writerows(all_rows)
    return packs


# ═══════════════════════════════ PPT
def build_deck(packs):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def tb(sl, x, y, w, h):
        s = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        s.text_frame.word_wrap = True
        return s.text_frame

    def run(tf, text, size, color, bold=False, first=False, space=4):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.space_after = Pt(space)
        r = p.add_run(); r.text = text
        r.font.name = FONT; r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = RGBColor.from_string(color)
        return p

    def fit_pic(sl, path, x, y, w, h):
        """按比例放进 (x,y,w,h) 框内"""
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            with Image.open(path) as im:
                iw, ih = im.size
            if not iw or not ih:
                return
            s = min(w / iw, h / ih)
            nw, nh = iw * s, ih * s
            sl.shapes.add_picture(path, Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2),
                                  width=Inches(nw))
        except Exception:
            pass

    for i, pk in enumerate(packs, 1):
        e = pk["exp"]
        sl = prs.slides.add_slide(blank)
        tf = tb(sl, 0.95, 0.40, 11.5, 0.8)
        run(tf, e["title"], 29, C_MAIN, True, first=True, space=2)
        tf2 = tb(sl, 0.95, 1.26, 11.5, 0.45)
        run(tf2, "%s ｜ %s" % (e["date"], e["place"]), 13, C_BODY, False, first=True)
        tf2b = tb(sl, 0.95, 1.60, 11.5, 0.42)
        run(tf2b, e["sub"], 12.5, C_ACC, False, first=True)

        tfl = tb(sl, 0.95, 2.20, 5.25, 4.3)
        run(tfl, "我做了什么", 16, C_ACC, True, first=True, space=6)
        for b in e["body"]:
            run(tfl, "· " + b, 12.5, C_BODY, False, space=6)

        if pk["main"]:
            fit_pic(sl, pk["main"]["dst"], 6.55, 2.10, 6.05, 3.35)
            cap = pk["main"]
            tfm = tb(sl, 6.55, 5.48, 6.05, 0.30)
            run(tfm, "%s ｜ %s ｜ %s" % (cap["role"], cap["cat3"][:14], cap["who"][:18]),
                9, C_BODY, False, first=True)
        x = 6.55
        for it in pk["steps"][:3]:
            fit_pic(sl, it["dst"], x, 5.86, 1.90, 1.15)
            x += 2.02
        tf3 = tb(sl, 0.8, 7.06, 9.2, 0.36)
        run(tf3, FOOTER, 10.5, C_BODY, False, first=True)
        tf4 = tb(sl, 11.9, 7.06, 1.0, 0.36)
        p = tf4.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
        r = p.add_run(); r.text = str(i)
        r.font.name = FONT; r.font.size = Pt(11); r.font.bold = True
        r.font.color.rgb = RGBColor.from_string(C_ACC)

    prs.save(DECK)
    return DECK


# ═══════════════════════════════ HTML
def build_preview(packs):
    H = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<title>汇报页面材料包（第二批）2026-10-06</title><style>',
         '*{box-sizing:border-box}body{margin:0;background:#f7f6f3;color:#22201d;',
         'font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}',
         '.wrap{max-width:1150px;margin:0 auto;padding:38px 26px 80px}',
         'h1{font-size:25px;margin:0 0 6px}h2{font-size:18px;margin:34px 0 10px;',
         'padding-bottom:7px;border-bottom:2px solid #e5e1da}',
         'table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0}',
         'th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}',
         'th{background:#efece6;font-weight:600}',
         '.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.bad{background:#fdeeee;border-left:4px solid #c0392b;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.pack{background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:16px 18px;margin:14px 0}',
         '.pack h3{margin:0 0 2px;font-size:17px;color:#1F3D2B}',
         '.pack .meta{color:#6b6660;font-size:12.5px;margin-bottom:10px}',
         '.imgs{display:flex;gap:9px;flex-wrap:wrap;margin:10px 0}',
         '.imgs figure{margin:0;flex:0 0 auto}',
         '.imgs img{display:block;border:1px solid #e5e1da;border-radius:4px;object-fit:cover}',
         '.imgs figcaption{font-size:11.5px;color:#6b6660;margin-top:3px;max-width:215px}',
         '.body{font-size:13.5px;color:#3a3733}',
         'blockquote{margin:10px 0;padding:10px 16px;background:#f2f0eb;border-radius:0 6px 6px 0;',
         'border-left:3px solid #b4b2a9;font-size:13.5px;color:#3a3733}',
         'code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:11.5px;word-break:break-all}',
         '.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin-right:4px}',
         '.t1{background:#e8f2ea;color:#1F3D2B}.t2{background:#fdf0e6;color:#9E3B2E}.t3{background:#eef0f6;color:#3b4a6b}',
         '.foot{margin-top:50px;padding-top:14px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}',
         '</style></head><body><div class="wrap">']
    A = H.append
    A("<h1>汇报页面材料包（第二批）</h1>")
    A('<p style="color:#6b6660;font-size:13px">生成 %s ｜ %d 段经历 ｜ 视觉沿用已有汇报（16:9 · 微软雅黑 · #1F3D2B / #9E3B2E）</p>'
      % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(packs)))
    A('<div class="ok"><b>每包含 7 项</b>：① 名称/日期/地点 ② 我的具体贡献及成果 ③ 一张主图 + 2–4 张过程图 '
      '④ 每张图的原始路径与拍摄者信息 ⑤ 可直接放进 PPT 的标题与正文 ⑥ 可直接念的讲述文字 ⑦ 一页可编辑 PPT 草稿。</div>')
    A('<div class="warn"><b>★ 拍摄者口径（严格按 role，不猜）</b>：'
      '<code>role=me</code> → 「我发出」；<code>role=them</code> → 「他人发来」；'
      '策展集/项目目录无 role 语义 → <b>「拍摄者待确认」</b>。</div>')
    A('<div class="warn"><b>★ 日期口径</b>：微信**已剥离 EXIF**，<b>拍摄日期拿不到</b>。'
      '本表给出的是 <b>转发日期</b>（微信消息时间 / 朋友圈发帖时间，有依据）、'
      '<b>目录日期</b>（微信按月导出，仅到月）、<b>事件日期</b>（经历区间）。'
      '拍摄日期一律标注「待确认」，不做推断。</div>')
    A('<div class="bad"><b>★ 证据规则（已生效）</b>：群内零发言只能说明「群聊中未找到参与证据」，'
      '<b>不能断定没有参加</b>；培训/公示/名单只构成时间链，'
      '个人角色仍需对应到名单或本人行动记录；<b>团队成果不直接等同个人贡献</b>。</div>')
    A('<p><b>可直接用的 PPT：</b><code>%s</code>（%d 页，可编辑）</p>' % (DECK, len(packs)))
    A('<p><b>入选原图索引：</b><code>%s</code></p>' % INDEX_CSV)

    for pk in packs:
        e = pk["exp"]
        A('<div class="pack">')
        A("<h3>%d. %s</h3>" % (e["no"], e["title"]))
        A('<div class="meta">%s ｜ %s ｜ 候选 %d 张 / 可用 %d 张 / 入选 %d 张</div>'
          % (e["date"], e["place"], pk["n_cand"], pk["n_good"], len(pk["caps"])))
        A('<div class="imgs">')
        for c in pk["caps"][:5]:
            src = "file:///" + c["dst"].replace("\\", "/")
            t = "t1" if c["cat3"].startswith("①") else ("t2" if c["cat3"].startswith("②") else "t3")
            A('<figure><img src="%s" style="height:%dpx" alt="%s">'
              '<figcaption><span class="tag %s">%s</span><br>%s<br>%s</figcaption></figure>'
              % (src, 205 if c["n"] == 1 else 140, c["role"], t, c["role"],
                 c["date_msg"] or c["date_dir"] or "日期待定",
                 c["who"][:22]))
        A("</div>")
        A('<div class="body"><b>我做了什么：</b><ul>')
        for b in e["body"]:
            A("<li>%s</li>" % b)
        A("</ul></div>")
        A("<b>可直接念的讲述文字：</b>")
        A("<blockquote>%s</blockquote>" % e["narration"])
        if pk["sheet"]:
            A("<p style='font-size:13px'>候选联系表：<code>%s</code></p>" % pk["sheet"])
        A("<details><summary style='cursor:pointer;font-size:13px;color:#24476f'>图源明细（原始路径 / 拍摄者 / 三类归属 / 日期）</summary>")
        A("<table><tr><th>#</th><th>用途</th><th>三类归属</th><th>转发日期</th><th>来源会话</th><th>拍摄者</th><th>原始路径</th></tr>")
        for c in pk["caps"]:
            A("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td></tr>"
              % (c["n"], c["role"], c["cat3"], c["date_msg"] or c["date_dir"] or "—",
                 (c["session"] or "—")[:20], c["who"], c["src"]))
        A("</table></details>")
        A("</div>")

    A('<div class="foot">工具 <code>tools\\build_ppt_packs.py</code> ｜ '
      '联系表 <code>_tmp\\sheets\\EXP*.jpg</code> ｜ 材料包 <code>_tmp\\ppt_packs\\</code> ｜ '
      '<b>内部资料，不得外传</b></div>')
    A("</div></body></html>")
    io.open(PREVIEW, "w", encoding="utf-8").write("\n".join(H))
    return PREVIEW


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--no-deck", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    packs = build_packs()
    p = build_preview(packs)
    print("→ %s" % p)
    if not a.no_deck:
        try:
            d = build_deck(packs)
            print("→ %s（%d 页可编辑 PPT）" % (d, len(packs)))
        except Exception:
            traceback.print_exc()
    n_img = sum(len(pk["caps"]) for pk in packs)
    print("入选图合计 %d 张" % n_img)


if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
