---
tags: [资产, 会话库, datasette]
created: 2026-09-26
---

# 跨工具 AI 会话库

> 把 Codex / Claude Code / DSH / ZCode / Grok 的全部对话汇总成一个可全文检索的库。

[[00_微信聊天分析总览|← 总览]] ｜ [[全盘资产总图]] ｜ [[原始数据源索引]] ｜ [[分析流水线]] ｜ [[DSH工作区]]

## ⚠️ 这里只是「已入库」的部分

`unified.db` 覆盖 **20,293 条已 ETL 入库**的会话。
**但磁盘上还有大量原始会话未入库**，在 [[DSH工作区]] 的 `04_会话归档\`：

| 未入库资产 | 内容 |
|---|---|
| `DeepSeek会话整理_20260827\` | DSH 全部历史会话 A–H 八类导出（41 会话，24,845 条） |
| `DSH溢出会话备份_Temp抢救\` | 2026-09-01 从 Temp 抢救的 **33 个溢出会话** |
| `DSH导出工具_20260827\` | 会话导出脚本 catalog/decompress/extract/organize.js |
| `Codex会话\` | 全量清单、分类、导出、数据库备份 |
| `Claude工作区\` | Claude 时代工作区（含 WeFlow 四套备份） |
| `opencode交接\` | 交接模板 + Go 接线手册 |
| DSH 程序会话库 | `AI-archive\apps\deepseek-harness\state\sessions\`（84 MB / 58 会话） |

> 💡 **待办**：跑一遍 `etl.py` 把这批也纳入 `unified.db` 的检索范围。

## 数据

| 来源 | 消息数 |
|---|---:|
| Codex (GPT-5.6-Sol) | 13,000 |
| Claude Code | 3,520 |
| DSH (DeepSeek Harness) | 3,518 |
| ZCode (Trae) | 250 |
| Grok | 5 |
| **合计** | **20,293** |

- 库文件：`C:/Users/wardc/Documents/New project gpt/AI-archive/conversations/unified.db`（169.5 MB · SQLite + FTS5）
- **在线检索：http://127.0.0.1:8001/unified**
- 启动：`cd AI-archive/conversations && python -m datasette unified.db --metadata metadata.json --port 8001`

## 中文检索已验证

- 搜「微信」→ 195 命中
- 搜「关宇佳」→ 8 命中
