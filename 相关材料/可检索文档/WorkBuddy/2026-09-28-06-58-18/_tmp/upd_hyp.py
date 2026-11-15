# -*- coding: utf-8 -*-
import sqlite3, datetime
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
c = sqlite3.connect('analysis.sqlite')

# 1) 修正：原 supports 误把「笑一周一周二上课」当成了他的排班印证（实为笑一自己的课表）
c.execute("update hypotheses set statement=?, supports=?, counters=?, discriminating_obs=?, updated_at=? "
          "where hyp_id='hyp:linfen-time-conflict'",
          ("临汾落地训练营（她 09-15 说模板为「5 天」）与我 09-24 对她说过的「美术馆排班周一到周四在」几乎必然撞车——工作日白天被实习占死，5 天不可能全落在周末。",
           "★唯一硬证据：我 2026-09-24 17:04 主动对她说「我跟美术馆确认排班周一到周四在」（我自己报的约束，不是她问出来的）；"
           "09-24 16:36 我还说过实习「要求每周去四天，可能会比较占时间就钉在学校了」。"
           "⚠️ 更正：此前引用的「笑一 10-07 19:20 印证」属误读——原话是我问她「你明天是不是周五周一周二要去学校上课」，"
           "她答「周一周二去」，那是笑一自己的课表，与他无关，已剔除。",
           "若落地赛只去 1–2 天 / 排在周末 / 美术馆可调班 / 她本来就只让他去部分天数，则冲突不成立",
           "落地赛的具体日期与天数（她拉群或私聊告知的行程表）；以及我 10-08 之后有没有跟她提过排班",
           now))

# 2) 修正：她不是只「给标准」，紧接着就派了具体活 → 改为「看现场 + 派活」双动作
c.execute("update hypotheses set statement=?, supports=?, counters=?, discriminating_obs=?, updated_at=? "
          "where hyp_id='hyp:linfen-video-standard'",
          ("她发《绝对者》（786s 视频号）+「去山西做东西要考慮运镜」不是纯「给标准/给资料」，而是「让你看现场 + 顺手派活」——两条动作前后只隔 2 小时（07:43 发片 → 09:52 派活）。",
           "★决定性新证据：2026-10-08 09:52 她紧接着发「你的版画工坊出2分鐘的視頻嗎」+「不要生成的」；"
           "同一模式在 2026-05-29 出现过（她发工作站施工进度 87s → 派现场活）；"
           "09-25 18:44→19:26 也是（「你的版画工坊到现在都没有一个宣传啊」→「你搞个小结式的视频推送，1分钟」）",
           "若她 10-08 之后再无追加交付要求，且只追问「片子看了有什么想法」，则更接近纯给资料",
           "她接下来 24–48h 是否继续加派具体活 / 是否只问「看了吗」",
           now))

NEW = [
 dict(hyp_id="hyp:video-not-generated",
   statement="她 10-08 09:52 那句「不要生成的」＝明确排斥 AIGC 生成画面，要的是实拍质感——这与他 09-24 主动向她推销的「用 AI 修复照片做像素化效果」方案正好相反。",
   about_event="2026-10-08 09:52「不要生成的」↔ 2026-09-24 16:15/16:36 我「用显影药水有个优势可以用 ai 修复照片然做像素化效果」/「扫描→AI做像素化修复→打印机输出」",
   supports="★她那句紧跟「你的版画工坊出2分鐘的視頻嗎」出现，是在给交付下限定条件；她 07:43 发的《绝对者》本身是 AI 题材但成片运镜是实拍级的",
   counters="若她后来又说「AI 效果也行 / 可以加点生成」，则本假设证伪",
   discriminating_obs="我下一版交出去的东西里有没有 AI 生成/修复的画面，她是否点出来",
   cross_domains="创作+关系", source_doc="决策中枢 2026-10-08"),
 dict(hyp_id="hyp:workshop-video-overdue",
   statement="「版画工坊 2 分钟视频」是从 2026-09-25 起就该交、拖了 13 天、被催过 2 次的活——它不是新任务，是旧欠账；她把时长从「1 分钟」提到「2 分钟」＝催得更具体，不是新需求。",
   about_event="09-25 18:44「你的版画工坊到现在都没有一个宣传啊，你得做一期呀」→ 09-25 19:26「你搞个小结式的视频推送」「1分钟」→ 09-30 14:05「版画工作坊的视频你做好了吗？」→ 10-08 09:52「你的版画工坊出2分鐘的視頻嗎」",
   supports="★四次记录完整可查；我 09-30 两次答「正在做/我抓紧/这两天加速应该有成果」——承诺过一次，仍未交；时长 1→2 分钟说明她记得并加码",
   counters="若我 09-30 至 10-08 之间已私下交付过（如微信文件/线下给看），则本假设证伪",
   discriminating_obs="09-30 至今我是否发过任何视频文件给陈晔（含 tvideo 类消息）",
   cross_domains="学业+创作", source_doc="决策中枢 2026-10-08"),
]
for h in NEW:
    c.execute("insert or replace into hypotheses "
              "(hyp_id,statement,about_event,supports,counters,discriminating_obs,status,cross_domains,source_doc,created_at,updated_at) "
              "values (?,?,?,?,?,?,?,?,?,?,?)",
              (h["hyp_id"], h["statement"], h["about_event"], h["supports"], h["counters"],
               h["discriminating_obs"], "open", h["cross_domains"], h["source_doc"], now, now))

# 3) 更新 hub 决策：现在被追的是「两件活 + 一个未知」
q = ("【当前节点】陈晔 10-08 两条线同时压过来：① 版画工坊 2 分钟视频（09-25 起欠 13 天，已催 2 次，且新增「不要生成的」限定）"
     "② 临汾落地赛（10 月·模板 5 天，与我美术馆实习周一到周四在岗冲突，日期未知）。我该先回什么、什么时候回、用什么口径？")
o = ("A 今天回「视频+运镜一起交」（推荐）：把 2 分钟视频当成今天的头号交付，同时把已答应的运镜整理一并发出；"
     "顺势问「落地赛具体几号、几天？群拉了吗？」；用「跟美术馆调一下排班」而不是「请假」的口径把约束摆出来｜"
     "B 先交运镜（已在 09:49 承诺），视频往后拖｜"
     "C 先只问日期与群，两件活都不提")
w = ("A 的理由：09:49 已说「运镜我拆一下」，不交＝第二次空口；视频已欠 13 天且被催 2 次，再拖会把她 09-25 那句「你得做一期呀」变成第三次催——"
     "导师线里「答应的没做」比「做得不够好」更伤。而「调排班」与「请假」是两个完全不同的信号：调排班＝我在安排，请假＝我在缺席。"
     "B 的风险：视频是旧账，先交新账会显得在挑好做的做。C 的风险：两件都不提只问日期，等于承认两件都没做。")
e = "① 她是否确认视频交付时间 ② 落地赛日期与天数 ③ 群是否拉 ④ 她是否再提「不要生成的」的边界"
c.execute("update decisions set question=?, options=?, why=?, expected=?, updated_at=? where dec_id='dec:20261008-linfen-hub'",
          (q, o, w, e, now))

c.commit()
print("hypotheses:", c.execute("select count(*) from hypotheses").fetchone()[0])
print("decisions :", c.execute("select count(*) from decisions").fetchone()[0])
for r in c.execute("select hyp_id,status from hypotheses where hyp_id like 'hyp:linfen%' or hyp_id like 'hyp:video%' or hyp_id like 'hyp:workshop%'"):
    print("  ", r)
c.close()
