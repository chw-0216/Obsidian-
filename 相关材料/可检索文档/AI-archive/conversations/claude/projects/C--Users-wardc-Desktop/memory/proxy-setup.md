---
name: proxy-setup
description: "User's v2rayN proxy ports and CLI proxy env-var setup for region-locked services"
metadata: 
  node_type: memory
  type: project
  originSessionId: fd104b03-bdd0-4080-878c-b6b9864c1327
  modified: 2026-07-20T23:44:55.769Z
---

User is in China (Beijing) and relies on **v2rayN** for a proxy. Local listeners: SOCKS5 `127.0.0.1:1099`, HTTP `127.0.0.1:1100`, PAC `127.0.0.1:1101`. Verified 2026-07-01: node exits via US (LAX), OpenAI auth endpoint reachable through the HTTP proxy.

**Why:** CLI tools (Codex, git, npm, Claude Code) ignore Windows PAC settings and connect directly with the China IP, which trips region blocks (OpenAI Codex login returned 403 "Country not supported" because the token-exchange step went direct).

**How to apply:** For region-locked CLI work, ensure traffic goes through the proxy. User-level env vars are now set permanently: `HTTPS_PROXY`/`HTTP_PROXY` = `http://127.0.0.1:1100`, `ALL_PROXY` = `socks5://127.0.0.1:1099`, and (added 2026-07-21) `NO_PROXY` = `localhost,127.0.0.1,::1,xiaomimimo.com,.xiaomimimo.com`.

**PAC vs env vars — two separate systems, don't conflate them.** User habitually runs v2rayN in **PAC mode** (`AutoConfigURL` = `http://127.0.0.1:1101/pac/…`, `ProxyEnable=0`). That PAC is gfwlist2pac-generated (~8000 domains) and its `FindProxyForURL` **strips subdomains progressively and matches parent suffixes** — so `api.anthropic.com` is proxied via the `anthropic.com` entry, while `xiaomimimo.com` is absent and goes direct. But **PAC only covers WinINET apps (browsers)** — CLI tools (Rust/reqwest, Node, curl, git) never read `AutoConfigURL`, which is exactly why the env vars exist. Consequence: env vars have **no smart routing**, so domestic endpoints get pushed through the US proxy unless listed in `NO_PROXY`. Adding `xiaomimimo.com` measured **0.84s → 0.08s**; official API still correctly proxied. Add more domestic domains to `NO_PROXY` as they come up. Caveat: when v2rayN is OFF, these vars make CLI tools fail (can't reach 127.0.0.1:1100) — clear them for that session. Relates to [[dev-environment]].

**Codex proxy facts (verified 2026-07-21):**
- `@openai/codex` npm package is a JS launcher around a **Rust binary** (`@openai/codex-win32-x64/vendor/.../codex.exe`, ~308MB). Rust/reqwest **does** honor `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`/`NO_PROXY` — so env vars work for Codex.
- Codex picks `HTTPS_PROXY` (1100) over `ALL_PROXY` (1099) — observed via TCP connection capture.
- **Use the HTTP proxy (1100), NOT SOCKS5 (1099), for Codex.** A/B with `codex exec`, two rounds each, fully reproducible: SOCKS5 → `Transport channel closed` ×3 and `http/request failed` ×3 every round; privoxy → 0 every round. Failures concentrate on long-lived/streaming connections (the MCP HTTP-streaming transport at `backend-api/ps/mcp`). The old 4.x v2rayN's SOCKS5 inbound handles streaming poorly. SOCKS5 *is* faster per single request (0.59s vs 0.86s) and is theoretically more protocol-transparent — that reasoning is a trap here; stability wins. Worth re-testing if v2rayN is upgraded to an xray/sing-box build.
- `wss://` handshake succeeds through **both** SOCKS5 (clean `101 Switching Protocols`) and privoxy (CONNECT tunnel). The privoxy-breaks-WebSocket theory was **tested and not confirmed**. privoxy's `limit-connect` is not restricted either (`CONNECT :8443` → 200).
- Connection capture during a real `codex exec` showed **no direct-to-internet connections** — no proxy bypass, WebSocket included.
- v2rayN here is an **old 4.x-style build** (`wv2ray.exe` + external `v2ray_privoxy.exe`), which has **no TUN mode**. Clash Verge v2.5.1 has TUN capability but no service/wintun installed and its only node (`198.65.3.86`) **requires v2rayN as a front proxy** — so Clash-Verge TUN would create a routing loop and kill all connectivity. Full all-protocol (UDP/QUIC) coverage is therefore not achievable until a standalone working node exists in a TUN-capable client.
- Env vars only cover TCP via cooperating libraries; they cannot cover UDP/QUIC. See [[clash-verge-setup]].
- 2026-07-21: upgraded `@openai/codex` 0.142.5 → 0.144.6 (old CLI was rejected with 400 "requires a newer version" for model `gpt-5.6-sol` in user's config.toml). After upgrade, end-to-end `codex exec` through the launcher succeeded with zero errors. Launcher script: `Desktop\Claude工作区\02_脚本与工具\Codex走代理.ps1` (probes 1100-first, verifies exit country, per-process env injection). A `codex` wrapper function in the (newly created) PowerShell `$PROFILE` routes plain `codex` through the launcher automatically; bypass with `& "$env:APPDATA\npm\codex.cmd"`.
