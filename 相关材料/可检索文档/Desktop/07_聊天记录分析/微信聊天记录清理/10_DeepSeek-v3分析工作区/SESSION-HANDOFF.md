# SESSION-HANDOFF · 微信分析 v3 工作区

更新：2026-08-17T08:18:37+08:00 · 阶段：deep-analysis-phase1 · 状态：running

## 新会话启动提示

请先读 CLAUDE.md、CONTEXT-PROTOCOL.md、SESSION-HANDOFF.md、RUN-STATE.json，运行「恢复命令」验证未回退，然后继续下一步：

  python -m src.v3_deep_analyzer dryrun runs/deep_keep_rest --db data/wechat-analysis-v3.sqlite3

任何 API 或扩大范围的动作先经用户确认。

## 恢复命令（新会话从这里开始）

```
python -m unittest discover -s tests -v
```
```
python -m src.v3_events discover --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_events bundle --db data/wechat-analysis-v3.sqlite3 --limit 30
```
```
python -m src.v3_events dryrun --db data/wechat-analysis-v3.sqlite3
```
```
阅读 DEEP-REVIEW-SPEC.md，升级 v3_events.py / v3_event_review.py / schema / tests；不调用 API
```
```
python -m unittest discover -s tests -v（基线验证）
```
```
python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.draft.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_event_pkg build --events evc_a5d9c3c5dbbb6caf,evc_59a505bbba79b7e8,evc_93130b1552a25445 --db data/wechat-analysis-v3.sqlite3 --outdir runs/deep_p1
```
```
python -m src.v3_deep_analyzer dryrun runs/deep_p1 --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_deep_analyzer analyze runs/deep_p1 --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_deep_analyzer analyze runs/deep_alumni --db data/wechat-analysis-v3.sqlite3
```
```
python -m src.v3_deep_analyzer dryrun runs/deep_keep_rest --db data/wechat-analysis-v3.sqlite3
```

## 当前状态

全量 11 个 keep 事件深度分析完成（校友会 3 + 其余 8），全量权力结构视图已生成 reports/POWER-STRUCTURE-VIEW-20260817.md。8 个新事件 8/8 成功，合计输入 150K/输出 24K ≈ 17.4 万 token。核心发现：Sīrius R（周冉学姐，女）3 事件全部 unequal/them 是典型异性+权力结构；用户默认位置为服务者/执行者；情感不对称仅在陈老师与舒哥。

## 检查点日志（最新在前）

### DEEP-ALL-KEEP-11-EVENTS-DONE @ 2026-08-17T08:18:37+08:00
> 全量 11 个 keep 事件深度分析完成（校友会 3 + 其余 8），全量权力结构视图已生成 reports/POWER-STRUCTURE-VIEW-20260817.md。8 个新事件 8/8 成功，合计输入 150K/输出 24K ≈ 17.4 万 token。核心发现：Sīrius R（周冉学姐，女）3 事件全部 unequal/them 是典型异性+权力结构；用户默认位置为服务者/执行者；情感不对称仅在陈老师与舒哥。
- **已完成**：批量深度分析 8 个剩余 keep 事件（8/8 成功）；聚合 11 事件/38 联系人全量权力结构视图；生成 reports/POWER-STRUCTURE-VIEW-20260817.md
- **未完成**：用户确认跨事件模式洞察（服务者定位/认可诉求）；2 个 pending 事件（和舒哥聚会/机票托运）未纳入，可后续处理
- **风险**：全部为模型推断(inferred)，跨事件模式仅 SīriusR/方老师/陈老师达 3 事件阈值，其余为单事件观察
- **下一步**：python -m src.v3_deep_analyzer dryrun runs/deep_keep_rest --db data/wechat-analysis-v3.sqlite3

### DEEP-ALUMNI-3-EVENTS-READY @ 2026-08-17T08:09:31+08:00
> 聚焦校友会 3 事件（中秋联谊会/橄榄球联谊赛/公众号事务）深度分析，0 API 准备就绪。强化权力结构分析：DEEP_SYSTEM_PROMPT 新增「权力结构分析」指引 + relationship_profile 新增 power_dynamic 字段（balance/dominant_side/asymmetry_dimensions/gender_relevant）。9 测试全绿。3 事件包已构建到 runs/deep_alumni，dryrun 输入合计 72.6K 字符。阻塞：ANTHROPIC_AUTH_TOKEN 未设置。
- **已完成**：强化 DEEP_SYSTEM_PROMPT 权力结构分析 + power_dynamic 字段；9 个无 API 测试全绿；构建校友会 3 事件包到 runs/deep_alumni（中秋 24片段/橄榄球 5片段/公众号 3片段）；dryrun 确认输入规模：公众号 6.3K / 橄榄球 12.5K / 中秋 53.8K 字符
- **未完成**：用户配置 ANTHROPIC_AUTH_TOKEN 后运行 analyze
- **风险**：ANTHROPIC_AUTH_TOKEN 未设置，analyze 会因缺 token 失败
- **下一步**：python -m src.v3_deep_analyzer analyze runs/deep_alumni --db data/wechat-analysis-v3.sqlite3

### DEEP-ANALYZER-IMPLEMENTED @ 2026-08-17T07:42:41+08:00
> 深度分析模块 src/v3_deep_analyzer.py 完成（0 API 编码）：DEEP_SYSTEM_PROMPT + build_deep_input + parse_deep_result + apply_deep_result + _v3_event_deep_analysis 表 + dryrun/analyze CLI。8 个无 API 测试全绿。dryrun 确认 3 事件输入规模合计 91K 字符（中秋 53.8K/舒哥钓鱼 24.7K/橄榄球 12.5K）。暂停等用户确认 token 预算再跑 analyze。
- **已完成**：实现 DEEP_SYSTEM_PROMPT（5 深度槽位+反证+备选+置信度，证据回链）；实现 build_deep_input（facts+证据+联系人+完整片段，保留 msg id 回链）；实现 parse_deep_result（schema 校验 + evidence_id 回链校验）；实现 apply_deep_result + _v3_event_deep_analysis 表（记录 token/模型/prompt 版本/证据覆盖）+ 回填候选槽位；8 个无 API 测试全绿（tests/test_v3_deep_analyzer.py）；dryrun 验证输入规模：橄榄球 12.5K / 舒哥钓鱼 24.7K / 中秋 53.8K 字符
- **未完成**：用户确认 token 预算后运行 analyze（真正调用 DeepSeek v4 Flash）
- **风险**：analyze 需 ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN 环境变量 + 用户明确授权；中秋联谊会 53.8K 字符为最大单事件输入，单次调用可容纳（<128K 上下文）
- **下一步**：python -m src.v3_deep_analyzer analyze runs/deep_p1 --db data/wechat-analysis-v3.sqlite3

### DEEP-ANALYZER-IMPLEMENTATION-START @ 2026-08-17T07:40:42+08:00
> 开始实现深度分析模块 src/v3_deep_analyzer.py：把事件包转成深度分析输入（完整片段+证据+联系人+facts），单事件单次 API 调用输出 5 个深度槽位+反证+备选+confidence。0 API 编码阶段。
- **已完成**：审查 3 事件包组成：中秋联谊会 24片段(16信号+8上下文)/44K字符；橄榄球 5片段/9.9K；舒哥钓鱼 15片段/18.8K；抽查发现上下文片段 SīriusR ord10 含报名结果等关键后续，确认不能粗暴删上下文；确认 API 基础设施可复用：v3_api.ApiClient.call + parse_json
- **未完成**：实现 DEEP_SYSTEM_PROMPT + build_deep_input + parse_deep_result + apply_deep_result + ensure_deep_schema；新增 _v3_event_deep_analysis 表（记录 token/模型/prompt版本/证据覆盖）；dryrun 验证 0 API + 无 API 测试
- **风险**：97K token 估算为 char-based 高估，实际约 50-60K，单次调用可容纳；深度分析真正调用 API 前须经用户确认 token 预算
- **下一步**：python -m src.v3_deep_analyzer dryrun runs/deep_p1 --db data/wechat-analysis-v3.sqlite3

### DEEP-P1-PACKAGES-BUILT @ 2026-08-15T14:43:44+08:00
> 深度分析首阶段：3 个已确认事件完整聊天包已构建（0 API）。修正恢复命令模块名笔误(v3_event_package->v3_event_pkg)并优化 v3_event_pkg.py 的 N+1 查询。3 事件输入 token 估算合计约 18.3 万。
- **已完成**：修正交接文档/恢复命令模块名笔误；优化 retrieve_segments 的 N+1 查询（一次 IN 查询替代逐条查询）；构建 3 事件完整聊天包到 runs/deep_p1（中秋联谊会 97K tok / 橄榄球 26K / 舒哥钓鱼 61K）
- **风险**：深度分析多步调用会放大 token；中秋联谊会包 97K tok 最大，需先经用户确认 token 预算再调用 API；单测 body 通过但 tempfile 清理在沙箱受限，已在真实 build 命令上验证功能
- **下一步**：python -m src.v3_event_pkg build --events evc_a5d9c3c5dbbb6caf,evc_59a505bbba79b7e8,evc_93130b1552a25445 --db data/wechat-analysis-v3.sqlite3 --outdir runs/deep_p1

### DEEP-P1-RETRIEVAL-START @ 2026-08-08T02:01:59+08:00
> 深度分析首阶段：为 3 个已确认事件（2025中秋联谊会·筹备报名 / 校友会·奥森橄榄球联谊赛 / 与舒哥钓鱼）检索完整聊天包。已授权 DeepSeek v4 Flash API；先检索后跑 3 事件验证质量，暂停等确认再批量。
- **已完成**：读协议+54 测试全绿；确认 3 事件候选/证据/联系人/窗口规模
- **未完成**：实现完整聊天包检索模块；为 3 事件生成事件包；深度分析 3 事件
- **风险**：事件窗口含大量非信号消息，完整包按信号所在片段 transcript 取；李紫懿/舒泽林会话消息多需控 token
- **下一步**：python -m src.v3_event_pkg build --events evc_a5d9c3c5dbbb6caf,evc_59a505bbba79b7e8,evc_93130b1552a25445 --db data/wechat-analysis-v3.sqlite3 --outdir runs/deep_p1

### EVENT-REVIEW-30-FINALIZED @ 2026-08-07T01:02:24+08:00
> 30 候选人工复核完成并落库：event_review_feedback.draft.jsonl（30 行预填草稿，用户确认）→ finalize → _v3_event_review 30 行（confirmed 11/split 1/rejected 12/pending 6）+ _v3_event_judgments 13 个最终事件。54 测试全绿。0 API。
- **已完成**：生成 event_review_feedback.draft.jsonl（30 行，判定结合原文证据）+ 可读预览页 event_review_feedback.draft.preview.html；finalize 落库：_v3_event_review 30 行；_v3_event_judgments 13 事件（11 确认 + 1 拆分×2）；model_guess 与 user_correction 并存 30/30；reports/EVENT-REVIEW-DEEP-DRYRUN-REPORT.md 追加第 7 节复核结果；54/54 测试全绿
- **未完成**：6 个 pending 候选（c95d8a/c104d9/5b08a4/d70d5f/9a44d9/c87bbc）可继续人工确认，改草稿重跑 finalize；深度分析 token 计划仍待用户确认（填充深度槽位）
- **风险**：无 API 阶段深度槽位保持为空；深度分析须先经用户确认 token 预算；6 pending 不落最终判断，如需纳入须补充判定后重跑
- **下一步**：python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.draft.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3

### EVENT-REVIEW-HTML-FIXED-REOPENED @ 2026-08-07T00:42:47+08:00
> 复核页空白 bug 已修复并验证：RUN_ID 替换后缺引号导致 JS 语法错误→整页空白。模板改为 const RUN_ID="__RUN_ID__"，node --check 通过，headless Chrome 确认 30 张预填档案卡渲染正常、无未捕获错误；已重新打开复核页等待用户确认显示与开始人工复核。
- **已完成**：event_review.html 模板 RUN_ID 引号 bug 已修（const RUN_ID="__RUN_ID__"）；node --check 校验 JS 语法通过；headless Chrome 确认 30 卡渲染、0 未捕获错误；临时文件已清理；已重新打开 runs/event_review_p1_deep/event_review.html 等待用户确认
- **未完成**：用户确认复核页正常显示；完成 30 候选人工复核并导出 event_review_feedback.jsonl 到 runs/event_review_p1_deep/；运行 finalize 落库（见下一步）；深度分析 token 计划仍待用户确认（用于填充深度槽位）
- **风险**：若页面仍空白：确认是否旧缓存版本（按 Ctrl+F5 强制刷新）或非默认浏览器打开；无 API 阶段深度槽位保持为空；深度分析须先经用户确认 token 预算
- **下一步**：python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3

### USER-CHOSE-MANUAL-REVIEW-30 @ 2026-08-07T00:34:45+08:00
> 用户选择 2：对 30 个高信号事件候选执行低负担人工复核（0 API）；深度分析 token 计划仍待用户另行确认
- **已完成**：生成 runs/event_review_p1_deep/event_review.html（30 候选预填档案复核页）
- **未完成**：用户在浏览器打开复核页逐卡确认；导出 event_review_feedback.jsonl；finalize 落库
- **下一步**：python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3

### DEEP-REVIEW-IMPLEMENTED-DRYRUN-DONE @ 2026-08-07T00:31:42+08:00
> DEEP-REVIEW-SPEC 两项强制要求落地完成并 dry-run 通过：预填判断档案（facts+深度槽位+反证槽位+暂定判定）+ 低负担复核页（首屏预填/确认纠偏/猜测修正并存/幂等落库）。54 测试全绿，219 候选落库，30 候选复核包+HTML 已生成。已暂停等待用户确认深度分析 token 计划
- **已完成**：schema 补列+幂等迁移；build_analysis_profile；assess_stability；USER_VERDICTS 反馈链路；event_review.html 模板；真实 DB dry-run：219 候选全部 retrieval_ready；runs/event_review_p1_deep/ 复核包+HTML；EVENT-REVIEW-DEEP-DRYRUN-REPORT.md
- **未完成**：用户确认是否执行模型级深度分析（token 预算）；30 候选人工复核
- **风险**：深度分析需用户确认 token 预算后才可填充深度槽位；无 API 阶段槽位保持为空
- **下一步**：python -m src.v3_event_review finalize runs/event_review_p1_deep/event_review_feedback.jsonl --bundle runs/event_review_p1_deep/event_review_bundle.json --db data/wechat-analysis-v3.sqlite3

### EVENT-TESTS-GREEN-54 @ 2026-08-07T00:30:26+08:00
> 事件中心测试全绿：54/54（42 基线 + 12 新增事件测试）。新增覆盖：预填字段导出/导入幂等、模型猜测与用户修正并存、反证槽位存在、三事件阈值暂定判定、schema 补列幂等、HTML 渲染安全
- **已完成**：新增 tests/test_v3_events.py（12 测试全部通过）
- **未完成**：真实 DB dry-run + 30 候选复核包 + 渲染 event_review.html；dry-run 报告；更新 RUN-STATE/SESSION-HANDOFF
- **风险**：无 API 阶段槽位必须保持为空；用户确认后如需深度分析须先确认 token 预算
- **下一步**：python -m src.v3_events dryrun --db data/wechat-analysis-v3.sqlite3

### DEEP-REVIEW-SCHEMA+PROFILE-IMPLEMENTED @ 2026-08-07T00:29:50+08:00
> 实现预填判断档案数据契约与 schema：analysis_status/confidence/analysis_profile_json，幂等补列；build_analysis_profile 只生成确定性 facts + 空深度槽位 + 反证槽位 + conclusion_stability；低负担复核页模板已补全
- **已完成**：v3_events.py：STABILITY_REQUIRED_EVENTS/assess_stability/build_analysis_profile/schema 补列+幂等迁移/write_candidates+build_bundle 携带档案；v3_event_review.py：USER_VERDICTS/load 校验 user_verdict+user_correction/apply 落库三新列/_EVENT_REVIEW_HTML_TEMPLATE 补全
- **未完成**：运行新增事件测试；dry-run+复核包+报告；更新 RUN-STATE/SESSION-HANDOFF
- **风险**：HTML 模板 JS 语法风险；无 API 阶段槽位必须保持为空，避免被误读为模型已推理
- **下一步**：python -m unittest discover -s tests -v

### SESSION-RESUME-IMPLEMENT-DEEP-REVIEW @ 2026-08-07T00:19:12+08:00
> 续接会话：把 DEEP-REVIEW-SPEC.md 两项强制要求落地到 schema/代码/复核页/测试
- **已完成**：已读 CONTEXT-PROTOCOL/SESSION-HANDOFF/RUN-STATE/DEEP-REVIEW-SPEC/v3_events.py/v3_event_review.py/test_v3_noapi.py
- **未完成**：实现预填档案数据契约与 schema；实现低负担复核页；新增无 API 事件测试；dry-run 报告
- **风险**：v3_event_review.py 尚未实现 _EVENT_REVIEW_HTML_TEMPLATE，render 会 NameError
- **下一步**：python -m unittest discover -s tests -v（基线验证）

### USER-DIRECTION-DEEP-REVIEW-SPEC @ 2026-08-07T00:18:02+08:00
- **已完成**：已写入 DEEP-REVIEW-SPEC.md：深度预填判断档案与低负担人工确认界面为强制规范
- **风险**：无 API 阶段只能建立预填档案框架和证据包，不能伪造模型深度结论；深度推理须另行确认 token 预算
- **下一步**：阅读 DEEP-REVIEW-SPEC.md，升级 v3_events.py / v3_event_review.py / schema / tests；不调用 API

### EVENT-DISCOVERY-ENGINE-CODED @ 2026-08-07T00:14:20+08:00
> 事件发现引擎 src/v3_events.py 完成并调优：强合并键限特定人名+专有项目词；人物正则收紧；递归词过滤增强；复核包多样去重。dry-run 219 候选，top30 覆盖 陈老师3/舒泽林3/格拉18/井邻2。
- **已完成**：新增 src/v3_events.py（信号提取/时间解析/活动段聚类/跨会话候选链接/打分排序/select 多样去重/_v3_event_* 表）；dry-run 验证：219 候选，跨联系人 103，多日 96，关键上下文 103；top30 覆盖全部 4 大指定上下文；井邻拼住/舒泽林托运/校友会招生均为真实线索
- **未完成**：实现 v3_event_review.py：event_review.html（确认/改名/调时间/合并拆分/角色/事实推测/期待价值）+ 反馈落库；单元测试 test_v3_events.py；生成 ~30 候选复核包 + 渲染 event_review.html；dry-run 报告 + 最终检查点
- **风险**：跨月人员主线（周冉/校友会）跨多会话，个别候选偏大，交由复核页拆分；泛用姓氏+称谓 仍可能误识（明白学长→白学长），影响有限
- **下一步**：python -m unittest discover -s tests -v

### PHASE1-START @ 2026-08-07T00:01:44+08:00
> 事件中心第一阶段启动：无 API 事件候选发现 + 本地复核页 + ~30 候选复核包 + 上下文续接机制。
- **已完成**：已读 CLAUDE.md/START-HERE/SESSION-HANDOFF/RUN-STATE 与现有 v3_review/v3_hist/executor 代码；已建 CONTEXT-PROTOCOL.md 与 scripts/checkpoint.py（原子更新 handoff/run-state）；已完成数据探查：725 会话/71550 消息/6303 片段；关键上下文 陈老师25/舒泽林1会话/格拉185/井邻29/周冉40；无真实群聊；两库内容一致
- **未完成**：实现 v3_events.py 信号提取+候选聚类+表结构；实现 v3_event_review.py 复核包+event_review.html+反馈落库；生成 ~30 高信号候选复核包；单元测试 + dry-run 报告
- **风险**：跨日/跨联系人合并阈值依赖 dry-run 校准，先用保守参数；文件传输助手/美团等服务会话需排除，避免噪声候选
- **下一步**：python -m unittest discover -s tests -v

## 项目约束

- 只写本工作区 10_DeepSeek-v3分析工作区；01_主项目 / 09_未迁移脚本 / WeFlow 导出 / 原始库只读。
- 只新建 _v3 版本化表；不覆盖 annotations / aggressive_* / contact_* 历史表。
- 事件候选必须同时具备 时间 + 实体/项目词 + 任务/语义 三类信号，禁止只按日期合并。
- 候选/证据/联系人/复核/最终判断全部回链 message_id / segment_id / candidate_id。
- API Token 只从环境变量读取；不打印不落盘。当前阶段不调用任何 API。
- 不自动发送微信/外部消息；不删除原始导出。试运行并发 ≤8。

## 历史背景

# SESSION-HANDOFF · DeepSeek v3 试运行

更新：2026-08-06（约 21:10，人机协作复核流程闭环；50 片段二次校准完成于 02:00）

## 任务状态

目标：建立可复用的 v3 执行器 + 人机协作复核工作流（证据提取 → 候选判断 → 用户确认/修正 → 关系价值判断），完成分层真实试运行、扩大前校准与人工价值判断，然后停止等待用户确认。
**当前：人机协作复核已闭环。** base-v1.1-compact 50 片段校准完成（82/82 单元，0 失败，Schema 100%，证据回链 100%）；50 片段人工复核全部完成并落库（`v3_review`），43 会话价值聚合（`v3_final_judgments`），复核报告已生成。全量 Token 预测仍 ≈21.6M（超 14M 目标约 7.6M）。已按要求暂停，等待用户确认下一步。复核环节 0 新增 API。

## 已完成

1. **只读检查**
   - 读取 CLAUDE.md、START-HERE.md。
   - 检查 v3 数据库副本结构：725 会话 / 71,550 消息 / 6,303 片段。
   - 检查旧 `async_executor.py` 与 `09_未迁移脚本与运行依赖\高吞吐异步标注流程-复现说明.md`。
   - 已标注覆盖：`annotations` 87 + `aggressive_annotations` 140 = 227 个不同片段（单消息 140、2-3 有 1、4-10 有 0、11-30 有 2、31+ 有 84）。

2. **安全边界确认**
   - 只写工作区 `10_DeepSeek-v3分析工作区`；`01_主项目` / `09_未迁移脚本` 只读。
   - 已备份数据库副本到 `data\backup\wechat-analysis-v3.prewrite.sqlite3`。
   - `verify` 通过：工作区 DB 副本只新增 5 个 `_v3` 表（`v3_annotations`、`v3_message_annotations`、`v3_call_log`、`v3_failures`、`v3_run_meta`），历史表未改动。

3. **API 配置确认（未打印 Token）**
   - base_url：`https://api.deepseek.com/anthropic`（来自 `ANTHROPIC_BASE_URL` 环境变量）。
   - 模型：`deepseek-v4-flash`；Token 只从环境变量 `ANTHROPIC_AUTH_TOKEN` 读取。
   - 冒烟调用 2 次（前台、已完成，均为极小请求）：认证、端点、模型、`max_tokens=8192` 均正常，usage 返回正常。

4. **构建的文件**（全部位于工作区）
   | 文件 | 用途 |
   |---|---|
   | `config/v3_config.json` | 模型/API/并发/合批/重试/抽样/路径配置 |
   | `prompts/base_annotation.md` | 单次调用基础标注提示词与 JSON Schema |
   | `src/v3_core.py` | transcript 解析、清理、PII 脱敏、窗口切分、合批、校验、抽样、重试预算（纯逻辑） |
   | `src/v3_io.py` | `_v3` 表创建、单写者 Recorder 写 DB+JSONL、manifest 原子写入 |
   | `src/v3_api.py` | aiohttp 异步客户端（Anthropic 兼容 /v1/messages，usage 双格式回退） |
   | `src/deepseek_v3_executor.py` | 主执行器：worker 池（真建/真停）、重试泵、并发监控、正常退出、plan/run/report/verify CLI |
   | `src/v3_report.py` | 报告生成（各尺寸耗时、Schema 合格率、证据回链、Token、失败分布） |
   | `src/__init__.py` | 包标记 |
   | `tests/test_v3_noapi.py` | 30 个不调用 API 的测试 |
   | `data/backup/wechat-analysis-v3.prewrite.sqlite3` | 运行前 DB 备份 |
   | `runs/plan_v3_20260805_183059/plan.json` | 当前抽样计划（20 片段 / 31 单元 / 20 批次） |

5. **不调用 API 的测试：全部通过**
   - `python -m unittest discover -s tests` → **30 个测试 OK**（transcript 解析、HTML 实体清理、PII 脱敏、窗口切分、合批预算、提示词只含对应文本、Schema 校验、结果拆分、去重哈希、重试退避、分层抽样优先未标注、Recorder DB+JSONL 往返、并发池真实建/停 worker、JSON 代码围栏解析、thinking 开关）。
   - `python -m src.deepseek_v3_executor verify` → 只新增 `_v3` 表。
   - `python -m src.deepseek_v3_executor plan` → 生成计划，未调用 API。

6. **抽样计划详情（runs/plan_v3_20260805_183059/plan.json）**
   - 各尺寸 4 个片段：单消息 4、2-3 条 4、4-10 条 4、11-30 条 4、31+ 条 4 = 20 片段。
   - 单元 31 个（31+ 与 16 条片段切窗：每窗口 ≤15 条，只含对应文本），批次 20（短单元真实合批），跳过 0。

## 20 片段真实试运行结果（pilot_v3_20260805_184949）

- **成功 31/31 单元，0 失败**；API 22 次调用，429=0、超时=0、校验失败=0、error_rate=0.0455（仅 1 次解析错误被重试消化）。
- **Schema 合格率 100%**（31/31）；**证据回链率 100%**（289/289 引用都落在实际证据内）；标注消息 289 条。
- Token：in=23,619 / out=73,478；耗时 151.6s；平均每请求 in=1125 / out=3499 / 21.4s。
- 各尺寸片段全部成功：单消息 4、2-3 条 4、4-10 条 4、11-30 条 5 单元、31+ 条 14 单元。
- 长片段窗口切分、短片段合批、结果拆分均按设计工作；队列清空正常退出。
- 报告：`reports/PILOT-QUALITY-REPORT.md`；manifest 与 JSONL 在 `runs/pilot_v3_20260805_184949/`。

## 试运行中发现的 Bug 及修复

**症状**：首轮试运行大量单元 `JSON 未闭合` / `响应中没有 JSON`（12 个失败），且失败无 call_log、无重试。
**根因**：DeepSeek Anthropic 兼容端点默认启用思维链（`content` 全是 `type=thinking` 块），模型把 max_tokens=8192 预算全耗在 thinking 上，`extract_text` 只认 `type=text` 故返回空 → 解析失败。
**修复**（已测试 30/30 通过）：
1. `src/v3_api.py`：请求体加 `thinking={'type':'disabled'}`（拆出可测试的 `build_body()`）。
2. `src/deepseek_v3_executor.py`：解析异常（`ValueError`/`JSONDecodeError`）归类为可重试 `error_parse` 并记录 call_log，不再冒泡为永久失败。
3. `tests/test_v3_noapi.py`：新增 5 个测试（代码围栏 JSON 解析、thinking 开关、parse_json 前导文本）。
- 诊断脚本保留在 `diag/diag_api_response.py`（含 base_url/token 读取，无 token 落盘）。

## 已知问题 / 说明

- 报告按**原始片段桶**统计窗口单元（`segment_message_count`），避免把长片段窗口误归入小桶。
- API usage 同时兼容 `input_tokens/output_tokens` 与 `prompt_tokens/completion_tokens`。
- aiohttp 依赖：本机无 aiohttp，执行器回退从只读目录 `09_未迁移脚本与运行依赖\runtime\vendor` 导入（仅读，不改）。
- `prompts/base_annotation.md` 为 base-v1；如提示词变更，`prompt_version` 需同步，去重键为 内容哈希+模型+提示词版本。

## 50 片段校准结果（base-v1.1-compact，pilot_v3_20260806_013846）

- 成功 82/82 单元，0 失败；56 次 API 调用，429=0、超时=0、校验失败=1（已重试消化）。
- Schema 合格率 100%（82/82）；证据回链率 100%（765/765）；标注消息 765 条。
- 每消息输出 194 tok（base-v1 为 254，-24%）；错误率 0.0179（base-v1 0.0455，-61%）。
- **语义抽查 10 例**（`reports/semantic_review_calibration.md`）：证据完整、无编造、事件归属正确；仅发现 2 处提示词口径小问题（#5 把"同意/感谢"误入 requests；#10 commitment 方向写反），不涉及证据与覆盖。
- 报告：`reports/CALIBRATION-QUALITY-REPORT.md`；全量规模报告：`reports/SCALE-READINESS-REPORT.md`。

**Token 会计重要发现**：DeepSeek 兼容端点把 system prompt 做服务端缓存，`input_tokens` 不再计入 system（单独报 `cache_read_input_tokens≈1408/调用`）。执行器只记 `input_tokens`，校准 in=4,509 是低估。修正后全量投影：输入合计 ≈7.82M（用户内容 0.48M + system cache 7.34M）、输出 ≈13.8M、总计 ≈**21.6M**，超出 14M 目标约 7.6M。

## 人机协作复核完成（pilot_v3_20260806_013846，0 新增 API）

**流程**：证据提取（既有 `v3_annotations`）→ 候选关系/预期/背景判断（静态 HTML 复核界面，数据内嵌）→ 用户确认/修正 → 最终关系价值判断（规则聚合落库）。

- 复核包：`runs/pilot_v3_20260806_013846/review/review.html`（50 片段 / 82 窗口单元 / 43 会话；localStorage 自动保存，可刷新续接）。
- 反馈导出：`runs/pilot_v3_20260806_013846/review/review_feedback.jsonl`（50 行，`finalize` 已消费；桌面还有一份副本）。
- 落库：`v3_review` 50 行（确认 49 / 修正 1 / 未复核 0）；`v3_final_judgments` 43 会话。
- 价值：44 段打分均值 39.5（双峰：0-19 十六段 vs 60-79 十九段）；保留建议 28 保留 / 14 清理 / 8 待定。
- 报告：`reports/REVIEW-VALUE-REPORT-pilot_v3_20260806_013846.md`。

**复核界面 bug 已修（重要）**：修正项 JSON 文本框曾双重转义（回显时二次 `JSON.stringify`），导致用户编辑后的文本非法、导出被硬拦截、`review_feedback.jsonl` 一直没生成。修复：文本框直显原始 payload；导出/复制改为「警告后放行」，坏项保留原文并标记 `payload_error`；无效 JSON 项标红提示；文本框编辑接入自动保存。唯一坏项 `seg_0345863f…` 的 relationship_signals[1]「客气罢了」已按原文入库（信息性记录，不影响聚合）。

## 复核后补做（2026-08-06）

1. **历史标注归一化**：`src/v3_hist.py`（0 API）把 227 段三套历史 schema 归一成 `_v3_hist_segments`（227）/ `_v3_hist_messages`（140）备查表，幂等、只读源表。运行：`python -m src.v3_hist --db data/scale/wechat-analysis-scale.sqlite3`。
2. **importance 缺口修复**：见 `RUN-STATE.json` 的 `importance_gap_fixed`（executor `_coerce_importance` + 数据 NULL 修正 + 2 回归测试）。
3. **6 段无备注判定已补说明**（井邻拼住 / 同学学业交流 / 撤回无内容 / 格拉校友会会长周冉·协会宣发 / 姐图文往来 / 单条确认共享）。教训：finalize 用反馈文件全字段覆盖库，备注必须写进 `review_feedback.jsonl` 再跑 finalize。
4. **格拉校友上下文**：周冉是用户所在格拉斯哥校友会会长（用户负责协会宣发），格拉校友片段按高价值对待、倾向 keep。已存长期记忆 `glasgow-alumni-high-value`。全库含「格拉斯哥/格拉/Glasgow」关键词片段约 **133 段**，当前 50 段复核（按 transcript 关键词检测）一个都没覆盖——**扩大复核范围时应优先覆盖**。

## 未完成 / 下一步

1. **下一步起点**：等待用户在窗口中确认（a）是否扩大复核范围（可基于库中其他已标注片段生成更大的复核包）、（b）是否扩大全量分析规模（见 `reports/SCALE-READINESS-REPORT.md` 第 8 节 A/B/C 选项）。未启动全量。
   - 候选优化（可省 ~5M）：提高 `max_units_per_batch`/`max_msgs_per_batch` 减少调用次数（省 system cache）、精简 system prompt（1,408→~1,000 tok/调用）。
   - 若按"cache 折扣价"口径，等效成本 ≈15M，接近 14M。
2. 复核 / 落库命令（0 API）：
   - 重新生成复核页：`python -m src.deepseek_v3_executor review pilot_v3_20260806_013846 --config config/v3_config.scale.json`
   - 反馈落库 + 会话聚合 + 报告：`python -m src.deepseek_v3_executor finalize pilot_v3_20260806_013846 --config config/v3_config.scale.json --feedback runs/pilot_v3_20260806_013846/review/review_feedback.jsonl`
3. 全量运行用 `python -m src.deepseek_v3_executor run --config config/v3_config.scale.json`（如需更高并发可在命令行覆盖，但需先与用户确认；建议 4→8）。
4. 若要复现校准报告：`python -m src.deepseek_v3_executor report pilot_v3_20260806_013846 --config config/v3_config.scale.json`。

## 安全提醒

- 未启动、也不会自动启动全量分析。
- API Token 未打印、未写入任何文件。
- 未删除/覆盖任何历史文件；DB 历史表（annotations / aggressive_* / contact_*）未改动。

