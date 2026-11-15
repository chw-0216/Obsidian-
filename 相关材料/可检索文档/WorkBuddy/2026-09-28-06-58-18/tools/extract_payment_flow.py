# -*- coding: utf-8 -*-
"""
extract_payment_flow.py  ——  从索引库提取「支付/消费」结构化流水（只读）

数据源（微信内的官方推送号，全本地）：
  微信支付       gh_3dfda90e39d6
  美团钱包       gh_be6f97978aa6
  美团           wxid_6853388533711
  美团金融服务   gh_d2e7afdd1d2a
  支付宝         gh_5d925baa110d

⚠️ 边界：公众号历史最早 2025-08-01（微信侧限制），此前无数据。
⚠️ 微信支付推送 ≠ 完整账单：只覆盖「转账/收款/退款/部分商户」，
   扫码付款给个体户多数不推。要完整账单需在微信内「下载账单」导出 CSV。

输出：
  _tmp/payment_flow.csv        结构化流水（时间/来源/类型/方向/金额/摘要/原文）
  _tmp/payment_flow_stats.txt  统计摘要
"""
import sqlite3, re, io, os, datetime, csv
from collections import Counter, defaultdict

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp"
os.makedirs(OUT, exist_ok=True)

SOURCES = {
    "gh_3dfda90e39d6":  "微信支付",
    "gh_be6f97978aa6":  "美团钱包",
    "wxid_6853388533711": "美团",
    "gh_d2e7afdd1d2a":  "美团金融服务",
    "gh_5d925baa110d":  "支付宝",
}

AMT_PATS = [
    r"[¥￥]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"支付金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"交易金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"退款金额[:：]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"应还金额[:：]\s*(?:人民币)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"需还款金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"变动金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"扣款金额[:：]\s*(?:9月美团月付账单)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"还款金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    r"订单金额[:：]\s*([0-9]+(?:\.[0-9]{1,2})?)",
]

# 方向判定：先匹配"类型"，再决定方向
def classify(ct):
    """返回 (类型, 方向, 摘要)"""
    s = ct.strip()
    if "扣款失败" in s:      return "扣款失败", "警示", "还款扣款失败"
    if "退款" in s and "到账" in s: return "退款到账", "收入", "退款"
    if "退款成功" in s:      return "退款成功", "收入", "退款"
    if "收益到账" in s:      return "收益到账", "收入", "支付返利"
    if "还款成功" in s:      return "还款成功", "支出", "信用还款"
    if "还款提醒" in s:      return "还款提醒", "警示", "信用账单提醒"
    if "额度变动" in s:      return "额度变动", "中性", "授信额度变化"
    if "提现发起" in s:      return "零钱提现发起", "中性", "零钱→银行卡"
    if "提现已到账" in s:    return "零钱提现已到账", "中性", "零钱→银行卡"
    if "已支付" in s or "已扣费" in s or "支付成功" in s or "交易成功" in s \
       or "购买成功" in s or "微信支付凭证" in s:
        return "支出", "支出", "付款"
    if "收款" in s:          return "收款", "收入", "收款"
    if "转账" in s:          return "转账", "中性", "转账"
    if "先享后付" in s:      return "先享后付", "中性", "信用支付通知"
    if "订单取消" in s:      return "订单取消", "中性", "取消"
    if "待支付" in s:        return "待支付", "中性", "未付款"
    if "收到新订单" in s:    return "订单通知", "中性", "订单"
    return "其他", "中性", s[:24]

def amount_of(ct):
    for p in AMT_PATS:
        m = re.search(p, ct)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None

def merchant_of(ct):
    for p in [r"商户名[称]?[:：]\s*(.{1,40}?)(?:\s|交易金额|支付方式|$)",
              r"商品详情[:：]?\s*(.{1,40}?)(?:\s|商户名称|$)",
              r"商品名[称]?[:：]\s*(.{1,40}?)(?:\s|支付|$)",
              r"订单内容[:：]\s*(.{1,30}?)(?:\s|取消时间|$)"]:
        m = re.search(p, ct)
        if m:
            return m.group(1).strip()
    return ""

def main():
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    q = c.execute
    rows = []
    for sk, name in SOURCES.items():
        for ts, ct in q("select ts, content from messages where session_key=? order by ts", (sk,)):
            if not ct:
                continue
            kind, direction, summary = classify(ct)
            rows.append({
                "时间": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                "来源": name,
                "类型": kind,
                "方向": direction,
                "金额": ("%.2f" % amount_of(ct)) if amount_of(ct) is not None else "",
                "摘要": summary,
                "商户": merchant_of(ct),
                "原文": ct.replace("\n", " ")[:300],
            })
    rows.sort(key=lambda r: r["时间"])
    c.close()

    # 写 CSV
    fp = os.path.join(OUT, "payment_flow.csv")
    with io.open(fp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["时间", "来源", "类型", "方向", "金额", "摘要", "商户", "原文"])
        w.writeheader()
        w.writerows(rows)

    # 统计
    L = []
    W = L.append
    W("支付/消费流水统计（数据源：微信内官方推送号 · 全本地）")
    W("=" * 64)
    W("总条数: %d" % len(rows))
    W("时间范围: %s → %s" % (rows[0]["时间"][:10], rows[-1]["时间"][:10]))
    W("")
    W("按来源:")
    for k, v in Counter(r["来源"] for r in rows).most_common():
        W("  %-10s %5d" % (k, v))
    W("")
    W("按方向:")
    for k, v in Counter(r["方向"] for r in rows).most_common():
        W("  %-6s %5d" % (k, v))
    W("")
    W("按类型 TOP15:")
    for k, v in Counter(r["类型"] for r in rows).most_common(15):
        W("  %-14s %5d" % (k, v))
    W("")

    # 支出合计（仅"支出"方向且有金额）
    exp = [float(r["金额"]) for r in rows if r["方向"] == "支出" and r["金额"]]
    inc = [float(r["金额"]) for r in rows if r["方向"] == "收入" and r["金额"]]
    W("支出类可解析金额: %d 笔" % len(exp))
    W("  支出合计 ¥%s" % format(sum(exp), ",.2f"))
    W("  收入合计 ¥%s（退款+返利+收款）" % format(sum(inc), ",.2f"))
    W("")

    W("逐月（全部来源 · 条数 / 支出金额）:")
    bym_n = Counter(); bym_e = defaultdict(float)
    for r in rows:
        m = r["时间"][:7]
        bym_n[m] += 1
        if r["方向"] == "支出" and r["金额"]:
            bym_e[m] += float(r["金额"])
    for m in sorted(bym_n):
        W("  %s  %4d 条   支出 ¥%s" % (m, bym_n[m], format(bym_e[m], ",.2f")))
    W("")

    W("=" * 64)
    W("★ 信用/债务类提醒（美团月付线 · 全新发现）")
    W("=" * 64)
    for r in rows:
        if r["类型"] in ("还款提醒", "还款成功", "扣款失败", "额度变动"):
            W("  [%s] %-8s %-10s %s" % (r["时间"][:10], r["来源"], r["类型"], r["原文"][:96]))
    W("")

    W("=" * 64)
    W("★ 含商户/商品名的记录（可用于归类消费结构）")
    W("=" * 64)
    for r in rows:
        if r["商户"]:
            W("  [%s] ¥%-9s %s" % (r["时间"][:10], r["金额"] or "-", r["商户"]))

    sp = os.path.join(OUT, "payment_flow_stats.txt")
    io.open(sp, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:60]))
    print("\n→ CSV: %s" % fp)
    print("→ 统计: %s" % sp)

if __name__ == "__main__":
    main()
