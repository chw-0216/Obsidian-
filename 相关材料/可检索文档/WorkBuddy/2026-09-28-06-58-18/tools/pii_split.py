# -*- coding: utf-8 -*-
r"""
pii_split.py —— PII 分流：区分「内部分析必需」与「不可公开」，并生成汇报展示版

背景
----
`privacy_audit.py` ⑨ 报出知识库 **57 处** 手机号 / 身份证 / 银行卡（25 个文件）。
但「有 PII」和「不能公开」不是一回事 —— 要分开处理：

  A 内部分析必需  本地分析要用（识别联系人、核对事件）→ **保留**，但**永不出库**
  B 不可公开      真人 PII / 身份证 / 银行卡 → **保留在库**，任何外发材料**一律不得含**
  C 工具自动索引  由脚本生成的清单，PII 只是「顺带被扫进来的」→ 可**脱敏后保留**
  D 可脱敏        展示时不影响信息的 → 直接打码

产出
----
  1. `_tmp\pii\pii_台账.csv`       逐处：文件 / 类型 / 分类 / 处置
  2. `_tmp\pii\PII分流报告.html`    分类汇总（可给本人看）
  3. `_tmp\pii\公开版\`             **对外产物的脱敏副本**（汇报展示用）

安全约束
--------
· 只读源；只写 `_tmp\pii\`
· **不改动知识库原文件**（要真脱敏用 `sanitize_vault_pii.py --apply`）
· 公开版是**副本**，原文件一个字节都不动
"""
import os, io, re, sys, csv, json, glob, shutil, datetime, traceback

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
PACK = r"C:\Users\wardc\Desktop\中期汇报_成果与材料_2026-10-05"
OUT = os.path.join(WS, "_tmp", "pii")
PUBLIC = os.path.join(OUT, "公开版")

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

PATTERNS = [
    ("手机号", re.compile(r"(?<![0-9A-Za-z])(1[3-9]\d{9})(?![0-9A-Za-z])")),
    ("身份证", re.compile(r"(?<![0-9A-Za-z])(\d{17}[\dXx])(?![0-9A-Za-z])")),
    ("银行卡", re.compile(r"(?<![0-9A-Za-z])(\d{16,19})(?![0-9A-Za-z])")),
]
_ID_W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_C = "10X98765432"

# 分类规则：(路径关键词, 分类, 处置, 风险级)
CLASSIFY = [
    ("_低价值联系人", "A 内部分析必需", "保留在库；外发材料一律剔除", "中（商家/服务联系人）"),
    ("01_人物档案", "B 不可公开", "保留在库；**外发一律脱敏**", "高（真人联系方式）"),
    ("03_事件库", "B 不可公开", "保留在库；**外发一律脱敏**", "★最高（含身份证）"),
    ("02_文件名录", "C 工具自动索引", "脚本产物 → 可整表脱敏或排除外发", "中"),
    ("_附件", "C 工具自动索引", "脚本产物 → 可整表脱敏或排除外发", "中"),
    ("04_方法论", "C 工具自动索引", "示例数据 → 打码即可", "低"),
    ("04_工作台", "B 不可公开", "保留在库；**外发一律脱敏**", "高"),
    ("01_个人信息", "B 不可公开", "保留在库；**外发一律脱敏**", "高"),
]


def id_ok(s):
    if not re.fullmatch(r"\d{17}[\dXx]", s or ""):
        return False
    return _ID_C[sum(int(s[i]) * _ID_W[i] for i in range(17)) % 11] == s[17].upper()


def luhn_ok(s):
    if not (s or "").isdigit() or not (16 <= len(s) <= 19):
        return False
    tot, alt = 0, False
    for ch in reversed(s):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        tot += d
        alt = not alt
    return tot % 10 == 0


def valid(label, v):
    if label == "身份证":
        return id_ok(v)
    if label == "银行卡":
        return luhn_ok(v)
    return True


def mask(label, v):
    if label == "手机号":
        return v[:3] + "****" + v[-4:]
    if label == "身份证":
        return v[:6] + "********" + v[-4:]
    return v[:4] + "********" + v[-4:]


def classify(rel):
    for key, cat, act, risk in CLASSIFY:
        if key in rel:
            return cat, act, risk
    return "D 待判", "人工确认", "待定"


def scan_text(t):
    """返回 [(类型, 值, 起止)]"""
    out = []
    for label, rx in PATTERNS:
        for m in rx.finditer(t):
            v = m.group(1)
            if valid(label, v):
                out.append((label, v, m.start(), m.end()))
    return out


def scan_vault():
    rows = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if not fn.lower().endswith((".md", ".csv", ".txt", ".json")):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, VAULT)
            try:
                t = io.open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            hits = scan_text(t)
            # ★ 文件名本身含 PII 也算一处（Obsidian 文件列表会直接显示）
            fnhits = scan_text(fn)
            cat, act, risk = classify(rel)
            for label, v, a, b in hits:
                rows.append({"位置": "正文", "文件": rel, "类型": label, "值": mask(label, v),
                             "分类": cat, "风险": risk, "处置": act})
            for label, v, a, b in fnhits:
                rows.append({"位置": "文件名", "文件": rel, "类型": label, "值": mask(label, v),
                             "分类": cat, "风险": risk, "处置": act + "（★ 文件名需一并改名）"})
    return rows


def scan_outbound():
    """扫描对外产物（工作区 HTML + 桌面包）—— 这些才是真正会被看到的"""
    rows = []
    targets = []
    for p in glob.glob(os.path.join(WS, "*.html")):
        targets.append(p)
    if os.path.isdir(PACK):
        for root, dirs, files in os.walk(PACK):
            for fn in files:
                if fn.lower().endswith((".html", ".md", ".csv")):
                    targets.append(os.path.join(root, fn))
    for p in targets:
        try:
            t = io.open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for label, v, a, b in scan_text(t):
            rows.append({"位置": "对外产物", "文件": p, "类型": label, "值": mask(label, v),
                         "分类": "★ 外发风险", "风险": "高", "处置": "必须脱敏后才能外发"})
    return rows


def build_public():
    """生成对外产物的**脱敏副本**（原文件不动）"""
    os.makedirs(PUBLIC, exist_ok=True)
    made = []
    srcs = sorted(glob.glob(os.path.join(WS, "*.html")))
    if os.path.isdir(PACK):
        srcs += sorted(glob.glob(os.path.join(PACK, "**", "*.html"), recursive=True))
    for p in srcs:
        try:
            t = io.open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        n = 0
        for label, rx in PATTERNS:
            def rep(m):
                nonlocal n
                v = m.group(1)
                if not valid(label, v):
                    return m.group(0)
                n += 1
                return mask(label, v)
            t = rx.sub(rep, t)
        if n:
            dst = os.path.join(PUBLIC, os.path.basename(p))
            io.open(dst, "w", encoding="utf-8").write(t)
            made.append((os.path.basename(p), n))
    return made


def html(rows, outbound, made):
    from collections import Counter
    c1 = Counter(r["分类"] for r in rows)
    c2 = Counter(r["类型"] for r in rows)
    H = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<title>PII 分流报告 · 2026-10-06</title><style>',
         '*{box-sizing:border-box}body{margin:0;background:#f7f6f3;color:#22201d;',
         'font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}',
         '.wrap{max-width:1040px;margin:0 auto;padding:38px 26px 80px}',
         'h1{font-size:25px;margin:0 0 6px}h2{font-size:17px;margin:32px 0 10px;',
         'padding-bottom:7px;border-bottom:2px solid #e5e1da}',
         'table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}',
         'th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}',
         'th{background:#efece6;font-weight:600}',
         '.bad{background:#fdeeee;border-left:4px solid #c0392b;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         'code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:12.5px}',
         '.foot{margin-top:50px;padding-top:14px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}',
         '</style></head><body><div class="wrap">']
    A = H.append
    A("<h1>PII 分流报告</h1>")
    A('<p style="color:#6b6660;font-size:13px">生成 %s ｜ 知识库 <code>%s</code></p>' % (NOW, VAULT))
    A('<div class="bad"><b>★ 本报告只做分流，不改动任何原文件。</b>'
      '要真正脱敏知识库，另跑 <code>python tools\\sanitize_vault_pii.py --apply</code>（会先备份）。</div>')

    A("<h2>一、总览</h2>")
    A("<table><tr><th>项</th><th>值</th></tr>"
      "<tr><td>知识库命中</td><td><b>%d 处</b>（%d 个文件）</td></tr>"
      "<tr><td>其中文件名本身含 PII</td><td>%d 处（★ Obsidian 文件列表会直接显示）</td></tr>"
      "<tr><td>对外产物命中</td><td><b>%d 处</b></td></tr>"
      "<tr><td>类型分布</td><td>%s</td></tr></table>"
      % (len(rows), len(set(r["文件"] for r in rows)),
         sum(1 for r in rows if r["位置"] == "文件名"),
         len(outbound),
         " ｜ ".join("%s %d" % (k, v) for k, v in c2.most_common())))

    A("<h2>二、按分类（内部分析 vs 可公开）</h2>")
    A("<table><tr><th>分类</th><th>处数</th><th>处置</th></tr>")
    act = {r["分类"]: r["处置"] for r in rows}
    for k, v in c1.most_common():
        A("<tr><td><b>%s</b></td><td>%d</td><td>%s</td></tr>" % (k, v, act.get(k, "")))
    A("</table>")
    A('<div class="warn"><b>分流原则</b>：'
      '<b>A 内部分析必需</b> = 本地分析要用来识别联系人/核对事件，<b>保留在库，但永不出库</b>；'
      '<b>B 不可公开</b> = 真人 PII / 身份证 / 银行卡，任何外发材料<b>一律不得含</b>；'
      '<b>C 工具自动索引</b> = 脚本扫出来的清单，PII 是顺带进来的，<b>可整表脱敏或排除外发</b>。</div>')

    if outbound:
        A("<h2>三、★ 对外产物里的 PII（最需要处理）</h2>")
        A("<table><tr><th>文件</th><th>类型</th><th>值（已打码）</th></tr>")
        for r in outbound[:60]:
            A("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (os.path.basename(r["文件"]), r["类型"], r["值"]))
        A("</table>")
    else:
        A("<h2>三、对外产物里的 PII</h2>")
        A('<div class="ok"><b>零命中</b> —— 工作区 HTML 与桌面包里<b>没有</b>手机号 / 身份证 / 银行卡。'
          '也就是说：<b>现有对外材料本身是干净的</b>，风险只在知识库内部。</div>')

    A("<h2>四、逐处清单</h2>")
    A("<table><tr><th>位置</th><th>文件</th><th>类型</th><th>值</th><th>分类</th><th>风险</th></tr>")
    for r in rows:
        A("<tr><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>"
          % (r["位置"], r["文件"], r["类型"], r["值"], r["分类"], r["风险"]))
    A("</table>")

    A("<h2>五、公开版（汇报展示用）</h2>")
    if made:
        A("<p>已生成 <b>%d</b> 份脱敏副本 → <code>_tmp\\pii\\公开版\\</code>：</p>" % len(made))
        A("<table><tr><th>文件</th><th>脱敏处数</th></tr>")
        for fn, n in made:
            A("<tr><td>%s</td><td>%d</td></tr>" % (fn, n))
        A("</table>")
    else:
        A('<div class="ok">对外产物无 PII → <b>无需生成脱敏副本</b>（原件即可直接展示）。</div>')

    A('<div class="foot">工具 <code>tools\\pii_split.py</code> ｜ '
      '真脱敏用 <code>tools\\sanitize_vault_pii.py --apply</code> ｜ 原文件未被改动</div>')
    A("</div></body></html>")
    return "\n".join(H)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 74)
    print("PII 分流")
    print("=" * 74)
    rows = scan_vault()
    print("知识库命中 %d 处 ｜ %d 个文件" % (len(rows), len(set(r["文件"] for r in rows))))
    outbound = scan_outbound()
    print("对外产物命中 %d 处" % len(outbound))
    made = build_public()
    print("公开版（脱敏副本）%d 份" % len(made))

    # CSV
    p = os.path.join(OUT, "pii_台账.csv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["位置", "文件", "类型", "值", "分类", "风险", "处置"])
        w.writeheader()
        w.writerows(rows + outbound)
    # HTML
    hp = os.path.join(OUT, "PII分流报告.html")
    io.open(hp, "w", encoding="utf-8").write(html(rows, outbound, made))
    print("→ %s" % p)
    print("→ %s" % hp)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
