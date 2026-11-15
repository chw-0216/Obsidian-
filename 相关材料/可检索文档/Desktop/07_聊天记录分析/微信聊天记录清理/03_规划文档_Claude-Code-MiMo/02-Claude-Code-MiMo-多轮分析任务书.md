# Claude Code＋小米 MiMo：微信多轮分析与数字分身任务书

> 已选路线：个人记忆系统、沟通改善、数字分身三方向融合。个人记忆系统是唯一数据底座，沟通教练和数字分身都是它的上层应用，不各自维护互相冲突的联系人画像或 Persona。

## 0. 当前状态与总开关

```yaml
RUN_MODE: design_only
ALLOW_READ_CHAT_BODY: false
ALLOW_REMOTE_MODEL_CALLS: false
ALLOW_CONTACT_NAMES_IN_MODEL: false
DATA_SCOPE_ON_EXECUTION: all_private_chats
REDACTION_ON_EXECUTION: none
ALLOW_REMOTE_MODEL_CALLS_ON_EXECUTION: true
ALLOW_CONTACT_NAMES_IN_MODEL_ON_EXECUTION: true
PRIVACY_AS_ANALYSIS_CONSTRAINT: false
ALLOW_EXTERNAL_MESSAGES: false
ALLOW_AUTOMATIC_REPLIES: false
ALLOW_VOICE_CLONE: false
ALLOW_PUBLIC_DIGITAL_TWIN: false
```

前四个 `false` 只表示当前交付仍处于方案判断阶段，并不代表未来需要脱敏。用户选定路线并把 `RUN_MODE` 改为执行模式后，允许读取全部私聊正文、把完整上下文和联系人姓名提交给 MiMo，不因隐私而抽样或裁剪。发送消息、自动回复、声音克隆和公开数字分身仍是独立功能开关。

## 1. 可直接交给 Claude Code 的总任务

```text
你正在为数据所有者蔡浩文设计一个本地优先的微信聊天多轮分析系统。

产品路线已经确定：
1. 建立可检索、可更新、可回到原始证据的个人记忆系统；
2. 基于同一记忆系统分析蔡浩文的沟通模式，生成可验证的沟通练习；
3. 基于同一记忆系统建立明确标识为 AI 的数字分身。

三者必须共享统一的 observation、episode、memory_item、relationship、pattern、coaching_experiment 和 persona_rule 数据契约。沟通教练及数字分身不得另建无法追溯的“黑箱画像”。

当前模式是 DESIGN_ONLY。只生成框架文件，不运行数据分析，不读取聊天正文，不调用远程模型，不安装依赖，不外发数据。

系统未来会通过 Claude Code 调用小米 MiMo Token Plan。用户已确认这些是自己的聊天记录，执行阶段可分析全部私聊正文、保留联系人姓名、不做脱敏。运行仍使用明确的模式门，目的是控制任务范围、质量和成本，而不是隐私限制：
1. pilot：用少量样本校准标签和提示词；
2. standard：覆盖全部私聊，采用分段、分层摘要和证据回链控制上下文；
3. deep：只围绕用户指定的人物、时间或问题；
4. digital_twin：可读取完整分析库，但对事实、观点和人格设定区分“用户确认”与“模型推断”。

核心原则：
- 原始数据只读，任何清洗都生成新层；
- 观察、推断和用户确认必须分开；
- 每个结论保留时间、片段 ID、证据消息 ID、置信度和其他解释；
- 不做心理或医学诊断，不推断政治、宗教、性取向、健康等敏感身份；
- 不对联系人做“价值评分”，不生成操控、PUA、欺骗或逼迫策略；
- 沟通优化目标是清晰、尊重、倾听、边界、互惠和真实表达；
- 数字分身必须公开表明自己是 AI，不得冒充本人，不得自动联系任何人；
- Token 不得写入日志或 Git；联系人姓名和完整原文可以进入 MiMo 分析及本地证据库，报告中是否展示由报告用途决定。

请只完成下述目录、Schema、提示词和评估设计，并在最后生成 DESIGN-REVIEW.md。路线本身已经选定，不要再次要求用户在记忆系统、沟通改善和数字分身之间三选一。不要执行任何分析脚本。
```

## 2. 建议目录

```text
wechat-personal-ai/
├─ README.md
├─ CLAUDE.md
├─ config/
│  ├─ permissions.yaml
│  ├─ budgets.yaml
│  └─ label-taxonomy.yaml
├─ schemas/
│  ├─ round-1-observation.schema.json
│  ├─ round-2-relationship.schema.json
│  ├─ round-3-self-pattern.schema.json
│  ├─ round-4-coaching.schema.json
│  └─ round-5-digital-twin.schema.json
├─ prompts/
│  ├─ round-1-observation.md
│  ├─ round-2-relationship.md
│  ├─ round-3-self-pattern.md
│  ├─ round-4-roleplay.md
│  └─ round-5-persona.md
├─ src/
│  ├─ inventory.py
│  ├─ normalize.py
│  ├─ select_samples.py
│  ├─ run_round.py
│  ├─ verify_evidence.py
│  └─ export_review.py
├─ reviews/
│  ├─ user-confirmed-facts.jsonl
│  ├─ rejected-inferences.jsonl
│  └─ corrections.jsonl
├─ digital-twin/
│  ├─ PRIVATE-MEMORY.md
│  ├─ PUBLIC-PERSONA.md
│  ├─ COMMUNICATION-STYLE.md
│  ├─ UNCERTAINTY-RULES.md
│  └─ SYSTEM-PROMPT.md
└─ DESIGN-REVIEW.md
```

设计阶段可以创建空目录和模板，但不得生成真实联系人、真实摘要或真实 Persona。

## 3. 六轮分析框架

### Round 0：数据契约和质量盘点

目标：只回答“有什么数据、缺什么数据、能否追溯”，不理解内容。

输出：

- 文件和消息数量；
- 时间覆盖；
- 私聊、群聊、公众号分类；
- 文本、图片、语音、文件等消息类型；
- 空目录、重复消息、异常时间、缺失媒体；
- 数据源哈希和导入版本。

审批门：用户确认范围后，才能进入 Round 1。

### Round 1：可观察事实与对话片段

分析单位：一次连续对话，而不是孤立消息。

输出字段：

- `segment_id`；
- 时间范围；
- 主题；
- 明确表达的目标和请求；
- 关键事件；
- 承诺、待办和截止信息；
- 可观察语气；
- 证据消息 ID；
- 置信度；
- 无法判断项。

禁止输出：人格标签、关系定性、心理诊断和敏感身份推断。

### Round 2：单段关系的长期互动模型

输入：同一联系人的全部 Round 1 结果、本地统计和按需检索的原文片段；必要时可以对关键时间段重新读取完整原文。

输出字段：

- 互动时间线；
- 常见主题和场景；
- 双方主动发起和回应情况；
- 明确表达的偏好与边界；
- 冲突、回避和修复事件；
- 未完成事项；
- 关系变化的多种可能解释；
- 支持和反对每个解释的证据片段 ID；
- 用户确认状态。

联系人真实姓名可以发送给 MiMo，以保持跨对话、备注名和关系事件的一致性；同时保留稳定联系人 ID，避免改名造成断链。

### Round 3：跨关系的自我沟通模式

输入：全部关系模型；需要核对模式时，可以回读具体联系人的原文和证据片段。

输出分为三列：

1. **稳定观察**：多个场景重复出现且有证据；
2. **情境行为**：只在工作、亲密关系、陌生人或冲突场景出现；
3. **待验证假设**：证据不足，必须由用户确认。

建议观察维度：

- 主动发起与跟进；
- 问题是否明确；
- 是否倾听并回应对方表达；
- 解释长度和信息密度；
- 表达需求和拒绝的方式；
- 面对冲突、冷淡和不确定性的反应；
- 表达感谢、认可和情绪支持的方式；
- 线上交流与现实行动是否一致。

### Round 4：沟通教练与行为实验

每条建议必须使用以下结构：

```yaml
situation: 触发场景
current_pattern: 当前可观察做法
desired_outcome: 用户希望改善的结果
new_behavior: 一项可执行替代行为
example_phrasing: 两到三种真实自然的表达
practice_roleplay: 一个模拟场景
success_signal: 如何判断是否改善
review_date: 复盘日期
evidence_ids: 证据片段
confidence: 0-1
```

规则：

- 每月最多推荐三项实验；
- 不以“让别人服从、喜欢或回复”为成功指标；
- 成功指标应是表达更清晰、尊重边界、减少误解或更符合本人价值；
- 模拟结果不得自动写入真实聊天窗口。

### Round 5：数字分身记忆与 Persona

数字分身使用分层记忆：

| 记忆块 | 内容 | 是否可公开 | 更新方式 |
|---|---|---:|---|
| identity | 本人确认的稳定事实 | 部分 | 只能人工确认 |
| values | 本人确认的价值观和原则 | 部分 | 人工确认＋版本记录 |
| preferences | 喜好、习惯、表达偏好 | 部分 | 可撤销、可过期 |
| communication_style | 本人认可的高质量表达模式 | 是 | 从精选样本提炼 |
| episodic_memory | 带时间和证据的个人事件 | 否 | 自动建议、人工确认 |
| relationship_context | 联系人和关系上下文 | 按用途决定 | 按联系人组织、保留证据 |
| current_projects | 当前目标和项目状态 | 否 | 定期更新 |
| uncertainty | 冲突、未知和待确认信息 | 否 | 持续维护 |
| public_persona | 允许数字分身使用的公开资料 | 是 | 每次发布前审核 |

数字分身系统提示词必须包含：

```text
我是蔡浩文授权的 AI 数字分身，不是蔡浩文本人。
我可以使用完整分析库辅助理解，但必须区分本人确认的事实、聊天中的直接表达和模型推断。
我不会代替本人作出承诺、表达感情、处理金钱、法律、医疗或亲密关系决定。
当证据不足、记忆冲突或问题要求我代表他人表态时，我会说明不确定，并建议联系本人确认。
```

### Round 6：审计、对抗测试和用户校正

检查项目：

- 引用的证据 ID 是否真实存在；
- 结论是否超出证据；
- 同一事实是否存在冲突版本；
- 是否把推测写进确认记忆；
- 是否把无关联系人的内容错误带入当前回答；
- 数字分身是否承认自己是 AI；
- 用户能否删除、修改和导出所有记忆；
- 更换模型后是否仍能使用同一记忆库。

## 4. 标签体系

第一版只保留可复核标签：

- `topic`：工作、学习、家庭、朋友、情感、消费、出行、摄影、创作等；
- `intent`：询问、请求、分享、邀约、确认、拒绝、安慰、道歉、感谢、协商；
- `event`：会面、决定、冲突、承诺、完成、取消、转折；
- `tone_observed`：轻松、正式、支持、焦虑、低落、生气、疏离、不确定；
- `interaction`：主动发起、追问、及时回应、延迟回应、明确边界、关系修复；
- `action_item`：责任方、事项、状态、截止信息；
- `evidence`：消息 ID、片段 ID、时间和来源。

禁止标签：人格好坏、情感价值、社会价值、操控难度、服从度、精神疾病和敏感身份。

## 5. 运行模式与审批门

| 模式 | 数据范围 | MiMo 调用 | 产物 | 必须审批 |
|---|---|---:|---|---:|
| design_only | 无正文 | 否 | 模板、Schema、测试 | 当前默认 |
| pilot | 用户指定的少量片段 | 是 | 标签质量样本 | 是 |
| standard | 全部私聊，分层处理 | 是 | 联系人和自我模式草稿 | 是 |
| deep | 指定人物／时间／问题 | 是 | 专题报告 | 是 |
| digital_twin | 仅用户确认记忆 | 是 | 私人或公开 Persona | 是 |

审批文件使用：

```yaml
approved_by: 蔡浩文
approved_at: null
run_mode: design_only
data_scope: [all_private_chats]
remote_model: mimo-v2.5-pro
max_batches: 0
max_total_usage: 0
include_contact_names: true
allow_external_messages: false
```

在本任务书仍为 `design_only` 时不得读取正文；用户选定路线并切换运行模式后，按 `all_private_chats` 执行。

## 6. 质量指标

- **证据准确率**：引用 ID 能回到正确原文的比例；目标 100%。
- **事实忠实度**：摘要和事件无编造；人工抽检目标 ≥95%。
- **用户同意度**：用户认可的模式或记忆比例。
- **推断隔离率**：未经确认的推断进入稳定记忆的数量；目标 0。
- **上下文串线数**：把无关联系人或无关事件写进当前结论；目标 0。
- **建议可执行率**：建议能否在一周内尝试并观察结果。
- **人格漂移**：数字分身跨多轮是否改变原则或冒充本人；目标 0 次严重漂移。

## 7. Claude Code 在设计阶段应交付的文件

1. 五份 JSON Schema；
2. 五份 MiMo 提示词模板；
3. 权限和预算配置模板；
4. 证据链验证测试；
5. 用户确认、否决和纠正的数据格式；
6. 数字分身私有／公开记忆隔离规则；
7. `DESIGN-REVIEW.md`，列出所有待用户选择项；
8. 不包含真实聊天结果的合成数据测试。

完成后停止，不运行 pilot。
