# wechat-personal-ai 系统设计计划

## Context

用户蔡浩文已有 WeChat-MiMo-Analyzer（数据清洗+分段+单轮标注），现在要升级为完整的三合一系统：
1. 个人记忆系统（可检索、可更新、可追溯）
2. 沟通教练（基于记忆系统的可验证练习）
3. 数字分身（明确标识为 AI）

当前模式：DESIGN_ONLY — 只生成框架、Schema、提示词、模板，不运行分析。

## 交付清单

### 1. 目录结构（26个文件）

```
wechat-personal-ai/
├─ README.md                          # 项目说明
├─ CLAUDE.md                          # Claude Code 规则
├─ DESIGN-REVIEW.md                   # 待用户选择项
├─ config/
│  ├─ permissions.yaml                # 运行模式与权限门
│  ├─ budgets.yaml                    # Token/成本预算
│  └─ label-taxonomy.yaml             # 标签体系定义
├─ schemas/
│  ├─ round-1-observation.schema.json # 可观察事实
│  ├─ round-2-relationship.schema.json # 关系模型
│  ├─ round-3-self-pattern.schema.json # 自我模式
│  ├─ round-4-coaching.schema.json    # 沟通教练
│  └─ round-5-digital-twin.schema.json # 数字分身
├─ prompts/
│  ├─ round-1-observation.md          # R1 提示词
│  ├─ round-2-relationship.md         # R2 提示词
│  ├─ round-3-self-pattern.md         # R3 提示词
│  ├─ round-4-roleplay.md             # R4 角色扮演
│  └─ round-5-persona.md              # R5 Persona
├─ src/
│  ├─ inventory.py                    # R0 数据盘点
│  ├─ normalize.py                    # 数据规范化
│  ├─ select_samples.py               # 样本选择
│  ├─ run_round.py                    # 轮次执行器
│  ├─ verify_evidence.py              # 证据链验证
│  └─ export_review.py                # 审核导出
├─ reviews/
│  ├─ user-confirmed-facts.jsonl      # 用户确认的事实
│  ├─ rejected-inferences.jsonl       # 用户否决的推断
│  └─ corrections.jsonl               # 用户纠正
├─ digital-twin/
│  ├─ PRIVATE-MEMORY.md               # 私有记忆
│  ├─ PUBLIC-PERSONA.md               # 公开人设
│  ├─ COMMUNICATION-STYLE.md          # 沟通风格
│  ├─ UNCERTAINTY-RULES.md            # 不确定性规则
│  └─ SYSTEM-PROMPT.md                # 系统提示词
└─ tests/
   └─ synthetic-test-data.json        # 合成测试数据
```

### 2. 五份 JSON Schema 设计要点

**Round 1 — observation.schema.json**
- 核心：segment_id, time_range, topic, goals, events, action_items, tone_observed, evidence_msg_ids, confidence
- 禁止：人格标签、关系定性、心理诊断
- action_items 结构：responsible, task, status, deadline

**Round 2 — relationship.schema.json**
- 核心：contact_id, contact_name, timeline, themes, initiation_pattern, boundaries, conflicts, repair_events, pending_items, explanations[], user_confirmed
- explanations 结构：hypothesis, supporting_evidence_ids, contradicting_evidence_ids, confidence

**Round 3 — self-pattern.schema.json**
- 三列结构：stable_observations[], contextual_behaviors[], unverified_hypotheses[]
- 每个模式：dimension, description, evidence_ids, frequency, scenarios
- 维度：initiation, clarity, listening, response_length, need_expression, conflict_reaction, gratitude, consistency

**Round 4 — coaching.schema.json**
- 每条建议：situation, current_pattern, desired_outcome, new_behavior, example_phrasing[], practice_roleplay, success_signal, review_date, evidence_ids, confidence
- 约束：每月最多3项，不以操控为目标

**Round 5 — digital-twin.schema.json**
- 记忆块：identity, values, preferences, communication_style, episodic_memory, relationship_context, current_projects, uncertainty, public_persona
- 每块：content, source, user_confirmed, created_at, updated_at, expires_at

### 3. 五份提示词模板设计要点

- R1：严格只观察，不推断，输出结构化 JSON
- R2：基于 R1 结果分析关系动态，支持多个解释假设
- R3：跨关系找模式，三列分类（稳定/情境/待验证）
- R4：生成可执行的沟通实验，含角色扮演场景
- R5：构建分层记忆，严格区分确认/推断/公开/私有

### 4. 配置文件

- permissions.yaml：5种运行模式的数据范围、模型调用、产物定义
- budgets.yaml：每轮/每批/总量的 Token 和成本限制
- label-taxonomy.yaml：topic/intent/event/tone/interaction/action_item/evidence 七大类

### 5. 证据链验证

- verify_evidence.py：检查引用的 msg_id/segment_id 是否存在于数据库
- 检查结论是否超出证据范围
- 检查是否存在跨联系人串线

### 6. 用户确认机制

- user-confirmed-facts.jsonl：用户确认的稳定事实
- rejected-inferences.jsonl：用户否决的模型推断
- corrections.jsonl：用户对错误的纠正

### 7. 数字分身隔离

- PRIVATE-MEMORY.md：不可公开的完整记忆
- PUBLIC-PERSONA.md：可公开的人设
- UNCERTAINTY-RULES.md：何时说"不确定"、何时建议联系本人

### 8. DESIGN-REVIEW.md

列出所有待用户选择的决策项。

## 与现有系统的关系

- 数据源复用 WeChat-MiMo-Analyzer 的 `wechat-private-v2.sqlite3`
- 新系统有自己的数据库（含 observation/episode/memory_item/relationship/pattern/coaching_experiment/persona_rule 表）
- 新系统可引用旧系统的 segment_id 和 msg_id 作为证据
- 旧系统继续独立运行，新系统不覆盖它

## 实施顺序

1. README.md + CLAUDE.md
2. config/ 三个配置文件
3. schemas/ 五个 JSON Schema
4. prompts/ 五个提示词模板
5. src/ 六个 Python 模块（骨架+docstring，不含真实分析逻辑）
6. reviews/ 三个 JSONL 模板
7. digital-twin/ 五个 MD 模板
8. tests/synthetic-test-data.json
9. DESIGN-REVIEW.md

## 验证方式

- JSON Schema 通过 jsonschema 库验证合成数据
- 提示词模板不含真实联系人或真实摘要
- 所有 src/ 文件可 import 无报错
- DESIGN-REVIEW.md 列出所有待决策项
