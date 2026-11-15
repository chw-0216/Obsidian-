# EVENT-REVIEW-DEEP-DRYRUN-REPORT · 深度预填复核包 dry-run

- 生成时间：2026-08-07T00:31:00+08:00
- 阶段：event-center-phase1 · 0 API
- 来源：`src/v3_events.py`（候选发现 + 预填档案）+ `src/v3_event_review.py`（复核包/HTML）
- 数据库：工作区副本 `data/wechat-analysis-v3.sqlite3`（只写 `_v3_event_*` 表）

## 1. 本阶段落地内容（DEEP-REVIEW-SPEC 强制要求）

### 改动一：深度预填判断档案（数据契约 + schema）

- `_v3_event_candidates` 新增列：`analysis_status`（当前全为 `retrieval_ready`）、
  `analysis_profile_json`（219/219 候选均写入）、`confidence`（全 NULL，无 API 阶段不伪造置信度）。
- 幂等补列迁移：老库缺列时 `ALTER TABLE ADD COLUMN`，重复 `ensure_event_schema` 不报错（已测试）。
- 预填档案结构（`analysis_profile`，schema_version=prefill-profile-1.0）：
  - `facts[]`：仅确定性可推导事实（时间范围/参与者/主导任务/解析日期/关键实体），
    每条带 `status`(fact/inferred/unknown)、`confidence`、`evidence_ids`（可回链 `eve_*`）。
  - 深度槽位（**无 API 阶段一律为空/None，绝不假装模型已推理**）：
    `deep_hypotheses`、`alternative_hypotheses`、`relationship_profile`、
    `value_assumptions`、`communication_advice`。
  - `counter_evidence`：反证槽位，本阶段保留为空数组，但 schema 与复核页均展示该槽位。
  - `conclusion_stability`：`assess_stability(supporting_events)`，<3 个独立已确认事件 → `tentative`。

### 改动二：低负担人工确认界面（event_review.html）

- 每张卡**首屏展示预填档案**：analysis_status 横幅（"待深度分析"）、facts 列表、
  六大槽位（含反证槽位）、暂定假设标记、时间/联系人/实体/线索元信息、证据包（可折叠）。
- 主要操作：确认 / 部分正确 / 错误 / 拒绝；改名（title_override）、角色修正、
  期望/价值/建议修正、价值分、保留建议、合并/拆分、**一句真实背景补充**（note）。
- **模型猜测与用户修正并存**：`user_correction` 以 `{field: {guess, corrected, reason}}` 记录；
  `model_guess`（原预填档案快照）随反馈一起导出。
- 导出 `event_review_feedback.jsonl` → `load_event_feedback` 校验 → `apply_event_feedback`
  幂等 upsert 到 `_v3_event_review`（新增 `user_verdict` / `user_correction_json` / `model_guess_json`）。
- localStorage 自动保存，可刷新续接；支持重导反馈 JSONL。

## 2. 候选发现统计（与上一里程碑一致，未回退）

| 指标 | 值 |
|---|---|
| 扫描会话 | 718（排除 7） |
| 文本消息扫描 | 57,356 |
| 信号消息 | 9,390 |
| 活动段 runs | 2,178 |
| 候选总数 | 219 |
| 跨联系人候选 | 103 |
| 多日候选 | 96 |
| 关键上下文候选 | 103 |

## 3. 复核包与渲染

- 复核包：`runs/event_review_p1_deep/event_review_bundle.json`（30 候选，schema_version=event-review-1.1）
- HTML：`runs/event_review_p1_deep/event_review.html`（数据内嵌，无服务器；注入 `<` 已转义，`</script>` 计数 =1）
- top30 覆盖四大关键上下文：周冉/校友会（5+）、格拉（5+）、井邻（2）、舒哥（3）、陈老师（1）等

## 4. 预填档案抽查（候选 evc_5e302c7e6815d11e · 周冉 · 报名/申请）

- analysis_status: `retrieval_ready`；facts=5 条（时间范围 fact/1.0、联系人 fact/1.0、主导任务 fact/0.8、…）
- 深度槽位：deep_hypotheses=[]、alternative_hypotheses=[]、relationship_profile=None、value_assumptions=[]
- counter_evidence=[]（槽位存在）
- conclusion_stability: `tentative`（0/3 已确认事件）
- 证据回链：363 条证据均在 snapshot 内，evidence_id 可回链 `message_id`

## 5. 无 API 测试覆盖（54/54 全绿，其中事件测试 12 个）

| 测试 | 断言 |
|---|---|
| `test_profile_has_traceable_facts` | facts 带 status/confidence/evidence_ids，confidence 为 None |
| `test_profile_deep_slots_empty_honest` | 深度槽位为空/None，note 明示"待深度分析" |
| `test_counter_evidence_slot_exists` | 反证槽位存在 |
| `test_stability_tentative_below_three` | 0/1/2→tentative，3/4→stable |
| `test_apply_feedback_idempotent` | 同一反馈重导两次行数不变 |
| `test_model_guess_and_user_correction_coexist` | model_guess_json 与 user_correction_json 并存、内容分别可读 |
| `test_export_import_roundtrip_feedback` | 导出→load→落库行数一致 |
| `test_load_feedback_rejects_bad_verdict` | 非法 user_verdict 被拒 |
| `test_event_schema_has_analysis_columns` / `test_schema_migration_idempotent_on_existing` | schema 列齐全、补列幂等 |
| `test_render_html_shows_prefill_and_slots` | HTML 首屏含"待深度分析/反证/暂定假设/用户修正"，`</script>` 计数=1 |

## 6. 诚实边界确认

- **无 API 阶段未调用任何 API**；219 候选的 `analysis_status` 全为 `retrieval_ready`，`confidence` 全 NULL。
- 深度槽位全部为空/None，未以任何模型输出填充；复核页横幅明确"模型级深度推理未执行"。
- 历史表（annotations / aggressive_* / contact_*）未改动；只新建/更新 `_v3_event_*` 表。
- 证据、联系人、复核、最终判断全部可回链 `message_id` / `segment_id` / `candidate_id`。

## 7. 30 候选人工复核已完成并落库（2026-08-07）

- 复核方式：生成 `event_review_feedback.draft.jsonl`（30 行预填草稿，判定结合原文证据）+ 可读预览页
  `event_review_feedback.draft.preview.html`，用户确认后直接 finalize（0 API）。
- 落库：`_v3_event_review` 30 行（confirmed 11 / split 1 / rejected 12 / pending 6）；
  `_v3_event_judgments` 13 个最终事件（11 确认 + 1 拆分为 2）。
- `user_correction` 与 `model_guess` 并存：30/30 行均落库。
- 事件聚合规则：confirmed → 单事件；split → 每部件一事件；rejected / pending → 不落最终判断。

### 最终事件清单（13 个，含 keep 建议）

| 事件 | keep | 拆分部件 |
|---|---|---|
| 2025中秋联谊会·筹备报名 | keep | |
| 求职简历投递·老师沟通 | keep | |
| 客座教授上课通知·卫生安排 | keep | |
| 周三去乡村美育站 | keep | |
| 学生拟录取+下乡学习申请 | keep | |
| 校友会·奥森橄榄球联谊赛 | keep | |
| 格拉求职面试咨询 | keep | |
| 与舒哥钓鱼 | keep | |
| 邵老师研学·周三面谈 | keep | |
| 校友会公众号事务 | keep | |
| 关心朋友健康·电暖器 | keep | |
| 和舒哥聚会（拆分自 0bbe02） | pending | |
| 打折机票/跨国托运咨询（拆分自 0bbe02） | pending | |

### 判定要点与诚实边界

- 12 个 rejected 候选均为聚类质量问题（多会话/多主题被并成单候选），已记录理由，不落最终判断。
- 6 个 pending 候选（c95d8a/c104d9/5b08a4/d70d5f/9a44d9/c87bbc）留待用户进一步确认，不落最终判断。
- 判定基于原文证据 quote 的推断，用户已口头确认"差不多正确"；如需修正可重导草稿再跑 finalize（幂等）。

## 8. 待确认项（下一步暂停点）

1. **深度分析 token 计划待用户确认**：当前仅完成无 API 阶段预填档案框架。
   若要对已确认的高信号候选执行模型级深度推理（填充 deep_hypotheses /
   alternative_hypotheses / counter_evidence / relationship_profile / value_assumptions /
   communication_advice），需先给出每事件包大小与 token 预测，经用户确认后分批执行。
2. **6 个 pending 候选**可继续人工确认；重导 `event_review_feedback.draft.jsonl` 修改后重新 finalize（幂等）。
3. **扩大候选规模**：当前仅 30 候选（top30）。如需覆盖更多高信号候选，调整 bundle 生成参数重新生成。
