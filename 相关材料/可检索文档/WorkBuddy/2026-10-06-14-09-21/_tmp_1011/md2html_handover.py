# -*- coding: utf-8 -*-
"""把交接总文档 MD 转成印痕风格的 HTML（自包含，无外部依赖）。"""
import re, html, io, sys

SRC = r"C:\Users\wardc\Desktop\中期汇报_2026-09\00_交接总文档_2026-10-11.md"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\00_交接总文档_2026-10-11.html"

with io.open(SRC, encoding="utf-8") as f:
    lines = f.read().split("\n")

def esc(s):
    return html.escape(s, quote=False)

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)
    return s

out = []
i = 0
n = len(lines)
toc = []

while i < n:
    ln = lines[i]
    s = ln.strip()

    # 代码块
    if s.startswith("```"):
        buf = []
        i += 1
        while i < n and not lines[i].strip().startswith("```"):
            buf.append(esc(lines[i]))
            i += 1
        i += 1
        out.append("<pre>" + "\n".join(buf) + "</pre>")
        continue

    # 分隔线
    if s == "---":
        out.append("<hr>")
        i += 1
        continue

    # 标题
    m = re.match(r"^(#{1,4})\s+(.*)$", s)
    if m:
        lv = len(m.group(1)); txt = m.group(2)
        hid = "s%d" % len(toc)
        toc.append((lv, txt, hid))
        out.append('<h%d id="%s">%s</h%d>' % (lv, hid, inline(txt), lv))
        i += 1
        continue

    # 表格
    if s.startswith("|"):
        rows = []
        while i < n and lines[i].strip().startswith("|"):
            rows.append(lines[i].strip())
            i += 1
        cells = []
        for r in rows:
            parts = [c.strip() for c in r.strip("|").split("|")]
            cells.append(parts)
        body = []
        head = cells[0]
        data = cells[2:] if len(cells) > 1 and re.match(r"^[\s:\-|]+$", rows[1]) else cells[1:]
        body.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead>")
        body.append("<tbody>")
        for r in data:
            body.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
        body.append("</tbody>")
        out.append('<div class="tw"><table>' + "".join(body) + "</table></div>")
        continue

    # 引用
    if s.startswith(">"):
        buf = []
        while i < n and lines[i].strip().startswith(">"):
            buf.append(inline(lines[i].strip()[1:].strip()))
            i += 1
        out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
        continue

    # 列表
    if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
        ordered = bool(re.match(r"^\d+\.\s+", s))
        tag = "ol" if ordered else "ul"
        buf = []
        while i < n:
            t = lines[i].strip()
            mm = re.match(r"^[-*]\s+\[( |x)\]\s+(.*)$", t)
            if mm:
                mark = "☑" if mm.group(1) == "x" else "☐"
                buf.append('<li class="todo">%s %s</li>' % (mark, inline(mm.group(2))))
                i += 1
                continue
            if re.match(r"^[-*]\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^[-*]\s+", "", t)))
                i += 1
                continue
            if re.match(r"^\d+\.\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^\d+\.\s+", "", t)))
                i += 1
                continue
            break
        out.append("<%s>" % tag + "".join(buf) + "</%s>" % tag)
        continue

    # 空行
    if s == "":
        i += 1
        continue

    # 段落
    buf = [inline(s)]
    i += 1
    while i < n:
        t = lines[i].strip()
        if t == "" or t.startswith(("#", ">", "|", "```", "-", "*", "1.", "---")):
            break
        buf.append(inline(t))
        i += 1
    out.append("<p>" + " ".join(buf) + "</p>")

# TOC（只收 h2）
toc_html = []
for lv, txt, hid in toc:
    if lv == 2:
        toc_html.append('<a href="#%s">%s</a>' % (hid, esc(re.sub(r"\*\*", "", txt))))

CSS = """
:root{--paper:#F6F2E9;--ink:#202321;--red:#B5493A;--line:#d9d2c4;--soft:#6b6660;}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Source Han Sans SC","Microsoft YaHei","PingFang SC",system-ui,sans-serif;
 font-size:15px;line-height:1.78;}
.wrap{max-width:1000px;margin:0 auto;padding:48px 34px 90px;}
header.top{border-bottom:3px double var(--ink);padding-bottom:22px;margin-bottom:8px;}
header.top .kicker{font-size:12px;letter-spacing:.32em;color:var(--red);font-weight:700;}
h1{font-size:30px;line-height:1.35;margin:14px 0 10px;letter-spacing:.01em;}
header.top .meta{font-size:12.5px;color:var(--soft);line-height:1.9;}
nav.toc{background:#fff;border:1px solid var(--line);border-left:4px solid var(--red);
 padding:18px 22px;margin:26px 0 40px;border-radius:2px;}
nav.toc b{display:block;font-size:12px;letter-spacing:.2em;color:var(--red);margin-bottom:10px;}
nav.toc a{display:inline-block;color:var(--ink);text-decoration:none;font-size:13px;
 margin:3px 14px 3px 0;padding:2px 0;border-bottom:1px solid transparent;}
nav.toc a:hover{border-bottom-color:var(--red);color:var(--red);}
h2{font-size:21px;margin:52px 0 16px;padding-bottom:9px;border-bottom:2px solid var(--ink);
 letter-spacing:.01em;}
h3{font-size:16.5px;margin:32px 0 12px;color:var(--red);}
h4{font-size:14.5px;margin:22px 0 10px;}
p{margin:11px 0;}
b{font-weight:700;}
code{background:#eae4d7;padding:1.5px 6px;border-radius:3px;font-size:12.8px;
 font-family:"Cascadia Mono",Consolas,monospace;color:#7a3226;}
pre{background:#232120;color:#efe9dd;padding:16px 18px;border-radius:3px;overflow-x:auto;
 font-family:"Cascadia Mono",Consolas,monospace;font-size:12.6px;line-height:1.7;
 border-left:4px solid var(--red);}
pre code{background:none;color:inherit;padding:0;}
blockquote{margin:16px 0;padding:14px 20px;background:#fff;border-left:4px solid var(--red);
 border-radius:2px;color:#33302c;font-size:14.5px;}
blockquote b{color:var(--red);}
.tw{overflow-x:auto;margin:18px 0;}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.3px;
 border:1px solid var(--line);}
th{background:#232120;color:#f2ede3;text-align:left;padding:9px 12px;font-weight:600;
 font-size:12.5px;letter-spacing:.02em;white-space:nowrap;}
td{padding:8px 12px;border-top:1px solid var(--line);vertical-align:top;line-height:1.66;}
tr:nth-child(even) td{background:#faf7f0;}
ul,ol{margin:11px 0;padding-left:24px;}
li{margin:5px 0;}
li.todo{list-style:none;margin-left:-20px;}
hr{border:0;border-top:1px dashed var(--line);margin:40px 0;}
i{color:var(--soft);}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--line);
 font-size:12px;color:var(--soft);text-align:center;}
@media print{body{background:#fff;}nav.toc{page-break-inside:avoid;}h2{page-break-after:avoid;}}
"""

doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>中期汇报《在场与回应》· 交接总文档 2026-10-11</title>
<style>%s</style></head><body><div class="wrap">
<header class="top">
<div class="kicker">HANDOVER · 唯一总入口</div>
<h1>中期汇报《在场与回应》· 交接总文档</h1>
<div class="meta">版本 2026-10-11 23:10 ｜ 取代 09-19/09-24 的 5 份旧交接文档<br>
项目根目录：C:\\Users\\wardc\\Desktop\\中期汇报_2026-09\\ ｜ 生成：WorkBuddy AI</div>
</header>
<nav class="toc"><b>目录</b>%s</nav>
%s
<footer>本文件整合 2026-09-19 至 2026-10-11 全部工作产物与核查结论 · 事实以正文第 3 节硬口径为准</footer>
</div></body></html>""" % (CSS, "".join(toc_html), "\n".join(out))

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)

# 校验
import os
print("OUT bytes:", os.path.getsize(OUT))
for t in ["div", "table", "tr", "td", "th", "h2", "h3", "p", "ul", "ol", "li", "blockquote", "pre"]:
    o = doc.count("<%s" % t) + doc.count("<%s " % t)
    c = doc.count("</%s>" % t)
    flag = "OK " if o == c else "!! "
    print("%s%s open=%d close=%d" % (flag, t, o, c))
