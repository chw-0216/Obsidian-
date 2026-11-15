# COMPACT.md — Claude Code 上下文压缩保留指令

## 压缩时保留以下内容

### 1. 核心状态（必须保留）
- 当前运行阶段（Phase 1/2/3/深度报告）
- 数据库路径：`data/scale/wechat-analysis-scale.sqlite3`
- 端点：`http://156.238.239.147:3000/v1`，model: `custom/deepseek-v4-pro`
- 当前活跃进程 PID 及其 run_id
- 最近一次 RUN-STATE.json 的关键字段

### 2. 已完成任务摘要（必须保留）
- Phase 1 标注完成数（成功/失败/总数）
- Phase 2 模式提取完成数/总数
- Phase 3 进化完成数/总数
- 深度联系人报告完成数

### 3. 待完成任务（必须保留）
- 下一步需要执行的命令（完整、可直接复制运行）
- 当前阻塞/失败需要修复的问题

### 4. 关键修复记录（必须保留）
- `ApiClient.call()` 返回 `(parsed, in_tok, out_tok)` 三元组，不要二次调用 extract_openai_text
- `thinking: {type: disabled}` 必须加到请求体
- `--token` 从 `ANTHROPIC_AUTH_TOKEN` 环境变量读取
- 25 个失败标注跳过即可，不影响 Phase 2/3

### 5. 可以丢弃的
- Phase 2/3 逐条联系人的详细分析输出（文件已保存到 runs/deep_evolution/）
- 日志文件的完整内容（已保存到 logs/）
- 重复的错误诊断信息
- 中间调试命令的输出

## 压缩后恢复流程

压缩后，Claude Code 应该：
1. 检查 CHECKPOINT.md 获取最新状态
2. 检查是否有遗漏的活跃进程
3. 从上次中断的地方继续执行