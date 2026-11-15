# DeepSeek v3 微信分析工作区约定

本工作区用于在不覆盖历史成果的前提下，开发并试运行微信聊天记录 v3 分析流水线。

## 边界

- 只允许修改本工作区：`C:\Users\wardc\Desktop\微信聊天记录清理\10_DeepSeek-v3分析工作区`。
- 以下目录只读参考，不得修改、移动或删除：
  - `C:\Users\wardc\Desktop\微信聊天记录清理\01_主项目_WeChat-MiMo-Analyzer`
  - `C:\Users\wardc\Desktop\微信聊天记录清理\09_未迁移脚本与运行依赖`
- 使用本工作区的 `data\scale\wechat-analysis-scale.sqlite3` 数据库（已扩容授权）；不得写回旧数据库。
- 不删除原始 WeFlow 导出，不触碰未被 WeFlow 解析的微信本机数据，不自动发送微信或其他外部消息。
- API Token 只能从环境变量或 Claude 设置读取；不得打印、复制、写入源码、日志、报告或聊天内容。
- 已完成全量标注（6,303 段），授权已扩容至全量 Phase 2/3 + 深度联系人报告。无需再次确认。

## 模型与数据原则

- Claude Code 当前会话使用 `deepseek-v4-flash`。
- 直接批量调用也使用已配置的 DeepSeek Anthropic 兼容接口，不得改动全局配置。
- 不索取或保存隐藏思维链。输出只保留短理由、证据 ID、置信度、替代解释和需用户确认项。
- 明确区分原文事实、可观察行为、模型推断和不确定解释。
- 每项重要结论必须能回链到 `segment_id` 或消息 `evidence_id`。

## 工程原则

- 新建版本化的 `_v3` 表和结果文件，不覆盖 `annotations`、`aggressive_*`、`contact_*` 历史表。
- 实现真正的短片段合批、长片段窗口切分、有限重试、正常退出、断点续跑、输入哈希去重和原子写入。
- 进度按完整片段数、各阶段覆盖率、失败率和每百万 Token 的有效结果统计；不要用 output tokens/min 单独预测完成时间。

## 当前任务：继续 Phase 2/3

**重要：新会话启动后，第一件事是读 CHECKPOINT.md，然后检查是否有旧进程需要先处理。**

快速启动命令：
```powershell
cd "C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区"
.\启动-Phase2-Phase3.ps1
```

此脚本自动设置环境变量（token + proxy），按顺序执行 Phase 2 → Phase 3 → 深度联系人报告。

## 上下文压缩策略

当 Claude Code 触发自动压缩（auto-compact）时：

1. **保留核心信息**：CHECKPOINT.md 的关键状态、数据库路径、端点信息、启动命令
2. **压缩中间输出**：Phase 2/3 的逐条联系人分析结果可以压缩，但最终汇总排名必须保留
3. **主动压缩**：在 Phase 2 完成后、Phase 3 启动前，手动执行 `/compact` 清理 Phase 2 的逐条输出
4. **COMPACT.md**：此文件定义了压缩时保留的内容结构，见项目根目录 COMPACT.md

