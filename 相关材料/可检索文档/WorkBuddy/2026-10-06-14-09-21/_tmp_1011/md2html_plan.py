# -*- coding: utf-8 -*-
"""把后半场执行方案 MD 转成印痕风格 HTML（自包含，无外部依赖）。"""
import re, html, io, os

SRC = r"C:\Users\wardc\Desktop\中期汇报_2026-09\00_后半场执行方案_2026-10-12.md"
OUT = r"C:\Users\wardc\Desktop\中期汇报_2026-09\00_后半场执行方案_2026-10-12.html"
TITLE = "中期汇报《在场与回应》· 后半场执行方案 2026-10-12"
KICKER = "PLAN · 井邻之后 · 素材缺口补齐"
H1 = "后半场执行方案 · 素材缺口补齐清单"
META = ("版本 2026-10-12 ｜ 承接《井邻之后：后半场完整交接文档》<br>"
        "项目根目录：C:\\Users\\wardc\\Desktop\\中期汇报_2026-09\\ ｜ 生成：WorkBuddy AI")
FOOTER = "本文件只处理井邻之后的后半场 · 前半场（澜沧、井邻）不在此重新策划 · 现状以 2026-10-12 磁盘核查为准"

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

out, toc = [], []
i, n = 0, len(lines)
# 跳过 MD 一级标题（已在 header 里）
while i < n and not lines[i].strip().startswith("# "):
    i += 1
i += 1

while i < n:
    ln = lines[i]
    s = ln.strip()

    if s.startswith("```"):
        buf = []
        i += 1
        while i < n and not lines[i].strip().startswith("```"):
            buf.append(esc(lines[i])); i += 1
        i += 1
        out.append("<pre>" + "\n".join(buf) + "</pre>"); continue

    if s == "---":
        out.append("<hr>"); i += 1; continue

    m = re.match(r"^(#{1,4})\s+(.*)$", s)
    if m:
        lv = len(m.group(1)); txt = m.group(2)
        hid = "s%d" % len(toc)
        toc.append((lv, txt, hid))
        out.append('<h%d id="%s">%s</h%d>' % (lv, hid, inline(txt), lv))
        i += 1; continue

    if s.startswith("|"):
        rows = []
        while i < n and lines[i].strip().startswith("|"):
            rows.append(lines[i].strip()); i += 1
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        head = cells[0]
        data = cells[2:] if len(cells) > 1 and re.match(r"^[\s:\-|]+$", rows[1]) else cells[1:]
        body = ["<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead>", "<tbody>"]
        for r in data:
            body.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
        body.append("</tbody>")
        out.append('<div class="tw"><table>' + "".join(body) + "</table></div>"); continue

    if s.startswith(">"):
        buf = []
        while i < n and lines[i].strip().startswith(">"):
            buf.append(inline(lines[i].strip()[1:].strip())); i += 1
        out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>"); continue

    if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
        ordered = bool(re.match(r"^\d+\.\s+", s))
        tag = "ol" if ordered else "ul"
        buf = []
        while i < n:
            t = lines[i].strip()
            mm = re.match(r"^[-*]\s+\[( |x)\]\s+(.*)$", t)
            if mm:
                mark = "☑" if mm.group(1) == "x" else "☐"
                buf.append('<li class="todo">%s %s</li>' % (mark, inline(mm.group(2)))); i += 1; continue
            if re.match(r"^[-*]\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^[-*]\s+", "", t))); i += 1; continue
            if re.match(r"^\d+\.\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^\d+\.\s+", "", t))); i += 1; continue
            break
        out.append("<%s>" % tag + "".join(buf) + "</%s>" % tag); continue

    if s == "":
        i += 1; continue

    buf = [inline(s)]
    i += 1
    while i < n:
        t = lines[i].strip()
        if t == "" or t.startswith(("#", ">", "|", "```", "-", "*", "---")) or re.match(r"^\d+\.\s+", t):
            break
        buf.append(inline(t)); i += 1
    out.append("<p>" + " ".join(buf) + "</p>")

toc_html = ['<a href="#%s">%s</a>' % (hid, esc(re.sub(r"\*\*", "", txt))) for lv, txt, hid in toc if lv == 2]

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
h2{font-size:21px;margin:52px 0 16px;padding-bottom:9px;border-bottom:2px solid var(--ink);letter-spacing:.01em;}
h3{font-size:16.5px;margin:32px 0 12px;color:var(--red);}
h4{font-size:14.5px;margin:22px 0 10px;}
p{margin:11px 0;}
b{font-weight:700;}
code{background:#eae4d7;padding:1.5px 6px;border-radius:3px;font-size:12.8px;
 font-family:"Cascadia Mono",Consolas,monospace;color:#7a3226;}
pre{background:#232120;color:#efe9dd;padding:16px 18px;border-radius:3px;overflow-x:auto;
 font-family:"Cascadia Mono",Consolas,monospace;font-size:12.6px;line-height:1.7;border-left:4px solid var(--red);}
pre code{background:none;color:inherit;padding:0;}
blockquote{margin:16px 0;padding:14px 20px;background:#fff;border-left:4px solid var(--red);
 border-radius:2px;color:#33302c;font-size:14.5px;}
blockquote b{color:var(--red);}
.tw{overflow-x:auto;margin:18px 0;}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.3px;border:1px solid var(--line);}
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
<title>%s</title>
<style>%s</style></head><body><div class="wrap">
<header class="top">
<div class="kicker">%s</div>
<h1>%s</h1>
<div class="meta">%s</div>
</header>
<nav class="toc"><b>目录</b>%s</nav>
%s
<footer>%s</footer>
</div></body></html>""" % (TITLE, CSS, KICKER, H1, META, "".join(toc_html), "\n".join(out), FOOTER)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)

print("OUT bytes:", os.path.getsize(OUT))
bad = 0
for t in ["div", "table", "thead", "tbody", "tr", "td", "th", "h2", "h3", "h4", "p",
          "ul", "ol", "li", "blockquote", "pre", "code", "b", "i", "nav", "header", "footer", "style", "html", "body"]:
    o = len(re.findall(r"<%s(?=[\s>/])" % t, doc)); c = len(re.findall(r"</%s>" % t, doc))
    ok = (o == c)
    if not ok: bad += 1
    print("%s%-11s open=%d close=%d" % ("OK " if ok else "!! ", t, o, c))
print("void hr:", len(re.findall(r"<hr>", doc)))
print("h2 count:", len(re.findall(r"<h2 ", doc)), "| TOC links:", len(toc_html))
print("UNBALANCED TAGS:", bad)
