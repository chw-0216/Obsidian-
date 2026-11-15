# -*- coding: utf-8 -*-
"""通用 MD → 印痕风格 HTML 转换器。
用法: python md2html_generic.py <src.md> <out.html> "<标题>" "<KICKER>" "<H1>" "<META>" "<FOOTER>"
"""
import re, html, io, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
TITLE = sys.argv[3] if len(sys.argv) > 3 else "文档"
KICKER = sys.argv[4] if len(sys.argv) > 4 else ""
H1 = sys.argv[5] if len(sys.argv) > 5 else TITLE
META = sys.argv[6] if len(sys.argv) > 6 else ""
FOOTER = sys.argv[7] if len(sys.argv) > 7 else ""

lines = io.open(SRC, encoding="utf-8").read().split("\n")

def esc(s): return html.escape(s, quote=False)

def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)
    return s

out, toc = [], []
i, n = 0, len(lines)
while i < n and not lines[i].strip().startswith("# "):
    i += 1
i += 1

while i < n:
    s = lines[i].strip()
    if s.startswith("```"):
        buf = []; i += 1
        while i < n and not lines[i].strip().startswith("```"):
            buf.append(esc(lines[i])); i += 1
        i += 1
        out.append("<pre>" + "\n".join(buf) + "</pre>"); continue
    if s == "---":
        out.append("<hr>"); i += 1; continue
    m = re.match(r"^(#{1,4})\s+(.*)$", s)
    if m:
        lv = len(m.group(1)); txt = m.group(2); hid = "s%d" % len(toc)
        toc.append((lv, txt, hid))
        out.append('<h%d id="%s">%s</h%d>' % (lv, hid, inline(txt), lv)); i += 1; continue
    if s.startswith("|"):
        rows = []
        while i < n and lines[i].strip().startswith("|"):
            rows.append(lines[i].strip()); i += 1
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        data = cells[2:] if len(cells) > 1 and re.match(r"^[\s:\-|]+$", rows[1]) else cells[1:]
        b = ["<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in cells[0]) + "</tr></thead>", "<tbody>"]
        for r in data:
            b.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
        b.append("</tbody>")
        out.append('<div class="tw"><table>' + "".join(b) + "</table></div>"); continue
    if s.startswith(">"):
        buf = []
        while i < n and lines[i].strip().startswith(">"):
            buf.append(inline(lines[i].strip()[1:].strip())); i += 1
        out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>"); continue
    if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
        tag = "ol" if re.match(r"^\d+\.\s+", s) else "ul"
        buf = []
        while i < n:
            t = lines[i].strip()
            if re.match(r"^[-*]\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^[-*]\s+", "", t))); i += 1; continue
            if re.match(r"^\d+\.\s+", t):
                buf.append("<li>%s</li>" % inline(re.sub(r"^\d+\.\s+", "", t))); i += 1; continue
            break
        out.append("<%s>" % tag + "".join(buf) + "</%s>" % tag); continue
    if s == "":
        i += 1; continue
    buf = [inline(s)]; i += 1
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
 font-family:"Source Han Sans SC","Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:15px;line-height:1.78;}
.wrap{max-width:1020px;margin:0 auto;padding:48px 34px 90px;}
header.top{border-bottom:3px double var(--ink);padding-bottom:22px;margin-bottom:8px;}
header.top .kicker{font-size:12px;letter-spacing:.3em;color:var(--red);font-weight:700;}
h1{font-size:29px;line-height:1.35;margin:14px 0 10px;}
header.top .meta{font-size:12.5px;color:var(--soft);line-height:1.9;}
nav.toc{background:#fff;border:1px solid var(--line);border-left:4px solid var(--red);padding:18px 22px;margin:26px 0 40px;border-radius:2px;}
nav.toc b{display:block;font-size:12px;letter-spacing:.2em;color:var(--red);margin-bottom:10px;}
nav.toc a{display:inline-block;color:var(--ink);text-decoration:none;font-size:13px;margin:3px 14px 3px 0;border-bottom:1px solid transparent;}
nav.toc a:hover{border-bottom-color:var(--red);color:var(--red);}
h2{font-size:21px;margin:52px 0 16px;padding-bottom:9px;border-bottom:2px solid var(--ink);}
h3{font-size:16.5px;margin:32px 0 12px;color:var(--red);}
h4{font-size:14.5px;margin:22px 0 10px;}
p{margin:11px 0;}
code{background:#eae4d7;padding:1.5px 6px;border-radius:3px;font-size:12.8px;
 font-family:"Cascadia Mono",Consolas,monospace;color:#7a3226;}
pre{background:#232120;color:#efe9dd;padding:16px 18px;border-radius:3px;overflow-x:auto;
 font-family:"Cascadia Mono",Consolas,monospace;font-size:12.6px;line-height:1.7;border-left:4px solid var(--red);}
pre code{background:none;color:inherit;padding:0;}
blockquote{margin:16px 0;padding:14px 20px;background:#fff;border-left:4px solid var(--red);border-radius:2px;font-size:14.5px;}
.tw{overflow-x:auto;margin:18px 0;}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.2px;border:1px solid var(--line);}
th{background:#232120;color:#f2ede3;text-align:left;padding:9px 12px;font-weight:600;font-size:12.4px;white-space:nowrap;}
td{padding:8px 12px;border-top:1px solid var(--line);vertical-align:top;line-height:1.64;}
tr:nth-child(even) td{background:#faf7f0;}
ul,ol{margin:11px 0;padding-left:24px;}
li{margin:5px 0;}
hr{border:0;border-top:1px dashed var(--line);margin:40px 0;}
i{color:var(--soft);}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--line);font-size:12px;color:var(--soft);text-align:center;}
@media print{body{background:#fff;}nav.toc{page-break-inside:avoid;}h2{page-break-after:avoid;}}
"""

doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>%s</style></head><body><div class="wrap">
<header class="top"><div class="kicker">%s</div><h1>%s</h1><div class="meta">%s</div></header>
<nav class="toc"><b>目录</b>%s</nav>
%s
<footer>%s</footer></div></body></html>""" % (TITLE, CSS, KICKER, H1, META, "".join(toc_html), "\n".join(out), FOOTER)

io.open(OUT, "w", encoding="utf-8").write(doc)

print("OUT bytes:", os.path.getsize(OUT))
bad = 0
for t in ["div","table","thead","tbody","tr","td","th","h2","h3","h4","p","ul","ol","li","blockquote","pre","code","nav","header","footer","style","html","body"]:
    o = len(re.findall(r"<%s(?=[\s>/])" % t, doc)); c = len(re.findall(r"</%s>" % t, doc))
    if o != c: bad += 1; print("!! %s open=%d close=%d" % (t, o, c))
print("h2:", len(re.findall(r"<h2 ", doc)), "| TOC:", len(toc_html), "| UNBALANCED:", bad)
