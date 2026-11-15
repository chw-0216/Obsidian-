# customer-profile-demo 重建实施计划（规划稿 · 不含代码）

> 本文件依据《客户画像系统重建教学文档》产出，目标是给执行者（Codex / 其它编程 Agent / 你自己）一份**可直接照做的分阶段实施路线图**，并提前暴露文档中会导致返工的疑点与缺口。
> 当前状态：**规划阶段**。环境由你自己准备与运行（`pnpm install → 建库建表 → 构建 → 启动`）。

---

## 0. 结论摘要

- 项目形态：pnpm workspace monorepo（`@cpd/common` + `@cpd/server`(NestJS 11) + `@cpd/web`(Vue3+Vite)），MySQL(Prisma 7) + Redis(BullMQ/缓存) + SSE，双分析引擎（规则离线 / LLM 自动切换回退）。
- 规模预估：约 70+ 个后端源文件、30+ 个前端组件文件、1 个共享类型文件（约 500 行契约）。
- **强烈建议的落地顺序**：先"核心链路"（客户/事件/画像/双引擎/前端核心），再"扩展模块"（微信导入、主动触达与接管、知识库、商城）。
- **必须提前认清的边界**：微信 WCDB 解密工具链、RPA 发送器、商城库、旧 SQLite 迁移源 **都不可由本文档凭空生成**，它们属于"宿主环境契约"。重建代码必须以"可降级 / 可 mock"的方式实现这些接口，否则在无对应环境的机器上会直接失败。

---

## 1. 前置条件与环境缺口

### 1.1 运行环境

| 项 | 要求 | 备注 |
| --- | --- | --- |
| Node.js | **≥ 22.12**（建议 22 LTS 最新） | 文档写 22.5，但 Prisma 7 与 Vite 8 均要求 ≥22.12，**按 22.12+ 准备** |
| pnpm | ≥ 9 | workspace + 各包 filter 脚本 |
| MySQL | 8.x，库 `customer_profile`，utf8mb4 | 建表用 `prisma db push` |
| Redis | 6+（可缺失） | 缺失时队列不可用、缓存降级直查，规则引擎仍可用 |
| DeepSeek Key | 可选 | 不填则以"规则引擎 (离线)"模式运行 |

### 1.2 外部工具契约（不可生成，只能对接/降级）

| 外部依赖 | 文档对应 | 建议实现策略 |
| --- | --- | --- |
| WCDB 解密工具链 | `WCDB_ELECTRON` / `WCDB_SCRIPTS` / `WCDB_RUNTIME`，`wcdb_server.js`、`get_key_v2.js`、`accounts.json` | 视为**黑盒 HTTP 服务**：后端只写客户端代理（/ping、/sessions、/messages、/count、/contacts、/displaynames、/sns、/sns-stats）；密钥捕获向导把 `get_key_v2.js` 当黑盒脚本调用，状态机照文档实现。工具缺失时微信模块整体"未配置/不可用"提示 |
| RPA 发送器 | `SENDER_BASE=http://127.0.0.1:8790` + `SENDER_MOCK=1` | 写 HTTP 客户端（/health、/send）；`SENDER_MOCK=1` 时本地模拟发送成功，保证 Demo 可全流程演示 |
| 商城库 | `SHOP_DB_HOST/PORT/USER/PASSWORD/NAME` | mysql2 只读连接池；**表结构文档未给出**，仅列出用到的字段（mt_wx_user、ords、mt_user_profile、pro_info、pro_sku、mt_ai_knowledge、mt_ai_sensitive_word）→ 需在现场按字段名适配，未配置时整模块降级"不可用" |
| 旧 SQLite 迁移源 | `data/profile.db`（§5.5 启动恢复） | 需引入 `better-sqlite3`（文档未列依赖）；文件不存在时跳过 |

### 1.3 版本/命名偏差提醒（生成前先确认，避免返工）

1. **Node 版本**：文档写 ≥22.5，实际按 ≥22.12 执行（Prisma 7、Vite 8 的硬要求）。
2. **LLM 模型名**：文档样例 `deepseek-v4-flash` 是假设值，实际模型名以所配 API 的可用列表为准（做成可配置，不改代码）。
3. **Prisma 7 的形态**：driver adapter（`@prisma/adapter-mariadb`）+ `prisma.config.ts` 是 Prisma 7 的标准做法，与文档一致；但注意 Prisma 7 下 `prisma generate` 需要显式 `output` 目录、CLI 通过 `prisma.config.ts` 读取环境（详见 §3）。

---

## 2. 架构与数据流

### 2.1 模块依赖

```
@cpd/common (数据契约，唯一类型来源)
   │  前后端都从这里 import，禁止各写一套
   ▼
apps/server (NestJS)
 ├─ AccountsModule ◄─ 全局 AccountContextMiddleware (AsyncLocalStorage, X-Account-Id)
 ├─ AnalyzerModule  ─ 规则引擎 / LLM(OpenAI 兼容, 失败回退)
 ├─ ProfileModule   ─ mergeAnalysis 共享算法（事件/会话/朋友圈/增量复用）
 ├─ CustomersModule ─ 内存 store + MySQL 持久化 + Redis 缓存 + BullMQ 队列 + SSE
 │     └─ 依赖: PrismaModule, RedisModule, Analyzer, Profile
 ├─ WechatModule    ─ WCDB 代理 / 导入 / 朋友圈（依赖 Accounts 当前实例 + Customers）
 ├─ OutboundModule  ─ 草稿/审批/30s发送/20s回听/全自动接管（依赖 Customers, Wechat, Analyzer, Kb, Shop）
 ├─ KbModule        ─ TF-IDF/向量检索 + 导入 + 聊天沉淀（依赖 Analyzer）
 ├─ ShopModule      ─ 商城直连 + 绑定/同步/意图分类（依赖 Customers, Profile, Outbound 注入）
 └─ SeedModule      ─ 首次启动写 5 个种子客户（纯规则引擎，零 LLM）

apps/web (Vue3)
 ├─ api.ts（统一 X-Account-Id 头 + 全部 API 函数，类型来自 common）
 ├─ App.vue（布局 + SSE + 账号切换 + toast）
 └─ 组件: CustomerList / CustomerDetail / WechatImport / MomentsView /
          AccountManage / OutboundView(6 Tab) / Reports / Sparkline
```

### 2.2 核心数据流

1. **事件流**：`addEvent` → 内存 push（前端立即可见"待分析"）→ BullMQ `analysis` 队列 → `processAnalysis` → `mergeAnalysis` 更新画像 → 全量落库 → 失效 Redis 缓存 → SSE 推 `profile.updated` → HTTP 202 先行返回。
2. **会话流**：微信导入 / `addConversation` → `conversation-analysis` 队列（全量）→ 60s 合并窗口 debounce 的增量分析 → 事实去重合并 → 画像更新 → SSE。
3. **接管流**：20s 回听新客户消息 → 入库 + 停推计划任务 + 生成建议 + 落 `reply_events` + SSE；接管客户 → BullMQ `auto-reply` 延迟任务（8~40s）→ 到点复核 + 硬闸门 → 智能回复 → RPA 发送 → `chat_messages.source='ai'` 写回。
4. **朋友圈流**：`moments-analysis` 队列 → 关联/新建客户 → 画像合并 → SSE `moments.analyzed`。

---

## 3. 文档待定 / 冲突点（实现前必须先定，否则返工）

| # | 疑点 | 建议决策 |
| --- | --- | --- |
| D1 | **SSE 无法携带 `X-Account-Id` 头**（浏览器 `EventSource` 不支持自定义头），而文档要求"前端每个请求都带该头" | 方案 A（推荐）：SSE 地址带 `?account=<id>` 查询参数，服务端解析后决定推送范围；切换账号时重建 EventSource。方案 B：单条全局 SSE，服务端按事件里的 `accountId` 过滤后仅推给匹配会话（不可靠）。选 **A** |
| D2 | **Prisma 7 生成细节**：`prisma generate` 需显式 `output`；CLI 环境变量读取方式变化 | Phase 1 时先做最小验证（`db push` + `generate` 成功）再继续，把 `prisma.config.ts` 写对（读根 `.env` 的 `DATABASE_URL`），generator 设 `output = "../src/generated/prisma"`，运行时用 `PrismaMariaDb` adapter |
| D3 | **时间字段存字符串**（`YYYY-MM-DD HH:mm[:ss]`） | 完全照文档：Prisma schema 时间列用 `String`，服务层统一 `nowStr()` 工具生成/解析，避免时区坑；**不要**中途改成 `DateTime`，否则类型契约与排序逻辑要全改 |
| D4 | **JSON 字段存 TEXT** | 每张表的 `*_json` 列用 Text，服务层封装 `jsonGet/jsonSet` 序列化；禁止直接把 DB 行当对象用 |
| D5 | **旧 SQLite 迁移** 依赖未列出 | 增加 `better-sqlite3`（仅迁移用，只读）；迁移逻辑幂等：MySQL 非空即跳过 |
| D6 | **WCDB / RPA / 商城** 为黑盒 | 全部按 §1.2 契约实现客户端 + 降级；**接口路径、报文结构以本文档 §5.7/§5.8/§5.10 为准**，现场适配 |
| D7 | **风险词表**（私密/承诺夸大/营销黑词）只枚举了部分 | 文档列出的词先照抄实现为常量表；保留"可扩展"注释，运行期不落库（够用），不要把枚举当成文档缺口阻塞 |
| D8 | **商城表结构未给出** | 查询语句按文档字段名先写；提供 `SHOP_DB_*` 未配置时优雅降级；现场若字段名不符，只改 SQL 映射层，不动契约类型 |
| D9 | **SSE 与账号隔离**（见 D1）还影响"未登录即收到所有账号事件" | SSE 服务端按 `?account=` 过滤；事件结构已带 `accountId`，前端只处理匹配账号的 toast/刷新 |
| D10 | **`pnpm start` 用 `node apps/server/dist/main.js` 托管 web 静态** | 保持；注意生产模式下 `/api/*` 放行 + 其余回退 `index.html`（SPA），必须写成"先匹配 /api 再 fallback"的顺序，否则前端路由 404 |
| D11 | **`accounts` 表 `id` 是自增 PK 还是自定义？** 文档 accounts 表 `id`(PK) 未说明类型 | 建议 `id` 用字符串/自增均可，但注册表 JSON 里用 `id` 作为主键引用；**决定：`id` 用 String 类型 UUID（与 outbox/reply/shop 的 `account_id` 外键一致，避免隐式转换）** |
| D12 | **`Profile` 的 `history` 单独存表**，`profile_json` 不存 history | `CustomerDetail` 组装时 `profile_json`（去 history） + `profile_history` 表拼接成完整 `DetailProfile`；`mergeAnalysis` 每次 push 一条 history 并同步重写 `profile_json` |
| D13 | **`conversations` 与 `chat_messages` 全量重建**（persistCustomer 事务） | 照文档：customer 变更时"upsert → 重建 events/history/conversations/messages"。数据量大时慢，但 MVP 可接受；保留注释说明 |
| D14 | **DeepSeek 模型名**（见 §1.3） | 做成可配置，样例值可替换；`testLLM` 在启动/页面可点，用于现场确认 |
| D15 | **多个"LLM 预算"概念**（会话每日 3 次、接管每日 10 次、自动回复每日 2 条） | 分别落在不同计数器，别混用；会话预算存内存/Redis 按日滚动，接管预算从 `customer_send_state` / 日计数读 |

---

## 4. 分阶段实施计划

> 每阶段末尾有"✅ 阶段验收"，全部满足才进入下一阶段。**外部工具缺失不影响阶段完成**，相关模块以"可降级实现 + 文档说明"交付。

### Phase 0 — 脚手架与共享契约
**目标**：monorepo 骨架可跑通 `pnpm install` + `@cpd/common` 构建；前后端都能 import 共享类型。
- [ ] 根 `package.json`（scripts: build/start/dev:server/dev:web）、`pnpm-workspace.yaml`、`tsconfig.base.json`（ES2022 + commonjs + strict）
- [ ] `.npmrc`（只允许 @prisma 相关包跑构建脚本）、`.env` / `.env.example`、`.gitignore`、`run.cmd`
- [ ] `packages/common`：`src/types.ts` **完整实现第 4 节全部 30+ 接口**（一个文件，字段名/类型一字不差），`src/index.ts` 全量导出；`package.json` 配 `main`/`types` 指向 dist
- [ ] 首次构建 `@cpd/common` 成功
- ✅ 验收：`pnpm --filter @cpd/common build` 产出 `dist/index.d.ts`；类型文件与 §4 逐条对照无遗漏

### Phase 1 — 服务端基座（可运行空壳）
**目标**：`nest build` 通过；`prisma db push` 能建全表；`node main.js` 能起服务、托管静态、SPA 回退。
- [ ] `main.ts`：`loadEnv()`（零依赖手写解析根 `.env`，已有系统变量优先）→ `NestFactory.create(AppModule)` → `enableCors()` → 静态托管 `apps/web/dist`（/api 放行 + 回退 index.html）→ `listen(PORT || argv[2] || 3000)` → 打印引擎模式/模型/脱敏 key
- [ ] `app.module.ts`：注册全部模块 + 全局 `AccountContextMiddleware`
- [ ] `PrismaModule`：`prisma.config.ts`（读 `DATABASE_URL`）、**完整 Prisma schema（§5.2 全部 17 张表，含索引/唯一/默认值/外键，时间用 String，JSON 用 Text）**、driver adapter（`PrismaMariaDb`）、`db push` 验证
- [ ] `RedisModule`：ioredis + 连接失败降级标志；提供 `cacheGet/cacheSet/del(key 前缀)`，Redis 不可用时自动直查
- [ ] `AccountContextMiddleware`：AsyncLocalStorage + `X-Account-Id` 解析（仅限已注册账号，否则回退注册表 current）+ `currentIdValue()`
- [ ] SSE 基础：rxjs Subject + `GET /api/events`（支持 `?account=` 过滤，见 D1/D9）
- ✅ 验收：`nest build` 无类型错误；`prisma db push` 建出 17 张表；启动后访问 `http://127.0.0.1:3000/api/...` 有响应；无 Redis 也能启动

### Phase 2 — 分析引擎（纯函数，先于画像）
**目标**：规则引擎离线全功能 + LLM 客户端 + 全部 7 类分析函数可单测。
- [ ] **规则引擎**：标签规则表（14 条，正则 OR + 基础权重）→ 加权规则（加强词每次 +25%，≤3 次，封顶 1.0）→ 意图规则表（顺序命中，置信 0.8/默认 0.4）→ 情感计算（正负词表，`clamp((pos-neg)/max(1,pos+neg))`，两位小数）→ 主题（五类）→ 关键词
- [ ] **LLM 客户端**：OpenAI 兼容 `/chat/completions`，`temperature 0.2~0.7`、`response_format json_object`、超时 30~60s、剥离 ```json 后 `JSON.parse`、数值钳制；`llmJson(prompt, maxTokens)`（先 `thinking:{type:'disabled'}`，失败重试不带）；`testLLM`（128 max_tokens 验证 key/延迟/usage）；`maskedKey`（4+***+4）
- [ ] **事件级** `analyzeEvent`（约束 2~5 标签、情感 -1/0/1、记录 usage、`source='LLM'`、`engine='LLM(<model>)'`）
- [ ] **会话级** `analyzeConversation`（≤100 条、每条 `序号. [客户/客服] 内容`、内容截断 200 字；facts field 枚举 12 类、必带 confidence/evidence、≤12 条；规则兜底版本含固定事实抽取与置信度）
- [ ] **增量** `analyzeConversationDelta`（输入画像摘要+旧上下文+新段；tags 带 `action: confirm|new|revise` + reason；规则兜底 action 全 `new`）
- [ ] **触达生成** `generateOutboundMessage`（**隐私红线：仅 price_sensitivity/brand_pref/consumption/decision_style/communication_pref 五字段可用**；60~90 字口语化；`computeRiskFlags` 实现超长/链接/私密词/承诺夸大/营销黑词/过短；`message_hash` SHA1 前 16 位 + 近 30 条去重标记；规则兜底模板）
- [ ] **回复建议** `generateReplySuggestion`（30~60 字，先承接情绪；规则兜底：问句/非问句固定文案）
- [ ] **智能回复** `generateIntelligentReply`（20~80 字；优先级：商城事实→知识库→兜底 should_auto=false；投诉/退款/赔偿/法律/情绪激动/要求人工→安抚转人工；连续自动回复 ≥2 轮倾向 false；规则兜底一律保守转人工 confidence 0.3）
- [ ] `checkTextSafety`（复用 computeRiskFlags）+ 引擎信息聚合
- ✅ 验收：无 Key 时规则引擎对 §7 种子事件产出合理标签/意图/情感/主题；配 Key 后 `testLLM` 通过，LLM 失败能自动回退且 `engine` 标注

### Phase 3 — 画像模型（纯函数）
**目标**：`mergeAnalysis` 及全部辅助方法实现，可与 Phase 4 联调。
- [ ] `newProfile()`（空画像结构完整）
- [ ] `mergeAnalysis`：版本+1、命中加权（`min(1, old*0.6+weight*0.5)`/新建 score=weight）、`revise` 软着陆、未命中 `*0.92`、情感滚动均值+序列、意图取最新、流失风险三标签取最高分（≥0.5 高/≥0.3 中/否则低）、delta 计算（new/up/down/same）、history push（reason 截断 60 字）
- [ ] 辅助：`applyEvent`、`applyConversation`（事实按 field+value 去重取最大 confidence 补 evidence）、`applyConversationDelta`（返回新增标签名列表）、`applyMoments`
- ✅ 验收：针对同一事件序列重复调用，标签分数单调符合加权+衰减公式、版本号递增、delta 正确

### Phase 4 — 客户域与异步（核心链路闭合）
**目标**：前端可见"提交事件→待分析→画像 +1→SSE 刷新"全链路；重启数据不丢。
- [ ] 内存 `store`/`conversations` + `persistCustomer` 事务（upsert→重建 events/history/conversations/messages）
- [ ] `onModuleInit` 启动恢复：等待账号注册表 → `migrateLegacyData`（可选）→ 从 MySQL 加载 → 修复（账号归属回填/名称清洗/未分析会话重排队/按 wxid 合并重复客户/合并重复会话/按 WCDB 备注同步名/自动回复状态镜像）→ 无数据则种子建库
- [ ] `SeedModule`：5 个种子客户（§7 事件逐条跑规则引擎）
- [ ] `addEvent`：内存先入 → BullMQ `analysis` 队列（attempts 2、退避 2000ms、removeOnComplete 100~200）→ `processAnalysis` → 落库 → 失效缓存 → SSE `profile.updated`（含 version/engine/totalTokens/newTags）
- [ ] 缓存：列表 `profile:customers:<accountId>` TTL 30s、详情 `profile:customer:<id>` TTL 60s，变更失效；Redis 挂自动直查
- [ ] 会话：`addConversation`（消息非空校验→入队 `conversation-analysis`）、`reanalyze`、增量（60s debounce + 每客户每日 LLM 预算 3 次，超预算仅规则）
- [ ] 其它：`reset()`/`resetAccount()`/`accountStats()`/`exportData()`/`removeCustomer()`（级联）、`enrichCustomerFromShop`（留接口，Phase 8 填）
- [ ] API：/api/customers CRUD、/api/customers/:id/events、conversations、/api/events、/api/reset、/api/engine、/api/test-llm、/api/export
- ✅ 验收：提交事件 202 返回→数秒内画像版本 +1、SSE toast、不刷新自动更新；重启数据不丢、不重复调 LLM；无 Redis 全流程仍可演示

### Phase 5 — 账号体系 + 微信接入
**目标**：多账号隔离 + 微信会话/朋友圈导入全流程（WCDB 工具存在时真实可用，缺失时明确提示）。
- [ ] **账号注册表**：本地 JSON（默认 `D:\ai\tools\wechat-data\accounts.json`，`ACCOUNTS_FILE` 可覆盖）结构 `{current, accounts[], ignored[]}` + 同步 upsert 到 MySQL
- [ ] **每账号 WCDB 实例生命周期**：独立端口（默认 8788 逐 +1）、`ensureRunning`（ping 探测，未运行用 `electron + wcdb_server.js <key> <port> <data_dir>` 后台拉起，detached 隐藏窗口）；`start/stop`（netstat 找端口 PID → taskkill）
- [ ] `activate(id)`（先 ensureRunning → 写注册表 current）；`checkKey`（存在且 64 位 hex）；`add/remove/rename`
- [ ] **自动发现**：扫微信数据目录（默认 `D:\xwechat_files`，深度 5，跳过 node_modules/cache/temp）找含 `session.db` 的 `wxid_*` 目录 → 候选/忽略/恢复
- [ ] **密钥捕获向导**：`startCapture`（后台 `get_key_v2.js`）+ `captureStatus` 轮询（状态机 9 态）+ `finishCapture`（验证密钥解密→保存 key 文件→注册→启动→切换）+ cancel；中间态写 `capture.json`
- [ ] **WCDB 只读代理**：/ping、/sessions、/messages、/count、/contacts、/displaynames、/sns、/sns-stats；会话过滤（过滤 @chatroom/gh_/系统会话，取前 120）；显示名优先级 备注→昵称→别名→wxid（清洗不可见字符、截 40 字）；extra_buffer protobuf 解析地区（field5/6/7，过滤 CN）；消息类型映射（local_type 低 16 位 + 9 类映射 + 占位符 + 跳过系统消息 + 角色判定）
- [ ] **导入**：`POST /api/wechat/import`（days/max 过滤、文本 <2 条拒绝、wxid 优先复用客户、地区回填城市、同 wxid 同消息数同 end_ts 判重、addConversation 入队）
- [ ] **朋友圈**：/api/wechat/sns 分页、/moments/groups 分组统计、`POST /moments/analyze`（文字≥2 条好友入队 `moments-analysis`，可选 create_customers；完成 SSE `moments.analyzed`）
- ✅ 验收：多账号切换后客户/会话/微信数据完全隔离；无 WCDB 工具时页面给出"先启动实例"提示；有工具时导入会话、画像事实（带置信度/依据）、朋友圈分析与标签可演示

### Phase 6 — 主动触达与全自动接管
**目标**：草稿→审批→(mock)发送→回听→(可选)全自动接管全流程可演示；报表可出数。
- [ ] **草稿生成**：`generateDrafts(customerIds, kind, context)`（业务画像摘要→`generateOutboundMessage`→去重 hash+风险标记→落 `outbox_tasks` draft）
- [ ] **审批状态机**：draft→approved→queued→sending→sent；rejected/cancelled/blocked/failed；事务类可自动发送、营销/关怀类必须人工审批
- [ ] **30s 调度** `executeDue()`（running 防重入）：窗口/日上限/冷却/7 天计数/48h 活跃豁免/发送器健康 → 节奏抖动 `[min,max]`、每 burst 条暂停、daily_cap 默认 5 → POST `SENDER_BASE/send`（mock 可跳过）→ 成功 verification 回读、连败 3 次停批；`sendNow`
- [ ] **20s 回听** `watchReplies()`：新消息检测（end_ts 游标 + lastSeen 基线，首次只打基线）→ 增量入库 + 停推未发任务 + 生成建议 + 落 `reply_events` + SSE `outbound.reply`；**退订/拉黑词**标 blocklisted（停推+不自动回复）；**硬转人工词**强制转人工
- [ ] **send_settings CRUD**（§5.8.4 全参数 + windows 文本域，落 `send_settings` 表，重启保留）
- [ ] **全自动接管**：开关（single/takeover，单条+批量，`auto_reply_state_log` 审计）；BullMQ `auto-reply` 延迟 8~40s（静默期 23:00-08:30 顺延）→ 到点复核 → 智能回复 → 硬闸门（无硬转人工词/输出安全/轮次<20/日预算<10/风暴限流 5min/5条）→ RPA 发送 → `source='ai'` 写回（只在最新一条是客户消息时回，不抢话）
- [ ] **转人工** = takeover_paused=true + 原因 + `handoff_json`（触发消息/建议/原因/最近 12 条上下文/知识条目/商城事实）；仅手动恢复；单条/批量恢复
- [ ] 风暴限流超限顺延至多 3 次后转人工；`auto_reply_note` 注入 prompt；知识库 `customer_ids` 限定子集
- [ ] **报表** `GET /api/outbound/report?days`（send/replies/customer_reply_rate/funnel/takeover）
- ✅ 验收：mock 模式草稿→审批→sent 状态流；设置保存重启保留；回听/接管（如需真实微信）或人工模拟消息可演示；报表出数

### Phase 7 — 知识库
**目标**：条目 CRUD + 双模式检索 + 导入 + 聊天沉淀 + 商城知识同步。
- [ ] CRUD（含 `customer_ids` 范围：null=全账号共享 / 非空=仅这些客户）、status（active/pending）
- [ ] **检索**：默认 TF-IDF 余弦（中文二元组 + 英文单词，idf 平滑，score>0.01 过滤，同分 use_count 降序）；配置 `EMBEDDING_*` 后切向量检索、失败回退本地
- [ ] 导入：Markdown（`## 标题`+段落）、CSV（标题,内容,标签，跳表头）
- [ ] **聊天沉淀** `POST /api/kb/mine`：扫最近 20 客户×3 会话的"提问(问号/吗/呢/怎么/多少/什么 且 ≥4 字)→客服回答(≥4 字)"问答对 → LLM 提炼去重 → pending，人工启用
- [ ] **商城知识同步**：按 `shop_kb_id` 幂等 upsert，保留 `use_count`
- ✅ 验收：新增/导入/沉淀/启用/检索可演示；`customer_ids` 限定生效

### Phase 8 — 商城接入
**目标**：绑定 + 实时查询 + 定时同步 + 意图分类 + 注入接管链路（未配置时优雅降级）。
- [ ] mysql2 连接池（只读、参数化、2.5s 超时、每次查询写 `shop_query_log`）；未配置全部降级
- [ ] 查询：`findUsersByPhone`（精确）/`findUsersByNickname`（LIKE 仅建议）/`findUserByOpenId`/`getOrdersByOpenId`（最新 3 条，open_id 强制限定）/`getMemberAsset`/`searchProducts`（shelf=1 未删，价格 COALESCE）
- [ ] **绑定**：手机号唯一命中自动绑定 / 昵称弱匹配仅"建议" / 人工兜底；绑定后立即拉商城画像（basic_tags/consume_stats/vip_info/ai_summary）合并进画像（`source='商城'`，`enrichCustomerFromShop`）
- [ ] **定时同步**（默认 30min，`SHOP_SYNC_INTERVAL_MIN`）：商品缓存（update_time 游标增量，唯一 pro_id+sku_id）、商城知识、敏感词（全量替换）、已绑定客户画像刷新
- [ ] **意图分类** ShopIntentService：三类词典规则（订单/会员/商品）单命中 0.85、多命中 LLM 裁决失败回退首个 0.5
- [ ] **接管注入**：按意图注入订单状态/物流单号/会员资产到回复 prompt；售后办理/纠纷/定价承诺一律转人工
- ✅ 验收：未配置时页面显示"商城未连接"且其它功能不受影响；配置后绑定/查询/同步/意图可演示

### Phase 9 — 前端
**目标**：全部页面与交互实现，类型全部来自 `@cpd/common`，`vue-tsc --noEmit` 通过。
- [ ] 骨架：`index.html`、`main.ts`、`vite.config.ts`（5173，/api→3000 代理，dist 输出）、`style.css`（§6.3 全套 CSS 变量与组件样式）、`App.vue`（header 徽章/账号切换/localStorage `cp_account`/两栏网格/全宽视图/全局 toast/SSE 订阅）
- [ ] `api.ts`：统一 `api<T>()`（自动带 `X-Account-Id`）+ §5.11 全部函数 + `sentiLabel/sentiColor/avatarColor/avatarChar`
- [ ] `CustomerList.vue`（卡片/接管徽章/情感色标签/新增标签橙色徽章/排序/批量接管）
- [ ] `CustomerDetail.vue`（KPI/接管面板/商城绑定/动态标签/画像事实/意图风险/Sparkline/模拟事件表单/最近事件/微信会话/朋友圈/版本历史）
- [ ] `WechatImport.vue`（双栏/勾选/预览/搜索/地区/批量导入/逐条日志）
- [ ] `MomentsView.vue`（KPI/分析操作/瀑布流/搜索/分页/SSE 日志）
- [ ] `AccountManage.vue`（候选卡片/密钥捕获向导/已忽略/账号表格/新增表单）
- [ ] `OutboundView.vue`（6 Tab：草稿箱/发送记录/发送设置/回复通知/知识库/运营报表，含交接包展开、恢复接管、解除黑名单）
- [ ] `Reports.vue`、`Sparkline.vue`
- ✅ 验收：`pnpm --filter @cpd/web build` 通过、`vue-tsc --noEmit` 零错误；核心链路页面可操作

### Phase 10 — 联调与验收
- [ ] 全量构建：`common → server → web → pnpm start`；确认首页 5 种子客户
- [ ] 逐项跑 §10.3 验收清单（见 §6 对照表）
- [ ] 修复类型/运行问题直至全部通过；产出 README/运行说明

### Phase 11 — 可选增强（不做不阻塞验收）
- [ ] Embedding 向量检索真正生效（配 `EMBEDDING_*`）
- [ ] 商城库表结构现场适配完善
- [ ] RPA 真实发送对接联调

---

## 5. 关键实现要点备忘

- **契约唯一性**：任何结构变更只改 `packages/common`，前后端编译期立刻暴露不一致。
- **fallback 纪律**：所有 LLM 调用必须 try/catch → 规则兜底 → `engine` 字段标注（`LLM(<model>)` 或 `规则`/`微信规则`/`商城`）。
- **数值钳制**：weight/sentiment/confidence 解析后一律 clamp，防止脏数据污染画像。
- **隐私红线**：消息生成只用 5 个业务字段；发送前必过 `checkTextSafety`；商城完整手机号/地址不进 LLM。
- **异步不阻塞**：入队失败不阻塞主流程；HTTP 202 先行返回；SSE 是刷新驱动，别在处理器里等结果。
- **账号隔离**：服务层一律经 `currentIdValue()`；SSE 按 `?account=` 过滤；本地缓存 key 必须带 accountId 前缀。
- **幂等**：合并客户/会话、商城知识 upsert、微信导入判重都要幂等，启动恢复路径尤其要稳。
- **合规**：保留文档 §9 的声明（个人微信自动化违反微信用户协议）；UI 无隐藏群发/拉新能力。

---

## 6. 验收对照表（§10.3 → 阶段）

| §10.3 | 验收项 | 验证阶段 | 验证方式 |
| --- | --- | --- | --- |
| 1 | 首次启动 5 种子客户，画像版本≥1，标签/情感/意图/风险有值 | P4/P10 | 启动后首页 + DB 检查 |
| 2 | 模拟事件→待分析→版本+1→高亮→SSE toast→不刷新更新 | P4/P9/P10 | 页面操作 + 控制台 |
| 3 | 重启数据不丢、不重复调 LLM | P4/P10 | 重启后核对 |
| 4 | 无 Key 规则引擎可演示；配 Key 测试连接成功、引擎显示 LLM 引擎 | P2/P10 | `/api/engine` + 页面 |
| 5 | 导出 JSON 备份；重置恢复种子 | P4/P10 | 页面按钮 |
| 6 | 草稿→审批→(mock)sent；设置保存重启保留 | P6/P10 | 页面操作 |
| 7 | 知识库/商城绑定/接管引用知识库与商城事实 | P7/P8/P6/P10 | 页面操作（未配置时验证降级提示） |
| 8 | 微信导入全流程（有 WCDB 时） | P5/P10 | 页面操作 |
| 9 | 多账号完全隔离；账号管理增删改/启停/清空/导出 | P5/P10 | 页面操作 |
| 10 | `vue-tsc --noEmit` + `nest build` 零类型错误 | P10 | 构建命令 |

---

## 7. 风险登记与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| Prisma 7 / Vite 8 与 Node 版本不匹配 | 安装/构建失败 | 环境按 ≥22.12 准备；Phase 1 先做最小 `db push` 验证 |
| SSE 与账号头冲突 | 事件串号/收不到 | 采用 `?account=` 方案（D1） |
| 外部工具（WCDB/RPA/商城/旧 SQLite）缺失 | 相关模块无法真实演示 | 一律降级 + mock，验收项相应降级为"提示正确" |
| 商城表结构未知 | 查询失败 | 字段名按文档先实现 + 映射层隔离 + 现场适配 |
| 微信自动化的封号风险 | 合规 | 保留 §9 声明；只做低频文字单发；文档明示 |
| LLM 模型名/响应格式漂移 | 解析失败回退 | `llmJson` 容错 + 规则兜底 + `testLLM` 现场确认 |
| 全量落库（persistCustomer）性能 | 数据多时慢 | MVP 接受；保留优化注释；缓存兜底 |
| 20s/30s 轮询与 60s debounce 竞态 | 重复分析/漏分析 | 游标 + running 防重入 + job 名区分 delta/full |

---

## 8. 给执行者（Codex / 后续 Agent）的执行守则

1. **不许"简化或省略"任何模块**，尤其 outbound/接管/知识库/商城；缺环境就降级，不许砍功能。
2. 接口契约**只来自 `@cpd/common`**，禁止前后端各写一套。
3. 严格按 §5.2 建表（表名/字段/索引/默认值一致，时间 String、JSON Text）。
4. 分析引擎必须"规则离线可用 + LLM 切换/失败回退"，规则明细照 §5.3.1。
5. 全部界面文案简体中文；构建必须过 `nest build` 与 `vue-tsc --noEmit`。
6. 每完成一个 Phase 跑一次该阶段验收再继续；最终按 §6 对照表逐项自证并给出验证结果。
7. 保留本文件 §3 的决策（D1–D15），如与文档冲突以本节决策为准并注释说明。
