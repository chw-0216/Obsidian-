# -*- coding: utf-8 -*-
r"""
photo_collect.py —— 把「中期汇报要用的照片」集中到一个文件夹

任务：照片散在 5 个地方（09_PPT用图 / 07_照片素材 / 桌面项目夹 / AI-archive / 微信库），
      按**汇报主题**归集到 `桌面\中期汇报_2026-09\10_照片汇总_<日期>\`，一主题一个子目录，
      每主题附一张**带编号的联系表**，并出一份总台 HTML + CSV 清单。

设计要点
--------
★ 不覆盖：输出目录若已存在，自动加 `-b` / `-c` 后缀（本机安全闸门把「覆盖」算作删除）
★ 质量过滤：`doc_like` 三判据（低饱和+高亮 / 纯黑白占比 / 近灰占比）剔除截图·文档·拍屏
★ 白名单不过滤：已人工策展的图源（PPT用图 / 澜沧优先推荐 / RAW优化版 / 定稿图 / C1原片）
★ 按来源分优先级排序：显式文件(0) > 目录扫描(1) > 库 root(2)；策展源按文件名序
★ 只读：绝不修改任何来源文件

用法
----
  python tools\photo_collect.py --dry     # 只统计不复制
  python tools\photo_collect.py           # 正式生成
"""
import os, sys, io, csv, re, math, shutil, sqlite3, datetime, argparse, traceback
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
sys.path.insert(0, os.path.join(WS, "tools"))
DB = os.path.join(WS, "_tmp", "batch", "batch.sqlite")

DESK = r"C:\Users\wardc\Desktop\中期汇报_2026-09"
PPTU = os.path.join(DESK, "09_PPT用图")
MAT = os.path.join(DESK, "07_照片素材")

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".hevc"}

# 已人工策展 → 不做质量过滤
TRUSTED_KEYS = ["09_PPT用图", "01_优先推荐", "RAW优化版", "定稿图", "C1原片", "_定稿图"]

MIN_W = 800          # 最小宽度（TRUSTED 不适用）
MIN_BYTES = 80_000   # 最小字节（TRUSTED 不适用）
MIN_RATIO, MAX_RATIO = 0.45, 2.4   # 幻灯片友好比例
ITEM_MAX_MB = 25     # 单张上限（TRUSTED 不适用）—— 原图过大对 PPT 无意义
MB_CAP = 200         # 每主题体积预算

# 必须排除：PII / 手机原始数据 / 系统噪音
EXCLUDE_PAT = re.compile(
    r"刘丽萍|检查报告|身份证|手机全文件解析|手机个人信息|\.recycle|collectcenter|"
    r"微信缩略图|Thumbs|\.tmp", re.I)

_QUAL_CACHE = {}
_META = None          # path(lower) → dict(w,h,bytes,date,date_src,category,role,session_name)


def _load_meta():
    """一次性把库里全部照片元数据读进内存 —— 避免对每个文件再开一次 PIL"""
    global _META
    if _META is not None:
        return _META
    _META = {}
    try:
        c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
        for r in c.execute("select path,width,height,bytes,date,date_src,category,role,"
                           "session_name,session_type,md5 from photos"):
            _META[(r["path"] or "").lower()] = dict(
                w=r["width"] or 0, h=r["height"] or 0, bytes=r["bytes"] or 0,
                date=r["date"] or "", date_src=r["date_src"] or "",
                category=r["category"] or "", role=r["role"],
                session_name=r["session_name"] or "", session_type=r["session_type"] or "",
                md5=r["md5"])
        c.close()
    except Exception:
        traceback.print_exc()
    return _META


def _probe(path):
    """拿 (w,h,bytes)：优先库元数据，缺失才开 PIL"""
    m = _load_meta().get(path.lower())
    if m and m["w"] and m["h"]:
        return m["w"], m["h"], (m["bytes"] or _size(path))
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(path) as im:
            im.draft("RGB", (1600, 1600))   # JPEG 快速降采样，不解全图
            w, h = im.size
        return w, h, _size(path)
    except Exception:
        return 0, 0, _size(path)


def _size(p):
    try:
        return os.path.getsize(p)
    except Exception:
        return 0


# ---------------------------------------------------------------- 质量判别
def _qual(path):
    """→ (S均值, V均值, 纯黑白占比, 近灰占比)；直方图法，快"""
    if path in _QUAL_CACHE:
        return _QUAL_CACHE[path]
    r = None
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(path) as im:
            im.draft("RGB", (384, 384))     # ★ 关键：JPEG 只解缩略图
            im = im.convert("RGB")
            im.thumbnail((288, 288))
            hsv = im.convert("HSV")
            sh = hsv.getchannel("S").histogram()
            vh = hsv.getchannel("V").histogram()
            lh = im.convert("L").histogram()
        n = sum(sh) or 1
        n2 = sum(lh) or 1
        S = sum(i * c for i, c in enumerate(sh)) / n / 255.0
        V = sum(i * c for i, c in enumerate(vh)) / n / 255.0
        bw = (sum(lh[:6]) + sum(lh[250:])) / n2
        gray = sum(sh[:26]) / n            # S<0.10
        r = (S, V, bw, gray)
    except Exception:
        r = None
    _QUAL_CACHE[path] = r
    return r


def doc_like(path):
    """True = 像文档/截图/拍屏，不该进汇报"""
    q = _qual(path)
    if not q:
        return False
    S, V, bw, gray = q
    return (S < 0.12 and V > 0.85) or (bw >= 0.15) or (gray >= 0.55)


def trusted(path):
    p = path.replace("/", "\\")
    return any(k in p for k in TRUSTED_KEYS)


# ---------------------------------------------------------------- 数据源
def db_rows(roots, pathfilter=None, roles=None):
    c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    w, a = ["root in (%s)" % ",".join("?" * len(roots))], list(roots)
    if roles:
        w.append("(" + " or ".join(["role=?" if r else "role is null" for r in roles]) + ")")
        a += [r for r in roles if r]
    out = []
    for r in c.execute("select * from photos where " + " and ".join(w), a):
        p = r["path"]
        if pathfilter and not re.search(pathfilter, p, re.I):
            continue
        if EXCLUDE_PAT.search(p):
            continue
        out.append(dict(path=p, date=r["date"], date_src=r["date_src"],
                        category=r["category"], role=r["role"],
                        session_name=r["session_name"], session_type=r["session_type"],
                        width=r["width"] or 0, height=r["height"] or 0,
                        bytes=r["bytes"] or 0, md5=r["md5"], src="库:" + r["root"], pri=2))
    c.close()
    return out


def fs_rows(d, recursive=True):
    out = []
    if not os.path.isdir(d):
        return out
    if recursive:
        for dp, _, fs in os.walk(d):
            for fn in fs:
                out.append(os.path.join(dp, fn))
    else:
        for fn in os.listdir(d):
            out.append(os.path.join(d, fn))
    meta = _load_meta()
    res = []
    for p in out:
        if os.path.splitext(p)[1].lower() not in IMG_EXT:
            continue
        if EXCLUDE_PAT.search(p):
            continue
        w, h, b = _probe(p)
        if not b:
            continue
        m = meta.get(p.lower()) or {}
        res.append(dict(path=p, date=m.get("date", ""), date_src=m.get("date_src") or "目录",
                        category=m.get("category", ""), role=m.get("role"),
                        session_name=m.get("session_name") or os.path.basename(os.path.dirname(p)),
                        session_type=m.get("session_type", ""), width=w, height=h, bytes=b,
                        md5=m.get("md5"), src="目录:" + os.path.basename(d), pri=1))
    return res


def file_rows(paths):
    meta = _load_meta()
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        w, h, b = _probe(p)
        m = meta.get(p.lower()) or {}
        out.append(dict(path=p, date=m.get("date", ""), date_src=m.get("date_src") or "策展",
                        category=m.get("category") or "① 已策展", role=m.get("role"),
                        session_name=m.get("session_name") or "09_PPT用图",
                        session_type=m.get("session_type", ""), width=w, height=h, bytes=b,
                        md5=m.get("md5"), src="策展", pri=0))
    return out


def pptu(*nums):
    """取 09_PPT用图 下以这些数字开头的文件"""
    if not os.path.isdir(PPTU):
        return []
    out = []
    for fn in sorted(os.listdir(PPTU)):
        m = re.match(r"^(\d+)", fn)
        if m and int(m.group(1)) in nums:
            out.append(os.path.join(PPTU, fn))
    return out


# ---------------------------------------------------------------- 主题定义
def buckets():
    return [
        dict(no=1, key="01_封面与个人概况", page="P1/P3",
             note="封面 · 个人概况与研究定位",
             files=pptu(1),
             dirs=[], roots=[], pf=None, cap=6, sort="name"),

        dict(no=2, key="02_工作站_接待与讲解", page="P6/P8/P9",
             note="洞台村乡村美育工作站 · 工作坊运营 · 8 批次接待讲解",
             files=pptu(2, 3, 4, 5, 6),
             dirs=[os.path.join(MAT, "01_工作站与领导接待"),
                   os.path.join(MAT, "03_工作站现场_导师记录"),
                   os.path.join(MAT, "06_区委书记到访_导师聊天_2026-08-22")],
             roots=[], pf=None, cap=40, sort="size"),

        dict(no=3, key="03_版画三技", page="P7",
             note="技法支撑：木版 / 石版 / 丝网",
             files=pptu(50, 51, 52),
             dirs=[os.path.join(MAT, "02_版画技法_木版与石版")],
             roots=[], pf=None, cap=26, sort="size"),

        dict(no=4, key="04_澜沧支教", page="P11",
             note="社会服务：知行计划 · 澜沧支教（Movers4Climate）",
             files=pptu(10, 11, 12, 13, 14, 15, 16, 17),
             dirs=[],
             roots=["澜沧课堂照", "澜沧提交包", "知行最终版", "知行最终材料"],
             pf=None, cap=36, sort="name"),

        dict(no=5, key="05_学术研讨会", page="P12",
             note="学术会务：第五届美学与艺术研究学术研讨会",
             files=pptu(30, 31, 32),
             dirs=[os.path.join(MAT, "05_学术会务_论坛")],
             roots=[], pf=None, cap=30, sort="size"),

        dict(no=6, key="06_开街活动", page="P10",
             note="开街活动 · 长城国际动漫谷（2026-08-02 怀柔渤海镇洞台村）",
             files=pptu(40, 41, 42), dirs=[], roots=[], pf=None, cap=8, sort="name"),

        dict(no=7, key="07_国际交流", page="P13",
             note="英国驻华使馆电影季 × 亚当斯密商学院",
             files=pptu(20, 21, 22, 23, 24, 25, 26),
             dirs=[], roots=[], pf=None, cap=10, sort="name"),

        dict(no=8, key="08_AI与交互技术", page="P15",
             note="技术赋能：AI 与交互技术（数字人 / MediaPipe / 生成影像 / 视觉方案）",
             files=[],
             dirs=[os.path.join(r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷", "偏移四型-MediaPipe-v2"),
                   os.path.join(r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷", "交互文件与主视觉汇总")],
             roots=["AI产物"],
             pf=r"悲鸿|在场与回应|数字人|交互|偏移四型|MediaPipe|丝网印刷工作坊|乡村美育工作站|井邻",
             exc=r"海报|宣传页|招募|报名|主视觉_0|投屏版|微信公众号封面|图文包",
             cap=36, sort="size"),

        dict(no=9, key="09_井邻项目视觉", page="P6/P15",
             note="井邻项目视觉体系 · 版画作品 · 主视觉",
             files=[],
             dirs=[os.path.join(r"C:\Users\wardc\Desktop\新增RAW优化版", "01_推荐纳入材料")],
             roots=["井邻项目", "井邻宣传", "图片素材", "RAW优化版"],
             pf=None,
             # ★ 剔除跨时期污染：575周年＝格拉斯哥校友会活动（不属于「考上央美之后」）
             exc=r"575|校友会|格拉斯哥|Glasgow|海报|主视觉_0|招募|宣传页|刘丽萍|"
                 r"井邻临时策划|绘画修改参考|偏移四型A4|偏移四型CMYK",
             cap=40, sort="size"),

        dict(no=10, key="10_朋友圈_他发的", page="P3/P16",
             note="本人发布的朋友圈（role=me，66 张）—— 时间线证据",
             files=[], dirs=[], roots=["朋友圈"], pf=None,
             cap=66, sort="date"),

        dict(no=11, key="11_摄影原片_C1", page="P7/P14",
             note="Capture One 摄影原片（2025）—— 本人摄影能力实证",
             files=[], dirs=[], roots=["C1原片"], pf=None,
             cap=24, sort="size"),
    ]


# ---------------------------------------------------------------- 收集
def collect(b):
    items = []
    items += file_rows(b.get("files") or [])
    for d in (b.get("dirs") or []):
        items += fs_rows(d)
    if b.get("roots"):
        items += db_rows(b["roots"], b.get("pf"), roles=(["me"] if b["roots"] == ["朋友圈"] else None))

    # 存在性 + 扩展名 + 主题级排除
    exc = re.compile(b["exc"], re.I) if b.get("exc") else None
    items = [it for it in items
             if os.path.exists(it["path"])
             and os.path.splitext(it["path"])[1].lower() in IMG_EXT
             and not (exc and exc.search(it["path"]))]

    # 质量门槛
    kept, dropped = [], Counter()
    for it in items:
        if not trusted(it["path"]):
            if it["width"] and it["width"] < MIN_W:
                dropped["分辨率不足"] += 1; continue
            if it["bytes"] and it["bytes"] < MIN_BYTES:
                dropped["文件过小"] += 1; continue
            if it["bytes"] > ITEM_MAX_MB * 1048576:
                dropped["单张超过 %dMB（原图过大）" % ITEM_MAX_MB] += 1; continue
            if it["width"] and it["height"]:
                r = it["width"] / max(1, it["height"])
                if not (MIN_RATIO <= r <= MAX_RATIO):
                    dropped["比例不适合幻灯片"] += 1; continue
            if doc_like(it["path"]):
                dropped["像截图/文档/拍屏"] += 1; continue
        kept.append(it)

    # 去重：md5 优先，否则 (basename, bytes)
    seen, uniq = set(), []
    for it in kept:
        k = it["md5"] or (os.path.basename(it["path"]).lower(), it["bytes"])
        if k in seen:
            dropped["重复"] += 1; continue
        seen.add(k); uniq.append(it)

    # 排序
    mode = b.get("sort", "size")
    if mode == "name":
        uniq.sort(key=lambda x: (x["pri"], os.path.basename(x["path"])))
    elif mode == "date":
        uniq.sort(key=lambda x: (x["pri"], x["date"] or ""))
    else:
        uniq.sort(key=lambda x: (x["pri"], -x["width"], -x["bytes"]))

    # 双上限：张数 + 字节预算（贪心按序取）
    budget = b.get("mb", MB_CAP) * 1048576
    picked, used = [], 0
    for it in uniq:
        if len(picked) >= b["cap"]:
            dropped["超出张数上限(取前 %d)" % b["cap"]] += 1
            continue
        if used + it["bytes"] > budget and picked:
            dropped["超出体积预算(%dMB)" % b.get("mb", MB_CAP)] += 1
            continue
        picked.append(it); used += it["bytes"]
    return picked, len(items), dropped


# ---------------------------------------------------------------- 输出
def safe_out(base):
    p = base
    for suf in ["", "-b", "-c", "-d", "-e"]:
        cand = base + suf
        if not os.path.exists(cand):
            return cand
    return base + "-" + datetime.datetime.now().strftime("%H%M%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    base = a.out or os.path.join(DESK, "10_照片汇总_" + datetime.date.today().strftime("%Y-%m-%d"))
    OUT = base if a.dry else safe_out(base)
    print("输出目录:", OUT, "(dry)" if a.dry else "")

    import contact_sheet as CS

    manifest, summary = [], []
    for b in buckets():
        picked, total, dropped = collect(b)
        size = sum(x["bytes"] for x in picked)
        summary.append(dict(no=b["no"], key=b["key"], page=b["page"], note=b["note"],
                            候选=total, 入册=len(picked), 大小MB=round(size / 1048576, 1),
                            剔除=dict(dropped)))
        print("\n[%s] %s  候选 %d → 入册 %d  (%.1f MB)"
              % (b["key"], b["page"], total, len(picked), size / 1048576))
        if dropped:
            print("    剔除:", dict(dropped))
        if a.dry:
            for it in picked[:6]:
                print("      ·", os.path.basename(it["path"]))
            continue

        dst = os.path.join(OUT, b["key"])
        os.makedirs(dst, exist_ok=True)
        for i, it in enumerate(picked, 1):
            ext = os.path.splitext(it["path"])[1].lower()
            name = "%s_%02d%s" % (b["key"], i, ext)
            try:
                shutil.copy2(it["path"], os.path.join(dst, name))
            except Exception as e:
                print("    复制失败:", it["path"], e)
            manifest.append(dict(主题=b["key"], 页=b["page"], 序号="%02d" % i,
                                 归档名=name, 原始路径=it["path"],
                                 来源=it.get("src") or "", 日期=it.get("date") or "",
                                 宽=it["width"], 高=it["height"],
                                 字节=it["bytes"], 谁发的=it.get("role") or ""))

        # 联系表（带编号，放进同目录）
        try:
            CS.build_sheet(picked, os.path.join(dst, "联系表_%s.jpg" % b["key"][:2]),
                           prefix=b["key"][:2], title="%s ｜ %s" % (b["key"], b["page"]),
                           cols=8, cell=280)
        except Exception:
            traceback.print_exc()

    if a.dry:
        return

    # CSV 清单
    csvp = os.path.join(WS, "照片汇总清单_%s.csv" % datetime.date.today().strftime("%Y-%m-%d"))
    with io.open(csvp, "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        wr.writeheader(); wr.writerows(manifest)
    print("\n→ %s（%d 行）" % (csvp, len(manifest)))

    # 总台 HTML（放汇总目录内，图片走相对路径）
    html = build_html(summary, OUT, manifest)
    hp = os.path.join(OUT, "00_照片汇总总台.html")
    io.open(hp, "w", encoding="utf-8").write(html)
    print("→ %s" % hp)
    print("\n合计入册 %d 张 / %.1f MB" % (len(manifest),
          sum(m["字节"] for m in manifest) / 1048576))


def build_html(summary, OUT, manifest):
    tot = len(manifest)
    totmb = sum(m["字节"] for m in manifest) / 1048576
    cards = []
    for s in summary:
        sheet = "%s\\联系表_%s.jpg" % (s["key"], s["key"][:2])
        has = os.path.exists(os.path.join(OUT, sheet))
        img = ('<img class="sheet" src="%s" alt="%s">' % (sheet.replace("\\", "/"), s["key"])) if has else ""
        drop = "".join("<li>%s：%d</li>" % (k, v) for k, v in s["剔除"].items())
        cards.append(f"""
  <section class="card">
    <h3>{s['key']} <span class="pg">{s['page']}</span></h3>
    <p class="note">{s['note']}</p>
    <p class="stat"><b>{s['入册']}</b> 张入册 ｜ 候选 {s['候选']} ｜ {s['大小MB']} MB</p>
    {img}
    {('<details><summary>剔除明细</summary><ul>' + drop + '</ul></details>') if drop else ''}
  </section>""")
    gaps = """
  <section class="card gap">
    <h3>缺口（诚实标注）</h3>
    <ul>
      <li><b>06 厦门版画实验</b>：`09_PPT用图\\60_厦门版画实验_1/2/3` 实测仅 570×380 / 380×390 / 250×386，无现成可用图。</li>
      <li><b>07 北京广播电视台 AIGC 实习</b>：全库仅 3 张，无工作现场照。</li>
      <li><b>08 英国校友会活动</b>：群转发 210 张绝大多数是电影海报 / 报名二维码 / 拍屏幕界面（含手机号），<b>不直接进 PPT</b>。</li>
      <li><b>手机相机原片 3,323 张</b>：2025-09 → 2026-09 逐月都有，<b>尚未取回本机</b>（手机当前为 MTP 模式，USB 调试未开）。</li>
    </ul>
  </section>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>中期汇报 · 照片汇总总台</title>
<style>
:root{{--ink:#1F3D2B;--acc:#9E3B2E;--txt:#5A5A5A;--bg:#FAF9F6;--line:#E4E0D8;--card:#fff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--txt);
 font:15px/1.7 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
header{{background:var(--ink);color:#fff;padding:34px 40px 28px}}
header h1{{margin:0 0 6px;font-size:26px;letter-spacing:.5px}}
header p{{margin:2px 0;font-size:13.5px;color:#CFE0D4}}
header .big{{font-size:15px;color:#fff;margin-top:10px}}
main{{max-width:1180px;margin:0 auto;padding:26px 20px 70px}}
.summary{{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 26px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;
 padding:14px 20px;min-width:150px}}
.kpi b{{display:block;font-size:24px;color:var(--ink)}}
.kpi span{{font-size:12.5px;color:#8A867E}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:18px 20px 22px;margin:0 0 20px}}
.card h3{{margin:0 0 4px;font-size:17px;color:var(--ink)}}
.card h3 .pg{{font-size:12px;color:#fff;background:var(--acc);
 border-radius:20px;padding:2px 10px;margin-left:8px;vertical-align:2px}}
.note{{margin:2px 0 6px;font-size:13.5px;color:#7C7970}}
.stat{{margin:0 0 12px;font-size:13px;color:var(--ink)}}
.stat b{{font-size:17px;color:var(--acc)}}
.sheet{{width:100%;border:1px solid var(--line);border-radius:8px;display:block}}
details{{margin-top:10px;font-size:13px}}
details summary{{cursor:pointer;color:var(--acc)}}
details ul{{margin:6px 0 0 18px;padding:0}}
.gap{{border-left:5px solid var(--acc)}}
.gap ul{{margin:8px 0 0 18px;padding:0}}
.gap li{{margin-bottom:5px}}
footer{{text-align:center;color:#A8A49C;font-size:12.5px;padding:20px}}
code{{background:#F1EEE8;padding:1px 5px;border-radius:4px;font-size:12.5px}}
</style></head><body>
<header>
  <h1>中期汇报 · 照片汇总总台</h1>
  <p>蔡浩文 ｜ 12250300012 ｜ 社会美育与乡村振兴</p>
  <p>按汇报主题归集 ｜ 一主题一子目录 ｜ 每目录附带编号联系表</p>
  <p class="big">合计 <b>{tot}</b> 张 ／ {totmb:.1f} MB</p>
</header>
<main>
  <div class="summary">
    <div class="kpi"><b>{tot}</b><span>入册照片</span></div>
    <div class="kpi"><b>{len(summary)}</b><span>主题子目录</span></div>
    <div class="kpi"><b>{totmb:.0f} MB</b><span>占用空间</span></div>
    <div class="kpi"><b>11</b><span>张联系表</span></div>
  </div>
  {''.join(cards)}
  {gaps}
</main>
<footer>照片汇总总台 ｜ 生成于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 全部原图未改动</footer>
</body></html>"""


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
