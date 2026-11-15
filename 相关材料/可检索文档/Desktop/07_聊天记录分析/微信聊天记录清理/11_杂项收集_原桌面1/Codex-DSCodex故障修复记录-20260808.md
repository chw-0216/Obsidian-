# Codex DSCodex 路由污染修复记录

**日期**: 2026-08-08  
**故障现象**: ChatGPT Codex Work 模式打不开，所有 GPT 请求返回 HTTP 401

---

## 根因

DSCodex 在 `~/.codex/config.toml` 中注入了全局路由覆盖：

```toml
openai_base_url = "http://127.0.0.1:10110/.../v1"
model_catalog_json = "C:\\Users\\wardc\\.codex\\dscodex-models.json"
```

所有 Codex 原生 GPT 请求被劫持到 DSCodex 本地代理（127.0.0.1:10110），
DSCodex 转发 ChatGPT OAuth 失败（HTTP 401），导致 Work 模式不可用。

### 故障链

```
Codex / Work
    ↓
~/.codex/config.toml → openai_base_url
    ↓
127.0.0.1:10110 → DSCodex
    ↓
转发 ChatGPT OAuth → 401
    ↓
Work / 原生 GPT 功能失败
```

---

## 修复操作

**原则**: 最小修复，只删除两条路由覆盖，其他一切保留。

### 已删除

- `openai_base_url = "http://127.0.0.1:10110/.../v1"`
- `model_catalog_json = "C:\\Users\\wardc\\.codex\\dscodex-models.json"`

### 已保留

| 配置项 | 值 | 原因 |
|---|---|---|
| `model` | `gpt-5.6-sol` | 当前正常配置，不做版本回退 |
| `model_reasoning_effort` | `max` | 同上 |
| `ANTHROPIC_BASE_URL` 等 6 项 | `api.deepseek.com/...` | Claude Code → DeepSeek 桥接，与 Codex 无关 |
| `HTTP_PROXY / HTTPS_PROXY` | `127.0.0.1:1100` | v2rayN，正常代理 |
| `[desktop] enabled-reasoning-efforts` | DSCodex 注入 | 非路由项，第二阶段处理 |
| `[model_providers.ollama-local]` | `localhost:11434` | 独立 provider，非全局覆盖 |
| `[model_providers.deepseek-via-litellm]` | `127.0.0.1:4000` | 独立 provider，非全局覆盖 |

---

## 修复后架构

```
           ┌→ OpenAI/ChatGPT 原生后端 → Codex / Work ✅
你的电脑 ──┤
           └→ DeepSeek (ANTHROPIC_BASE_URL) → Claude Code ✅
```

---

## 备份文件

| 文件 | 说明 |
|---|---|
| `~/.codex/config.toml.bak-before-native-route-restore-20260808-190927` | 修复前快照（含 DSCodex 注入） |
| `~/.codex/config.toml.pre-dscodex.bak` | DSCodex 安装前的干净配置 |
| `~/.codex/config.toml.backup` | OpenCodex 注入版（03:40） |
| `~/.codex/rollback-20260808/` | 8月8日回滚目录 |

---

## 历史故障时间线

```
2026-08-08 00:38  OpenCodex 创建 profile (opencodex.config.toml → 10100)
2026-08-08 03:40  OpenCodex 改写 config.toml (openai_base_url → 10100)
2026-08-08 04:14  干净配置备份 (pre-dscodex.bak)
2026-08-08 04:54  OpenCodex config.json 最终写入
2026-08-08 17:47  DSCodex 移除 + Codex 更新
2026-08-08 18:12  DSCodex 重新部署 (V4 Pro)
2026-08-08 19:02  DSCodex 注入当前 config.toml (openai_base_url → 10110)
2026-08-08 19:09  本次最小修复完成
```
