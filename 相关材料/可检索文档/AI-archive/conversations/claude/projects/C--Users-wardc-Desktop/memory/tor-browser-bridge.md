---
name: tor-browser-bridge
description: "Tor Browser bridge config on this machine — Snowflake stalls, meek works"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8e2ef370-8a49-4e01-ae42-f5b5989b1e09
---

Tor Browser is at `C:\Users\wardc\Desktop\Tor Browser` (portable, v140.12.0). On this network (Beijing), the built-in **Snowflake** bridge stalls at bootstrap PROGRESS=10 (`network-liveness=down`, no circuit). The built-in **meek** bridge connects reliably to 100% (~1–2 min, slow but stable).

Config was persisted via `...\TorBrowser\Data\Browser\profile.default\user.js` with `torbrowser.settings.bridges.{enabled=true,source=0,builtin_type="meek"}` and `quickstart.enabled=true` — so it auto-connects on launch with no manual "Connect" click. Delete user.js to change bridges via the UI.

**How to apply:** if Tor won't connect here, prefer meek over Snowflake/obfs4. Diagnose live via control port 9151 (cookie auth at `Data\Tor\control_auth_cookie`): `GETINFO status/bootstrap-phase`; `SETCONF DisableNetwork=0` acts as the "Connect" button. Related: [[dev-environment]], [[machine-health-g15]].
