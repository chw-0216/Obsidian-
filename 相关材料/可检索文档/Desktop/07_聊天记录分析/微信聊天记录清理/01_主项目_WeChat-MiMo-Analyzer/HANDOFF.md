# HANDOFF.md — 上下文交接文档
> 更新时间：2026-08-02 15:45

## 已完成的代码修改

### 1. 数据库 Schema 扩展 (`src/aggressive_executor.py`)
- 新增表：`aggressive_annotations`, `aggressive_message_annotations`, `aggressive_entities`, `aggressive_events`, `aggressive_run_stats`
- 与旧 `annotations` 表并存，不冲突
- 旧表 87 条标注保留不动

### 2. 同步执行器 (`src/aggressive_executor.py`)
- urllib 直连 MiMo API（不走 Claude CLI 子进程）
- Schema 嵌入 system prompt（不走 metadata）
- 自动 worker 扩容（4→6→9→13→19，基于错误率）
- 按 char_count ASC 排序（小片段优先）
- 每批次 300s 超时
- 已验证：94 片段成功入库，0 消息标注丢失

### 3. 异步执行器 (`src/async_executor.py`)
- aiohttp 连接池（已安装到 `vendor/` 目录）
- 三段式 Schema：Pass A 消息级 / Pass B 片段级 / Pass C 实体合并
- 自适应合批：单消息 10个/批，2-3消息 5个/批，4-10消息 2个/批，>10消息切窗口
- 专用 writer 线程（asyncio Queue → SQLite 批量提交 + JSONL 分片）
- 5 队列加权调度（55%消息标注 / 20%片段上下文 / 10%复标 / 10%实体合并 / 5%证据裁判）
- Pass A/B/C 端到端验证通过（3片段，111s）
- **尚未全量部署**

### 4. 诊断工具
- `src/diagnostic.py` — 5步渐进验证
- `src/stage0_check.py` — 启动前检查

## MiMo API 兼容方式
```
POST https://token-plan-cn.xiaomimimo.com/anthropic/v1/messages
Headers: x-api-key, anthropic-version: 2023-06-01, Content-Type: application/json
Body: {model, max_tokens, system, messages}
```
- **不要用 metadata.anthropic_json_schema** — MiMo 不支持，会返回截断响应
- **Schema 必须嵌入 system prompt**
- 输出 token 上限 16384
- 实测延迟：1条消息 ~30s，10条 ~50s，60条 ~111s

## 吞吐基准测试结果（2026-08-02 15:43）
| Workers | 成功率 | Output tok/min | 备注 |
|---------|--------|---------------|------|
| 32 | 75% | 43,415 | ← 最佳 |
| 64 | 75% | 41,934 | |
| 96 | 70% | 46,074 | |
| 128 | 60% | 33,155 | |

**注意**：所有级别成功率只有 75%，错误来自 Pass A 的 evidence_id 验证失败（模型返回的 ID 与输入不完全一致）。需要修复验证逻辑或 prompt。

## 已知问题
1. **evidence_id 验证过严**：模型有时截断或修改 evidence_id hash，导致验证失败。需要在 prompt 中更强调"必须完全一致"，或放宽验证为前缀匹配
2. **大片段输出截断**：60条消息片段输出 ~9734 tokens（16K 上限的 60%），但加上 Pass B/C 三次调用总 token 更多
3. **同步执行器速率瓶颈**：urllib 同步调用，单 worker ~1.6/min，19 workers ~11/min

## 已否决的方案
- `metadata.anthropic_json_schema` — MiMo 不支持
- `claude -p` 子进程调用 — 太慢，无法并发
- 按 message_count DESC 排序 — 大片段先跑容易撞 token 上限
- 全字段单 Schema — 输出太大，需要拆分 Pass A/B/C

## 待实施设计（已在 async_executor.py 中编码但未全量运行）
- [ ] 自适应合批（已编码）
- [ ] 双层 Schema 拆分 Pass A/B/C（已编码）
- [ ] 异步长连接池（已编码，vendor 已安装 aiohttp）
- [ ] 32-256 并发基准测试（部分完成：32/64/96/128 各100次）
- [ ] 专用 writer 线程 + JSONL 分片（已编码）
- [ ] Token/min 吞吐监控（已编码）
- [ ] 自动扩容基于吞吐而非错误率（已编码）

## 下一步准确操作顺序
1. **修复 evidence_id 验证**：在 Pass A prompt 中更强强调 ID 必须完全一致，或改为前12字符前缀匹配
2. **安全停止旧执行器**：确认 `byflxks1f` 已停止（已做）
3. **启动异步执行器**：`python src/async_executor.py`，初始 32 workers
4. **观察前100个片段**：确认成功率 >95% 后再放量
5. **基准测试 192/256 workers**：如果 128 仍稳定
6. **全量运行直到 6303 片段完成**
