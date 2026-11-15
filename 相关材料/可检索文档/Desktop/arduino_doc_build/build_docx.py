# -*- coding: utf-8 -*-
"""把腾讯智能文档《这个状态变量是干什么用的》(Arduino 学习对话) 整理成 Word 文档。"""
import json, os, re
from html.parser import HTMLParser

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
BLOCKS = json.load(open(os.path.join(BASE, "blocks.json"), encoding="utf-8"))
IMG_DIR = os.path.join(BASE, "img")
OUT = r"C:\Users\wardc\Desktop\Arduino学习对话整理_这个状态变量是干什么用的.docx"

# ---------- 配色 ----------
NAVY = RGBColor(0x1F, 0x3B, 0x57)
BLUE = RGBColor(0x2E, 0x75, 0xB6)
GREY = RGBColor(0x59, 0x59, 0x59)
LGREY = RGBColor(0x7F, 0x7F, 0x7F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x26, 0x26, 0x26)

FONT_H = "微软雅黑"
FONT_B = "宋体"
FONT_M = "Consolas"

# ---------- 章 / 问 元数据 ----------
CHAPTERS = [
    ("第 1 章", "状态变量与呼吸灯",
     "本章从一张课堂幻灯片上的呼吸灯代码出发，弄清 boolean up 这个状态变量的作用、if/else 的分工，"
     "以及初始化语句为什么不能省；随后把同一思路迁移到传感器场景，并比较三种呼吸灯实现方式。",
     list(range(1, 13))),
    ("第 2 章", "串口调试与 Processing / Unity 联动",
     "本章把开发板内部的数据“看”出来：Serial.begin / print / println 的用法、串口监视器的使用要点，"
     "以及把数据接到 Processing（视觉）和 Unity（游戏）里的写法与注意事项。",
     list(range(13, 19))),
    ("第 3 章", "蜂鸣器基础：有源蜂鸣器",
     "本章认识有源蜂鸣器：接线方式、用 digitalWrite 控制响停，以及一段用高低电平“手动震荡”的进阶代码；"
     "同时澄清“蜂鸣器用来展现家电功率”的误解。",
     list(range(19, 23))),
    ("第 4 章", "综合联动与数据类型",
     "本章把呼吸灯与蜂鸣器写进同一个程序，用 millis() 做非阻塞定时、让蜂鸣器音随亮度变化；"
     "随后拆解联动代码里出现的 unsigned long。",
     list(range(23, 25))),
    ("第 5 章", "有源与无源蜂鸣器、音调与频率",
     "本章对比两类蜂鸣器，给出 C 大调频率表与 tone() / noTone() 的用法，"
     "最后解析一段用低音 Do–Si 演奏旋律的代码。",
     list(range(25, 28))),
]

TITLES = {
    1: "图中的状态变量 up 有什么用",
    2: "if / else 在呼吸灯里怎么分工",
    3: "逐行拆解呼吸灯代码",
    4: "传感器项目里怎么用状态变量",
    5: "状态变量之后还能用哪些变量",
    6: "原文代码 OCR：呼吸灯完整例程",
    7: "三行初始化语句的含义",
    8: "初始状态与 if / else 的关系",
    9: "为什么 boolean up = true 是必须的",
    10: "三种呼吸灯实现思路的梳理",
    11: "没有初始值时程序会“乱猜”吗",
    12: "拆解 boolean up = true; 及缺省后果",
    13: "串口调试（Debugging）是干什么用的",
    14: "用串口联动 Unity / Processing",
    15: "串口语法：Serial.begin 与 println 格式",
    16: "串口监视器与传感器数据",
    17: "Serial.begin(9600) 里的 9600 是什么",
    18: "串口代码 OCR 与 Processing 联调",
    19: "有源蜂鸣器怎么用",
    20: "蜂鸣器进阶代码逐行分析",
    21: "蜂鸣器能“展现家电功率”吗",
    22: "buzzer + OUTPUT：这段代码的输出含义",
    23: "呼吸灯 + 蜂鸣器联动完整代码",
    24: "unsigned long 是什么、为什么用它计时",
    25: "有源与无源蜂鸣器的区别",
    26: "音调与频率：有源能变调吗、频率表",
    27: "低音 Do–Si 旋律代码解析",
}

IMG_DESC = {
    1: "课堂投影：Analog Out 幻灯片，呼吸灯示例代码（对应 Q1）",
    2: "同一页幻灯片叠加手机屏摄；右侧为心形、星形 LED 灯环（对应 Q5）",
    3: "Debugging 幻灯片：通过串行通信输出数据、Serial.print 与 println（对应 Q13）",
    4: "Debugging 幻灯片：串口语法代码（Serial.begin / println 格式）（对应 Q15）",
    5: "实拍串口监视器界面与 RGB 灯代码（部分被遮挡）（对应 Q16）",
    6: "有源蜂鸣器接线示意：信号接数字引脚 D8（对应 Q19）",
    7: "有源蜂鸣器进阶代码幻灯片（高/低频交替报警）（对应 Q20）",
    8: "无源蜂鸣器幻灯片：连接方法与调声函数 tone / noTone（对应 Q26）",
    9: "无源蜂鸣器代码：tone(…,131,150) 等低音旋律（对应 Q27）",
}

# ---------- 剔除表格块下的嵌套文本（单元格内容会重复出现在正文） ----------
_filtered = []
_i = 0
while _i < len(BLOCKS):
    _b = BLOCKS[_i]
    _filtered.append(_b)
    if _b["type"] == "simple_table":
        _d = _b.get("depth", 0)
        _j = _i + 1
        while _j < len(BLOCKS) and BLOCKS[_j].get("depth", 0) > _d:
            _j += 1
        _i = _j
    else:
        _i += 1
BLOCKS = _filtered

# ---------- 生成统计 ----------
code_no, img_no = {}, {}
_ci = _ii = 0
for _idx, _b in enumerate(BLOCKS):
    if _b["type"] == "code":
        _ci += 1
        code_no[_idx] = _ci
    elif _b["type"] == "image":
        _ii += 1
        img_no[_idx] = _ii

# ---------- 嵌套去重：父块 innerText 会包含子块内容 ----------
def _first_line(t):
    for ln in (t or "").split("\n"):
        if ln.strip():
            return ln.strip()
    return ""


for _i, _b in enumerate(BLOCKS):
    _d = _b.get("depth", 0)
    _j = _i + 1
    _desc = []
    while _j < len(BLOCKS) and BLOCKS[_j].get("depth", 0) > _d:
        _fl = _first_line(BLOCKS[_j].get("text", ""))
        if _fl:
            _desc.append(_fl)
        _j += 1
    if not _desc:
        continue
    _lines = (_b.get("text") or "").split("\n")
    if len(_lines) <= 1:
        continue
    _keep = []
    for _ln in _lines:
        if _ln.strip() in _desc:
            break
        _keep.append(_ln)
    if _keep and len(_keep) < len(_lines):
        _nb = dict(_b)
        _nb["text"] = "\n".join(_keep)
        BLOCKS[_i] = _nb

# ---------- 切分对话轮次 ----------
turn_start = [i for i, b in enumerate(BLOCKS)
              if b["type"] == "text" and b["text"].startswith("用户")]
TURNS = []
for k, st in enumerate(turn_start):
    en = turn_start[k + 1] if k + 1 < len(turn_start) else len(BLOCKS)
    seg = list(range(st, en))
    ai_abs = next((j for j in seg if BLOCKS[j]["type"] == "text"
                   and BLOCKS[j]["text"].startswith("元宝")), None)
    if ai_abs is None:
        continue
    pos = seg.index(ai_abs)
    TURNS.append({
        "no": k + 1,
        "q": [(j, BLOCKS[j]) for j in seg[1:pos]],
        "a": [(j, BLOCKS[j]) for j in seg[pos + 1:]],
    })
assert len(TURNS) == 27, len(TURNS)

# ---------- 低层工具 ----------
def set_run(run, size=10.5, bold=False, italic=False, color=None, font=FONT_B, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    name = FONT_M if mono else font
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    rf.set(qn("w:ascii"), name)
    rf.set(qn("w:hAnsi"), name)
    rf.set(qn("w:eastAsia"), FONT_B if mono else name)


def shade_par(par, fill):
    ppr = par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def shade_cell(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def border_par(par, sides=("left",), sz=12, color="2E75B6", space=4):
    ppr = par._p.get_or_add_pPr()
    bdr = ppr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        ppr.append(bdr)
    for side in sides:
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), str(space))
        el.set(qn("w:color"), color)
        bdr.append(el)


def cell_borders(cell, color="C9D3E0", sz=4):
    tcpr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        b.append(el)
    tcpr.append(b)


def set_cell_margins(table, top=40, bottom=40, left=70, right=70):
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{k}")
        el.set(qn("w:w"), str(v))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr.append(mar)


def no_split(par):
    ppr = par._p.get_or_add_pPr()
    el = OxmlElement("w:keepLines")
    ppr.append(el)


def add_field(par, instr, size=9, color=LGREY):
    run = par.add_run()
    set_run(run, size=size, color=color, font=FONT_B)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    par._p.append(fld)


# ---------- 行内格式解析 ----------
class InlineParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.runs = []

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            self.stack.append(dict(attrs).get("style", "") or "")
        elif tag == "br":
            self.runs.append(("\n", False, False, False))

    def handle_endtag(self, tag):
        if tag == "span" and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not data:
            return
        bold = any("font-weight:bold" in s for s in self.stack)
        ital = any("font-style:italic" in s for s in self.stack)
        grey = any("text-grey" in s for s in self.stack)
        self.runs.append((data, bold, ital, grey))


def parse_inline(html):
    p = InlineParser()
    p.feed(html or "")
    out = []
    for txt, bold, ital, grey in p.runs:
        if not txt:
            continue
        if out and out[-1][1] == bold and out[-1][2] == ital and out[-1][3] == grey:
            out[-1][0] += txt
        else:
            out.append([txt, bold, ital, grey])
    return [tuple(x) for x in out]


def add_runs(par, runs, size=10.5, color=DARK, font=FONT_B, bold_all=False):
    for txt, bold, ital, grey in runs:
        # 原文残留的 Markdown 粗体标记 **…** 转成真正的加粗
        segs = txt.split("**")
        for k, seg in enumerate(segs):
            if not seg:
                continue
            r = par.add_run(seg)
            set_run(r, size=size, bold=(bold or bold_all or (k % 2 == 1)),
                    italic=ital, color=(LGREY if grey else color), font=font)


def split_runs_by_newline(runs):
    """把行内 runs 按换行拆成若干“段落 runs”。"""
    parts = [[]]
    for txt, bold, ital, grey in runs:
        segs = txt.split("\n")
        for k, seg in enumerate(segs):
            if k > 0:
                parts.append([])
            if seg:
                parts[-1].append((seg, bold, ital, grey))
    return parts


def multiline_runs(text, html):
    """优先用 html 还原行内加粗；若换行数对不上则退回纯文本。"""
    runs = parse_inline(html) if html else [(text, False, False, False)]
    parts = split_runs_by_newline(runs)
    want = text.count("\n") + 1
    if len(parts) != want:
        parts = [[(ln, False, False, False)] for ln in text.split("\n")]
    return [p for p in parts if p]


# ---------- 文档骨架 ----------
doc = Document()

# 页面设置 A4
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.3)
sec.bottom_margin = Cm(2.1)
sec.left_margin = Cm(2.5)
sec.right_margin = Cm(2.3)
sec.header_distance = Cm(1.2)
sec.footer_distance = Cm(1.1)
sec.different_first_page_header_footer = True

# 默认样式
normal = doc.styles["Normal"]
normal.font.name = FONT_B
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK
normal.paragraph_format.line_spacing = 1.45
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.space_before = Pt(0)
rf = normal.element.rPr.rFonts
rf.set(qn("w:eastAsia"), FONT_B)

core = doc.core_properties
core.title = "这个状态变量是干什么用的（Arduino 学习对话整理）"
core.subject = "腾讯智能文档《这个状态变量是干什么用的》整理稿"
core.author = "DeepSeek Harness"
core.comments = "原文 27 轮问答，按主题重排为 5 章；内容保持原意，整理者补充内容已标注。"


def blank(space=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("")
    set_run(r, size=space)
    return p


def h1(text, kicker=None, new_page=True):
    p = doc.add_paragraph(style="Heading 1")
    pf = p.paragraph_format
    pf.space_before = Pt(16)
    pf.space_after = Pt(14)
    pf.keep_with_next = True
    if new_page:
        pf.page_break_before = True
    if kicker:
        r = p.add_run(kicker + "　")
        set_run(r, size=20, bold=True, color=BLUE, font=FONT_H)
    r = p.add_run(text)
    set_run(r, size=20, bold=True, color=NAVY, font=FONT_H)
    border_par(p, sides=("bottom",), sz=10, color="2E75B6", space=6)
    return p


def h2(text):
    p = doc.add_paragraph(style="Heading 2")
    pf = p.paragraph_format
    pf.space_before = Pt(15)
    pf.space_after = Pt(7)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, size=13.5, bold=True, color=BLUE, font=FONT_H)
    return p


def h3(text):
    p = doc.add_paragraph(style="Heading 3")
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, size=11.5, bold=True, color=NAVY, font=FONT_H)
    return p


def h4(text):
    p = doc.add_paragraph(style="Heading 4")
    pf = p.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, size=10.5, bold=True, color=GREY, font=FONT_H)
    return p


def body(text, runs=None, size=10.5, space_after=4, indent=0.0, first_line=0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if indent:
        pf.left_indent = Cm(indent)
    if first_line:
        pf.first_line_indent = Cm(first_line)
    if runs:
        add_runs(p, runs, size=size)
    else:
        r = p.add_run(text)
        set_run(r, size=size, color=DARK)
    return p


def note(text, size=9, color=LGREY, align=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.25
    if align is not None:
        pf.alignment = align
    r = p.add_run(text)
    set_run(r, size=size, italic=False, color=color, font=FONT_H)
    return p


def code_block(code, cap=None):
    if cap:
        note(cap, size=8.5, color=LGREY)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.08
    pf.left_indent = Cm(0.25)
    pf.right_indent = Cm(0.15)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    lines = code.replace("\u200c", "").rstrip("\n").split("\n")
    for i, line in enumerate(lines):
        r = p.add_run(line if line else " ")
        set_run(r, size=8.5, color=RGBColor(0x1A, 0x1A, 0x1A), font=FONT_M, mono=True)
        if i != len(lines) - 1:
            r.add_break()
    pf.keep_together = True
    shade_par(p, "F5F7FA")
    border_par(p, sides=("top", "left", "bottom", "right"), sz=4, color="D3DBE6", space=4)
    return p


def quote_block(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(6)
    pf.left_indent = Cm(0.45)
    pf.line_spacing = 1.3
    lines = text.split("\n")
    for i, line in enumerate(lines):
        r = p.add_run(line)
        set_run(r, size=9.5, color=GREY, font=FONT_B)
        if i != len(lines) - 1:
            r.add_break()
    shade_par(p, "F7F9FC")
    border_par(p, sides=("left",), sz=18, color="C9D6E5", space=6)
    return p


def table_block(rows, font_size=9, tight=False):
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    set_cell_margins(t, top=30 if tight else 40, bottom=30 if tight else 40)
    for ri, trow in enumerate(t.rows):
        trpr = trow._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if ri == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        row = rows[ri]
        for ci in range(ncol):
            cell = t.cell(ri, ci)
            txt = row[ci] if ci < len(row) else ""
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0 if tight else 1.18
            r = p.add_run(txt)
            if ri == 0:
                set_run(r, size=font_size, bold=True, color=WHITE, font=FONT_H)
                shade_cell(cell, "2E75B6")
            else:
                set_run(r, size=font_size, color=DARK)
                if ri % 2 == 0:
                    shade_cell(cell, "F2F6FB")
            cell_borders(cell)
    # 表后留白
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run("")
    set_run(r, size=2)
    return t


def image_block(shot, desc, width=13.6):
    path = os.path.join(IMG_DIR, f"shot_{shot - 1}.png")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(path, width=Cm(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(0)
    cap.paragraph_format.space_after = Pt(8)
    r = cap.add_run(f"图 {shot}　{desc}")
    set_run(r, size=8.5, color=LGREY, font=FONT_H)
    return p


def question_box(texts):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(8)
    pf.left_indent = Cm(0.15)
    pf.right_indent = Cm(0.1)
    pf.line_spacing = 1.35
    r = p.add_run("用户提问")
    set_run(r, size=8, bold=True, color=BLUE, font=FONT_H)
    r.add_break()
    first = True
    for txt in texts:
        if not first:
            r.add_break()
        first = False
        r2 = p.add_run(txt)
        set_run(r2, size=10.5, color=RGBColor(0x1F, 0x33, 0x4D), font=FONT_B)
    shade_par(p, "EAF2FB")
    border_par(p, sides=("left",), sz=24, color="2E75B6", space=6)
    return p


def divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("")
    set_run(r, size=2)
    border_par(p, sides=("bottom",), sz=4, color="DCE3EC", space=1)


def list_item(text, depth=0, kind="bullet", num=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    base = 0.55 + depth * 0.6
    pf.left_indent = Cm(base)
    pf.first_line_indent = Cm(-0.45)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.4
    if kind == "bullet":
        mark = "• " if depth == 0 else "◦ "
    else:
        mark = f"{num}. " if depth == 0 else f"（{num}）"
    r = p.add_run(mark)
    if kind == "number":
        set_run(r, size=10.5, bold=True, color=BLUE)
    else:
        set_run(r, size=10.5, color=BLUE)
    return p


def fill_list_item(p, runs):
    add_runs(p, runs, size=10.5)


def cont_line(text, depth, runs=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.95 + depth * 0.6)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.4
    if runs:
        add_runs(p, runs, size=10, color=DARK)
    else:
        r = p.add_run(text)
        set_run(r, size=10, color=GREY)
    return p


# ---------- 页眉页脚 ----------
def build_header_footer(section):
    hdr = section.header
    hp = hdr.paragraphs[0]
    hp.paragraph_format.space_after = Pt(0)
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(16.2), WD_TAB_ALIGNMENT.RIGHT)
    r = hp.add_run("Arduino 学习对话整理")
    set_run(r, size=8.5, color=LGREY, font=FONT_H)
    r = hp.add_run("\t腾讯智能文档《这个状态变量是干什么用的》")
    set_run(r, size=8.5, color=LGREY, font=FONT_H)
    border_par(hp, sides=("bottom",), sz=4, color="DCE3EC", space=2)

    ftr = section.footer
    fp = ftr.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("— ")
    set_run(r, size=9, color=LGREY)
    add_field(fp, " PAGE ", size=9, color=LGREY)
    r = fp.add_run(" —")
    set_run(r, size=9, color=LGREY)


build_header_footer(sec)

# =====================================================================
# 封面
# =====================================================================
blank(90)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
r = p.add_run("腾讯智能文档　·　对话整理")
set_run(r, size=11, bold=True, color=BLUE, font=FONT_H)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(4)
r = p.add_run("这个状态变量是干什么用的")
set_run(r, size=34, bold=True, color=NAVY, font=FONT_H)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(2)
p.paragraph_format.space_after = Pt(14)
r = p.add_run("Arduino 入门对话整理稿　·　状态变量 / 串口通信 / 蜂鸣器")
set_run(r, size=14, color=BLUE, font=FONT_H)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(2)
p.paragraph_format.space_after = Pt(18)
r = p.add_run("")
set_run(r, size=2)
border_par(p, sides=("bottom",), sz=16, color="2E75B6", space=2)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
r = p.add_run("27 轮问答　·　27 段代码　·　4 张表格　·　9 张配图")
set_run(r, size=11, color=GREY, font=FONT_H)

blank(180)

info = [
    ("来　　源", "docs.qq.com/aio/DTXBTT3VndWdCSXFk（腾讯文档 · 智能文档）"),
    ("文档类型", "腾讯智能文档（smart canvas）· 用户 ↔ 腾讯元宝 AI 对话"),
    ("内容规模", "27 轮问答｜27 段代码｜4 张表格｜9 张配图"),
    ("整理日期", "2026-10-22（Asia/Shanghai）"),
]
t = doc.add_table(rows=len(info), cols=2)
t.autofit = False
t.alignment = WD_TABLE_ALIGNMENT.LEFT
for i, (k, v) in enumerate(info):
    c0, c1 = t.cell(i, 0), t.cell(i, 1)
    c0.width = Cm(2.8)
    c1.width = Cm(13.4)
    for c in (c0, c1):
        c.text = ""
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
    r = c0.paragraphs[0].add_run(k)
    set_run(r, size=9, color=LGREY, font=FONT_H)
    r = c1.paragraphs[0].add_run(v)
    set_run(r, size=9, color=GREY)

# =====================================================================
# 整理说明
# =====================================================================
h1("整理说明")

body("本文档是腾讯智能文档《这个状态变量是干什么用的》的整理稿。原文记录了用户与腾讯元宝 AI 围绕 Arduino 入门的 27 轮问答，"
     "内容从一盏“呼吸灯”的状态变量讲起，逐步延伸到 if/else 分支、传感器状态机、串口调试、Processing / Unity 联动，"
     "以及有源、无源蜂鸣器的用法与音调频率。")

body("整理方式：① 按主题重排为 5 章，每一问都保留“问题原文 + 回答正文”；② 清理原文中平台产生的行号、空块与排版噪声；"
     "③ 代码块统一为等宽字体并保留注释；④ 4 张表格、9 张课堂/实物配图原样内嵌；⑤ 原文的三级小节标题保留为三级标题；"
     "⑥ 原文中折叠的“引用 N 篇资料”保留提示文字，未展开。")

body("问答内容保持原意，未改动技术结论。整理者补充的内容——章节导读、知识地图、速查表、勘误提示——均已明确标注。"
     "原文含 AI 生成内容（文末有注），部分 OCR 段落有残缺、个别说法建议以实测为准，详见附录 C。")

note("提示：在 Word 中打开后，可用「视图 → 导航窗格」按标题快速跳转；封面不显示页码，其余页在页脚显示页码。",
     size=9, color=LGREY)

h2("知识地图")
table_block([
    ["章节", "覆盖问题", "核心知识点"],
    ["第 1 章　状态变量与呼吸灯", "Q1–Q12", "状态变量 up、if/else 分工、初始化、传感器状态机、三种实现思路"],
    ["第 2 章　串口调试与外部联动", "Q13–Q18", "Serial 语法、串口监视器、Processing / Unity 联动"],
    ["第 3 章　蜂鸣器基础", "Q19–Q22", "有源蜂鸣器接线、digitalWrite 控制、手动震荡报警"],
    ["第 4 章　综合联动与数据类型", "Q23–Q24", "呼吸灯 + 蜂鸣器联动、millis 非阻塞、unsigned long"],
    ["第 5 章　源、音调与频率", "Q25–Q27", "有源 vs 无源、tone()、C 大调频率表、低音旋律"],
])

# =====================================================================
# 目录
# =====================================================================
_dir_h = h1("目　录")
_dir_h.paragraph_format.space_before = Pt(6)
_dir_h.paragraph_format.space_after = Pt(6)
for (num, title, _intro, qs) in CHAPTERS:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{num}　{title}")
    set_run(r, size=11, bold=True, color=NAVY, font=FONT_H)
    for q in qs:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(0.7)
        pf.first_line_indent = Cm(-0.7)
        pf.space_after = Pt(0)
        pf.line_spacing = 0.95
        pf.tab_stops.add_tab_stop(Cm(1.7), WD_TAB_ALIGNMENT.LEFT)
        r = p.add_run(f"Q{q}")
        set_run(r, size=8.5, bold=True, color=BLUE, font=FONT_H)
        r = p.add_run("\t")
        r = p.add_run(TITLES[q])
        set_run(r, size=9, color=GREY)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(8)
p.paragraph_format.space_after = Pt(1.5)
r = p.add_run("附录")
set_run(r, size=11.5, bold=True, color=NAVY, font=FONT_H)
for txt in ["附录 A　知识点速查表", "附录 B　代码索引", "附录 C　勘误与技术复核提示",
            "附录 D　原文与配图说明"]:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.7)
    pf.space_after = Pt(0.5)
    r = p.add_run(txt)
    set_run(r, size=9, color=GREY)

# =====================================================================
# 正文
# =====================================================================
def render_question(qblocks):
    texts = []
    img = None
    for idx, b in qblocks:
        if b["type"] == "text" and b["text"]:
            texts.append(b["text"])
        elif b["type"] == "image":
            img = img_no.get(idx)
        elif b["type"] == "code":
            texts.append(b["code"])
    if texts:
        question_box(texts)
    if img:
        image_block(img, IMG_DESC.get(img, ""))


def render_answer(ablocks, turn_no):
    numbered = {}
    run_no = 0
    prev_type = None
    for idx, b in ablocks:
        t = b["type"]
        txt = b.get("text", "")
        if t == "text":
            run_no = 0
            if "文档部分内容可能由 AI 生成" in txt:
                continue
            if not txt:
                continue
            for part in multiline_runs(txt, b.get("html", "")):
                joined = "".join(x[0] for x in part).strip()
                if not joined or re.fullmatch(r"\d+\.", joined):
                    continue
                body("", runs=part, size=10.5)
            prev_type = t
        elif t in ("header2", "header3"):
            run_no = 0
            if txt:
                h3(txt)
            prev_type = t
        elif t == "header4":
            run_no = 0
            if txt:
                h4(txt)
            prev_type = t
        elif t in ("bulleted_list", "numbered_list"):
            if not txt:
                continue
            parts = multiline_runs(txt, b.get("html", ""))
            if not parts:
                continue
            first_text = "".join(x[0] for x in parts[0]).strip()
            if t == "numbered_list":
                m = re.match(r"^(\d+)\.\s*$", first_text)
                if m:
                    num = int(m.group(1))
                    content = parts[1:]
                else:
                    m2 = re.match(r"^(\d+)\.\s*(.+)$", first_text, re.S)
                    if m2:
                        num = int(m2.group(1))
                        content = [[(m2.group(2), False, False, False)]] + parts[1:]
                    else:
                        run_no += 1
                        num = run_no
                        content = parts
                if not content:
                    continue
                p = list_item("", depth=b["depth"], kind="number", num=num)
                add_runs(p, content[0], size=10.5)
                for extra in content[1:]:
                    cont_line("", depth=b["depth"], runs=extra)
            else:
                run_no = 0
                p = list_item("", depth=b["depth"], kind="bullet")
                add_runs(p, parts[0], size=10.5)
                for extra in parts[1:]:
                    cont_line("", depth=b["depth"], runs=extra)
            prev_type = t
        elif t == "code":
            run_no = 0
            code_block(b["code"])
            prev_type = t
        elif t == "simple_table":
            run_no = 0
            table_block(b["table"])
            prev_type = t
        elif t == "image":
            run_no = 0
            n = img_no.get(idx)
            if n:
                image_block(n, IMG_DESC.get(n, ""))
            prev_type = t
        elif t == "quote":
            run_no = 0
            quote_block(txt)
            prev_type = t
        elif t == "toggle":
            run_no = 0
            note(f"〔原文折叠区〕{txt}", size=8.5, color=LGREY)
            prev_type = t
        elif t == "divider":
            divider()
            prev_type = t


for (num, title, intro, qs) in CHAPTERS:
    h1(title, kicker=num)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(10)
    pf.left_indent = Cm(0.3)
    pf.line_spacing = 1.4
    r = p.add_run("本章导读　")
    set_run(r, size=9, bold=True, color=BLUE, font=FONT_H)
    r = p.add_run(intro)
    set_run(r, size=9.5, color=GREY, font=FONT_H)
    shade_par(p, "F6F8FB")
    border_par(p, sides=("left",), sz=18, color="B7CBE3", space=6)

    for q in qs:
        turn = TURNS[q - 1]
        h2(f"Q{q}　{TITLES[q]}")
        render_question(turn["q"])
        render_answer(turn["a"], q)

# =====================================================================
# 附录 A 知识点速查表
# =====================================================================
h1("知识点速查表", kicker="附录 A")
body("下表把 27 轮问答里的核心概念压缩成一句话，右侧标注对应问题，方便回原文查细节。", size=10)

table_block([
    ["概念 / 语法", "一句话要点", "对应问题"],
    ["状态变量 up", "boolean 方向标记：控制亮度“变亮 / 变暗”，到 0 与 255 时翻转", "Q1、Q8、Q9"],
    ["if / else", "按 up 的真假走不同分支：if 里 val++，else 里 val--", "Q2、Q7"],
    ["初始化三行", "设定引脚、起始亮度、初始方向，为 loop() 提供起点", "Q7、Q12"],
    ["缺省初始值", "全局变量默认 false：程序先走 else，亮度从 0 减到 -1，节奏错乱", "Q9、Q11、Q12"],
    ["三种呼吸灯方案", "硬件模拟电路 / for 循环直控 / 状态变量控制方向", "Q10"],
    ["传感器状态机", "用状态变量记录“上一次状态”，避免重复触发、实现模式切换与迟滞", "Q4"],
    ["变量扩展", "enum 多状态、阈值/步长变量、millis() 时间变量、传感器读数变量", "Q5"],
    ["Serial.begin(9600)", "初始化串口，9600 是波特率（bps），收发两端必须一致", "Q13、Q15、Q17"],
    ["print vs println", "println 在末尾多输出回车换行；print 不换行", "Q13"],
    ["串口监视器", "Arduino IDE 内查看开发板输出；波特率需与代码一致", "Q13、Q16"],
    ["Processing 联动", "import processing.serial.*；bufferUntil('\\n') 后按行读数", "Q14、Q18"],
    ["Unity 联动", "System.IO.Ports 读串口；Api Compatibility Level 设为 .NET Framework", "Q14"],
    ["有源蜂鸣器", "内部自带振荡电路，通电即响、音调固定，digitalWrite 只能控制响停", "Q19、Q25"],
    ["无源蜂鸣器", "需要外部方波，用 tone(pin, freq) / noTone(pin) 控制音调", "Q25、Q26"],
    ["C 大调频率表", "C4=262Hz … B5=988Hz；A4=440Hz 为基准", "Q26"],
    ["unsigned long", "0–4,294,967,295；配合 millis() 记录时间点，避免溢出", "Q24"],
    ["非阻塞定时", "if (millis() - prev >= interval) { … } 代替 delay()", "Q23"],
    ["map()", "把亮度 0–255 映射为蜂鸣器半周期 10–1，实现音随亮度变化", "Q23"],
], font_size=8.5, tight=True)

# =====================================================================
# 附录 B 代码索引
# =====================================================================
h1("代码索引", kicker="附录 B")
body("正文共收录原文 27 段代码。下表按出现顺序列出所在问题、行数与首行摘要，便于检索。", size=10)

code_rows = [["编号", "所在问题", "行数", "首行 / 内容摘要"]]
for idx, b in enumerate(BLOCKS):
    if b["type"] != "code":
        continue
    turn = next((t["no"] for t in TURNS
                 if any(j == idx for j, _ in t["a"]) or any(j == idx for j, _ in t["q"])), None)
    code = b["code"].replace("\u200c", "").strip("\n")
    lines = [x for x in code.split("\n") if x.strip()]
    head = lines[0].strip() if lines else ""
    head = re.sub(r"\s+", " ", head)
    if len(head) > 46:
        head = head[:46] + "…"
    code_rows.append([f"{code_no[idx]:02d}", f"Q{turn}" if turn else "—",
                      str(len(code.split("\n"))), head])
table_block(code_rows)

# =====================================================================
# 附录 C 勘误与复核提示
# =====================================================================
h1("勘误与技术复核提示", kicker="附录 C")

h3("原文已指出的问题")
for txt in [
    "注释拼写：//tracks weather the count is up or down 中 weather 应为 whether（原文多处提及）。",
    "示例代码缺少 pinMode(ledPin, OUTPUT);：呼吸灯示例的 setup() 为空，实际运行前应补上。",
    "Serial.println(currentValue, BYTE) 在较新 Arduino 版本中已不推荐使用（原文已提示）。",
    "有源蜂鸣器无法靠 digitalWrite 改变音调：音调由内部振荡电路决定，外部电路只能控制响/停。",
]:
    p = doc.add_paragraph(style=None)
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.first_line_indent = Cm(-0.3)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("▪ ")
    set_run(r, size=10, color=BLUE)
    r = p.add_run(txt)
    set_run(r, size=10)

h3("整理者补充提示（建议实测确认）")
for txt in [
    "“val 从 0 减 1 变成 -1，PWM 中被当作 255”属于实现相关行为，不同 Arduino 核心的处理可能不同；建议以实际板子实测为准，或先把 val 声明为 unsigned int。",
    "同一位引脚不能同时用于两种输出（如 LED 与蜂鸣器）时，请按原文接线说明分开引脚；本整理未改动原文接线方案。",
    "图片为课堂投影与手机实拍，部分代码被遮挡或反光，Q6、Q12、Q16 的“OCR”内容本身不完整（原文已说明“部分被遮挡”），请以幻灯原图为准。",
    "原文多处“引用 N 篇资料作为参考”为折叠区，本次整理未展开，也未逐条核对引用来源。",
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.first_line_indent = Cm(-0.3)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("▪ ")
    set_run(r, size=10, color=BLUE)
    r = p.add_run(txt)
    set_run(r, size=10)

# =====================================================================
# 附录 D 原文与配图说明
# =====================================================================
h1("原文与配图说明", kicker="附录 D")
body("原文来源：腾讯智能文档《这个状态变量是干什么用的》"
     "（https://docs.qq.com/aio/DTXBTT3VndWdCSXFk，本地文档 ID DTXBTT3VndWdCSXFk / MpSOugugBIqd）。"
     "该文档为“智能文档（smart canvas）”类型，正文由用户与元宝的对话块组成，文末注明“文档部分内容可能由 AI 生成”。", size=10)

body("整理时通过渲染页面逐块提取文本、代码、表格与图片，再按主题重排；图片以页面渲染截图的方式内嵌。"
     "下图为配图与原文位置的对应关系。", size=10)

img_rows = [["图号", "所在问题", "内容说明"]]
for n in range(1, 10):
    owner = next((t["no"] for t in TURNS
                  if any(idx in img_no and img_no[idx] == n
                         for idx, _ in (t["q"] + t["a"]))), None)
    img_rows.append([f"图 {n}", f"Q{owner}" if owner else "—", IMG_DESC.get(n, "")])
table_block(img_rows)

note("说明：本整理稿仅用于学习与个人参考；原文版权归原作者所有。", size=9, color=LGREY)

doc.save(OUT)
print("saved:", OUT)
print("paragraphs:", len(doc.paragraphs), "tables:", len(doc.tables))
