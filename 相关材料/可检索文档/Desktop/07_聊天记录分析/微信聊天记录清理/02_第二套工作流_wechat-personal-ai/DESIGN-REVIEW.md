# DESIGN-REVIEW.md

> 生成时间：2026-08-02
> 状态：DESIGN_ONLY — 框架设计完成，待用户审批

## 已完成

### 1. 目录结构（26个文件）

```
wechat-personal-ai/
├─ README.md                           ✅
├─ CLAUDE.md                           ✅
├─ DESIGN-REVIEW.md                    ✅（本文件）
├─ config/
│  ├─ permissions.yaml                 ✅ 运行模式与权限门
│  ├─ budgets.yaml                     ✅ Token/成本预算
│  └─ label-taxonomy.yaml              ✅ 标签体系定义
├─ schemas/
│  ├─ round-1-observation.schema.json  ✅ 可观察事实
│  ├─ round-2-relationship.schema.json ✅ 关系模型
│  ├─ round-3-self-pattern.schema.json ✅ 自我模式
│  ├─ round-4-coaching.schema.json     ✅ 沟通教练
│  └─ round-5-digital-twin.schema.json ✅ 数字分身
├─ prompts/
│  ├─ round-1-observation.md           ✅ R1 提示词
│  ├─ round-2-relationship.md          ✅ R2 提示词
│  ├─ round-3-self-pattern.md          ✅ R3 提示词
│  ├─ round-4-roleplay.md              ✅ R4 角色扮演
│  └─ round-5-persona.md               ✅ R5 Persona
├─ src/
│  ├─ inventory.py                     ✅ R0 数据盘点
│  ├─ normalize.py                     ✅ 数据规范化
│  ├─ select_samples.py                ✅ 样本选择
│  ├─ run_round.py                     ✅ 轮次执行器
│  ├─ verify_evidence.py               ✅ 证据链验证
│  └─ export_review.py                 ✅ 审核导出
├─ reviews/
│  ├─ user-confirmed-facts.jsonl       ✅ 用户确认的事实
│  ├─ rejected-inferences.jsonl        ✅ 用户否决的推断
│  └─ corrections.jsonl                ✅ 用户纠正
├─ digital-twin/
│  ├─ PRIVATE-MEMORY.md                ✅ 私有记忆
│  ├─ PUBLIC-PERSONA.md                ✅ 公开人设
│  ├─ COMMUNICATION-STYLE.md           ✅ 沟通风格
│  ├─ UNCERTAINTY-RULES.md             ✅ 不确定性规则
│  └─ SYSTEM-PROMPT.md                 ✅ 系统提示词
└─ tests/
   └─ synthetic-test-data.json         ✅ 合成测试数据
```

### 2. 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据库 | 独立于旧系统 | 新增表结构（observations/relationships/patterns/coaching/persona） |
| ID 策略 | 继承确定性 SHA-256 | 幂等可重放 |
| 证据链 | 每个结论引用 msg_id/segment_id | 可追溯到原始证据 |
| 标签体系 | 7大类 + 禁止列表 | 只保留可复核标签 |
| 提示词 | 5轮独立模板 | 每轮有明确的分析边界 |
| 模式门 | 5种运行模式 | 控制任务范围和成本 |
| 记忆分层 | 9个记忆块 | 严格区分确认/推断/公开/私有 |

## 待用户选择项

### 1. 运行模式切换

当前：`design_only`

需要你确认：
- [ ] 切换到 `pilot` 模式，先用少量样本校准
- [ ] 还是直接切换到 `standard` 模式，全量处理

### 2. 预算确认

当前设置：
- R1（可观察事实）：$5.00，50批
- R2（关系模型）：$8.00，30批
- R3（自我模式）：$3.00，5批
- R4（沟通教练）：$2.00，3批
- R5（数字分身）：$2.00，3批
- 全局上限：$20.00

需要你确认：
- [ ] 预算是否合适
- [ ] 是否需要调整某轮的预算

### 3. 数据范围

当前设置：全部私聊（725个会话，71,550条消息）

需要你确认：
- [ ] 是否包含文件传输助手（3,903条，主要是笔记和AI对话）
- [ ] 是否包含美团等服务号（597条）
- [ ] 是否有不想被分析的联系人

### 4. 标签体系扩展

当前 topic 列表：工作、学习、家庭、朋友、情感、消费、出行、摄影、创作、健康、租房、校友会、艺术项目、AI技术、金融理财、考研备考、日常闲聊、其他

需要你确认：
- [ ] 是否需要添加其他主题
- [ ] 是否需要添加其他意图类型

### 5. 数字分身用途

当前设置：仅本地使用，不公开

需要你确认：
- [ ] 数字分身是否需要与他人互动
- [ ] 如果是，哪些信息可以公开
- [ ] 是否需要设置"联系人可见性"（某些人可以看到更多）

### 6. 沟通教练方向

基于已有分析，你可能想改善的方向：
- [ ] 时间管理（经常拖延、说"过两天"）
- [ ] 边界设定（难以拒绝人）
- [ ] 冲突处理（在亲密关系中回避）
- [ ] 求助方式（经济困难时的表达）
- [ ] 其他：___

## 与旧系统的关系

| 方面 | 旧系统 (WeChat-MiMo-Analyzer) | 新系统 (wechat-personal-ai) |
|------|------|------|
| 数据库 | `wechat-private-v2.sqlite3` | 独立数据库 |
| 分析单位 | 片段（segment） | 片段 → 关系 → 自我 → 教练 → Persona |
| 标注深度 | 单轮结构化标注 | 多轮递进分析 |
| 用户参与 | 无 | 确认/否决/纠正机制 |
| 产物 | overview.md | 记忆系统 + 沟通教练 + 数字分身 |

两个系统独立运行，新系统引用旧系统的 segment_id 和 msg_id 作为证据。

## 下一步

1. 你确认上述选择项
2. 切换 `RUN_MODE` 到 `pilot` 或 `standard`
3. 开始执行 R0（数据盘点）
4. 逐步执行 R1 → R5
