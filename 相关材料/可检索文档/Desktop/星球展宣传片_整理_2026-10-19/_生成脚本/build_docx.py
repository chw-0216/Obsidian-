# -*- coding: utf-8 -*-
"""生成《寻星展宣传片_拍摄执行方案_v0.1.docx》"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\wardc\Desktop\星球展宣传片_整理_2026-10-19\寻星展宣传片_拍摄执行方案_v0.2.docx"

BODY_FONT = "宋体"
HEAD_FONT = "微软雅黑"
DARK = RGBColor(0x1F, 0x2A, 0x44)
GRAY = RGBColor(0x66, 0x66, 0x66)
ACCENT = "1F4E79"
HEADER_BG = "DCE6F1"
ZEBRA_BG = "F2F5FA"

doc = Document()

# ---------- page setup ----------
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


def body_style():
    st = doc.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = Pt(10.5)
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), BODY_FONT)
    pf = st.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.4


body_style()


def para(text="", size=10.5, bold=False, color=None, align=None,
         name=BODY_FONT, space_before=0, space_after=4, first_indent=False, italic=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.4
    if first_indent:
        pf.first_line_indent = Pt(size * 2)
    r = p.add_run(text)
    set_font(r, name, size, bold, color, italic)
    return p


def h1(text, num=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14)
    pf.space_after = Pt(6)
    pf.keep_with_next = True
    r = p.add_run((num + "  " if num else "") + text)
    set_font(r, HEAD_FONT, 14, True, DARK)
    # bottom border
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), ACCENT)
    pbdr.append(bottom)
    # insert pBdr at schema-correct position (before shd/spacing/ind/jc/...)
    successors = ("w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
                  "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
                  "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
                  "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
                  "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
                  "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")
    inserted = False
    for tag in successors:
        el = pPr.find(qn(tag))
        if el is not None:
            el.addprevious(pbdr)
            inserted = True
            break
    if not inserted:
        pPr.append(pbdr)
    return p


def h2(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_font(r, HEAD_FONT, 11.5, True, RGBColor(0x2E, 0x5C, 0x8A))
    return p


def bullet(text, size=10.5, bold_prefix=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.35
    r0 = p.add_run("• ")
    set_font(r0, BODY_FONT, size, False, RGBColor(0x2E, 0x5C, 0x8A))
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        set_font(rb, BODY_FONT, size, True)
    r = p.add_run(text)
    set_font(r, BODY_FONT, size)
    return p


def num_item(idx, text, size=10.5, bold_prefix=None, spacing=1.35):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = spacing
    r0 = p.add_run(f"{idx}. ")
    set_font(r0, BODY_FONT, size, True, RGBColor(0x2E, 0x5C, 0x8A))
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        set_font(rb, BODY_FONT, size, True)
    r = p.add_run(text)
    set_font(r, BODY_FONT, size)
    return p


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    successors = ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
                  "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge",
                  "w:tcPrChange")
    inserted = False
    for tag in successors:
        el = tcPr.find(qn(tag))
        if el is not None:
            el.addprevious(shd)
            inserted = True
            break
    if not inserted:
        tcPr.append(shd)


def cell_margins(table, top=40, bottom=40, left=80, right=80):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    look = tblPr.find(qn("w:tblLook"))
    if look is not None:
        look.addprevious(mar)
    else:
        tblPr.append(mar)


def make_table(headers, rows, widths, font_size=8.5, header_size=8.8, zebra=True):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    cell_margins(table)
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        c.width = Cm(widths[i])
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        set_font(r, HEAD_FONT, header_size, True, RGBColor(0x1F, 0x3A, 0x5F))
        shade(c, HEADER_BG)
    # repeat header row
    trPr = hdr._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)

    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        trPr = table.rows[ri + 1]._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        cant.set(qn("w:val"), "true")
        trPr.append(cant)
        for ci, val in enumerate(row):
            c = cells[ci]
            c.width = Cm(widths[ci])
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(str(val))
            set_font(r, BODY_FONT, font_size)
            if zebra and ri % 2 == 1:
                shade(c, ZEBRA_BG)
    # enforce widths on grid
    tbl = table._tbl
    grid = tbl.tblGrid
    for i, w in enumerate(widths):
        grid.gridCol_lst[i].set(qn("w:w"), str(int(w * 567)))
    return table


def add_page_number_footer():
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("第 ")
    set_font(r1, BODY_FONT, 9, False, GRAY)
    fld1 = OxmlElement("w:fldSimple")
    fld1.set(qn("w:instr"), "PAGE")
    r_in = OxmlElement("w:r")
    t_in = OxmlElement("w:t")
    t_in.text = "1"
    r_in.append(t_in)
    fld1.append(r_in)
    p._p.append(fld1)
    r2 = p.add_run(" 页 / 共 ")
    set_font(r2, BODY_FONT, 9, False, GRAY)
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    r_in2 = OxmlElement("w:r")
    t_in2 = OxmlElement("w:t")
    t_in2.text = "1"
    r_in2.append(t_in2)
    fld2.append(r_in2)
    p._p.append(fld2)
    r3 = p.add_run(" 页")
    set_font(r3, BODY_FONT, 9, False, GRAY)


# ================= 封面区 =================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(2)
r = p.add_run("《寻星——系外行星主题科普艺术展》")
set_font(r, HEAD_FONT, 20, True, DARK)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(6)
r = p.add_run("宣传片拍摄执行方案")
set_font(r, HEAD_FONT, 20, True, DARK)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(12)
r = p.add_run("v0.2 整理稿 ｜ 2026-10-19 ｜ 含 22 张现场素材原图索引")
set_font(r, HEAD_FONT, 11, False, GRAY)

# 信息提示条
info = doc.add_table(rows=1, cols=1)
info.alignment = WD_TABLE_ALIGNMENT.CENTER
info.autofit = False
info.style = "Table Grid"
cell_margins(info, top=80, bottom=80, left=140, right=140)
c = info.rows[0].cells[0]
c.width = Cm(USABLE)
shade(c, "F7F9FC")
p = c.paragraphs[0]
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("素材来源：")
set_font(r, HEAD_FONT, 9, True, RGBColor(0x2E, 0x5C, 0x8A))
r = p.add_run("领导提供的腾讯文档《这是领导让我拍星球展宣传片的初步思考方案…》中的初步方案、元宝对话记录，以及对话中导出的 22 张现场素材原图（已归档至「素材_元宝对话原图」）。")
set_font(r, BODY_FONT, 9, False, GRAY)
p.add_run().add_break()
r = p.add_run("当前状态：")
set_font(r, HEAD_FONT, 9, True, RGBColor(0x2E, 0x5C, 0x8A))
r = p.add_run("已完成素材归档与镜头映射；待补充成片时长、风格偏好、领导具体要求等信息后定稿。")
set_font(r, BODY_FONT, 9, False, GRAY)

# ================= 一、项目概况 =================
h1("项目概况", "一、")
rows = [
    ("展览名称", "寻星——系外行星主题科普艺术展（World-Seeking）"),
    ("展览性质", "2026 年全国科普月系列活动"),
    ("主办单位", "中央美术学院美术馆"),
    ("学术支持", "清华大学天文系"),
    ("展期", "2026 年 9 月 22 日—11 月 8 日"),
    ("展览地点", "中央美术学院美术馆 一层展厅（含四层楼顶吊顶装置区域）"),
    ("拍摄任务", "拍摄一支「种草」向宣传短片，用于展期传播与社交平台引流"),
    ("拍摄设备", "佳能 5D Mark IV + 24–105mm 镜头（沿用初步方案）"),
]
make_table(["项目", "内容"], rows, [3.2, 14.0], font_size=9.2, header_size=9.2)

h2("拍摄对象（已确认的四类重点）")
num_item(1, "进入展厅第一眼看到的展览主视觉与星球元素（美术馆入口/主视觉展板）。", bold_prefix="进门展示：")
num_item(2, "墙面星球展板、科普项目墙、时间线长墙、数据立柱、原理展板、温度数据亚克力展板等。", bold_prefix="展示墙：")
num_item(3, "展厅中部的彩色球体/悬挂式星球装置。", bold_prefix="中间装置：")
num_item(4, "美术馆四层楼顶不规则吊顶上的星球模型群与星云图案。", bold_prefix="四层楼顶：")

# ================= 二、B1-B9 =================
h1("基础依据：领导初步方案的 9 个镜头（B1–B9）", "二、")
p = para("原方案标题为《墙面星球展｜9 个视频镜头》，按墙面图像设计，现场布局为假想示意、并非实际展览照片，实拍时需按现场实际展墙校准。",
         size=9.5, color=GRAY, space_after=2)
p = para("核心原则：正面拍清楚，侧面拍空间，细节靠剪辑切换；每条素材拍 6–10 秒，固定镜头拍 8 秒。",
         size=9.5, color=GRAY, space_after=6)

rows = [
    ("B1", "105mm", "图像局部", "挑一处颜色，固定拍 8 秒", "局部质感、色彩细节"),
    ("B2", "24mm", "整面展墙", "站在入口，固定拍 8 秒", "交代空间与展墙全貌"),
    ("B3", "50mm", "单颗星球", "正对展板，圆形拍完整", "构图完整、比例准确"),
    ("B4", "35mm", "慢扫展墙", "身体站定，镜头慢慢转", "横向扫过一排展板"),
    ("B5", "70mm", "图像到展签", "从星球向下，慢慢俯仰", "由画面过渡到文字"),
    ("B6", "85mm", "说明文字", "拍清展签，核对信息", "信息准确、可做插入镜头"),
    ("B7", "85mm", "圆形匹配", "分拍两颗，圆心同位置", "便于剪辑对位与转场"),
    ("B8", "35mm", "看展背影", "人靠边，星球图像清楚", "增加人情味与代入感"),
    ("B9", "35mm", "展名收尾", "固定拍 8 秒，预留字幕", "片尾落版、预留文字位"),
]
make_table(["镜号", "焦距", "画面内容", "拍法 / 运镜", "备注"], rows,
           [1.3, 1.7, 3.2, 6.2, 4.8], font_size=8.8)
p = para("注意：B9 的「展名」需替换为实际展名「寻星——系外行星主题科普艺术展」；原示意图中的「星球科普展」为占位文字，不能直接使用。",
         size=9, color=GRAY, space_before=4, space_after=4)

# ================= 三、现场元素 =================
h1("现场元素与拍摄价值（已补充信息）", "三、")
rows = [
    ("1", "入口主视觉展板（正面/背面/玻璃门）",
     "正面含「2026 年全国科普月系列活动」「系外行星主题科普艺术展」「寻星 World-Seeking」「9.22—11.8」「中央美术学院美术馆一层展厅」；背面有清华大学天文系等联合标识、橙蓝渐变图形与彩色球体装置",
     "视频开篇定调，第一时间交代展名、时间、地点与打卡坐标", "No.03、20–22"),
    ("2", "悬挂式星球装置",
     "空中悬浮、色彩丰富、多层纵深，底部地面有反光",
     "空间纵深与沉浸氛围的核心镜头", "No.02、18、19"),
    ("3", "墙面星球展板",
     "按假想布局设计的整面星球图像墙（方案示意），现场以实际展墙为准",
     "B1–B9 基础镜头的主体对象", "No.01、No.12"),
    ("4", "科普项目墙",
     "「CHORUS」「觅音」「HWO」「天邻」4 个系外行星探索项目图文（01–04），下方配透明展柜",
     "体现科普厚度，可拍编号与标题细节", "No.04"),
    ("5", "时间线长墙",
     "2005、2008「望舒（HD 173416 b）」、2009（开普勒太空望远镜）、2018（TESS）、2022、2024、2026、「今天」等节点；含「热海星」「寒冷外侧超级地球」等主题与「科学家们用什么方法看见系外行星？」板块",
     "时间递进感、叙事线索", "No.05–12"),
    ("6", "数据立柱「系外行星有多重？」",
     "「2148 颗」大号数字 + 质量分布饼图",
     "数据型视觉亮点，适合特写与花字", "No.14"),
    ("7", "形成原理立柱「系外行星如何形成？」",
     "星云—原行星盘—行星系统线性演化流程图",
     "硬核科普的流程感镜头", "No.15"),
    ("8", "温度数据亚克力展板「系外行星的温度是多少？」",
     "「923 颗」统计 + 温度分布柱状图；右侧立柱悬挂蓝绿相间类地行星模型",
     "透明材质的叠加层次，画面辨识度高", "No.16"),
    ("9", "角落类木星条纹球体装置",
     "单颗条纹球体，背景可见「CAFAN STORE」礼品店标识与书籍陈列",
     "补充环境与商业配套信息，作为过渡镜头", "No.13"),
    ("10", "四层楼顶不规则吊顶",
     "悬挂多个类地/气态行星模型，浅色天花板绘白色星云，轨道射灯形成星芒高光",
     "仰拍全景，营造沉浸式宇宙氛围", "No.18、19"),
    ("11", "展厅长廊全景",
     "左侧时间线长墙，底部连续行星模型展示台，右侧白色立柱与橙红色悬挂模型，顶部射灯与地面反光",
     "收尾空间镜头，强调纵深与沉浸感", "No.17"),
]
make_table(["序号", "现场元素", "画面特点", "拍摄价值", "素材编号"], rows,
           [1.0, 3.8, 6.4, 3.6, 2.4], font_size=8.0)
p = para("素材归档：22 张原图已按编号整理至「素材_元宝对话原图」文件夹（No.01–22，另含三张素材总览图），文件名与内容一一对应，可直接对照现场与分镜使用。",
         size=9, color=GRAY, space_before=4, space_after=4)

# ================= 四、结构建议 =================
h1("成片结构建议（5 段式，30–60 秒可调）", "四、")
rows = [
    ("1 开篇·进门星球", "玻璃门外推进 / 主视觉展板特写", "入口主视觉、玻璃门、展板背面", "4–6 秒", "交代展名、展期、地点，建立第一印象"),
    ("2 氛围·仰望星空", "四层楼顶吊顶、悬挂星球群仰拍", "吊顶装置、单颗星球特写", "5–8 秒", "用空间感与光影营造「宇宙沉浸」"),
    ("3 主体·展示墙", "墙面星球、项目墙、时间线、数据立柱、原理/温度展板", "B1–B9 + 科普展板补充镜头", "12–20 秒", "呈现「科普 + 艺术」的内容厚度"),
    ("4 高潮·中间装置", "彩色球体装置环绕/特写", "中间装置、彩色球体、亚克力互动区", "4–6 秒", "视觉高潮，体现艺术与科学的碰撞"),
    ("5 收尾·长廊全景", "长廊横移或后退，落版信息", "长廊全景、展名收尾", "4–6 秒", "留下空间余韵，完成展名与展期落版"),
]
make_table(["段落", "内容", "镜头来源", "参考时长", "目的"], rows,
           [3.0, 4.6, 4.2, 1.9, 3.5], font_size=8.5)
p = para("若最终为 15 秒版本，可每个段落只保留 1 个最有代表性的镜头；若为 60 秒版本，可按「展示墙 → 数据细节 → 装置」的顺序在主体段落内部再分小节。",
         size=9, color=GRAY, space_before=4, space_after=4)

# ================= 五、分镜脚本 =================
h1("分镜脚本（可执行清单）", "五、")
p = para("「必拍」为成片骨架；「备选」视现场条件与时长取舍。焦距可按实际机身/镜头调整，运镜以现场走位为准。",
         size=9, color=GRAY, space_after=5)
rows = [
    ("S01", "开篇", "35mm", "玻璃门外向入口主视觉推进", "稳定器或滑轨 Dolly In / 平推", "4 秒", "玻璃反光与门外环境，注意避开自拍倒影"),
    ("S02", "开篇", "50mm", "「寻星 World-Seeking」主标题、展期、地点信息", "三脚架固定平拍", "3 秒", "文字必须清晰、水平"),
    ("S03", "开篇", "50/85mm", "展板背面联合标识、橙蓝渐变图形、彩色球体", "固定或轻微横移", "3 秒", "展板表面射灯高光"),
    ("S04", "氛围", "24mm", "四层楼顶不规则吊顶 + 星球模型群 + 星云图案", "低角度仰拍，缓慢上摇", "5 秒", "需确认可进入的高点/安全机位"),
    ("S05", "氛围", "105mm", "单颗条纹星球特写（B1 演变）", "三脚架固定，拍 8 秒", "8 秒（取 3–4 秒）", "长焦易抖，尽量上脚架"),
    ("S06", "主体", "24mm", "悬挂式星球装置整体（低角度）", "仰拍 + 缓慢推进/上摇", "4 秒", "地面反光、空间局促"),
    ("S07", "主体", "24mm", "整面展墙全貌（B2）", "入口固定拍 8 秒", "8 秒", "构图水平、边缘裁切"),
    ("S08", "主体", "50mm", "单颗星球正面（B3）", "正对固定", "6–8 秒", "圆形完整、比例不变形"),
    ("S09", "主体", "35mm", "慢扫展墙一排（B4）", "站定身体转动/滑轨横移", "8 秒", "匀速，起幅落幅各留 1 秒"),
    ("S10", "主体", "70mm", "星球图像 → 展签（B5）", "从星球向下缓慢俯仰", "6–8 秒", "对焦行程要稳，避免呼吸感"),
    ("S11", "主体", "85mm", "展签说明文字（B6）", "固定", "6 秒", "核对展签信息准确无误"),
    ("S12", "主体", "85mm", "圆形匹配：分拍两颗星球（B7）", "固定/微移，圆心同位置", "6 秒", "为后期对位转场准备"),
    ("S13", "主体", "35mm", "看展背影（B8）", "固定或轻跟随", "6–8 秒", "人物靠边，星球图像不被遮挡"),
    ("S14", "主体", "35mm", "展名收尾（B9，替换为「寻星」）", "固定 8 秒，预留字幕", "8 秒", "片尾落版文字区域留白"),
    ("S15", "主体", "35mm", "科普项目墙 01–04 与透明展柜", "横移或下摇", "8 秒", "射灯高光，避开反光角度"),
    ("S16", "主体", "35mm", "时间线长墙 2008 → 2026", "沿墙横移（Truck）", "8 秒", "射灯反光、文字清晰度"),
    ("S17", "主体", "85mm", "数据立柱「2148 颗」+ 质量饼图", "固定或缓慢下摇", "3–4 秒", "立柱表面反光"),
    ("S18", "主体", "85mm", "形成原理流程图（星云 → 行星系统）", "固定或缓慢平移", "3–4 秒", "平面反光、对焦准确"),
    ("S19", "主体", "85mm", "温度亚克力「923 颗」+ 柱状图", "低角度/侧移，必要时 CPL", "3–4 秒", "顶部射灯高光，透明材质易反光"),
    ("S20", "高潮", "35mm", "中间彩色球体装置", "环绕/横移", "4–6 秒", "观众干扰、展品安全距离"),
    ("S21", "收尾", "24mm", "长廊全景横移/后退", "Truck Shot 或 Dolly Out", "8 秒", "地面反光、保持水平"),
    ("S22", "备选", "50mm", "角落类木星条纹球体（CAFAN STORE 背景）", "固定或轻推", "4 秒", "环境杂乱，注意构图取舍"),
]
make_table(["镜号", "段落", "焦段", "画面内容", "拍法 / 运镜", "时长", "要点 / 风险"], rows,
           [1.0, 1.1, 1.3, 3.9, 4.1, 1.7, 3.1], font_size=8.0, header_size=8.4)

# ================= 六、技术要点 =================
h1("拍摄技术要点", "六、")
h2("1. 反光控制（本片最大难点）")
bullet("展板、玻璃门、亚克力、立柱表面均有射灯或环境高光：优先侧移机位找反射盲区，必要时压低机位。")
bullet("备偏振镜（CPL）用于玻璃与亚克力；黑色遮光板/遮光罩/黑旗用于压掉高光。")
bullet("入口玻璃门拍摄避开自拍倒影；可在门外侧向拍，减少正面反射。")
bullet("按素材编号核对重点反光面：No.03、20–22（玻璃与展板）、No.14–16（立柱与亚克力）、No.12/17（长墙射灯与地面反光）。")
h2("2. 光线与星芒")
bullet("顶部轨道射灯打在星球模型上的星芒可作为艺术光效保留，但避免直射镜头导致画面发灰。")
bullet("尽量固定白平衡，避免不同展区色温跳变；注意展陈灯光的显色性。")
h2("3. 稳定与运镜")
bullet("固定镜头（B1/B2/B9 类）必须上三脚架，保证 8 秒素材稳定可用。")
bullet("横移、推进优先使用滑轨/稳定器；手持运镜保持匀速，起幅落幅各留 1 秒余量。")
h2("4. 素材规格（建议，待与后期确认）")
bullet("常规镜头 4K/25p；需要慢动作的细节可补 1080p/50p 或 60p。")
bullet("每条素材 6–10 秒，固定镜头 8 秒；同一机位可多拍一条备用。")
h2("5. 构图原则")
bullet("正面拍清楚（文字、数据、展签），侧面拍空间（长廊、吊顶、装置纵深），细节靠剪辑切换。")
bullet("竖屏成片优先按 9:16 构图，同时保留 16:9 安全区以便横版复用（待确认平台后定）。")
h2("6. 声音")
bullet("若最终无旁白，建议现场录 1–2 分钟环境声（展厅底噪）供后期铺底；有旁白则预留录制时间。")

# ================= 七、现场执行清单 =================
h1("现场执行清单", "七、")
h2("器材")
for item in ["佳能 5D Mark IV 机身 + 24–105mm 镜头（备用电池、存储卡）",
             "三脚架、滑轨或稳定器",
             "偏振镜（CPL）、遮光罩、黑旗/黑卡",
             "补光/反光板（视现场光线）",
             "监视器/手机监看、场记表"]:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    r = p.add_run("☐  " + item)
    set_font(r, BODY_FONT, 10)

h2("人员与分工（待确认）")
for item in ["摄影师 / 摄影助理", "出镜人物（模特或馆方人员，待定）", "馆方对接人与场地许可"]:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    r = p.add_run("☐  " + item)
    set_font(r, BODY_FONT, 10)

h2("场地与许可")
for item in ["提前勘察动线：入口 → 四层楼顶吊顶 → 展墙 → 中间装置 → 长廊",
             "确认四层楼顶/吊顶区域可进入、可架机位，落实安全措施",
             "确认三脚架、滑轨、补光设备的使用许可",
             "选择开馆前或闭馆后时段拍摄，避开观众高峰"]:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    r = p.add_run("☐  " + item)
    set_font(r, BODY_FONT, 10)

h2("信息核对（拍摄前）")
for prefix, text in [("展名：", "寻星——系外行星主题科普艺术展（World-Seeking）"),
                     ("展期：", "2026.9.22—11.8"),
                     ("地点：", "中央美术学院美术馆一层展厅"),
                     ("主办：", "中央美术学院美术馆；学术支持：清华大学天文系"),
                     ("科普项目名：", "CHORUS、觅音、HWO、天邻"),
                     ("数据数字：", "2148 颗、923 颗等（以现场展板为准）")]:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    r = p.add_run("☐  ")
    set_font(r, BODY_FONT, 10)
    rb = p.add_run(prefix)
    set_font(rb, BODY_FONT, 10, True)
    rt = p.add_run(text)
    set_font(rt, BODY_FONT, 10)

# ================= 八、后期与交付 =================
h1("后期与交付", "八、")
bullet("大场景定调（进门/仰拍）→ 细节放大（装置/数据墙）→ 空间沉浸收尾（长廊）。", bold_prefix="剪辑结构：")
bullet("运动方向匹配、遮挡转场、圆形匹配（B7）对位转场。", bold_prefix="节奏与转场：")
bullet("轻快或氛围感音乐；可加「打卡坐标」「展期」等花字特效；片尾落版展名、展期、地点、主办与学术支持信息。", bold_prefix="BGM 与花字：")
bullet("主片 + 15 秒竖版 + 封面帧；字幕文件与素材备份（待确认）。", bold_prefix="交付版本：")

# ================= 九、待补充信息 =================
h1("待补充信息清单", "九、")
h2("成片层面")
for i, item in enumerate([
        "成片时长（15 秒 / 30 秒 / 60 秒）与画幅（竖屏 9:16 / 横屏 16:9）。",
        "发布平台（视频号、小红书、抖音、馆方公众号等）与投放场景。",
        "风格偏好（梦幻宇宙风 / 硬核科普风 / 轻松打卡风），是否有参考片。",
        "是否需要旁白、配乐风格、字幕（中/英）与花字规范。",
        "领导的具体要求、审片流程与最终交付时间。"], 1):
    num_item(i, item, size=9.5, spacing=1.15)

h2("拍摄层面")
for i, item in enumerate([
        "四层楼顶与不规则吊顶区域是否可以进入拍摄，机位与安全条件。",
        "中间装置的确切位置、可环绕空间与观众动线。",
        "展厅灯光是否可配合调整（射灯角度、开关控制）。",
        "是否安排人物出镜（模特/策展人/观众），是否需要肖像授权。",
        "拍摄日期与时段（开馆前/闭馆后），可用时长。",
        "是否需要馆方/校方 logo、片头片尾规范与素材使用授权。"], 6):
    num_item(i, item, size=9.5, spacing=1.15)

# ================= 十、附录：参考图与素材总览 =================
doc.add_page_break()
h1("附录：参考图与素材总览", "十、")
p = para("附图 1：领导初步方案《墙面星球展｜9 个视频镜头》（佳能 5D Mark IV + 24–105mm，按墙面图像设计，现场布局为假想示意）。",
         size=9, color=GRAY, space_before=2, space_after=4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.keep_with_next = True
doc.add_picture(os.path.join(os.path.dirname(OUT), "参考图_9镜头方案_B1-B9.jpg"), width=Cm(12.2))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

p = para("附图 2：现场素材总览 No.01–08（原图见「素材_元宝对话原图」文件夹，编号一一对应）。",
         size=9, color=GRAY, space_before=8, space_after=4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.keep_with_next = True
doc.add_picture(os.path.join(os.path.dirname(OUT), "素材_元宝对话原图", "_素材总览_01-08.jpg"), width=Cm(14.6))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

p = para("附图 3：现场素材总览 No.09–16。",
         size=9, color=GRAY, space_before=8, space_after=4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.keep_with_next = True
doc.add_picture(os.path.join(os.path.dirname(OUT), "素材_元宝对话原图", "_素材总览_09-16.jpg"), width=Cm(14.6))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

p = para("附图 4：现场素材总览 No.17–22。",
         size=9, color=GRAY, space_before=8, space_after=4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.keep_with_next = True
doc.add_picture(os.path.join(os.path.dirname(OUT), "素材_元宝对话原图", "_素材总览_17-22.jpg"), width=Cm(14.6))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

# ================= 十一、来源与备注 =================
h1("来源与备注", "十一、")
p = para("来源文档：腾讯文档《这是领导让我拍星球展宣传片的初步思考方案，接下来我会给你补充信息》（创建者：蔡浩文）。", size=9.5)
p = para("素材原图：元宝对话中的 22 张现场照片与方案图，已归档至「素材_元宝对话原图」文件夹（No.01–22），并附三张素材总览图。", size=9.5)
num_item(1, "原 9 镜头方案明确标注「假想画面，非实际展览照片」，现场需按实际展墙重新校准构图与机位。", size=9.5)
num_item(2, "B9 原图示例文字「星球科普展」为占位，实拍与后期须替换为「寻星——系外行星主题科普艺术展」。", size=9.5)
num_item(3, "本稿由 AI 助手根据上述文档内容整理，未到现场核实；标注「待确认」处需以现场与领导意见为准。", size=9.5)

add_page_number_footer()

# document properties
doc.core_properties.title = "《寻星——系外行星主题科普艺术展》宣传片拍摄执行方案 v0.2"
doc.core_properties.subject = "星球展宣传片拍摄方案整理"
doc.core_properties.author = "DSH 整理"
doc.core_properties.comments = "基于领导初步方案与现场补充信息整理"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print("saved:", OUT)
print("size:", os.path.getsize(OUT), "bytes")
