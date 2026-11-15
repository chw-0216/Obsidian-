---
name: clash-verge-setup
description: Clash Verge Rev v2.5.1 已装于 Program Files; 有一键导入 IP:端口:账密 凭证的自动化脚本 节点导入ClashVerge.ps1
metadata: 
  node_type: memory
  type: project
  originSessionId: f8e50ce4-0b28-4f3f-981a-18bba6d0b908
---

2026-07-11 装好 Clash Verge Rev v2.5.1（`C:\Program Files\Clash Verge`，配置在 `%APPDATA%\io.github.clash-verge-rev.clash-verge-rev`，混合端口 7897，TCP 外部控制器默认关闭只留命名管道）。与 [[proxy-setup]] 的 v2rayN 并存，两者勿同时开系统代理。

**主力工具**：`Claude工作区\02_脚本与工具\节点转订阅.py`（+同名 .bat 双击版，2026-07-12）— 离线、无 AI/API，把任意格式节点地址转成 Clash 订阅文档并自动导入。支持 IP:端口:账密 四段凭证、ss/vmess/trojan/vless(Reality)/hysteria2/tuic/socks5 URI、订阅链接（直连失败自动走 v2rayN 下载）、base64 订阅。流程：解析 → 凭证类自动加 v2rayN 前置候选 → verge-mihomo 临时实例（17890/控制器19091）逐个校验+测延迟 → 文档存档到 订阅输出\ → 写入固定档案 uid `lclaude0001`（覆盖式不堆积）→ 重启软件 → 经 7897 验证出口 IP。`--convert-only` 只出文档。用户曾想接 MiMo API 做 AI 解析，后改要求纯离线（旧 PS1 版 节点导入ClashVerge.ps1 已被取代但保留）。

**排查经验**（2026-07-11，节点 198.65.3.86:443 案例）：这类四段凭证的服务商常封中国大陆来源 IP（返回 `errorMsg: Mainland China IP banned`），需 v2rayN 前置（mihomo `dialer-proxy`）；该节点同端口跑 SOCKS5 + HTTP 网关 + SNI 中继（SNI 中继模式经前置实测可通、无需认证，但非标准代理协议，Clash 无对应出站类型）；当时那组账密已被 SOCKS5 明确拒绝（rejected username/password）= 凭证过期。curl 测链式代理可用 `--preproxy socks5h://127.0.0.1:1099`。
