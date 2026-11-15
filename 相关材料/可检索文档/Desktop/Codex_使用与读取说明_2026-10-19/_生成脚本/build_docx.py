# -*- coding: utf-8 -*-
"""把 Codex_使用与读取说明_v1.md 转成排版好的 DOCX。"""
import os
import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"C:\Users\wardc\Desktop\Codex_使用与读取说明_2026-10-19"
SRC = os.path.join(BASE, "Codex_使用与读取说明_v1.md")
OUT = os.path.join(BASE, "Codex_使用与读取说明_v1.docx")

BODY = "宋体"
HEAD = "微软雅黑"
MONO = "Consolas"
DARK = RGBColor(0x1F, 0x2A, 0x44)
GRAY = RGBColor(0x66, 0x66, 0x66)
ACCENT = "1F4E79"
HEADER_BG = "DCE6F1"
ZEBRA_BG = "F2F5FA"
CODE_BG = "F4F4F4"

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.0)
sec.left_margin = Cm(1.9)
sec.right_margin = Cm(1.9)
USABLE = 17.2


def set_font(run, name, size, bold=False, color=None, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)


def style_normal():
    st = doc.styles["Normal"]
    st.font.name = BODY
    st.font.size = Pt(10.5)
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), BODY)
    pf = st.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.35


style_normal()


def shade_paragraph(p, color):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def add_runs(p, text, size=10.5, base_bold=False, mono_size=None):
    """解析 **粗体** 与 `代码` 两种行内格式"""
    if mono_size is None:
        mono_size = max(size - 1.0, 8)
    pattern = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            r = p.add_run(text[pos:m.start()])
            set_font(r, BODY, size, base_bold)
        tok = m.group(0)
        if tok.startswith("**"):
            r = p.add_run(tok[2:-2].replace("`", ""))
            set_font(r, HEAD, size, True)
        else:
            r = p.add_run(tok[1:-1])
            set_font(r, MONO, mono_size, False, RGBColor(0x8B, 0x1A, 0x1A))
        pos = m.end()
    if pos < len(text):
        r = p.add_run(text[pos:])
        set_font(r, BODY, size, base_bold)


def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    add_runs(p, text, size=14, base_bold=True)
    for r in p.runs:
        set_font(r, HEAD, 14, True, DARK)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), ACCENT)
    pbdr.append(bottom)
    pPr.append(pbdr)


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    add_runs(p, text, size=11.5, base_bold=True)
    for r in p.runs:
        set_font(r, HEAD, 11.5, True, RGBColor(0x2E, 0x5C, 0x8A))


def body_p(text, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.35
    add_runs(p, text, size=size)


def bullet(text, size=10.5, indent=0.75):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(indent)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.3
    r = p.add_run("• ")
    set_font(r, BODY, size, False, RGBColor(0x2E, 0x5C, 0x8A))
    add_runs(p, text, size=size)


def num_item(text, size=10.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.3
    add_runs(p, text, size=size)


def quote(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.6)
    pf.space_before = Pt(2)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.3
    add_runs(p, text, size=9.5)
    for r in p.runs:
        r.font.color.rgb = GRAY


def code_block(code):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.25)
    pf.right_indent = Cm(0.25)
    pf.space_before = Pt(3)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.05
    shade_paragraph(p, CODE_BG)
    lines = code.rstrip("\n").split("\n")
    for i, ln in enumerate(lines):
        r = p.add_run(ln)
        set_font(r, MONO, 8.5, False, RGBColor(0x22, 0x22, 0x22))
        if i < len(lines) - 1:
            r.add_break()


def memo(v, w):
    val, typ = v
    el = OxmlElement(f"w:{typ}")
    el.set(qn("w:w"), str(w))
    el.set(qn("w:type"), "dxa")
    return val, el


def add_table(rows):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    if ncols == 2:
        widths = [4.6, 12.6]
    elif ncols == 3:
        widths = [3.8, 8.2, 5.2]
    else:
        widths = [USABLE / ncols] * ncols
    table = doc.add_table(rows=0, cols=ncols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    # 列宽：均分，第一列稍窄
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        trPr = table.rows[ri]._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        if ri == 0:
            tblHeader = OxmlElement("w:tblHeader")
            tblHeader.set(qn("w:val"), "true")
            trPr.append(tblHeader)
        for ci in range(ncols):
            c = cells[ci]
            c.width = Cm(widths[ci])
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            text = row[ci] if ci < len(row) else ""
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            if ri == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(p, text, size=9)
                for r in p.runs:
                    set_font(r, HEAD, 9, True, RGBColor(0x1F, 0x3A, 0x5F))
                shade_cell(c, HEADER_BG)
            else:
                add_runs(p, text, size=9)
                if ri % 2 == 0:
                    shade_cell(c, ZEBRA_BG)
    grid = table._tbl.tblGrid
    for ci, w in enumerate(widths):
        grid.gridCol_lst[ci].set(qn("w:w"), str(int(w * 567)))


def shade_cell(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def add_page_number_footer():
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("第 ")
    set_font(r1, BODY, 9, False, GRAY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    p._p.append(fld)
    r2 = p.add_run(" 页 / 共 ")
    set_font(r2, BODY, 9, False, GRAY)
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld2.append(r)
    p._p.append(fld2)
    r3 = p.add_run(" 页")
    set_font(r3, BODY, 9, False, GRAY)


# ---------------- 解析 Markdown ----------------
lines = open(SRC, encoding="utf-8").read().splitlines()
i = 0
first_title = True

while i < len(lines):
    line = lines[i].rstrip()

    if not line.strip():
        i += 1
        continue

    # 水平分隔线：跳过
    if line.strip() in ("---", "***", "___"):
        i += 1
        continue

    # 代码块
    if line.strip().startswith("```"):
        i += 1
        code_lines = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code_lines.append(lines[i])
            i += 1
        i += 1
        code_block("\n".join(code_lines))
        continue

    # 表格
    if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|\s*$", lines[i + 1].strip()):
        rows = []
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(header)
        i += 2
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(row)
            i += 1
        add_table(rows)
        continue

    # 标题
    if line.startswith("# "):
        text = line[2:].strip()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        set_font(r, HEAD, 20, True, DARK)
        i += 1
        continue

    if line.startswith("## "):
        h1(line[3:].strip())
        i += 1
        continue

    if line.startswith("### "):
        h2(line[4:].strip())
        i += 1
        continue

    # 引用
    if line.startswith(">"):
        text = line.lstrip("> ").strip()
        if text:
            quote(text)
        i += 1
        continue

    # 列表
    if line.startswith("- "):
        bullet(line[2:].strip())
        i += 1
        continue

    m = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
    if m:
        num_item(f"{m.group(1)}. {m.group(2)}")
        i += 1
        continue

    # 版本行（第二段居中小字）
    if line.startswith("版本 v1.0"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
        add_runs(p, line, size=10.5)
        for r in p.runs:
            r.font.color.rgb = GRAY
        i += 1
        continue

    body_p(line)
    i += 1

add_page_number_footer()
doc.core_properties.title = "Codex 使用与读取说明（本机版）v1.0"
doc.core_properties.author = "DSH 整理"
doc.core_properties.subject = "Codex 使用说明 + 本地会话数据读取指南"

doc.save(OUT)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
