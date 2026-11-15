# -*- coding: utf-8 -*-
r"""
build_experience_dossiers.py —— 每段经历一份独立档案（骨架 + 本地可算字段）

分工（★ 诚实标注哪些是本地算的、哪些必须模型读原文才能给）
--------------------------------------------------------
  【本地可算 → 本脚本填】
    六时点（从日期区间推准备/开始/结束）· 日期依据 · 相关材料位置（按时间窗+关键词）
    · 同期聊天量 · 相关会话清单
  【必须模型读原文 → 标 `待模型`】
    具体行动 · 我的贡献 · 分歧解释 · 竞争解释 · 反例 · 中期汇报怎么讲

★ 为什么不猜：这五项要么需要读原话、要么需要跨材料比对 ——
  本地规则猜出来的一定错，宁可留空并显式标注「待模型」。

用法
----
  python tools\build_experience_dossiers.py
"""
import os, io, re, csv, json, glob, sqlite3, datetime, traceback

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
OUTDIR = os.path.join(BATCH, "dossiers")
OUT_HTML = os.path.join(WS, "经历档案_首版_2026-10-06.html")
PACK = r"C:\Users\wardc\Desktop\中期汇报_成果与材料_2026-10-05"
CSVDIR = os.path.join(PACK, "02_数据表")

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# 每条线在聊天里可能出现的会话关键词（用于找「同期聊天」）
LINE_KW = {
    "A": ["陈晔", "导！急速回", "武宏", "花家地", "CAFA"],
    "B": ["井邻", "洞台", "悲鸿", "怀柔", "工作站", "陈晔"],
    "C": ["澜沧", "知行", "Movers4Climate", "绿墨护未", "米雪"],
    "D": ["美学与艺术", "会务", "论坛"],
    "E": ["北京广播电视台", "吴显", "美术馆", "厦门", "女美术家", "新东方"],
    "F": ["格拉斯哥", "校友", "中拍", "郎园", "美术馆之夜"],
    "G": ["数字人", "知津", "涅槃", "Hyper3D", "TouchDesigner", "MediaPipe"],
    "H": ["古北水镇", "照片"],
}


def rd(name):
    p = os.path.join(CSVDIR, name)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_range(s):
    """把 '2026-04-26 → 05-10' / '2026-08' / '2025-09 → 至今' 解析成 (lo, hi, basis)"""
    s = (s or "").strip()
    if not s:
        return "", "", ""
    # 统一分隔符
    s2 = s.replace("–", "-").replace("—", "-")
    parts = [p.strip() for p in re.split(r"→|~|至", s2) if p.strip()]
    def norm(t, base_year=None):
        t = t.strip()
        if t in ("至今", "今"):
            return datetime.date.today().strftime("%Y-%m-%d")
        m = re.match(r"^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$", t)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), m.group(3)
            return "%04d-%02d-%02d" % (y, mo, int(d) if d else 1)
        m = re.match(r"^(\d{1,2})(?:-(\d{1,2}))?$", t)
        if m and base_year:
            mo, d = int(m.group(1)), m.group(2)
            return "%04d-%02d-%02d" % (base_year, mo, int(d) if d else 1)
        m = re.match(r"^(\d{4})$", t)
        if m:
            return "%s-01-01" % m.group(1)
        return ""
    lo = norm(parts[0]) if parts else ""
    base = int(lo[:4]) if lo else None
    hi = norm(parts[1], base) if len(parts) > 1 else lo
    return lo, hi, ("从「%s」解析" % s)


def find_materials(c, lo, hi, kw, cap=12):
    """在时间窗内找相关材料（按路径/文件名关键词）"""
    if not lo:
        return []
    hi2 = hi or lo
    q = """select path,ext,kind,bytes,mtime from materials
           where substr(mtime,1,10) between ? and ? limit 4000"""
    rows = list(c.execute(q, (lo, hi2)))
    out = []
    for path, ext, kind, nb, mt in rows:
        base = os.path.basename(path)
        if any(k and k in base for k in kw):
            out.append((path, ext, kind, nb, mt))
    out.sort(key=lambda x: -x[3])
    return out[:cap]


def find_sessions(c, lo, hi, kw, cap=12):
    """在时间窗内找相关会话（从 chunks 表）"""
    if not lo:
        return []
    hi2 = hi or lo
    q = """select session_name,session_type,count(*),sum(nmsg) from chunks
           where lo<=? and hi>=? group by 1,2 order by 4 desc limit 60"""
    rows = list(c.execute(q, (hi2, lo)))
    hit = [r for r in rows if any(k and k in (r[0] or "") for k in kw)]
    return hit[:cap]


def build():
    os.makedirs(OUTDIR, exist_ok=True)
    c = sqlite3.connect(DB)
    cand = rd("02_候选成果总表_全部.csv")
    if not cand:
        print("★ 找不到候选成果 CSV，请先跑 export_report_pack.py")
        return None

    docs = []
    for i, r in enumerate(cand, 1):
        line = (r.get("线") or "").strip()
        key = line[:1]
        lo, hi, basis = parse_range(r.get("日期", ""))
        kw = LINE_KW.get(key, [])
        mats = find_materials(c, lo, hi, kw)
        sess = find_sessions(c, lo, hi, kw)

        # 六时点：只有「开始 / 结束」能从日期区间直接推；其余标待定
        six = {
            "准备开始": lo + "（区间起点，**实际准备日待模型从原文确认**）" if lo else "待模型",
            "实际开始": lo or "待模型",
            "关键节点": "待模型（需读该时段聊天/文件找出转折点）",
            "结束": hi or "进行中",
            "交付": "待模型（需找出交付动作与对方确认）",
            "反馈": "待模型（需找出对方评价/采用/公开）",
        }
        d = {
            "n": i, "线": line, "日期": r.get("日期", ""), "事项": r.get("事项", ""),
            "个人贡献_表内": r.get("个人贡献", ""), "具体产物": r.get("具体产物", ""),
            "状态": r.get("状态", ""), "备注": r.get("备注", ""),
            "lo": lo, "hi": hi, "basis": basis, "six": six,
            "mats": mats, "sess": sess,
        }
        docs.append(d)

    # ---- 落盘 Markdown ----
    for d in docs:
        L = ["# 经历档案 %02d ｜ %s" % (d["n"], d["事项"][:60]),
             "",
             "> 线：%s ｜ 日期：%s ｜ 状态：%s" % (d["线"], d["日期"], d["状态"]),
             "> ★ `待模型` = 需模型读原始聊天/材料才能给，**本地不猜**。",
             ""]
        L += ["## 一、六时点", "", "| 时点 | 值 |", "|---|---|"]
        for k, v in d["six"].items():
            L.append("| %s | %s |" % (k, v))
        L += ["", "**日期依据**：%s" % (d["basis"] or "（无区间，需从原文定位）"), ""]
        L += ["## 二、具体行动与我的贡献", "",
              "- 表内已记贡献：%s" % (d["个人贡献_表内"] or "—"),
              "- 具体行动（**待模型**）：读该时段聊天，逐条列出「他实际做了什么」",
              "- ★ 拆开写：哪些是他**独立决定/独立完成**的，哪些是**团队动作**",
              ""]
        L += ["## 三、已有成果与产物", "", "- 表内已记产物：%s" % (d["具体产物"] or "—"), ""]
        L += ["## 四、相关材料位置（时间窗内匹配）", ""]
        if d["mats"]:
            L += ["| 文件 | 类型 | 大小 | 时间 |", "|---|---|---|---|"]
            for p, ext, kind, nb, mt in d["mats"]:
                L.append("| `%s` | %s | %.1f KB | %s |" % (p, kind, nb / 1024, mt))
        else:
            L.append("（时间窗内未按关键词匹配到材料 —— 需模型/人工补）")
        L += ["", "## 五、同期聊天（该时段的活跃会话）", ""]
        if d["sess"]:
            L += ["| 会话 | 类型 | 片段数 | 消息数 |", "|---|---|---|---|"]
            for nm, st, nch, nm2 in d["sess"]:
                L.append("| %s | %s | %d | %s |" % (nm, st, nch, "{:,}".format(nm2 or 0)))
        else:
            L.append("（该时段未匹配到相关会话 —— 需扩大关键词或人工确认）")
        L += ["", "## 六、仍有分歧的解释 / 竞争解释 / 反例（**待模型**）", "",
              "- 竞争解释 A：待模型",
              "- 竞争解释 B：待模型",
              "- 反例线索：待模型",
              "",
              "## 七、中期汇报可以怎么讲（**待模型**）", "",
              "- 一句话讲法：待模型",
              "- 可展示素材：见第四节",
              "- ⚠️ 口径提醒：见《汇报清单（首版）》第四节「证据规则」",
              ""]
        p = os.path.join(OUTDIR, "EXP-%02d.md" % d["n"])
        io.open(p, "w", encoding="utf-8").write("\n".join(L))
        d["path"] = p

    # ---- 汇总 HTML ----
    from collections import Counter
    H = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<title>经历档案（首版）2026-10-06</title><style>',
         '*{box-sizing:border-box}body{margin:0;background:#f7f6f3;color:#22201d;',
         'font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}',
         '.wrap{max-width:1100px;margin:0 auto;padding:38px 26px 80px}',
         'h1{font-size:25px;margin:0 0 6px}h2{font-size:17px;margin:30px 0 10px;',
         'padding-bottom:7px;border-bottom:2px solid #e5e1da}',
         'table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}',
         'th,td{border:1px solid #e5e1da;padding:6px 9px;text-align:left;vertical-align:top}',
         'th{background:#efece6;font-weight:600}',
         '.warn{background:#fff8e6;border-left:4px solid #e0a800;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         '.ok{background:#eef7ef;border-left:4px solid #3f9d54;padding:11px 15px;border-radius:0 6px 6px 0;margin:14px 0;font-size:13.5px}',
         'code{background:#efece6;padding:1px 5px;border-radius:3px;font-size:12px}',
         '.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}',
         '.card{flex:1 1 150px;background:#fff;border:1px solid #e5e1da;border-radius:8px;padding:12px 14px}',
         '.card .v{font-size:21px;font-weight:700}.card .k{font-size:12px;color:#6b6660}',
         '.foot{margin-top:50px;padding-top:14px;border-top:1px solid #ddd9d2;font-size:12.5px;color:#6b6660}',
         '</style></head><body><div class="wrap">']
    A = H.append
    A("<h1>经历档案（首版）</h1>")
    A('<p style="color:#6b6660;font-size:13px">生成 %s ｜ %d 段经历 ｜ 来源：候选成果表 × 材料时间窗 × 聊天片段</p>'
      % (NOW, len(docs)))
    A('<div class="warn"><b>★ 这份档案是「骨架」</b>：'
      '<b>六时点 / 日期依据 / 相关材料 / 同期聊天</b> = 本地已算好；'
      '<b>具体行动 / 我的贡献 / 竞争解释 / 反例 / 汇报讲法</b> = 标 <code>待模型</code>。'
      '这五项要么需要读原话、要么需要跨材料比对，<b>本地规则猜出来的一定错，所以不猜</b>。</div>')

    n_mat = sum(1 for d in docs if d["mats"])
    n_sess = sum(1 for d in docs if d["sess"])
    A('<div class="kpi">')
    for k, v in [("经历段数", str(len(docs))), ("匹配到材料", "%d 段" % n_mat),
                 ("匹配到同期聊天", "%d 段" % n_sess), ("待模型字段", "5 项/段")]:
        A('<div class="card"><div class="v">%s</div><div class="k">%s</div></div>' % (v, k))
    A('</div>')

    A("<h2>一、档案总表</h2>")
    A("<table><tr><th>#</th><th>线</th><th>日期</th><th>事项</th><th>状态</th>"
      "<th>材料</th><th>同期会话</th><th>档案</th></tr>")
    for d in docs:
        A("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
          "<td>%d</td><td>%d</td><td><code>%s</code></td></tr>"
          % (d["n"], d["线"][:2], d["日期"], d["事项"][:70], d["状态"],
             len(d["mats"]), len(d["sess"]), os.path.basename(d["path"])))
    A("</table>")

    A("<h2>二、按线统计</h2>")
    cnt = Counter(d["线"] for d in docs)
    A("<table><tr><th>线</th><th>经历段数</th><th>匹配到材料</th></tr>")
    for k, v in cnt.most_common():
        nm = sum(1 for d in docs if d["线"] == k and d["mats"])
        A("<tr><td>%s</td><td>%d</td><td>%d</td></tr>" % (k, v, nm))
    A("</table>")

    A("<h2>三、还缺什么（明确列出）</h2>")
    A("<table><tr><th>缺口</th><th>说明</th></tr>"
      "<tr><td>每段的「具体行动 / 我的贡献」</td><td>需模型读该时段原始聊天 → 逐条列出实际动作，并拆开「独立完成 vs 团队动作」</td></tr>"
      "<tr><td>「关键节点 / 交付 / 反馈」三个时点</td><td>需模型读原文找出转折点、交付动作与对方确认</td></tr>"
      "<tr><td>竞争解释与反例</td><td>需模型跨材料比对（聊天 ↔ 照片 ↔ 文件 ↔ 后续回顾）</td></tr>"
      "<tr><td>汇报讲法</td><td>依赖上面三项</td></tr>"
      "<tr><td>材料匹配不全</td><td>%d 段未按关键词匹配到材料 → 需放宽关键词或人工指认</td></tr>"
      "<tr><td>同期聊天匹配不全</td><td>%d 段未匹配到相关会话 → 同上</td></tr>"
      "</table>" % (len(docs) - n_mat, len(docs) - n_sess))

    A('<div class="foot">工具 <code>tools\\build_experience_dossiers.py</code> ｜ '
      '档案 Markdown 在 <code>_tmp\\batch\\dossiers\\</code> ｜ <b>内部资料，不得外传</b></div>')
    A("</div></body></html>")
    io.open(OUT_HTML, "w", encoding="utf-8").write("\n".join(H))
    c.close()
    return len(docs), n_mat, n_sess


if __name__ == "__main__":
    try:
        r = build()
        if r:
            print("经历档案 %d 段 ｜ 匹配到材料 %d 段 ｜ 匹配到同期聊天 %d 段" % r)
            print("→ %s" % OUT_HTML)
            print("→ %s" % OUTDIR)
    except Exception:
        traceback.print_exc()
