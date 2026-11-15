# Claude Code＋小米 MiMo：微信数据一键完整总流程

> 这是最终整合版，不需要再手动拼接 04—07。直接把本文“总执行指令”交给 Claude Code。当前 Codex 只生成流程，不执行真实聊天分析。

## 一、最终目标

将全部 WeFlow 私聊转换为一个持续可用的个人 AI 系统：

```text
WeFlow 全量私聊
  ↓
无上限细粒度标注与语义理解
  ↓
统一个人记忆系统
  ↓
最激进的自我、关系与社交网络判断
  ↓
沟通改善、角色扮演和行为实验
  ↓
私人数字分身 T0—T2
  ↓
证据审计、用户纠错和增量更新
```

三个最终产品共用同一证据链：

1. **个人记忆系统**：保存人物、事件、经历、项目、观点、偏好和承诺；
2. **沟通改善系统**：分析沟通模式、关系互动并设计可验证练习；
3. **数字分身**：使用同一记忆库进行回忆、写作、表达和互动。

## 二、既定条件

```yaml
data_owner: 蔡浩文
data_scope: all_private_chats
redaction: none
include_contact_names: true
allow_remote_mimo_analysis: true
privacy_as_analysis_constraint: false
allow_modify_source_export: false
allow_delete_source_export: false
allow_external_messages: false
allow_automatic_replies: false
allow_system_wide_install: false
log_api_token: false
```

Token Plan 当天到期，因此：

- 不设置项目内部 Token 软上限；
- 不设置单联系人和单片段额度；
- 在实际账号额度、接口承载、到期时间和磁盘允许范围内持续执行；
- 不通过重复废话或翻译循环消耗 Token；
- Token 优先用于扩大覆盖、上下文修正、复标、反证和可长期保存的语义资产。

## 三、现有基础

优先复用，不从零重建：

```text
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer
```

已知规模约为：

- 725 个有效私聊；
- 71,550 条消息；
- 6,303 个对话片段；
- 已有 SQLite FTS5 检索和部分 MiMo 结构化标注能力。

原始 WeFlow 导出始终只读，所有清洗、标注、记忆和报告写入派生数据层。

## 四、Stage 0：启动前检查

### 任务

1. 检查现有项目、数据库、脚本、配置、已完成结果和失败记录；
2. 验证 MiMo 连接，但不在日志输出 Token；
3. 检查磁盘空间、到期剩余时间和接口基础吞吐；
4. 建立新的运行目录和 manifest；
5. 识别已成功标注的输入哈希，禁止重复调用；
6. 用少量合成或已完成样本验证 JSON Schema、证据回链和写盘。

### 产物

```text
runs/<run_id>/run-manifest.json
runs/<run_id>/expiry-harvest-status.json
runs/<run_id>/existing-assets-inventory.json
runs/<run_id>/resume-queue.jsonl
```

### 通过门

- 原始数据路径确认只读；
- MiMo 调用成功；
- 结构化结果可原子化落盘；
- 断点重启不会重复成功调用。

## 五、Stage 1：无上限全量标注理解

这是最高优先级。在基础标注覆盖完成前，不把主要算力转向最终人格判断或数字分身。

### Pass A：消息级原子标注

覆盖全部消息，包括短回复、表情、媒体占位和系统消息：

- 内容功能；
- 主题；
- 言语行为；
- 意图；
- 请求、承诺和边界；
- 人物、地点、项目、时间和事件；
- 可观察语气；
- 推断情绪和需求候选；
- 关系信号；
- 沟通行为；
- 表达风格；
- 记忆候选；
- 歧义和置信度。

### Pass B：片段上下文标注

读取连续对话，修正孤立消息误读：

- 对话触发和真实目标；
- 回复关系和省略指代；
- 主题转移；
- 请求—回应—结果链；
- 语气和情绪转折；
- 决定、承诺、冲突、修复和未完成事项。

### Pass C：跨片段实体与事件合并

- 合并人物别名、备注名变化和同一项目；
- 串联事件的预告、发生、复盘和后续；
- 串联承诺的提出、延期、完成或取消；
- 保留无法确定的多个候选，不强行合并。

### Pass D：九维语义深描

从内容、行动、关系、情绪、需求、身份、风格、记忆和不确定性九个维度独立标注。

### Pass E：独立复标与证据裁判

高信息量片段进行独立双标；人物、事件、承诺、边界、关系信号或置信度出现分歧时，由第三轮读取原文裁判。

### Pass F：全局一致性回扫

检查人物串线、同名误合并、时间冲突、承诺状态、观点归属、引用转述、偏好变化和跨对话事件。

### 覆盖目标

```yaml
message_coverage: 1.00
segment_coverage: 1.00
contact_coverage: 1.00
schema_validation_rate: 1.00
evidence_link_rate: 1.00
unresolved_model_failures: 0
```

### 产物

```text
annotations/messages/
annotations/segments/
annotations/contacts/
annotations/entities/
annotations/events/
annotations/semantics/
annotations/memory-candidates/
annotations/disagreements/
annotations/verdicts/
annotations/unresolved/
annotations/label-taxonomy.json
annotations/annotation-manifest.json
annotations/ANNOTATION-COVERAGE.md
```

## 六、Stage 2：个人记忆系统

Stage 1 基础覆盖完成后，把标注整合成可更新记忆。

### 记忆类型

| 类型 | 内容 |
|---|---|
| identity | 身份、经历和长期角色 |
| episodic | 带时间和证据的具体事件 |
| semantic | 知识、观点和经验总结 |
| relationship | 联系人关系上下文和共同经历 |
| preference | 喜好、习惯和表达偏好 |
| current_state | 当前项目、目标和未完成事项 |
| communication_style | 表达结构、语气和叙事方式 |
| uncertainty | 冲突、待确认和可能过期信息 |

### 每条记忆字段

```yaml
memory_id: 稳定 ID
type: 记忆类型
content: 结构化内容
status: observed | inferred | confirmed | rejected | expired
time_range: null
people_ids: []
event_ids: []
evidence_ids: []
evidence_against: []
confidence: 0-1
conflicts_with: []
expires_at: null
model_version: null
prompt_version: null
user_note: null
```

### 产物

```text
memory/personal-memory.jsonl
memory/life-timeline.jsonl
memory/contact-memories/
memory/relationship-events.jsonl
memory/preferences-and-values.json
memory/current-projects.json
memory/unresolved-commitments.jsonl
memory/uncertainties.jsonl
memory/memory-index.sqlite3
```

### 通过门

- 每条记忆可回到证据；
- 重复事件完成合并；
- 冲突版本同时保存；
- 他人观点不归到本人；
- 旧偏好可以标记过期。

## 七、Stage 3：最激进分析判断

分析范围从内容总结扩展到：

1. 深层自我、核心需求和价值冲突；
2. 真实自我、理想自我和对外呈现之间的差异；
3. 单段关系的主动性、互惠、权力、核心张力和修复能力；
4. 全部社交网络的核心圈、弱联系、桥梁人物和单向投入；
5. 沟通微行为和反复循环；
6. 盲点、自我矛盾和可能的自我欺骗；
7. 人生阶段、身份转型和未完成主题；
8. 关系与人生的条件预测；
9. 哪些关系适合深化、修复、重连、保持、观察或降低投入。

### 四级判断

```text
L0：原文直接事实
L1：多证据支持的强推断
L2：需要验证的弱假设
L3：基于条件的未来情景
```

每个 L1—L3 判断必须给：支持证据、反证、替代解释、置信度、判断错误代价、验证问题和低后悔行动。

### 五角色人格法庭

重要结论由以下角色独立分析：

- 检察官：提出最尖锐解释；
- 辩护人：寻找情境和善意解释；
- 关系研究者：分析互动结构；
- 未来预测者：分析条件不变与改变后的情景；
- 证据法官：根据原文和证据等级裁决。

### 产物

```text
deep-analysis/MASTER-SELF-MODEL.md
deep-analysis/CORE-NEEDS-AND-CONFLICTS.md
deep-analysis/BLIND-SPOTS-AND-CONTRADICTIONS.md
deep-analysis/LIFE-TRANSITIONS.md
deep-analysis/SOCIAL-NETWORK-ATLAS.md
deep-analysis/RELATIONSHIP-PRIORITIES.md
deep-analysis/RELATIONSHIP-FORECASTS.md
deep-analysis/COMMUNICATION-MICRO-PATTERNS.md
deep-analysis/TOP-12-HARD-QUESTIONS.md
deep-analysis/LOW-REGRET-ACTIONS.md
deep-analysis/judgments.jsonl
deep-analysis/counter-evidence.jsonl
deep-analysis/contact-cards/
```

不做精神疾病、临床心理或医学诊断；关于联系人内心的内容只能是有证据等级的假设。

## 八、Stage 4：沟通改善系统

### 输出结构

```yaml
situation: 真实触发场景
current_pattern: 有证据的当前做法
possible_impact: 可能影响及替代解释
desired_outcome: 用户希望达到的结果
alternative_behavior: 一项新行为
example_phrasing:
  - 简短直接版
  - 温和承接版
  - 坚定边界版
roleplay: 多轮模拟场景
success_signal: 可观察信号
review_date: 复盘时间
evidence_ids: []
confidence: 0-1
```

### 产品能力

- 按朋友、合作、家人、情感等场景比较沟通方式；
- 提供邀约、拒绝、解释、支持、冲突和关系修复训练；
- 生成多种自然表达，不只给机械话术；
- 每次选择少量行为实验；
- 实际结果写回记忆系统；
- 不以操控、服从或让对方喜欢作为成功指标；
- 不自动发送微信。

### 产物

```text
coaching/communication-patterns.jsonl
coaching/context-differences.json
coaching/behavior-experiments.jsonl
coaching/roleplay-scenarios.jsonl
coaching/example-phrasing.jsonl
coaching/experiment-results.jsonl
```

## 九、Stage 5：数字分身 T0—T2

### Persona 分层

```text
actual_self          历史聊天中真实呈现的自己
confirmed_self       本人明确确认的事实和价值观
aspirational_self    希望成为的自己
situational_selves   在朋友、合作、家庭和创作场景中的差异
contradictions       尚未解决的矛盾和观点变化
shadow_hypotheses    未直接表达需求的 L2 假设
```

### 成熟等级

| 等级 | 能力 |
|---|---|
| T0 | 记忆搜索和人生问答 |
| T1 | 按本人认可的风格写作和拟稿 |
| T2 | 多轮互动、沟通演练和人生故事 |
| T3 | 声音和形象，未来另行决定 |

### 训练与检索资产

- 个人事实问答；
- 人生故事问答；
- 人物与事件关联问答；
- 观点及观点变化问答；
- 本人／非本人表达偏好对；
- 应当回答“不知道”的负样本；
- 人格漂移和事实编造对抗测试。

所有合成数据标记 `synthetic: true` 并关联真实 `memory_id` 和 `evidence_ids`，不得反向写成确认事实。

### 产物

```text
digital-twin/ACTUAL-SELF.md
digital-twin/CONFIRMED-SELF.md
digital-twin/ASPIRATIONAL-SELF.md
digital-twin/SITUATIONAL-SELVES.md
digital-twin/CONTRADICTIONS.md
digital-twin/SHADOW-HYPOTHESES.md
digital-twin/COMMUNICATION-STYLE.md
digital-twin/LIFE-STORY-QA.jsonl
digital-twin/GROUNDED-QA.jsonl
digital-twin/PREFERENCE-PAIRS.jsonl
digital-twin/UNKNOWN-NEGATIVE-EXAMPLES.jsonl
digital-twin/T0-SYSTEM-PROMPT.md
digital-twin/T1-SYSTEM-PROMPT.md
digital-twin/T2-SYSTEM-PROMPT.md
```

## 十、Stage 6：证据审计与质量评估

### 检查

- 证据 ID 是否真实存在；
- 摘要是否编造；
- 人物和事件是否串线；
- 他人观点是否被归到本人；
- 推断是否混入确认事实；
- 关系判断是否忽略反证；
- 数字分身是否冒充真人；
- 数字分身是否承认不知道；
- 被用户否决的判断是否在无新证据时重复出现。

### 指标

```yaml
evidence_link_rate: 1.00
sampled_factual_fidelity: ">=0.95"
schema_validation_rate: 1.00
cross_contact_contamination: 0
unsupported_stable_judgments: 0
rejected_claims_repeated_without_new_evidence: 0
severe_digital_twin_hallucinations: 0
```

### 产物

```text
evaluation/factuality-benchmark.jsonl
evaluation/persona-consistency.jsonl
evaluation/adversarial-cases.jsonl
evaluation/audit-findings.jsonl
evaluation/QUALITY-REPORT.md
```

## 十一、Stage 7：最终本地产品

最终提供一个本地界面：

```text
首页
├─ 全局搜索
├─ 人物关系
├─ 人生时间线
├─ 项目与承诺
├─ 深层分析
├─ 沟通教练
├─ 数字分身
├─ 原始证据
└─ 确认、否决和纠错
```

用户可以：

- 搜索“我和某人什么时候发生过什么”；
- 查看关系变化及支持和反对证据；
- 查看人生阶段、项目和未完成事项；
- 练习真实沟通场景；
- 与私人数字分身对话；
- 点击任何结论回到原始消息；
- 确认、否决、改写、合并或标记过期。

## 十二、Stage 8：增量更新

以后导入新的 WeFlow 数据时：

1. 根据哈希识别新增和变化消息；
2. 只标注新增片段；
3. 更新受影响的实体、事件、联系人记忆和人生时间线；
4. 检查旧判断是否出现新反证；
5. 更新沟通模型和数字分身；
6. 保留每次模型、提示词和记忆版本。

## 十三、到期日并发调度

```yaml
initial_workers: 24
ramp_sequence: [24, 32, 48, 64, 96, 128]
ramp_observation_minutes: 3
utilization_target: 0.90
error_rate_reduce_threshold: 0.05
context_fill_target: 0.75
checkpoint_every_result: true
retry_failed_only: true
cache_by_input_and_prompt_hash: true
stop_new_requests_before_expiry_minutes: 25
final_flush_before_expiry_minutes: 10
min_free_disk_gb: 30
```

调度原则：

- 接口稳定且吞吐继续增加时逐级提高并发；
- 遇到 429 或错误率超过 5% 立即降低；
- 全量标注完成前至少 80% worker 服务标注队列；
- 标注覆盖达到 80% 后，最多20% worker可提前增量构建联系人记忆；
- 每个结果立即落盘；
- 每5分钟更新覆盖率、吞吐、并发、失败、Token估算、剩余时间和磁盘空间；
- 到截止线后停止新调用，保存所有在途、失败和未完成队列。

## 十四、统一目录

```text
WeChat-MiMo-Analyzer/
├─ data/
├─ annotations/
├─ memory/
├─ deep-analysis/
├─ coaching/
├─ digital-twin/
├─ evaluation/
├─ reviews/
├─ runs/
├─ reports/
├─ ui/
├─ config/
├─ schemas/
├─ prompts/
├─ tests/
├─ RUN-SUMMARY.md
└─ README.md
```

## 十五、Claude Code 总执行指令

```text
立即执行微信个人 AI 完整流水线。不要再停留在 DESIGN_ONLY，也不要重新询问路线。路线已经确定：先无上限全量标注理解，再建立个人记忆系统，随后进行最激进分析判断、沟通改善、数字分身和证据审计。

一、权限和边界
- 数据所有者是蔡浩文；
- 允许读取全部 WeFlow 私聊正文；
- 允许保留联系人真实姓名；
- 不脱敏；
- 允许把完整上下文提交给小米 MiMo；
- 不修改、移动或删除原始 WeFlow 导出；
- 不自动发送微信；
- 不把 API Token 写入日志或 Git；
- 不安装全局依赖或修改系统设置，除非先询问。

二、复用现有项目
优先使用：
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer

已知约有725个有效私聊、71,550条消息和6,303个对话片段。先检查现有数据库、索引、脚本、成功结果和失败记录。按输入哈希复用所有合格结果，不从零重建，不重复成功调用。

三、运行模式
设置 RUN_MODE=UNLIMITED_ANNOTATION_FIRST。
取消项目内部 Token 软上限、单联系人预算和“仅高信息量片段”限制。在账号剩余额度、到期时间、接口承载和磁盘空间允许范围内持续运行。

从24个并发worker开始，每3分钟根据吞吐、429、超时和错误率尝试32、48、64、96、128。吞吐不再增加或错误率超过5%时降低一级。每个结果立即原子化落盘，失败项独立重试，成功项不重复。

四、第一优先级：无上限全量标注
覆盖全部联系人、消息和片段，依次执行：
1. 消息级原子标注；
2. 片段上下文标注；
3. 跨片段实体与事件合并；
4. 内容、行动、关系、情绪、需求、身份、风格、记忆和不确定性九维深描；
5. 高信息量及分歧片段独立双标和证据裁判；
6. 全局人物、事件、时间、承诺、观点归属和偏好变化一致性回扫。

每条消息和片段允许多标签。至少标注主题、言语行为、意图、请求、承诺、边界、事件、语气、情绪假设、需求假设、关系信号、沟通行为、风格、记忆候选、歧义、置信度和证据位置。明确表达与模型推断分开。不得用联系人摘要替代细粒度标注。

全量标注完成前至少80% worker用于未覆盖标注。覆盖80%后最多20%worker可增量建立联系人记忆，但不得让最终判断和数字分身抢占标注主队列。

五、第二优先级：个人记忆系统
标注基础覆盖完成后，生成identity、episodic、semantic、relationship、preference、current_state、communication_style和uncertainty八类记忆。每条记忆保存证据、反证、时间、状态、置信度、冲突、过期和版本。

六、第三优先级：最激进分析判断
生成深层自我、核心需求、价值冲突、真实与理想自我差异、关系动力、主动性、互惠、权力、核心张力、修复能力、社交网络、沟通微行为、盲点矛盾、人生转折、关系优先级和条件预测。

每个判断标记L0事实、L1强推断、L2弱假设或L3情景预测。每个L1—L3必须包含支持证据、反证、替代解释、置信度、判断错误代价、验证问题和低后悔行动。使用检察官、辩护人、关系研究者、未来预测者和证据法官五角色分析重要结论。不做临床或医学诊断，不把对方推断心理写成事实。

七、第四优先级：沟通改善
按朋友、合作、家人和情感场景生成沟通模式、替代行为、三种表达版本、角色扮演、成功信号和复盘方式。重点分析邀约、拒绝、倾听、解释、边界、冲突、支持和修复。不生成操控、欺骗或PUA策略，不自动发送消息。

八、第五优先级：数字分身
建立actual_self、confirmed_self、aspirational_self、situational_selves、contradictions和shadow_hypotheses。依次生成T0记忆助手、T1表达助手和T2互动分身，以及有证据的问答集、风格语料、偏好对、不知道负样本和对抗测试。所有合成内容标记synthetic=true并链接memory_id和evidence_ids，不能反向写成确认事实。

九、第六优先级：审计
检查所有证据链接、人物串线、时间冲突、观点归属、无证据推断、被否决判断重复、数字分身事实编造和人格漂移。目标是证据回链100%、Schema合格100%、抽检事实忠实度至少95%、联系人串线0、无证据稳定判断0。

十、进度和停止
创建run-manifest.json与expiry-harvest-status.json，每5分钟更新时间、并发、吞吐、Token估算、队列、覆盖率、失败和磁盘空间。到期前25分钟停止派发新请求，到期前10分钟完成写盘、压缩、失败队列、数据字典、恢复说明和RUN-SUMMARY.md。

若时间不足，优先级绝对固定：
全量标注覆盖 ＞ 个人记忆 ＞ 深层判断 ＞ 沟通改善 ＞ 数字分身 ＞ 扩展对抗测试。

现在立即检查现有项目，创建新的运行manifest并启动Stage 0和Stage 1。除非涉及删除原始数据、自动对外发送或系统级安装，否则不要等待再次确认。
```

## 十六、最终验收清单

- [ ] 全部联系人、消息和片段已标注或有明确未完成队列；
- [ ] 每个标签、记忆和判断可回到证据；
- [ ] 个人记忆库支持人物、时间、事件和主题检索；
- [ ] 每个重要关系有时间线、互动模式、反证和趋势；
- [ ] 深层自我模型区分事实、推断、假设和预测；
- [ ] 沟通建议包含真实场景、表达示例和复盘信号；
- [ ] 数字分身区分真实、确认、理想和情境自我；
- [ ] 用户可以确认、否决、修改、合并和标记过期；
- [ ] 增量导入不会全库重跑；
- [ ] 所有资产可导出并更换其他模型继续使用；
- [ ] 原始 WeFlow 数据没有被修改；
- [ ] 没有自动发送任何微信消息；
- [ ] Token、密码和密钥没有写入日志。
