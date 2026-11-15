# -*- coding: utf-8 -*-
r"""
build_ppt_packs_b3.py —— 第三批：国际交流 / 开街活动 两段新经历材料包
                          + 主 PPT 17 页配图体检表

为什么是这两段：
  主 PPT（照片版，17 页）逐页体检后发现 ——
    · 第 13 页「国际交流：英国大使馆与亚当斯密商学院」→ 第二批没做过材料包
    · 第 10 页「开街活动与传播」→ 第二批没做过材料包（且主 PPT 只有 3 张图）
    · 第 15 页「技术赋能：AI 与交互技术」→ **0 张图**（全篇唯一无图页）
  故第三批补 09 / 10 两段；第 15 页的补图建议放在配图体检表里。

★ 与第二批的差异（口径修正）
  · `DB_EXCLUDE` 放开 `汇报照片素材` / `PPT用图` —— 这两桶正是国际交流线的图源
  · 新增 `pathfilter`：同一 root 里跨经历混装时按路径正则收窄
    （`汇报照片素材` 同时装着 校友会/论坛/接待/版画/支教 五条线）
  · 保留第二批全部纪律：弱日期 root 必须关键词命中、朋友圈只取 role=me、
    拍摄者严格按 role 判定、日期四类分列

★ 诚实边界
  · `20_亚当斯密_会场1.jpg` 实测仅 118×210（缩略图）→ 已标注不可用，不入选
  · `60_厦门版画实验_1/2/3` 实测 570×380 / 380×390 / 250×386 → 太小，不可用
  · 开街活动全库仅 3 张 → 如实标注缺口

用法
----
  python tools\build_ppt_packs_b3.py --build
  python tools\build_ppt_packs_b3.py --build --no-deck
"""
import os
import re
import io
import sys
import csv
import json
import shutil
import sqlite3
import argparse
import datetime
import subprocess
import traceback
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ppt_packs as B  # noqa: E402

WS = B.WS
RUNSTAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

DECK = os.path.join(WS, "中期汇报_经历页_第三批_2026-10-06.pptx")
PREVIEW = os.path.join(WS, "汇报页面材料包_第三批_2026-10-06.html")
INDEX_CSV = os.path.join(WS, "入选原图索引_第三批_2026-10-06.csv")
AUDIT = os.path.join(WS, "主PPT17页_配图体检_2026-10-06.html")

MASTER_DECK = os.path.join(
    r"C:\Users\wardc\Desktop\中期汇报_2026-09\06_PPT成品",
    "中期汇报_社会美育与乡村振兴_照片版_蔡浩文_12250300012.pptx")

# ═══════════════════════════════ 第三批经历（2 段）
EXP3 = [
    dict(no=9, name="国际交流（英国大使馆 × 亚当斯密商学院）",
         date="2025-09 → 2026-09", place="英国驻华使馆大使官邸（光华路15号）/ 亮马桥希尔顿 / 北京",
         # ★★ 只取**用户自己策展的** `09_PPT用图`（亚当斯密 21–24 / 大使馆电影季 25–26）。
         #   为什么不取 `汇报照片素材\08_英国校友会活动`（210 张）：
         #   实测那 210 张里绝大多数是**校友群转发的电影海报、活动海报、招募二维码、
         #   拍屏幕的界面照**（含手机号），连续三次把自动选图带偏
         #   （公众号编辑器截图 → 橙色报名二维码 → 《得闲谨制》电影海报）。
         #   群转发图另出联系表 `_tmp\sheets\SRC_校友会群转发图.jpg` 供人工筛，
         #   不自动进 PPT。
         lo=None, hi=None,
         roots=["PPT用图"],
         pathfilter=r"亚当斯密|大使馆|电影季",
         cur=[], kw=["亚当斯密", "大使馆", "电影季"],
         title="国际交流：英国大使馆与亚当斯密商学院",
         sub="校友会活动的组织与参与 · 2025—2026",
         body=[
             "英国大使馆 · 2025 英国电影季：2025年9月23日于英国使馆大使官邸（光华路15号），"
             "英国驻华使馆与苏格兰政府办公室联袂举办，庆祝 2025 英国电影季与苏格兰政府驻华办公室成立 20 周年，"
             "我协助校友会报名与组织参与。",
             "格拉斯哥大学亚当·斯密商学院《国富论》250 周年：参与 2026年4月7日北京站庆典（亮马桥希尔顿）"
             "与北京大学经济学院联合研讨会。",
             "我参与校友会活动的筹备、分工与传播，作为商学院校友代表参与组织。",
             "同期担任格拉斯哥大学北京校友会公众号编辑：推文撰写、秀米排版、联合活动转载对接。",
             "★ 口径：校友会活动是**组织与参与**，不是学术产出；公众号编辑是可佐证的具体产出。",
             "⚠️ **图源口径**：本页只用**用户自己策展的 `09_PPT用图`**（亚当斯密 21–24 / 大使馆电影季 25–26）。"
             "校友群转发的 210 张图**不进 PPT** —— 实测其中绝大多数是电影海报、活动海报、招募二维码、"
             "拍屏幕的界面照，无法作为现场影像使用；另出联系表供人工筛。",
         ],
         narration="国际交流这条线，我做的是「组织与参与」。"
                   "2025 年 9 月，英国使馆和苏格兰政府办公室在大使官邸办英国电影季，"
                   "我帮着校友会报名、组织大家去。"
                   "2026 年 4 月，亚当·斯密商学院《国富论》250 周年北京站，"
                   "我作为商学院校友代表参与筹备和分工。"
                   "同时我还是格拉斯哥大学北京校友会公众号的编辑，负责推文和排版。"),

    dict(no=10, name="开街活动（长城国际动漫谷 2026-08-02）",
         date="2026-08-02", place="北京市怀柔区渤海镇洞台村 · 长城国际动漫谷",
         # ★ 同样不设日期窗：`09_PPT用图\40/42` 的 date 是 2026-09-01（策展时间），
         #   设 hi=2026-08-31 会把它俩挡掉 → 只剩 1 张。开街素材本来就少，不能再漏。
         lo=None, hi=None,
         roots=["PPT用图", "井邻宣传", "井邻项目", "朋友圈"],
         pathfilter=r"开街|动漫谷|集章|寻街|沙龙",
         cur=[], kw=["开街", "动漫谷", "集章", "寻街", "沙龙", "游客", "官媒"],
         title="在地实践：长城国际动漫谷开街",
         sub="2026年8月2日 · 原定 7月11日，受台风「巴威」影响延期",
         body=[
             "活动当天我承担现场保障：集章打卡（10:00—16:00）与「动漫遇见乡村」沙龙论坛的现场执行。",
             "领导寻街（10:30—11:00）环节我负责引导与讲解；会议结束后协调领导用餐。",
             "我引导现场游客关注工作站小红书，并转发官媒报道扩大传播。",
             "领导现场指出门口英文拼写问题，我当日协调整改完成。",
             "★ 口径：开街是**团队活动**；我个人的部分是现场执行、讲解引导与整改。",
             "⚠️ **照片缺口（如实标注）**：全库仅 3 张（`09_PPT用图\\40/41/42_开街_*`），"
             "且画面以**工作站门头与陈列作品**为主 —— **没有开街当天的人流与活动现场照**。"
             "需本人补拍或向活动方索取。",
         ],
         narration="8 月 2 号长城国际动漫谷开街，原定是 7 月 11 号，"
                   "因为台风「巴威」延期了。当天我做的是现场保障——"
                   "集章打卡、动漫遇见乡村的沙龙论坛，还有领导寻街的引导和讲解。"
                   "领导当场指出门口英文拼写有问题，我当天就协调改完了。"
                   "这块照片比较少，现场图只有三张。"),
]

# ═══════════════════════════════ 主 PPT 17 页 → 主题
PAGE_TOPIC = [
    (1, "封面", []),
    (2, "目录", []),
    (3, "个人概况与研究定位", []),
    (4, "研究方向的内涵", []),
    (5, "一年实践 · 数据看板", []),
    (6, "实践主线一：洞台村乡村美育工作站", [1]),
    (7, "技法支撑：版画三技", [3]),
    (8, "工作坊运营与成果", [1]),
    (9, "对外服务：8批次接待与讲解", [1]),
    (10, "开街活动与传播", [10]),
    (11, "社会服务：知行计划 · 澜沧支教", [2]),
    (12, "学术会务：第五届美学与艺术研究学术研讨会", [4]),
    (13, "国际交流：英国大使馆与亚当斯密商学院", [9]),
    (14, "研究探索：经济学 × 艺术", []),
    (15, "技术赋能：AI 与交互技术", [8]),
    (16, "问题反思与下一阶段计划", []),
    (17, "恳请批评指正", []),
]

# 建议阈值：主 PPT 每页正文页至少 3 张图才不空
MIN_PICS = 3

# ★ 已人工策展的图源 → 不做画面质量过滤（避免误杀黑白肖像/设计稿）
TRUSTED_ROOTS = {"PPT用图"}

# ★ 「幻灯片友好」过滤 —— 体检表推荐用图时排除印刷分色件
#   坑：`pick()` 按宽度降序取，会把 14031×9921 的 CMYK 硫酸纸分版 TIF、
#   3307×3552 的 1bit BMP 网版当「最佳主图」。这些是**制版文件**，不是画面素材。
SLIDE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
SEP_PAT = re.compile(r"POSITIVE|NEGATIVE|1bit|分版|菲林|网版|硫酸纸|_SEP", re.I)


def slide_ok(path, w, h):
    if os.path.splitext(path)[1].lower() not in SLIDE_EXT:
        return False
    if (w or 0) < 1200 or not h:
        return False
    r = w / float(h)
    if r < 0.45 or r > 2.3:          # 太竖/太横都不适合 16:9 版面
        return False
    if SEP_PAT.search(os.path.basename(path)):
        return False
    return True


# ═══════════════════════════════ 画面质量判别（排除截图 / 文档 / 纯色图）
_QUAL_CACHE = {}


def photo_qual(path):
    """返回 (饱和度均值, 亮度均值, 灰度标准差, 纯黑白占比, 近灰占比)，均归一化到 0–1。"""
    if path in _QUAL_CACHE:
        return _QUAL_CACHE[path]
    try:
        from PIL import Image, ImageStat
        import numpy as np
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(path) as im:
            rgb = im.convert("RGB").resize((200, 200))
        hsv = rgb.convert("HSV")
        sm = ImageStat.Stat(hsv).mean
        gs = ImageStat.Stat(rgb.convert("L")).stddev[0]
        g = np.asarray(rgb.convert("L"))
        bw = float(((g >= 250) | (g <= 5)).mean())
        S = np.asarray(hsv)[:, :, 1].astype("float32") / 255.0
        gray = float((S < 0.10).mean())          # ★ 近灰像素占比 = 最强判据
        out = (sm[1] / 255.0, sm[2] / 255.0, gs / 255.0, bw, gray)
    except Exception:
        out = None
    _QUAL_CACHE[path] = out
    return out


def doc_like(path):
    """★★ 明显「不是画面素材」的图 —— 排除，防止被选成 PPT 主图。

    坑（2026-10-06 实测，国际交流段连续翻车三次）：
      ① 先选出 **微信公众号编辑器界面截图**（几乎全白，画着红框箭头）
      ② 加低饱和过滤后 → 换成 **橙色报名二维码海报**（高饱和，躲过）
      ③ 再加纯黑白过滤后 → 换成 **拍摄电脑屏幕的照片**
         （公众号绑定界面，带手机号 28221751313 —— **还是 PII 风险**）

    可靠判据（实测分得很干净）：
      A. **低饱和 + 高亮度**（S<0.12 且 V>0.85）→ 白底截图/文档/白底海报
         公众号编辑器截图 S=0.021 V=0.992 ；真实课堂照 S=0.19–0.26 V=0.54–0.59
      B. **纯黑白占比 ≥0.15** → 高对比文档 / 二维码海报 / 长图
         白底长图 0.63–0.70 ；二维码海报 0.20–0.52 ；真实照片 **0.000**
      C. **★ 近灰占比 ≥0.55**（饱和度 <0.10 的像素）→ 屏幕截图 / 文档 / 拍屏幕的照片
         屏幕照 0.86–0.90 ；文档 0.65 ；**真实照片 0.002–0.04**

    ★★ 诚实边界：**「彩色海报」仍无法自动识别**。试过 edge / 平坦度 /
      颜色多样性 / 中央裁切，都不行 —— 实测彩色二维码海报 flat=0.71，
      而暗光会场照 flat=0.73（真照片反而更平坦）。故不做海报判别，
      改为在排序里把「近灰占比」当权重（见 pick3），并在产物里把主图
      标为「自动推荐 · 待人工确认」。
    """
    q = photo_qual(path)
    if not q:
        return False
    s, v, gs, bw, gray = q
    return (s < 0.12 and v > 0.85) or gs < 0.10 or bw >= 0.15 or gray >= 0.55


def pick3(items, min_w=700, min_bytes=40000):
    """在 B.pick 之前做三件事：① 剔除明显非画面素材 ② 主图限定「幻灯片形状」
    ③ 主图在同优先级里优先选「近灰占比低」（最像照片）的那张。

    ★ 递归坑：必须先保存原函数引用（`_orig_pick`），否则 main 里
      `B.pick = pick3` 之后这里再调 `B.pick(...)` 会无限递归（实测踩过）。

    ★ 全景坑：只用 B.pick 时主图会选到 5426×1280 的全景长条（比例 4.24），
      塞进 6.05×3.35in 的框里上下留大片空白。故主图池限定 长宽比 0.5–2.2。
    """
    clean = [it for it in items if not it.get("doc_like")]
    if len(clean) < 2:
        clean = items
    shaped = [it for it in clean
              if it["h"] and 0.5 <= it["w"] / float(it["h"]) <= 2.2]
    pool = shaped if len(shaped) >= 2 else clean
    good = [it for it in pool if it["w"] >= min_w and it["bytes"] >= min_bytes]
    if len(good) < 2:
        good = [it for it in pool if it["w"] >= 500]
    if not good:
        return None, [], []

    PRI = {"② 记录我工作过程（我产出的设计/作品）": 0, "① 我拍摄/记录成果": 1,
           "② 记录我工作过程（导师记录/现场）": 2, "③ 项目整体现场与成果": 3}
    good.sort(key=lambda it: (PRI.get(it["cat3"], 9),
                              it.get("gray") or 0.0,     # ★ 近灰占比低的更像照片
                              it.get("bw") or 0.0,
                              -it["w"]))
    main = good[0]

    rest = [it for it in good[1:]]
    rest.sort(key=lambda x: (x["date_msg"] or x["date_dir"] or "9999"))
    steps, used = [], _Counter()
    for it in rest:
        if used[it["cat3"]] >= 2:
            continue
        steps.append(it); used[it["cat3"]] += 1
        if len(steps) >= 3:
            break
    if len(steps) < 3:
        for it in rest:
            if it not in steps:
                steps.append(it)
            if len(steps) >= 3:
                break
    return main, steps[:3], good


_orig_pick = B.pick
_Counter = Counter


# ═══════════════════════════════ 取图（按 root 分别查询）
_orig_gather = B.gather


def gather3(exp, limit_per_root=40):
    """★★★ 与 B.gather 的关键差异：**按 root 分别查询**。

    坑（2026-10-06 新踩）：`B.gather` 用的是**一条** SQL
        select * from photos where root in (...) order by width desc limit 3000
    当 root 集合里含 `朋友圈`（7,806 行）时，`order by width desc` 会让
    结果集被大图占满，**width 较小的小编号策展图直接被 limit 挤出去**。
    实测：开街段 root 含朋友圈 → `09_PPT用图\40_开街_活动1.jpg`(1280px) 与
    `41`(986px) 被截断，3 张只剩 1 张，而且**不报错**。
    修法：每个 root 各发一条 SQL（各带自己的 limit），再合并去重。
    """
    kws = exp.get("kw") or []
    items, seen, sns_pool = [], set(), []
    c = B._conn()
    for root in [r for r in (exp.get("roots") or []) if r not in B.DB_EXCLUDE]:
        w, a = ["root=?"], [root]
        if exp.get("lo"):
            w.append("date>=?"); a.append(exp["lo"])
        if exp.get("hi"):
            w.append("date<=?"); a.append(exp["hi"])
        sql = ("select * from photos where " + " and ".join(w) +
               " order by width desc limit %d" % max(limit_per_root, 2000))
        for r in c.execute(sql, a):
            blob = (r["path"] or "") + " " + (r["session_name"] or "") + " " + (r["note"] or "")
            hit = sum(1 for k in kws if k in blob) if kws else 0
            if root == "朋友圈":
                if r["role"] == "me":
                    sns_pool.append((hit, r))
                continue
            if r["md5"] in seen:
                continue
            if kws and hit == 0:
                continue
            if root in B.WEAK_DATE_ROOTS and (not kws or hit == 0):
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
                cat3=B.three_class(r["role"], r["root"], r["category"], r["session_name"]),
                who=B.photographer(r["role"], r["session_name"], "数据库")))
    c.close()

    # ---- 直扫目录（策展成品集，不入库）
    for dpath, dlabel in (exp.get("dirs") or []):
        if not os.path.isdir(dpath):
            continue
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".hevc"}
        for dp, _ds, fs in os.walk(dpath):
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

    # ---- 朋友圈（他本人发的）——先按关键词；整体候选 < 4 才放宽
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
        add_sns([(h, r) for h, r in sns_pool if h > 0])
        if len(items) < 4:
            add_sns(sns_pool)

    # ---- 画面质量标注（截图/文档类 + 近灰占比 + 纯黑白占比）—— 供 pick3 排除与排序
    # ★ 已人工策展的图源不做质量过滤：`PPT用图` 是用户自己挑过的，
    #   再过滤只会误杀（实测 `25_大使馆电影季_肖像.jpg` 是**黑白肖像**，
    #   gray=0.96 被误判为文档）。
    for it in items:
        q = photo_qual(it["path"])
        it["doc_like"] = False if it["root"] in TRUSTED_ROOTS else doc_like(it["path"])
        it["gray"] = q[4] if q else 0.0
        it["bw"] = q[3] if q else 0.0

    # ---- 路径正则收窄（同一 root 跨经历混装时用）
    pf = exp.get("pathfilter")
    if pf:
        pat = re.compile(pf)
        items = [it for it in items
                 if pat.search("%s %s %s" % (it.get("path") or "", it.get("note") or "",
                                             it.get("session") or ""))]
    return items


def counts(exp, g=None):
    """只统计，不落盘（用于配图体检表）。g 缺省用第三批的 gather3。"""
    items = (g or gather3)(exp)
    _main, _steps, good = B.pick(items)
    return items, good


# ═══════════════════════════════ HTML
CSS = (
    '*{box-sizing:border-box}body{margin:0;background:#f7f6f3;color:#22201d;'
    'font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}'
    '.wrap{max-width:1150px;margin:0 auto;padding:38px 26px 80px}'
    'h1{font-size:25px;margin:0 0 6px}h2{font-size:18px;margin:34px 0 10px;'
    'padding-bottom:7px;border-bottom:2px solid #e5e1da}'
    'table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0}'
    'th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}'
    'th{background:#efece6;font-weight:600}'
    '.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}'
    '.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}'
    '.bad{background:#fdeeee;border-left:4px solid #c0392b;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}'
    '.pack{background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:16px 18px;margin:14px 0}'
    '.pack h3{margin:0 0 2px;font-size:17px;color:#1F3D2B}'
    '.pack .meta{color:#6b6660;font-size:12.5px;margin-bottom:10px}'
    '.imgs{display:flex;gap:9px;flex-wrap:wrap;margin:10px 0}'
    '.imgs figure{margin:0;flex:0 0 auto}'
    '.imgs img{display:block;border:1px solid #e5e1da;border-radius:4px;object-fit:cover}'
    '.imgs figcaption{font-size:11.5px;color:#6b6660;margin-top:3px;max-width:215px}'
    '.body{font-size:13.5px;color:#3a3733}'
    'blockquote{margin:10px 0;padding:10px 16px;background:#f2f0eb;border-radius:0 6px 6px 0;'
    'border-left:3px solid #b4b2a9;font-size:13.5px;color:#3a3733}'
    'code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:11.5px;word-break:break-all}'
    '.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin-right:4px}'
    '.t1{background:#e8f2ea;color:#1F3D2B}.t2{background:#fdf0e6;color:#9E3B2E}.t3{background:#eef0f6;color:#3b4a6b}'
    '.foot{margin-top:50px;padding-top:14px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}'
    '.gap{color:#9E3B2E;font-weight:600}'
    '.fine{color:#3f9d54;font-weight:600}'
)


def _head(title, sub):
    return ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
            '<title>%s</title><style>%s</style></head><body><div class="wrap">' % (title, CSS),
            "<h1>%s</h1>" % title,
            '<p style="color:#6b6660;font-size:13px">%s</p>' % sub]


def build_preview3(packs):
    H = _head("汇报页面材料包（第三批）",
              "生成 %s ｜ %d 段经历 ｜ 视觉沿用已有汇报（16:9 · 微软雅黑 · #1F3D2B / #9E3B2E）"
              % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(packs)))
    A = H.append
    A('<div class="ok"><b>每包含 7 项</b>：① 名称/日期/地点 ② 我的具体贡献及成果 ③ 一张主图 + 2–4 张过程图 '
      '④ 每张图的原始路径与拍摄者信息 ⑤ 可直接放进 PPT 的标题与正文 ⑥ 可直接念的讲述文字 ⑦ 一页可编辑 PPT 草稿。</div>')
    A('<div class="ok"><b>本批新开的图源</b>：<code>汇报照片素材</code>（策展成品集，含英国校友会活动 210 张）'
      '与 <code>PPT用图</code>（策展精选 33 张）。第二批把这两桶排除是为了防重复，'
      '本批用 <code>pathfilter</code> 按路径正则收窄后启用。</div>')
    A('<div class="warn"><b>★ 新增「画面质量」过滤（本批首次启用）</b>：'
      '第二批的选图只按「三类归属 + 分辨率」排序，对画面内容零判断 —— '
      '实测国际交流段自动选出的<b>主图是一张微信公众号编辑器界面截图</b>（几乎全白、上面画着红框箭头）。'
      '本批加入判别器：<b>低饱和（S&lt;0.12）且高亮度（V&gt;0.85）</b>，或灰度标准差 &lt;0.10 → 判为截图/文档，'
      '不参与主图/过程图挑选（<b>但仍保留在候选池与联系表里</b>，可人工复核）。</div>')
    A('<div class="warn"><b>★ 拍摄者口径（严格按 role，不猜）</b>：'
      '<code>role=me</code> → 「我发出」；<code>role=them</code> → 「他人发来」；'
      '策展集/项目目录无 role 语义 → <b>「拍摄者待确认」</b>。'
      '校友会照片全部来自微信群 → 一律「拍摄者待确认」。</div>')
    A('<div class="warn"><b>★ 日期口径</b>：微信<b>已剥离 EXIF</b>，<b>拍摄日期拿不到</b>。'
      '本表给出 <b>转发日期</b>（微信消息时间 / 朋友圈发帖时间）、<b>目录日期</b>、'
      '<b>事件日期</b>；拍摄日期一律「待确认」。</div>')
    A('<div class="bad"><b>★ 实测不可用图（已剔除，勿再选用）</b>：'
      '<code>20_亚当斯密_会场1.jpg</code> 仅 <b>118×210</b>；'
      '<code>60_厦门版画实验_1/2/3</code> 仅 <b>570×380 / 380×390 / 250×386</b>。'
      '这些是缩略图，放进 16:9 页面会糊。</div>')
    A('<p><b>可直接用的 PPT：</b><code>%s</code>（%d 页，可编辑）</p>' % (DECK, len(packs)))
    A('<p><b>入选原图索引：</b><code>%s</code></p>' % INDEX_CSV)
    A('<p><b>主 PPT 配图体检：</b><code>%s</code></p>' % AUDIT)

    for pk in packs:
        e = pk["exp"]
        A('<div class="pack">')
        A("<h3>%d. %s</h3>" % (e["no"], e["title"]))
        A('<div class="meta">%s ｜ %s ｜ 候选 %d 张（其中截图/文档类 %d 张已排除）'
          ' / 可用 %d 张 / 入选 %d 张</div>'
          % (e["date"], e["place"], pk["n_cand"], pk.get("n_doc", 0),
             pk["n_good"], len(pk["caps"])))
        A('<div class="warn" style="margin:8px 0"><b>主图为自动推荐 · 请人工确认</b>：'
          '自动选图只能排除「低饱和白底截图」与「纯黑白占比≥0.15 的文档/二维码海报」，'
          '<b>无法可靠区分彩色海报与暗光现场照</b>。请对照候选联系表确认或替换主图。</div>')
        A('<div class="imgs">')
        for c in pk["caps"][:5]:
            src = "file:///" + c["dst"].replace("\\", "/")
            t = "t1" if c["cat3"].startswith("①") else ("t2" if c["cat3"].startswith("②") else "t3")
            A('<figure><img src="%s" style="height:%dpx" alt="%s">'
              '<figcaption><span class="tag %s">%s</span><br>%s<br>%s</figcaption></figure>'
              % (src, 205 if c["n"] == 1 else 140, c["role"], t, c["role"],
                 c["date_msg"] or c["date_dir"] or "日期待定", c["who"][:22]))
        A("</div>")
        A('<div class="body"><b>我做了什么：</b><ul>')
        for b in e["body"]:
            A("<li>%s</li>" % b)
        A("</ul></div>")
        A("<b>可直接念的讲述文字：</b>")
        A("<blockquote>%s</blockquote>" % e["narration"])
        if pk["sheet"]:
            A("<p style='font-size:13px'>候选联系表：<code>%s</code></p>" % pk["sheet"])
        A("<details><summary style='cursor:pointer;font-size:13px;color:#24476f'>"
          "图源明细（原始路径 / 拍摄者 / 三类归属 / 日期）</summary>")
        A("<table><tr><th>#</th><th>用途</th><th>三类归属</th><th>转发日期</th>"
          "<th>来源会话</th><th>拍摄者</th><th>原始路径</th></tr>")
        for c in pk["caps"]:
            A("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
              "<td><code>%s</code></td></tr>"
              % (c["n"], c["role"], c["cat3"], c["date_msg"] or c["date_dir"] or "—",
                 (c["session"] or "—")[:20], c["who"], c["src"]))
        A("</table></details>")
        A("</div>")

    A('<div class="foot">工具 <code>tools\\build_ppt_packs_b3.py</code> ｜ '
      '联系表 <code>_tmp\\sheets\\EXP*.jpg</code> ｜ 材料包 <code>_tmp\\ppt_packs\\</code> ｜ '
      '<b>内部资料，不得外传</b></div>')
    A("</div></body></html>")
    io.open(PREVIEW, "w", encoding="utf-8").write("\n".join(H))
    return PREVIEW


# ═══════════════════════════════ 主 PPT 配图体检
def master_page_pics(path):
    """读主 PPT：每页的图片张数 + 标题"""
    from pptx import Presentation
    out = {}
    prs = Presentation(path)
    for i, s in enumerate(prs.slides, 1):
        pics, head = 0, ""
        for sh in s.shapes:
            if sh.__class__.__name__ == "Picture":
                pics += 1
            if sh.has_text_frame and sh.text_frame.text.strip() and not head:
                head = sh.text_frame.text.strip().split("\n")[0]
        out[i] = (head, pics)
    return out


def build_audit(packs2, packs3):
    """主 PPT 17 页逐页配图体检 + 具体补图建议"""
    mp = master_page_pics(MASTER_DECK)
    expmap = {}
    for pk in list(packs2) + list(packs3):
        expmap[pk["exp"]["no"]] = pk
    # 第三批的 good 列表没随 build_packs 返回 → 现算（只有 2 段，很便宜）
    for pk in packs3:
        if "good" not in pk:
            _it, gd = counts(pk["exp"])
            pk["good"] = gd

    H = _head("主 PPT 17 页配图体检",
              "基准：<code>%s</code> ｜ 体检 %s"
              % (os.path.basename(MASTER_DECK), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    A = H.append
    A('<div class="ok"><b>体检口径</b>：以「主 PPT 现状图数」对「本机可用候选图数（≥700px 且 ≥40KB）」。'
      '判定阈值：正文页 <b>≥3 张</b>为合格；<b>0 张</b>为严重缺口；1–2 张为偏薄。</div>')

    A("<h2>一、逐页体检表</h2>")
    A("<table><tr><th>页</th><th>标题</th><th>现有图</th><th>可用候选</th>"
      "<th>缺口判定</th><th>可用素材来源</th></tr>")
    rows = []
    for no, topic, exps in PAGE_TOPIC:
        head, pics = mp.get(no, (topic, 0))
        n_avail = 0
        srcs = []
        for x in exps:
            pk = expmap.get(x)
            if pk:
                n_avail += pk["n_good"]
                srcs.append("%02d %s（可用 %d）" % (x, pk["exp"]["name"][:14], pk["n_good"]))
        if pics == 0 and exps:
            verdict = '<span class="gap">★ 严重缺口（0 图，但素材充足）</span>'
        elif pics == 0:
            verdict = '<span class="gap">★ 无图（且本机无对应素材）</span>'
        elif pics < MIN_PICS and n_avail >= MIN_PICS:
            verdict = '<span class="gap">偏薄（%d 张，可补到 ≥%d）</span>' % (pics, MIN_PICS)
        elif pics < MIN_PICS:
            verdict = '<span class="gap">偏薄（素材也不足）</span>'
        else:
            verdict = '<span class="fine">合格</span>'
        rows.append((no, head or topic, pics, n_avail, verdict, "；".join(srcs) or "—"))
        A("<tr><td>%d</td><td>%s</td><td>%d</td><td>%d</td><td>%s</td><td>%s</td></tr>"
          % (no, head or topic, pics, n_avail, verdict, "；".join(srcs) or "—"))
    A("</table>")

    n0 = sum(1 for r in rows if r[2] == 0)
    nthin = sum(1 for r in rows if 0 < r[2] < MIN_PICS)
    A('<div class="bad"><b>结论</b>：17 页中 <b>%d 页完全没有图</b>，<b>%d 页偏薄（1–2 张）</b>，'
      '其余合格。最该先补的是「有素材但 0 图」的页 —— 素材已在库，只是没放进去。</div>' % (n0, nthin))

    # ---- 需要补图的页：给具体推荐
    A("<h2>二、需要补图的页 · 具体推荐图</h2>")
    for no, topic, exps in PAGE_TOPIC:
        head, pics = mp.get(no, (topic, 0))
        if pics >= MIN_PICS:
            continue
        A('<div class="pack"><h3>第 %d 页 · %s</h3>' % (no, head or topic))
        A('<div class="meta">现有 %d 张 ｜ 判定：%s</div>'
          % (pics, "无图" if pics == 0 else "偏薄"))
        if not exps:
            kind = "封面 / 目录" if no <= 2 else "反思 / 致谢"
            A('<p style="font-size:13.5px">该页属<b>%s</b>类，本机无对应照片素材；'
              '建议用图表、示意图或数据看板替代，不必强塞照片。</p>' % kind)
        else:
            cand = []
            for x in exps:
                pk = expmap.get(x)
                if pk:
                    cand += list(pk.get("good") or [])
            # ★ 只推「幻灯片友好」的图（排除 TIF/BMP 制版件与极端长宽比）
            cand = [it for it in cand if slide_ok(it["path"], it["w"], it["h"])]
            # ★ 排序按「关键词命中数优先，再按宽度」——
            #   单纯按宽度会把「只蹭到一个泛词的大图」排到最前（如 class-print 撞上「数字人」），
            #   而真正贴题的（偏移四型 + MediaPipe 双命中）反被压下去。
            cand.sort(key=lambda it: (-(it.get("kw_hit") or 0), -it["w"]))
            if cand:
                A('<p style="font-size:12.5px;color:#6b6660">'
                  '以下按「幻灯片友好」（JPG/PNG · ≥1200px · 长宽比 0.45–2.3 · 排除制版分色件）筛出：</p>')
                for it in cand[:6]:
                    A('<p style="font-size:12.5px;margin:3px 0">'
                      '<b>%dx%d</b> ｜ %s ｜ %s<br><code>%s</code></p>'
                      % (it["w"], it["h"], it["cat3"][:16], it["who"], it["path"]))
            else:
                A('<p style="font-size:13.5px">该页对应经历<b>无「幻灯片友好」候选图</b>'
                  '（可用候选存在但多为 TIF/BMP 制版件或分辨率不足）→ 需另找素材。</p>')
        A("</div>")

    A("<h2>三、本机实测不可用的图（避免误用）</h2>")
    A("<table><tr><th>文件</th><th>尺寸</th><th>问题</th></tr>")
    A("<tr><td><code>09_PPT用图\\20_亚当斯密_会场1.jpg</code></td><td>118×210</td>"
      "<td>缩略图，放大必糊 → 同组用 21–24 代替</td></tr>")
    A("<tr><td><code>09_PPT用图\\60_厦门版画实验_1.jpg</code></td><td>570×380</td>"
      "<td>分辨率不足 → 厦门线需另找原图</td></tr>")
    A("<tr><td><code>09_PPT用图\\60_厦门版画实验_2.jpg</code></td><td>380×390</td><td>同上</td></tr>")
    A("<tr><td><code>09_PPT用图\\60_厦门版画实验_3.jpg</code></td><td>250×386</td><td>同上</td></tr>")
    A("</table>")

    A('<div class="foot">工具 <code>tools\\build_ppt_packs_b3.py</code> ｜ '
      '基准文件 <code>%s</code> ｜ <b>内部资料，不得外传</b></div>' % MASTER_DECK)
    A("</div></body></html>")
    io.open(AUDIT, "w", encoding="utf-8").write("\n".join(H))
    return AUDIT


# ═══════════════════════════════ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--no-deck", action="store_true")
    ap.add_argument("--audit-only", action="store_true")
    a = ap.parse_args()

    # ---- 第二批 8 段（只统计，用于体检表；不重写其产物）
    # ★ 必须用**原始的 B.gather + 原始的 DB_EXCLUDE**，
    #   否则统计口径与已交付的第二批产物对不上（新版 gather3 是按 root 分查 + 放开策展桶）。
    EXP2 = list(B.EXPERIENCES)
    packs2 = []
    print("== 第二批 8 段（仅统计 · 沿用已交付口径）==")
    for e in EXP2:
        items, good = counts(e, g=_orig_gather)
        caps = []
        main, steps, _g = B.pick(items)
        for it in ([main] if main else []) + steps:
            caps.append(dict(n=len(caps) + 1, role=("主图" if not caps else "过程图"),
                             src=it["path"], w=it["w"], h=it["h"], who=it["who"],
                             cat3=it["cat3"], date_msg=it["date_msg"],
                             date_dir=it["date_dir"]))
        packs2.append(dict(exp=e, caps=caps, n_cand=len(items), n_good=len(good), good=good))
        print("  %02d %-28s 候选 %-4d 可用 %-4d" % (e["no"], e["name"][:28], len(items), len(good)))

    # ★ 第三批才放开策展两桶 + 换用按 root 分查的 gather3 + 启用画面质量过滤
    B.DB_EXCLUDE = {"微信缩略图"}
    B.gather = gather3
    B.pick = pick3

    if a.audit_only:
        p = build_audit(packs2, [])
        print("→ %s" % p)
        return

    # ---- 第三批 2 段（正式产出）
    B.OUT = os.path.join(WS, "_tmp", "ppt_packs", "b3-" + RUNSTAMP)
    B.EXPERIENCES = EXP3
    B.DECK = DECK
    B.PREVIEW = PREVIEW
    B.INDEX_CSV = INDEX_CSV
    print("\n== 第三批 %d 段（产出）==" % len(EXP3))
    packs3 = B.build_packs()
    # 标注每段被「画面质量」拦下的截图/文档类数量（仍保留在候选池里，可人工复核）
    for pk in packs3:
        its = gather3(pk["exp"])
        pk["n_doc"] = sum(1 for it in its if it.get("doc_like"))

    p1 = build_preview3(packs3)
    print("→ %s" % p1)
    if not a.no_deck:
        try:
            d = B.build_deck(packs3)
            print("→ %s（%d 页可编辑 PPT）" % (d, len(packs3)))
        except Exception:
            traceback.print_exc()

    p2 = build_audit(packs2, packs3)
    print("→ %s" % p2)

    # ---- 校友会群转发图：单独出联系表（★ 不自动进 PPT，供人工筛）
    sns_dir = os.path.join(B.CUR, "08_英国校友会活动")   # ★ B.CUR 就是 07_照片素材
    if os.path.isdir(sns_dir):
        print("\n== 校友会群转发图联系表 ==")
        subprocess.run([sys.executable, os.path.join(HERE, "contact_sheet.py"),
                        "--dir", sns_dir, "--min-w", "700", "--min-bytes", "40000",
                        "--prefix", "SRC", "--name", "SRC_校友会群转发图",
                        "--title", "格拉斯哥校友会 · 微信群转发图 ｜ 多为海报/招募/二维码，需人工筛",
                        "--cols", "8", "--cell", "300"], check=False)

    print("入选图合计 %d 张" % sum(len(pk["caps"]) for pk in packs3))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
