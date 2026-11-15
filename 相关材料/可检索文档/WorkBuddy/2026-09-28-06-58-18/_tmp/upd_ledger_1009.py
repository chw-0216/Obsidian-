# -*- coding: utf-8 -*-
import sqlite3, datetime, re
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\analysis.sqlite"
c = sqlite3.connect(DB)
now = "2026-10-09 09:00"

# ---------- 1. hypotheses 新增 5 条 ----------
H = [
 ("hyp:chenye-academic-question",
  "2026-10-08 22:06 陈晔**第一次向他提学术问题**（「Aigc 审美具备边际效应递增吗」）—— 全库 7,281 条里极罕见的「她问他」。截至 10-09 09:00 已 11 小时未答（他只回「我研究研究老师」）→ 这是本线**唯一会过期**的机会窗口。",
  "10-08 22:06 她发链接 +「Aigc 审美具备边际效应递增吗」；22:25 我「我研究研究老师」+ 两张图；22:32 她「这拍了what [捂脸][捂脸][捂脸]」",
  "全库导师线 7,281 条中，「她主动提问学术问题」此前无同类记录；她同时段唯一话题即为该问题（同夜再无其他事务指令）",
  "若她随后自己回答了该问题、或转给他人、或该问题是转发他人的，则「机会窗口」性质减弱",
  "① 他是否在 10-09 内作答 ② 她是否追问 ③ 该问题是否出现在他的研究/作业产出里",
  "学业+创作", "open", "05-纠偏层 三·补·53"),

 ("hyp:xiaoyi-action-fulfilled",
  "10-07 笑一的核心不满是「见不到任何行动的」「说的话做不到」；**10-08 他给出了可被观察到的行动**（16:40 约 → 17:13 见面 → 10-09 01:18 送回，共约 8.5 小时），她主动说「爱你老公」→ **要求已兑现**。",
  "10-08 16:32「宝贝怎么说」/16:37「我在西北门这边」「不用化妆了宝贝」/16:40「出去转转」「蓝港」/17:13 她「五分钟来」/17:25 语音通话/10-09 01:18 她「我进来了宝贝」→ 她「爱你老公」",
  "10-07 她要「可验证的行动」；10-08 他当天即执行（不是承诺）；她次日凌晨主动说「爱你老公」+「你也早点休息明天还去上课」",
  "若他 10-08 实际未见面（纯线上），或她随后仍提「见不到行动」，则本假设需修正",
  "① 下次约会是否准时 ② 他「下次我回来早些」这条新承诺是否兑现 ③ 她是否再提「落空」",
  "关系+方法论", "confirmed", "05-纠偏层 三·补·53"),

 ("hyp:cashflow-1010-chain",
  "10-08 一天的现金流链条（转账 + 微信支付双证据）：**先向舒泽林借 300 → 再向母亲分两次要 200+250=450 → 当晚在蓝色港湾「丝芙兰」消费 ¥630**。→ 「没有稳定收入」的最硬实证。",
  "16:52 我「想借 200 明天还能成吗」→ 16:53 舒转账 300；18:12 我「老妈能要 100 吗」「学校吃个饭」→ 18:13 母转 200；18:17 我「老妈能再要 250 元吗」「还个钱」→ 18:17 母转 250；微信支付 18:20 ¥680 → 18:22 退款 → 18:23 ¥630「丝芙兰北京蓝色港湾店」",
  "微信支付流水（同一日）与转账记录在时间上首尾相接；两笔向母亲的请求间隔 5 分钟，第二笔明说「还个钱」",
  "若那 300 并非当日归还、或 450 元另有用途，则链条需修正",
  "① 那 300 是否当日/次日归还 ② ¥630 的实际用途 ③ 10 月现金流的月度总量",
  "现金流", "confirmed", "05-纠偏层 三·补·53"),

 ("hyp:chenwen-revival",
  "陈昶文线 2026-07/08/09 **三个月归零**后，于 10-08 下午**复活 107 条**，且**气氛毫无隔阂**（开口第一句「八百年没见了」→ 立刻恢复打闹）→ 支持「归零不是关系破裂」。",
  "按月：2025-12 3,137（峰）→ 2026-01 1,444 → 02 108 → 03 312 → 04 62 → 05 673 → 06 539 → 07/08/09 = 0 → 10-08 107",
  "10-08 15:42 他「卧槽」「八百年没见了」「你来了？」；15:56「天下第一帅」；16:34「我靠滚蛋哈哈哈哈哈哈」——全程无一句解释、无一句问责",
  "若 07–09 的归零有明确的外部原因（如他出国/换号/冲突），则「非关系破裂」的读法需补充限定",
  "① 07–09 归零的原因（**数据不说，不得推断**）② 是否形成新的联系节奏",
  "关系", "open", "05-纠偏层 三·补·53"),

 ("hyp:chuanmei-toolbox",
  "10-08 20:15 母亲说「你去传媒的工具盒没带。在桌子上」→ 10-09 上课的**教具可能没带**；但 10-09 08:21 他称「在了已经」（在教室）→ 工具盒是否最终带到，**数据无法判定**。",
  "10-08 20:15 母「浩文：你去传媒的工具盒没带。在桌子上」；22:48 母「工具盒我要不要给你送去[抱拳][爱心]」；10-09 08:03 母「到了」；08:21 我「在了已经」",
  "「在了已经」只证明他到教室，不证明工具盒带到；母亲 20:15 的陈述与 10-09 早上的信息之间无中间确认",
  "若他 10-09 上课实际使用了自己/别人的设备，则「忘带」成立但后果轻微",
  "① 工具盒最终是否带到 ② 母亲说的「工具盒」是否＝「交互盒子」（Arduino 套件）③ 母亲 10-09 早上是否也去了中传",
  "学业+家庭", "open", "05-纠偏层 三·补·53"),
]
for h in H:
    c.execute("insert or replace into hypotheses "
      "(hyp_id,statement,about_event,supports,counters,discriminating_obs,cross_domains,status,source_doc,created_at,updated_at) "
      "values (?,?,?,?,?,?,?,?,?,?,?)", h + (now, now))

# ---------- 2. decisions 新增 2 条 ----------
D = [
 ("dec:20261009-aigc-question",
  "陈晔 10-08 22:06 问「Aigc 审美具备边际效应递增吗」，他回了「我研究研究老师」但未作答。今天要不要给答案？",
  "兑现「我研究研究」+ 抓住导师首次提问的窗口 + 不让她觉得问了没用",
  "A 今天上午先给一段有观点的短答（先结论后论据）+ 说明后续会做实证（推荐）/ B 等做出完整材料再答 / C 不再提",
  "", "", "① 今天是否作答 ② 她是否回应 ③ 是否追问细节",
  "", "open", "", "", now, now),
 ("dec:20261009-xiaoyi-next",
  "10-08 已兑现一次「可被观察到的行动」，但结尾又给了新承诺「下次我回来早些」。下一步怎么走？",
  "把一次性行动变成稳定预期（10-07 的失效模式是「说的话做不到」）",
  "A 主动定死下一次时间并提前 24h 确认（推荐）/ B 等她提 / C 只维持日常聊天",
  "", "", "① 下次见面是否准时 ② 她是否再提「落空」",
  "", "open", "", "", now, now),
]
for d in D:
    c.execute("insert or replace into decisions "
      "(dec_id,question,goal,options,chosen,why,expected,outcome,status,decided_at,reviewed_at,created_at,updated_at) "
      "values (?,?,?,?,?,?,?,?,?,?,?,?,?)", d)

# ---------- 3. persons note 刷新 ----------
for tk, note in [
 ("deerluna",            "n=7281 me_pct=65.3 last=2026-10-08 22:33"),
 ("wxid_wdnk6ue9kiyn22", "n=6646 me_pct=52.5 last=2026-10-09 01:21"),
 ("wxid_0gb0smyjaoyk22", "n=6382 me_pct=45.4 last=2026-10-08 16:35 · ★07-09归零后10-08复活107条"),
 ("wxid_0ejd54z34nmv32", "n=1820 me_pct=64.3 last=2026-10-09 00:40"),
 ("wxid_1wa75s1kze3o22", "n=16497 me_pct=45.3 last=2026-10-09 08:23"),
 ("guo647789",           "n=48 me_pct=64.6 last=2026-10-09 08:59 · 李老师(海燕)·中传交互技术课"),
]:
    r = c.execute("select note from persons where talker=?", (tk,)).fetchone()
    if r:
        old = r[0] or ""
        new = re.sub(r"^n=\d+ me_pct=[\d.]+ last=[\d\-: ]+", note, old)
        if new == old:
            new = note + (" | " + old if old else "")
        c.execute("update persons set note=? where talker=?", (new, tk))
        print("  persons ok:", tk)
    else:
        print("  persons 缺:", tk)

# ---------- 4. sources last_ok ----------
for sid in ["wechat:index.sqlite","engine:00-真相源·数字基准.md","engine:04-人际地图.md","engine:05-纠偏层.md"]:
    c.execute("update sources set last_ok=? where source_id=?", (now, sid))
c.commit()

print("=" * 60)
print("hypotheses", c.execute("select count(*) from hypotheses").fetchone()[0])
for r in c.execute("select status,count(*) from hypotheses group by status"): print("  ", r)
print("decisions", c.execute("select count(*) from decisions").fetchone()[0],
      "| open", c.execute("select count(*) from decisions where status='open'").fetchone()[0])
print("sources", c.execute("select count(*) from sources").fetchone()[0])
print("persons", c.execute("select count(*) from persons").fetchone()[0])
print("aliases", c.execute("select count(*) from aliases").fetchone()[0])
print("procedures", c.execute("select count(*) from procedures").fetchone()[0])
