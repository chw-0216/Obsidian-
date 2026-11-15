# -*- coding: utf-8 -*-
"""
生成《在场与回应》井邻章 7 页（可编辑 PPT）
风格：暖纸色 #F6F2E9 / 炭黑 #202321 / 陶土红 #B5493A / 细线 #D8D2C4 / 克制字号
图片策略：pic_cover() 等比裁切填充，杜绝撑破版面；bias 控制裁切重心（人物照保头部）
"""
import os, glob
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree
from PIL import Image

PAPER = RGBColor(0xF6, 0xF2, 0xE9)
INK   = RGBColor(0x20, 0x23, 0x21)
RED   = RGBColor(0xB5, 0x49, 0x3A)
GREY  = RGBColor(0x6E, 0x6B, 0x64)
LINE  = RGBColor(0xD8, 0xD2, 0xC4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SANS = "微软雅黑"
SERIF = "宋体"

DESK = r"C:\Users\wardc\Desktop"
P_PPT  = os.path.join(DESK, r"中期汇报_2026-09\09_PPT用图")
P_SITE = os.path.join(DESK, r"中期汇报_2026-09\07_照片素材\03_工作站现场_导师记录")
P_RECV = os.path.join(DESK, r"中期汇报_2026-09\07_照片素材\01_工作站与领导接待")
P_HXR  = os.path.join(DESK, r"中期汇报_2026-09\07_照片素材\06_柚子柚_黄欣然记者_2026-07-29")
P_KEY  = os.path.join(DESK, r"05_井邻项目_视觉与丝网印刷\12秒丝网版画_9个关键帧_20260721")
P_S3   = os.path.join(DESK, r"中期汇报_2026-09\07_照片素材\06_区委书记到访_导师聊天_2026-08-22")

W, H = Inches(13.333), Inches(7.5)
M    = Inches(0.72)
CW   = W - 2 * M
RX   = M + Inches(7.62)     # 右栏起点 = 8.34"
RW   = CW - Inches(7.62)    # 右栏宽  = 4.273"
FOOT = H - Inches(0.56)     # 页脚基线 6.94"


def find(folder, prefix):
    hits = sorted(glob.glob(os.path.join(folder, prefix + "*")))
    return hits[0] if hits else None


def set_ea(run, name):
    rPr = run._r.get_or_add_rPr()
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    for tag in ('ea', 'cs'):
        el = rPr.find(ns + tag)
        if el is None:
            el = etree.SubElement(rPr, ns + tag)
        el.set('typeface', name)


def rect(slide, l, t, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, l, t, w, h)
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(lw)
    s.shadow.inherit = False
    return s


def text(slide, l, t, w, h, items, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """items: list of (str, size, bold, color, font, space_after_pt)"""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    first = True
    for it in items:
        s, size, bold, color, fname = it[0], it[1], it[2], it[3], it[4]
        sa = it[5] if len(it) > 5 else 4
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(sa)
        p.line_spacing = 1.28
        r = p.add_run(); r.text = s
        r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = fname
        set_ea(r, fname)
    return tb


def pic_cover(slide, path, l, t, w, h, bias=0.5):
    """等比裁切填充：图片铺满 (l,t,w,h)，多余部分裁掉。bias = 从上方裁掉的比例（0.5 居中）"""
    if not path or not os.path.exists(path):
        print("  [MISS]", path)
        return None
    iw, ih = Image.open(path).size
    box_r, img_r = w / h, iw / ih
    pic = slide.shapes.add_picture(path, l, t, width=w, height=h)
    if img_r > box_r:                       # 图更宽 → 裁左右
        keep = box_r / img_r
        c = (1 - keep) / 2
        pic.crop_left = c; pic.crop_right = c
    elif img_r < box_r:                     # 图更高 → 裁上下
        keep = img_r / box_r
        excess = 1 - keep
        pic.crop_top = excess * bias
        pic.crop_bottom = excess * (1 - bias)
    return pic


def caption(slide, l, t, w, txt, size=9.5):
    text(slide, l, t, w, Inches(0.26),
         [(txt, size, False, GREY, SANS, 0)])


def base(prs, tag, title, judge, page_no, note):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, W, H, fill=PAPER)
    text(s, M, Inches(0.46), CW, Inches(0.3), [(tag, 11.5, True, RED, SANS, 2)])
    text(s, M, Inches(0.78), CW, Inches(0.62), [(title, 25, True, INK, SANS, 4)])
    text(s, M, Inches(1.44), CW, Inches(0.42), [(judge, 13.5, False, RED, SANS, 0)])
    rect(s, M, Inches(2.00), CW, Pt(0.75), fill=LINE)
    text(s, M, FOOT, Inches(9.0), Inches(0.3),
         [("中期汇报 · 在场与回应 ｜ 蔡浩文 · 12250300012", 9.5, False, GREY, SANS, 0)])
    text(s, W - M - Inches(1.0), FOOT, Inches(1.0), Inches(0.3),
         [(f"{page_no:02d}", 9.5, True, RED, SANS, 0)], align=PP_ALIGN.RIGHT)
    if note:
        s.notes_slide.notes_text_frame.text = note
    return s


def card(slide, l, t, w, h, title, lines, accent=RED, fs=10.5):
    rect(slide, l, t, w, h, fill=WHITE, line=LINE)
    rect(slide, l, t, Pt(2.2), h, fill=accent)
    text(slide, l + Inches(0.18), t + Inches(0.13), w - Inches(0.32), Inches(0.3),
         [(title, 12.5, True, accent, SANS, 3)])
    body = [(x, fs, False, INK, SANS, 3) for x in lines]
    text(slide, l + Inches(0.18), t + Inches(0.46), w - Inches(0.32), h - Inches(0.6), body)


def table(slide, l, t, w, h, data, col_w=None, fs=10, head_fs=10):
    rows, cols = len(data), len(data[0])
    gf = slide.shapes.add_table(rows, cols, l, t, w, h)
    tbl = gf.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Emu(int(w * cw / total))
    for ri, row in enumerate(data):
        tbl.rows[ri].height = Inches(0.30)
        for ci, val in enumerate(row):
            c = tbl.cell(ri, ci)
            c.margin_left = c.margin_right = Inches(0.06)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if ri else RGBColor(0xEC, 0xE6, 0xD8)
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.line_spacing = 1.12
            r = p.add_run(); r.text = str(val)
            r.font.size = Pt(head_fs if ri == 0 else fs)
            r.font.bold = (ri == 0)
            r.font.color.rgb = INK
            r.font.name = SANS
            set_ea(r, SANS)
    return tbl


prs = Presentation()
prs.slide_width, prs.slide_height = W, H

# ═══════════════════════ 第 1 页 · 从授课到建场 ═══════════════════════
s = base(prs, "02 井邻 · 工作站承担什么任务", "从授课到建场",
         "澜沧是一段集中的学校课程；井邻是一个必须有人持续建设、维护和回应的村庄工作站。", 1,
         "与澜沧集中开展的课程不同，井邻要求持续维护空间、材料与协作关系。我的驻村工作记录覆盖三十三个工作日，"
         "其中三十二天的工作人员栏只有我一个人。现场在洞台村78号，我承担从桌台水池、导轨射灯、空调显示屏等基础条件准备，"
         "到制版印制、布展讲解与日常运营的全过程工作。澜沧是一段集中的学校课程，而井邻是一个必须有人持续建造、维护和回应的村庄工作站。")

pic_cover(s, find(P_PPT, "03_书记到访_印制台全景"), M, Inches(2.24), Inches(7.30), Inches(4.10))
caption(s, M, Inches(6.40), Inches(7.30),
        "洞台村 78 号工作站室内全景：丝网印制台、展墙与工作区（区委书记到访时拍摄）")

card(s, RX, Inches(2.24), RW, Inches(1.60), "地点与服务对象",
     ["北京市怀柔区渤海镇洞台村 78 号",
      "响水湖长城脚下 · 京承高速宽沟站出口",
      "对象：村民 · 井邻客人 · 预约访客 · 各级参访者"])
card(s, RX, Inches(3.94), RW, Inches(1.60), "我的角色",
     ["丝网印刷 / 版画工作坊负责人",
      "工作站现场执行",
      "项目由陈晔老师推动（学术主理人）"])
rect(s, RX, Inches(5.64), RW, Inches(0.70), fill=WHITE, line=LINE)
rect(s, RX, Inches(5.64), Pt(2.2), Inches(0.70), fill=RED)
text(s, RX + Inches(0.18), Inches(5.74), RW - Inches(0.32), Inches(0.3),
     [("驻村记录 33 个工作日", 12, True, RED, SANS, 2)])
text(s, RX + Inches(0.18), Inches(6.04), RW - Inches(0.32), Inches(0.3),
     [("其中 32 天工作人员栏只有我一人", 9.5, False, GREY, SANS, 0)])

# ═══════════════════════ 第 2 页 · 让变化看得见 ═══════════════════════
s = base(prs, "02 井邻 · 工作站怎样具备使用条件", "让变化看得见",
         "空间只有具备可用条件，美育活动才能真正落地 —— 这一页只写我负责过的具体判断。", 2,
         "第2页让变化看得见。左图是7月25日的施工状态，我在现场拉线定位、确定射灯与显示屏的安装位；"
         "右图是同一天完工后空间已在使用，四位来客在印制台前挑选与操作。"
         "我提出画作悬挂的两套方案并论证：画框较重，画轨承重不足，建议打孔悬挂。"
         "空间只有具备了可用条件，美育活动才能真正落地。")

g2 = Inches(0.18)
w2 = (CW - 3 * g2) / 4
iw = (CW - Inches(0.18)) / 2
pic_cover(s, find(P_SITE, "20260725_工作站现场_107"), M, Inches(2.24), iw, Inches(3.23))
pic_cover(s, find(P_SITE, "20260725_工作站现场_101"), M + iw + Inches(0.18),
          Inches(2.24), iw, Inches(3.23), bias=0.45)
caption(s, M, Inches(5.52), iw, "施工过程 · 2026.07.25　现场拉线定位，确定射灯与显示屏安装位")
caption(s, M + iw + Inches(0.18), Inches(5.52), iw, "完工使用 · 2026.07.25　同一空间已投入印制与接待")

conds = ["操作台：2.7×1.5m 乒乓球桌改造", "石槽水池砌筑 + 排污上下水", "二线导轨射灯 ×4 根 2m",
         "34 寸曲面屏壁挂 + 电视壁挂", "路由器 + 小米盒子全屏投屏", "画作打孔悬挂（否掉画轨方案）",
         "腾讯 / 高德 / 百度 地图登记", "工作站物料费用记账台账"]
for i, c in enumerate(conds):
    r, cc = divmod(i, 4)
    x = M + cc * (w2 + g2)
    y = Inches(5.88) + r * Inches(0.40)
    rect(s, x, y, w2, Inches(0.36), fill=WHITE, line=LINE)
    rect(s, x, y, Pt(1.8), Inches(0.36), fill=INK)
    text(s, x + Inches(0.12), y + Inches(0.07), w2 - Inches(0.2), Inches(0.24),
         [(c, 9, False, INK, SANS, 0)])

# ═══════════════════════ 第 3 页 · 一次工作坊怎样发生 ═══════════════════════
s = base(prs, "02 井邻 · 一次工作坊怎样发生", "参与发生在每一个可选择的节点",
         "「怎么走进来 — 在哪里作选择 — 我怎样示范 — 得到什么图像」，比排列十张热闹活动照更能解释参与式艺术。", 3,
         "在工作坊里，我关注参与者在哪一步能够作选择，在哪一步需要帮助。参与者走进来后，先在展区挑选自己喜欢的图案，"
         "随后我示范如何握刮板、保持倾角匀速推印，最后亲手揭版晾干。"
         "参与式艺术的核心，就是把技法转化为每个人都可以亲身经验的创作闭环。")

steps = [("01", "走入现场", "村口海报 · 三平台地图定位 · 门头指引，降低寻访与心理进入门槛"),
         ("02", "挑选图案", "在展区浏览四色分版方案，结合微信扫码 MBTI 生成个性化图形"),
         ("03", "示范推印", "操作台前指导握刮板角度、均墨力度与网版套位，带领亲手刮印"),
         ("04", "带走作品", "亲手揭版、风干固色，在专属标签处签名，成为带得走的乡村记忆")]
for i, (no, ttl, desc) in enumerate(steps):
    y = Inches(2.24) + Inches(0.86) * i
    rect(s, M, y, Inches(6.60), Inches(0.74), fill=WHITE, line=LINE)
    text(s, M + Inches(0.14), y + Inches(0.06), Inches(0.6), Inches(0.3),
         [(no, 15, True, RED, SANS, 0)])
    text(s, M + Inches(0.78), y + Inches(0.05), Inches(5.6), Inches(0.28),
         [(ttl, 12, True, INK, SANS, 1)])
    text(s, M + Inches(0.78), y + Inches(0.32), Inches(5.6), Inches(0.36),
         [(desc, 9.5, False, GREY, SANS, 0)])

pic_cover(s, find(P_KEY, "05_5s_刮板推印"), RX, Inches(2.24), RW, Inches(1.90))
pic_cover(s, find(P_HXR, "20260729_我与领导一起印制"), RX, Inches(4.24), RW, Inches(1.90), bias=0.40)
text(s, RX, Inches(6.18), RW, Inches(0.5),
     [("上：12 秒丝网动画关键帧 · 刮板推印", 9, False, GREY, SANS, 1),
      ("下：与来访领导共同印制（黄欣然摄 · 2026.07.29）", 9, False, GREY, SANS, 0)])

# ═══════════════════════ 第 4 页 · 两次开街与参与入口 ═══════════════════════
s = base(prs, "02 井邻 · 两次开街与参与入口", "定价不是商业牟利，是组织参与的一部分",
         "价格机制是为了平衡公益普及与工作站长期维持的材料成本 —— 它决定谁能走进来。", 4,
         "定价也是组织参与的一部分。我设置了村民免费、井邻客人五十八元、预约六十八元的入口。"
         "结合经济学背景，分析不同对象的进入条件、时间成本和材料支出。开街检验了工作站接受不同来访者的能力。"
         "价格机制不是商业牟利，而是为了平衡公益普及与工作站长期维持的材料成本。")

tiers = [("村民", "免费参与", "消除本土村民的经济门槛，鼓励老人与青少年常态化进入，让工作站融入洞台村日常生活"),
         ("井邻客人", "58 元体验", "与周边精品民宿及动漫谷园区客群协同，40 分钟丝网印制体验，含单色/双色手提袋与全套材料"),
         ("预约访客", "68 元定制", "面向专程造访的研学与艺术爱好者，覆盖特种纸张、多套色网版耗损、环保水性油墨与一对一指导")]
for i, (who, price, desc) in enumerate(tiers):
    y = Inches(2.24) + Inches(1.24) * i
    rect(s, M, y, Inches(6.60), Inches(1.12), fill=WHITE, line=LINE)
    rect(s, M, y, Pt(2.2), Inches(1.12), fill=RED)
    text(s, M + Inches(0.20), y + Inches(0.12), Inches(2.0), Inches(0.32),
         [(who, 13, True, INK, SANS, 0)])
    text(s, M + Inches(0.20), y + Inches(0.52), Inches(2.0), Inches(0.3),
         [(price, 12, True, RED, SANS, 0)])
    text(s, M + Inches(2.35), y + Inches(0.16), Inches(4.05), Inches(0.86),
         [(desc, 9.5, False, GREY, SANS, 0)])

pic_cover(s, find(P_PPT, "42_开街_活动3"), RX, Inches(2.24), RW, Inches(2.40))
caption(s, RX, Inches(4.68), RW, "长城国际动漫谷开街现场 · 2026.08.02")
milestones = [("07-11", "首印", "工作站首次对外印制，确立四色分版主视觉"),
              ("08-02", "试运营", "动漫谷开街同日试运营；突遇暴雨，我全程坚守维护物料"),
              ("09-20", "正式开街", "形成村民免费 / 井邻客人 58 元 / 预约 68 元三档入口")]
for i, (d, ttl, desc) in enumerate(milestones):
    y = Inches(5.02) + Inches(0.54) * i
    rect(s, RX, y, RW, Inches(0.48), fill=WHITE, line=LINE)
    rect(s, RX, y, Pt(1.8), Inches(0.48), fill=RED)
    text(s, RX + Inches(0.12), y + Inches(0.05), Inches(0.75), Inches(0.24),
         [(d, 10, True, RED, SANS, 0)])
    text(s, RX + Inches(0.90), y + Inches(0.04), Inches(1.0), Inches(0.22),
         [(ttl, 10, True, INK, SANS, 0)])
    text(s, RX + Inches(0.90), y + Inches(0.25), RW - Inches(1.05), Inches(0.22),
         [(desc, 8.5, False, GREY, SANS, 0)])

# ═══════════════════════ 第 5 页 · 多批接待与沟通 ═══════════════════════
s = base(prs, "02 井邻 · 多批接待与沟通", "八批对接是高密度常态劳动，不是合影",
         "六批现场对接，两批为前置准备与材料支持 —— 每一次都有前夜借版、制版、调墨与现场讲解。", 5,
         "接待工作让我反复向不同对象解释项目。现有记录中共有八批相关接待与支持，其中六批是现场对接，"
         "两批是前置准备与材料支持。我承担了从前夜借版、制版、调墨，到现场讲解、技术示范和会后整理的完整链条。"
         "面对区领导、组织部门、科学家外宾等不同群体，我练习用准确的语言阐述美育理念。")

data = [["日期", "到访", "我做了什么"],
        ["07-29", "区政协主席 · 区委宣传部部长", "带领导上版印制；现场讲解；作品赠予沟通"],
        ["07-29", "北京日报记者 + 镇宣传干事", "现场接待与记录；会后核对来访信息"],
        ["07-31", "怀柔区委组织部", "现场接待；同日跟进空调安装、处理住户异议"],
        ["08-02", "长城国际动漫谷开街领导", "当日驻站值守；暴雨坚守；借钥匙取网版材料"],
        ["08-03", "未来科学城领导（筹备）", "撰写并提交丝网印刷工作坊专项介绍材料"],
        ["08-15", "怀柔区委书记", "提前借版重新制版；现场拍摄记录"],
        ["08-16", "世界科学家团队（外宾）", "主动自荐 → 现场英文介绍与实操展示"],
        ["08-20", "梁区长 + 北京市文旅局局长", "借版制版 / 现场调网 / 讲解示范 / 展陈固定"]]
table(s, M, Inches(2.24), CW, Inches(2.94), data, col_w=[1.0, 4.0, 6.0], fs=10, head_fs=10.5)

strip = [(find(P_SITE, "20260729_工作站现场_092"), "07-29　区政协主席 · 宣传部部长"),
         (find(P_SITE, "20260729_工作站现场_091"), "07-29　北京日报记者 · 镇宣传干事"),
         (find(P_SITE, "20260731_工作站现场_075"), "07-31　怀柔区委组织部"),
         (find(P_S3, "20260822_区委书记到访_站内听取介绍"), "08-15　怀柔区委书记")]
for i, (p, lab) in enumerate(strip):
    x = M + i * (w2 + g2)
    pic_cover(s, p, x, Inches(5.32), w2, Inches(1.32), bias=0.42)
    rect(s, x, Inches(6.34), w2, Inches(0.30), fill=INK)
    text(s, x + Inches(0.10), Inches(6.39), w2 - Inches(0.18), Inches(0.22),
         [(lab, 8.5, False, WHITE, SANS, 0)])

# ═══════════════════════ 第 6 页 · 一次现场工作的细节 ═══════════════════════
s = base(prs, "02 井邻 · 一次现场工作的细节", "把领导关切转化为当天的具体行动",
         "2026 年 8 月 20 日 · 怀柔区梁区长与北京市文旅局局长到站视察 —— 我的一天。", 6,
         "选一批讲深：8月20日梁区长与市文旅局局长到访。我在前一天傍晚主动请缨，当晚借版制版；"
         "当天早上六点五十九分出发，途中发生车辆剐蹭仍安全抵达。领导重点询问了常态化运营与村民参与度。"
         "当天下午，按导师与现场反馈加固展陈固定、借笔记本调试无线网络，并巩固村民常态化免费参与机制。"
         "右上图是我当天提交的文化墙主视觉诗句木刻方案实物。只有把领导关切转化为具体行动，对接才有实质意义。")

timeline = [("8/19 18:41", "我主动请缨", "「领导来了版画/丝网这块我能讲清楚。今晚要不要先去把版制了，明天直接用」"),
            ("8/19 晚", "借取网版并完成制版准备", "为次日现场印制做好物料与网版准备"),
            ("8/20 06:59", "出发（途中车辆剐蹭）", "仍安全抵达；08:49 到达工作站"),
            ("8/20 10:23", "提交文化墙主视觉诗句方案", "6 句备选：燕山脚下书声朗 / 长城脚下墨花香 / 怀柔山乡入画图 / 栗林深处翰墨香 / 京韵满乡书意浓 / 雁栖河畔童心画"),
            ("8/20 现场", "调网 · 互动 · 收口", "借笔记本调试无线网络；与村民互动开展美育；对接关总完成展品上墙固定"),
            ("8/20 14:56", "把体验者转为线上关注", "导师要求「来体验的人不能白体验，让他们关注我们的小红书」→ 现场引导体验群众关注工作站账号")]
for i, (tm, ttl, desc) in enumerate(timeline):
    y = Inches(2.26) + Inches(0.74) * i
    rect(s, M, y, Inches(8.05), Inches(0.64), fill=WHITE, line=LINE)
    text(s, M + Inches(0.16), y + Inches(0.17), Inches(1.15), Inches(0.3),
         [(tm, 10.5, True, RED, SANS, 0)])
    text(s, M + Inches(1.40), y + Inches(0.06), Inches(6.45), Inches(0.28),
         [(ttl, 11, True, INK, SANS, 0)])
    text(s, M + Inches(1.40), y + Inches(0.31), Inches(6.45), Inches(0.32),
         [(desc, 8.5, False, GREY, SANS, 0)])

pic_cover(s, find(P_SITE, "20260820_工作站现场_036"), RX, Inches(2.24), RW, Inches(3.20))
caption(s, RX, Inches(5.48), RW, "8/20 10:23 提交的文化墙主视觉诗句方案（木刻实物）")
card(s, RX, Inches(5.76), RW, Inches(1.00), "领导核心关切 → 当日行动",
     ["关切：工作站能否常态化运营、村民能否随时进来印",
      "行动：借笔记本调无线网 / 展品上墙固定 / 引导体验群众关注小红书"],
     accent=INK, fs=8.5)

# ═══════════════════════ 第 7 页 · 33 天记录与问题跟进 ═══════════════════════
s = base(prs, "02 井邻 · 33 天的记录与问题跟进", "日志把「忙碌」变成可检查、可闭环的行动",
         "8 项台账问题：7 项已解决，1 项持续跟进（记录时点截至 2026-08-20）。", 7,
         "日志把忙碌变成可检查的行动。现有八项问题中七项已解决，一项持续跟进。"
         "比如空调问题，从7月8日发现管道被拔，到房东顾虑外墙美观、邻居阻拦，经过大半个月的多方协调重新排布管线，"
         "最终在7月31日恢复制冷；收纳柜调出受阻，我直奔村大队协调闲置资产。"
         "这两个案例说明我如何面对真实的乡村社会关系，把突发的阻碍转化为切实可用的空间条件。"
         "澜沧让我看到课堂内的选择，井邻让我看到持续参与取决于空间、维护与协作。")

cases = [("案例一 · 空调不制冷（7/8 → 7/31）",
          ["7/8 发现管道被拔、不制冷 → 7/10 跟进外机安装",
           "7/27–7/29 与关总、房东（曹委员）多方协调管道方案",
           "7/31 安装完成、试机制冷正常 → 8/1 向王总汇报闭环"]),
         ("案例二 · 收纳柜调配（7/28 → 7/31）",
          ["7/28 赴卫生站协调，柜子归邮局在账、未能调出",
           "7/29 赴村大队挑选闲置柜子",
           "7/31 村支书提供柜子，申请两人协助搬入工作站"])]
for i, (ttl, lines) in enumerate(cases):
    card(s, M, Inches(2.26) + Inches(1.72) * i, Inches(6.20), Inches(1.56), ttl, lines, accent=INK)

data2 = [["#", "问题", "状态"],
         ["1", "导轨安装（7/7 完成）", "已解决"],
         ["2", "空调不制冷、管道被拔（7/31）", "已解决"],
         ["3", "显示屏更换与安装位（7/25）", "已解决"],
         ["4", "显示屏角部裂痕换新（7/19）", "已解决"],
         ["5", "立面墙插座缺配电箱钥匙", "跟进中"],
         ["6", "房东顾虑不愿打洞（7/29 调整管线）", "已解决"],
         ["7", "卫生站柜子调出受阻（7/31 大队借柜）", "已解决"],
         ["8", "隔壁住户反对空调外机（7/31 协调收口）", "已解决"]]
table(s, RX, Inches(2.26), RW, Inches(3.10), data2, col_w=[0.5, 5.2, 1.4], fs=9.5, head_fs=10)
text(s, RX, Inches(5.44), RW, Inches(0.3),
     [("摘自《洞台村乡村美育工作站 · 驻村工作日志》（蔡浩文记录）", 8.5, False, GREY, SANS, 0)])

stats = [("33", "个工作日", "驻村工作日志覆盖天数"),
         ("8", "项台账问题", "空调 / 显示屏 / 导轨 / 柜子 / 插座 / 邻里"),
         ("7 / 8", "已解决", "1 项持续跟进（记录时点 2026-08-20）")]
sw = (CW - Inches(0.36)) / 3
for i, (num, unit, desc) in enumerate(stats):
    x = M + i * (sw + Inches(0.18))
    rect(s, x, Inches(5.80), sw, Inches(0.80), fill=WHITE, line=LINE)
    rect(s, x, Inches(5.80), Pt(2.2), Inches(0.80), fill=RED)
    text(s, x + Inches(0.18), Inches(5.90), Inches(1.5), Inches(0.4),
         [(num, 20, True, RED, SANS, 0)])
    text(s, x + Inches(1.30), Inches(5.92), sw - Inches(1.45), Inches(0.3),
         [(unit, 11, True, INK, SANS, 2)])
    text(s, x + Inches(1.30), Inches(6.20), sw - Inches(1.45), Inches(0.3),
         [(desc, 8.5, False, GREY, SANS, 0)])

out = os.path.join(r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21",
                   "井邻章_7页_可编辑_2026-10-06.pptx")
prs.save(out)
print("SAVED:", out)
print("页数:", len(prs.slides._sldIdLst))
