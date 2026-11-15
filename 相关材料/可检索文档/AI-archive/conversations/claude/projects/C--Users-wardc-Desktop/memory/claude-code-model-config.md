---
name: claude-code-model-config
description: "mimo vs 官方 Anthropic 的配置冲突：桌面端强制官方端点，导致 mimo 模型名泄漏搞坏 web 工具"
metadata:
  node_type: memory
  type: project
  originSessionId: d09bcb75-25ca-4b6f-ab53-c14abd203de6
  modified: 2026-07-20T23:34:43.588Z
---

用户的 Claude Code 在**两处**都写着完整 mimo 配置：用户级环境变量 **和** `~/.claude/settings.json` 的 `env` 块 —— `ANTHROPIC_BASE_URL` = `https://token-plan-cn.xiaomimimo.com/anthropic`、`ANTHROPIC_AUTH_TOKEN` = `tp-…`、`ANTHROPIC_MODEL` 与 `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL` 全 = `mimo-v2.5-pro`。

历史：2026-07-10 曾移除（备份 `settings.json.bak-20260710`），07-17 用户要求接回。

**冲突机理（2026-07-21 查清）：** Claude Code **桌面端会强制把 `ANTHROPIC_BASE_URL` 覆盖成 `https://api.anthropic.com`**（它用订阅 OAuth 登录），却仍继承环境变量里的 mimo **模型名**。这个混搭是坏的：`WebSearch` 报 `There's an issue with the selected model (mimo-v2.5-pro)`，因为 web 工具用 `ANTHROPIC_DEFAULT_HAIKU_MODEL`，而官方端点没有这个模型。所以"接回 mimo 会搞坏 web 工具"有了精确机理——**不是 mimo 本身不行**。

**已验证事实：**
- mimo token 和端点**有效** —— 直接 `POST /anthropic/v1/messages` 用 `mimo-v2.5-pro` 拿到正常回复。必须**不走代理**（国内端点；直连 0.25s vs 经 v2rayN 0.84s）。
- `api.anthropic.com` 在这台机器上**直连 403**、**经代理 401**（即可达）—— 官方 API 必须走代理，而代理已全局配好。见 [[proxy-setup]]。
- **桌面端无法用 mimo**，配置层面改不动，应用会覆盖。终端 `claude` CLI 则可以。

**建议做法：** 按运行环境拆开 —— 把 mimo 配置从全局环境变量 / settings.json 挪进 PowerShell `$PROFILE` 里的 `claude` 包装函数（与 [[proxy-setup]] 中 codex 启动器同款方案），让 CLI 得到完整 mimo（省订阅额度）、桌面端回到干净官方 OAuth（web 工具正常）。

⚠️ **2026-07-21 已向用户提出此方案，用户未作选择，因此未改动任何配置——目前仍是全局 mimo 状态，桌面端 web 工具持续报错。** 动之前务必先问：这是在订阅额度和可用 web 工具之间权衡，属用户决策。相关：[[dev-environment]]
