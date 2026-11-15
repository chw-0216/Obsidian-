# -*- coding: utf-8 -*-
r"""debt_check.py —— 王逸伦 / 舒泽林 转账去重核对"""
import sqlite3, datetime, re
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

WHO = {"wxid_4e4mad0ve4fn22": "王逸伦", "wxid_0ejd54z34nmv32": "舒泽林"}

for sk, nm in WHO.items():
    print("=" * 76)
    print("【%s】全部「转账」相关消息（原始，未去重）" % nm)
    print("=" * 76)
    rows = con.execute(
        "select ts, role, content from messages where session_key=? and content like '%转账%' order by ts",
        (sk,)).fetchall()
    for r in rows:
        c = (r["content"] or "").replace("\n", " ")
        amt = re.search(r'([\d,]+\.\d{2})', c)
        cur = "￥" if "￥" in c else " "
        print("  %s  %-3s  %s%s" % (fmt(r["ts"]),
              "我" if r["role"] == "me" else "他",
              cur, amt.group(1) if amt else "?"))

    # ★ 去重：内容归一化（去掉 ￥ 与空格）+ 同一笔两行 → 按 (金额, 时间窗 ±5min) 归并
    print("\n  --- 去重后（同一笔转账微信记两行，时间差 < 3 分钟视为同一笔）---")
    seen = []
    for r in rows:
        c = (r["content"] or "").replace("￥", "").replace(" ", "")
        amt = re.search(r'([\d,]+\.\d{2})', c)
        a = amt.group(1) if amt else "?"
        dup = False
        for s in seen:
            if s["amt"] == a and abs(s["ts"] - r["ts"]) <= 180:
                s["rows"] += 1
                s["roles"].add(r["role"])
                dup = True
                break
        if not dup:
            seen.append(dict(ts=r["ts"], amt=a, rows=1, roles={r["role"]}))
    for s in seen:
        # 谁付钱：转账卡片在「谁的消息流里出现」= 收款人视角；
        # 但 index 里 role 是「本人视角」——role=me 表示这条卡片出现在本人消息里
        print("  %s  %s 元  (%d 行)" % (fmt(s["ts"]), s["amt"], s["rows"]))
    print()
