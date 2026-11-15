# -*- coding: utf-8 -*-
"""2026-10-08 微信同步后的状态更新：陈晔线闭环 + 笑一线新事实"""
import sqlite3, datetime
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
c = sqlite3.connect('analysis.sqlite')

# ============ ① 陈晔线：状态翻转 ============
# 1.1 「不要生成的」已由本人 10:06 正面确认 → 假设结
c.execute("""update hypotheses set
  statement=?,
  supports=?,
  counters=?,
  discriminating_obs=?,
  status=?,
  updated_at=?
  where hyp_id='hyp:video-not-generated'""",
 ("她 10-08 09:52 那句「不要生成的」＝明确排斥 AIGC 生成画面，要实拍质感。"
  "★ 已由本人 2026-10-08 10:06 正面确认：我回「用实拍照片和现场素材剪，不生成」——"
  "这条假设的两层含义里，第一层（不要 AI 生成画面）成立且我已按此承诺。",
  "★决定性证据：我 2026-10-08 10:06:36 原话「老师，能出，两分钟。用实拍照片和现场素材剪，不生成」"
  "—— 我主动复述了她的限定条件并承诺遵守，等于双方对交付形态达成一致；她 10:07:28 回「橫屏」＝接受这个前提后只补规格。",
  "若她后续又说「AI 效果也行 / 可以加点生成」，则本假设证伪",
  "已判别完毕。第二层（是否指向我 09-24 提的「AI 修复照片」方案）仍需本人确认",
  "confirmed", now))

# 1.2 版画工坊视频欠账 + 新增期限
c.execute("""update hypotheses set
  statement=?,
  supports=?,
  counters=?,
  discriminating_obs=?,
  status=?,
  updated_at=?
  where hyp_id='hyp:workshop-video-overdue'""",
 ("「版画工坊 2 分钟视频」是从 2026-09-25 起就该交、拖了 13 天、被催 2 次的旧欠账。"
  "★ 2026-10-08 已闭环：我 10:06 承诺「这周做一下」，她 10:07 定规格「橫屏」→ "
  "**本周末（10-11）前是硬期限，且用途已明确为横屏现场播放**。",
  "四次催收记录完整；★我 10-08 10:06:36 承诺「这周做一下」+ 她 10:07:28「橫屏」＝期限与规格同时确定。"
  "硬证据：09-30 至 10-08 我发给她 type='video' 的消息只有 10-03 的 4 条手势演示，确实未交。",
  "若我 10-08 至 10-11 之间未交，则「这周做一下」成为第二次空头承诺",
  "10-11 前我是否发出横屏 2 分钟视频",
  "confirmed", now))

# 1.3 脚本回避假设：补反证（对视频不回避，对脚本仍回避）
c.execute("""update hypotheses set
  supports=?,
  counters=?,
  updated_at=?
  where hyp_id='hyp:linfen-script-avoidance'""",
 ("09-19 19:54 承诺「这两天给您初稿」至今未兑现；09:49 回复全文无「脚本」二字。"
  "★新增关键分化：我 10-08 10:06:36 对「版画工坊视频」是**正面处理**（确认能出/给期限/问用途），"
  "但对「临汾脚本」从 09-19 起 19 天只字未提 → 回避是**脚本专属**，不是对导师的普遍回避。",
  "★反证（部分）：10-08 10:06 我主动回复并给出交付期限，证明我不回避她派的活；"
  "→ 本假设收窄为「只回避脚本这一件」，不成立为「回避导师」。若我 10-09 前主动提「脚本」，则整条证伪。",
  now))

# 1.4 她发片=看现场+派活 → 补 10-07 秒回证据
c.execute("""update hypotheses set
  supports=?,
  updated_at=?
  where hyp_id='hyp:linfen-video-standard'""",
 ("★决定性证据：10-08 07:43 发《绝对者》→ 09:52 派活 → 我 10:06 回 → 她 10:07:28 **秒回「橫屏」**（22 分钟内）。"
  "「秒回一个具体规格」＝她在盯着这件事的落地，不是随手给资料。"
  "同一模式在 2026-05-29（发工作站施工 87s → 派现场活）、09-25（催宣传片 → 定 1 分钟）都出现过。",
  now))

# 1.5 新增：横屏=现场放
NEW_HYP = [
 dict(hyp_id="hyp:chenye-horizontal-screen",
   statement="她 10-08 10:07 只答「橫屏」＝该视频用途是**现场播放**（大屏/投影），不是公众号推文；"
             "我 10:06 问的「发公众号还是现场放」在她那里等价于「定横竖屏」。",
   about_event="2026-10-08 10:06 我「是发公众号还是现场放？我按用途定横竖屏」→ 10:07 她「橫屏」",
   supports="她直接跳到答案（横屏）而不回答「公众号还是现场」→ 说明在她心里用途已经确定，只差把规格告诉我；"
            "横屏是现场/大屏的默认规格（公众号图文通常竖屏或两者皆可）",
   counters="若后续她说「也发公众号」或视频实际出现在公众号推文里，则本假设证伪",
   discriminating_obs="视频最终出现在哪里（版画工坊现场 / 公众号 / 其他）",
   cross_domains="学业+创作", source_doc="微信同步 2026-10-08"),
 dict(hyp_id="hyp:xiaoyi-action-gap",
   statement="笑一 2026-10-07 的核心不满不是「你不关心我」，而是「**你说的做不到 / 我看不到行动**」"
             "——她要的是可验证的行动，不是情绪安抚。",
   about_event="2026-10-07 18:44–19:43 笑一会话一小时深度对话",
   supports="★原话密集且一致：「你有时候说的话做不到」/「我不喜欢被应付」/「总之是无法落地的」/"
            "「说的再好」/「我是见不到任何行动的」/「所以何时陪我」/「我不喜欢这种一直落空的感觉」/"
            "「下回约时间要很确定噢」；她甚至拿我自己的话反打：「答应我跟我吃饭」「又糊弄过去」。"
            "我的回应也是同向的：「就是知道你难受，但我没管你。这比单纯没察觉更伤人」「这个我认」。",
   counters="若她后续在别的场合表达的是「你不在乎我」这类情感需求，而非「你没做到」这类行动需求，则收窄",
   discriminating_obs="我 10-08 至 10-12 是否有**可被她观察到的具体行动**（接她 / 定死时间 / 兑现一件事）",
   cross_domains="关系+现金流", source_doc="微信同步 2026-10-08"),
 dict(hyp_id="hyp:xiaoyi-linlina",
   statement="笑一怀疑「林丽娜」仍在（她说「她不是你的前女友是你现女友吧」「现在？」），"
             "我称「已经断干净了」——这是 10-07 对话里唯一一个我主动交代、且她当场质疑的点。",
   about_event="2026-10-07 19:37–19:39 我主动说「之前那个林丽娜」→ 她追问「现在？」→ 我「已经断干净了」",
   supports="我主动开启这个话题（「我说一个事情，你可能会很生气」）说明我认为它有解释价值；"
            "她连问三次（「搞什么呢」「现在？」「那她挺能忍的」）说明她没被说服",
   counters="若全库无林丽娜的独立会话或近期往来痕迹，则「断干净」为真",
   discriminating_obs="索引库是否有 talker 指向林丽娜的会话，及其末次时间",
   cross_domains="关系", source_doc="微信同步 2026-10-08"),
]
for h in NEW_HYP:
    c.execute("insert or replace into hypotheses "
              "(hyp_id,statement,about_event,supports,counters,discriminating_obs,status,cross_domains,source_doc,created_at,updated_at) "
              "values (?,?,?,?,?,?,?,?,?,?,?)",
              (h["hyp_id"], h["statement"], h["about_event"], h["supports"], h["counters"],
               h["discriminating_obs"], "open", h["cross_domains"], h["source_doc"], now, now))

# ============ ② 决策：hub 回填 outcome ============
c.execute("""update decisions set
  outcome=?,
  status=?,
  decided_at=?,
  reviewed_at=?,
  updated_at=?
  where dec_id='dec:20261008-linfen-hub'""",
 ("★已按「推荐 A」的实质执行，且效果优于预期：我 2026-10-08 10:06:36 一条消息同时完成四件事——"
  "① 确认能出（兑现承诺）② 主动复述「不生成」（对齐她的限定）③ 反问用途（问出关键未知）"
  "④ 给出期限「这周做一下」。她 10:07:28 秒回「橫屏」，22 分钟内闭环。"
  "→ 视频交付：**规格=横屏 · 期限=本周末（10-11）**。"
  "→ 但「落地赛日期 + 群 + 脚本」三项**仍未问、仍未交**，下一轮头号动作转移到这里。",
  "closed", "2026-10-08", "2026-10-08", now))

# ============ ③ 新增决策 ============
NEW_DEC = [
 dict(dec_id="dec:20261008-workshop-video",
   question="版画工坊 2 分钟横屏视频——我 10-06 已承诺「这周做一下」，本周末（10-11）是硬期限。用什么素材、什么结构、在哪交付？",
   goal="兑现承诺（导师线）+ 不触碰「不要生成的」红线 + 顺便把洞台村现场的影像资产用起来",
   options=("A 实拍照片 + 现场素材剪辑（推荐，已向她承诺的口径）：用 09-25 至今洞台村/版画工坊的实拍照片与现场视频，"
            "做 2 分钟横屏小结片，本周内发出｜"
            "B 追加补拍：先回现场补一天素材再做｜"
            "C 只交粗剪：先给结构，等她反馈再精修"),
   chosen="", 
   why=("A 是唯一与她 10-07 07:43《绝对者》+ 09:52「不要生成的」两条指令同时对齐的方案："
        "实拍 = 不生成；2 分钟横屏 = 现场播。且我 10:06 已经用这个口径承诺过，改口径＝自己打脸。"
        "B 的风险：时间不够，周末前补拍未必排得开（周一至周四在美术馆实习）。"
        "C 的风险：她已催两次，「粗剪」容易被读成又一次拖延。"),
   expected="① 我是否在 10-11 前交出 ② 她是否接受 ③ 是否追加修改要求",
   outcome="", status="open"),
 dict(dec_id="dec:20261008-xiaoyi-promise",
   question="我 2026-10-07 19:31 对笑一承诺「明天如果顺利我来接你」+「我把事情推一推」，"
            "同时她说「下回约时间要很确定噢」。今天（10-08）要不要履约、怎么履约？",
   goal="把「说的做不到」这条核心指控用一次可验证的行动翻转掉（这是她自己给出的判别标准）",
   options=("A 今天按承诺去接 + 把下次时间**当场定死**（推荐）｜"
            "B 去接但不提下次时间｜"
            "C 说明理由改期，并当场定一个新的确定时间"),
   chosen="",
   why=("A 直接命中她的原话「我是见不到任何行动的」和「下回约时间要很确定噢」——"
        "一次「准时出现 + 当场定死下一次」能同时回应两条；"
        "B 只解决一半，下次仍会被问「所以何时陪我」；"
        "C 诚实但又一次是「说的」，她已明确说「说的再好我是见不到任何行动的」。"
        "★ 注意：我今天（10-08）有 09:53 已确认的「明早的课」要提前预约入校，接人时间需与之错开。"),
   expected="① 是否成行 ② 下次时间是否当场确定 ③ 她当晚的语气变化",
   outcome="", status="open"),
]
for d in NEW_DEC:
    c.execute("insert or replace into decisions "
              "(dec_id,question,goal,options,chosen,why,expected,outcome,status,decided_at,reviewed_at,created_at,updated_at) "
              "values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (d["dec_id"],d["question"],d["goal"],d["options"],d["chosen"],d["why"],d["expected"],
               d["outcome"],d["status"],"","",now,now))

c.commit()
print("hypotheses:", c.execute("select count(*) from hypotheses").fetchone()[0])
print("decisions :", c.execute("select count(*) from decisions").fetchone()[0])
for r in c.execute("select hyp_id,status from hypotheses order by hyp_id"):
    print("   H", r[0], r[1])
for r in c.execute("select dec_id,status from decisions order by dec_id"):
    print("   D", r[0], r[1])
c.close()
