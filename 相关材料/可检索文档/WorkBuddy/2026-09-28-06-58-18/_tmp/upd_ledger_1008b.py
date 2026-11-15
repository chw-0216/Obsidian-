# -*- coding: utf-8 -*-
import sqlite3, datetime
DB = r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/analysis.sqlite"
c = sqlite3.connect(DB)
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------- 1. hypotheses 新增 3 条 ----------
H = [
 ("hyp:chuanmei-course-12w",
  "他自 2026-09-11 起在跟一门 12 周课程（地点被称作「传媒」，主讲李老师），由母亲牵线、王利敏联络，进出需提前预约「入校」+ 实名认证 → 这是「家庭关系网作为资源供给通道」的第 4 次使用（前三次：考央美兜底 / 安奇推荐信 / 母亲的车）。",
  "2026-09-11 王利敏加好友「我是王利敏」→ 同日转述李老师「她这个课是12周」「你妈妈特别希望你借这个机会把课程完整跟下来」→ 09-20「下次的课是10月9号上午」→ 10-08「记得明天上午的课」",
  "王利敏 09-11 13:19 原话含「你妈妈特别希望你借这个机会把课程完整跟下来」；09-18 原话「没有及时看到你妈妈发的信息」→ 母亲是开口的人；12 周 + 需预约入校 + 需实名认证 → 旁听性质，非学历",
  "若课程实际由他自己申请（非母亲牵线），或他实际注册为在读学生，则本假设证伪",
  "① 他是否出示过选课/注册凭证 ② 12 周结束后是否有学分或结业 ③ 王利敏与李老师是否与母亲直接认识",
  "学业+家庭", "open", "05-纠偏层 三·补·52"),
 ("hyp:chuanmei-interaction-device",
  "2026-09-20「老师已经给我设备了」「交互盒子」是他第一次被记录到接触交互设备 → 与其「交互装置（TouchDesigner / MediaPipe / Unity DMX）」方向吻合，是他交互能力的实物接触起点。",
  "2026-09-20 13:58 我「小王阿姨老师已经给我设备了」「很顺利」「交互盒子」「我研究一下」",
  "他主动汇报「已经给我设备了」并说「我研究一下」→ 对该设备有主动性；与其技能清单里的交互装置方向一致",
  "若该设备只是普通教具（非交互装置），或他只接触一次，则不构成「能力起点」",
  "后续是否出现该设备的作品/记录（照片、代码、视频、群内讨论）",
  "学业+创作", "open", "05-纠偏层 三·补·52"),
 ("hyp:wanglimin-no-note",
  "王利敏属于「有对价的关系」，但他没有为她写规程化备注 → 与「备注即规程」不矛盾：备注出现在「需要他自己维护」的关系上，而这条线由母亲转交、不需要他维护。",
  "他对王利敏用语「收到小王阿姨！」「感谢小王阿姨！！！」（与对陈晔「明白老师」同构），但通讯录无规程化备注",
  "三·补·17：全库 691 条真备注中，含「指令/自律」词的只有 1 条（陈晔）；王利敏 58 条全为礼仪性回复，无备注记录",
  "若通讯录中实际存在她的规程化备注（需查 contact.db 确认）则本假设证伪",
  "查 contact.db 中 a35599192 的 remark 字段",
  "关系+方法论", "open", "05-纠偏层 三·补·52 / 三·补·17"),
]
for h in H:
    c.execute("insert or replace into hypotheses "
      "(hyp_id,statement,about_event,supports,counters,discriminating_obs,cross_domains,status,source_doc,created_at,updated_at) "
      "values (?,?,?,?,?,?,?,?,?,?,?)", h + (now, now))

# ---------- 2. decisions 新增 1 条 ----------
D = [
 ("dec:20261009-chuanmei-class",
  "2026-10-09（明天）上午在中传有课，需① 完成「实名认证」② 提前预约入校。他 10-08 09:53 已答应「链接我这就认证，明早的课记着，约好回您」。今天要不要落地？",
  "兑现对王利敏的承诺 + 保证明天能进校 + 不辜负母亲的安排",
  "A 今天立刻做完认证+预约并回一条确认（推荐）/ B 只做不说 / C 明天早上现场处理",
  "", "", "① 是否今天完成认证与预约 ② 明天是否顺利入校上课 ③ 王利敏是否再催",
  "", "open", "", "", now, now),
]
for d in D:
    c.execute("insert or replace into decisions "
      "(dec_id,question,goal,options,chosen,why,expected,outcome,status,decided_at,reviewed_at,created_at,updated_at) "
      "values (?,?,?,?,?,?,?,?,?,?,?,?,?)", d)

# ---------- 3. persons 更新 ----------
row = c.execute("select * from persons where talker='a35599192'").fetchone()
print("a35599192 原记录:", row)
c.execute("""update persons set name=?, relation=?, distance=?, note=?
             where talker='a35599192'""",
  ("王利敏", "母亲牵线的课程联络人", "未标定",
   "n=58 me_pct=55.2 last=2026-10-08 10:19；★真名王利敏（2026-09-11 自报）；称呼「小王阿姨」；母亲牵线 → 中传 12 周课程联络人；主讲李老师；需提前预约入校；见 05 三·补·52"))

# 关键人 note 数字刷新
for tk, note in [
 ("wxid_1wa75s1kze3o22", "n=16377 me_pct=45.4 last=2026-10-07 18:18"),
 ("deerluna",            "n=7271 me_pct=65.3 last=2026-10-08 10:07"),
 ("wxid_wdnk6ue9kiyn22", "n=6579 me_pct=52.5 last=2026-10-07 19:43"),
 ("wxid_id1nfp5f20e122", "n=3013 me_pct=41.8 last=2026-09-16 23:54"),
 ("wxid_0ejd54z34nmv32", "n=1772 me_pct=64.3 last=2026-10-07 10:34"),
 ("filehelper",          "n=6547 me_pct=100.0 last=2026-10-08 12:29"),
]:
    r = c.execute("select note from persons where talker=?", (tk,)).fetchone()
    if r:
        old = r[0] or ""
        # 只替换开头的 n=... 段
        import re
        new = re.sub(r"^n=\d+ me_pct=[\d.]+ last=[\d\-: ]+", note, old)
        if new == old:
            new = note + (" | " + old if old else "")
        c.execute("update persons set note=? where talker=?", (new, tk))
        print("  persons 更新:", tk)
    else:
        print("  persons 缺:", tk)

# ---------- 4. aliases 新增 ----------
for al, pid, kind in [("王利敏", "a35599192", "真名"), ("小王阿姨", "a35599192", "称呼")]:
    c.execute("insert or replace into aliases(alias,person_id,kind) values(?,?,?)", (al, pid, kind))
    print("  alias 写入:", al)

# ---------- 5. sources 刷新 ----------
for sid, note in [("wechat:index.sqlite", "实时索引库"),
                  ("db:analysis.sqlite", "结缔组织库"),
                  ("engine:00-真相源·数字基准.md", "自我理解引擎"),
                  ("engine:04-人际地图.md", "自我理解引擎"),
                  ("engine:05-纠偏层.md", "自我理解引擎")]:
    c.execute("update sources set last_ok=? where source_id=?", (now, sid))
c.execute("""insert or replace into sources(source_id,kind,path,content_hash,first_seen,last_ok,privacy,note)
             values(?,?,?,?,?,?,?,?)""",
  ("wechat:live-json", "wechat",
   r"C:/Users/wardc/Desktop/07_聊天记录分析/weflow_live", "", now, now, "local_only",
   "gen_live_json.py 产物 · 三层同步第③层"))

c.commit()

# ---------- 汇总 ----------
print("=" * 60)
print("hypotheses", c.execute("select count(*) from hypotheses").fetchone()[0])
for r in c.execute("select status,count(*) from hypotheses group by status"): print("  ", r)
print("decisions", c.execute("select count(*) from decisions").fetchone()[0],
      "| open", c.execute("select count(*) from decisions where status='open'").fetchone()[0])
print("sources", c.execute("select count(*) from sources").fetchone()[0])
print("persons", c.execute("select count(*) from persons").fetchone()[0])
print("aliases", c.execute("select count(*) from aliases").fetchone()[0])
print("王利敏 alias:", c.execute("select * from aliases where person_id='a35599192'").fetchall())
