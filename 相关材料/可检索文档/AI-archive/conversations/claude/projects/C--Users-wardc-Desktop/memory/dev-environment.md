---
name: dev-environment
description: "What dev tooling is installed on the user's Windows machine (Claude Code, VS Code, Git, Node, Python, SSH)"
metadata: 
  node_type: memory
  type: project
  originSessionId: d25b5302-142a-4c22-a709-5ea8f2aa6d13
---

Installed & configured the user's Windows 11 dev environment on 2026-06-28:

- **Claude Code CLI** v2.1.195 (native build) at `C:\Users\wardc\.local\bin\claude.exe`; that dir added to user PATH.
- **VS Code** 1.126.0 + `anthropic.claude-code` extension.
- **Git** 2.54, **Node.js** 24.18 LTS + npm 11.16, **Python** 3.12.10 (`py` launcher), **Windows Terminal** (pre-existing).
- **SSH**: ed25519 key at `~/.ssh/id_ed25519` (passphrase-less), `~/.ssh/config` has a github.com entry. ssh-agent autostart NOT yet enabled (needs admin: `Set-Service ssh-agent -StartupType Automatic`).
- **Git global config**: user.name=蔡浩文, user.email=kayleigh_teneturzy@protestant.com, init.defaultBranch=main, core.autocrlf=true.
- Common project dir at `C:\Users\wardc\Desktop\Projects`.

**Claude Code now points at Xiaomi MiMo** (configured & tested working 2026-06-28):
- It's a **Token Plan** (`tp-` key) → must use base URL `https://token-plan-cn.xiaomimimo.com/anthropic` (NOT `api.xiaomimimo.com`, which is for pay-as-you-go `sk-` keys; mixing them gives 401 Invalid API Key).
- Model `mimo-v2.5-pro` for all tiers (opus/sonnet/haiku mapped to it); append `[1m]` for 1M context.
- Config in `~/.claude/settings.json` env block, user-level env vars, and PowerShell profile `Documents\WindowsPowerShell\profile.ps1`. `~/.claude.json` has `hasCompletedOnboarding:true`.
- MiMo does NOT support Claude Code Thinking/extended-thinking — must toggle it off (Tab) or requests error.
- Desktop doc: `C:\Users\wardc\Desktop\小米MiMo接入ClaudeCode-配置说明.md` (contains the raw key — sensitive).

See [[machine-health-g15]] for hardware caveats (confirm whether G15 and this `wardc` machine are the same).
