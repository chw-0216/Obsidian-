---
name: wechat-export-4110
description: 微信 4.1.10.53 聊天记录导出尝试——当前无可用工具;2025下半年生态被团灭
metadata: 
  node_type: memory
  type: project
  originSessionId: d09bcb75-25ca-4b6f-ab53-c14abd203de6
---

用户想批量导出本机全部微信聊天记录(自己账号,合法备份需求)。机器上是**微信 4.x「Weixin」新版,版本 4.1.10.53**,数据目录 `C:\Users\wardc\AppData\Roaming\Tencent\xwechat\`(不是老 3.x 的 WeChat)。

**核心结论(2026-07-10 更新):** 微信 **Windows 4.1.10 起改了密钥机制**——不再把 raw key 缓存进内存,只留一个 passphrase,用完即从内存清零;真实 enc_key 需 `PBKDF2-SHA512(passphrase, db_salt, 256000, 32)` 现推。所以 chatlog / wechat-decrypt 的内存扫描全部 0 命中(实测管理员下扫完 886MB 主进程仍 0 hex 模式)。分界线明确:**Windows 4.1.9.x 仍能扫到(旧 raw key 缓存),4.1.10.x 起扫不到**。macOS 4.1 已有 LLDB 断点方案破解,Windows 4.1.10 尚无验证过的直接方案。

**可行解法(小降级,已按此推进):** 降到 **微信 4.1.9** → 登录 → `find_all_keys.py` 提密钥(作者实测 27/27)→ `decrypt_db.py` 解密 → 可再升回 4.1.10(`all_keys.json` 仍有效,因 enc_key 对账号/设备稳定)。4.1.9 安装包:archive.org `wechat-win-4.1.9` / `WeChatWin_4.1.9.exe`(md5 d3e0151764545e368a03a5565114e8b8,sha1 973b540d20ea69c47c7eebfa9958edbd03c184cc,须验签是否腾讯官方)。备份在 `D:\wechat_backup_20260710`,安装包在 `D:\wechat_downgrade`。
**活跃账号:** `wxid_zn4ozsnn8esr21_db45`(数据库 294MB message_0.db;另有旧小号 wxid_1wa75s1kze3o22_4180 可忽略)。
**主力工具:** `ylytdeng/wechat-decrypt`(Python,克隆在工作区 01_GitHub项目,已建 .venv 装 pycryptodome+zstandard,config.json 已配好)。备用直接破 4.1.10 的实验性工具:`TANGandXUE/wcdb-key-tool` 的 `wcdb_key_tool_windows.py capture-experimental`(需 Windows SDK 的 cdb.exe,作者标注**未验证**)。

---
**历史背景:** 2025 下半年老一代工具被团灭:
- chatlog(sjzar):2025-10-20「final commit」封版,只到 4.0 时代;实测 `chatlog key` 即使管理员+指定主进程(PID 20584/Weixin.exe)仍 `no valid key found`——认不出 4.1.10 内存布局。
- PyWxDump(xaoyaoo):2025-10-20「删库跑路~」作者清空。
- wechat-dump-rs(0xlane):GitHub 返回 451,法律下架。
- WeChatMsg/留痕(LC044):2025-12 只有「更新图片/改 readme」,撤了全部 release,无代码更新;README 已 404。

**已在本机装好的东西(以后要重试可复用):** Go 1.26.5(`C:\Program Files\Go`)、mingw-w64 gcc 16.1.0(WinLibs,`%LOCALAPPDATA%\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_...\mingw64\bin`,winget 报 exit1 但文件完好、PATH 未注册)、chatlog.exe 已用 `CGO_ENABLED=1` 编译成功于 `C:\Users\wardc\go\bin\chatlog.exe`。

**尚存的路子:** ①微信官方「聊天记录迁移与备份→备份到电脑」(能存但只能还原回微信,不可读为数据);②把微信降级到 4.0.x 让 chatlog 能解(有强制更新/拒绝登录/4.1库不兼容旧客户端的风险,未尝试)。相关:[[dev-environment]] [[proxy-setup]]
