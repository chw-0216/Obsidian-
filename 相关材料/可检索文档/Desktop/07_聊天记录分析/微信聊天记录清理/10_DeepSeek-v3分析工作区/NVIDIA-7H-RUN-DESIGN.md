# NVIDIA 免费 DeepSeek v4 pro · 7 小时微信深度分析运行设计

> 状态：**代码就绪，等待 NVIDIA API key（nvapi-...）一键启动**
> 设计日期：2026-08-28

## 一、目标

在 NVIDIA 免费层（`https://integrate.api.nvidia.com/v1`，≤ 40 RPM）上，用 DeepSeek v4 pro 模型，
对微信聊天记录做一轮 7 小时上限的深度分析，主任务是**全量未标注片段的标注**，
并顺带处理可深度分析的事件。

## 二、关键事实（已核实）

| 项 | 值 |
|---|---|
| 全量片段 | 6,303（scale 库 `data/scale/wechat-analysis-scale.sqlite3`） |
| 已 v3 成功标注 | 82 片段 |
| 历史标注（旧版+激进版） | 227 片段（归一化在 `_v3_hist_segments`，只读） |
| 本次计划单元 | 8,972 个（全量 plan 实测） |
| 本次计划批次 | 5,268 批（每次 API 调用处理一批） |
| 全局限速 | 40 RPM（NVIDIA 免费层上限） |
| 计划生成耗时 | 1.5 秒（去重优化后；原 >2 分钟） |
| 测试基线 | 73/73 通过 |

## 三、容量核算：7 小时足够

- 40 RPM × 60 × 7 = **16,800 次调用上限**
- 全量 5,268 批次 → 需 5,268 次调用
- 纯限速时间 = 5,268 ÷ 40 ≈ **131.7 分钟 ≈ 2.2 小时**
- 加每请求耗时（约 3–15 秒，并发 3 worker），主体阶段约 **2.5–3.5 小时**
- **7 小时预算绰绰有余**，留有约 3–4 小时余量应对重试与慢请求

> 注意：40 RPM 是**硬顶**（令牌桶强制 ≤ 40 次/分钟），不是吞吐。3 个并发 worker 的
> 潜在吞吐约 45 RPM，被限速器压回 40，因此实际速率稳定在 40 RPM 附近。

## 四、执行流程（启动脚本 `启动-NVIDIA-7小时分析.ps1`）

- **阶段 0**：无 API 基线验证（`unittest` 73 测试 + `plan` 全量预演）
- **阶段 A（主体）**：全量片段标注 —— `deepseek_v3_executor run`，40 RPM 限速，
  去重自动跳过已标注（内容哈希 + 模型 + 提示词版本）
- **阶段 B**：pending 事件深度分析（见下方「数据缺口」，当前会安全跳过）
- **阶段 C**：生成质量报告

## 五、本次代码改动（均已落地，测试全绿）

1. **`src/v3_api.py`**（核心）
   - 新增 `api_style`：`"anthropic"`（默认，DeepSeek 官方不回归）/ `"openai"`（NVIDIA）
   - 新增 `TokenBucket` 全局限速器（`rpm_limit`），保证所有并发调用合计 ≤ RPM 上限
   - 新增 OpenAI 兼容响应解析（`extract_openai_text`）
   - 内置 aiohttp vendor 回退（不再依赖调用方传 `vendor_dir`）
2. **`src/deepseek_v3_executor.py`**
   - 读取并传递 `api.api_style` / `api.rpm_limit` / `api.rate_burst`
   - **去重性能优化**：`_load_existing_success_hashes()` 一次预加载成功哈希，
     消除全量 plan 时的 N+1 连接（2 分钟 → 1.5 秒）
3. **`src/v3_deep_analyzer.py`**
   - `analyze` 新增 `--api-style` / `--rpm-limit`，深度分析同样走 NVIDIA + 限速
4. **`src/v3_event_pkg.py`**（修复既有 bug）
   - `resolve_source_candidates` 自洽设置 `row_factory`（修复 tuple 索引 TypeError）
   - `_involved_conversations` 合并 evidence ∪ contacts 会话（修复事件包漏块）
5. **`tests/test_v3_event_pkg.py`**（修复 fixture SQL 语法）
6. **新增**：`config/v3_config.nvidia.json`、`启动-NVIDIA-7小时分析.ps1`
7. **诊断脚本**：`diag/inspect_pending_events.py`、`diag/inspect_evs_source.py`、`diag/inspect_evs_detail.py`

## 六、已知数据缺口（诚实说明）

**2 个 pending 事件是拆分空壳，无法深度分析：**
- `evs_31ee09e464ed1148`（和舒哥聚会）
- `evs_36fb1961def13dc1`（打折机票/跨国托运咨询）

核实结果：两者在 `_v3_event_judgments` 有标题，但 `source_candidate_ids` 指向自己不存在的候选，
`_v3_event_evidence` 0 行、`_v3_event_contacts` 0 行 —— 拆分时证据/联系人未随拆分产物迁移。

**影响**：阶段 B 会尝试构建包，失败后安全跳过（0 副作用）。这 2 个事件要深度分析，
需先人工回填：在 `_v3_event_candidates` / `_v3_event_evidence` / `_v3_event_contacts`
补上源候选与证据，或把它们的 `source_candidate_ids` 改指回真实源候选 `evc_*`。

另一个已知事项：6 个 review 未判定候选（`evc_26dade557b9a44d9`、`evc_374bcb53c2c95d8a`、
`evc_3d7ca93accc87bbc`、`evc_3e7f57ed2cc104d9`、`evc_60302951ac5b08a4`、`evc_e634c423d1d70d5f`）
仍是 pending，不在本次深度分析范围。

## 七、如何启动（等 key 后）

```powershell
# 方式一：参数传 key（仅本进程内存，不落盘）
cd 'C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区'
.\启动-NVIDIA-7小时分析.ps1 -ApiKey "nvapi-你的key"

# 方式二：环境变量
$env:NVIDIA_API_KEY="nvapi-你的key"
.\启动-NVIDIA-7小时分析.ps1
```

## 八、安全边界（沿用工作区约定）

- 只写本工作区 `10_DeepSeek-v3分析工作区`；`01_主项目` / `09_未迁移脚本` / WeFlow 导出 / 原始库只读。
- 只写 `_v3` 版本化表，不覆盖历史表。
- API key 只从环境变量/参数读取，不打印、不落盘。
- 不自动发送微信/外部消息，不删除原始导出。
- 全局限速 40 RPM 主动节流，不触发 429。
