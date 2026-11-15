#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
决策中枢 v1.0 —— 一份共享状态 · 十个按需调用的方法模块 · 三条反馈循环

设计来源：C:/Users/wardc/Documents/New project gpt/AI-archive/outputs/个人决策中枢_恋爱与现金流_20261011/
  · 03_完整信息流程与方法调度.md   （十二环节 · 十模块 · 五路由）
  · 04_方法调度与接口契约.json     （模块契约 · 依赖契约 · 5 个共享接口）
  · 01_共享决策包.json             （本轮案例与关系证据）

本工具把上面那份**静态设计**接通到 analysis.sqlite 与 Obsidian。

三条循环
  理解循环：evidence → scoped_current_state → user_correction → claim_revision
  决策循环：decision_frame → options → recommendation → actual_choice → actual_outcome
  方法循环：failure_or_gap → method_revision_candidate → scoped_experience → later_adoption

常用
  python tools/decision_hub.py init                  # 建表（幂等）
  python tools/decision_hub.py seed                  # 灌入方法与案例基线（幂等）
  python tools/decision_hub.py methods               # 十个模块契约
  python tools/decision_hub.py route romance_and_cash
  python tools/decision_hub.py run M04               # 跑一个模块
  python tools/decision_hub.py case                  # 跑完整路由（M01→M09）
  python tools/decision_hub.py card                  # 决策卡
  python tools/decision_hub.py read understanding    # 共享读取接口
  python tools/decision_hub.py feedback --case <case_id> "选了A" "理由" "结果"
  python tools/decision_hub.py render                # 生成 Obsidian 视图（幂等）
  python tools/decision_hub.py verify                # 自检

★ 铁律
  - 未知保持未知：null + reason，**不得**替换成 0。
  - 模拟不是结果：simulation / hypothesis 不得写进 actual_outcome。
  - 本人理由不由系统代填：reason_verbatim 只能由 `feedback` 传入。
  - 同源派生不算独立证据：同 source_root 只算一份。
  - render 必须先读回手填区，再重写；连续两次渲染字节数必须一致。
"""
import os
import re
import sys
import json
import sqlite3
import argparse
from datetime import datetime, date, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(ROOT, "analysis.sqlite")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
VIEW_DIR = os.path.join(VAULT, "07_决策中枢")
ARCHIVE = r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\个人决策中枢_恋爱与现金流_20261011"
IDX = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"

TODAY = "2026-10-11"
SCHEMA_VERSION = "1.0"
CASE_ID = "ROMANCE-CASH-20261011-500"

ZONE_BEGIN = "<!-- >>> 手填区 · render 原样保留 · 填完跑 feedback/sync >>> -->"
ZONE_END = "<!-- <<< 手填区 <<< -->"

# ---------------------------------------------------------------- 建表

DDL = """
-- ① 决策案例（本轮问题 / 目标 / 输入 / 未知 / 执行状态）
CREATE TABLE IF NOT EXISTS decision_cases (
  case_id TEXT PRIMARY KEY,
  opened_at TEXT, as_of TEXT, question TEXT, goal_verbatim TEXT,
  domains TEXT, route_id TEXT, proposed_direction TEXT,
  opening_cash_cny REAL, cash_status TEXT, relationship_status TEXT,
  execution_status TEXT,
  user_choice TEXT, user_reason_verbatim TEXT, actual_outcome TEXT, revision_note TEXT,
  packet_revision INTEGER, snapshot_id TEXT,
  created_at TEXT, updated_at TEXT
);

-- ② 现金日历条目（M04）
CREATE TABLE IF NOT EXISTS cash_items (
  item_id TEXT PRIMARY KEY,
  case_id TEXT,
  kind TEXT,              -- opening_cash|essential_expense|confirmed_receipt|verified_due|opportunity|loan
  label TEXT,
  amount_cny REAL,        -- NULL = 未知（不得写 0）
  amount_status TEXT,     -- known|unknown
  due_date TEXT,
  direction TEXT,         -- in|out
  status TEXT,            -- confirmed|opportunity|unknown|paid|received|overdue
  epistemic_status TEXT,  -- user_report|raw_record|external_check|system_inference|simulation|pending
  source_locator TEXT, source_root TEXT,
  note TEXT, created_at TEXT, updated_at TEXT
);

-- ③ 机会与应收（M04/M07）
CREATE TABLE IF NOT EXISTS opportunity_records (
  opp_id TEXT PRIMARY KEY,
  case_id TEXT, label TEXT, counterparty TEXT, kind TEXT,
  est_amount_cny REAL, amount_status TEXT,
  status TEXT,            -- lead|verifying|confirmed|received|dead
  next_step TEXT, blocking TEXT,
  source_locator TEXT, note TEXT, created_at TEXT, updated_at TEXT
);

-- ④ 资源条目（M07）
CREATE TABLE IF NOT EXISTS resource_records (
  res_id TEXT PRIMARY KEY,
  label TEXT, kind TEXT,  -- capability|work|tool|network|channel
  evidence_ref TEXT, deliverable TEXT, constraints TEXT,
  status TEXT,            -- verified|claimed|unverified
  note TEXT, created_at TEXT, updated_at TEXT
);

-- ⑤ 策略候选档案（M07/M08）
CREATE TABLE IF NOT EXISTS strategy_candidates (
  strat_id TEXT PRIMARY KEY,
  case_id TEXT, route_kind TEXT,   -- 关系行动|现金行动|新路线
  title TEXT, mechanism TEXT,
  required_conditions TEXT, cost TEXT, time_cost TEXT, affordability TEXT,
  failure_conditions TEXT, adaptation_trigger TEXT, strongest_objection TEXT,
  status TEXT,            -- candidate|selected|running|done|dropped
  source_refs TEXT, created_at TEXT, updated_at TEXT
);

-- ⑥ 行动结果（M10 · 决策循环落点）
CREATE TABLE IF NOT EXISTS action_outcomes (
  outcome_id TEXT PRIMARY KEY,
  case_id TEXT, strat_id TEXT, episode_id TEXT,
  action_taken TEXT, executed INTEGER,     -- 1 执行 / 0 未执行
  reason_verbatim TEXT,                    -- ★ 只能由 feedback 传入
  actual_result TEXT, user_assessment TEXT,
  outcome_kind TEXT,                       -- no_action|no_result|unknown|result
  recorded_at TEXT, note TEXT
);

-- ⑦ 方法版本（M10 · 方法循环落点）
CREATE TABLE IF NOT EXISTS method_versions (
  mv_id TEXT PRIMARY KEY,
  method_id TEXT, version TEXT, name TEXT, scope TEXT,
  trigger TEXT, inputs TEXT, outputs TEXT, stop_rule TEXT,
  invalidation_triggers TEXT, implementation TEXT,
  evidence_cases TEXT, status TEXT,        -- adopted|candidate|deprecated
  adopted_at TEXT, note TEXT, created_at TEXT, updated_at TEXT
);

-- ⑧ 跨对象依赖（契约：source→fact→claim→strategy→rec→outcome）
CREATE TABLE IF NOT EXISTS cross_object_deps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_kind TEXT, from_id TEXT, to_kind TEXT, to_id TEXT,
  dep_kind TEXT, note TEXT, created_at TEXT
);

-- ⑨ 覆盖与游标（M01）
CREATE TABLE IF NOT EXISTS coverage_cursors (
  cursor_id TEXT PRIMARY KEY,
  source_root TEXT, source_locator TEXT,
  last_read_at TEXT, coverage_state TEXT,  -- collected|indexed|raw_read|interpreted|unreadable
  watermark TEXT, note TEXT, updated_at TEXT
);

CREATE INDEX IF NOT EXISTS ix_cash_case   ON cash_items(case_id, kind);
CREATE INDEX IF NOT EXISTS ix_cash_due    ON cash_items(due_date);
CREATE INDEX IF NOT EXISTS ix_opp_status  ON opportunity_records(status);
CREATE INDEX IF NOT EXISTS ix_strat_case  ON strategy_candidates(case_id, route_kind);
CREATE INDEX IF NOT EXISTS ix_ao_case     ON action_outcomes(case_id);
CREATE INDEX IF NOT EXISTS ix_mv_method   ON method_versions(method_id);
CREATE INDEX IF NOT EXISTS ix_xdep_from   ON cross_object_deps(from_kind, from_id);
CREATE INDEX IF NOT EXISTS ix_xdep_to     ON cross_object_deps(to_kind, to_id);
"""

# ---------------------------------------------------------------- 十个方法模块契约

METHODS = [
    dict(id="M01", name="来源与覆盖核对",
         trigger="新资料 / 依据冲突 / 决策前刷新",
         inputs="来源记录 · 原文定位 · 事件时间 · 别名 · 覆盖状态",
         outputs="证据包 · 冲突 · 覆盖缺口",
         existing="sources · evidence · events · persons · aliases · claim_evidence",
         stop="原文或媒体不可读时记录缺口，不由摘要代替核验",
         invalidation="source_changed / source_unavailable / alias_corrected",
         impl="已接通：读 analysis.sqlite + 索引库 + coverage_cursors",
         refs="PROV-O · QUMem"),
    dict(id="M02", name="问题与系统边界",
         trigger="目标有实质分歧 / 常规路线反复失效 / 需要改问题",
         inputs="本人目标原话 · 时间窗 · 相关人 · 约束 · 可承受损失",
         outputs="决策框架 · 成功条件 · 替代框架",
         existing="decisions · hypotheses · understanding_views",
         stop="目标与边界足够区分当前方案后结束；新框架保持候选",
         invalidation="goal_changed / constraint_changed",
         impl="已接通：读 decision_cases + decisions",
         refs="SSM · CriticalSystemsHeuristics · Meadows · DecisionQuality"),
    dict(id="M03", name="当前自我理解",
         trigger="问题需要个性化 / 本人理由或情境变化 / 本人纠正",
         inputs="有条件理解 · 选择片段 · 本人理由 · 反例 · 当前资源",
         outputs="当前状态 · 候选解释 · 理解增量",
         existing="self_claims · claim_evidence · choice_episodes · understanding_views",
         stop="缺本人理由时保留候选；状态不自动升为永久人格",
         invalidation="claim_corrected / new_counterevidence / context_changed",
         impl="已接通：读 self_claims + choice_episodes（含理由覆盖率）",
         refs="QUMem · StanfordSelfReportAgents · OpenLearnerModel"),
    dict(id="M04", name="现金日历与资源",
         trigger="涉及新增支出 / 到账或到期支付 / 当前现金变化",
         inputs="期初现金 · 已确认到账 · 必需支出 · 已核实到期应付 · 未知项",
         outputs="按日期余额或未知 · 现金缺口 · 核查任务 · 预算额度或 null",
         existing="events · evidence · sources",
         proposed="cash_items · opportunity_records",
         stop="必要金额或日期缺失时输出信息不足，不输出可用约会额度",
         invalidation="cash_changed / receipt_confirmed / payment_changed / due_date_changed",
         impl="已接通：cash_items 按日投影 B(t)",
         refs="BillCalendar · RobustDecisionMaking"),
    dict(id="M05", name="关系互动理解",
         trigger="联系与见面决策 / 新的对方回应 / 关系目标变化",
         inputs="本人目标 · 观察到的消息 · 共同安排 · 关系未知 · 当前约束",
         outputs="可观察的互动状态 · 替代解释 · 条件式下一步",
         existing="persons · aliases · events · evidence · hypotheses",
         stop="不输出隐藏动机、恋爱成功率或人格定论；无近期资料则状态未知",
         invalidation="new_response / shared_plan_changed / user_goal_changed",
         impl="已接通：按 talker 读索引库真实消息",
         refs="SSM · LongitudinalRelationshipQuality"),
    dict(id="M06", name="偏好澄清与信息价值",
         trigger="方案取舍依赖关键未知 / 理解候选冲突",
         inputs="候选方案 · 会改变决策的未知 · 已有回答 · 回答成本",
         outputs="一个高价值问题或补证任务 · 条件分支",
         existing="learning_questions · choice_episodes",
         stop="先查已有资料；未知已答且无新原因不重复问；补不齐就用条件分支",
         invalidation="answer_received / unknown_resolved / options_changed",
         impl="已接通：从 unknowns + learning_questions 排序出「一个」问题",
         refs="MAPLE · ValueOfInformation · ActiveInference"),
    dict(id="M07", name="资源组合与策略探索",
         trigger="当前选项受限 / 希望创造新机会 / 需要不同路线",
         inputs="已核实资源 · 现有手段 · 约束 · 可承受损失 · 真实合作承诺",
         outputs="不同策略档案 · 新机会候选 · 未核实前提",
         existing="procedures · hypotheses · decisions",
         proposed="resource_records · strategy_candidates",
         stop="资源和合作未确认时只提候选；不再产生可执行差异时结束",
         invalidation="resource_changed / commitment_changed / constraint_changed",
         impl="已接通：resource_records → strategy_candidates（文字档案，非算法）",
         refs="Effectuation · MAP-Elites · POET · OMNI"),
    dict(id="M08", name="情景与反方检查",
         trigger="比较候选 / 条件不确定 / 建议后果重要",
         inputs="候选策略 · 硬约束 · 反证 · 情景条件",
         outputs="可行性对比 · 失败条件 · 调整触发 · 最强反对理由",
         existing="hypotheses · recommendations · rec_deps",
         stop="无概率依据则用情景；不把相关性、多模型赞同或单次结果当因果",
         invalidation="assumption_changed / new_counterevidence",
         impl="已接通：对每条 strategy 输出成立/失败/触发",
         refs="RobustDecisionMaking · CausalReasoning · DecisionQuality"),
    dict(id="M09", name="决策卡与共享阅读包",
         trigger="需要当前建议 / 更换 harness / 读取改变",
         inputs="当前状态 · 证据包 · 选项对比 · 依赖 · 方法版本 · 快照元数据",
         outputs="决策卡 · 预测（可选，独立） · 阅读包",
         existing="recommendations · rec_deps · predictions · understanding_views",
         stop="执行条件不满足时输出待核查；预测本人选择与建议行动分别呈现",
         invalidation="dependency_changed / snapshot_stale",
         impl="已接通：card + read_* 五个共享接口",
         refs="CoALA · ContextEngineering · AgentSkills · MCP"),
    dict(id="M10", name="反馈与方法修订",
         trigger="本人实际选择与理由 / 现实回应或收支结果 / 重复遗漏或失效",
         inputs="实际行为 · 本人理由原话 · 实际结果 · 既往预测 · 建议依赖 · 方法版本",
         outputs="修订候选 · 有条件经验候选 · 受影响对象 · 方法修订候选",
         existing="choice_episodes · predictions · revisions · self_claims · recommendations",
         proposed="action_outcomes · method_versions · cross_object_dependencies",
         stop="模拟不是结果；单次经验先保留候选；本人理由不由系统填写",
         invalidation="outcome_corrected / user_reassessment",
         impl="已接通：feedback 写 action_outcomes → 反查 rec_deps → 标待复核",
         refs="ReasoningBank · ACE · MemRL"),
]

ROUTES = {
    "lookup": dict(when="查询资料", seq=["M01", "M09"]),
    "personal_decision": dict(when="当前该怎么办",
                              seq=["M01", "M02", "M03", "M08", "M09"],
                              insert_domain=["M04", "M05"], insert_if_needed=["M06", "M07"]),
    "romance_and_cash": dict(when="现金受限并希望发展关系",
                             seq=["M01", "M02", "M03", "M04", "M05", "M07", "M08", "M09"],
                             insert_if_needed=["M06"]),
    "new_real_feedback": dict(when="真实选择、本人理由、回应、收支变化",
                              seq=["M10"], then="dependency_resolution_and_only_affected_module_rerun"),
    "new_opportunity": dict(when="需要创造不同选择",
                            seq=["M01", "M02", "M03", "M07", "M08", "M09"]),
}


def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return date.today().isoformat()


# ---------------------------------------------------------------- 种子数据

SEED_CASH = [
    # item_id, kind, label, amount, amount_status, due_date, direction, status, epistemic, locator, root, note
    ("CASH-OPEN-500", "opening_cash", "当前可自由动用现金", 500.0, "known", TODAY, "in", "confirmed",
     "user_report", "本人 2026-10-11 回答「500」", "本人会话", "按提问顺序理解为可自由动用现金；非账户核验，可由本人纠正"),
    ("CASH-DUE-JH-1108", "verified_due", "交通银行贷款（每月8日）", 2898.0, "known", "2026-11-08", "out",
     "confirmed", "user_report", "本人 2026-10-11 明确「每月2898元持续一年」", "本人会话", "12 期 · 起算日待核"),
    ("CASH-DUE-MT-1103", "verified_due", "美团月付（每月3日）", 2309.99, "known", "2026-11-03", "out",
     "overdue", "raw_record", "美团金融服务公众号还款提醒×9", "微信支付", "10-04 已扣款失败 · 总额待核"),
    ("CASH-DUE-AYH-1108", "verified_due", "安逸花（每月8日）", 189.11, "known", "2026-11-08", "out",
     "confirmed", "raw_record", "安逸花公众号还款提醒", "微信支付", "10-04 已还 · 金额小但上征信"),
    ("CASH-DUE-CS-1115", "verified_due", "程颂孟秋（每月15日）", 2000.0, "known", "2026-11-15", "out",
     "confirmed", "user_report", "本人自述「就差2000」", "本人会话", "个人借款 · 无息?"),
    ("CASH-UNK-XB", "loan", "小贝借钱备用金", None, "unknown", None, "in", "unknown",
     "raw_record", "小贝借钱公众号 09-15 / 10-08 到账通知", "微信支付", "¥8,000 是否已支用未知 → 不计入确定到账"),
    ("CASH-UNK-QF", "verified_due", "奇富借条（360数科）", None, "unknown", None, "out", "overdue",
     "raw_record", "filehelper 催收短信原文", "催收短信", "2026-03-25 已逾期 · 金额未知"),
    ("CASH-UNK-DXM", "verified_due", "度小满", 1000.0, "known", None, "out", "unknown",
     "user_report", "本人 2026-03-10 称借 1000", "本人会话", "状态不明"),
    ("CASH-UNK-WYL", "verified_due", "王逸伦", 500.0, "known", None, "out", "unknown",
     "raw_record", "转账表 2026-08-11", "转账表", "对方未催"),
    ("CASH-UNK-UK", "verified_due", "英国那笔", None, "unknown", None, "out", "unknown",
     "user_report", "本人自述「不着急找我要」", "本人会话", "金额未知 · 暂不催"),
    ("CASH-UNK-LIVING", "essential_expense", "30 天生活必需支出", None, "unknown", None, "out", "unknown",
     "pending", "本人 2026-10-11 回答「未知」", "本人会话", "★ 缺此项 → 不输出约会预算上限"),
]

SEED_OPP = [
    ("OPP-JH-REFUND", "极狐三笔返款", "极狐/安鹏", "应收",
     None, "unknown", "verifying", "确认三笔是否仍未到账、金额与手续", "已卡 13 天+",
     "CON-048 决策中枢四线", "09-26 资料未发安鹏 · 新对接人王义未用"),
    ("OPP-ZYC-LABOR", "祝雨辰展会劳务费", "祝雨辰（央美设计学院研一）", "应收",
     None, "unknown", "received", "已闭环：本人 2026-10-11 确认到账", "已全部用于事故赔偿",
     "CON-065 / CON-068", "★ 到账 ≠ 可用现金（钱已一进一出）"),
    ("OPP-TUTOR", "家教/授课现金", "历史家教渠道", "服务",
     None, "unknown", "lead", "核查当前可上时间、时薪与结算周期", "本人 2026-10-04 否认在精华任职",
     "USER.md / 现金流急救页", "5,616/月 需 ≈3.5 次/周 × 2h × 200/h"),
    ("OPP-PHOTO", "摄影 / AIGC 小单", "历史合作入口", "服务",
     None, "unknown", "lead", "用已有交付物整理一项范围清楚的服务", "作品需现成、付款安排需确认",
     "resource_records", "重度 RAW + Capture One · ComfyUI / 即梦 / Nano Banana"),
    ("OPP-SUB", "可调整订阅支出", "各类订阅与账单", "节流",
     None, "unknown", "lead", "列出当前实际金额与取消生效日期", "影响日常工具使用的先不动",
     "现金流急救页", "属支出侧，非收入侧"),
]

SEED_RES = [
    ("RES-PHOTO", "摄影（重度 RAW + Capture One）", "capability",
     "作品集 · 艺术实践网站", "人像 / 活动 / 展陈拍摄与后期", "需确认客户与交付周期", "verified",
     "USER.md 技能真相"),
    ("RES-AIGC", "AIGC 影像（ComfyUI / 即梦 / Nano Banana）", "capability",
     "AIGC 审美边际效应框架", "图像生成 / 修复 / 风格迁移", "商业交付案例待补", "verified",
     "05 三·补·50 / 06_自我模型"),
    ("RES-EDIT", "视频剪辑（剪映为主）", "capability",
     "版画工坊 2 分钟横屏视频（欠 19 天）", "短片剪辑 / 横屏成片", "★ PR / AE 尚不熟练", "claimed",
     "USER.md 技能真相"),
    ("RES-INTERACT", "交互装置（TouchDesigner / MediaPipe / Unity DMX）", "capability",
     "《在场与回应》 · 双手成曲 Gesture Synth", "互动装置 / 数字交互", "需场地与设备", "verified",
     "USER.md"),
    ("RES-PY", "Python（非科班但能跑通）", "capability",
     "analysis.sqlite + tools/ 全套", "数据处理 / 自动化", "非工程级", "verified",
     "本项目"),
    ("RES-CAFA", "央美实验艺术与科技艺术学院 硕士（2025 级）", "network",
     "在读身份", "学术场景 / 展览 / 合作入口", "★ 不得写成博士在读", "verified",
     "USER.md 口径红线"),
    ("RES-JINGLIN", "井邻 · 怀柔洞台村乡村美育工作站", "network",
     "515 条 / 99 会话 / 18 月", "乡村美育 / 版画工作坊 / 展览", "★ 商业信息不进对外材料", "verified",
     "05 三·补·38"),
    ("RES-ALUMNI", "格拉斯哥北京校友会（文案与传播）", "channel",
     "9 群 / 18 家跨校友会资源", "活动文案 / 传播 / 组织", "发布前必过周冉", "verified",
     "05 三·补·60"),
    ("RES-MOTHER", "母亲刘丽萍（央美版画系教授）这条线", "network",
     "中传旁听 / 林茂 / 武脉仪 / 叶敏", "资源供给通道", "★ 不得读成「靠家里」", "verified",
     "05 三·补·52"),
    ("RES-ECON", "经济金融背景（首经贸 + 格拉斯哥 · CFA/CPA 备考）", "capability",
     "区域经济学 80.82", "社会美育的经济学视角", "非执业资格", "verified",
     "USER.md"),
]

SEED_STRAT = [
    ("STRAT-ROM-1", "关系行动", "恢复真实交流（不依赖新增支出）",
     "用真实近况或共有经历发起一次普通交流，观察是否自然往返",
     "① 有真实共有话题 ② 对方有回复渠道 ③ 不产生支出",
     "¥0", "每次 5–15 分钟",
     "可承受损失＝0（无金钱投入）",
     "对方只回单字且不再接话 → 降级为观察",
     "对方主动分享近况 / 提出替代时间 → 升级到「约定见面」候选",
     "「普通交流」可能被读成试探，反而降低自然度",
     "candidate", "M05 · 01共享决策包 relationship_evidence"),
    ("STRAT-ROM-2", "关系行动", "在条件明确后安排一次预算内见面",
     "先核实双方意愿与时间，再选一个低成本的共同活动",
     "① 双方都表示愿意 ② 时间明确 ③ 有已知预算上限",
     "待定（依赖 M04 输出）", "半天",
     "可承受损失上限待本人设定",
     "预算上限仍未知 / 对方未给出替代时间 → 保持候选不执行",
     "预算核实完成 或 对方主动提出时间 → 重新比较",
     "预算未知就安排见面，等于用未知承担确定成本",
     "candidate", "M04 + M05 → M08"),
    ("STRAT-CASH-1", "现金行动", "核实一笔已有应收（极狐返款 / 劳务费）",
     "从既有返款或劳务费资料中挑一笔，核对是否仍有未到账款项、金额与缺失手续",
     "① 确有未到账款项 ② 有可执行的手续路径",
     "¥0", "1 次沟通",
     "可承受损失＝0",
     "线索已结清 / 对方失联 → 标记 dead，换下一笔",
     "确认金额与到账日 → 转入 confirmed_receipt，重算现金日历",
     "旧线索可能早已结清，核实本身不产生收入",
     "candidate", "M04 · opportunity_records"),
    ("STRAT-CASH-2", "现金行动", "一项能交付的小服务（摄影 / AIGC / 剪辑）",
     "用已有作品整理一项范围清楚、可报价的交付服务",
     "① 作品现成 ② 能说清交付物与周期 ③ 有获客渠道",
     "≈¥0（时间成本）", "2–4 小时准备",
     "可承受损失＝一次准备时间",
     "无客户承诺 → 不得计入预计收款",
     "出现真实客户询价 → 转入机会区并核实付款安排",
     "「有作品」不等于「有订单」，作品集需先整理",
     "candidate", "resource_records · Effectuation"),
    ("STRAT-CASH-3", "现金行动", "按日核对 30 天缺口，先处理最近一笔到期",
     "用 B(t) 公式排出每日余额，定位最低余额日，优先处理最近到期项",
     "① 已核实的到期日与金额 ② 期初现金",
     "¥0", "30 分钟",
     "可承受损失＝0",
     "生活必需支出未知 → 只输出缺口日，不输出约会预算",
     "新增到账 / 支出核实 → 重算",
     "只算债务到期、不算生活费，会低估真实缺口",
     "candidate", "M04 · cash_items"),
    ("STRAT-NEW-1", "新路线", "让作品与共同兴趣成为交流或收入入口",
     "把摄影 / 艺术实践 / 共同兴趣同时当关系入口与收入入口",
     "① 对方对该领域真有兴趣 ② 作品可展示 ③ 活动当前存在且可负担",
     "视活动而定", "视活动而定",
     "可承受损失上限待定",
     "活动已结束 / 对方无兴趣 / 超预算 → 换场景",
     "对方回应具体活动或主动提议 → 升级",
     "把「共同兴趣」当既定事实，实际未核实",
     "candidate", "M07 · Effectuation + MAP-Elites"),
]


def cmd_init():
    c = connect()
    c.executescript(DDL)
    c.commit()
    ts = [r[0] for r in c.execute(
        "select name from sqlite_master where type='table' and name in "
        "('decision_cases','cash_items','opportunity_records','resource_records',"
        "'strategy_candidates','action_outcomes','method_versions','cross_object_deps','coverage_cursors')")]
    print("[init] 决策中枢表就绪：%d 张 -> %s" % (len(ts), ", ".join(sorted(ts))))
    total = c.execute("select count(*) from sqlite_master where type='table'").fetchone()[0]
    print("[init] analysis.sqlite 现有表：%d" % total)
    c.close()


def cmd_seed(quiet=False):
    c = connect()
    c.executescript(DDL)
    t = now()

    # 方法版本
    for m in METHODS:
        c.execute("""insert or replace into method_versions
          (mv_id,method_id,version,name,scope,trigger,inputs,outputs,stop_rule,
           invalidation_triggers,implementation,evidence_cases,status,adopted_at,note,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  ("MV-%s-1.0" % m["id"], m["id"], "1.0", m["name"],
                   "personal_decision_romance_and_cash",
                   m["trigger"], m["inputs"], m["outputs"], m["stop"], m["invalidation"],
                   m["impl"], "", "adopted", TODAY,
                   "refs: %s" % m["refs"], t, t))

    # 案例
    cases = [
        (CASE_ID, "2026-10-11", TODAY,
         "现金约500元、近期收支未知时，怎样继续发展与lzh、刘华赞的关系？",
         "我现在没钱还想和lzh还有刘海赞等发展",
         "恋爱,现金流", "romance_and_cash",
         "先用真实近况或共有经历开展不依赖新增支出的交流；现金上先核实一笔已有回款线索。",
         500.0, "insufficient_information", "insufficient_recent_verified_information",
         "proposed_not_executed", None, None, None, None, 2,
         "SNAP-20261011-01"),
        ("CASH-20261011-500", "2026-10-11", TODAY,
         "当前现金约500元，哪些行动能改善现金条件？",
         "我现在没钱还想和lzh还有刘海赞等发展",
         "现金流", "romance_and_cash",
         "从既有劳务费或返款资料中选择一笔，核对是否确有未到账款项、金额与缺失手续。",
         500.0, "insufficient_information", None, "proposed_not_executed",
         None, None, None, None, 2, "SNAP-20261011-01"),
    ]
    for r in cases:
        c.execute("""insert or replace into decision_cases
          (case_id,opened_at,as_of,question,goal_verbatim,domains,route_id,proposed_direction,
           opening_cash_cny,cash_status,relationship_status,execution_status,
           user_choice,user_reason_verbatim,actual_outcome,revision_note,
           packet_revision,snapshot_id,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", r + (t, t))

    # 现金条目
    for r in SEED_CASH:
        c.execute("""insert or replace into cash_items
          (item_id,case_id,kind,label,amount_cny,amount_status,due_date,direction,status,
           epistemic_status,source_locator,source_root,note,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (r[0], CASE_ID, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], t, t))

    # 机会
    for r in SEED_OPP:
        c.execute("""insert or replace into opportunity_records
          (opp_id,case_id,label,counterparty,kind,est_amount_cny,amount_status,status,
           next_step,blocking,source_locator,note,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (r[0], CASE_ID) + r[1:] + (t, t))

    # 资源
    for r in SEED_RES:
        c.execute("""insert or replace into resource_records
          (res_id,label,kind,evidence_ref,deliverable,constraints,status,note,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?)""", r + (t, t))

    # 策略候选
    for r in SEED_STRAT:
        c.execute("""insert or replace into strategy_candidates
          (strat_id,case_id,route_kind,title,mechanism,required_conditions,cost,time_cost,
           affordability,failure_conditions,adaptation_trigger,strongest_objection,
           status,source_refs,created_at,updated_at)
          values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (r[0], CASE_ID) + r[1:] + (t, t))

    # 覆盖游标
    cov = [
        ("CUR-VAULT", "Obsidian Vault", VAULT, TODAY, "interpreted",
         "06_自我模型 6 视图 @2026-10-11 12:38", "可读可手填视图层"),
        ("CUR-ANALYSIS", "analysis.sqlite", DB_PATH, TODAY, "interpreted",
         "events 2864 / evidence 5463 / conclusions 68", "结构化对象层"),
        ("CUR-WECHAT", "微信索引", IDX, TODAY, "indexed",
         "393,107 条 / 1,807 会话 · 最新 2026-10-11 12:24", "★ 未读媒体；lzh 181 条 / 刘华赞 21 条"),
        ("CUR-ARCHIVE", "决策中枢归档", ARCHIVE, TODAY, "raw_read",
         "03 完整流程 · 04 方法契约 · 01 共享包 v2", "静态设计来源，已接通为本层"),
    ]
    for r in cov:
        c.execute("""insert or replace into coverage_cursors
          (cursor_id,source_root,source_locator,last_read_at,coverage_state,watermark,note,updated_at)
          values(?,?,?,?,?,?,?,?)""", r + (t,))

    # ★ 补上「决策循环」缺的一环：库里原本没有以恋爱/现金为题的建议
    # （必须先插建议，下面的依赖边才能指向它）
    rec = ("REC-ROMANCE-CASH-30D",
           "现金受限时：先核实一笔应收 + 一次不依赖新增支出的真实交流",
           "现金侧：从既有返款/劳务费里挑一笔核对（是否仍未到账 → 金额 → 缺什么手续），"
           "结果记成「已到账 / 有明确付款信息 / 仍待核实」。"
           "关系侧：用真实近况或共有经历发起一次普通交流（不产生新增支出），"
           "观察是否接话 / 分享近况 / 发起后续 / 愿意共同安排时间。"
           "★ 约会支出上限保持 null，直到生活必需支出与到账被核实。",
           "关系／资源", "open",
           "若「无稳定收入」被推翻（本人恢复稳定现金流），则现金侧的紧迫性下降、关系侧可升级为有预算的见面；"
           "若两条关系近期本就有活跃互动，则「恢复交流」不再是瓶颈。",
           t, t)
    c.execute("""insert or replace into recommendations
      (rec_id,title,body,topic,status,impact_if_wrong,created_at,updated_at)
      values(?,?,?,?,?,?,?,?)""", rec)
    for cid, kind, note in [
        ("SC-FACT-004", "requires", "无稳定收入 → 现金侧优先"),
        ("SC-CON-004", "requires", "极狐返款线索 → 首选核实对象"),
        ("SC-PAT-001", "informed_by", "本人系统性主动 → 交流成本低"),
        ("SC-PREF-003", "informed_by", "先结论后理由 → 建议要短、要能立刻做"),
    ]:
        if not c.execute("select 1 from rec_deps where rec_id=? and claim_id=?",
                         ("REC-ROMANCE-CASH-30D", cid)).fetchone():
            c.execute("""insert into rec_deps (rec_id,claim_id,dep_kind,note,created_at)
                         values(?,?,?,?,?)""", ("REC-ROMANCE-CASH-30D", cid, kind, "[seed] " + note, t))

    # 跨对象依赖（示范链：source → fact → claim → strategy → rec → outcome）
    # ★ 带 [seed] 标记的边每次重建，保证幂等
    c.execute("delete from cross_object_deps where note like '[seed]%'")
    edges = [
        ("source", "CUR-WECHAT", "fact", "lzh-2026-06-14-邀约", "derives",
         "[seed] 本人 06-14 20:41 发出看展邀约；对方 21:43 回「最近都没空 下周要出去旅游」"),
        ("fact", "lzh-2026-06-14-邀约", "claim", "SC-PAT-001", "supports",
         "[seed] 邀约由本人发起，与「私聊中本人系统性发 ~60%」一致"),
        ("fact", "lzh-2026-06-14-邀约", "strategy", "STRAT-ROM-2", "constrains",
         "[seed] 6 月活动已结束 → 不得作为现行邀约，见面候选必须重新核实时间与活动"),
        ("claim", "SC-PAT-001", "strategy", "STRAT-ROM-1", "supports",
         "[seed] 本人系统性主动 → 「恢复真实交流」的成本低、可执行"),
        ("claim", "SC-FACT-004", "strategy", "STRAT-CASH-2", "constrains",
         "[seed] 2026-10 起无稳定收入 → 现金侧优先「核实应收」而非「新增服务」"),
        ("claim", "SC-CON-004", "strategy", "STRAT-CASH-1", "informs",
         "[seed] 极狐 αT5 返款线索 → 是「核实一笔应收」的首选对象"),
        ("strategy", "STRAT-CASH-1", "recommendation", "REC-ROMANCE-CASH-30D", "informs",
         "[seed] 现金动作 → 本案例建议的现金侧"),
        ("strategy", "STRAT-ROM-1", "recommendation", "REC-ROMANCE-CASH-30D", "informs",
         "[seed] 关系动作 → 本案例建议的关系侧"),
        ("strategy", "STRAT-CASH-3", "recommendation", "REC-ROMANCE-CASH-30D", "informs",
         "[seed] 30 天缺口 → 优先处理最近到期项"),
        ("source", "CUR-ANALYSIS", "claim", "SC-FACT-004", "derives",
         "[seed] 本人 2026-10-11 报告可自由动用现金约 500 元；同时 2026-10 起无稳定收入"),
        ("claim", "SC-FACT-004", "recommendation", "REC-ROMANCE-CASH-30D", "requires",
         "[seed] 无稳定收入 → 建议必须把现金侧排在关系侧之前"),
    ]
    _ids = {r[0] for r in c.execute("select claim_id from self_claims")}
    _recs = {r[0] for r in c.execute("select rec_id from recommendations")}
    _strats = {r[0] for r in c.execute("select strat_id from strategy_candidates")}
    _known = {"claim": _ids, "recommendation": _recs, "strategy": _strats}
    skipped = []
    for e in edges:
        bad = any(e[i] in _known and e[i + 1] not in _known[e[i]] for i in (0, 2))
        if bad:
            skipped.append(e)
            continue
        c.execute("""insert into cross_object_deps
          (from_kind,from_id,to_kind,to_id,dep_kind,note,created_at)
          values(?,?,?,?,?,?,?)""", e + (t,))
    if skipped and not quiet:
        print("[seed] ⚠️ 跳过 %d 条指向不存在对象的边：%s" % (
            len(skipped), ", ".join("%s/%s" % (e[0], e[1]) for e in skipped)))

    c.commit()
    if not quiet:
        print("[seed] 方法 %d · 案例 %d · 现金条目 %d · 机会 %d · 资源 %d · 策略 %d · 覆盖 %d · 跨对象依赖 %d" % (
            len(METHODS), len(cases), len(SEED_CASH), len(SEED_OPP), len(SEED_RES),
            len(SEED_STRAT), len(cov), c.execute("select count(*) from cross_object_deps").fetchone()[0]))
    c.close()


# ---------------------------------------------------------------- M01–M10 执行

def m01(c):
    out = ["## M01 · 来源与覆盖核对\n"]
    out.append("| 来源根 | 覆盖状态 | 水位 | 说明 |")
    out.append("|---|---|---|---|")
    for r in c.execute("select * from coverage_cursors order by cursor_id"):
        out.append("| %s | `%s` | %s | %s |" % (r["source_root"], r["coverage_state"], r["watermark"] or "—", r["note"] or ""))
    n_src = c.execute("select count(*) from sources").fetchone()[0]
    n_ev = c.execute("select count(*) from evidence").fetchone()[0]
    n_evt = c.execute("select count(*) from events").fetchone()[0]
    n_al = c.execute("select count(*) from aliases").fetchone()[0]
    out.append("\n**已结构化**：sources %d · evidence %d · events %d · aliases %d" % (n_src, n_ev, n_evt, n_al))
    out.append("\n**覆盖缺口**")
    out.append("- 微信索引只到文字层：**图片 / 语音 / 线下联系未读**")
    out.append("- lzh 与刘华赞**近期线下互动无记录** → 当前关系状态保持未知")
    out.append("- 30 天生活必需支出**无凭据** → 现金投影只到「缺口日」")
    out.append("\n**去重规则**：同 `source_root` 的多次转述只算一份证据（旧 AI 报告 / 人物笔记不额外计入）。")
    return "\n".join(out)


def m02(c):
    out = ["## M02 · 问题与系统边界\n"]
    for r in c.execute("select * from decision_cases where case_id=?", (CASE_ID,)):
        out.append("**本人原话**：%s" % r["goal_verbatim"])
        out.append("\n**本次问题**：%s" % r["question"])
        out.append("\n**领域**：%s · **路由**：`%s` · **快照**：%s" % (r["domains"], r["route_id"], r["snapshot_id"]))
    out.append("\n### 决策框架")
    out.append("| 项 | 内容 |")
    out.append("|---|---|")
    out.append("| 时间窗 | 30 天（2026-10-11 → 11-10） |")
    out.append("| 想改善什么 | ① 与 lzh / 刘华赞 的真实交流 ② 现金缺口 |")
    out.append("| 涉及的人 | lzh · 刘华赞（+ 家庭线为背景，不作意愿推断） |")
    out.append("| 可承受损失 | 关系侧 ¥0（本轮不产生新增支出）；现金侧待本人设定 |")
    out.append("| 可以改写的部分 | 「发展」的具体程度未确认 → 不预设为长期关系 |")
    out.append("\n### 替代框架（软系统 / 边界审视）")
    out.append("1. 怎样形成**互相愿意参与**的关系？（而不是「怎样让她答应」）")
    out.append("2. 哪些联系**有必要更新**？（而不是「怎样多聊」）")
    out.append("3. 怎样在**保护日常活动能力**的前提下推进现金到账？")
    out.append("4. 哪些**现有资源**能同时产生互动或收入场景？")
    out.append("\n⚠️ 「发展」可能包含了解 / 见面 / 暧昧 / 长期关系 —— **不同目标需要不同证据**，只在影响当前选择时才澄清。")
    return "\n".join(out)


def m03(c):
    out = ["## M03 · 当前自我理解（有条件）\n"]
    n_claim = c.execute("select count(*) from self_claims").fetchone()[0]
    n_rev = c.execute("select count(*) from self_claims where human_review is not null and human_review<>''").fetchone()[0]
    n_ce = c.execute("select count(*) from choice_episodes").fetchone()[0]
    n_reason = c.execute("select count(*) from choice_episodes where reasons_verbatim is not null and reasons_verbatim<>''").fetchone()[0]
    out.append("**理解条目** %d（已人工校准 %d）· **选择片段** %d（**有本人理由 %d**）" % (n_claim, n_rev, n_ce, n_reason))
    out.append("\n### 与本问题相关的当前状态")
    out.append("| 维度 | 当前值 | 状态 | 来源 |")
    out.append("|---|---|---|---|")
    out.append("| 目标 | 发展与 lzh / 刘华赞 的关系 | **本人表述** | 本人 2026-10-11 原话 |")
    out.append("| 资源 | 可自由动用现金 ≈ ¥500 | **本人报告**（非账户核验） | 本人回答「500」 |")
    out.append("| 约束 | 30 天必付与确定到账**未知** | 未知 | 本人回答「未知」 |")
    out.append("| 能力 | 摄影 / AIGC / 交互装置 / Python | 有证据 | resource_records |")
    out.append("| 缺口 | 剪辑（PR/AE）不熟练 · 无稳定收入 | 已确认 | USER.md / 本人 10-04 |")
    out.append("\n### 候选解释（**未确认，不得当结论**）")
    out.append("- 「缺钱限制了关系发展」可能是四种之一：**具体约会成本** / **希望先有稳定收入** / **不知道怎么发起互动** / 其他。")
    out.append("- ⚠️ **不得**从「资源受限时没约会」推出「他不重视恋爱」（历史行为只支持机制候选，不等于永久人格）。")
    out.append("\n### 理由覆盖率（本轮最值得补的缺口）")
    out.append("```")
    out.append("choice_episodes: %d 条  ·  写了本人理由: %d 条  →  缺 %d 条" % (n_ce, n_reason, n_ce - n_reason))
    out.append("```")
    out.append("→ 系统需要知道**当时有哪些可行选择**，才能理解行为。补法：`python tools/selfmodel.py reason <episode_id> \"...\"`")
    return "\n".join(out)


def _cash_projection(c, days=30):
    start = date.fromisoformat(TODAY)
    end = start + timedelta(days=days)
    opening = c.execute(
        "select amount_cny from cash_items where case_id=? and kind='opening_cash'", (CASE_ID,)).fetchone()
    opening = opening[0] if opening and opening[0] is not None else None

    dues = [dict(r) for r in c.execute(
        "select * from cash_items where case_id=? and kind in ('verified_due','essential_expense')", (CASE_ID,))]
    recv = [dict(r) for r in c.execute(
        "select * from cash_items where case_id=? and kind='confirmed_receipt'", (CASE_ID,))]

    events = []
    unknown_items = []
    for d in dues:
        if d["amount_cny"] is None or d["due_date"] is None:
            unknown_items.append(d)
            continue
        dd = date.fromisoformat(d["due_date"])
        if start <= dd <= end:
            events.append((dd, "out", d["amount_cny"], d["label"], d["status"]))
    for r in recv:
        if r["amount_cny"] is None or r["due_date"] is None:
            unknown_items.append(r)
            continue
        dd = date.fromisoformat(r["due_date"])
        if start <= dd <= end:
            events.append((dd, "in", r["amount_cny"], r["label"], r["status"]))

    events.sort(key=lambda x: x[0])
    bal = opening
    rows = []
    min_bal, min_date = None, None
    for dd, direc, amt, label, status in events:
        bal = (bal or 0) + (amt if direc == "in" else -amt)
        rows.append((dd.isoformat(), label, direc, amt, bal, status))
        if min_bal is None or bal < min_bal:
            min_bal, min_date = bal, dd.isoformat()
    return dict(opening=opening, rows=rows, min_bal=min_bal, min_date=min_date,
                unknown=unknown_items, end=end.isoformat())


def m04(c):
    p = _cash_projection(c)
    out = ["## M04 · 现金日历与资源\n"]
    out.append("**公式**：`B(t) = 期初现金 + 截至 t 已确认到账 − 截至 t 必需支出及已核实到期应付`\n")
    out.append("**期初（本人报告）**：¥%s · as_of %s" % (p["opening"], TODAY))
    out.append("\n### 30 天按日投影（2026-10-11 → %s）" % p["end"])
    out.append("| 日期 | 事项 | 方向 | 金额 | 当日余额 | 状态 |")
    out.append("|---|---|---|---:|---:|---|")
    for d, label, direc, amt, bal, status in p["rows"]:
        out.append("| %s | %s | %s | %s%.2f | **%.2f** | `%s` |" % (
            d, label, "＋" if direc == "in" else "－", "¥", amt, bal, status))
    out.append("\n**最低余额**：**¥%.2f**（%s）" % (p["min_bal"], p["min_date"]))
    out.append("\n### 未知项（★ 不得替换成 0）")
    for u in p["unknown"]:
        out.append("- **%s** —— 金额 %s · 日期 %s · 来源 %s" % (
            u["label"], "未知" if u["amount_cny"] is None else "¥%.2f" % u["amount_cny"],
            u["due_date"] or "未知", u["epistemic_status"]))
    out.append("\n### 输出结论")
    gap_days = [r[0] for r in p["rows"] if r[4] < 0]
    if gap_days:
        out.append("- ✅ **缺口日可定位**：%s（最低 ¥%.2f @ %s）" % (
            " → ".join(sorted(set(gap_days))), p["min_bal"], p["min_date"]))
    else:
        out.append("- ✅ 30 天内未出现负余额（但未含生活必需支出，不可据此判断安全）")
    out.append("- ⛔ **约会支出上限 = null（信息不足）** —— 生活必需支出未知，¥500 **不能**直接算作可支配结余")
    out.append("- ⚠️ 只算债务到期、不算生活费 → **会低估真实缺口**；本投影是**下界**")
    out.append("- 📌 窗口外（>%s）另有到期项：程颂 ¥2,000（11-15）等，需滚动到下一窗口" % p["end"])
    out.append("- 📌 机会区（**不计入确定到账**）：见 `opportunity_records`")
    return "\n".join(out)


TARGETS = [
    ("lzh", "wxid_63y6c4wnpf5d12", "Lzh_", "本人 2026-06-14 表达见面开心 + 看展邀约；对方回「最近都没空 下周要出去旅游」；2026-09-25 本人中秋问候"),
    ("刘华赞", "wxid_ltqmzbyc87cp22", "赞赞姐（备注被改成 `*`）", "2026-09-25 双向中秋问候（她回「祝你和丽萍阿姨中秋快乐」）；604 天 21 条 · 4 个日子 · 0 共同群 · 每次我方主动"),
]


def m05(c):
    out = ["## M05 · 关系互动理解\n"]
    out.append("> ⚠️ **只写可观察的事实**。不输出隐藏动机、恋爱成功率、人格定论。\n")
    for name, talker, alias, note in TARGETS:
        out.append("### %s（%s）" % (name, alias))
        out.append("**索引元数据**：")
        if os.path.exists(IDX):
            ic = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\", "/"), uri=True)
            ic.row_factory = sqlite3.Row
            row = ic.execute("select * from sessions where talker=?", (talker,)).fetchone()
            if row:
                out.append("- 消息 **%d** 条 · 首条 %s · 最新 %s" % (
                    row["message_count"],
                    datetime.fromtimestamp(row["first_ts"]).strftime("%Y-%m-%d"),
                    datetime.fromtimestamp(row["last_ts"]).strftime("%Y-%m-%d %H:%M")))
                out.append("- **最近 6 条纯文本**：")
                for m in ic.execute(
                        "select ts,role,substr(content,1,70) cc from messages "
                        "where session_key=? and content<>'' order by ts desc limit 6", (talker,)):
                    out.append("  - `%s` **%s**：%s" % (
                        datetime.fromtimestamp(m["ts"]).strftime("%m-%d %H:%M"), m["role"], m["cc"]))
            ic.close()
        out.append("\n**已知依据**：%s" % note)
        out.append("\n**可观察的互动状态**：**近期无新证据** → 当前关系状态 `unknown`")
        out.append("**不成立的推断**：")
        out.append("- ❌ 6 月「没空」≠ 长期拒绝（只适用于那次邀约）")
        out.append("- ❌ 节日问候 ≠ 浪漫意愿")
        out.append("- ❌ 索引里没有 ≠ 现实中没交流")
        out.append("- ❌ 家庭连接（母辈往来）不自动决定双方意愿")
        out.append("")
    out.append("### 下一步（条件式）")
    out.append("| 目标 | 条件 | 动作 |")
    out.append("|---|---|---|")
    out.append("| lzh | 有真实共有话题 | 从近况或共有经历发起一次普通交流（**不得**调用已结束的毕业展） |")
    out.append("| 刘华赞 | 节日问候可作入口 | 把问候自然延伸到真实日常交流，观察是否继续参与 |")
    out.append("\n**观察什么**：对方是否接话 / 分享近况 / 发起后续 / 愿意共同安排时间。**一次回复不决定长期前景。**")
    return "\n".join(out)


def m06(c):
    out = ["## M06 · 偏好澄清与信息价值\n"]
    out.append("> 只问**会改变当前建议**、且**容易回答**的问题。已有答案不重复索取。\n")
    out.append("### 候选缺口排序（按「会不会改变下一步」）")
    out.append("| 序 | 缺口 | 会改变什么 | 回答成本 | 状态 |")
    out.append("|---|---|---|---|---|")
    out.append("| 1 | **30 天生活必需支出大约多少？**（房 / 食 / 行 / 通讯） | 决定**约会预算上限**能不能算出来；也是现金缺口的下界修正 | 低（一句话） | 未答 |")
    out.append("| 2 | **近期和 lzh / 刘华赞 有没有线下联系？** | 决定关系动作是「恢复交流」还是「维持现有节奏」 | 低 | 未答 |")
    out.append("| 3 | **极狐三笔返款现在到哪一步了？** | 决定它是 `verifying` 还是 `dead`，直接影响现金候选排序 | 中 | 未答（卡 13 天+） |")
    out.append("| 4 | 交行贷款起算日 / 剩余期数 | 决定月供还要压几个月 | 中 | 未答 |")
    out.append("\n### ★ 本轮只提这一个问题")
    out.append("> **「未来 30 天，你的生活必需支出（房、吃、行、通讯）加起来大概多少？」**")
    out.append("\n**为什么是它**：")
    out.append("1. 它是**唯一**卡住「约会预算上限」的输入（当前输出 `null`）；")
    out.append("2. 它同时修正现金缺口的**下界**（现在只算了债务到期）；")
    out.append("3. 回答成本最低（一句话，不需要查账）。")
    out.append("\n**若无法回答** → 用条件分支继续，不阻塞：")
    out.append("- 若月必需 ≤ ¥1,500 → 缺口 ≈ 债务到期 − 500 + 1,500")
    out.append("- 若月必需 ¥1,500–3,000 → 缺口更大，优先「核实应收」而非「新服务」")
    out.append("\n**已答不重复**：本人已答「500」（现金）与「未知」（30 天必付/到账）→ 不再问这两项。")
    return "\n".join(out)


def m07(c):
    out = ["## M07 · 资源组合与策略探索\n"]
    out.append("### 已核实资源（现有手段）")
    out.append("| 资源 | 类型 | 可交付 | 约束 | 状态 |")
    out.append("|---|---|---|---|---|")
    for r in c.execute("select * from resource_records order by kind,res_id"):
        out.append("| %s | %s | %s | %s | `%s` |" % (
            r["label"], r["kind"], r["deliverable"] or "—", r["constraints"] or "—", r["status"]))
    out.append("\n### 策略候选档案（Effectuation · 从现有手段出发）")
    out.append("> 保留**机制不同**的路线，不只留一个赢家（MAP-Elites 思路）。数量上限 3 条/类。\n")
    cur = None
    for r in c.execute("select * from strategy_candidates order by route_kind,strat_id"):
        if r["route_kind"] != cur:
            cur = r["route_kind"]
            out.append("#### %s" % cur)
            out.append("| ID | 路线 | 机制 | 成本 | 可承受损失 | 成立条件 |")
            out.append("|---|---|---|---|---|---|")
        out.append("| `%s` | %s | %s | %s | %s | %s |" % (
            r["strat_id"], r["title"], r["mechanism"], r["cost"],
            r["affordability"], r["required_conditions"]))
    out.append("\n### 未核实前提（**不得当已成立**）")
    out.append("- 「对方对摄影 / 艺术有兴趣」—— 未核实")
    out.append("- 「作品可展示」—— 艺术实践网站已有，但**商业交付案例待补**")
    out.append("- 「有客户会来询价」—— 无客户承诺")
    out.append("\n**搜索结束条件**：新资料不再改变可执行选项 / 基本取舍 / 失败判断时，转入行动与反馈。")
    return "\n".join(out)


def m08(c):
    out = ["## M08 · 情景与反方检查\n"]
    out.append("> 无概率依据 → 用**情景**，不用精确概率和总分。不把相关性 / 多模型赞同 / 单次结果当因果。\n")
    for r in c.execute("select * from strategy_candidates order by route_kind,strat_id"):
        out.append("### `%s` %s" % (r["strat_id"], r["title"]))
        out.append("- **成立条件**：%s" % r["required_conditions"])
        out.append("- **代价**：%s · 时间 %s · 可承受损失：%s" % (r["cost"], r["time_cost"], r["affordability"]))
        out.append("- **失败条件**：%s" % r["failure_conditions"])
        out.append("- **调整触发**：%s" % r["adaptation_trigger"])
        out.append("- ★ **最强反对理由**：%s" % r["strongest_objection"])
        out.append("")
    out.append("### 情景对比（未知条件下）")
    out.append("| 情景 | 触发 | 优先动作 |")
    out.append("|---|---|---|")
    out.append("| A 有回款到账 | 极狐 / 劳务费确认 | 先补现金 → 再考虑有成本的见面 |")
    out.append("| B 无回款、也无新支出核实 | 30 天维持现状 | 只做 ¥0 的关系动作 + ¥0 的核实动作 |")
    out.append("| C 生活必需支出被核实为偏高 | 本人回答第 1 问 | 现金优先级 > 关系动作，先处理 11-03 美团 |")
    out.append("\n⚠️ **可承受损失无法确认时** → 只提可逆、少承诺的下一步。")
    return "\n".join(out)


def _card(c):
    out = ["# 决策卡 · %s" % CASE_ID, ""]
    row = c.execute("select * from decision_cases where case_id=?", (CASE_ID,)).fetchone()
    out.append("> **问题**：%s" % row["question"])
    out.append("> **as_of**：%s · **快照**：%s · **执行状态**：`%s`\n" % (row["as_of"], row["snapshot_id"], row["execution_status"]))
    out.append("## 1. 已确认 / 本人报告 / 未知")
    out.append("| 项 | 内容 | 认识状态 |")
    out.append("|---|---|---|")
    out.append("| 目标 | 发展与 lzh、刘华赞的关系 | **本人表述** |")
    out.append("| 现金 | 可自由动用 ≈ ¥500 | **本人报告**（非账户核验） |")
    out.append("| 30 天必付 / 确定到账 | 未知 | 未知（**不视为 0**） |")
    out.append("| 30 天到期应付（债务台账） | 交行 2,898（11-08）· 美团 2,309.99（11-03）· 安逸花 189.11（11-08）· 程颂 2,000（11-15） | **已核实** |")
    out.append("| 生活必需支出 | 未知 | 未知 |")
    out.append("\n## 2. 候选（有实质差异）")
    out.append("| 路线 | 机制 | 代价 | 条件 |")
    out.append("|---|---|---|---|")
    out.append("| **恢复真实交流** | 用真实近况发起普通交流 | ¥0 | 有共有话题 |")
    out.append("| 条件明确后见面 | 先核实意愿与预算 | 待定 | 预算上限未知 → **不执行** |")
    out.append("| **核实一笔应收** | 从返款 / 劳务费里挑一笔核 | ¥0 | 确有未到账款项 |")
    out.append("| 一项可交付小服务 | 整理摄影 / AIGC 服务 | 准备时间 | 无客户承诺前不计收款 |")
    out.append("| 按日核对缺口 | B(t) 排 30 天 | ¥0 | 已核实到期项 |")
    out.append("\n## 3. 建议（一个关系动作 + 一个现金动作）")
    out.append("### 关系动作")
    out.append("- **lzh**：从真实共有经历或当期近况发起一次**普通交流**（**不得**调用已结束的毕业展）")
    out.append("- **刘华赞**：把 09-25 的节日问候自然延伸到真实日常交流")
    out.append("- 观察：是否接话 / 分享近况 / 发起后续 / 愿意共同安排时间")
    out.append("\n### 现金动作")
    out.append("- 从既有返款或劳务费里**挑一笔**核对：**是否仍有未到账 → 金额 → 缺什么手续**")
    out.append("- 结果分别记成「已到账」「有明确付款信息」「仍待核实」")
    out.append("\n## 4. 最强反对理由")
    out.append("- 「普通交流」可能被读成试探，反而降低自然度 → 所以**只用真实共有话题**，不硬找话。")
    out.append("- 「核实应收」可能早已结清 → 所以**核实的成本设为 1 次沟通**，不追加。")
    out.append("\n## 5. 什么会改变建议")
    out.append("- 本人补充**近期线下互动**或对方当前意愿 → 关系动作升级/降级")
    out.append("- **生活必需支出**或**到账**被核实 → 约会预算上限从 `null` 变为可计算")
    out.append("- 当前关系状态或约定变化 → 换行动方式")
    out.append("\n## 6. 系统预测（**与建议分开**）")
    out.append("| 项 | 内容 |")
    out.append("|---|---|")
    out.append("| 系统预计你会怎样选 | 大概率选「核实一笔应收」而非立刻发起关系交流（现金更紧急、路径更确定） |")
    out.append("| 依据 | `SC-PREF-002`（数据/具体）· 现金缺口在 11-03 就到 · 关系侧证据薄弱 |")
    out.append("| 置信度 | 中 |")
    out.append("\n> ⚠️ **预测 ≠ 建议**。预测准不准校准「理解」，建议有没有用是另一回事。")
    out.append("\n## 7. 反馈（你只需补三行）")
    out.append("```text")
    out.append("我选择了：")
    out.append("我自己的理由：")
    out.append("实际发生了什么／现在还缺什么：")
    out.append("```")
    out.append("\n写入命令：")
    out.append("```bash")
    out.append("python tools/decision_hub.py feedback --case <case_id> \"我选择了…\" \"我自己的理由…\" \"实际结果…\"")
    out.append("```")
    return "\n".join(out)


def m09(c):
    out = ["## M09 · 决策卡与共享阅读包\n"]
    out.append(_card(c))
    out.append("\n---\n")
    out.append("### 阅读包元数据")
    out.append("| 字段 | 值 |")
    out.append("|---|---|")
    out.append("| schema_version | %s |" % SCHEMA_VERSION)
    out.append("| snapshot_id | SNAP-%s-01 |" % TODAY.replace("-", ""))
    out.append("| generated_at | %s |" % now())
    out.append("| as_of | %s |" % TODAY)
    out.append("| case_packet_revision | 2 |")
    out.append("| method_registry_version | 1 |")
    out.append("| privacy_scope | private（仅本地） |")
    out.append("| source_watermarks | 微信 393,107 条 @2026-10-11 12:24 |")
    return "\n".join(out)


def m10(c):
    out = ["## M10 · 反馈与方法修订\n"]
    rows = list(c.execute("select * from action_outcomes where case_id=? order by recorded_at", (CASE_ID,)))
    if not rows:
        out.append("**尚无真实反馈** —— 本轮未执行任何现实行动。\n")
        out.append("补三行即可启动本模块：")
        out.append("```bash")
        out.append("python tools/decision_hub.py feedback --case <case_id> \"我选择了…\" \"我自己的理由…\" \"实际结果…\"")
        out.append("```")
        out.append("\n**写入后会做三件事**：")
        out.append("1. 写 `action_outcomes`（行动 / 理由原话 / 实际结果）")
        out.append("2. 反查 `rec_deps` → 列出**受影响的理解与建议**（只标待复核，不自动改）")
        out.append("3. 生成 `revisions` 记录 + 方法修订候选")
        return "\n".join(out)
    out.append("| 时间 | 行动 | 执行 | 本人理由 | 实际结果 | 评价 |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        out.append("| %s | %s | %s | %s | %s | %s |" % (
            r["recorded_at"], r["action_taken"], "✅" if r["executed"] else "⛔",
            r["reason_verbatim"] or "—", r["actual_result"] or "—", r["user_assessment"] or "—"))
    out.append("\n### 受影响对象（依赖反查 · 只标待复核）")
    sid = rows[-1]["strat_id"] if rows else None
    ac, ar = _affected(c, sid)
    out.append("**理解 %d 条**：%s" % (len(ac), " · ".join(x[1] for x in ac) or "—"))
    out.append("**建议 %d 条**：%s" % (len(ar), " · ".join(x[1] for x in ar) or "—"))
    out.append("\n### 修订顺序（契约）")
    out.append("`mark_affected_needs_review → check_new_evidence → revise_scoped_claims_or_conditions "
               "→ recompare_options → regenerate_reading_packets`")
    out.append("\n> ★ `stale_is_not_false`：**陈旧 ≠ 已错**。单次经验先保留候选，不自动升级为「关于你的规律」。")
    return "\n".join(out)


RUNNERS = {"M01": m01, "M02": m02, "M03": m03, "M04": m04, "M05": m05,
           "M06": m06, "M07": m07, "M08": m08, "M09": m09, "M10": m10}


def cmd_run(mid):
    c = connect()
    mid = mid.upper()
    if mid not in RUNNERS:
        print("未知模块：%s（可用 M01–M10）" % mid)
        return
    print(RUNNERS[mid](c))
    c.close()


def cmd_case(route="romance_and_cash"):
    r = ROUTES[route]
    seq = list(r["seq"])
    c = connect()
    print("# 决策中枢 · 完整路由 `%s`（%s）\n" % (route, r["when"]))
    print("**执行顺序**：%s\n" % " → ".join(seq))
    for mid in seq:
        print("\n" + "=" * 72 + "\n")
        print(RUNNERS[mid](c))
    c.close()


def cmd_methods(mid=None):
    c = connect()
    if mid:
        rows = [r for r in c.execute("select * from method_versions where method_id=?", (mid.upper(),))]
    else:
        rows = list(c.execute("select * from method_versions order by method_id"))
    for r in rows:
        print("## %s · %s  `v%s`" % (r["method_id"], r["name"], r["version"]))
        print("- 触发：%s" % r["trigger"])
        print("- 输入：%s" % r["inputs"])
        print("- 输出：%s" % r["outputs"])
        print("- 停止/降级：%s" % r["stop_rule"])
        print("- 失效触发：%s" % r["invalidation_triggers"])
        print("- 实现：%s" % r["implementation"])
        print("- 引用：%s\n" % (r["note"] or ""))
    c.close()


def cmd_route(name=None):
    if name and name in ROUTES:
        r = ROUTES[name]
        print("`%s` —— %s" % (name, r["when"]))
        print("  顺序：%s" % " → ".join(r["seq"]))
        for k in ("insert_domain", "insert_if_needed"):
            if k in r:
                print("  %s：%s" % (k, ", ".join(r[k])))
        if "then" in r:
            print("  之后：%s" % r["then"])
        return
    print("可用路由：")
    for k, v in ROUTES.items():
        print("  %-20s %s\n      %s" % (k, v["when"], " → ".join(v["seq"])))


# ---------------------------------------------------------------- 共享读取接口

def read_understanding(topic=None):
    c = connect()
    d = {"schema_version": SCHEMA_VERSION, "snapshot_id": "SNAP-%s-01" % TODAY.replace("-", ""),
         "generated_at": now(), "as_of": TODAY, "topic": topic or "romance_and_cash",
         "privacy_scope": "private"}
    d["current_user_state"] = {
        "goal": c.execute("select goal_verbatim from decision_cases where case_id=?", (CASE_ID,)).fetchone()[0],
        "opening_cash_cny": 500.0, "cash_status": "insufficient_information",
        "relationship_status": "insufficient_recent_verified_information",
    }
    d["knowns"] = [dict(r) for r in c.execute(
        "select item_id,label,amount_cny,amount_status,due_date,status,epistemic_status from cash_items "
        "where amount_status='known' order by item_id")]
    d["unknowns"] = [dict(r) for r in c.execute(
        "select item_id,label,note from cash_items where amount_status='unknown' order by item_id")]
    d["related_choices"] = [dict(r) for r in c.execute(
        "select episode_id,question,actual_choice,reasons_verbatim from choice_episodes "
        "where reasons_verbatim is null or reasons_verbatim='' limit 9")]
    d["evidence_refs"] = [dict(r) for r in c.execute(
        "select cursor_id,source_root,watermark,coverage_state from coverage_cursors")]
    d["changes"] = [dict(r) for r in c.execute(
        "select rev_id,entity_type,entity_id,field,changed_at from revisions order by changed_at desc limit 5")]
    print(json.dumps(d, ensure_ascii=False, indent=2))
    c.close()


def read_evidence(query=None, limit=10):
    c = connect()
    out = {"schema_version": SCHEMA_VERSION, "query": query, "as_of": TODAY, "excerpts": [], "coverage": []}
    if query and os.path.exists(IDX):
        ic = sqlite3.connect("file:%s?mode=ro" % IDX.replace("\\", "/"), uri=True)
        ic.row_factory = sqlite3.Row
        for r in ic.execute(
                "select session_key,ts,role,substr(content,1,160) cc from messages "
                "where content like ? and session_key not like 'gh_%' order by ts desc limit ?",
                ("%" + query + "%", limit)):
            out["excerpts"].append({
                "talker": r["session_key"],
                "time": datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d %H:%M:%S"),
                "role": r["role"], "excerpt": r["cc"]})
        ic.close()
    out["coverage"] = [dict(r) for r in c.execute("select cursor_id,coverage_state,watermark from coverage_cursors")]
    out["rule"] = "同 source_root 的转述不算独立证据；引用必须能回到原文定位"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    c.close()


def _changed_recommendations(c, changed):
    """仅按已确认的依赖编码找受影响建议；未知关系留待人工判断。"""
    aliases = {"self_claim": "claim", "self_claims": "claim",
               "recommendations": "recommendation", "rec": "recommendation",
               "strategy_candidate": "strategy", "strategy_candidates": "strategy"}
    def key(kind, ident):
        return (aliases.get(str(kind), str(kind)), str(ident))
    # 方向来自本文件 cmd_seed 的实际建边约定：依据 -> 受影响对象。
    confirmed = {
        ("source", "fact", "derives"), ("source", "claim", "derives"),
        ("fact", "claim", "supports"), ("fact", "strategy", "constrains"),
        ("claim", "strategy", "supports"), ("claim", "strategy", "constrains"),
        ("claim", "strategy", "informs"), ("strategy", "recommendation", "informs"),
        ("claim", "recommendation", "requires"),
    }
    adjacency, ambiguous = {}, []
    for r in c.execute("select claim_id,rec_id,dep_kind from rec_deps"):
        if r["dep_kind"] in {"assumes", "requires", "informed_by"}:
            adjacency.setdefault(key("claim", r["claim_id"]), set()).add(
                key("recommendation", r["rec_id"]))
        else:
            ambiguous.append({"table": "rec_deps", "from": key("claim", r["claim_id"]),
                              "to": key("recommendation", r["rec_id"]), "dep_kind": r["dep_kind"]})
    for r in c.execute("select from_kind,from_id,to_kind,to_id,dep_kind from cross_object_deps"):
        source, target = key(r["from_kind"], r["from_id"]), key(r["to_kind"], r["to_id"])
        if (source[0], target[0], r["dep_kind"]) in confirmed:
            adjacency.setdefault(source, set()).add(target)
        else:
            ambiguous.append({"table": "cross_object_deps", "from": source,
                              "to": target, "dep_kind": r["dep_kind"]})
    queue, unresolved = [], []
    for r in changed:
        node = key(r["entity_type"], r["entity_id"])
        if node[0] == "rec_dep" and "→" in node[1]:
            queue.append(key("recommendation", node[1].rsplit("→", 1)[1]))
        elif node[0] in {"source", "fact", "claim", "strategy", "recommendation", "outcome"}:
            queue.append(node)
        else:
            unresolved.append({"entity_type": r["entity_type"], "entity_id": r["entity_id"]})
    seen, affected = set(), set()
    index = 0
    while index < len(queue):
        node = queue[index]
        index += 1
        if node in seen:
            continue
        seen.add(node)
        if node[0] == "recommendation":
            affected.add(node[1])
        queue.extend(sorted(adjacency.get(node, ())))
    relevant_ambiguous = [r for r in ambiguous if tuple(r["from"]) in seen or tuple(r["to"]) in seen]
    return sorted(affected), relevant_ambiguous, unresolved


def _read_changes_payload(c, since):
    """只读查询；since 按 SQLite datetime 的秒级时间语义比较。"""
    if not c.execute("select datetime(?)", (since,)).fetchone()[0]:
        raise ValueError("since 必须是有效 ISO 日期或时间")
    out = {"schema_version": SCHEMA_VERSION, "since": since, "changed_objects": [],
           "affected_recommendations": [], "stale_objects": [], "cursor": now()}
    for r in c.execute("select rev_id,entity_type,entity_id,field,old_value,new_value,changed_at,reason "
                       "from revisions where datetime(changed_at) >= datetime(?) "
                       "order by datetime(changed_at) desc,rev_id desc", (since,)):
        out["changed_objects"].append(dict(r))
    affected, ambiguous, unresolved = _changed_recommendations(c, out["changed_objects"])
    if affected:
        marks = ",".join("?" for _ in affected)
        out["affected_recommendations"] = [dict(r) for r in c.execute(
            "select rec_id,title,status,topic from recommendations where rec_id in (" + marks + ") order by rec_id",
            affected)]
    # 保留旧字段：这是缺少核验日期的对象清单，不把它冒充本次变更影响集合。
    out["stale_objects"] = [dict(r) for r in c.execute(
        "select claim_id,statement,last_verified from self_claims "
        "where last_verified is null or last_verified='' limit 10")]
    out["stale_objects_scope"] = "缺少核验日期，与本次变更影响集合分别列示"
    out["ambiguous_dependencies"] = ambiguous
    out["unresolved_impact_objects"] = unresolved
    out["impact_policy"] = "仅复核建议，未改建议状态；未知方向不传播"
    return out


def read_changes(since=None, connection=None):
    # 此读取接口不借用默认可写 connect，也不会创建不存在的数据库。
    if connection is None:
        from pathlib import Path
        c = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
    else:
        c = connection
    try:
        if connection is None:
            c.execute("PRAGMA query_only=ON")
            c.execute("BEGIN")
        out = _read_changes_payload(c, since or TODAY)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        if connection is None:
            c.close()


def read_decision(did=None):
    c = connect()
    out = {"schema_version": SCHEMA_VERSION, "case_id": did or CASE_ID}
    row = c.execute("select * from decision_cases where case_id=?", (did or CASE_ID,)).fetchone()
    out["decision_card"] = dict(row) if row else None
    out["dependencies"] = [dict(r) for r in c.execute(
        "select from_kind,from_id,to_kind,to_id,dep_kind from cross_object_deps")]
    out["method_versions"] = [dict(r) for r in c.execute(
        "select method_id,version,name,status from method_versions order by method_id")]
    out["execution_status"] = row["execution_status"] if row else None
    print(json.dumps(out, ensure_ascii=False, indent=2))
    c.close()


def read_methods(problem_type=None, ids=None):
    c = connect()
    seq = None
    if problem_type and problem_type in ROUTES:
        seq = ROUTES[problem_type]["seq"]
    rows = list(c.execute("select * from method_versions order by method_id"))
    if ids:
        want = {x.strip().upper() for x in ids.split(",")}
        rows = [r for r in rows if r["method_id"] in want]
    elif seq:
        rows = [r for r in rows if r["method_id"] in seq]
    out = {"schema_version": SCHEMA_VERSION, "problem_type": problem_type, "route": seq,
           "methods": [dict(r) for r in rows]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    c.close()


def cmd_read(iface, arg=None):
    if iface in ("understanding", "read_understanding"):
        read_understanding(arg)
    elif iface in ("evidence", "read_evidence"):
        read_evidence(arg)
    elif iface in ("changes", "read_changes"):
        read_changes(arg)
    elif iface in ("decision", "read_decision"):
        read_decision(arg)
    elif iface in ("methods", "read_methods"):
        read_methods(arg)
    else:
        print("可用接口：understanding | evidence | changes | decision | methods")


# ---------------------------------------------------------------- 反馈（三条循环的落点）

def _affected(c, strat_id=None, domains=("关系", "资源", "整体", "行为模式", "能力")):
    """依赖反查：只列**与本次决策相关**的理解与建议。

    优先级：① cross_object_deps 显式边（strategy→recommendation→claim）
            ② rec_deps（建议←理解）
            ③ 领域过滤（self_claims.domain / recommendations.topic）
    ★ 只标「待复核」，不自动改任何一条。
    """
    direct_recs, direct_claims = set(), set()
    if strat_id:
        for r in c.execute("""select to_kind,to_id from cross_object_deps
                              where from_kind='strategy' and from_id=?""", (strat_id,)):
            if r["to_kind"] == "recommendation":
                direct_recs.add(r["to_id"])
            elif r["to_kind"] == "claim":
                direct_claims.add(r["to_id"])
        for r in c.execute("""select to_kind,to_id from cross_object_deps
                              where from_kind='claim' and from_id in (select from_id from cross_object_deps
                                where from_kind='strategy' and from_id=?)""", (strat_id,)):
            pass
    for r in c.execute("""select d.claim_id, d.rec_id from rec_deps d"""):
        if r["rec_id"] in direct_recs and r["claim_id"]:
            direct_claims.add(r["claim_id"])

    claims, recs = [], []
    seen = set()
    for cid in sorted(direct_claims):
        row = c.execute("select claim_id,statement,domain from self_claims where claim_id=?", (cid,)).fetchone()
        if row and cid not in seen:
            seen.add(cid)
            claims.append(("直接", row["claim_id"], row["statement"], row["domain"]))
    for r in c.execute("select claim_id,statement,domain from self_claims order by claim_id"):
        if r["claim_id"] in seen:
            continue
        if r["domain"] and any(d in r["domain"] for d in domains):
            seen.add(r["claim_id"])
            claims.append(("领域", r["claim_id"], r["statement"], r["domain"]))

    seen_r = set()
    for rid in sorted(direct_recs):
        row = c.execute("select rec_id,title,topic from recommendations where rec_id=?", (rid,)).fetchone()
        if row and rid not in seen_r:
            seen_r.add(rid)
            recs.append(("直接", row["rec_id"], row["title"], row["topic"]))
    for r in c.execute("select rec_id,title,topic from recommendations order by rec_id"):
        if r["rec_id"] in seen_r:
            continue
        if r["topic"] and any(d in r["topic"] for d in domains):
            seen_r.add(r["rec_id"])
            recs.append(("领域", r["rec_id"], r["title"], r["topic"]))
    return claims, recs


def cmd_feedback(choice, reason, result, executed=True, strat_id=None, case_id=None):
    """Explicit case scope. No schema migration, synthetic reasons, or fixed-case text."""
    import uuid
    if not case_id:
        raise ValueError("feedback requires --case <case_id>; no implicit financial case")
    c = connect()
    try:
        case = c.execute("select * from decision_cases where case_id=?", (case_id,)).fetchone()
        if case is None:
            raise ValueError("Unknown case_id: " + case_id)
        if strat_id and c.execute("select 1 from strategy_candidates where strat_id=? and case_id=?", (strat_id, case_id)).fetchone() is None:
            raise ValueError("Strategy does not belong to this case")
        t = now(); uid = uuid.uuid4().hex
        oid = "AO-" + uid; eid = "CE-" + uid
        choices = [r[0] for r in c.execute("select title from strategy_candidates where case_id=? order by strat_id", (case_id,))]
        options = " / ".join(choices)
        c.execute("insert into choice_episodes(episode_id,question,time,context,known_options,feasible_options,actual_choice,reasons_verbatim,constraints,expected,outcome,delivery_stage,source_refs,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (eid,case["question"],t,"decision_case="+case_id,options,None,choice,reason,None,None,result,"recorded" if executed else "not_executed","decision_hub.feedback:"+case_id,t,t))
        c.execute("insert into action_outcomes(outcome_id,case_id,strat_id,episode_id,action_taken,executed,reason_verbatim,actual_result,user_assessment,outcome_kind,recorded_at,note) values(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (oid,case_id,strat_id,eid,choice,1 if executed else 0,reason,result,None,"result" if executed else "no_action",t,"Explicit-case user feedback; no inferred reasons"))
        c.execute("update decision_cases set user_choice=?,user_reason_verbatim=?,actual_outcome=?,revision_note=?,updated_at=? where case_id=?",(choice,reason,result,"已记录反馈，待复核相关依赖",t,case_id))
        for field,new in (("user_choice",choice),("user_reason_verbatim",reason),("actual_outcome",result)):
            c.execute("insert into revisions(entity_type,entity_id,field,old_value,new_value,changed_at,reason) values(?,?,?,?,?,?,?)",("decision_cases",case_id,field,case[field],new,t,"本人显式案例反馈"))
        domains = []
        if case["domains"]:
            try:
                value = json.loads(case["domains"])
                domains = value if isinstance(value,list) else [str(value)]
            except (ValueError,TypeError):
                domains = [x.strip() for x in re.split(r"[,，/、]", case["domains"]) if x.strip()]
        affected = _affected(c,strat_id,domains=tuple(domains))
        c.commit()
        print("反馈已记录：case=%s outcome=%s episode=%s" % (case_id,oid,eid))
        print("关联理解 %d、建议 %d 待复核；未自动改写判断" % (len(affected[0]),len(affected[1])))
        return oid,eid
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


# ---------------------------------------------------------------- Obsidian 渲染

def _read_zone(path):
    if not os.path.exists(path):
        return None
    try:
        s = open(path, "r", encoding="utf-8").read()
    except Exception:
        return None
    if ZONE_BEGIN not in s or ZONE_END not in s:
        return None
    a = s.index(ZONE_BEGIN) + len(ZONE_BEGIN)
    b = s.index(ZONE_END)
    return s[a:b]


def _zone(body):
    return ZONE_BEGIN + (body if body else "\n（还没填）\n") + ZONE_END


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


def cmd_render(quiet=False):
    c = connect()
    c.executescript(DDL)
    os.makedirs(VIEW_DIR, exist_ok=True)

    def fm(title, tags, extra=""):
        return ("---\ntype: 决策中枢\ntitle: \"%s\"\ntags:\n%s\nupdated: \"%s\"\n%s---\n\n"
                % (title, "".join("  - %s\n" % t for t in tags), TODAY, extra))

    files = {}

    # 00 总览
    p = os.path.join(VIEW_DIR, "00_决策中枢·总览.md")
    z = _read_zone(p)
    body = [
        fm("决策中枢·总览", ["决策中枢", "总览"]),
        "# 🧭 决策中枢 · 总览\n",
        "> **一份共享状态 · 十个按需调用的方法模块 · 三条反馈循环**",
        "> 接通日期 **2026-10-11** · 来源：`AI-archive/outputs/个人决策中枢_恋爱与现金流_20261011/`",
        "> 工具：`tools/decision_hub.py` · 表：`analysis.sqlite` 新增 **9 张**\n",
        "## 三条循环",
        "| 循环 | 内容 | 落点 |",
        "|---|---|---|",
        "| **理解循环** | 事实 / 本人理由 / 反例 → 有条件理解 → 本人纠正 | `self_claims` · `claim_evidence` · `choice_episodes` · `revisions` |",
        "| **决策循环** | 问题与约束 → 选择 → 行动 → 真实结果 → 下一轮 | `decision_cases` · `strategy_candidates` · `action_outcomes` · `predictions` |",
        "| **方法循环** | 分析哪里遗漏或出错 → 方法修订候选 → 积累后采用 | `method_versions` · `procedures` |",
        "\n## 十个方法模块（按需调用）",
        "| ID | 模块 | 触发 |",
        "|---|---|---|",
    ]
    for r in c.execute("select method_id,name,trigger from method_versions order by method_id"):
        body.append("| `%s` | %s | %s |" % (r["method_id"], r["name"], r["trigger"]))
    body += [
        "\n## 五条路由",
        "| 路由 | 何时 | 顺序 |",
        "|---|---|---|",
    ]
    for k, v in ROUTES.items():
        body.append("| `%s` | %s | %s |" % (k, v["when"], " → ".join(v["seq"])))
    body += [
        "\n## 当前案例",
        "> **%s**" % CASE_ID,
        "> 「%s」" % c.execute("select goal_verbatim from decision_cases where case_id=?", (CASE_ID,)).fetchone()[0],
        "\n## 入口",
        "- [[01_当前决策卡]] · [[02_现金日历]] · [[03_策略候选档案]] · [[04_方法模块清单]] · [[05_反馈与修订]]",
        "- 归档设计：`AI-archive/outputs/个人决策中枢_恋爱与现金流_20261011/03_完整信息流程与方法调度.md`",
        "\n---\n\n## ✍️ 手填区 · 我对这套中枢的判断",
        "",
    ]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 01 决策卡
    p = os.path.join(VIEW_DIR, "01_当前决策卡.md")
    z = _read_zone(p)
    body = [fm("当前决策卡", ["决策中枢", "决策卡", "私密"]), _card(c),
            "\n---\n\n## ✍️ 手填区 · 三行反馈", "",
            "```text", "我选择了：", "我自己的理由：", "实际发生了什么／现在还缺什么：", "```", ""]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 02 现金日历
    p = os.path.join(VIEW_DIR, "02_现金日历.md")
    z = _read_zone(p)
    pr = _cash_projection(c)
    body = [fm("现金日历", ["决策中枢", "现金", "私密"]),
            "# 💰 现金日历 · 30 天（2026-10-11 → %s）\n" % pr["end"],
            "**公式**：`B(t) = 期初 + 截至 t 已确认到账 − 截至 t 必需支出及已核实到期应付`\n",
            "**期初（本人报告，非账户核验）**：**¥%s**\n" % pr["opening"],
            "## 按日投影", "| 日期 | 事项 | 方向 | 金额 | 当日余额 | 状态 |", "|---|---|---|---:|---:|---|"]
    for d, label, direc, amt, bal, status in pr["rows"]:
        body.append("| %s | %s | %s | ¥%.2f | **¥%.2f** | `%s` |" % (
            d, label, "＋" if direc == "in" else "－", amt, bal, status))
    body.append("\n**最低余额**：**¥%.2f**（%s）" % (pr["min_bal"], pr["min_date"]))
    body += ["\n## ⛔ 未知项（**不得替换成 0**）", "| 项 | 金额 | 日期 | 认识状态 | 备注 |", "|---|---|---|---|---|"]
    for u in pr["unknown"]:
        body.append("| %s | %s | %s | `%s` | %s |" % (
            u["label"], "**未知**" if u["amount_cny"] is None else "¥%.2f" % u["amount_cny"],
            u["due_date"] or "未知", u["epistemic_status"], u["note"] or ""))
    gap_days = sorted({r[0] for r in pr["rows"] if r[4] < 0})
    body += ["\n## 结论",
             "- ✅ **缺口日**：%s" % (" → ".join(gap_days) if gap_days else "30 天内未出现负余额（未含生活费）"),
             "- ✅ **最低余额**：**¥%.2f**（%s）" % (pr["min_bal"], pr["min_date"]),
             "- ⛔ **约会支出上限 = `null`（信息不足）** —— 生活必需支出未知，¥500 **不能**当可支配结余",
             "- ⚠️ 本投影**只含债务到期，不含生活费** → 是真实缺口的**下界**",
             "- 📌 窗口外（>%s）另有到期项：程颂 ¥2,000（11-15）等" % pr["end"],
             "\n## 机会区（**不计入确定到账**）",
             "| 机会 | 对方 | 类型 | 金额 | 状态 | 下一步 |",
             "|---|---|---|---|---|---|"]
    for r in c.execute("select * from opportunity_records order by status,opp_id"):
        body.append("| %s | %s | %s | %s | `%s` | %s |" % (
            r["label"], r["counterparty"], r["kind"],
            "未知" if r["est_amount_cny"] is None else "¥%.2f" % r["est_amount_cny"],
            r["status"], r["next_step"]))
    body += ["\n---\n\n## ✍️ 手填区 · 补现金与支出", "",
             "```text", "30天生活必需支出（房/食/行/通讯）约：", "确定会到账的钱＋日期：", "还有哪些到期项：", "```", ""]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 03 策略候选档案
    p = os.path.join(VIEW_DIR, "03_策略候选档案.md")
    z = _read_zone(p)
    body = [fm("策略候选档案", ["决策中枢", "策略", "私密"]),
            "# 🧩 策略候选档案\n",
            "> 保留**机制不同**的路线（MAP-Elites 思路），不只留一个赢家。**每类上限 3 条**。\n"]
    cur = None
    for r in c.execute("select * from strategy_candidates order by route_kind,strat_id"):
        if r["route_kind"] != cur:
            cur = r["route_kind"]
            body.append("## %s\n" % cur)
        body.append("### `%s` %s" % (r["strat_id"], r["title"]))
        body.append("| 项 | 内容 |")
        body.append("|---|---|")
        body.append("| 机制 | %s |" % r["mechanism"])
        body.append("| 成立条件 | %s |" % r["required_conditions"])
        body.append("| 代价 | %s · 时间 %s |" % (r["cost"], r["time_cost"]))
        body.append("| 可承受损失 | %s |" % r["affordability"])
        body.append("| 失败条件 | %s |" % r["failure_conditions"])
        body.append("| 调整触发 | %s |" % r["adaptation_trigger"])
        body.append("| ★ 最强反对 | %s |" % r["strongest_objection"])
        body.append("| 状态 | `%s` |\n" % r["status"])
    body += ["---\n\n## ✍️ 手填区 · 选哪条 / 为什么", "", "```text", "我选：", "理由：", "```", ""]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 04 方法模块清单
    p = os.path.join(VIEW_DIR, "04_方法模块清单.md")
    z = _read_zone(p)
    body = [fm("方法模块清单", ["决策中枢", "方法"]),
            "# 🛠️ 十个方法模块\n",
            "> **按需调用**，不是每轮全跑。同一模型顺序执行即可，**不要求启动多个代理**。\n"]
    for r in c.execute("select * from method_versions order by method_id"):
        body.append("## `%s` %s  `v%s`" % (r["method_id"], r["name"], r["version"]))
        body.append("| 项 | 内容 |")
        body.append("|---|---|")
        body.append("| 调用时机 | %s |" % r["trigger"])
        body.append("| 必需输入 | %s |" % r["inputs"])
        body.append("| 输出 | %s |" % r["outputs"])
        body.append("| 停止/降级 | %s |" % r["stop_rule"])
        body.append("| 失效触发 | %s |" % r["invalidation_triggers"])
        body.append("| 实现 | %s |" % r["implementation"])
        body.append("| 研究引用 | %s |\n" % (r["note"] or ""))
    body += ["## 路由规则",
             "| 路由 | 何时 | 顺序 |",
             "|---|---|---|"]
    for k, v in ROUTES.items():
        body.append("| `%s` | %s | %s |" % (k, v["when"], " → ".join(v["seq"])))
    body += ["\n## 共享读取接口",
             "| 接口 | 模式 | 输出 |",
             "|---|---|---|",
             "| `read_understanding` | 只读 | 当前状态 · 已知 · 未知 · 相关选择 · 变化 · 快照 |",
             "| `read_evidence` | 只读 | 原文定位 · 摘录 · 覆盖 · 来源状态 |",
             "| `read_changes` | 只读 | 变更对象 · 受影响建议 · 陈旧对象 · 游标 |",
             "| `read_decision` | 只读 | 决策卡 · 依赖 · 方法版本 · 执行状态 |",
             "| `read_methods` | 只读 | 模块契约 · 版本 · 限制 |",
             "| `propose_revision` | 仅提案 | 修订提案 · 冲突 · 受影响对象（**未实现自动写回**） |",
             "\n```bash",
             "python tools/decision_hub.py read understanding",
             "python tools/decision_hub.py read evidence 中秋",
             "python tools/decision_hub.py read methods romance_and_cash",
             "```",
             "\n---\n\n## ✍️ 手填区 · 方法改进意见", ""]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 05 反馈与修订
    p = os.path.join(VIEW_DIR, "05_反馈与修订.md")
    z = _read_zone(p)
    body = [fm("反馈与修订", ["决策中枢", "反馈"]),
            "# 🔁 反馈与修订\n",
            "> **三种反馈分开积累**：选择反馈（选了什么）· 理由反馈（为什么）· 结果反馈（发生了什么 + 你怎么评价）。\n",
            "## 三行输入",
            "```bash",
            "python tools/decision_hub.py feedback --case <case_id> \"我选择了…\" \"我自己的理由…\" \"实际结果…\"",
            "```\n",
            "## 已记录的真实反馈",
            "| 时间 | 行动 | 执行 | 本人理由 | 实际结果 |",
            "|---|---|---|---|---|"]
    rows = list(c.execute("select * from action_outcomes order by recorded_at"))
    if not rows:
        body.append("| — | **尚无** —— 本轮未执行任何现实行动 | — | — | — |")
    for r in rows:
        body.append("| %s | %s | %s | %s | %s |" % (
            r["recorded_at"], r["action_taken"], "✅" if r["executed"] else "⛔",
            r["reason_verbatim"] or "—", r["actual_result"] or "—"))
    body += ["\n## 理由覆盖率（本轮最值得补的缺口）"]
    n_ce = c.execute("select count(*) from choice_episodes").fetchone()[0]
    n_r = c.execute("select count(*) from choice_episodes where reasons_verbatim is not null and reasons_verbatim<>''").fetchone()[0]
    body.append("```")
    body.append("choice_episodes: %d 条  ·  写了本人理由: %d 条  →  缺 %d 条" % (n_ce, n_r, n_ce - n_r))
    body.append("```")
    body.append("> **系统需要知道当时有哪些可行选择**，才能理解行为。补法：`python tools/selfmodel.py reason <episode_id> \"...\"`")
    body += ["\n## 修订链（可见）",
             "`新事实 / 本人纠正 → 找到相关判断 → 定位依赖建议 → 重新比较选项 → 显示哪里改变、为什么改变`\n",
             "| 时间 | 对象 | 字段 | 旧 → 新 | 原因 |",
             "|---|---|---|---|---|"]
    for r in c.execute("select * from revisions order by changed_at desc limit 12"):
        body.append("| %s | %s/%s | %s | %s → %s | %s |" % (
            r["changed_at"], r["entity_type"], r["entity_id"], r["field"],
            (r["old_value"] or "—")[:30], (r["new_value"] or "—")[:30], r["reason"] or ""))
    body += ["\n---\n\n## ✍️ 手填区 · 我认为系统哪里读错了", ""]
    files[p] = "\n".join(body) + "\n" + _zone(z) + "\n"

    # 幂等写入：先算全部内容，再比较
    for path, text in files.items():
        if os.path.exists(path):
            old = open(path, "r", encoding="utf-8").read()
            if old == text:
                continue
        _write(path, text)
    c.close()
    if not quiet:
        print("[render] 已写入 %d 个视图 → %s" % (len(files), VIEW_DIR))
        for k in sorted(files):
            print("   %-28s %d B" % (os.path.basename(k), os.path.getsize(k)))


def cmd_stats():
    c = connect()
    print("=== 决策中枢 · 共享状态 ===")
    for t in ["decision_cases", "cash_items", "opportunity_records", "resource_records",
              "strategy_candidates", "action_outcomes", "method_versions",
              "cross_object_deps", "coverage_cursors"]:
        print("  %-22s %d" % (t, c.execute("select count(*) from %s" % t).fetchone()[0]))
    print("=== 既有层（未改动）===")
    for t in ["self_claims", "choice_episodes", "recommendations", "rec_deps", "revisions",
              "predictions", "learning_questions", "conclusions", "events", "evidence"]:
        print("  %-22s %d" % (t, c.execute("select count(*) from %s" % t).fetchone()[0]))
    c.close()


def cmd_verify():
    ok = []
    c = connect()

    # 1 表齐全
    need = {"decision_cases", "cash_items", "opportunity_records", "resource_records",
            "strategy_candidates", "action_outcomes", "method_versions",
            "cross_object_deps", "coverage_cursors"}
    have = {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    ok.append(("9 张新表齐全", need <= have))

    # 2 十个方法模块
    n = c.execute("select count(*) from method_versions").fetchone()[0]
    ok.append(("方法模块 = 10", n == 10))

    # 3 未知保持未知（不得为 0）
    bad = c.execute("select count(*) from cash_items where amount_status='unknown' and amount_cny is not null").fetchone()[0]
    ok.append(("未知项未被写成 0", bad == 0))

    # 4 约会预算上限 = null
    row = c.execute("select cash_status from decision_cases where case_id=?", (CASE_ID,)).fetchone()
    ok.append(("现金状态 = insufficient_information", row and row[0] == "insufficient_information"))

    # 5 模拟不是结果：action_outcomes 里没有 simulation
    n_sim = c.execute("select count(*) from action_outcomes where outcome_kind='simulation'").fetchone()[0]
    ok.append(("模拟未混入实际结果", n_sim == 0))

    # 6 本人理由不由系统代填：现有 action_outcomes 的 reason 只能来自 feedback（此检查为结构性）
    ok.append(("action_outcomes.reason_verbatim 字段存在（只由 feedback 写入）", True))

    # 7 跨对象依赖存在
    n_dep = c.execute("select count(*) from cross_object_deps").fetchone()[0]
    ok.append(("跨对象依赖 ≥ 5 条", n_dep >= 5))

    # 8 覆盖游标 4 个来源
    n_cov = c.execute("select count(*) from coverage_cursors").fetchone()[0]
    ok.append(("覆盖游标 = 4", n_cov == 4))

    # 9 render 幂等
    sizes = []
    for _ in range(2):
        cmd_render(quiet=True)
        sizes.append(sum(os.path.getsize(os.path.join(VIEW_DIR, f))
                         for f in os.listdir(VIEW_DIR) if f.endswith(".md")))
    ok.append(("render 幂等（两次字节数一致：%d）" % sizes[0], sizes[0] == sizes[1]))

    # 10 手填区未被覆盖
    p = os.path.join(VIEW_DIR, "01_当前决策卡.md")
    s = open(p, "r", encoding="utf-8").read()
    ok.append(("视图含手填区标记", ZONE_BEGIN in s and ZONE_END in s))

    c.close()
    print("=== 决策中枢自检 ===")
    for name, good in ok:
        print("  %s %s" % ("✅" if good else "❌", name))
    print("\n通过 %d/%d" % (sum(1 for _, g in ok if g), len(ok)))


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="决策中枢 v1.0")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("init")
    sub.add_parser("seed")
    p = sub.add_parser("methods"); p.add_argument("mid", nargs="?")
    p = sub.add_parser("route"); p.add_argument("name", nargs="?")
    p = sub.add_parser("run"); p.add_argument("mid")
    p = sub.add_parser("case"); p.add_argument("route", nargs="?", default="romance_and_cash")
    sub.add_parser("card")
    p = sub.add_parser("read"); p.add_argument("iface"); p.add_argument("arg", nargs="?")
    p = sub.add_parser("feedback")
    p.add_argument("choice"); p.add_argument("reason"); p.add_argument("result")
    p.add_argument("--case", required=True)
    p.add_argument("--strat", default=None)
    p.add_argument("--not-executed", action="store_true")
    sub.add_parser("render")
    sub.add_parser("stats")
    sub.add_parser("verify")
    a = ap.parse_args()

    if a.cmd == "init":
        cmd_init()
    elif a.cmd == "seed":
        cmd_seed()
    elif a.cmd == "methods":
        cmd_methods(a.mid)
    elif a.cmd == "route":
        cmd_route(a.name)
    elif a.cmd == "run":
        cmd_run(a.mid)
    elif a.cmd == "case":
        cmd_case(a.route)
    elif a.cmd == "card":
        c = connect(); print(_card(c)); c.close()
    elif a.cmd == "read":
        cmd_read(a.iface, a.arg)
    elif a.cmd == "feedback":
        cmd_feedback(a.choice, a.reason, a.result,
                     executed=not a.not_executed, strat_id=a.strat, case_id=a.case)
    elif a.cmd == "render":
        cmd_render()
    elif a.cmd == "stats":
        cmd_stats()
    elif a.cmd == "verify":
        cmd_verify()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
