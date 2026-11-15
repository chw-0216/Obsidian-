# DeepSeek Harness：模型、可视化窗口与对话交叉索引交接文档

> 生成时间：2026-09-21（本机状态检查）
> 用途：让下一次接手的人快速理解“模型怎么选、窗口怎么看、对话和文件如何互相定位”，并知道哪些索引可靠、哪些存在漂移。

## 0. 先读这几条

1. 推荐入口：桌面快捷方式 → `Open-DeepSeek-Harness.vbs` → `Open-DeepSeek-Harness.ps1` → `Start-DeepSeek-Harness.ps1`。
2. 当前运行时是归档目录内隔离安装的 `0.1.5-rc.2`；不要把全局 `dsh` 当常规入口。全局 `0.1.2-alpha.3` 只作为回退。
3. Web 窗口只应访问本机 `127.0.0.1:3080`。认证 URL 含 Token，不要复制到聊天、截图或外发文档。
4. 启动后在工作区切换器选择 `C:\Users\wardc\Desktop\DSH工作区`。当前程序缓存仍显示旧的 `C:\Users\wardc\Desktop` 注册信息，这是交叉索引混乱的主要来源。
5. 新文件先放 `05_收件箱`，完成后归档到主题目录并更新 `00_INDEX.md`。

## 1. 当前基线

| 项目 | 当前值 | 说明 |
|---|---|---|
| 程序目录 | `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\deepseek-harness\` | 安装、状态、脚本和维护记录 |
| 当前运行时 | `runtime\node_modules\@deepseek-ai\dsh@0.1.5-rc.2` | 隔离安装，启动器固定调用 |
| 回退运行时 | 用户级全局 `@deepseek-ai/dsh@0.1.2-alpha.3` | 未覆盖、未卸载 |
| 工作区启动路径 | `C:\Users\wardc\Desktop\DSH工作区` | 启动脚本当前写死的 Workspace |
| DSH_HOME | `...\deepseek-harness\state\` | 会话、设置、附件、凭据和索引 |
| Web 地址 | `http://127.0.0.1:3080` | 仅本机监听 |
| 默认权限 | `workspace-write` | 新会话默认工作区写入，越界需要批准 |
| 默认 Agent preset | `cordis` | 设置文件指定 |
| 会话文件 | 115 个、约 111.7 MB | 同一 Session 可能同时有旧版和 V3 压缩文件 |

## 2. 模型选择矩阵

| 场景 | 首选 | 备选 | 推理强度建议 | 注意事项 |
|---|---|---|---|---|
| 日常问答、整理、并行小任务 | `deepseek-official / deepseek-flash` | MiMo V2.5 | `high` | 当前默认，速度和成本平衡 |
| 复杂关系分析、长材料归纳、重要决策 | `deepseek-official / deepseek-v4-pro` | MiMo V2.5 Pro | `high` 或 `max` | 速度较慢，适合最终结论 |
| 图片、截图、视觉材料 | `deepseek-flash` | 支持视觉的第三方模型 | `high` | 确认输入类型为 text + image |
| 编程、API、命令行 | DeepSeek V4 Pro | GLM Coding Plan | `high` | 工具调用优先官方或稳定 Coding Plan |
| 快速连接测试 | 对应提供方的最小模型 | 不建议旗舰模型 | `off` 或 `high` | 测试会话及时归档 |

### 2.1 已配置的提供方

- `deepseek-official`：`deepseek-flash`、`deepseek-v4-pro`；旧 Flash 别名仅为历史会话兼容。
- `xiaomi-token-plan-cn`：`mimo-v2.5-pro`、`mimo-v2.5`。
- `zai-coding-plan`：`glm-5.2`、`glm-5.3-flash`。
- `scnet-deepseek-flash`：国家超算 DeepSeek V4 Flash 路由。
- `nvidia-nim`：DeepSeek、Kimi、MiniMax、GPT-OSS、Nemotron、Step 等模型。
- `freellmapi`：本地聚合路由，取决于本机 `127.0.0.1:3001` 服务。

已从配置移除明文、不可信的 `http://156.238.239.147:3000/v1` 中转。旧中转密钥引用可能仍在凭据文件中，应在服务端废弃或轮换。

### 2.2 模型配置注意事项

- 默认 `deepseek-flash + high` 适合大多数任务；最终定稿或深层推理时再切 `deepseek-v4-pro`。
- 长会话不要频繁切换模型；切换后在回复开头注明“本轮模型”。
- 官方模型配置写入了 100 万上下文和 384K 最大输出；第三方模型以服务商实际返回为准。
- 模型下拉框不能证明 API Key 可用；本次没有逐个实际调用所有提供方。
- 新版仍保留本地 `reasoning_content` 工具调用热修复；任何升级后都要复测。

## 3. 可视化窗口使用手册

### 3.1 正确打开方式

1. 点击桌面 DeepSeek Harness 入口。
2. 等待本地 Web 服务启动。
3. 浏览器进入认证页面后，不要复制带 Token 的地址。
4. 在 Workspace 切换器选择 `C:\Users\wardc\Desktop\DSH工作区`，不要长期在原始 `Desktop` 工作区新建会话。
5. 新建会话后立刻改成结构化标题，例如 `[Weflow][笑一][数据分析][证据整理][2026-09]`。

### 3.2 可视化窗口的高效分区

| 区域 | 用途 | 推荐做法 |
|---|---|---|
| 主对话区 | 当前任务与模型回复 | 一次只保留一个明确目标 |
| Sidebar 文件预览 | Markdown、代码、HTML、PDF、图片和 Office | 预览后再决定是否引用 |
| Sidebar 终端 | PowerShell、文件检查、运行脚本 | 只在正确 Workspace 执行 |
| Browser 面板 | 打开指定 URL、查看网页状态 | 登录信息不要写入普通会话标题 |
| Subagent 会话 | 并行拆分研究或批处理 | 每个子任务要有明确输出文件 |
| Plan/Review 面板 | 查看计划、文件改动和差异 | 交付前逐文件确认 |

### 3.3 一次任务的窗口操作顺序

```text
选 Workspace → 新建/续接主会话 → 明确模型 → 主会话建立任务地图
→ Sidebar 预览材料 → 终端检查文件 → 子会话并行分析
→ 主会话汇总 → 文件改动审阅 → 产物放入 05_收件箱
→ 移动到主题目录 → 更新 00_INDEX.md → 写交接摘要
```

## 4. 对话交叉索引体系

### 4.1 四层索引

| 层级 | 唯一定位 | 当前来源 | 用法 |
|---|---|---|---|
| 工作区层 | Workspace path / title | `state\storages\workspace.json` | 确认会话属于哪个目录 |
| 会话层 | Session ID + 标题 | `state\storages\session_projcache.json` | 在 UI 或磁盘中定位对话 |
| 文件层 | 绝对路径 / 文件名 | `DSH工作区\00_INDEX.md` 与主题目录 | 找输入材料和交付物 |
| 模型层 | provider + model + reasoning | 会话设置、回复上下文、模型配置 | 判断结论由谁生成 |

### 4.2 推荐的会话命名规则

```text
[主题][对象][动作][阶段][日期]
[Weflow][笑一][聊天分析][证据整理][2026-09]
[知行计划][植物染][课程报告][最终交付][2026-09]
[Harness][模型配置][版本升级][验收][2026-09]
```

### 4.3 主会话与证据会话

- 主会话只保留目标、判断、最终路线和交付结论。
- 证据会话一条只负责一个材料包、一个人物或一个技术故障。
- 证据会话结束时写三行：来源文件；provider/model/reasoning；结论是否进入主会话或交付文件。
- 不要把同一人物、项目或 API 测试拆成大量无标题的一次性会话。

## 5. 当前工作区文件地图

| 目录 | 主要内容 | 建议用法 |
|---|---|---|
| `01_人物` | 笑一、火山雪0号、李梓燏、米雪 | 人物主线与聊天证据 |
| `02_项目` | Movers4Climate 等项目资料 | 申报、影像、群聊和工具包 |
| `03_技术` | API、中兴光猫、节点代理、customer-profile | 技术故障和配置交接 |
| `04_会话归档` | DSH、Codex、Claude、OpenCode 会话导出 | 只读归档 |
| `05_收件箱` | 新导入文件和暂未归类产物 | 所有新文件的临时入口 |
| `99_待清理_20260901` | 旧安装包、重复快捷方式和废弃工具 | 删除前人工确认 |

工作区当前顶层目录统计：

| 目录 | 文件数 | 约占用 |
|---|---:|---:|
| `01_人物` | 33 | 4.9 MB |
| `02_项目` | 25 | 4256.1 MB |
| `03_技术` | 28 | 0.9 MB |
| `04_会话归档` | 57424 | 3211.8 MB |
| `05_收件箱` | 3 | 0.1 MB |

关键文件：

- `C:\Users\wardc\Desktop\DSH工作区\00_INDEX.md`：全区总索引，优先阅读。
- `C:\Users\wardc\Desktop\DSH工作区\AGENTS.md`：工作区行为约定。
- `C:\Users\wardc\Desktop\DSH工作区\01_人物\笑一\00_速查卡.md`：人物主线入口。
- `C:\Users\wardc\Desktop\DSH工作区\01_人物\笑一\01_文件索引与清理计划.md`：笑一材料入口。
- `C:\Users\wardc\Desktop\DSH工作区\04_会话归档\DeepSeek会话整理_20260827\`：已导出的 A–H 会话分类。
- `C:\Users\wardc\Desktop\DSH工作区\04_会话归档\DSH溢出会话备份_Temp抢救\`：未完全归档的溢出会话原始数据。

## 6. 最值得优先固定/加标签的会话

| 主题 | 标题 | Session ID | 轮次/步骤 | 建议动作 |
|---|---|---|---:|---|
| 人物主线：画像、行动指南、数据与归档 | 笑一 | `session-0019f76f-ee1d-4d43-b54e-1a93fc9bfe36` | 199/453 | 纳入主题索引；记录模型与最终文件 |
| 最长会话：人物主线，适合做历史上下文基准 | 陈晔 | `session-70ac5f3b-4268-4574-a4c4-b300331dfc0e` | 610/828 | 纳入主题索引；记录模型与最终文件 |
| Weflow 数据分析主线 | 查找Weflow微信数据分析 | `session-89608bf1-a80c-429c-93f4-62ffe8ae3625` | 38/518 | 纳入主题索引；记录模型与最终文件 |
| Weflow 技术修复主线 | weflow锚点漂移修复 | `session-544600eb-7feb-4e1d-bd92-60d56e3ecc36` | 1/11 | 纳入主题索引；记录模型与最终文件 |
| Weflow 技术修复主线 | 修复 weflow 锚点漂移 | `session-894e23bf-303a-478e-8352-90c1adae0fbd` | 7/120 | 纳入主题索引；记录模型与最终文件 |
| 知行计划文件定位 | 查找知行计划文件 | `session-5c5baab3-aa13-47f9-aed7-72d4bcdecdf0` | 16/113 | 纳入主题索引；记录模型与最终文件 |
| 植物染/美育项目研究 | 植物染信息分析建议 | `session-e84090ea-354c-46b9-8506-ecb36b73bbc7` | 15/58 | 纳入主题索引；记录模型与最终文件 |
| MiMo 提供方接入 | 接入小米MIMO token计划模型 | `session-1c1511c4-01b2-4374-9af8-abe3b3bcfbcf` | 2/52 | 纳入主题索引；记录模型与最终文件 |
| 国家超算提供方接入 | 接入国家超算中心API | `session-702d00af-d7a7-4050-a0cf-20386e07ca8f` | 1/13 | 纳入主题索引；记录模型与最终文件 |
| 中转站测试历史（不建议继续使用） | 测试中转站API接入 | `session-38f8b86d-3e13-46b6-9aa4-081ee1eb6e28` | 8/95 | 纳入主题索引；记录模型与最终文件 |
| 中转站测试历史（不建议继续使用） | 中转站测试状态与可用模型总结 | `session-cb5a8f1c-59b0-4ff4-967b-656ea59a4ffc` | 6/23 | 纳入主题索引；记录模型与最终文件 |
| 家庭网络 | 管理CMCC与华为增强器网络 | `session-4b794c32-96f7-4d1c-a3f2-d85a0a80c491` | 3/118 | 纳入主题索引；记录模型与最终文件 |
| 设备与调试 | 手机连接电脑调试 | `session-8953dc4d-c0ad-4b2a-abbc-bfdb32e437cc` | 41/206 | 纳入主题索引；记录模型与最终文件 |
| Harness 工作区设计 | 整理DeepSeek Harness工作区方案 | `session-fffdef06-edc6-4470-83e2-7d4f0926f92b` | 5/51 | 纳入主题索引；记录模型与最终文件 |
| 跨会话/文件整理方案 | 对话文件整理方案咨询 | `session-57df6d73-1040-44b4-83ea-707d44d416eb` | 15/225 | 纳入主题索引；记录模型与最终文件 |

优先级判断：

- `笑一` 和 `陈晔` 是最长、最需要稳定主索引的两条人物主线。
- Weflow 有多个相关会话，应合并成“数据导出—分析—锚点修复—交付”链路。
- API/模型接入测试应与正式使用会话分开，测试完成后归档。
- `知行计划`、`植物染`、`Movers4Climate` 应各自建立项目级主会话。

## 7. 索引状态与异常

- Workspace 注册表：1 个工作区，登记 78 个 Session ID。
- Session 缓存元数据：86 条。
- 已归档 ID：10 条，其中 5 条仍有缓存元数据。
- Desktop 注册表中找不到缓存元数据：20 条。
- 缓存中不在当前 Desktop 注册表的记录：28 条。

### 7.1 注册表中有、缓存中没有的 ID

```text
session-53e59600-6a06-4d0b-89b7-6510130489db\nsession-f6b4407e-83b9-4996-a072-5b152e93ce69\nsession-afd0ee55-7a20-43e1-a0e3-23c154273f5f\nsession-4752a83a-ca7f-4ebc-96a6-0badf317f619\nsession-347a74e0-5864-40ea-9a35-45a8b35feff5\nsession-309b3e8d-af75-4dfb-b6cf-838e6763b4fb\nsession-caedb662-e2fa-4f29-ac4a-ce0fef7f6711\nsession-9e98c1cd-b627-4b43-8518-cad06709ff9a\nsession-b047e18b-4747-45bb-9482-d20e0160e0d1\nsession-641f676f-f3ef-494f-8f7d-ce9ecf20c1fe\nsession-4fc162c1-5836-479f-8f69-d5fe2d1bc1f2\nsession-7d9ea0bc-4a09-4e00-98d0-3d5e653c219f\nsession-25109098-255d-4600-9f5a-d9f2f300f14e\nsession-1626894a-206d-4dab-afa9-a15e0b70e57c\nsession-44631390-0a76-4984-90fa-6cba823ce6dc\nsession-4cc61add-bd74-42c4-a7e9-9ad7f684ed0c\nsession-c626d09c-9624-4dcb-8863-a8ebb7f70ea4\nsession-1b2f3a44-e59a-44b9-b1f0-09dccc9b8318\nsession-2aa9e71b-45c1-4845-897f-75964349c7b7\nsession-06a166a7-46e7-486c-a6a5-8208fa78c4b4
```

这些 ID 很可能是旧会话、已清理会话或缓存迁移未同步记录。不要直接按 ID 删除；先在 Web UI 或磁盘会话目录确认。

### 7.2 缓存中有、当前 Desktop 注册表没有的记录

完整列表见本文最后的“全量 Session 目录”，状态标记为 `缓存未登记`。这批记录大多集中在 2026-08-19 的批量文件分析，以及 2026-08-24/09-01 的短会话。

### 7.3 权限历史

- 新默认设置已经是 `workspace-write`。
- 旧 Session 的缓存中仍能看到 `danger-full-access`、`approval: never`。历史会话可能保留旧权限事件；不要假设全局设置变化后历史会话已经自动变安全。

## 8. 文件、图片与模型的交叉定位方法

### 从文件找到会话

1. 在 `00_INDEX.md` 或主题目录确认文件归属。
2. 用文件名、日期、人物/项目名搜索 Session 标题。
3. 在 UI 打开候选 Session，确认上下文中是否出现该文件路径。
4. 记录 Session ID、provider、model、reasoning 和最终产物路径。

### 从会话找到文件

1. 先看会话标题和 Workspace。
2. 查看 Sidebar 的文件引用、交付文件卡片和回合结束文件改动。
3. 对图片/PDF/Office 文件优先使用 Sidebar 预览，不要重复导入副本。
4. 把最终文件移动到主题目录，避免长期停留在会话临时目录。

### 从模型找到结论

1. 在会话开头写明：`本轮模型：provider/model；推理：high 或 max`。
2. 重要结论用 Pro 或第二提供方复核。
3. 把模型差异写入交付文件：共同事实、模型推断、待核验项。
4. 不把 API 测试回复，27 20:33 | `session-462b05a2-cdb1-45f8-ac3e-64ec389eb10d` | 仅回复“套餐 Flash 已连接”。 | 1 | 1 |
| 已归档 | 2026-08-27 20:43 | `session-cc9f1164-1ad0-4f43-bc05-b0ecf6fa7716` | 仅回复“套餐 Flash 已连接”。 | 2 | 31 |
| Desktop登记 | 2026-27 21:27 | `session-e52943f0-15db-472c-999e-5e08a83ea344` | 模型扩额 | 12 | 83 |
| Desktop登记 | 2026-08-27 21:52 | `session-5e7ef0c1-8aa2-4d94-a4cb-f5fa3ac0a64b` | 帮我解决用edge打开http://pay.cafa | 2 | 29 |
| Desktop登记 | 2026-08-28 00:10 | `session-b5a080a6-4797-4630-ab8d-eb6474c7a77e` | 这是啥户画像系统（customer-prof | 3 | 5 |
| Desktop登记 | 2026-08-28 13:49 | `session-68cd809e-f901-4dde-91b2-b4e55d1331c9` | 本地部署zcode | 1 | 16 |
| Desktop登记 | 2026-08-28 17:06 | `session-5c5baab3-aa13-47f9-aed7-72d4bcdecdf0` | 查找知行计划文件 | 16 | 113 |
| Desktop登记 | 2026-08-29 00:30 | `session-ae244605-aa70-4cef-9fa6-09d1c6365fea` | 李梓橘 | 27 | 153 |
| Desktop登记 | 2026-08-29 11:01 | `session-d1b71597-00b4-45e2-94b5-16ad047c546f` | 恢复丢失的Codex会话 | 2 | 17 |
| Desktop登记 | 2026-08-30 13:09 | `session-d506c42f-204f-4488-b3ba-3abf6c04f44c` | 云南之行行程报备与潜在意图分析 | 1 | 14 |
| Desktop登记 | 2026-08-31 12:11 | `session-38c353e1-2ac5-4851-9732-a9bbfd599913` | 拖延回复米雪进度说明 | 3 | 14 |
| Desktop登记 | 2026-08-31 15:02 | `session-1c04aa1e-06e6-4b0e-8d42-c854620f46f0` | 如何快速截屏 | 5 | 14 |
| Desktop登记 | 2026-08-31 18:03 | `session-38f8b86d-3e13-46b6-9aa4-081ee1eb6e28` | 测试中转站API接入 | 8 | 95 |
| Desktop登记 | 2026-08-31 18:29 | `session-cb5a8f1c-59b0-4ff4-967b-656ea59a4ffc` | 中转站测试状态与可用模型总结 | 6 | 23 |
| Desktop登记 | 2026-09-01 01:10 | `session-c8aa2e21-06e8-475f-9b9a-123e9f1d9742` | 笑一新 | 30 | 110 |
| 缓存未登记 | 2026-09-01 01:14 | `8ed9c4a0-59c1-4fbe-b63e-b4aaa705a28b` | 你是蔡浩文（wardc）的私人分 | 1 | 9 |
| 缓存未登记 | 2026-09-01 01:14 | `b739f8fe-0397-4ebb-95fe-3807914d1c3d` | 你是蔡浩文（wardc）的私人分 | 1 | 2 |
| Desktop登记 | 2026-09-01 02:56 | `session-fffdef06-edc6-4470-83e2-7d4f0926f92b` | 整理DeepSeek Harness工作区方案 | 5 | 51 |
| Desktop登记 | 2026-09-01 02:58 | `session-57df6d73-1040-44b4-83ea-707d44d416eb` | 对话文件整理方案咨询 | 15 | 225 |
| Desktop登记 | 2026-09-01 11:30 | `session-cc98c129-565d-48b3-b3b9-20a870aebcab` | 新会话开始时读 07_聊天记录分 | 1 | 8 |
| Desktop登记 | 2026-09-01 16:06 | `session-c699f4db-05c8-4144-b3b3-77d349851ec9` |  | 0 | 0 |

## 13. 交接结束时必须留下的摘要模板

```markdown
## 本次交接
- 主任务：
- 主 Session：
- 相关 Session：
- 使用模型：provider / model / reasoning
- 已确认事实：
- 仍需核验：
- 输入文件：
- 输出文件：
- 下一步：
- 是否需要归档：是 / 否
```

> 安全提醒：本文不包含任何 API Key、认证 Token 或凭据值。认证 URL、`.credentials.yaml`、`web.log` 不应复制到聊天、截图或公共同步目录。

