# -*- coding: utf-8 -*-
"""
build_payment_events.py —— 把「钱」事件化，并入事件库源（幂等）

两类：
  C·支付流事件 —— 消费/账单（微信支付、美团、支付宝官方推送号）
  D·转账事件   —— 人际转账 ≥¥1000（私聊里的转账卡片）

背景：交叉分析发现 —— 支出 ≥¥500 的 23 天里，7 天事件库完全空白（占 57% 金额）。
     即：**事件库对「钱」几乎是盲的**。本脚本把关键钱节点做成事件补进去。

入选规则：
  支付流 ① 单笔支出 ≥ ¥500 ② 类型 ∈ {扣款失败, 还款成功} ③ 额度变动
  转账   ④ 金额 ≥ ¥1000（同一会话同一天同金额去重）
去重：支付按 (日期, 金额, 类型)；转账按 (会话, 日期, 金额)

幂等：每次运行先删除 来源∈{C·支付流事件, D·转账事件} 的行，再重新追加。
"""
import csv, io, os, re, sqlite3, datetime, shutil
from collections import Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
SRC = os.path.join(WS, "events_merged.csv")
PAY = os.path.join(WS, "_tmp", "payment_flow.csv")
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

FIELDS = ["来源", "日期", "类别", "性质", "事件", "对话人", "涉及人", "主体",
          "层级", "分", "影响", "条数", "证据", "日期_原始", "日期修正"]

events = []

# ============ C · 支付流事件 ============
pays = list(csv.DictReader(io.open(PAY, encoding="utf-8-sig")))

def pick(r):
    if r["类型"] in ("扣款失败", "还款成功"):
        return True
    if r["类型"] == "额度变动":
        return True
    # 行程票（火车票/机票）—— 金额常低于 500 但事件价值高
    if re.search(r"站\s*-\s*\S+站|12306", r["原文"] or ""):
        return True
    if r["方向"] == "支出" and r["金额"]:
        return float(r["金额"]) >= 500
    return False

seen = set()
for r in pays:
    if not pick(r):
        continue
    amt = r["金额"]
    key = (r["时间"][:10], amt, r["类型"])
    if key in seen:
        continue
    seen.add(key)

    d = r["时间"][:10]
    kind, src, txt = r["类型"], r["来源"], r["原文"]
    v = float(amt) if amt else 0.0

    if re.search(r"站\s*-\s*\S+站|12306", txt):
        mm = re.search(r"(\S+站)\s*-\s*(\S+站)", txt)
        leg = ("%s → %s" % (mm.group(1), mm.group(2))) if mm else "火车票"
        desc, layer, score = "出行票务 ¥%s（%s）" % (format(v, ",.2f"), leg), "B", 24
    elif kind == "扣款失败":
        desc, layer, score = "★ 信用扣款失败：" + txt[:60], "A", 40
    elif kind == "还款成功":
        desc, layer, score = "信用还款 ¥%s（%s）" % (format(v, ",.2f"), src), "B", 25
    elif kind == "额度变动":
        desc, layer, score = "信用额度变动：" + txt[:60], "B", 22
    elif v >= 10000:
        desc, layer, score = "★ 大额支出 ¥%s（%s）" % (format(v, ",.2f"), src), "A", 40
    elif v >= 1000:
        desc, layer, score = "大额支出 ¥%s（%s）" % (format(v, ",.2f"), src), "A", 30
    else:
        desc, layer, score = "支出 ¥%s（%s）" % (format(v, ",.2f"), src), "B", 18

    events.append({
        "来源": "C·支付流事件", "日期": d, "类别": "钱/财务", "性质": "已发生",
        "事件": desc, "对话人": src, "涉及人": "", "主体": "我",
        "层级": layer, "分": str(score),
        "影响": "支出" if v > 0 else kind, "条数": "1",
        "证据": txt[:200], "日期_原始": d, "日期修正": "",
    })

# ============ D · 转账事件（人际金钱）============
c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
q = c.execute
name_of = {}
pat = re.compile(r"转账\s*([0-9]+(?:\.[0-9]{1,2})?)元")
seen2 = set()
for sk, ts, ct in q("""select session_key, ts, content from messages
                       where content like '%转账%' and session_key not like 'gh_%'
                         and session_key not like '%@chatroom' order by ts"""):
    m = pat.search(ct or "")
    if not m:
        continue
    v = float(m.group(1))
    if v < 1000:
        continue
    d = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    key = (sk, d, v)
    if key in seen2:
        continue
    seen2.add(key)
    if sk not in name_of:
        r = q("select display_name from sessions where talker=?", (sk,)).fetchone()
        name_of[sk] = r[0] if r else sk
    who = name_of[sk]
    layer, score = ("A", 35) if v >= 3000 else ("B", 22)
    events.append({
        "来源": "D·转账事件", "日期": d, "类别": "钱/财务", "性质": "已发生",
        "事件": "收到转账 ¥%s（来自 %s）" % (format(v, ",.2f"), who),
        "对话人": who, "涉及人": who, "主体": "我",
        "层级": layer, "分": str(score), "影响": "收入",
        "条数": "1", "证据": (ct or "")[:200], "日期_原始": d, "日期修正": "",
    })
c.close()

# ============ 幂等合并 ============
rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))
before = len(rows)
MONEY_SRC = {"C·支付流事件", "D·转账事件"}
kept = [r for r in rows if r.get("来源") not in MONEY_SRC]
removed = before - len(kept)

for r in kept:
    r.setdefault("日期_原始", r.get("日期", ""))
    r.setdefault("日期修正", "")
    for f in FIELDS:
        r.setdefault(f, "")

allrows = kept + events
allrows.sort(key=lambda r: (r["日期"] or "9999"))

if not os.path.exists(SRC + ".bak-money"):
    shutil.copy2(SRC, SRC + ".bak-money")

with io.open(SRC, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    for r in allrows:
        w.writerow({k: r.get(k, "") for k in FIELDS})

print("「钱」事件化完成（幂等）")
print("=" * 52)
print("  原有事件           : %d" % len(kept))
print("  移除旧钱事件       : %d" % removed)
print("  新增 · 支付流事件  : %d" % sum(1 for e in events if e["来源"] == "C·支付流事件"))
print("  新增 · 转账事件    : %d" % sum(1 for e in events if e["来源"] == "D·转账事件"))
print("  合计               : %d" % len(allrows))
print()
print("  新增事件逐月:")
for k, v in sorted(Counter(e["日期"][:7] for e in events).items()):
    print("    %s  %d" % (k, v))

