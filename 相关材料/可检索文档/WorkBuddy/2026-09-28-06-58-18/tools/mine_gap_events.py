# -*- coding: utf-8 -*-
"""
mine_gap_events.py —— 补抽 2026-07 → 2026-10 的事件缺口

背景：事件库在 2026-07 之后密度断崖（08=2.9、09=1.6 事件/千条消息，常态 ~9）。
      旧抽取源（远程 v3 标注）已停，且违反数据主权 → 改为**本地规则抽取**。

做法：按「会话 × 天」聚合，命中「事件动词」才成候选；标注来源（会话+时间）+ 确定性。
      **候选 ≠ 已核实**：一律标「待核实」，供人工过一遍。

输出：
  _tmp/gap_events_2026H2.csv   —— 候选事件（date / 会话 / 类别 / 摘要 / 证据时间 / 确定性）
  _tmp/gap_daily.csv           —— 缺口窗口逐日：消息数 / 候选数 / 活跃会话数

只读 index.sqlite。用法：python tools\\mine_gap_events.py
"""
import os, io, re, csv, sqlite3, sys, datetime
from collections import defaultdict, Counter

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TMP = os.path.join(WS, "_tmp")
INDEX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
# ★ 索引库里「本人发的消息」role = **me**（不是 self！取值只有 me / them / system）
SELF = "wxid_zn4ozsnn8esr21"

START = "2026-07-01"
END = "2026-10-05"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 刷屏群（他 0 发言，已知噪音）
NOISE_SESSIONS = {"25410000808@chatroom", "18440588614@chatroom"}

# 系统/服务账号（不是真人对话；支付流另有专表）
SYS_NAMES = {"微信支付", "微信团队", "服务通知", "美团", "美团金融服务", "微信运动",
             "文件传输助手", "微信公众平台", "腾讯新闻", "订阅号消息", "微信收款助手",
             "微信支付凭证", "QQ邮箱提醒", "微信安全中心"}

# ── 强事件动词：命中即「真有事发生」 ──────────────────────────
STRONG = re.compile(
    r"决定|确定|定了|定下来|敲定|拟录取|录取|录用|面试|答辩|开题|提交|交了|报名|"
    r"入职|离职|辞职|转正|offer|签了|签合同|"
    r"开幕|开展|布展|撤展|发布|上线|结课|期末|毕业|立项|审批|通过了|没通过|驳回|"
    r"住院|手术|体检|挂号|复诊|搬家|提车|买车|退租|"
    r"出发|抵达|回京|返程|下乡|驻村|出差|"
    r"吵架|冷战|生气|和好|分手|复合|表白|同居|报警|事故|剐蹭|赔偿")

# ── 弱事件动词：需与强动词或长对话共存 ────────────────────────
WEAK = re.compile(
    r"见面|见了|见一下|借钱|借款|借点|借了|还钱|还上|还清|还款|逾期|欠款|欠了|"
    r"报销|经费|结算|合同|报价|谈事|聊了|开会|汇报|思想汇报|评审|丢了|坏了|修车")

# ── 噪音：命中即丢 ────────────────────────────────────────────
NOISE = re.compile(
    r"撤回了一条消息|拍一拍|红包|收款到账|支付成功|余额不足提醒|"
    r"新年|春节|节日|祝福|投票|助力|砍价|拼团|优惠|秒杀|促销|"
    r"语音通话|视频通话|未接通|已取消|无法显示|发送了图片|分享了一首")

CAT = [
    ("钱/财务",   r"转账|还款|逾期|扣款|欠款|借款|网贷|分期|账单|学费|报销|经费|结算|还钱|还清|借了"),
    ("学业/学术", r"导师|论文|开题|答辩|课程|作业|成绩|奖学金|入党|思想汇报|结课|期末|录取|毕业"),
    ("项目/实践", r"井邻|洞台|乡村美育|工作站|立项|合作|方案|甲方|客户|布展|拍摄|发布|展览"),
    ("求职/职场", r"实习|录用|面试|入职|离职|辞职|转正|offer|简历|工资|课酬"),
    ("家庭",     r"父母|爸爸|妈妈|家里|冷战|奶奶|小姑|房租|望京|我妈|我爸"),
    ("亲密关系", r"同居|老公|老婆|女朋友|相亲|约会|分手|复合|表白|接机"),
    ("出行/迁移", r"出发|抵达|回京|返程|机票|高铁|下乡|驻村|出差|云南|澜沧|怀柔|承德"),
    ("社交/见面", r"聚会|聚餐|见面|喝酒|校友|联谊|婚礼|生日|看展"),
    ("生活/事务", r"住院|手术|体检|挂号|搬家|提车|买车|维修|快递|钥匙|赔偿|事故|剐蹭"),
]


def cat_of(text):
    for name, kw in CAT:
        if re.search(kw, text):
            return name
    return "待定"


def main():
    con = sqlite3.connect("file:" + INDEX.replace("\\", "/") + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    names = {r["talker"]: (r["display_name"] or r["talker"])
             for r in con.execute("select talker,display_name from sessions")}
    types = {r["talker"]: r["session_type"] for r in con.execute("select talker,session_type from sessions")}

    t0 = int(datetime.datetime.strptime(START, "%Y-%m-%d").timestamp())
    t1 = int(datetime.datetime.strptime(END, "%Y-%m-%d").timestamp()) + 86400

    # (session, day) -> [rows]
    buckets = defaultdict(list)
    day_tot = Counter()
    for r in con.execute(
            "select session_key,ts,role,content from messages where ts>=? and ts<? order by ts", (t0, t1)):
        sk = r["session_key"]
        if sk in NOISE_SESSIONS:
            continue
        if types.get(sk) == "公众号" or sk.startswith("gh_") or "biz" in (sk or ""):
            continue
        day = datetime.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d")
        buckets[(sk, day)].append(r)
        day_tot[day] += 1
    con.close()

    events = []
    for (sk, day), rows in buckets.items():
        sname = names.get(sk, sk)
        if sname in SYS_NAMES:            # 系统账号 → 不进事件层（支付流另有专表）
            continue
        if len(rows) < 4:                 # 太短不成事件
            continue
        stype = types.get(sk, "")
        # 剔除链接转发 / 群公告 / 加好友提示 —— 这些不是「他的事件」
        rows = [r for r in rows
                if not re.search(r"https?://|mp\.weixin\.qq\.com|view \d|"
                                 r"我通过了你的朋友验证请求|@openim|阅读原文", r["content"] or "")]
        if len(rows) < 4:
            continue
        text = "\n".join((r["content"] or "") for r in rows)
        if NOISE.search(text) and not STRONG.search(text):
            continue
        s_hits = [r for r in rows if STRONG.search(r["content"] or "")]
        w_hits = [r for r in rows if WEAK.search(r["content"] or "")]
        mine_hits = [r for r in (s_hits or w_hits) if r["role"] == "me"]
        if stype == "群聊":
            # 群聊：必须**他自己**说了强事件词（否则是别人在群里发生的事）
            if not [r for r in s_hits if r["role"] == "me"] or len(rows) < 8:
                continue
        else:
            if not s_hits and not (w_hits and len(rows) >= 12):
                continue
        hits = s_hits or w_hits
        mine = mine_hits
        pick = (mine or hits)[:4]
        if not pick:
            continue
        excerpt = " ｜ ".join(
            ("我：" if r["role"] == "me" else "") + re.sub(r"\s+", " ", (r["content"] or ""))[:90]
            for r in pick)
        ts0 = min(r["ts"] for r in rows)
        ts1 = max(r["ts"] for r in rows)
        hm = (datetime.datetime.fromtimestamp(ts0).strftime("%H:%M") + "–" +
              datetime.datetime.fromtimestamp(ts1).strftime("%H:%M"))
        score = (2 if s_hits else 0) + (2 if mine else 0) + min(len(rows) // 8, 3)
        events.append({
            "date": day,
            "time": hm,
            "session": sname,
            "session_type": stype,
            "session_key": sk,
            "msg_n": len(rows),
            "score": score,
            "category": cat_of(text),
            "excerpt": excerpt[:400],
            "certainty": "确定（有明确日期）",
            "review_status": "待核实",
        })

    # 每天最多 6 条（按 score 取高），避免刷屏会话灌满
    by_day = defaultdict(list)
    for e in events:
        by_day[e["date"]].append(e)
    events = []
    for d in sorted(by_day):
        pick = sorted(by_day[d], key=lambda x: (-x["score"], -x["msg_n"]))[:6]
        events.extend(sorted(pick, key=lambda x: x["time"]))

    events.sort(key=lambda e: (e["date"], e["time"]))
    with io.open(os.path.join(TMP, "gap_events_2026H2.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(events[0].keys()))
        w.writeheader()
        w.writerows(events)

    # 逐日
    days = sorted(day_tot)
    cand_by_day = Counter(e["date"] for e in events)
    sess_by_day = defaultdict(set)
    for e in events:
        sess_by_day[e["date"]].add(e["session_key"])
    with io.open(os.path.join(TMP, "gap_daily.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "消息数", "候选事件数", "活跃会话数"])
        for d in days:
            w.writerow([d, day_tot[d], cand_by_day.get(d, 0), len(sess_by_day.get(d, ()))])

    print("窗口 %s → %s" % (START, END))
    print("候选事件 %d 条 ｜ 覆盖 %d 天 ｜ 活跃会话 %d 个" % (
        len(events), len(cand_by_day), len({e["session_key"] for e in events})))
    print("\n按类别：")
    for k, v in Counter(e["category"] for e in events).most_common():
        print("  %-10s %4d" % (k, v))
    print("\n按月：")
    for k, v in sorted(Counter(e["date"][:7] for e in events).items()):
        print("  %s  %4d" % (k, v))
    print("\n零候选日（消息>0）：")
    zero = [d for d in days if day_tot[d] > 200 and cand_by_day.get(d, 0) == 0]
    print("  共 %d 天：%s" % (len(zero), " ".join(zero[:30])))
    print("\n→ _tmp\\gap_events_2026H2.csv / gap_daily.csv")


if __name__ == "__main__":
    main()
