# CONTEXT-PROTOCOL · 强制上下文续接协议

本协议保证：**不依赖对话窗口记忆。** 任何会话崩溃、关闭或上下文接近耗尽后，新会话仅凭
`SESSION-HANDOFF.md` + `RUN-STATE.json` 即可无损失恢复。

## 1. 何时必须写检查点（checkpoint）

以下任一时刻，**在继续做任何事之前**先运行 checkpoint：

1. **每个重要里程碑完成时**（发现跑通、候选生成、复核页生成、测试全绿、报告落盘）。
2. **每次修改代码之前**（改任何 `src/`、`scripts/`、`tests/`、`config/` 文件前）。
3. **每次运行测试之前 / 之后**。
4. **任何长任务开始之前**（恢复命令、已完成、未完成、风险、下一步必须先落盘）。
5. **发现上下文接近不足时**：先 checkpoint，再停止，并在 `SESSION-HANDOFF.md` 留下可复制的新会话启动提示。

## 2. checkpoint 命令

```powershell
python scripts/checkpoint.py `
  --milestone "EVENT-DISCOVERY-ENGINE-CODED" `
  --phase "event-center-phase1" `
  --status "running" `
  --done "新增 src/v3_events.py（信号提取+候选聚类）" `
  --next "python -m unittest tests.test_v3_events -v" `
  --risk "候选聚类跨日合并阈值需要 dry-run 后校准"
```

脚本会**原子**重写 `SESSION-HANDOFF.md` 与 `RUN-STATE.json`（临时文件 + `os.replace`），
历史叙事保留在 `.checkpoint/handoff_history.md`，每次检查点追加记录到
`.checkpoint/log.jsonl`。

## 3. 新会话恢复流程（写进每次 handoff）

1. `cat SESSION-HANDOFF.md`（读状态 + 恢复命令）。
2. `cat RUN-STATE.json`（读结构化状态与统计）。
3. 运行 `## 恢复命令` 一节列出的验证命令（测试、dry-run、verify），确认未回退。
4. 从 `## 下一步` 继续；**任何涉及 API 或扩大范围的动作必须先经用户确认**。

## 4. 强制约束（每会话重申）

- 只写本工作区 `10_DeepSeek-v3分析工作区`；`01_主项目`、WeFlow 导出、原始聊天库只读。
- 只新建 `_v3` 版本化表，不覆盖 `annotations` / `aggressive_*` / `contact_*` 历史表。
- 事件候选**必须同时**具备时间 + 实体/项目词 + 任务/语义线索三类信号，禁止只按日期合并。
- 候选、证据、联系人关联、复核、最终判断全部可回链到 `message_id` / `segment_id` / `candidate_id`。
- API Token 只从环境变量读取；不打印、不写入任何文件。当前阶段**不调用任何 API**。
- 不自动发送微信/外部消息；不删除原始导出。
- 试运行并发 ≤8，当前仅授权 ~30 个高信号事件候选的无 API 复核包；完成即暂停等确认。

## 5. 上下文接近耗尽的信号与动作

- 症状：回答变慢、丢细节、同一文件反复重读、无法回忆本会话早段决策。
- 动作：立即运行一次 checkpoint（用 `--milestone "CONTEXT-CHECKPOINT"`），
  在 `SESSION-HANDOFF.md` 顶部写一段「新会话启动提示」（一段可复制的恢复命令），然后停止。
