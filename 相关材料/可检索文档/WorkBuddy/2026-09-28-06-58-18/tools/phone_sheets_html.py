# -*- coding: utf-8 -*-
r"""
phone_sheets_html.py —— 把手机相机原片的逐月联系表汇成「一个网页」

输入：`--dir <手机相机原片目录>`（需已跑过 phone_sheets.py，存在 `_联系表\`）
产出：`<dir>\_联系表\00_手机原片总台.html`

特点
  · 单文件、浅色主题、中文；图片走**相对路径**，整个目录拷走也能离线看
  · 顶部「一图看全」+ 编号规则 + 缺口提示
  · 每张联系表一节：表号 / 张数 / 日期范围 / 原图 <img>
  · 附「编号 → 文件名」检索说明（真要在 `_联系表索引.csv` 里查）

用法：
  python tools\phone_sheets_html.py --dir "C:\Users\wardc\Desktop\手机相机原片_2026-10-06"
"""
import os, io, re, csv, glob, argparse, html, datetime

MONTH_CN = {1: "一月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
            7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "十一月", 12: "十二月"}

# 主 PPT 已知缺口（供筛选时优先看）—— 与 10_照片汇总 的结论一致
GAPS = [
    ("2026-06", "厦门集美 / 支教现场", "全库目前**无课堂现场照**，06 桶最缺"),
    ("2026-07", "北京台 AIGC 实习", "全库仅 3 张，实习期现场几乎空白"),
    ("2026-08", "AI 与交互技术", "主 PPT 第 15 页「技术赋能」目前 **0 图**"),
]


def month_cn(mo):
    try:
        y, m = mo.split("-")
        return "%s 年 %s" % (y, MONTH_CN[int(m)])
    except Exception:
        return mo


def read_csv(p):
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape(str(s or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    sd = os.path.join(a.dir, "_联系表")
    if not os.path.isdir(sd):
        print("!! 找不到 %s —— 先跑 phone_sheets.py" % sd)
        return

    # 收集表（排除总览图与临时文件）
    jpgs = sorted(p for p in glob.glob(os.path.join(sd, "*.jpg"))
                  if not os.path.basename(p).startswith("00_"))
    if not jpgs:
        print("!! 没有联系表图")
        return

    sheets = []
    total = 0
    months = []
    for jp in jpgs:
        tag = os.path.splitext(os.path.basename(jp))[0]
        rows = read_csv(os.path.join(sd, tag + ".csv"))
        dates = sorted(r.get("日期", "") for r in rows if r.get("日期"))
        mo = "%s-%s" % (dates[0][:4], dates[0][4:6]) if dates and len(dates[0]) >= 6 else "未知"
        if mo not in months:
            months.append(mo)
        total += len(rows)
        sheets.append(dict(tag=tag, mo=mo, n=len(rows), jpg=os.path.basename(jp),
                           d0=(dates[0] if dates else ""), d1=(dates[-1] if dates else "")))
    months.sort()

    ov = os.path.join(sd, "00_手机原片总览.jpg")
    has_ov = os.path.exists(ov)

    # 按月份分组渲染
    by_mo = {}
    for s in sheets:
        by_mo.setdefault(s["mo"], []).append(s)

    parts = []
    parts.append("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>手机相机原片 · 总台</title>
<style>
:root{--ink:#1f2a24;--ink2:#4a5750;--ink3:#8b968f;--line:#e4e0d8;--bg:#f7f6f3;
--card:#fff;--accent:#9e3b2e;--green:#1f3d2b;--soft:#eef2ee;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.7 "Microsoft YaHei","PingFang SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1500px;margin:0 auto;padding:26px 22px 70px}
header{background:var(--green);color:#fff;border-radius:14px;padding:24px 28px;margin-bottom:20px}
header h1{margin:0 0 6px;font-size:26px;letter-spacing:.5px}
header p{margin:0;color:#cfe0d4;font-size:14px}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0 4px}
.kpi{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);
border-radius:10px;padding:8px 16px;min-width:104px}
.kpi b{display:block;font-size:22px;line-height:1.25}
.kpi span{font-size:12px;color:#cfe0d4}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:20px 24px;margin-bottom:18px}
h2{font-size:19px;margin:0 0 12px;color:var(--green);
border-left:4px solid var(--accent);padding-left:11px}
h3{font-size:16px;margin:22px 0 8px;color:var(--green)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--soft);color:var(--green);font-weight:600;white-space:nowrap}
code{background:#f0eee9;border:1px solid var(--line);border-radius:4px;
padding:1px 6px;font-family:Consolas,monospace;font-size:13px;color:var(--accent)}
.hint{background:#fdf7f5;border-left:4px solid var(--accent);border-radius:8px;
padding:12px 16px;margin:12px 0;font-size:14px;color:var(--ink2)}
.hint b{color:var(--accent)}
.mohead{margin:26px 0 10px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.mohead h3{margin:0;font-size:18px;color:var(--green)}
.pill{display:inline-block;background:var(--soft);border:1px solid var(--line);
color:var(--ink2);border-radius:99px;padding:2px 11px;font-size:12px}
.pill.red{background:#fbeae7;border-color:#f0cdc6;color:var(--accent)}
.sheet{margin:14px 0 26px}
.sheet .cap{font-size:13px;color:var(--ink3);margin:0 0 6px;display:flex;
gap:12px;align-items:baseline;flex-wrap:wrap}
.sheet .cap b{color:var(--ink);font-size:14px}
.sheet img{width:100%;height:auto;display:block;border:1px solid var(--line);
border-radius:10px;background:#fff}
.over img{width:100%;height:auto;border:1px solid var(--line);border-radius:10px}
footer{margin-top:30px;padding-top:14px;border-top:1px solid var(--line);
color:var(--ink3);font-size:12.5px}
a{color:var(--accent)}
@media(max-width:640px){.wrap{padding:14px 12px 50px}header{padding:18px}}
</style></head><body><div class="wrap">""")

    parts.append('<header><h1>手机相机原片 · 总台</h1>'
                 '<p>逐月带编号联系表 —— 你按编号挑，我按编号取</p>'
                 '<div class="kpis">'
                 '<div class="kpi"><b>%d</b><span>张原片</span></div>'
                 '<div class="kpi"><b>%d</b><span>个月</span></div>'
                 '<div class="kpi"><b>%d</b><span>张联系表</span></div>'
                 '<div class="kpi"><b>%.1f GB</b><span>占用</span></div>'
                 '</div></header>' % (total, len(months), len(sheets),
                                      _dir_size(a.dir) / 1073741824.0))

    # 一图看全
    if has_ov:
        parts.append('<div class="card over"><h2>一图看全</h2>'
                     '<p style="margin:0 0 10px;color:#4a5750;font-size:14px">'
                     '每个月取 6 张代表图，快速判断这个月拍了什么。'
                     '完整编号见下方各联系表。</p>'
                     '<img src="%s" alt="逐月总览"></div>' % esc(os.path.basename(ov)))

    # 编号规则
    parts.append("""<div class="card"><h2>怎么用（30 秒）</h2>
<table>
<tr><th>步骤</th><th>做法</th></tr>
<tr><td>1 · 看</td><td>往下滚，看每张联系表。图左上角红底白字就是编号，例如
<code>2509A-017</code> = <b>2025 年 9 月</b>、第 A 段、第 <b>17</b> 张。</td></tr>
<tr><td>2 · 记</td><td>把想要的编号记下来发我，例如
<code>2509A-017, 2510B-043, 2604-012</code>。</td></tr>
<tr><td>3 · 查</td><td>想自己找原图：打开 <code>_联系表\\联系表索引.csv</code>，
按 <b>编号</b> 列筛 → 看 <b>文件</b> 列 → 到
<code>手机相机原片_2026-10-06\\</code> 取同名文件。</td></tr>
</table>
<div class="hint"><b>文件名已拍平</b>：全部改成 <code>YYYYmmdd_HHMMSS_原名.jpg</code>，
在资源管理器里按名称排序 = 按拍摄时间排序。</div>
<div class="hint"><b>注意</b>：这里是<b>相机原片</b>（1800×4000 或 4000×1800，单张 1–2.4 MB），
不含截图。截图 3,999 张另有清单，需要时再说。</div>
</div>""")

    # 缺口提示
    rows = "".join("<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % (m, w, d)
                   for m, w, d in GAPS)
    parts.append("""<div class="card"><h2>这批最可能补上的缺口</h2>
<p style="margin:0 0 10px;color:#4a5750;font-size:14px">
中期汇报目前有 3 处「有素材、没照片」，正好都是相机拍得多的场景 —— 优先看这几个月份：</p>
<table><tr><th>月份</th><th>对应内容</th><th>现状</th></tr>%s</table>
<div class="hint">对应到汇总目录：<code>06_开街活动\\</code> ·
<code>07_国际交流\\</code> · <code>08_AI与交互技术\\</code>（主 PPT 第 15 页）</div>
</div>""" % rows)

    # 逐月联系表
    parts.append('<div class="card"><h2>逐月联系表</h2>'
                 '<p style="margin:0 0 4px;color:#4a5750;font-size:14px">'
                 '按时间顺序排列。每张表最多 160 张，超出自动分段（A / B / C…）。</p>')
    for mo in months:
        ss = by_mo[mo]
        n = sum(x["n"] for x in ss)
        parts.append('<div class="mohead"><h3>%s</h3>'
                     '<span class="pill">%d 张</span>'
                     '<span class="pill">%d 张表</span></div>'
                     % (esc(month_cn(mo)), n, len(ss)))
        for s in ss:
            rng = "%s → %s" % (_fmt(s["d0"]), _fmt(s["d1"])) if s["d0"] else "日期见文件名"
            parts.append('<div class="sheet"><div class="cap">'
                         '<b>%s</b><span class="pill red">%d 张</span>'
                         '<span>%s</span>'
                         '<span>对照表：<code>%s.csv</code></span>'
                         '</div><img src="%s" alt="%s" loading="lazy"></div>'
                         % (esc(s["tag"]), s["n"], esc(rng), esc(s["tag"]), esc(s["jpg"]),
                            esc(s["tag"])))
    parts.append('</div>')

    parts.append('<footer>手机相机原片 · 逐月联系表总台 ｜ 生成于 %s ｜ '
                 '原图目录：<code>%s</code></footer>'
                 % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), esc(a.dir)))
    parts.append('</div></body></html>')

    outp = a.out or os.path.join(sd, "00_手机原片总台.html")
    with io.open(outp, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    print("→ %s（%.1f KB，%d 张表 / %d 张图）"
          % (outp, os.path.getsize(outp) / 1024.0, len(sheets), total))


def _fmt(d):
    if not d or len(d) < 8:
        return d or ""
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8])


def _dir_size(d):
    t = 0
    for p in glob.glob(os.path.join(d, "*")):
        try:
            if os.path.isfile(p):
                t += os.path.getsize(p)
        except Exception:
            pass
    return t


if __name__ == "__main__":
    main()
