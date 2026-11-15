---
name: codex-windows-sandbox
description: Codex 桌面版 Windows 沙箱状态与「找不到指定的模块」弹窗的根因/处置办法
metadata: 
  node_type: memory
  type: project
  originSessionId: a323715c-d3c4-4eb1-9694-082f6604c8f7
  modified: 2026-08-08T10:15:25.288Z
---

2026-07-08 排查结论(Codex MSIX 26.623.19656,config `[windows] sandbox = "elevated"`):

- 沙箱已完整安装:本地用户 CodexSandboxOnline/Offline、codex_sandbox_* 防火墙规则、`~/.codex/.sandbox/setup_marker.json`(v5)、`.sandbox-bin` 副本均就位;`codex sandbox <cmd>` 实测以 codexsandboxoffline 运行成功。
- 弹窗「codex-windows-sandbox-setup.exe 找不到指定的模块」= MSIX 应用做 **UAC 提权 setup** 时的 bug(提权后丢包身份,从包外/提权上下文启动 WindowsApps 内 exe 会失败;普通 CreateProcess 路径全部正常且有日志)。安装完成后正常使用不再触发。
- 若弹窗复发(通常在 Codex 更新、marker 版本升级后):用托管 CLI 在包外跑一次沙箱即可修复:
  `& "$env:LOCALAPPDATA\OpenAI\Codex\bin\<最新hash>\codex.exe" sandbox cmd /c whoami`
- 诊断入口:沙箱日志 `~/.codex/.sandbox/sandbox.YYYY-MM-DD.log`;桌面日志 `%LOCALAPPDATA%\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\Codex\Logs`。
- 2026-07-08 应用户要求把 Codex 权限全部拉满:config.toml 设 `sandbox_mode = "danger-full-access"`、`approval_policy = "never"`、`[tools] web_search = true`、`[shell_environment_policy] inherit="all" + ignore_default_excludes=true`(命令以 wardc 全权直跑、零审批)。备份:`config.toml.bak-before-full-access`。同日装了 ripgrep(winget)修复 doctor 的 search 警告。
- 2026-07-08 又按使用习惯补配:全局 `~/.codex/AGENTS.md`(中文默认+背景+Windows/代理/Ollama/VS Code 环境);`file_opener = "vscode"`;`[history] persistence = "save-all"`。
- Profile(此版本用**独立文件**格式 `~/.codex/<名>.config.toml`,内联 `[profiles.*]` 表会冲突报错):`finance`(on-request+workspace-write)、`aigc`(满权限,=全局默认)、`offline`(model hermes3:8b + ollama-local provider)。用 `codex -p <名>` 切换;`-p` 只对运行类命令有效,对 doctor 无效。
- 2026-07-08 用户澄清:真实用途是**生活/创意**类(情感分析、视觉设计、文档打磨),不是财经/代码。据此把 AGENTS.md 主线改成情感/生活+视觉设计+文档打磨(财经降为次要);建 `~/.codex/prompts/` 三个斜杠命令:`/情感`(共情+落地建议)、`/设计`(明确设计方向+直接产出)、`/文档`(结构/措辞/排版一起改+改动说明)。prompt 用 `$ARGUMENTS` 接用户输入。
- 2026-08-08 DSCodex 移除→重新部署 V4 Pro:Codex MSIX 26.803.5235.0(cli 0.147.0)。先彻底停用 OpenCodex 10100 自恢复(`codexAutoStart:false,codexShimAutoRestore:false`),保留 rollback 备份。然后改 DSCodex 源码(`tools/dscodex/src/`)从 V4 Flash→V4 Pro:constants.mjs(slug+wire model)、catalog.mjs(display/desc/identity)、autostart.mjs+cli.mjs(帮助文本)。设 DeepSeek API Key(sk-cde7e...)和 v2rayN HTTP 代理(127.0.0.1:1100)用于 GPT 流量的出站代理。install→start(PID 15460 port 10110)成功。架构:GPT 模型→chatgpt.com/backend-api/codex(OAuth forward);deepseek-v4-pro→api.deepseek.com/responses(API Key)。⚠️ V4 Pro 的 Codex Responses API 尚未开放(返回"available early August 2026"),GPT 模型此期间正常工作。自启动:Startup 文件夹 VBS(非 schtasks,免管理员权限)。备份:`config.toml.pre-dscodex.bak`、`config.toml.bak-dscodex-removal-20260808`、`rollback-20260808/`。
- 相关:[[proxy-setup]](marker 里 proxy_ports 1099/1100 即 v2rayN 端口),[[dev-environment]]
