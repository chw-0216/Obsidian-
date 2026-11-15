# -*- coding: utf-8 -*-
"""生成《Codex 双账号并行方案｜审慎修订版 v2》汇报 PPT。
内容以用户提供的 v2 修订版正文为准，补入本会话已核实的本机实测证据。
只写 PPT 文件，不改动任何源素材。
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import copy, sys

OUT = r"C:\Users\wardc\Desktop\Codex双账号并行方案_审慎修订版v2.pptx"

FONT = "Microsoft YaHei"
INK   = RGBColor(0x1A, 0x1D, 0x21)
BODY  = RGBColor(0x2C, 0x32, 0x3A)
MUTED = RGBColor(0x6B, 0x74, 0x80)
NAVY  = RGBColor(0x12, 0x1A, 0x2B)
BLUE  = RGBColor(0x2F, 0x6F, 0xED)
BLUE_D= RGBColor(0x1B, 0x4C, 0xB8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CARD  = RGBColor(0xF5, 0xF7, 0xFA)
CARD2 = RGBColor(0xEE, 0xF3, 0xFC)
LINE  = RGBColor(0xD8, 0xDE, 0xE8)
WARN_C= RGBColor(0x9A, 0x3B, 0x12)
WARN_B= RGBColor(0xFD, 0xF3, 0xEC)
OK_C  = RGBColor(0x14, 0x60, 0x4B)
OK_B  = RGBColor(0xEC, 0xF7, 0xF2)

SW, SH = 13.333, 7.5
M = 0.75
CW = SW - 2 * M
_DEBUG = "--debug" in sys.argv

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]


# ---------- 基础绘制工具 ----------
def rect(sl, x, y, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=None):
    s = sl.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(lw)
    s.shadow.inherit = False
    if adj is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = adj
        except Exception:
            pass
    return s


def tbox(sl, x, y, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf


def para(tf, first=False, align=PP_ALIGN.LEFT, space_before=0, space_after=0, line=1.22):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    p.line_spacing = line
    return p


def run(p, text, size=10, bold=False, color=BODY, italic=False):
    if not isinstance(size, (int, float)):
        size = 10
    size = max(6.0, min(48.0, float(size)))
    if not isinstance(color, RGBColor):
        color = BODY
    r = p.add_run(); r.text = str(text)
    if _DEBUG and len(str(text)) > 6:
        sys.stderr.write("RUN_IN len=%d repr=%r\n" % (len(str(text)), str(text)[:60]))
    f = r.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bool(bold)
    if italic:
        f.italic = True
    f.italic = italic
    f.color.rgb = color
    # 中文字体（east asian）显式设置
    rPr = r._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}" + tag.split(":")[1])
        if el is None:
            from lxml import etree
            el = etree.SubElement(rPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}" + tag.split(":")[1])
        el.set("typeface", FONT)
    return r


def slide_base(idx, kicker, title, subtitle=None):
    sl = prs.slides.add_slide(BLANK)
    rect(sl, 0, 0, SW, 0.155, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    rect(sl, 0, 0, 4.3, 0.155, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)

    tf = tbox(sl, M, 0.46, CW - 1.6, 0.3)
    p = para(tf, first=True)
    run(p, kicker, size=9.5, bold=True, color=BLUE)

    tf = tbox(sl, M, 0.76, CW - 1.2, 0.5)
    p = para(tf, first=True)
    run(p, title, size=21, bold=True, color=INK)

    y = 1.34
    if subtitle:
        tf = tbox(sl, M, y, CW - 1.2, 0.3)
        p = para(tf, first=True, line=1.15)
        run(p, subtitle, size=10.5, color=MUTED)
        y += 0.34
    rect(sl, M, y, CW, 0.018, fill=LINE, shape=MSO_SHAPE.RECTANGLE)
    y += 0.2

    # 页脚
    tf = tbox(sl, M, SH - 0.46, CW - 0.8, 0.26)
    p = para(tf, first=True)
    run(p, "Codex 双账号并行方案｜审慎修订版 v2 ｜ 2026-10-12 ｜ 结论：桌面 A + 独立 CLI B 双入口",
        size=8, color=MUTED)
    tf = tbox(sl, SW - M - 0.8, SH - 0.46, 0.8, 0.26, align=PP_ALIGN.RIGHT)
    p = para(tf, first=True, align=PP_ALIGN.RIGHT)
    run(p, "%02d" % idx, size=9, bold=True, color=MUTED)
    return sl, y


def alloc(avail, weights, gap=0.2, minh=0.85):
    n = len(weights)
    total_gap = gap * (n - 1)
    rest = avail - total_gap
    tw = float(sum(weights))
    hs = [max(minh, rest * w / tw) for w in weights]
    over = sum(hs) - rest
    if over > 0:
        hs[-1] = max(minh, hs[-1] - over)
    return hs


def cards(sl, y0, y1, items, cols=None, gap=0.2, weights=None):
    """items: [{'title','lines','tone'}]  lines: [(text, bold, size, color|None)]"""
    n = len(items)
    cols = cols or n
    rows = (n + cols - 1) // cols
    if weights is None:
        weights = [1] * rows
    hs = alloc(y1 - y0, weights, gap=gap)
    cw = (CW - gap * (cols - 1)) / cols
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x = M + c * (cw + gap)
        y = y0 + sum(hs[:r]) + gap * r if False else y0 + (sum(hs[:r]) + gap * r)
        h = hs[r]
        tone = it.get("tone", "plain")
        fill = {"plain": CARD, "blue": CARD2, "warn": WARN_B, "ok": OK_B}.get(tone, CARD)
        acc = {"plain": BLUE, "blue": BLUE, "warn": RGBColor(0xD9, 0x6B, 0x2B), "ok": RGBColor(0x1E, 0x8A, 0x6B)}.get(tone, BLUE)
        rect(sl, x, y, cw, h, fill=fill, adj=0.045)
        rect(sl, x, y, 0.055, h, fill=acc, shape=MSO_SHAPE.RECTANGLE)
        pad = 0.17
        tf = tbox(sl, x + pad, y + 0.13, cw - 2 * pad, h - 0.26)
        first = True
        if it.get("title"):
            p = para(tf, first=True, line=1.05)
            run(p, it["title"], size=12, bold=True, color=INK if tone == "plain" else (WARN_C if tone == "warn" else (OK_C if tone == "ok" else BLUE_D)))
            first = False
        for ln in it["lines"]:
            # 兼容：字符串行 或 (text, bold, size, color) 元组行
            if isinstance(ln, str):
                ln = (ln,)
            text = ln[0]
            bold = ln[1] if len(ln) > 1 else False
            size = ln[2] if len(ln) > 2 else 10
            color = ln[3] if len(ln) > 3 else BODY
            p = para(tf, first=first, space_before=(3.5 if not first else 5.5), line=1.2)
            first = False
            if text.startswith("• "):
                # 单 run 合并渲染：避免 bullet run + text run 的渲染丢失
                run(p, "•   " + text[2:], size=size, bold=bold, color=color)
            else:
                run(p, text, size=size, bold=bold, color=color)
            if _DEBUG:
                sys.stderr.write("DBG_CARD key=%r textlen=%d runs=%d joined=%r\n"
                                 % (it.get("title"), len(text), len(p.runs),
                                    "".join(x.text for x in p.runs)))
    return hs


def callout(sl, x, y, w, h, title, text, tone="blue", size=10.5):
    fill = {"blue": CARD2, "warn": WARN_B, "ok": OK_B}.get(tone, CARD2)
    acc = {"blue": BLUE, "warn": RGBColor(0xD9, 0x6B, 0x2B), "ok": RGBColor(0x1E, 0x8A, 0x6B)}.get(tone, BLUE)
    tc = {"blue": BLUE_D, "warn": WARN_C, "ok": OK_C}.get(tone, BLUE_D)
    rect(sl, x, y, w, h, fill=fill, adj=0.06)
    rect(sl, x, y, 0.06, h, fill=acc, shape=MSO_SHAPE.RECTANGLE)
    tf = tbox(sl, x + 0.2, y + 0.13, w - 0.4, h - 0.26)
    p = para(tf, first=True, line=1.05)
    run(p, title, size=11, bold=True, color=tc)
    p = para(tf, space_before=4.5, line=1.2)
    run(p, text, size=size, color=BODY)


# ---------------- 内容 ----------------
S = []

# 1 封面
S.append({"kind": "cover"})

# 2 需求拆解
S.append({
    "kicker": "01｜结论先行",
    "title": "你的需求应拆成三件独立的事",
    "subtitle": "三件事的风险与验收标准完全不同，不要指望一次操作同时解决。",
    "cards": [
        {"title": "① 两个账号各自登录", "tone": "blue", "lines": [
            "•  各自使用自己的订阅权益",
            "•  关键是「正规独立授权」，不是复制凭据",
        ]},
        {"title": "② 客户端 / 代理状态可靠隔离", "tone": "blue", "lines": [
            "•  不串凭据、会话与授权回调",
            "•  隔离边界多于「一个 home 目录」",
        ]},
        {"title": "③ 读本机素材并做 PPT", "tone": "blue", "lines": [
            "•  先查找 → 再读取 → 再生成",
            "•  登录成功 ≠ 工具链可用，须单独验收",
        ]},
    ],
    "callout": ("结论", "本地素材不需要因为账号而复制，也不需要第二台电脑；但「开出两个窗口」不等于「两个账号完全隔离」。用途上的目标方案仍是两个独立桌面环境，实现上的推荐改为：桌面 A 不动 + 官方 CLI 在独立目录登录 B（能接受终端入口时优先）。", "blue"),
})

# 3 本机实现复核
S.append({
    "kicker": "02｜本机实现复核",
    "title": "为什么 v1 的简单启动器不够",
    "subtitle": "定向只读检查：AppxManifest.xml、resources/owl-electron-app.json、app.asar 启动模块、config.toml 路径与安全字段。",
    "cards": [
        {"title": "已确认的本地事实", "tone": "ok", "lines": [
            "•  商店包名 OpenAI.Codex，版本 26.1007.2314.0；显示名与入口为 ChatGPT / app\\ChatGPT.exe",
            "•  同目录的小型 codex.exe 不能当作已验证的独立主程序",
            "•  App 会读取 CODEX_HOME，本地 app-server 继承该环境变量",
            "•  bootstrap 自行 app.setPath(\"userData\", …)，优先读 CODEX_ELECTRON_USER_DATA_PATH",
            "•  Windows 网络模块使用固定命名管道 \\\\.\\pipe\\codex-ipc",
        ]},
        {"title": "还解释不清的共享边界", "tone": "warn", "lines": [
            "•  固定 IPC 未在该函数中按 CODEX_HOME 区分",
            "•  用户数据路径覆盖属当前包的实现细节，不是稳定公开接口",
            "•  只传 --user-data-dir 不保证应用最终采用",
            "•  清单注册全局 codex: 协议并声明 1455/1457 防火墙规则 ⇒ 授权回调不能只靠目录隔离就宣称解决",
            "•  清单已禁用文件系统写入虚拟化，LocalCache 目录可能只是历史遗留",
        ]},
    ],
    "callout": ("判读口径", "以上是「实现线索」，不是「运行保证」；源码阅读不代替实际运行验收。已核实补充：桌面 App 内确实存在 Account switcher / Add account（codex.profileDropdown.addAccount 等），上限为 2 个已保存账号 ⇒ 交替使用是既有能力，双窗口才是待验证项。", "warn"),
})

# 4 必须更正的前稿说法
CORR = [
    ("账号本质就是一个 auth.json", "官方支持文件、系统凭据库、内存等多种保存方式；见到 auth.json 只证明存在文件凭据"),
    ("logout 一定发送 revoke，登录永久作废", "官方描述是清除当前保存的凭据，退出后可重新登录；不要为了保留 A 在线而退出 A"),
    ("同一账号两份独立登录必然互踢", "复制同一组 token 后并发刷新有失效风险；不能推导为正规独立授权必然互踢"),
    ("独立 CODEX_HOME + user-data-dir 保证桌面双开", "还涉及用户数据目录覆盖、单实例锁、固定 IPC、回调路由与本地服务，未验证不能保证"),
    ("config.toml、全盘权限、skills 必须整体继承", "应先建最小安全环境，按需复用经检查的 PPT 工具；整体复制会带入通知程序、MCP 与旧路径"),
    ("复制 memories 就是共享记忆", "复制形成独立快照，后续不自动双向同步；默认不迁移私人记忆与聊天历史"),
    ("PATH 无 codex 说明没装任何 CLI", "只说明当前执行环境没找到独立 codex 命令（本机实测：内置 CLI 位于 AppData\\Local\\OpenAI\\Codex\\bin\\…，未加入 PATH）"),
    ("PS 5.1 中文注释必导致 ParserError", "编码不匹配可能导致乱码或语法问题；合法编码与中文本身不是错误"),
    ("CODEX_SQLITE_HOME 可解决沙箱执行器冲突", "它控制 SQLite 状态位置，不是通用 IPC、执行器或登录回调冲突解决器"),
    ("复制 model = … 就能让新账号更强", "模型可用性取决于账号 / 工作区权益与服务端模型列表"),
]
S.append({
    "kicker": "03｜必须更正的说法",
    "title": "前稿 10 处需要修订的表述",
    "subtitle": "以下为需要在文档与汇报中统一更正的口径，避免把「推断」写成「承诺」。",
    "table": {"head": ["前稿说法", "修订后口径"], "rows": CORR, "w1": 4.35},
})

# 5 推荐路径
S.append({
    "kicker": "04｜推荐实施顺序",
    "title": "默认路径：桌面 A 不动 + 独立 CLI 登录 B",
    "subtitle": "该路径避开桌面单实例锁，使用官方文档明确描述的认证与目录机制；但不能据此宣称官方承诺所有多账号组合。",
    "timeline": [
        ("1", "确认独立 CLI 实际路径", "已有则用；没有再决定是否安装。不使用来源不明的账号管理器"),
        ("2", "为 B 建立新 Codex home", "不复制 A 的认证、会话、数据库与私密记忆"),
        ("3", "明确选择凭据保存方式", "文件模式在独立 home 下便于验证；auth.json 按密码保护，避免云盘同步与公开上传。用系统凭据库需核查条目作用域"),
        ("4", "独立浏览器个人资料中正规登录 B", "无需先注销 A 的浏览器或客户端"),
        ("5", "环境变量只对 B 的启动进程生效", "不写系统级 CODEX_HOME，不改用户配置档去影响 A"),
        ("6", "先验证账号与模型可用性", "再跑「查文件 + PPT 小样」验收（见后两页）"),
    ],
})

# 6 工作流 + 隐私
S.append({
    "kicker": "05｜本机查找与 PPT 工作流",
    "title": "权限边界与隐私边界",
    "subtitle": "提示词里的「不改源文件」是行为约束，不等于操作系统只读权限。",
    "cards": [
        {"title": "权限设计", "tone": "blue", "lines": [
            "•  查找阶段：指定目录与关键词，先列路径、大小、日期等元数据；不移动、不改名、不删除源文件",
            "•  PPT 阶段：读取你确认的素材，允许写入专门输出目录；默认保留源文件原样",
            "•  两个账号可读同一份素材，但不要同时编辑同一份 PPT；用 A/B 子目录或不同版本名，由你选稿",
            "•  「查全盘」不必默认使用 danger-full-access：它不仅扩展读取，还放开修改与执行风险",
            "•  敏感素材需要更强边界时，使用受控素材副本或真正的只读访问设计",
        ]},
        {"title": "隐私设计", "tone": "warn", "lines": [
            "•  文件保存在本机，不代表交给联网模型的正文仍只在本机处理；调用云模型时被选中内容通常会被发送",
            "•  账号 B 默认不继承微信私密数据、录音、聊天记忆、医疗材料、浏览器数据与凭据",
            "•  需要严格本地处理的材料，先用本地工具提取或脱敏，再由你决定是否提供摘要给云模型",
        ]},
    ],
})

# 7 验收 + 撤回
S.append({
    "kicker": "06｜验收与撤回标准",
    "title": "怎么算成功，失败怎么退",
    "subtitle": "验收不能只看「出现了两个窗口」或目录时间戳。",
    "cards": [
        {"title": "验收清单（全部通过才算成立）", "tone": "ok", "lines": [
            "•  界面显示实际不同的账号，必要时同时确认工作区；单看 account_id 不足以唯一证明身份",
            "•  各代理进程的实际环境、用户数据路径、凭据存储作用域不同",
            "•  授权完成、重启与凭据自动刷新后，B 仍是账号 B",
            "•  关闭 B 不影响 A；关闭 A 不影响 B",
            "•  两者读取指定素材、输出到不同路径；PPT 小样可编辑且预览正确",
            "•  商店更新后重新验证，不承诺私有启动变量跨版本稳定",
        ]},
        {"title": "撤回与清理", "tone": "warn", "lines": [
            "•  测试不通过：只关闭新实例并保留测试目录",
            "•  不覆盖 A 的配置，不递归删除用户目录",
            "•  A 可能后台刷新或写日志，其目录时间戳变化不能单独作为「串写」证据；要证明 B 的写入归属",
            "•  后续清理须由用户明确确认文件清单后，先备份再移至回收站",
            "•  v1 的 Remove-Item 递归删除回滚命令不再有效，请勿照旧稿执行",
        ]},
    ],
})

# 8 PPT 能力验收小样
S.append({
    "kicker": "07｜能力验收小样",
    "title": "登录之后，还要用一个非敏感小项目验证 5 件事",
    "subtitle": "官方 Plus 订阅登录与 API key 按量计费是两条不同路径；不要为了登录 B 而误换 API key。两个 Plus 账号的权益不会自动合并。",
    "cards": [
        {"title": "① 查找", "tone": "plain", "lines": ["能在指定目录按关键词找到文件，并正确报告来源路径与元数据"]},
        {"title": "② 读取", "tone": "plain", "lines": ["能读取选定的 PDF / Word / 图片素材正文，不只是核对文件名"]},
        {"title": "③ 生成", "tone": "plain", "lines": ["能生成真正可编辑的 PPTX，而不是把整页截图塞进幻灯片"]},
        {"title": "④ 预览核查", "tone": "plain", "lines": ["能预览并核查溢出、中文字体、图片清晰度、比例与可编辑性"]},
        {"title": "⑤ 修改另存", "tone": "plain", "lines": ["能按反馈只改指定页面，另存为新版本，不覆盖源素材"]},
    ],
})

# 9 备选方案
S.append({
    "kicker": "08｜备选方案与边界",
    "title": "若必须双桌面窗口，或其实不需要并行",
    "subtitle": "两条备选路径的前置条件与成本必须讲清楚，不能当成「无需验证的万能办法」。",
    "cards": [
        {"title": "若必须双桌面窗口", "tone": "warn", "lines": [
            "•  先审查当前版本的实际启动入口与状态作用域，不执行旧稿脚本",
            "•  核查用户数据路径是否生效、固定 IPC 如何路由、授权结果落到哪个客户端、凭据库是否共享",
            "•  先用空配置与非敏感素材运行；通过后再加入所需 PPT 工具，不全量继承旧配置",
            "•  第三方多开工具仅在源码、版本兼容性、更新方式与凭据处理审查通过后才考虑；README 声称支持 Windows ≠ 已适配你这一版",
            "•  新 Windows 用户或独立系统环境是进一步隔离选项，但涉及应用注册、文件 ACL、运行环境与服务，切换成本高",
        ]},
        {"title": "若其实不需要并行", "tone": "ok", "lines": [
            "•  使用客户端正常的退出 / 登录切换即可，这是合法正常操作",
            "•  退出当前凭据不意味着账号永久失效",
            "•  代价：不能同时保持两个桌面账号工作，需要接受这个限制",
            "•  已核实：桌面端自带账号切换器（上限 2 个已保存账号），交替使用无需双窗口",
        ]},
    ],
})

# 10 证据与状态
S.append({
    "kicker": "09｜证据与状态",
    "title": "本轮状态、证据来源与最终建议",
    "subtitle": "严格区分「官方文档明确支持」与「桌面多账号组合尚未证实」。",
    "cards": [
        {"title": "本轮状态", "tone": "plain", "lines": [
            "•  方案复核完成；未配置、未启动、未登录第二个客户端",
            "•  v1 实验脚本与回滚删除命令已撤回，请勿照旧稿执行",
            "•  默认不迁移历史会话与私人记忆",
        ]},
        {"title": "官方文档（2026-10-12 获取）", "tone": "plain", "lines": [
            "•  learn.chatgpt.com/docs/auth?surface=app（认证、凭据保存、退出登录）",
            "•  learn.chatgpt.com/docs/cli/reference（CLI 选项、沙箱、login/logout 定义）",
            "•  learn.chatgpt.com/docs/windows/windows-app（Windows 应用、PowerShell、沙箱与 Codex home）",
            "•  文档明确支持的机制与未证实的桌面多账号组合已分开表述",
        ]},
    ],
    "callout": ("最终建议", "先保住现有账号 A；不要照旧稿复制配置或运行启动器。能接受终端入口就优先验证「桌面 A + CLI B」；必须两个桌面窗口，就按当前版本先做隔离验证，再谈多开。", "ok"),
})


# 11 本机实测与双窗口结论
S.append({
    "kicker": "10｜本机实测与双窗口结论",
    "title": "一个 CLI + 一个桌面端：已具备本机依据",
    "subtitle": "以下为本会话在 C:\\Users\\wardc 上的只读取证与隔离实测，与 v2 正文的谨慎口径并列。",
    "cards": [
        {"title": "实测事实（已核实）", "tone": "ok", "lines": [
            "•  凭据按 CODEX_HOME 分离：CLI 使用独立 home 时 auth.json 与 A 互不读取",
            "•  daemon 控制套接字按 CODEX_HOME 定位（app-server-control.sock、app-server-daemon\\*.lock），不是全局单例",
            "•  隔离实测：独立 home 下 login status 返回 Not logged in，仅在该 home 内产生 tmp\\，未触碰 ~\\.codex",
            "•  兜底开关：daemon_auto_start 为 stable 且默认 true，可用 --disable daemon_auto_start 关闭",
            "•  桌面端切换器上限 2 个已保存账号，交替使用是既有能力",
        ]},
        {"title": "桌面双开的真实约束（关键）", "tone": "warn", "lines": [
            "•  单实例锁仅在 hasExplicitUserDataPath 为真时生效；环境变量为空则不获取锁，多实例会共用同一份用户数据与会话状态",
            "•  Windows IPC 为固定全局管道 codex-ipc，不随目录或账号变化 ⇒ 桌面双开必须单独解决这一层",
            "•  桌面双开因此要同时解决 管道 + 回调路由 + 凭据作用域 + 应用注册四件事",
            "•  上面三条来自包内代码，属实现线索，不等于运行保证，仍须实测验收",
        ]},
    ],
    "callout": ("本轮决定", "目标改为：桌面端保持账号 A，CLI 以独立 CODEX_HOME 登录账号 B，两窗口并行、全程不切换。唯一保留项是桌面双开改为独立实验：需以自定义 user data 路径启动第二个实例，并通过实测验收后再写入结论。", "blue"),
})


# ---------------- 渲染 ----------------
for i, spec in enumerate(S, start=1):
    kind = spec.get("kind")
    if kind == "cover":
        sl = prs.slides.add_slide(BLANK)
        rect(sl, 0, 0, SW, SH, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
        rect(sl, 0, 0, SW, 0.19, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
        rect(sl, M, 2.05, 0.09, 1.5, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
        tf = tbox(sl, M + 0.34, 1.98, CW - 1.0, 0.4)
        p = para(tf, first=True)
        run(p, "技术方案复核", size=13, bold=True, color=RGBColor(0x8F, 0xB6, 0xFF))
        tf = tbox(sl, M + 0.34, 2.44, CW - 0.6, 1.3)
        p = para(tf, first=True, line=1.12)
        run(p, "Codex 双账号并行方案", size=38, bold=True, color=WHITE)
        p = para(tf, space_before=6, line=1.12)
        run(p, "审慎修订版 v2", size=24, bold=True, color=RGBColor(0x8F, 0xB6, 0xFF))
        rect(sl, M + 0.34, 4.02, 3.2, 0.02, fill=RGBColor(0x35, 0x42, 0x5C), shape=MSO_SHAPE.RECTANGLE)
        tf = tbox(sl, M + 0.34, 4.28, CW - 1.0, 0.7)
        p = para(tf, first=True, line=1.28)
        run(p, "状态：方案复核完成 ｜ 未配置、未启动、未登录第二个客户端", size=12.5, color=RGBColor(0xC9, 0xD3, 0xE2))
        p = para(tf, space_before=5, line=1.28)
        run(p, "用途：查找本机文件并制作 PPT ｜ 日期：2026-10-12", size=12.5, color=RGBColor(0xC9, 0xD3, 0xE2))
        tf = tbox(sl, M + 0.34, SH - 0.95, CW - 1.0, 0.4)
        p = para(tf, first=True)
        run(p, "v1 的实验脚本与回滚删除命令已撤回，请勿照旧稿执行。", size=11, bold=True, color=RGBColor(0xFF, 0xC9, 0x8F))
        continue

    sl, y = slide_base(i, spec["kicker"], spec["title"], spec.get("subtitle"))
    y0 = y
    y1 = SH - 0.72

    if "cards" in spec:
        co = spec.get("callout")
        ch = 1.0
        if co:
            y1c = y1 - ch - 0.22
        else:
            y1c = y1
        cards(sl, y0, y1c, spec["cards"], cols=spec.get("cols", len(spec["cards"])))
        if co:
            callout(sl, M, y1 - ch, CW, ch, co[0], co[1], tone=co[2])

    elif "table" in spec:
        t = spec["table"]
        head = t["head"]; rows = t["rows"]; w1 = t["w1"]
        w2 = CW - w1
        rh = 0.415
        hh = 0.34
        y = y0
        rect(sl, M, y, CW, hh, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
        tf = tbox(sl, M + 0.14, y + 0.055, w1 - 0.28, 0.24)
        p = para(tf, first=True); run(p, head[0], size=10.5, bold=True, color=WHITE)
        tf = tbox(sl, M + w1 + 0.14, y + 0.055, w2 - 0.28, 0.24)
        p = para(tf, first=True); run(p, head[1], size=10.5, bold=True, color=WHITE)
        y += hh
        for ri, (a, b) in enumerate(rows):
            bg = RGBColor(0xFF, 0xFF, 0xFF) if ri % 2 == 0 else CARD
            rect(sl, M, y, CW, rh, fill=bg, shape=MSO_SHAPE.RECTANGLE)
            tf = tbox(sl, M + 0.14, y + 0.055, w1 - 0.28, rh - 0.1)
            p = para(tf, first=True, line=1.1)
            run(p, a, size=9.5, bold=True, color=RGBColor(0x8A, 0x3A, 0x1A))
            tf = tbox(sl, M + w1 + 0.14, y + 0.055, w2 - 0.28, rh - 0.1)
            p = para(tf, first=True, line=1.1)
            run(p, b, size=9.5, color=BODY)
            y += rh
        rect(sl, M, y, CW, 0.015, fill=LINE, shape=MSO_SHAPE.RECTANGLE)

    elif "timeline" in spec:
        items = spec["timeline"]
        avail = y1 - y0
        gap = 0.11
        h = (avail - gap * (len(items) - 1)) / len(items)
        for k, (num, ttl, desc) in enumerate(items):
            yy = y0 + k * (h + gap)
            rect(sl, M, yy, CW, h, fill=CARD, adj=0.09)
            rect(sl, M, yy, 0.055, h, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
            rect(sl, M + 0.22, yy + (h - 0.36) / 2, 0.36, 0.36, fill=BLUE, shape=MSO_SHAPE.OVAL)
            tf = tbox(sl, M + 0.22, yy + (h - 0.36) / 2 + 0.045, 0.36, 0.28, align=PP_ALIGN.CENTER)
            p = para(tf, first=True, align=PP_ALIGN.CENTER)
            run(p, num, size=11.5, bold=True, color=WHITE)
            tf = tbox(sl, M + 0.72, yy + 0.11, 2.95, h - 0.22, anchor=MSO_ANCHOR.MIDDLE)
            p = para(tf, first=True, line=1.12)
            run(p, ttl, size=11.5, bold=True, color=INK)
            tf = tbox(sl, M + 3.82, yy + 0.11, CW - 4.05, h - 0.22, anchor=MSO_ANCHOR.MIDDLE)
            p = para(tf, first=True, line=1.2)
            run(p, desc, size=9.5, color=BODY)

prs.save(OUT)
print("SAVED:", OUT)
print("slides:", len(prs.slides._sldIdLst))
