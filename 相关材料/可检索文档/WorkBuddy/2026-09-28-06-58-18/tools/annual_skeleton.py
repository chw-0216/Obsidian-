# -*- coding: utf-8 -*-
"""
annual_skeleton.py —— 年度事件骨架（2025-10 → 2026-10）

把 analysis.sqlite 的 2,864 条事件映射到 8 条生活线 × 月份，
并叠加 index.sqlite 的原始消息量，标出「事件薄但消息不清净」的月份 = 抽取缺口。

八条生活线（与本人方案一致）：
  家庭 · 资金 · 学习 · 工作与项目 · 亲密关系 · 社交 · 出行 · 个人创作

输出：
  _tmp/annual_skeleton.csv         —— 生活线 × 月份 计数矩阵
  _tmp/annual_skeleton_detail.csv  —— 逐事件打标（含 source 便于回查）

只读两个库。用法：python tools\\annual_skeleton.py
"""
import os, io, re, csv, sqlite3, sys
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
ANALYSIS = os.path.join(WS, "analysis.sqlite")
INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

START, END = "2025-10", "2026-10"

# ── 八条生活线：按优先级匹配（先命中先归属，允许并列多标）──────────────
FAMILY_PERSON = ("刘丽萍", "蔡峰峰", "蔡晓梅", "母亲", "父亲")
LOVE_PERSON = ("笑一", "沐茜妍", "Summer", "Parapluie", "Pink", "婷婷",
               "Rachael", "小苹果", "Sīrius R", "ɪɴɢ 📎")
MENTOR_PERSON = ("导师 陈晔", "导！急速回，三思回得体！！！", "陈晔")

LINES = [
    # (线名, 类别集合, 关键词正则, 命中人)
    ("家庭",   set(),                      r"父母|爸爸|妈妈|家里|冷战|奶奶|小姑|望京|房租|养老|生病|住院", FAMILY_PERSON),
    ("资金",   {"钱/财务"},                 r"网贷|还款|逾期|转账|借款|欠款|扣款|余额|学费|分期|账单", ("微信支付", "美团金融服务")),
    ("学习",   {"学业/学术"},               r"导师|论文|开题|答辩|课程|作业|成绩|奖学金|入党|思想汇报|研一|研二", MENTOR_PERSON),
    ("工作与项目", {"项目/商务", "项目/实践", "求职/职场"},
                                           r"井邻|洞台|乡村美育|工作站|项目|合作|合同|实习|录用|面试|媒体部|美术馆|报价|甲方", ()),
    ("亲密关系", set(),                     r"同居|老公|老婆|女朋友|男朋友|相亲|约会|分手|恋爱|接机|送车", LOVE_PERSON),
    ("社交",   {"社交/见面", "比赛/活动"},   r"聚会|聚餐|见面|喝酒|校友|联谊|婚礼|生日", ()),
    ("出行",   {"出行/迁移"},               r"出差|回京|返程|机票|航班|高铁|驻村|下乡|云南|澜沧|怀柔|承德|坝上", ()),
    ("个人创作", {"展演/创作"},             r"展览|作品|布展|开幕|创作|拍摄|设计|版画|丝网|摄影|海报", ()),
]


def ro(p):
    return sqlite3.connect("file:" + p.replace("\\", "/") + "?mode=ro", uri=True)


def classify(ev):
    """返回该事件命中的生活线列表（可多标）"""
    cat = (ev["category"] or "").strip()
    text = " ".join([ev["event"] or "", ev["person"] or "", ev["subject"] or "", ev["impact"] or ""])
    person = (ev["person"] or "").strip()
    hits = []
    for name, cats, kw, ppl in LINES:
        ok = False
        if cat in cats:
            ok = True
        if ppl and person in ppl:
            ok = True
        if re.search(kw, text):
            ok = True
        if ok:
            hits.append(name)
    return hits or ["未分类"]


def main():
    con = ro(ANALYSIS)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "select event_id,date,level,category,person,event,source,subject,impact from events "
        "where date>=? and date<=? order by date", (START + "-01", END + "-31")).fetchall()

    months = []
    y, m = 2025, 10
    while (y, m) <= (2026, 10):
        months.append("%04d-%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1

    # 计数矩阵
    mat = {ln: Counter() for ln, *_ in LINES}
    mat["未分类"] = Counter()
    detail = []
    for ev in rows:
        mm = (ev["date"] or "")[:7]
        if mm not in months:
            continue
        hits = classify(ev)
        for h in hits:
            mat[h][mm] += 1
        detail.append({
            "event_id": ev["event_id"], "date": ev["date"], "month": mm,
            "level": ev["level"], "line": "|".join(hits),
            "category": ev["category"], "person": ev["person"],
            "event": (ev["event"] or "")[:160], "source": (ev["source"] or "")[:60],
        })
    con.close()

    # 原始消息量
    con2 = ro(INDEX)
    msg = {}
    for mm, n in con2.execute(
            "select strftime('%Y-%m',ts,'unixepoch','localtime') m, count(*) "
            "from messages where m>=? and m<=? group by m", (START, END)):
        msg[mm] = n
    con2.close()

    # 写矩阵
    with io.open(os.path.join(TMP, "annual_skeleton.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["生活线"] + months + ["合计"])
        for ln in [n for n, *_ in LINES] + ["未分类"]:
            vals = [mat[ln][mm] for mm in months]
            w.writerow([ln] + vals + [sum(vals)])
        w.writerow(["原始消息量"] + [msg.get(mm, 0) for mm in months] + [sum(msg.get(mm, 0) for mm in months)])
        # 事件/千条消息 = 抽取密度
        dens = []
        for mm in months:
            tot = sum(mat[ln][mm] for ln, *_ in LINES)
            dens.append(round(1000.0 * tot / msg[mm], 1) if msg.get(mm) else 0)
        w.writerow(["事件/千条消息"] + dens + [""])

    with io.open(os.path.join(TMP, "annual_skeleton_detail.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
        w.writeheader()
        w.writerows(detail)

    # 控制台：矩阵 + 缺口
    print("生活线 × 月份（2025-10 → 2026-10）")
    hdr = "%-10s" % "线"
    print(hdr + "".join("%6s" % mm[2:] for mm in months) + "   合计")
    for ln in [n for n, *_ in LINES] + ["未分类"]:
        vals = [mat[ln][mm] for mm in months]
        print("%-10s" % ln + "".join("%6d" % v for v in vals) + "%7d" % sum(vals))
    print("%-10s" % "消息(千)" + "".join("%6.1f" % (msg.get(mm, 0) / 1000.0) for mm in months))
    dens = []
    for mm in months:
        tot = sum(mat[ln][mm] for ln, *_ in LINES)
        dens.append(1000.0 * tot / msg[mm] if msg.get(mm) else 0)
    print("%-10s" % "事件/千条" + "".join("%6.1f" % d for d in dens))
    print()
    avg = sum(dens[:10]) / 10.0
    print("★ 前 10 个月平均密度 %.1f 事件/千条；低于此 60%% 的月份 = 抽取缺口：" % avg)
    for mm, d in zip(months, dens):
        if d < avg * 0.6:
            print("   %s  密度 %.1f（事件 %d / 消息 %d）" % (
                mm, d, sum(mat[ln][mm] for ln, *_ in LINES), msg.get(mm, 0)))
    print("\n→ _tmp\\annual_skeleton.csv / annual_skeleton_detail.csv")


if __name__ == "__main__":
    main()
