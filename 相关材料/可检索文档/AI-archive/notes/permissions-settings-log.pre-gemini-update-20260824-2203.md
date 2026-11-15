# Permissions and Settings Change Log

| Date | Task | Files / Folders Created or Changed | Permission Requested / Granted | Settings / Environment Changed | External Locations Touched | Cleanup / Uninstall Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-12 | 外接硬盘 SMART 检查与 D: 卷标更新 | `AI-archive/tmp/run_smart_admin_2026-07-12.ps1`; `AI-archive/tmp/smartctl_sdb_2026-07-12.txt`; `AI-archive/tmp/smartctl_sdb_2026-07-12_clean.txt`; `AI-archive/tmp/label_d_2026-07-12.txt`; `AI-archive/notes/2026-07-12_外接硬盘SMART检查记录.md`; `AI-archive/permissions-settings-log.md` | 用户授权打开 Windows UAC 管理员 PowerShell；读取 `/dev/sdb` SMART；修改 `D:` 卷标 | `D:` 卷标从 `STORAGE` 改为 `CHECK_2026-10-12`；未改 PATH、环境变量、注册表、服务、计划任务 | `D:\` 卷标；`PhysicalDrive1` / `/dev/sdb` SMART 只读查询 | 卷标可用管理员终端 `label D: STORAGE` 改回；删除上述归档文件即可清理本次记录副本；SMART 查询无持久系统残留。 |
| 2026-07-10 | Created unified Codex/ChatGPT archive rule and tracking table | `AGENTS.md`; `AI-archive/README.md`; `AI-archive/permissions-settings-log.md`; `AI-archive/apps/`; `AI-archive/outputs/`; `AI-archive/tmp/`; `AI-archive/assets/`; `AI-archive/notes/` | None beyond current workspace write access | Added future working rule in `AGENTS.md`; no OS/app settings changed | None | Keep this folder as the default home for future AI-created/downloaded/installed files. |
| 2026-07-10 | Updated global Codex rules for permanent archive behavior | `C:\Users\wardc\.codex\AGENTS.md`; `AGENTS.md` formatting | User approved escalated write to global Codex settings file | Changed future default install/archive rule; no OS PATH/env/registry/service setting changed | `C:\Users\wardc\.codex\AGENTS.md` | Future installs go under `AI-archive/apps/<software-name>/`; each app still needs `INSTALL-NOTES.md`. |
| 2026-07-11 | 继续项目资产备份：575周年活动摄影、知行计划、北京台AIGC实习 | `D:\中文分类备份_2026-07-08\02_摄影与图像\格拉斯哥校友会575周年_活动摄影与图文素材\`; `D:\中文分类备份_2026-07-08\03_创作与技术项目\央美志愿项目_知行计划_进行中\`; `D:\中文分类备份_2026-07-08\04_重要文档_求职学业项目\央美研一寒假实习_北京台AIGC\`; Obsidian 项目笔记追加备份记录 | 用户授权/提权读取桌面与 Obsidian，写入外接盘 D: 和 Obsidian 项目笔记 | 无 PATH、环境变量、注册表、服务、计划任务或应用设置改动 | `D:\中文分类备份_2026-07-08\`; `C:\Users\wardc\Desktop\个人数据库_Obsidian\项目\*.md` | 本批次只备份不删除；本机原件仍保留；如需清理外接盘备份，可删除对应中文目录。 |
| 2026-07-11 | 荣耀 X60 Pro 有线连接与备份准备 | `AI-archive/apps/android-platform-tools/`; `AI-archive/apps/honor-suite/`；各自 `INSTALL-NOTES.md` | 用户授权下载官方组件；本次申请网络访问权限获准 | 未改 PATH、环境变量、注册表、服务、计划任务、Windows 安全设置或手机设置 | 从 `dl.google.com` 下载 Android Platform Tools；从 `honor.com` 保存荣耀手机助理官方页面及安装程序 | Android 工具为便携版，删除其目录即可；荣耀手机助理尚未安装，安装程序的 Windows 签名读取结果为 `UnknownError`，将不运行，待接线后复核及用户确认。 |
| 2026-07-11 | 荣耀 X60 Pro 有线备份工具包 | `AI-archive/apps/honor-phone-backup-toolkit/`（只读检查、诊断报告脚本与说明） | 当前工作区写入权限；未申请额外权限 | 未改 PATH、环境变量、注册表、服务、计划任务、Windows 安全设置或手机设置；验证时 ADB 曾短暂启动本地调试服务后退出 | 无 | 删除该工具包目录即可；脚本不 Root、不修改手机，运行诊断报告前须由用户在手机端开启并确认 USB 调试。 |
| 2026-07-11 | 荣耀 X60 Pro 首次有线备份尝试 | `D:\手机备份\荣耀X60Pro_完整可见存储备份_2026-07-11_231250\BACKUP-STARTED.txt` | 用户明确授权向外接硬盘 D: 只复制手机内部存储可见文件；外部写入获准 | 无 | `D:\手机备份\` | Windows 的 MTP 后台复制无法启动，目录内仅有开始记录、未复制任何手机文件；保留记录以便追溯，后续需用已授权 ADB 进行可靠复制或在可见 Explorer 会话中复制。 |
| 2026-07-11 | 荣耀 X60 Pro 重要资料有线备份完成 | `D:\手机备份\荣耀X60Pro_重要资料备份_2026-07-11_232600\`（含 `DCIM`、`Pictures`、`Movies`、`Download`、`Documents` 与 `BACKUP-LOG.txt`） | 用户明确授权，使用其已确认的 USB 调试授权和外接硬盘 D: 写入权限 | 临时启用 USB 调试和 RSA 授权；未改 PATH、注册表、服务、计划任务、系统安全设置或手机文件 | `D:\手机备份\`；手机内部存储的五个只读源目录 | 只复制，未删除/移动/改写手机文件；已核对手机端与备份端文件数完全一致：18,704 个，约 125.25 GB。USB 调试可在备份完成后由用户自行关闭。 |
| 2026-07-12 | 荣耀 X60 Pro 录音与应用外部资料续备份 | 计划写入现有 `D:\手机备份\荣耀X60Pro_重要资料备份_2026-07-11_232600\`；`Sounds` 已完成，Telegram 外部资料传输中断 | 用户授权只复制录音及指定应用可见外部资料到 D: | 无系统/手机设置变更 | `D:\手机备份\`；`/sdcard/Sounds`；指定 `Android/data` 目录 | `Sounds` 已复制 57 个文件、22.42 GB。Telegram 约 74% 时出现本地写入 I/O 错误，随后 D: 盘符从系统消失；已停止，未删除/修改手机文件，需用户检查并恢复外接硬盘后再核验与续传。 |
| 2026-07-11 | 验证 Codex 按需管理员权限通道 | 临时创建并已删除 `AI-archive/tmp/admin-permission-check.ps1` 与检查结果 JSON | 用户批准一次沙箱外只读身份检查及 Windows UAC；验证获得当前账户的高完整性管理员令牌 | 未修改 UAC、PATH、环境变量、注册表、服务、计划任务或其他系统设置；管理员令牌仅用于本次检查，未常驻 | 只调用 Windows UAC 与本机 PowerShell；未写入归档目录之外 | 临时检查文件已删除；没有持久权限需要撤销。后续管理员动作仍需逐项 UAC。 |
| 2026-07-11 | AI 管理员控制中心安装申请 | 已在 `AI-archive/tmp/ai-admin-control-center/` 构建并测试安装候选；尚未复制到桌面、Program Files 或 ProgramData | 申请安装固定哈希执行器到 Program Files、建立受限 ACL 的 ProgramData 可信事务库；权限审查因需要用户对精确持久变更知情确认而拒绝 | 未修改 ACL、UAC、PATH、环境变量、注册表、服务、计划任务或防火墙；未产生持久系统变更 | 拟写但实际未写：`C:\Program Files\AI Admin Control Center\`、`C:\ProgramData\AI Admin Control Center\` | 当前无需系统清理；构建候选仍仅在 AI-archive 临时目录。用户明确批准两处持久变更后再安装。 |
| 2026-07-11 | 安装并端到端测试 AI 管理员控制中心 | 已安装旧版执行器哈希 `b0668d...68f8`；已创建 ProgramData 可信事务库；桌面成品已复制；专用测试事务 `7d01c0818fd442a2bb07a13adc510eb2` | 用户明确批准 Program Files 与 ProgramData 持久变更；初装 UAC 获准。后续申请用修复版哈希 `053767...33f8` 替换已安装提权执行器，被权限审查拒绝，等待精确更新批准 | 未改 UAC、PATH、环境变量、注册表、服务、计划任务或防火墙；ProgramData ACL 为 Administrators/SYSTEM 完全控制、当前用户只读。专用空测试目录当前仍保留测试添加的单对象 ACE | `C:\Program Files\AI Admin Control Center\`; `C:\ProgramData\AI Admin Control Center\`; `C:\Users\wardc\Desktop\Claude工作区\02_脚本与工具\AI管理员控制中心\` | 真实项目未改。待用户明确批准执行器二进制替换后，立即更新执行器并回滚 `data\e2e-acl-target`，验证恢复后删除测试目录。 |
| 2026-07-11 | 电脑其他个人文件完整备份 | `AI-archive/notes/2026-07-11_电脑个人文件完整备份说明.md`；D 盘完整备份目录及 7 份复制日志 | 用户授权提权读取桌面、文档、图片、视频、音乐、下载和微信资料，并写入外接硬盘 D: | 无 PATH、环境变量、注册表、服务、计划任务或应用设置变更 | `D:\中文分类备份_2026-07-08\08_电脑个人文件完整备份_2026-07-11\`；`D:\中文分类备份_2026-07-08\99_备份日志\2026-07-11_完整备份_*.log` | 只复制未删除源文件。已备份 74,291 个实体文件、约 34.9 GiB；WPS 云盘 2,096 个未落地占位文件约 2.55 GB 未能复制，需在 WPS 下载后补备。删除 D 盘对应完整备份目录即可移除本次副本。 |
| 2026-07-11 | 深度分类备份：创作、聊天办公、AI记录与软件配置 | 创建 `AI-archive/tmp/2026-07-11_深度分类备份.ps1`；尝试写入 D 盘深度分类目录 | 用户授权提权读取 AppData、AI 工具和软件配置目录并写入 D: | 无 PATH、环境变量、注册表、服务、计划任务或应用设置变更；排除浏览器凭据、Cookie、密码库、SSH 私钥、缓存和可重装程序 | `D:\中文分类备份_2026-07-08\09_深度资料与软件配置_2026-07-11\`；掉线前已复制 Adobe 动态图形模板 2,147 个文件约 3.75 GiB | D: 在任务中途掉线，任务自动结束；重新连接后用同一脚本增量续传，已完成文件会跳过。本机源文件未删除。 |
| 2026-07-11 | 深度分类备份断点续传完成 | `AI-archive/notes/2026-07-11_深度分类备份说明.md`；修正 `AI-archive/tmp/2026-07-11_深度分类备份.ps1` 结果输出；D 盘 5 个中文分类和 34 份日志 | 用户再次授权读取创作、聊天办公、AI记录及软件配置并写入恢复后的 D: | 无 PATH、环境变量、注册表、服务、计划任务或应用设置变更 | `D:\中文分类备份_2026-07-08\09_深度资料与软件配置_2026-07-11\`；`D:\中文分类备份_2026-07-08\99_备份日志\2026-07-11_深度分类备份\` | 已备份 21,580 个文件约 8.34 GiB。本机源文件未删除。WPS 一个正在占用的 16 MB 缓存数据库未复制；VS Code User 源目录不存在。 |
| 2026-07-11 | 创建“物理世界模型与交互设计开源前沿周报”Codex 自动化 | Codex 应用创建 `C:\Users\wardc\.codex\automations\automation-2\automation.toml` | 用户明确要求定期跟踪并汇报；未申请管理员权限 | 新增每周五 10:00（本机北京时间）运行的 ACTIVE 自动化；研究范围含主流期刊、会议与预印本，开源范围含 GitHub、Hugging Face、GitLab、npm 及官方项目站；目标项目为 `C:\Users\wardc\Documents\New project gpt` | `C:\Users\wardc\.codex\automations\automation-2\` | 在 Codex 自动化页面停用或删除“物理世界模型与交互设计开源前沿周报”；删除后确认对应 `automation-2` 目录已移除。 |
| 2026-07-12 | 为井邻海报添加微信二维码 | `AI-archive/outputs/井邻海报_已添加微信二维码.png`; `AI-archive/permissions-settings-log.md` | 仅使用当前工作区写入权限；未申请管理员、网络或额外文件权限 | 未改 PATH、环境变量、注册表、服务、计划任务或应用设置 | 只读访问 `C:\Users\wardc\Desktop\井邻海报.png` 与 `C:\Users\wardc\Desktop\微信图片_20260712201649_2423_6.jpg`；图像编辑工具按其固定机制在 `C:\Users\wardc\.codex\generated_images\019f564b-62e8-7333-a75a-74d462d6f65d\exec-2f681c25-3ef1-4f58-bf4b-6cb3b3ff549d.png` 创建了一份未采用预览 | 最终成品仅需删除对应 `AI-archive/outputs` 文件即可清理；外部预览未被采用且二维码验证失败，可在用户确认后删除，不影响成品。 |
| 2026-07-12 | 更新井邻海报完整标识并移除开放日/开放时间 | `AI-archive/outputs/井邻海报_二维码与完整标识版.png`; `AI-archive/tmp/井邻海报_完整标识与去日期_预览1.png`; `AI-archive/permissions-settings-log.md` | 仅使用当前工作区写入权限；未申请管理员、网络或额外文件权限 | 未改 PATH、环境变量、注册表、服务、计划任务或应用设置 | 只读访问 `C:\Users\wardc\Desktop\微信图片_20260712202040_2424_6.png`；图像编辑工具按固定机制在 `C:\Users\wardc\.codex\generated_images\019f564b-62e8-7333-a75a-74d462d6f65d\exec-2dd058c1-3313-4163-b5d0-237376977d2e.png` 创建了一份未采用预览 | 最终成品为非覆盖式新版本，上一版仍保留；如需清理，可删除本行列出的最终文件、临时预览及外部未采用预览，不涉及系统卸载。 |
| 2026-07-12 | 井邻海报地址更正与全量小字校样 | `AI-archive/outputs/井邻海报_文字校正版.png`; `AI-archive/tmp/poster_text_proof.ass`; `AI-archive/tmp/井邻海报_校样_*.png`; `AI-archive/tmp/井邻海报_全量文字校样_预览*.png`; `AI-archive/tmp/visual-text-audit/`; `AI-archive/permissions-settings-log.md` | 仅使用当前工作区写入权限；未申请管理员或系统级权限 | 未改 PATH、环境变量、注册表、服务、计划任务、字体或应用设置；使用已有系统字体进行像素级排印 | 只读核对北京市政务服务网与怀柔区政府公开页面中的“渤海镇洞台村”；图像编辑工具按固定机制在 `C:\Users\wardc\.codex\generated_images\019f564b-62e8-7333-a75a-74d462d6f65d\exec-8503876a-0e31-4306-abae-7420dc6fb412.png` 创建了一份未采用预览 | 最终成品为非覆盖式新版本；临时校样、ASS 排印文件、协作校样裁剪和外部未采用预览均可在用户确认后删除，不影响最终 PNG。 |
| 2026-07-13 | 确认井邻海报地址与微信信息最终版本 | `AI-archive/outputs/井邻海报_最终确认版.png`; `AI-archive/tmp/poster_contact_final.ass`; `AI-archive/tmp/井邻海报_微信行校正_预览.png`; `AI-archive/tmp/井邻海报_微信同电话校正_预览.png`; `AI-archive/permissions-settings-log.md` | 仅使用当前工作区写入权限；未申请管理员、网络或额外文件权限 | 未改 PATH、环境变量、注册表、服务、计划任务、字体或应用设置 | 图像编辑工具按固定机制在 `C:\Users\wardc\.codex\generated_images\019f564b-62e8-7333-a75a-74d462d6f65d\exec-aace9be8-277a-4564-9a56-b1e2d7472ca7.png` 创建了一份未采用预览 | 最终确认保留“北京市怀柔区渤海镇洞台村南屋78号”和“微信：2822175131（微信同电话）”；最终确认版与文字校正版像素一致。临时试排及外部预览可在用户确认后删除。 |
| 2026-07-16 | 创建“蔡浩文每日行动简报”Codex 自动化 | Codex 应用创建 `C:\Users\wardc\.codex\automations\automation-3\automation.toml`；更新 `AI-archive/permissions-settings-log.md` | 用户明确要求创建每日简报；未申请管理员权限或额外文件系统权限 | 新增每周一至周五 07:00（本机北京时间）运行的 ACTIVE 自动化；内容包括个性化新闻与政策分析、科技艺术与开源工具、Claude/ChatGPT 更新、北京可参与机会和个人行动建议；目标项目为 `C:\Users\wardc\Documents\New project gpt` | `C:\Users\wardc\.codex\automations\automation-3\` | 在 Codex 自动化页面暂停或删除“蔡浩文每日行动简报”；删除后可确认对应 `automation-3` 目录已移除。 |
| 2026-07-16 | 安装 Gemma 4 Heretic E2B 本地模型 | 创建 `AI-archive/apps/Gemma4-Heretic-E2B/`，包含 GGUF、`Modelfile`、`INSTALL-NOTES.md`；更新本日志 | 用户批准执行现有 Ollama、读取硬件/模型状态、联网从 Hugging Face 下载约 3.43 GB GGUF，并向 Ollama 数据目录导入模型；一次直接 HF 模型名拉取因名称过长返回 400，未产生下载 | Ollama 新增模型 `gemma4-heretic-e2b:q4km`；未改 PATH、永久环境变量、注册表、服务、计划任务或 Ollama 全局设置 | 执行 `C:\Users\wardc\AppData\Local\Programs\Ollama\ollama.exe`；联网访问 Hugging Face；`C:\Users\wardc\.ollama\models\` 新增模型清单和内容哈希为 `0f7af330...1217ebe3` 的数据块 | 先运行 `ollama rm gemma4-heretic-e2b:q4km`，确认未被其他模型复用的数据块已清除，再删除 `AI-archive/apps/Gemma4-Heretic-E2B/`；不要直接手工删除可能共享的 Ollama 数据块。 |

| 2026-07-17 | 生成“蔡浩文每日行动简报” | 更新 `C:\\Users\\wardc\\.codex\\automations\\automation-3\\memory.md`；更新本日志 | 使用既有自动化目录写入权限及联网检索；未请求管理员或额外系统权限 | 无 PATH、环境变量、注册表、服务、计划任务或应用设置变更 | `C:\\Users\\wardc\\.codex\\automations\\automation-3\\memory.md`（记录本次已核验信息，避免下次重复） | 如需清空自动化历史，可在停用/删除自动化后删除 `automation-3` 目录；不会影响系统设置。 |

## 2026-07-11 — PhotoGIMP / GIMP 3.0.8

- 权限/操作：联网下载官方 GIMP 与 PhotoGIMP；运行 GIMP 安装器；写入归档目录和用户配置；修改当前用户 PATH。
- 归档路径：`
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\PhotoGIMP
`。
- 外部路径：`%APPDATA%\GIMP\3.0`、`%APPDATA%\Microsoft\Windows\Start Menu\Programs\GIMP 3.0.8-2.lnk`。
- 环境变量：当前用户 PATH 追加 `
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\PhotoGIMP\cli
`。
- 清理方式：运行 `GIMP\uninst\unins000.exe`，删除上述 AppData 配置与快捷方式，从用户 PATH 移除 CLI 路径，再删除应用文件夹。
- 详细记录：`
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\PhotoGIMP\INSTALL-NOTES.md
`。

## 2026-07-12 — FFmpeg 8.1.2

- 权限/操作：联网读取 GitHub 发布信息，下载并解压 FFmpeg，写入归档目录，修改当前用户 PATH。
- 归档路径：`
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg
`。
- 环境变量：当前用户 PATH 追加 `
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin
`。
- 其他外部改动：无。
- 清理方式：从用户 PATH 移除上述目录，再删除应用文件夹。
- 详细记录：`
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\FFmpeg\INSTALL-NOTES.md
`。

## 2026-07-15 — 店铺评价照片优化

- 权限/操作：经用户授权，读取 `C:\Users\wardc\Desktop\店铺评价` 中的 7 张原图；复制其中 6 张到归档临时目录进行非覆盖式图像优化；将 6 张成片写回桌面原文件夹。
- 外部写入：`C:\Users\wardc\Desktop\店铺评价\01_优化版_店内服务.png` 至 `06_优化版_门店全景.png`。
- 归档临时路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\tmp\店铺评价原图`（6 张原图副本）。
- 设置变更：无；未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：如需撤销，删除桌面文件夹内 6 个带“优化版”的 PNG，并删除上述归档临时目录；原始 JPG 不受影响。

| 2026-07-18 | Codex电脑卡顿体检 | 只读访问沙箱外的用户临时目录与浏览器缓存目录，用于统计体积；未删除或修改缓存 | C:\Users\wardc\AppData\Local\Temp；Google\Chrome、Microsoft\Edge、Mozilla\Firefox、BraveSoftware 用户缓存目录 | 无需清理权限变更；本次只有读取。 |

| 2026-07-18 | Codex电脑清理 | 用户明确授权；Chrome 与 Edge 已退出后，删除其 Cache、Code Cache、GPUCache，未修改书签、密码、下载或历史记录 | C:\Users\wardc\AppData\Local\Google\Chrome\User Data\{Default,Profile 1,Profile 6,Profile 10}\{Cache,Code Cache,GPUCache}；C:\Users\wardc\AppData\Local\Microsoft\Edge\User Data\Default\{Cache,Code Cache,GPUCache} | 缓存不可恢复但浏览器会自动重建；如要还原内容不可行，仅可重新产生缓存。 |

| 2026-07-18 | Codex电脑清理 | 只读统计 Docker、Ollama、AdsPower 的应用数据目录，用于区分可重建缓存与不可删除的模型/资料 | C:\Users\wardc\.docker、.ollama；AppData 下 Docker、Ollama、AdsPower 目录 | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读细分 Docker、Ollama 与 AdsPower 的占用，防止把镜像、容器、模型或浏览器资料误作缓存删除 | 同上及 Program Files 中名称匹配 AdsPower/Ads 的目录 | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读细分 Docker 与 AdsPower 子目录，确定可安全清除的缓存边界 | Docker、adspower_global、adspower_global-updater 子目录 | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 用户授权；Docker 未运行时清除其运行日志，AdsPower 未运行时清除 Cache、Code Cache、GPUCache、Dawn 缓存；未触碰 Docker WSL 虚拟磁盘、Ollama 模型或 AdsPower cwd_global 浏览器资料 | C:\Users\wardc\AppData\Local\Docker\log；C:\Users\wardc\AppData\Roaming\adspower_global 的上述缓存目录 | 已永久删除可重建缓存；应用下次启动会自动生成。 |

| 2026-07-18 | Codex电脑清理 | 只读定位 ChatGPT 的启动登记和数据目录，以分离可清理缓存与自动登录资料 | ChatGPT 进程、Run 注册表项、AppData 中名称含 ChatGPT/OpenAI 的目录 | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读细分 ChatGPT 数据目录和 Windows 启动项，用于只清理缓存并确认自启动机制 | C:\Users\wardc\AppData\Local\OpenAI；Windows Start Apps | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读确认运行中的 Codex（ChatGPT）数据目录内可重建缓存的体积，并读取 MSIX 启动任务状态 | C:\Users\wardc\AppData\Local\OpenAI\Codex；当前用户 AppModel StartupTask 注册表项 | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读检查 OpenAI MSIX 包的缓存目录，以确认可清理项且避开登录资料 | C:\Users\wardc\AppData\Local\Packages\OpenAI.* | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 只读细分 OpenAI 应用 LocalCache 的一级内容，仅识别名称明确的浏览器缓存目录；不读取或修改登录资料 | 两个 OpenAI MSIX 包的 LocalCache | 未修改文件；仅读取。 |

| 2026-07-18 | Codex电脑清理 | 用户授权；旧版 ChatGPT 未运行时清除其 Cache、Code Cache、GPUCache、Dawn 缓存；保留 Local Storage、IndexedDB、Network、Preferences、Local State 与其他登录资料 | C:\Users\wardc\AppData\Local\Packages\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0\LocalCache\Roaming\ChatGPT 的上述缓存目录 | 已永久删除可重建缓存；旧版 ChatGPT 下次启动会自动重建，自动登录资料保留。 |

| 2026-07-18 | 检查 ChatGPT 官方更新 | 用户授权只读访问微软官方商店目录与包清单，并打开 Microsoft Store“更新和下载”页面；确认当前使用 OpenAI 新版 ChatGPT/Codex 桌面应用，版本 `OpenAI.Codex_26.715.2305.0`，商店显示 ChatGPT“今天更新”且无待更新项；未安装第三方客户端、未点击“全部更新” | 只读访问 `storeedgefd.dsx.mp.microsoft.com`；打开 Microsoft Store；商店按原有自动更新机制自行更新/下载 Start Experiences App、反馈中心、HEVC 视频扩展、Microsoft 365 Copilot 等微软应用 | 未改 PATH、环境变量、注册表、服务、计划任务或应用设置；ChatGPT 无需额外安装或卸载。微软应用更新如需回退须使用各应用自身/系统恢复机制。 |

| 2026-07-21 | 蔡浩文每日行动简报（automation-3） | 联网只读核验官方公告、政府页面、官方仓库与可靠媒体；按自动化要求更新运行记忆 | 写入 `C:\Users\wardc\.codex\automations\automation-3\memory.md`；未创建其他外部文件 | 无系统设置、环境变量、AppData、注册表、服务或计划任务变更；如需清除，仅删除该自动化记忆中本次运行条目。 |

- 2026-07-21：将 ChatGPT 生成的两张套色印刷 PNG 从 Downloads 复制到桌面并重命名为 $dst1、$dst2；未修改系统设置。清理方式：删除桌面上的这两个文件即可。

| 2026-07-21 | 12 秒丝网版画动画 9 个关键帧 | 用户明确要求在桌面新建文件夹；申请桌面写入权限，将 9 张生成图按时间顺序编号复制保存 | `C:\Users\wardc\Desktop\12秒丝网版画_9个关键帧_20260721`；生成源保留在 Codex 默认生成图目录 | 未改 PATH、环境变量、AppData、注册表、服务、计划任务或应用设置；如需撤销，删除该桌面文件夹即可，生成源不受影响。 |

| 2026-07-23 | Claude 资料归档 | 用户明确要求读取桌面 ZIP 与 Claude 工作区并整合到 AI-archive；复制原始 ZIP、解压 users.json，并复制工作区中源码/文档/图片/记录；跳过 .venv、node_modules、.git、.next、__pycache__、dist、build 等可重建目录；原文件保留 | C:\Users\wardc\Desktop\data-b1172d6e-5032-4fbc-9e89-e65c2c13a73c-1784750099-3994880f-batch-0000.zip；C:\Users\wardc\Desktop\Claude工作区；C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Claude工作区；C:\Users\wardc\Documents\New project gpt\AI-archive\notes\ChatGPT\Claude迁移_2026-07-23 | 未修改 PATH、环境变量、AppData、注册表、服务或计划任务；未删除桌面原件；撤销时可删除本次新增的 apps\\Claude工作区 与 notes\\ChatGPT\\Claude迁移_2026-07-23 |

## 2026-07-23 — WeFlow 6.1.0

- 权限/操作：用户明确要求部署最新版 WeFlow；获准联网访问官方 GitHub 与 Release 元数据、向统一归档目录写入、运行官方安装器、调用 Microsoft Defender 扫描、首次启动程序、创建并修正桌面/开始菜单快捷方式。
- 官方来源：`https://github.com/hicccc77/WeFlow`；发行仓库 `https://github.com/hicccc77/weflow-releases/releases/tag/v6.1.0`。核对时 `6.1.0` 为 Latest；官方频道说明 `6.2.0` 尚未发布。
- 归档路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\`；主体位于 `app\`；保留 `WeFlow-6.1.0-x64-Setup.exe` 和 `INSTALL-NOTES.md`。
- 完整性/验证：安装包 SHA-256 为 `4CA445B281917F9E067324EE38FBAF2959C1438885D61731EC0FE80345CA7070`，与 GitHub 官方资产元数据一致；安装包无 Authenticode 代码签名；Defender 扫描完整安装目录未发现威胁；安装器退出码 `0`；主程序版本 `6.1.0.0`，已实际启动并验证主窗口与归档路径。
- 外部写入：`C:\Users\wardc\Desktop\WeFlow.lnk`；`C:\Users\wardc\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\WeFlow.lnk`；`C:\Users\wardc\AppData\Roaming\WeFlow\`（首次启动配置、日志与缓存）；`C:\Users\wardc\AppData\Local\weflow-updater\installer.exe`（自动更新缓存）；Defender 本地扫描历史新增记录。
- 设置修正：安装器生成的快捷方式因受控安装环境把目标写成不存在的 `C:\Users\CodexSandboxOffline\...`，已将两个快捷方式改为由 `C:\Windows\explorer.exe` 携带真实 `WeFlow.exe` 路径启动，并验证成功。
- 未发生：未改 PATH、永久环境变量、注册表卸载项、服务、计划任务或防火墙；未安装全局包或公共依赖；未读取、上传或导出微信聊天数据。
- 清理方式：先退出 WeFlow，运行 `apps\WeFlow\app\Uninstall WeFlow.exe`；删除两个快捷方式；确认不再需要后删除 `%LOCALAPPDATA%\weflow-updater\`；备份所需配置/导出后再删除 `%APPDATA%\WeFlow\`；最后删除 `apps\WeFlow\`。详细步骤见 `apps\WeFlow\INSTALL-NOTES.md`。


## 2026-07-24 — 井邻乡村美育工作站桌面版

- 权限/操作：用户明确要求部署为桌面点击即用的独立窗口；写入统一归档目录并创建桌面快捷方式。
- 安装路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\井邻乡村美育工作站\`。
- 外部写入：`C:\Users\wardc\Desktop\井邻乡村美育工作站.lnk`。
- 运行依赖：复用已有 `C:\Program Files\nodejs\node.exe` 与 Microsoft Edge；未安装新依赖、全局包或浏览器扩展。
- 首次运行数据：应用目录内生成 `.browser-profile\`（独立浏览器配置、摄像头授权和缓存）；启动失败时生成 `launch-error.log`。
- 未发生：未修改 PATH、永久环境变量、注册表、服务、计划任务或防火墙。
- 清理方式：关闭应用窗口，删除桌面快捷方式，再删除整个应用安装目录；详细步骤见应用目录内 `INSTALL-NOTES.md`。


## 2026-07-24 — PowerShell 7.6.4（x64）

- 权限/操作：用户明确要求检查并安装最新 PowerShell 7；联网核对微软官方文档与 GitHub Latest Release，下载官方 x64 MSI，按官方公布值校验 SHA-256，并通过 Windows UAC 授权执行系统级安装。
- 官方来源：`https://github.com/PowerShell/PowerShell/releases/tag/v7.6.4`；安装包 SHA-256 为 `D11942DF52FD12470169797ABFA4781D9480EFDC81000BA4FA55A5B921ED8DD0`，与官方发行页一致。
- 归档路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\PowerShell\`；保留 `installer\PowerShell-7.6.4-win-x64.msi` 和 `INSTALL-NOTES.md`。
- 系统安装：`C:\Program Files\PowerShell\7\`；加入机器级 PATH；注册 Windows 事件清单；创建 `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\PowerShell\PowerShell 7 (x64).lnk`。
- 注册表/更新：写入 `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PowerShellCore\` 及 Windows Installer/卸载项；MSI 产品代码 `{92D9A5DC-8C64-40D5-B1BC-98DB9C7FDB7F}`；启用 PowerShell 通过 Microsoft Update 更新（`UseMU=1`、`EnableMU=1`）。
- 验证：`pwsh.exe` 实际启动成功，报告 `PSVersion 7.6.4`、`PSEdition Core`，测试命令返回预期结果；Windows PowerShell 5.1 保留并可并存。
- 未发生：未启用 PowerShell Remoting，未增加资源管理器右键菜单，未修改防火墙，未创建服务或计划任务，未安装全局包或其他公共依赖。
- 过程记录：首次参数传递错误返回 `1639`；修正后非管理员安装被拒并记录 `1925/1603`；两次均未完成安装。UAC 管理员安装最终退出码 `0`。Application/MsiInstaller 日志及 Windows Installer 受保护缓存可能保留相应系统记录。
- 清理方式：从“设置 → 应用 → 已安装的应用”卸载 `PowerShell 7-x64`，或管理员运行 `msiexec.exe /x "{92D9A5DC-8C64-40D5-B1BC-98DB9C7FDB7F}"`；由 MSI 清理程序目录、PATH、快捷方式及注册表登记。Microsoft Update 属公共设置，不应仅因卸载 PowerShell 而直接关闭。确认无残留且不需留档后再删除归档目录；详细步骤见 `apps\PowerShell\INSTALL-NOTES.md`。

## 2026-07-24 — 微信数据本地完整导出

- 权限/操作：用户明确要求把微信可导出的数据保存到桌面单独文件夹；通过 WeFlow 6.1.0 读取本机微信数据并启动四类可读导出，同时以只读复制方式备份新版与旧版微信原始数据。
- 外部写入：`C:\Users\wardc\Desktop\微信完整导出_2026-07-24\`，包含 `01_WeFlow可读导出`、`02_原始数据备份`、`03_说明与清单`。
- WeFlow 设置变更：导出路径改为 `C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出`；目录结构设为“C（按会话分目录）”；导出全部时间的详细 JSON，并包含图片、视频、语音、文件、表情包、联系人头像及已有语音转写；单文件上限设为软件允许的 4096 MB。
- 可读导出范围：私聊 3020 个会话、群聊 810 个会话、公众号 673 个会话、曾经的好友 86 个会话。
- 原始备份：`C:\Users\wardc\xwechat_files` 复制为 `02_原始数据备份\xwechat_files`，32886 个文件、14.950 GB、0 个失败项；`C:\Users\wardc\Documents\WeChat Files` 复制为 `02_原始数据备份\WeChat Files_旧版`，10292 个文件、4.025 GB、0 个失败项。复制未使用 `/MIR`，未删除或修改源文件。
- 隐私：全程仅在本机读写，未上传微信数据库、聊天记录、媒体或附件。
- 未发生：未修改 PATH、永久环境变量、注册表、服务、计划任务或防火墙。
- 清理方式：退出 WeFlow 并确认导出任务停止后，仅删除 `C:\Users\wardc\Desktop\微信完整导出_2026-07-24` 即可撤销本次桌面副本；不要删除两个微信源目录。若要恢复 WeFlow 导出路径，可在 WeFlow“导出”页面重新选择其他文件夹。


## 2026-07-24 — PAC 分流与 WebRTC 防泄露

- 术语修正：用户所说的“webftc”应为 WebRTC。PAC 不是完整 VPN；HTTP/HTTPS 及 `ws/wss` 通常遵循代理规则，但 WebRTC UDP/STUN 可能绕过 PAC。
- 检查结果：当前运行 `C:\Program Files (x86)\V\v2rayN.exe`，版本 `2.31`（2019/08/06）；现有 PAC 为 `http://127.0.0.1:1101/pac/?t=20260723193435046`，SOCKS5 `127.0.0.1:1099`，HTTP `127.0.0.1:1100`；3 个节点；未记录或外传服务器地址、UUID、订阅链接等敏感字段。
- 用户授权/系统修改：经 Windows UAC 授权写入 `HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Google\Chrome\WebRtcIPHandling=disable_non_proxied_udp` 和 `HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Edge\WebRtcLocalhostIpHandling=disable_non_proxied_udp`。
- 防火墙修改：创建并启用 7 条出站 UDP 阻断规则，固定名称前缀为 `AIArchive-WebRTC-UDP-`，目标分别为 Chrome、Edge、ChatGPT、Claude、Codex、豆包和 WeFlow；规则组为 `AI-archive WebRTC Leak Protection`。仅阻断这些应用的 UDP，未阻断 TCP，因此 HTTP/HTTPS/WebSocket 保持可用。
- 验证：两项浏览器策略均读取为 `disable_non_proxied_udp`；7 条规则均为 `Enabled=True`、`Outbound`、`Block`、`UDP`；PAC 本地请求返回 HTTP 200，1099/1100/1101 三个端口均在监听；现有 PAC URL 和 v2rayN 节点配置未改变。
- 可能影响：Chrome/Edge 的 QUIC/HTTP3 回退到 TCP；WebRTC 语音/视频可能稍慢，若应用没有 TCP/TURN 回退则可能无法通话；普通网页、文字聊天和 WebSocket 不受影响。
- 未发生：未升级 v2rayN，未改节点、订阅、远程 DNS、系统 PAC、全局环境变量、服务或计划任务；未访问第三方 IP/WebRTC 泄露测试网站，避免把真实 IP 和网络接口信息发送给第三方。
- 归档：`C:\Users\wardc\Documents\New project gpt\AI-archive\notes\network\PAC-WebRTC防泄露_2026-07-24\`，包含详细说明、应用脚本和回滚脚本。
- 清理方式：管理员运行归档内 `Remove-WebRTCLeakProtection.ps1`，删除本次 7 条固定名称防火墙规则和两个新增浏览器策略值；不触碰 v2rayN PAC、节点、订阅或其他防火墙规则。


## 2026-07-24 — 偏移四型 MediaPipe 双手交互 v2

- 权限/操作：为“偏移四型”独立交互 v2 联网安装固定版本 `@mediapipe/tasks-vision@0.10.35`，并从 Google MediaPipe 官方模型仓库下载 `hand_landmarker.task`；安装与模型均限制在本次项目文件夹内。
- 项目路径：`C:\Users\wardc\Documents\Codex\2026-07-24\referenced-chatgpt-conversation-this-is-untrusted\work\Offset-Four-Types-Mediapipe-v2\`；最终交付另存到本次 Codex `outputs` 和桌面独立文件夹。
- 依赖位置：项目内 `node_modules\@mediapipe\tasks-vision\`；固定版本 `0.10.35`；npm 使用 `--ignore-scripts`，审计为 `0 vulnerabilities`；缓存定向到项目内 `.npm-cache\`。
- 模型位置：项目内 `models\hand_landmarker.task`，大小 7,819,105 bytes；官方来源 `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`。
- 运行设置：仅启动临时本机 HTTP 服务 `127.0.0.1`；摄像头视频仅在浏览器本地由 MediaPipe 处理，不上传、不保存。
- 未发生：未安装全局 npm 包，未修改 PATH、永久环境变量、AppData 应用设置、注册表、服务、计划任务或防火墙。
- 清理方式：停止本地预览服务后删除 v2 项目及其桌面副本即可；没有公共依赖需要卸载。项目内详见 `DEPENDENCY-NOTES.md`。

## 2026-07-24 — 丝网版画“手掌改树”视觉重构

- 权限/操作：读取用户提供的临时 PNG，使用 Codex 内置图像编辑生成一版视觉重构，并将最终成品非覆盖式复制到统一归档目录；仅使用现有读取与工作区写入权限，未申请管理员、网络或额外文件权限。
- 最终成品：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网版画_手掌改树_视觉重构_v1.png`（1254×1254，SHA-256：`73B98EAF12BEA8103B69C4A1C2E0C1422F2616AAB70E2E174EE6F382B726A8B7`）。
- 外部位置：只读访问原图 `C:\Users\wardc\AppData\Local\Temp\codex-clipboard-62a4ac4e-e97e-48fb-8451-f93636ab2c13.png`；图像工具按固定机制在 `C:\Users\wardc\.codex\generated_images\019f9150-f9ef-7183-87f8-27e0398fb2cf\call_eRCg9g9KB3NP035Kg5gURTYl.png` 保留生成源。
- 未发生：未修改 PATH、环境变量、AppData 应用设置、注册表、服务、计划任务或系统设置；未覆盖用户原图。
- 清理方式：如需撤销，删除上述归档成品即可；生成源可在用户确认后删除，不影响归档成品。

## 2026-07-24 — “制版”8张网版成果复制到桌面

- 权限/操作：按用户明确要求，在桌面新建 `C:\Users\wardc\Desktop\制版\`，将“新主视觉·8张网版版本”的完整交付副本复制至该目录。
- 来源：`C:\Users\wardc\Documents\Codex\2026-07-24\mbti-silkscreen-separation\outputs\v2-new-main-8plates\`。
- 核对结果：源目录与桌面副本均为 15 个文件、4,532,820 bytes；逐文件 SHA-256 对比无差异。
- 未发生：未移动或删除工作区原件，未覆盖既有桌面目录，未安装依赖，未修改 PATH、环境变量、AppData 设置、注册表、服务或计划任务。
- 清理方式：如需撤销桌面副本，可删除 `C:\Users\wardc\Desktop\制版\`；工作区原件不受影响。


## 2026-07-24 — T恤丝网印刷 8 张位图整理

- 权限/操作：按用户明确要求读取桌面“制版”目录的 8 张阳片，并在桌面新建“位图”文件夹；按原编号 01–08 整理为 1-bit BMP。
- 来源：C:\Users\wardc\Desktop\制版\02-eight-plates\。
- 外部写入：C:\Users\wardc\Desktop\位图\，包含 8 张 BMP、印刷说明和 SHA-256 校验清单。
- 印刷尺寸：保持 3307 × 3552 px、300 dpi；完整画布约 280 × 300.7 mm，主体约 250 × 271 mm，适合成人 T 恤胸前印花；未做二次缩放，避免网点变形。
- 未发生：未覆盖或修改源文件，未安装依赖，未修改 PATH、环境变量、AppData 设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，仅删除 C:\Users\wardc\Desktop\位图\；源文件仍保留在“制版”目录。

## 2026-07-24 — “悲鸿”T恤小标位图

- 权限/操作：按用户明确要求读取桌面原图，并在桌面新建 `C:\Users\wardc\Desktop\悲鸿\`，生成四个配色的小标 PNG 和一张四版排版 PNG。
- 外部写入：`C:\Users\wardc\Desktop\悲鸿\`；文件均为 300 dpi PNG，单版约 7.6 × 6.5 cm，四版排版约 15.2 × 13.5 cm，均小于 A4。
- 未发生：未覆盖原图，未安装依赖，未修改 PATH、环境变量、AppData 设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，可删除 `C:\Users\wardc\Desktop\悲鸿\`；桌面原图 `微信图片_20260724073105_2988_329.jpg` 不受影响。

## 2026-07-24 — “悲鸿”菲林/硫酸纸黑白位图

- 权限/操作：按用户后续要求，将“悲鸿”小标转换为纯黑白 1-bit BMP，生成“字形黑字白底”与“原版高反差”两套各四版，并各生成一张四版排版图。
- 外部写入：`C:\Users\wardc\Desktop\悲鸿\`；共10个 BMP，300 dpi；单版约 7.6 × 6.4 cm，排版图约 15.2 × 13.5 cm。
- 验证：全部文件模式为 `1`（1-bit 黑白），无灰阶；原始彩色 PNG 与 JPG 未覆盖。
- 清理方式：如需撤销，仅删除 `C:\Users\wardc\Desktop\悲鸿\` 中以 `悲鸿_菲林_` 开头的 BMP 文件即可。

## 2026-07-24 — 自动化周报记忆记录

- 权限/操作：按自动化要求联网检索并写入自动化记忆文件。
- 外部写入：$memoryPath，用于下次按“自上次运行以来”去重。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData 设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，可删除 C:\Users\wardc\.codex\automations\automation-2\memory.md；不影响本次周报正文。

## 2026-07-24 — 自动化周报记忆记录更正

- 权限/操作：因当前 PowerShell 未设置 CODEX_HOME，改用实际 Codex 目录写入自动化记忆文件。
- 外部写入：$memoryPath，用于下次按“自上次运行以来”去重。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData 设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，可删除 C:\Users\wardc\.codex\automations\automation-2\memory.md；不影响本次周报正文。

## 2026-07-24 — 乡村民宿周边生活照片专业精修导出到桌面

- 权限/操作：按用户明确要求，将 5 张专业精修 JPEG 写入桌面。
- 外部写入：C:\Users\wardc\Desktop\乡村民宿周边生活_专业精修5张_2026-07-24\
- 处理内容：裁切构图、删减画面边缘人物/杂乱空间、调整曝光与色彩、局部提亮人物、轻度降噪与锐化。原始 CR2 未修改。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务、计划任务或应用设置。
- 清理方式：如需撤销，删除上述桌面文件夹即可；不会影响 D:\DCIM\100EOS5D 中的原片。

## 2026-07-24 — 无动作虚化极高水准照片导出到桌面

- 权限/操作：按用户要求重新选取主体更清楚的相邻原始帧，精修 5 张并写入桌面，同时附人物与画面分析。
- 外部写入：C:\Users\wardc\Desktop\乡村民宿周边生活_无动作虚化_极高水准5张_2026-07-24\
- 处理内容：淘汰虚化明显的 J18A1893、J18A1900、J18A1903；改用 J18A1875、J18A1879、J18A1884、J18A1891、J18A1901；执行专业裁切、曝光与色彩调整、人物区域提亮、色彩降噪和局部锐化。
- 保真说明：未使用生成式补脸、换脸或虚构人物纹理；原始 CR2 未修改。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务、计划任务或应用设置。
- 清理方式：如需撤销，删除上述桌面文件夹即可；不会影响 D:\DCIM\100EOS5D 中的原片。

## 2026-07-26 — 乡村美育工作站青年艺术家招募海报

- 权限/操作：两次申请文件写入权限。第一次仅授权尚未存在的目标子文件夹，Windows 无法创建；第二次将范围调整为其父级 `AI-archive\outputs`，成功创建本次归档子文件夹并复制最终文件。未读取、修改或覆盖 `outputs` 内其他项目。
- 统一归档：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\乡村美育工作站_艺术家招募海报\`。
- 最终文件：可编辑单页 A3 PowerPoint、可编辑 SVG、高清 PNG 预览、主视觉 PNG、海报修改说明，共 5 个文件；SVG 需与主视觉 PNG 保持在同一文件夹。
- 生成源：主视觉由 Codex 内置图像生成工具创建，原始生成文件保留于 `C:\Users\wardc\.codex\generated_images\019f9d8e-e9bb-7f93-8739-7aeea11ccf3e\call_nq8DdfC4cK0oJZV4x70nHagW.png`；项目副本位于本次 Codex 工作目录。
- 验证：PowerPoint 实际渲染通过，版面越界检查为 `No overflow detected`；SVG 已单独渲染核对，图片链接与中文字形显示正常。
- 未发生：未安装新依赖，未修改 PATH、环境变量、AppData 应用设置、注册表、服务、计划任务或系统网络设置；未删除或覆盖既有海报。
- 清理方式：如需撤销归档，仅删除上述“乡村美育工作站_艺术家招募海报”子文件夹即可；不会影响其他项目。Codex 生成源可在用户确认后另行删除。

## 2026-07-28 — 每日行动简报自动化记忆记录

- 权限/操作：按自动化要求联网检索，并读取、更新自动化去重记忆。
- 外部写入：`C:\Users\wardc\.codex\automations\automation-3\memory.md`，仅用于下一次“每日行动简报”的增量筛选。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData 应用设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，可删除该自动化记忆文件；不影响已发送的简报正文。

## 2026-07-30 — 丝网印刷工作坊 34 寸带鱼屏海报

- 权限/操作：读取用户指定的桌面竖版海报，使用 Codex 内置图像编辑工具重排为 34 英寸、3440 × 1440 的超宽屏展示版；按当前 Codex 项目交付规则将成品写入项目输出目录。
- 外部读取：`C:\Users\wardc\Desktop\微信图片_20260730223428_53_13.jpg`；源文件未修改。
- 外部写入：`C:\Users\wardc\Documents\Codex\2026-07-30\new-chat\outputs\`，包含 PNG 和 JPG 两个 3440 × 1440 成品。
- 生成缓存：`C:\Users\wardc\.codex\generated_images\019fb36f-a9e2-7413-91ef-d517bd677277\call_fcBeJ5UE1nw551sNG52WoTJU.png`；最终成品已复制到项目输出目录。
- 验证：两份成品均为 3440 × 1440；PNG 中使用原海报二维码本体替换生成版本，避免二维码内容被重绘；完成全图视觉检查。
- 未发生：未安装依赖，未修改 PATH、环境变量、AppData 应用设置、注册表、服务、计划任务或系统设置。
- 清理方式：如需撤销，可删除上述项目输出目录中的两份“丝网印刷工作坊_34寸带鱼屏_3440x1440”文件；桌面原图不受影响。Codex 生成缓存可在确认不再需要后删除。

## 2026-07-31 — Live Body X-Ray Volume Portable 部署与启动

- 权限/操作：用户授权读取微信文件目录中的项目压缩包、写入统一软件归档目录，并授权本回合网络访问，以验证本机页面及加载 MediaPipe 公开资源。
- 归档路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Live-Body-XRay-Volume-Portable\`；包含原项目文件、零依赖 `server.cjs`、改良后的 Windows 启动器和 `INSTALL-NOTES.md`。
- 外部只读来源：`C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\msg\file\2026-07\Live-Body-XRay-Volume-Portable(4).zip`；SHA-256 为 `8E8C14B8FD8DD99E1D9E8CABD24BED3B412B601B248679B9233F2E949A3CF235`，源文件未修改。
- 依赖与网络：复用现有 Node.js `v24.18.0`，未安装 Python、npm 包或其他依赖；页面会访问 jsDelivr 与 Google Storage 上的 MediaPipe 代码、WASM 和模型。浏览器可能按自身规则写入常规 AppData 缓存，本次未修改浏览器设置。
- 运行状态：普通 Node.js 进程在 `127.0.0.1:5188` 提供仅本机可访问的静态服务；本次验证 HTTP `200`、页面脚本执行成功且浏览器控制台无报错。未代用户接受摄像头权限。
- 未发生：未改 PATH、永久环境变量、AppData 应用设置、注册表、服务、计划任务、防火墙、开机启动或 Windows 摄像头设置。
- 清理方式：先关闭运行 `server.cjs` 的 Node.js 进程，再删除整个应用目录；无共享依赖需要卸载。浏览器缓存可能与其他网站共用，如需清理应从浏览器设置中按站点/缓存规则操作。

## 2026-07-31 — Windows 更新“需要注意”诊断

- 权限/操作：经用户要求检查 Windows 设置；申请并获准打开 `ms-settings:`，只读查看“Windows 更新”状态，并读取系统版本、系统盘可用空间及 Windows Update 相关服务状态。
- 诊断结果：当前实际为 Windows 11 家庭中文版 22H2（OS Build `22621.4317`；旧注册表字段仍显示 `Windows 10 Home China`），设置页明确提示“你的 Windows 版本已终止服务”；系统盘可用空间约 `74.7 GB`，`BITS`、`UsoSvc`、`wuauserv` 服务均在运行。
- 系统/设置变更：无；尚未点击“检查更新”，未下载、安装更新或重启电脑。
- 外部写入：无。
- 清理方式：本次只有只读诊断，无需清理；如继续升级，将另行记录下载、安装与重启结果。

## 2026-07-31 — BaiduPCS-Go v4.0.1 部署与百度网盘分享下载

- 权限/操作：按用户要求从 GitHub 官方 Release 下载并运行 BaiduPCS-Go Windows x64 便携版，用于转存并下载用户给定的百度网盘分享。
- 安装路径：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\BaiduPCS-Go\`；内含程序、原始发布包、进程级隔离启动脚本和 `INSTALL-NOTES.md`。
- 版本与校验：v4.0.1；发布包 SHA-256 为 `BB3BC2409E55820D681DAEF880A6949748FBC81D740952C2B2C05C28A075A4EE`；已验证主程序可启动并正确报告版本。
- 应用设置：仅启动进程设置 `BAIDUPCS_GO_CONFIG_DIR`，配置和登录会话保存在安装目录内的 `config\pcs_config.json`；未创建永久环境变量，未写入默认 `%APPDATA%\BaiduPCS-Go`。配置文件可能包含登录会话凭据，不应外发。
- 外部写入：创建 `C:\Users\wardc\Desktop\百度网盘照片\` 作为 6 个共享照片文件的下载目录，并将程序 `savedir` 指向该目录。
- 云端变更：执行下载时，`transfer` 会把分享内容转存到用户百度网盘当前目录；云端副本的具体目录和结果将在任务完成后补记。
- 未发生：未安装全局包，未修改 PATH、永久环境变量、注册表、服务、计划任务、防火墙或系统网络设置。
- 清理方式：退出 `BaiduPCS-Go.exe` 后删除整个安装目录即可卸载；桌面下载结果和百度网盘云端转存副本均属用户数据，不会自动删除，删除前需用户确认。
- 启动修正：首次生成的三个 `.cmd` 文件因 LF 换行被 Windows 命令解释器错误拆分；已改为 Windows 标准 CRLF，并复测启动脚本可正确调用 v4.0.1。此修正仅发生在应用安装目录内。

## 2026-07-31 — 小米盒子电脑投屏诊断与局域网遥控

- 权限/操作：按用户明确要求扫描本人局域网并尝试连接“客厅的小米盒子”；电脑位于 `CU_MUkH_5G`，盒子位于同一路由器的 `CU_MUkH`，确认盒子地址为 `192.168.1.5`。
- 设备控制：通过盒子公开的本地 Xiaomi RController 接口成功发送“主页”和“菜单”按键；未使用或保存用户提供的 Wi-Fi 密码。
- 服务变更：启动了原本停止的 Windows `upnphost`（UPnP Device Host）服务；其启动类型仍为“手动”，重启后可恢复为按需状态。`SSDPSRV` 原本已运行，未修改启动类型。
- 未成功的变更：尝试将 `CU_MUkH_5G` 从“公用网络”改为“专用网络”，因当前会话无管理员权限而失败，网络类别保持“公用”；`fdPHost`、`FDResPub`、`WFDSConMgrSvc` 也因权限不足未能手动启动。未修改防火墙规则、注册表、PATH、环境变量或计划任务。
- 阶段结果：首次尝试时盒子仅能通过 DLNA/UPnP 发现，尚未在盒子端开启 Miracast；Windows 添加设备/投屏操作曾被用户按 Esc 中止。
- 最终结果：用户在盒子端开启 Miracast 后，Windows 成功连接 `客厅的小米盒子_f1d0`；系统显示活动的 `Generic Monitor (Mi TV)`，Wi-Fi Direct 虚拟网卡已连接。随后通过系统自带 `DisplaySwitch.exe /clone` 将显示模式明确设为“复制”，复核为两块活动显示器、Mi TV 在线、Wi-Fi Direct 链路正常。
- 持久设置：Windows 会保留该无线显示设备的配对记录及最近使用的投影模式，方便下次连接；未安装软件或驱动，未新增防火墙规则。
- 清理方式：如需立即还原本次唯一成功的服务状态变更，可在管理员 PowerShell 执行 `Stop-Service upnphost`；也可保持“手动”启动类型并等待系统重启/按需回收。

## 2026-08-01 — 丝网印刷工作坊海报桌面副本

- 权限/操作：按用户明确要求，将本次生成的精简放大版海报复制到桌面并命名为 `1.png`。
- 外部写入：`C:\Users\wardc\Desktop\1.png`。
- 系统/设置变更：无；未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可直接删除桌面文件 `C:\Users\wardc\Desktop\1.png`；归档/工作区中的原始成果不受影响。

## 2026-08-01 — 现场照片主视觉海报桌面副本

- 权限/操作：按用户明确要求，将现场照片主视觉版海报复制到桌面并命名为 `2.png`。
- 外部写入：`C:\Users\wardc\Desktop\2.png`。
- 系统/设置变更：无；未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可直接删除桌面文件 `C:\Users\wardc\Desktop\2.png`；工作区中的原始成果不受影响。

## 2026-08-01 — 无边框海报 SVG 桌面文件

- 权限/操作：按用户明确要求，为全幅摄影海报增加日期 `2026年8月2日`，并保存为桌面 SVG 文件。
- 外部写入：`C:\Users\wardc\Desktop\3.svg`；为单文件 SVG，内嵌原海报位图，新增日期为 SVG 矢量文字。
- 技术说明：摄影底图及原海报文字保持为高分辨率嵌入位图，无法在不改变摄影观感的情况下无损转换为纯矢量路径；日期文字可缩放、可编辑。
- 系统/设置变更：无；未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可直接删除 `C:\Users\wardc\Desktop\3.svg`；工作区中的原始成果不受影响。

## 2026-08-01 — 丝网印刷工作坊海报添加日期

- 权限/操作：按用户要求编辑桌面来源海报，为版面加入日期“8月2日”，并保存最终成品。
- 来源读取：`C:\Users\wardc\Desktop\1.png`；未改写原文件。
- 外部写入：因 Codex 当前任务的成品输出规则，另存至 `C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-8月2日.png`；同时归档至 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊-8月2日.png`。
- 工具生成副本：图像编辑工具自动保留生成文件于 `C:\Users\wardc\.codex\generated_images\019fbb3e-32ca-7b00-ad80-1c3941b54aab\exec-ea96a7a1-33dc-4c54-aac7-dc4b77c8dd8e.png`。
- 系统/设置变更：无；未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可删除上述 Codex 任务输出、`.codex\generated_images` 工具副本及归档副本；桌面原图不受影响。

## 2026-08-01 — 精简版海报完整日期纯矢量 SVG

- 权限/操作：按用户明确要求，将精简放大版海报日期改为“2026年8月2日”，并生成纯路径 SVG 保存到桌面。
- 来源读取：`C:\Users\wardc\Documents\Codex\2026-08-01\new-chat\outputs\丝网印刷工作坊海报-精简放大版.png`；未改写源文件。
- 外部写入：`C:\Users\wardc\Desktop\丝网印刷工作坊-2026年8月2日-矢量.svg`；另存任务成品至 `C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日-矢量.svg`，并同步归档至 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊-2026年8月2日-矢量.svg`。
- 技术说明：成品不含 `<image>` 嵌入位图，也不依赖字体；海报和日期均已转换为矢量路径，共 11222 个路径，画布为 `1024 × 1536`。
- 系统/设置变更：无；复用本机现有 Python、vtracer 与 fontTools，未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可删除上述桌面、任务输出与归档中的 SVG；源 PNG 不受影响。

## 2026-08-01 — 完整日期海报 JPG 桌面副本

- 权限/操作：按用户明确要求，将“2026年8月2日”版本海报渲染为高质量 JPG 并保存到桌面。
- 来源读取：`C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日-矢量.svg`。
- 外部写入：`C:\Users\wardc\Desktop\丝网印刷工作坊-2026年8月2日.jpg`；另存任务成品至 `C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日.jpg`，并同步归档至 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊-2026年8月2日.jpg`。
- 质量信息：`1024 × 1536`、RGB、JPEG quality 96、4:4:4、300 DPI 标记；三个副本哈希一致。
- 校验修正：预览时发现刚生成的 SVG 标题属性存在转义引号兼容问题，错误 JPG 仅为临时中间结果；已修复并覆盖桌面、任务输出和归档中的同名 SVG/JPG，最终 SVG 通过 XML 解析，最终 JPG 已人工预览确认。
- 系统/设置变更：无；复用本机现有浏览器渲染与 Pillow，未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可删除上述桌面、任务输出与归档中的 JPG；SVG 与源 PNG 不受影响。

## 2026-08-01 — 小米盒子改名准备与投屏断开

- 权限/操作：按用户要求，准备将小米盒子设备名称修改为“井邻乡村美育工作站交互屋小米盒子”；确认 Windows 仍识别 `客厅的小米盒子_f1d0`，且当时 Miracast 显示器处于连接状态。
- 系统显示变更：调用 Windows 自带 `DisplaySwitch.exe /internal`，从无线显示“复制”切换为“仅电脑屏幕”，以便盒子退出投屏后重新连接家庭 Wi-Fi 并进入本机设置；复核活动显示器数量为 1。
- 当前状态：名称尚未修改；盒子仍停留在 Miracast 应用且未恢复家庭 Wi-Fi/局域网遥控接口，需要用户用实体遥控器按“主页”退出 Miracast 后才能继续。
- 未发生：未安装软件或驱动，未修改防火墙、PATH、环境变量、注册表、服务或计划任务。
- 清理/恢复方式：盒子重新开启 Miracast 后，在电脑按 `Win + K` 连接，再按 `Win + P` 选择“复制”即可恢复投屏。

## 2026-08-01 — 丝网印刷工作坊投屏版 JPG

- 权限/操作：按用户要求，将“2026年8月2日”海报改排为适合扩展屏/投屏观看的 16:9 横版 JPG。
- 来源读取：`C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日.jpg`；未改写源文件。
- 外部写入：`C:\Users\wardc\Desktop\丝网印刷工作坊-2026年8月2日-投屏版.jpg`；另存任务成品至 `C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日-投屏版.jpg`，并同步归档至 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊-2026年8月2日-投屏版.jpg`。
- 质量信息：`1920 × 1080`、RGB、JPEG quality 96、4:4:4、150 DPI 标记；已人工预览确认。
- 系统/设置变更：无；复用本机现有 Python 与 Pillow，未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可删除上述桌面、任务输出与归档中的投屏版 JPG；原竖版 JPG/SVG 不受影响。

## 2026-08-01 — spacedesk 双小米盒子扩展屏安装完成

- 用户授权：用户明确要求开始安装，使两台已接入同一无线网络的小米盒子同时成为 Windows 11 的扩展显示器。
- 设备发现：Windows 主机 WLAN 为 `192.168.1.6`（`CU_MUkH_5G`，Public）；发现盒子 `交互`（`192.168.1.5`）和 `客厅的小米盒子`（`192.168.1.8`），两台 TCP 6095 可用，TCP 5555/ADB 尚未开放。
- 外部下载/归档：从 spacedesk 官方下载 Windows 11 64 位驱动 2.2.28，从 Google 官方下载 Android Platform Tools 37.0.1，从 GitHub `EFForg/apkeep` 下载 apkeep 1.0.0，并准备 spacedesk Android Viewer 2.1.37 XAPK；全部保存于 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\` 对应软件文件夹，每个文件夹均有 `INSTALL-NOTES.md`。
- 管理员权限：安装 MSI 与收紧防火墙规则时分别触发 Windows UAC；用户已批准。
- Windows 系统改动：安装 `spacedesk Windows DRIVER 2.2.28.0` 到 `C:\Program Files\datronicsoft\spacedesk\`；新增自动服务 `spacedeskService`、驱动/PnP 设备 `spacedeskDriverAndroidControl` / `spacedeskDriverBus`；新增入站防火墙规则 `spacedeskService`；新增 MSI 卸载项 `{D59F844E-6F71-426A-BD6F-EA8E8CDA33FA}`。
- 安全收紧：安装器默认防火墙规则为所有配置文件/所有远端地址，已改为仅 Private、Public 配置文件且 `RemoteAddress=LocalSubnet`；服务当前监听 TCP 28252。
- 本地隔离依赖：Android Platform Tools 与 apkeep 均未加入 PATH；APK 校验使用 `spacedesk\tools\apk-verify-venv` 中的 Python venv 和 `androguard 4.1.4`，未改全局 Python。
- APK 校验：Viewer 包名 `ph.spacedesk.beta`，版本 2.1.37，最低 Android 5.0；全部拆分 APK 的 v1/v2/v3 签名一致，开发者证书 SHA-256 为 `69572E3752B733BFA907795B3ED4BF71394A759A34FA99F9936664F3EFAA8C48`，主体为 datronicsoft Inc。
- 盒子设置与授权：用户在两台 `MiBOX4C` 上开启开发者模式、ADB 调试和未知来源安装，并分别确认本电脑的 RSA 调试授权；盒子地址为 `192.168.1.5` 和 `192.168.1.8`。独立 ADB 私钥只保存在 `spacedesk\tools\adb-key\`，未写入默认 `.android` 目录。
- 盒子端安装：通过局域网 ADB 向两台盒子安装 `ph.spacedesk.beta` 2.1.37 的基础包、中文语言包和 xxhdpi 资源包，均返回 Success；未额外授予麦克风等运行时权限。
- 最终验证：两台盒子均自动发现并连接 Windows 主机 `192.168.1.6`；`spacedeskService` 同时存在来自 `192.168.1.5` 与 `192.168.1.8` 的已建立连接；Windows 生成两块在线虚拟显示器并切换为扩展模式。分别截取盒子画面确认两台显示桌面的不同区域，不是镜像复制。
- 临时验证文件：`C:\Users\wardc\Documents\New project gpt\AI-archive\tmp\spacedesk-boxes\` 保存安装与扩展屏画面核验截图/UI 状态；盒子 `/sdcard` 中本次创建的临时截图和 XML 已清理。本机 ADB 会话已断开并停止。
- 当前状态：两台小米盒子已经同时作为两个独立 Windows 扩展屏运行；日常 Viewer 连接不需要 ADB。为减少局域网调试暴露，用户应在两台盒子上关闭 ADB 调试与未知来源安装权限。
- 清理/恢复：优先用 `MsiExec.exe /X{D59F844E-6F71-426A-BD6F-EA8E8CDA33FA}` 卸载 spacedesk 并重启；复核服务、驱动、PnP 设备、防火墙规则与 Program Files 目录均已移除；盒子端需分别卸载 Viewer、关闭 ADB 调试并撤销授权；最后按各 `INSTALL-NOTES.md` 删除归档辅助工具。

## 2026-08-01 — 丝网印刷工作坊投屏重新设计版 JPG

- 权限/操作：根据用户反馈，不再采用“左侧竖版海报 + 右侧补充文字”的展示方式，而是重新设计 16:9 投屏主视觉版。
- 来源读取：`C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日.jpg`；抽取其中红色丝印图案作为横版主视觉元素，未改写源文件。
- 外部写入：`C:\Users\wardc\Desktop\丝网印刷工作坊-2026年8月2日-投屏重新设计版.jpg`；另存任务成品至 `C:\Users\wardc\Documents\Codex\2026-08-01\8\outputs\丝网印刷工作坊-2026年8月2日-投屏重新设计版.jpg`，并同步归档至 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊-2026年8月2日-投屏重新设计版.jpg`。
- 质量信息：`1920 × 1080`、RGB、JPEG quality 96、4:4:4、150 DPI 标记；已人工预览确认。
- 系统/设置变更：无；复用本机现有 Python 与 Pillow，未安装依赖，未修改 PATH、环境变量、AppData、注册表、服务或计划任务。
- 清理方式：确认不再需要后，可删除上述桌面、任务输出与归档中的重新设计版 JPG；原竖版 JPG/SVG 与上一版投屏 JPG 不受影响。

## 2026-08-01 — 小米盒子固定投放防熄屏设置

- 权限/操作：按用户要求，为当前 Windows 11 到小米盒子的 Miracast 复制投屏设置持续显示。
- 排查结果：当前“平衡”电源计划中，接通电源时的关闭显示器和睡眠时间原本均为“永不”；电池模式下两项原本均为 180 秒（3 分钟）。Windows 屏幕保护程序已经关闭，无需修改。
- 系统设置变更：将当前电源计划的电池模式“在此时间后关闭显示”和“在此时间后睡眠”均改为 0（永不），并重新应用当前电源计划；随后使用 Windows 自带 `DisplaySwitch.exe /clone` 重新锁定复制投屏。
- 验证：接通电源与电池模式的显示关闭、睡眠超时均为 0；系统当前识别到 2 个活动显示设备。
- 影响：电脑未接电源时也会持续亮屏和运行，会增加耗电并可能耗尽电池；长期固定投放建议保持电脑接通电源。
- 未发生：未安装软件或驱动，未修改 PATH、环境变量、防火墙、AppData、注册表、服务或计划任务。
- 清理/恢复方式：如需恢复原来的电池模式 3 分钟超时，可运行 `powercfg /change monitor-timeout-dc 3` 和 `powercfg /change standby-timeout-dc 3`，或在“设置 → 系统 → 电源和电池 → 屏幕、睡眠和休眠超时”中调整。

## 2026-08-02 — 两台小米盒子同步全屏展示丝网印刷海报

- 用户授权：用户要求继续通过后台代码，把指定海报同时投放到两台已安装 spacedesk 的小米盒子显示屏。
- 来源读取：`C:\Users\wardc\Desktop\exec-a40272e1-be95-4f7c-9b97-a329a4f2ff88.png`；源文件未修改。
- 盒子控制：复用既有归档 ADB 工具和授权密钥，唤醒 `192.168.1.5`、`192.168.1.8` 并启动 spacedesk Viewer；两台均连接 Windows 主机 `192.168.1.6`。完成后已终止本机 ADB 进程，spacedesk 连接保持正常。
- 新增文件：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\spacedesk\tools\Show-DualPoster.ps1`；提供两个无边框、置顶、等比例缩放的海报窗口。
- 运行状态：隐藏后台 PowerShell 进程启动时 PID 为 `23348`；窗口分别位于 `DISPLAY5`（1920,0，1920×1080）与 `DISPLAY6`（3840,0，1920×1080），电脑主屏 `DISPLAY1` 不被覆盖。
- 掉线保护：非主屏少于两块时自动隐藏海报窗口，恢复两块后自动归位；按海报窗口的 `Esc` 可结束展示。没有设置开机启动、计划任务、注册表、PATH、环境变量、防火墙或额外服务。
- 临时核验：`AI-archive\tmp\spacedesk-boxes\` 中保留本次盒子连接界面和核验文件；两次盒子端画面抓取因超时留下 0 字节本地临时文件，不影响展示。
- 清理方式：先按 `Esc` 结束双屏展示，再按需删除脚本和临时核验文件；关闭 spacedesk Viewer 即可断开对应盒子，源海报不受影响。

## 2026-08-02 — 扩展屏壁纸后台等待投放

- 权限/操作：按用户要求以后台方式等待扩展屏重新连接；检测到第二屏后，自动在第二屏全屏显示 `扩展屏壁纸-1536x864.jpg`，按 `Esc` 可退出。
- 外部写入：无新增桌面文件；后台脚本位于 `C:\Users\wardc\Documents\Codex\2026-08-01\new-chat\work\watch-extended-wallpaper.ps1`。
- 当前状态：后台 PowerShell 进程已启动，轮询显示器状态；启动时系统仍仅识别主屏 `1536×864`，因此正在等待第二屏。
- 系统/设置变更：无；未修改显示模式、电源计划、PATH、环境变量、注册表、服务或计划任务。
- 清理方式：按 `Esc` 关闭投放窗口；若扩展屏尚未连接，可结束该后台 PowerShell 进程或重启电脑自动清理。

## 2026-08-02 — Claude Code 与 WeFlow 接入 MiMo Token Plan

- 用户授权：用户明确要求将 MiMo Token Plan 接入 Claude Code，并同步配置 WeFlow。
- Claude Code：确认现有 `C:\Users\wardc\.claude\settings.json` 与用户级环境变量已指向 MiMo Anthropic 兼容接口，模型为 `mimo-v2.5-pro`；未重复改写凭据。
- WeFlow：在 `C:\Users\wardc\AppData\Roaming\weflow\WeFlow-config.json` 对应的应用设置中新增 MiMo Token Plan 模型配置，使用 OpenAI Compatible 协议，模型为 `mimo-v2.5-pro`；API Key 由 WeFlow 应用安全存储，不在记录中明文保存。
- 验证：WeFlow 连接测试返回“连接成功，模型回复：连接成功”，并在界面切换为当前配置。
- 外部写入/设置：修改了 WeFlow 用户级设置目录 AppData；未修改 PATH、系统环境变量、注册表、服务、计划任务。
- 清理方式：在 Claude Code 删除或改回 `C:\Users\wardc\.claude\settings.json` 中的 MiMo 相关设置；在 WeFlow 的“设置 → AI 设置 → 基础配置”删除 MiMo Token Plan 配置或切回原配置；公共依赖无需清理。

## 2026-08-02 — WeFlow 私聊 MiMo 分析框架

- 用户授权：用户要求读取已导出的 WeFlow 私聊数据，并通过 Claude Code 的小米 MiMo Token Plan 建立高效分析与理解框架。
- 新建项目：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\`；包含清洗、分段、SQLite FTS5 检索、结构化 MiMo 标注、报告和测试。
- 外部只读来源：扫描 `C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出\` 中的私聊详细 JSON；未修改、移动或删除桌面导出和微信原始数据。
- 本地派生数据：读取 725 个有效私聊 JSON、71,550 条消息，生成 6,303 个对话片段和 71,550 条全文索引；当前数据库为项目内 `data\wechat-private-v2.sqlite3`。
- MiMo 外部传输：通过现有 Claude Code 用户配置调用 `mimo-v2.5-pro`，无隐私接口测试及 3 个真实对话片段试标注成功。模型输入默认匿名化联系人，并脱敏常见手机号、邮箱、身份证号、银行卡号和 IP；Token 未写入项目。
- 依赖/系统设置：复用现有 Python 3.12、SQLite FTS5 和 Claude Code；未安装新包，未修改 PATH、环境变量、注册表、服务、计划任务或防火墙。
- 调试派生文件：首次不完整索引已移动到项目内 `data\obsolete\wechat-private-initial-obsolete.sqlite3`，原始数据不受影响。
- 清理方式：删除整个 `WeChat-MiMo-Analyzer` 项目目录即可移除框架、派生索引、标注和报告；不会卸载 WeFlow/Claude Code，也不会删除桌面导出或微信原始数据。

## 2026-08-02 — 多轮分析与数字分身设计文档（仅设计）

- 用户更正范围：明确要求只生成方案框架和成熟案例比较，交给 Claude Code/MiMo 以后使用；本阶段不得继续运行聊天分析。
- 新增交付文件：`C:\Users\wardc\Documents\Codex\2026-08-02\claude-code-mimo-token-plan\outputs\01-方案比较与决策书.md`、`02-Claude-Code-MiMo-多轮分析任务书.md`、`03-三位一体融合实施蓝图.md`。
- 路径原因：Codex 当前任务的用户交付文件按应用要求保存在该任务 `outputs` 目录；未写入微信或 WeFlow 数据目录。
- 数据与接口：本阶段没有读取聊天正文、没有调用 MiMo 分析、没有生成真实联系人画像、没有发送消息、没有部署数字人；只进行了公开资料调研并创建设计文档。
- 系统设置：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务、防火墙或 WeFlow/Claude Code 配置。
- 设计假设更新：用户确认后续执行可分析全部私聊正文、保留联系人姓名并提交给 MiMo，不做脱敏，也不把隐私风险作为数据裁剪条件；当前仍仅修改设计文档，没有启动分析。自动发送、声音克隆和公开数字分身继续作为独立功能开关。
- 路线确认：用户选择个人记忆系统、沟通改善、数字分身三个方向融合；框架采用个人记忆系统为统一底座，沟通教练与数字分身共用证据链、记忆库和纠错反馈，不建立三套互相冲突的画像。
- 到期冲刺文档：因用户说明 MiMo Token Plan 当天到期，新增 `C:\Users\wardc\Documents\Codex\2026-08-02\claude-code-mimo-token-plan\outputs\04-Token今日到期冲刺执行方案.md`，提供 P0—P5 优先级、动态并发、断点续跑、落盘资产和可直接交给 Claude Code 的 `EXPIRY_HARVEST` 指令；本次仅生成方案，没有在 Codex 中启动该指令或调用 MiMo。
- 最激进补丁：按用户要求新增 `05-最激进到期冲刺补丁.md`（动态高并发、流水线重叠、多视角和扩展语料）及 `06-最激进分析判断补丁.md`（深层自我、关系动力、社交网络、盲点矛盾、条件预测、人格法庭和数字分身多版本）。用户随后澄清“激进”重点是分析判断方向，因此 `06` 强制大胆结论同时附带证据、反证、替代解释和置信度；仍未在 Codex 中运行真实聊天分析。
- 无上限标注优先：用户进一步指定先对全部聊天做无项目预算上限的细粒度标注理解，再进入深层判断。新增 `07-无上限全量标注理解优先补丁.md`，定义消息、片段、实体事件、语义深描、独立复标裁判和全局回扫六轮，目标覆盖 725 个私聊、71,550 条消息和 6,303 个片段；本次只生成 Claude Code 指令，未在 Codex 中启动标注或调用 MiMo。
- 一键完整总流程：按用户要求把 04—07 的到期冲刺、吞吐、无上限标注、个人记忆、深层判断、沟通改善、数字分身、审计、界面和增量更新整合为 `08-Claude-Code-MiMo一键完整总流程.md`；包含可直接交给 Claude Code 的单一总指令和完整验收清单。本次未执行该总指令。
- 清理方式：删除上述两个 Markdown 文件即可；不会影响既有分析项目、WeFlow 导出、Claude Code 或 MiMo 配置。

## 2026-08-02 — Codex 桌面端接入 Xiaomi MiMo Token Plan

- 用户授权：用户明确要求将已购买的 MiMo Token Plan 直接接入当前 Codex 界面。
- Codex 配置：修改 `C:\Users\wardc\.codex\config.toml`，默认模型切换为 `mimo-v2.5-pro`，新增自定义供应商 `mimo`，使用中国集群 Responses API `https://token-plan-cn.xiaomimimo.com/v1`；密钥仅通过 `MIMO_API_KEY` 环境变量读取，未明文写入配置文件或本日志。
- 模型目录：新建 `C:\Users\wardc\.codex\model-catalogs\model-catalogs.json`，登记 `mimo-v2.5-pro` 与 `mimo-v2.5` 的上下文、推理档位、输入模态和工具能力；按 MiMo 官方兼容要求关闭 Codex 内置 `web_search`，避免向网关发送不受支持的服务端搜索工具。浏览器、Computer Use 与 MCP 插件配置未删除。
- 用户级设置：新增 Windows 用户环境变量 `MIMO_API_KEY`（值复用本机既有 Claude Code Token Plan 凭证，未修改系统级环境变量或 PATH）。清理方式：在 PowerShell 执行 `[Environment]::SetEnvironmentVariable('MIMO_API_KEY',$null,'User')`，再重启 Codex。
- 备份：修改前配置完整备份至 `C:\Users\wardc\Documents\New project gpt\AI-archive\notes\codex-mimo\config-pre-mimo-20260802-234543.toml`；恢复时关闭 Codex，用该文件覆盖 `C:\Users\wardc\.codex\config.toml`，并按上一项移除环境变量。
- 验证：Token Plan `/v1/responses` 请求成功并返回 `mimo-v2.5-pro`；Codex `exec` 端到端文本请求成功；只读 Shell 工具调用成功；不再出现未知模型或不支持 `web_search` 的错误。
- 依赖与系统范围：未安装新软件或全局包，未改 PATH、系统环境变量、服务、计划任务、防火墙或 AppData 应用设置。

## 2026-08-03 — 井邻乡村美育工作站历史海报桌面整理

- 用户授权：用户明确要求查找此前已创建、完成度较高的井邻乡村美育工作站海报，在桌面新建文件夹并保存 JPG 版本；没有重新生成海报。
- 桌面写入：新建 `C:\Users\wardc\Desktop\井邻乡村美育工作站_成熟海报_JPG\`，保存 5 张筛选后的高质量 JPG：标准确认版、精简放大版、现场摄影版、全幅摄影版、光谱配色版。
- 只读来源：从既有 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\` 和 `C:\Users\wardc\Documents\Codex\2026-08-01\new-chat\outputs\` 中读取 PNG 成品；未移动、覆盖或修改原始文件。
- 筛选与转换：排除含“待定、待替换、示例电话”等占位信息的草稿；按原像素尺寸转换为 JPEG，质量 96、4:4:4 色度采样，并逐张完成视觉检查。
- 依赖/系统设置：复用本机现有 Python 3.12 与 Pillow 12.2.0；未安装依赖，未改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，删除桌面文件夹 `C:\Users\wardc\Desktop\井邻乡村美育工作站_成熟海报_JPG\` 即可；历史原图仍保留在上述来源目录。

## 2026-08-05 — Claude Code 新 API 令牌接入尝试

- 用户授权：用户要求将 Claude Code 的 API 认证令牌替换为其提供的新令牌；令牌未在本日志中明文记录。
- 外部写入：曾修改 `C:\Users\wardc\.claude\settings.json` 的 `ANTHROPIC_AUTH_TOKEN`，并修改 Windows 用户级环境变量 `ANTHROPIC_AUTH_TOKEN`；未修改 PATH、系统环境变量、注册表、服务或计划任务。
- 备份：修改前配置备份至 `C:\Users\wardc\Documents\New project gpt\AI-archive\notes\claudecode-api\settings-pre-key-change-20260805-153442.json`。
- 验证：使用原有 `https://token-plan-cn.xiaomimimo.com/anthropic` 与 `mimo-v2.5-pro` 发起最小兼容性请求，返回 HTTP 401；判断新令牌不能直接用于当前地址，尚缺新 API 的 Base URL/服务商信息。
- 当前状态：为避免 Claude Code 进入不可用状态，已恢复原 `settings.json` 和原用户级 `ANTHROPIC_AUTH_TOKEN`；新令牌未继续保留在配置中。
- 清理方式：删除上述备份文件即可清理本次尝试产生的备份；若后续获得新 API 地址，重新修改配置后需同步更新本节。

## 2026-08-05 — Claude Code 接入 DeepSeek Anthropic API

- 用户授权：用户确认新令牌属于 DeepSeek，并要求接入 Claude Code。
- Claude Code 配置：将 `C:\Users\wardc\.claude\settings.json` 的 API 地址改为 `https://api.deepseek.com/anthropic`；主模型为 `deepseek-v4-pro[1m]`，轻量模型和子代理模型为 `deepseek-v4-flash`。令牌未在本日志中明文记录。
- 用户级设置：同步修改 Windows 用户级 `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL`、三个默认模型变量和 `CLAUDE_CODE_SUBAGENT_MODEL`；未修改 `MIMO_API_KEY` 或 Codex 独立配置。
- 备份：修改前配置备份至 `C:\Users\wardc\Documents\New project gpt\AI-archive\notes\claudecode-api\settings-pre-deepseek-20260805-153628.json`。
- 验证：DeepSeek Anthropic `/v1/messages` 请求返回 HTTP 200；Claude Code `2.1.220` 端到端执行测试成功返回 `OK`。
- 清理方式：关闭 Claude Code 后，用上述备份恢复 `C:\Users\wardc\.claude\settings.json`，并删除或恢复本节列出的用户级环境变量；备份文件可直接删除。

## 2026-08-05 — 微信聊天记录清理流程与成果桌面归档

- 用户授权：用户要求把已找到的微信聊天数据清理流程、脚本、报告、人物画像结果和历史记录集中整理到桌面文件夹。
- 桌面写入：新建 `C:\Users\wardc\Desktop\微信聊天记录清理`，采用复制归档方式，保留原项目和原始数据不变；加入 WeFlow 原始导出后共约 71,969 个文件、约 33.7 GB。
- 复制内容：主项目数据库及其 `-wal/-shm` 伴随文件、报告、执行器、Layer 2 结果、断点、第二套工作流、Claude Code + MiMo 规划文档、Grok 审计材料、人工报告/标注、相关 Codex/Claude 历史索引，以及完整 WeFlow 原始导出。
- 原始 WeFlow 导出已复制到 `C:\Users\wardc\Desktop\微信聊天记录清理\07_WeFlow原始导出_2026-07-24`；实际核对为 71,848 个文件、约 33.57 GB；随后按用户授权删除原始目录。当前用户回收站未找到对应条目，恢复性不确定。
- 有意未复制：主项目中含明文 MiMo 凭据的 `src\contact_analyzer.py`（桌面归档只放脱敏安全模板）。
- 安全处理：未在日志、清单或归档中记录任何真实 Token；归档附带 `contact_analyzer.py.SECURITY-TEMPLATE.py`，提示使用环境变量并轮换旧凭据。
- 归档阶段系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；当时没有删除、移动或覆盖原始文件。后续原始 WeFlow 导出送入回收站的操作记录见下一节。
- 清理方式：如不再需要桌面副本，可删除 `C:\Users\wardc\Desktop\微信聊天记录清理`；已迁移源文件的主数据库和报告副本已按下一节清理，主项目中未迁移文件仍保留。因该文件夹含约 33.7GB 私人聊天资料，删除或外发前应再次确认。

## 2026-08-05 — 清理已迁移的 WeFlow 分析源文件

- 用户授权：用户明确要求清理已经导入桌面归档的 WeFlow 已处理聊天分析、流程和结果源文件，但不要触碰未被 WeFlow 破解的微信本机原始数据。
- 精确删除：删除前逐文件比对桌面归档副本的大小和 SHA-256；共删除 116 个已迁移源文件/空的源目录，包含主项目中已复制的数据库、报告、脚本、断点，第二套工作流源目录，Claude Code + MiMo 规划源目录，以及 5 个独立报告/历史文件。
- 保留：主项目中未迁移的 359 个文件（约 113 MB）保留，包括未复制的 `src\contact_analyzer.py`、其他未归档脚本、依赖和旧文件；没有按目录整体删除主项目。
- 未触碰：`C:\Users\wardc\xwechat_files`（约 15.99 GB）和 `C:\Users\wardc\Documents\WeChat Files`（约 4.03 GB）仍保留；桌面归档中的完整 WeFlow 副本和主数据库仍保留。
- 独立源文件：`C:\Users\wardc\Desktop\Claude工作区\微信数据人物画像分析.md`、`03_文档与说明\克隆人数据标注框架.md`、Grok 测试结果、指定 Codex/Claude 历史文件均已核对后清理。
- 系统范围：没有修改 PATH、环境变量、注册表、服务或计划任务；未清理未被 WeFlow 破解的微信原始目录。
## 2026-08-05 — 原始 WeFlow 导出清理

- 用户授权：用户明确要求删除已经复制到桌面归档的原始 WeFlow 导出。
- 删除目标：`C:\Users\wardc\Desktop\微信完整导出_2026-07-24`；删除前已核对归档副本存在、主数据库校验文件存在，且此前源/目标均为 71,848 个文件、约 33.57 GB。
- 执行方式：调用 Windows 回收站删除方式；删除后原始路径不存在，但当前用户回收站未找到对应条目，不能保证恢复；桌面归档副本仍存在。
- 恢复方式：当前用户回收站未找到该目录，因此不能保证可恢复；如需取回，只能检查其他用户回收站、备份或磁盘恢复工具。
- 系统范围：未删除 `微信聊天记录清理` 桌面归档、主分析项目或数据库；没有修改 PATH、环境变量、注册表、服务或计划任务。

## 2026-08-05 — Claude Code + DeepSeek v3 微信分析试运行工作区

- 用户授权：用户要求使用已配置 DeepSeek API 的 Claude Code 开始微信聊天分析，并打开可见窗口以便调试修改。
- 桌面写入：创建 `C:\Users\wardc\Desktop\微信聊天记录清理\10_DeepSeek-v3分析工作区`，包含隔离数据库副本、安全边界、启动任务和可见 PowerShell 启动脚本。
- 数据安全：从桌面主归档数据库复制 `wechat-analysis-v3.sqlite3`，复制后大小和 SHA-256 与源数据库一致；旧数据库和原始 WeFlow 导出不写入、不删除。
- 外部调用范围：Claude Code 使用现有 `https://api.deepseek.com/anthropic` 配置和 `deepseek-v4-flash`；本次任务最多运行 20 个分层抽样片段，之后暂停等待用户确认是否扩大规模。Token 未写入本日志或工作区。
- 系统范围：未修改 PATH、注册表、服务、计划任务或 Claude 全局设置；仅启动一个用户可见的 PowerShell/Claude Code 窗口。
- 清理方式：先关闭 Claude/PowerShell 窗口，再删除 `C:\Users\wardc\Desktop\微信聊天记录清理\10_DeepSeek-v3分析工作区`。如需保留试运行成果，只删除其中的启动脚本即可。

## 2026-08-05 — Codex 接入 DeepSeek API 的 LiteLLM 桥接

- 用户授权：用户要求在当前 Codex 中增加 DeepSeek API，同时保留 GPT-5.6 和全部现有聊天/工作记录。
- 归档安装：LiteLLM `1.95.0` 及代理依赖隔离安装到 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\LiteLLM-DeepSeek-Bridge\venv`；没有全局安装 Python/Node 包，也没有使用 Docker 服务。
- 外部配置：新增 Windows 用户级 `DEEPSEEK_API_KEY` 别名，复用既有用户级 DeepSeek 凭证；新增随机的 `CODEX_DEEPSEEK_BRIDGE_KEY` 作为本机桥接认证。真实值未写入日志、配置或安装记录。
- Codex 配置：修改 `C:\Users\wardc\.codex\config.toml`，仅追加 `deepseek-via-litellm` Provider，指向 `http://127.0.0.1:4000/v1`，使用 Responses API；默认模型仍为 `gpt-5.6-luna`，没有修改默认 OpenAI Provider、PATH、系统环境变量、注册表、服务或计划任务。
- 备份：修改前配置备份至 `C:\Users\wardc\Documents\New project gpt\AI-archive\notes\codex-deepseek-bridge\config-pre-deepseek-20260805-205231.toml`。
- 验证：DeepSeek `/v1/models`、LiteLLM `/v1/responses` 和 Codex CLI 端到端调用均成功；Codex CLI 返回 `CODEX_BRIDGE_OK`。当前 Codex 桌面端第三方 Provider 的模型选择器仍存在已知限制，因此没有启用会替换完整模型目录的 `model_catalog_json`。
- 运行方式：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\LiteLLM-DeepSeek-Bridge\start-bridge.ps1` 启动，`health-check.ps1` 验证，`stop-bridge.ps1` 停止；桥接服务仅监听 `127.0.0.1:4000`。
- 清理方式：停止桥接后删除归档应用目录；从 Codex 配置删除追加的 Provider 段；删除用户级 `DEEPSEEK_API_KEY` 和 `CODEX_DEEPSEEK_BRIDGE_KEY`；如需完整回滚，关闭 Codex 后使用备份文件恢复配置。

## 2026-08-05 — 丝网印刷工作坊图文包

- 用户授权：用户要求完成丝网印刷工作坊的招募推送、流程介绍和定价说明。
- 归档产物：在 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊图文包_2026-08-05` 创建招募长图、可编辑 Word 图文说明、可复制推送文案和一张主视觉示意图；未覆盖用户原有文件。
- 临时/外部路径：图像生成工具按其固定机制先将主视觉写入 `C:\Users\wardc\.codex\generated_images\019fd218-44e5-7f11-9efa-e1fbb2532caa\exec-3b356a40-cac2-420d-813d-3725ef04fe9e.png`，随后已复制一份到上述归档产物目录。该外部文件是工具生成缓存，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要成品，可删除上述归档产物目录；若需清理工具缓存，也可删除本节列出的单个 `.codex\generated_images` 文件，不影响归档中的最终成品。

## 2026-08-05 — 丝网印刷工作坊宣传页复制到桌面

- 用户授权：用户明确要求把本次完成的丝网印刷工作坊宣传页下载到桌面。
- 桌面写入：复制完整交付文件夹到 `C:\Users\wardc\Desktop\丝网印刷工作坊宣传页_2026-08-05\`，共 18 个文件、约 23.59 MB，包含招募主海报、六步课程流程图、WeFlow 主题说明的 JPG/PNG 版本、可编辑 HTML、公众号与群发文案及配套素材。
- 只读来源：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊宣传页_2026-08-05\`；采用复制方式，归档原件仍保留，未移动或覆盖。
- 验证：桌面副本与归档来源的文件数均为 18，总字节数一致。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要桌面副本，删除 `C:\Users\wardc\Desktop\丝网印刷工作坊宣传页_2026-08-05\` 即可；归档原件不受影响。

## 2026-08-05 — 安装微信 Windows 旧版 4.1.6.14

- 用户授权：用户明确要求安装旧版微信，以处理 WeFlow `6.1.0` 在微信 `4.1.11.55` 上出现的 V4 内存扫描失败。
- 版本选择：本机 WeFlow Windows 组件包含以 `4.1.6.14` 为边界的兼容分支，因此选择微信 `4.1.6.14` 进行兼容性测试；尚未登录或验证 WeFlow 读取结果。
- 下载归档：安装包保存到 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Weixin\wechatwin-v4.1.6.14-github.exe`，来源为 `cscnk52/wechat-windows-versions` 的 GitHub Release；腾讯旧版 CDN 已返回 404。安装包 SHA-256 为 `70C4B73C6EE306A916572193B4E1B9762516B93227AF1A2B48B662148A140B8E`，腾讯 Authenticode 数字签名有效。
- 系统安装：用 `/S` 静默安装到 `C:\Program Files\Tencent\Weixin\`；安装后 `Weixin.exe` 文件版本/产品版本均为 `4.1.6.14`，签名有效。
- 外部改动：新增公共桌面微信快捷方式、ProgramData 开始菜单微信与卸载快捷方式、Windows 已安装应用卸载项，并新增或更新 `HKEY_CURRENT_USER\Software\Tencent\Weixin`。未修改 PATH、环境变量，未新增服务或计划任务。
- 数据保护：安装器完成后自动启动了微信登录界面及 4 个插件子进程；未登录账号，发现后已结束全部微信进程。按安装开始时间回查，`C:\Users\wardc\xwechat_files`（约 15.88 GB）和 `C:\Users\wardc\Documents\WeChat Files`（约 4.03 GB）均没有新增或修改文件。首次主动启动前建议复制备份。
- 清理方式：完全退出微信后运行 `C:\Program Files\Tencent\Weixin\Uninstall.exe`；按 `AI-archive\apps\Weixin\INSTALL-NOTES.md` 检查程序目录、快捷方式和注册表残留。不要随客户端删除两个聊天数据目录。

## 2026-08-05 — 强制锁定微信 4.1.6.14、禁止自动更新

- 用户授权：用户明确要求永久禁止电脑微信更新，保持 WeFlow 可兼容的旧版状态。
- 现场现象：第一次安装 `4.1.6.14` 后，微信在数分钟内自行升级回 `4.1.11.55`。确认更新由 AppData 中的 `WeixinUpdate.exe` 插件及 `xwechat\update` 缓存机制参与完成。
- 回退结果：关闭全部微信进程，清除 `4.1.11.55` 客户端安装登记后重新安装 `4.1.6.14`；没有删除 `C:\Users\wardc\xwechat_files` 或 `C:\Users\wardc\Documents\WeChat Files`。
- 系统级执行阻断：新增 `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\WeixinUpdate.exe`，`Debugger` 为 `"C:\Windows\System32\cmd.exe" /d /q /c exit 0`，使任意路径下同名更新器立即退出。
- 用户设置：在 `HKCU\Software\Tencent\WeChat` 与 `HKCU\Software\Tencent\Weixin` 设置 `NeedUpdateType=0`。
- 防火墙：新增 `Codex-Weixin-4.1.6.14-UpdateBlock-1` 和 `Codex-Weixin-4.1.6.14-UpdateBlock-2` 两条出站阻断规则，仅针对已识别的微信更新器路径，不阻断微信主程序联网。
- ACL：对 `C:\Users\wardc\AppData\Roaming\Tencent\xwechat\xplugin\Plugins\WeixinUpdate`、`C:\Users\wardc\AppData\Roaming\Tencent\xwechat\update`、`C:\ProgramData\Tencent\WeChat\patch` 添加当前用户“拒绝写入/删除”规则；锁定前 SDDL 已保存。
- 更新器处理：原 `9012`、`9013` 两个腾讯签名更新器先复制到 `AI-archive\apps\Weixin\update-lock-state\updater-backup\`，再可逆停用。新版卸载过程中原插件目录被移除；最终重新建立为空目录并锁定，备份仍保留。
- 管理文件：新增 `lock-weixin-update.ps1`、`reapply-weixin-update-lock.ps1`、`unlock-weixin-update.ps1` 和 `update-lock-state\state.json`，全部位于 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Weixin\`。
- 验证：微信运行 40 秒后仍为 `4.1.6.14`；更新器进程、更新缓存文件、更新插件文件均为 0；安装目录中只有 `4.1.6.14`。三个锁定目录的实际写入测试均被拒绝，未留下测试文件。WeFlow `keyflow.log` 随后记录数据库密钥和图片密钥均获取成功，确认兼容链路已恢复。
- 恢复方式：以管理员身份运行 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Weixin\unlock-weixin-update.ps1`，恢复锁定前 ACL/注册表和更新器文件，并删除本次防火墙规则。此锁可跨重启保持，但管理员重装、手动解锁或腾讯更换更新器名称后应重新核验。

## 2026-08-05 — 丝网印刷工作坊数字人升级版复制到桌面

- 用户授权：用户要求去除宣传页中的 WeFlow 等字样，统一替换为数字人主题，并提升整体视觉设计。
- 归档产物：新建 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊宣传页_数字人升级版_2026-08-05\`，保留旧版未覆盖；包括招募主海报、六步课程流程图、数字人主题说明、公众号与群发文案、可编辑 HTML 和配套素材。
- 桌面写入：复制完整升级版到 `C:\Users\wardc\Desktop\丝网印刷工作坊宣传页_数字人升级版_2026-08-05\`，共 18 个文件、约 22.18 MB。
- 内容检查：公开图片与文案中未检出 `WeFlow`、`MBTI`、`聊天记录` 或 `聊天人格` 字样；数字人主题按“开发中、独立扩展方案”表述，未并入 68 / 58 元基础课程承诺。
- 验证：桌面副本与归档来源的文件数均为 18，总字节数一致；三张主图均为 1080 × 1920，并导出 PNG 与 JPG。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；浏览器渲染临时配置保存在归档 `tmp` 目录内。
- 清理方式：如不再需要桌面副本，删除 `C:\Users\wardc\Desktop\丝网印刷工作坊宣传页_数字人升级版_2026-08-05\` 即可；归档原件和旧版均不受影响。

## 2026-08-06 — 丝网印刷工作坊海报移除价格信息

- 用户授权：用户要求从海报中移除“对外体验价 68元/人”及“井邻客人专享 58元/人”等两张价格卡片内的文字。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊海报_去价格信息版.png`；保持原图 `1080 × 1920` 尺寸，未覆盖桌面源图。
- 外部位置：只读访问 `C:\Users\wardc\Desktop\微信图片_20260805220423_63_10.png`；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-a3f0b61e-279b-41b9-9242-73ccbe187bfd.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，删除上述归档 PNG；如需节省工具缓存空间，可单独删除所列 `.codex\generated_images` 预览，不影响最终成品。

## 2026-08-06 — 丝网印刷工作坊海报移除 WeFlow

- 用户授权：用户要求从上一版海报底部“主题加选”说明中去除 `WeFlow`。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊海报_去价格及WeFlow版.png`；基于无价格版本制作，仍为 `1080 × 1920`，未覆盖先前版本或桌面源图。
- 编辑结果：只移除 `WeFlow`，将剩余“聊天人格图谱 × 丝网印刷主题开发中，欢迎预约咨询。”左对齐，保持原文字形、颜色与背景一致。
- 外部位置：图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-b7dc26f4-67e6-490e-afa1-651639b201f6.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：可删除本节列出的归档 PNG；如需清理工具缓存，可单独删除所列 `.codex\generated_images` 预览，不影响最终成品。

## 2026-08-06 — 丝网印刷工作坊海报保留体验价

- 用户授权：用户澄清左侧红色卡片应保留“体验价 68元/人／课程指导与基础物料已包含”，但不得出现“对外”。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊海报_体验价保留_无WeFlow版.png`；基于无 WeFlow 版本制作，未覆盖任何先前版本。
- 编辑结果：恢复原左卡的 `68元/人` 与课程说明，并将标题精确改为“体验价”；右侧绿色卡片继续不含 `58元/人` 或任何井邻专享价格文字，底部也不含 `WeFlow`。
- 外部位置：只读访问桌面原图；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-82e3869b-eb79-4c1a-850a-8cb69c7e3960.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，删除本节列出的归档 PNG；未采用的预览缓存可单独删除，不影响成品。

## 2026-08-06 — 丝网印刷工作坊海报更换微信二维码并保存桌面

- 用户授权：用户提供新的微信二维码截图，并要求替换海报右下角二维码、保存到桌面。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊海报_体验价_新微信二维码_无WeFlow版.png`；保持 `1080 × 1920`，未覆盖先前版本。
- 桌面写入：复制同一文件至 `C:\Users\wardc\Desktop\丝网印刷工作坊海报_体验价_新微信二维码_无WeFlow版.png`；归档和桌面副本 SHA-256 一致。
- 编辑结果：从用户截图中透视校正并嵌入其二维码，仅改变右下角 `170 × 170` 的二维码卡片区域；“扫码咨询”及所有其它海报内容未改。嵌入后的二维码轮廓检测通过。
- 外部位置：只读访问 `C:\Users\wardc\Desktop\微信图片_20260806180940_33_32.jpg`；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-f203e0d0-8fde-44db-b7b5-6d6a01aa8044.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除桌面副本及上述归档 PNG 即可；如需清理预览缓存，可单独删除所列文件，不影响成品。

## 2026-08-06 — 聊天人格丝网印刷流程图去除 WeFlow

- 用户授权：用户要求从左上角英文小标题中移除 `WEFLOW`，保留 `× SCREEN PRINTING`。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\聊天人格丝网印刷流程图_去WeFlow版.png`；保持 `1080 × 1920`，未覆盖桌面原图。
- 编辑结果：仅在 `WEFLOW` 字形区域修复底图纹理，后方标题、中文文字、照片和版式保持不变；像素比对确认没有超出标题区域的改动。
- 外部位置：只读访问 `C:\Users\wardc\Desktop\微信图片_20260805220432_65_10.jpg`；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-fbdd7bab-c8fc-4b34-8d81-62b0a5f46115.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述归档 PNG 即可；未采用的预览缓存可单独删除，不影响成品。

## 2026-08-06 — 丝网印刷工作坊海报体验价文字校正

- 用户授权：用户指出左侧红色价格卡标题误显示为“本验价”，要求改正为“体验价”，并要求保存到桌面。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊海报_体验价文字校正版_新微信二维码_无WeFlow版.png`；保持 `1080 × 1920`，未覆盖先前版本。
- 桌面写入：复制同一文件至 `C:\Users\wardc\Desktop\丝网印刷工作坊海报_体验价文字校正版_新微信二维码_无WeFlow版.png`；归档与桌面副本 SHA-256 一致。
- 编辑结果：仅以原版字形修正红色卡片标题为“体验价”；`68元/人`、课程说明、右下角新微信二维码以及其余全部内容未变。像素比对确认改动未超出标题区域。
- 外部位置：只读访问桌面原海报 `C:\Users\wardc\Desktop\丝网印刷工作坊海报_体验价_新微信二维码_无WeFlow版.png` 和字形参考图 `C:\Users\wardc\Desktop\微信图片_20260805220423_63_10.png`；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-704834c0-71fa-4888-b107-cdeb84d246cc.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，删除本节列出的归档 PNG 和桌面副本；未采用的预览缓存可单独删除，不影响成品。

## 2026-08-06 — 丝网印刷工作坊课程流程保留体验价、移除井邻价

- 用户授权：用户要求保留“体验价 68元/人／课程指导与基础物料已包含”，且不出现“对外体验价”；移除所有井邻及 `58元/人` 信息。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊课程流程_体验价保留_去井邻58元版.png`；保持 `1080 × 1920`，未覆盖桌面原图。
- 编辑结果：仅重排底部绿色横条右侧价格小字为“体验价 68元/人”和“课程指导与基础物料已包含”；左侧“小班／时长”内容及其它六步流程、图片、文字均未改变。像素比对确认改动未超出该价格文字区域。
- 外部位置：只读访问 `C:\Users\wardc\Desktop\微信图片_20260805220428_64_10.jpg`；图像编辑工具按固定机制创建了未采用的预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-e2b864dd-b18b-40fb-92d3-00c4e4073ad9.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述归档 PNG 即可；未采用的预览缓存可单独删除，不影响成品。

## 2026-08-06 — 本轮图像成品统一复制到桌面

- 用户授权：用户要求将本轮完成的成品全部保存到桌面。
- 桌面写入：新增 `C:\Users\wardc\Desktop\聊天人格丝网印刷流程图_去WeFlow版.png` 与 `C:\Users\wardc\Desktop\丝网印刷工作坊课程流程_体验价保留_去井邻58元版.png`；先前的 `丝网印刷工作坊海报_体验价文字校正版_新微信二维码_无WeFlow版.png` 已在桌面，未覆盖。
- 验证：两张新桌面副本分别与其 `AI-archive\outputs` 原件 SHA-256 一致。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，可删除本节列出的桌面 PNG；归档原件不受影响。

## 2026-08-06 — 丝网印刷工作坊强招募主海报

- 用户授权：用户要求将招募文案放在最高优先级，采用更有吸引力的 slogan 并制作成海报；此前已要求本轮成品保存到桌面。
- 归档产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\丝网印刷工作坊_强招募主海报_第一次的印.png`，尺寸 `1080 × 1920`。
- 桌面写入：复制同一文件至 `C:\Users\wardc\Desktop\丝网印刷工作坊_强招募主海报_第一次的印.png`；归档与桌面副本 SHA-256 一致。
- 设计结果：采用主 slogan“刮一下，印出你的第一件作品。”，突出“零基础友好、3—5人小班、2—3小时、完成并带走1件作品、体验价68元/人、课程指导与基础物料已包含、小班预约制”；未加入 WeFlow、MBTI、井邻价或 `58元/人`。
- 素材使用：只读使用归档中的现场照片 `class-print-2.jpg`，并从用户桌面提供的 `微信图片_20260806180940_33_32.jpg` 透视校正并嵌入微信二维码；成品内二维码轮廓检测通过。
- 外部位置：图像设计工具生成了构图预览缓存 `C:\Users\wardc\.codex\generated_images\019fd67e-d077-7b02-8cef-8a306feec90b\exec-1ea2cd7e-94c1-4be4-af2d-be988226fbd5.png`；制作期间在当前工作区短暂创建的渲染脚本已删除，未留下额外中间文件。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，删除本节列出的桌面 PNG 和归档 PNG；预览缓存可单独删除，不影响成品。

## 2026-08-07 — 微信事件分析深度复核规范

- 用户授权：用户要求将“模型先深度预判、用户低负担确认”的两项复核要求直接写入微信聊天记录分析工作区。
- 桌面工作区写入：新增 `C:\Users\wardc\Desktop\微信聊天记录清理\10_DeepSeek-v3分析工作区\DEEP-REVIEW-SPEC.md`，作为事件分析与复核页的强制需求规范。
- 内容范围：规范深度预填判断档案、反证与置信度、用户确认/纠偏界面、无 API 与需确认的深度分析阶段，以及可追溯和隐私边界；未修改原始聊天数据、主项目或历史标注表。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；未发起项目级 API 调用。
- 清理方式：如不再需要，删除上述规范文件即可；它不影响聊天数据库或既有标注结果。

## 2026-08-08 — 每日行动简报自动化运行记录

- 用户授权：用户配置“蔡浩文每日行动简报”自动化，要求读取和更新该自动化的运行记忆。
- 外部位置写入：更新 `C:\Users\wardc\.codex\automations\automation-3\memory.md`，记录本次检索范围、已核验信息、仍有效机会和下次跟进重点。
- 系统范围：联网只读检索；未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除该条运行记录或自动化记忆只会影响后续简报的去重与连续性，不影响其他文件或系统设置。

## 2026-08-08 — 物理世界模型与交互设计开源前沿周报自动化运行记录

- 用户授权：用户配置“物理世界模型与交互设计开源前沿周报”自动化，要求联网检索并更新该自动化的运行记忆。
- 外部位置写入：更新 `C:\Users\wardc\.codex\automations\automation-2\memory.md`，记录本次检索范围、候选论文/项目、筛选结论和下次去重重点。
- 系统范围：联网只读检索；未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除该条运行记录或自动化记忆只会影响后续周报的去重与连续性，不影响其他文件或系统设置。

## 2026-08-08 — OpenCodex 本地接入 DeepSeek API

- 用户授权：用户明确要求用 OpenCodex 接入其提供的 DeepSeek API 密钥。
- 归档安装：以本地隔离方式安装 `@bitkyc08/opencodex` `2.10.2` 到 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\opencodex\`；使用本地 `node_modules`，未安装全局 npm 包、未修改 PATH。详细记录见同目录 `INSTALL-NOTES.md`。
- 密钥处理：DeepSeek 密钥只写入用户私有的 `C:\Users\wardc\.opencodex\config.json`；本日志、安装记录和命令输出均未保存密钥。该配置文件含明文凭据，应视为敏感文件。
- 外部位置与设置：新增/更新 `C:\Users\wardc\.opencodex\` 运行配置和状态；OpenCodex 向 `C:\Users\wardc\.codex\config.toml` 写入本机代理与模型目录引用，并新建/更新 `opencodex.config.toml`、`opencodex-catalog.json`、`models_cache.json`。项目启动时还自动向 `C:\Users\wardc\.grok\config.toml` 加入受管区块，并创建 `config.toml.bak-opencodex`；未导入或使用 Grok 凭据。
- 网络与验证：本机代理只监听 `127.0.0.1:10100`，向 `https://api.deepseek.com` 发起认证后的模型目录查询和一条最小 Responses 兼容性验证请求；`deepseek/deepseek-v4-flash` 返回 HTTP 200。该验证可能产生极少量 DeepSeek API 用量。
- 运行状态：启动了后台本机代理进程；未创建 Windows 服务、计划任务、开机启动项、注册表或环境变量。Windows 重启后需手动重新启动代理。
- 依赖缓存：npm 更新了共享缓存 `C:\Users\wardc\AppData\Local\npm-cache`；不应在卸载时直接删除，除非确认无其他 Node 项目使用。
- 清理方式：先运行 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\opencodex\node_modules\.bin\ocx.cmd uninstall`，它会停止代理并尝试还原 Codex/Grok 受管配置、移除 OpenCodex 私有配置；确认成功后再删除 `AI-archive\apps\opencodex\`。共享 npm 缓存保留。

## 2026-08-08 — Live Body X-Ray 版本汇总与交互视觉说明

- 用户授权：用户要求查找 Live Body X-Ray 的修改版本，统一罗列到桌面新文件夹，并解释运行细节及最合适的交互视觉修改方向。
- 只读范围：检查 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Live-Body-XRay-Volume-Portable\`，并在桌面微信导出备份、下载目录、Codex 工作区等位置检索同名压缩包；未修改原安装目录和原始聊天备份。
- 桌面写入：新增 `C:\Users\wardc\Desktop\Live Body X-Ray_版本与修改说明_2026-08-08\`，其中包含原始收件版副本、当前本机增强启动版副本、版本总览，以及详细运行原理和交互视觉设计建议。
- 版本结论：找到 7 个名称相近 ZIP，但 SHA-256 均为 `8E8C14B8FD8DD99E1D9E8CABD24BED3B412B601B248679B9233F2E949A3CF235`，实际是同一原始包的重复副本；未删除任何重复包。当前本机版仅增强 Windows/Node.js 启动方式和说明，`app.js`、`index.html`、`styles.css` 及视觉素材与原始版一致。
- 临时运行：为只读界面测试临时启动 `127.0.0.1:5188` 本地服务，完成桌面、手机竖屏和手机横屏布局检查后已停止；未申请或接受浏览器摄像头权限。
- 工作区临时文件：为哈希和逐文件比对，在 `C:\Users\wardc\Documents\Codex\2026-07-31\live-body-x-ray-c-users\work\source-compare-20260808\` 解压一份原始包；它只用于本次分析。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务、防火墙、摄像头设置或浏览器设置；未联网下载新资源。
- 清理方式：桌面汇总可整夹删除，不影响已安装程序；工作区临时比对目录也可删除。原始 ZIP 和安装目录均保持不变。

## 2026-08-08 — 微信升级至 4.1.12.26 并重新锁定更新

## 2026-08-08 — WeFlow 启动（本次会话）

- 用户授权：用户明确要求打开 WeFlow。
- 运行：从 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe` 启动 WeFlow；确认进程 `WeFlow` 已运行。未安装、更新或修改该应用。
- 临时权限：为初始化 Codex 桌面控制组件，申请只读访问 `C:\Users\wardc\AppData\Local\OpenAI\Codex`；该组件仍因系统级访问限制未能读取该目录，因此改用已安装应用的可执行文件启动。此权限仅本会话有效，无需清理文件或设置。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务、应用设置或用户数据。

## 2026-08-08 — 桌面文档“你好”

- 用户授权：用户要求在桌面创建名为“你好”的文档。
- 写入：新建 `C:\Users\wardc\Desktop\你好.txt`，内容为“你好”；创建前已确认目标文件不存在，未覆盖任何现有文件。
- 清理方式：如不再需要，可直接删除该单一文本文件；未修改任何系统设置或应用数据。

- 用户授权：用户明确要求安装最新微信 PC 版并重新禁止自动更新。
- 归档安装包：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Weixin\WeChatWin_4.1.12.exe`，SHA-256 `58997CFE4513AB71F107C2137BB570ADE030F228115C14688544CEC80E604053`，腾讯 Authenticode 签名有效。
- 系统安装：覆盖安装到 `C:\Program Files\Tencent\Weixin\`，新增版本目录 `4.1.12.26`（旧版 `4.1.6.14` 目录仍保留）。
- 聊天数据保护：`C:\Users\wardc\xwechat_files\` 和 `C:\Users\wardc\Documents\WeChat Files\` 未动。
- 更新锁（v2）：新增 IFEO 阻断 `WeixinUpdate.exe`；`NeedUpdateType=0`（HKCU WeChat/Weixin）；ACL 拒绝写入 `xwechat\update` 和 `ProgramData\Tencent\WeChat\patch`；防火墙出站阻断规则 `Codex-Weixin-4.1.12-UpdateBlock-1`；`WeixinUpdate.exe` 重命名为 `.codex-disabled` 并备份。
- 管理脚本：`unlock-weixin-4.1.12.ps1`（解锁）、`reapply-weixin-4.1.12-lock.ps1`（重锁），位于 `AI-archive\apps\Weixin\`；状态文件 `update-lock-state-v2\state.json`。
- 旧锁清理：4.1.6.14 的 IFEO、防火墙规则 `Codex-Weixin-4.1.6.14-UpdateBlock-*`、注册表 NeedUpdateType 均已移除。
- 系统范围：未修改 PATH、环境变量、服务、计划任务或其他应用设置；未安装公共依赖。
- 恢复方式：管理员运行 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\Weixin\unlock-weixin-4.1.12.ps1` 可恢复所有锁定前状态并移除防火墙规则。

## 2026-08-08 — DSCodex 同窗口 OAuth 共存修复

- 用户授权：用户要求绕开 DSCodex 导致 Codex Work 认证失败的问题，并继续在同一个 Codex 窗口使用 DeepSeek V4 Pro。
- 外部源码变更：修改历史安装目录 `C:\Users\wardc\tools\dscodex\`；新增 `src\codex-auth.mjs` 和认证测试，修改 `src\proxy.mjs` 使 GPT/Work 请求缺少认证头时动态读取当前 `C:\Users\wardc\.codex\auth.json` 的 access token 与 account id。不会读取、输出或保存 refresh token。
- 应用设置：重新通过 DSCodex 在 `C:\Users\wardc\.codex\config.toml` 注入 `openai_base_url`（`127.0.0.1:10110`，含随机路由令牌）与 `model_catalog_json`，保留 `model = "gpt-5.6-sol"` 和 `model_reasoning_effort = "max"`。
- 运行状态：DSCodex 路由器重新启动并监听 `127.0.0.1:10110`；未启动 OpenCodex，未修改 v2rayN、HTTP_PROXY、HTTPS_PROXY、ALL_PROXY、Claude Code/DeepSeek 环境变量、注册表、服务或计划任务。
- 验证结果：GPT 鉴权探测由原 HTTP 401 改为 HTTP 400（认证已通过，极简探测体不符合完整 Codex 请求格式）；模拟代理测试通过。DeepSeek V4 Pro 仍由服务端返回 HTTP 400，提示 Codex 集成尚未开放并要求暂用 V4 Flash。
- 清理方式：在 `C:\Users\wardc\tools\dscodex\` 运行 `node src/cli.mjs uninstall`，并按 `INSTALL-NOTES.md` 回退源码变更；此前备份为 `C:\Users\wardc\.codex\config.toml.bak-before-native-route-restore-20260808-190927`。

## 2026-08-08 — DeepSeek V4 Pro Responses-to-Chat 适配

- 用户授权：用户提供新的 DeepSeek API Key，并要求把 V4 Pro 在当前 Codex 窗口中实际跑通。
- API 验证：新 Key 已通过官方 DeepSeek `/models` 与 `/chat/completions` 验证；V4 Pro 可用。Key 未输出、未写入日志；DSCodex 使用 Windows DPAPI 加密保存。
- 外部源码与依赖：在 `C:\Users\wardc\tools\dscodex\` 增加隔离适配器源码，并固定添加本地依赖 `@bitkyc08/opencodex@2.10.2`。未安装全局包，未改 PATH、注册表、服务或计划任务。
- 运行配置：DSCodex 10110 内部启动适配器 10111；适配器只使用 `C:\Users\wardc\.codex\dscodex\chat-adapter\` 作为隔离的 OPENCODEX_HOME/CODEX_HOME，禁用 `codexAutoStart` 与 `codexShimAutoRestore`。它不会启动或恢复原有 OpenCodex 10100，也不会改写真实 Codex 配置。
- 验证：DSCodex 文本 V4 Pro、自动函数调用、函数结果回传均为 HTTP 200，并产生完整 Responses 结束事件。
- 清理方式：运行 `C:\Users\wardc\tools\dscodex\src\cli.mjs uninstall`（通过 node）停止外层路由；随后可删除明确路径 `C:\Users\wardc\.codex\dscodex\chat-adapter\`。若要移除本地转换依赖，在 DSCodex 目录执行 `npm uninstall @bitkyc08/opencodex`。

## 2026-08-11 — 长征题材油画完成稿视觉示意

- 用户授权：用户提供桌面照片 `C:\Users\wardc\Desktop\微信图片_20260811174608_63_5.jpg`，要求分析未完成油画并生成建议修改方向的成品示意；原照片仅作读取参考，未修改。
- 生成文件：图像生成工具按默认机制写入 `C:\Users\wardc\.codex\generated_images\019ff039-6611-70b2-b77c-4f8faf40c7a0\exec-606db56d-1ea7-490f-9073-829420ee7ae7.png`；另按当前 Codex 项目输出要求复制到 `C:\Users\wardc\Documents\Codex\2026-08-11\zhe\outputs\长征题材油画_修改方向完成稿示意_2026-08-11.png`。
- 统一归档：同步保存一份到 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\长征题材油画_修改方向完成稿示意_2026-08-11.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务、应用设置或其他用户数据。
- 清理方式：如不再需要，可删除上述 `.codex\generated_images` 中的单张生成图与本次 `Codex\2026-08-11\zhe\outputs` 中的副本；归档副本可按需保留或单独删除，均不影响原照片。

### 2026-08-11 — 重大题材风格忠实修订版

- 用户修订：要求不改动原有构图、人物、姿态、服装、器物与比例，主要强化“重大历史题材油画”风格。
- 新生成文件：图像生成工具写入 `C:\Users\wardc\.codex\generated_images\019ff039-6611-70b2-b77c-4f8faf40c7a0\exec-c3e34617-074e-46df-ba41-496016b69946.png`；未覆盖上一版。
- 项目输出副本：`C:\Users\wardc\Documents\Codex\2026-08-11\zhe\outputs\长征题材油画_重大题材风格忠实完成稿示意_2026-08-11.png`。
- 统一归档副本：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\长征题材油画_重大题材风格忠实完成稿示意_2026-08-11.png`。
- 系统范围：未安装依赖，未修改系统或应用设置；删除上述单张生成图及两个副本即可清理，不影响原照片。

### 2026-08-11 — “延安阳光下儿童”正面迎光眼神示意

- 用户授权：用户提供临时图片 `C:\Users\wardc\AppData\Local\Temp\codex-clipboard-93638e57-76be-4781-9fcb-0bd4e4e2780f.jpg`，要求给出极少改动的正面迎光眼神样子；原图只读，未修改。
- 生成过程：图像生成工具在 `C:\Users\wardc\.codex\generated_images\019ff039-6611-70b2-b77c-4f8faf40c7a0\` 生成三张递进预览：`exec-0ddef1a5-c401-4261-ba2c-ba5a37ee4604.png`、`exec-1f26b186-cf49-494c-b5dd-c8b4472178db.png`、`exec-eb16d42a-61db-4e36-bc16-73f565174311.png`；第二张未作为最终交付，第一张仅作为眼神方向加强参考，第三张作为极少改动参考。
- 项目输出副本：`C:\Users\wardc\Documents\Codex\2026-08-11\zhe\outputs\延安阳光下儿童_正面迎光眼神极少改动示意_2026-08-11.png`。
- 方向加强副本：`C:\Users\wardc\Documents\Codex\2026-08-11\zhe\outputs\延安阳光下儿童_眼神方向加强参考_勿照搬脸型_2026-08-11.png`；只用于参考瞳孔朝向，不用于照搬人物脸型。
- 统一归档副本：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\延安阳光下儿童_正面迎光眼神极少改动示意_2026-08-11.png`。
- 统一归档方向参考：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\延安阳光下儿童_眼神方向加强参考_勿照搬脸型_2026-08-11.png`。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：可删除上述 `.codex\generated_images` 中三张预览及本次 Codex 项目输出副本；归档副本可按需保留或单独删除，均不影响原始临时图片。

## 2026-08-15 — 小米盒子 spacedesk 海报横屏投放

- 用户授权：读取桌面原图 `C:\Users\wardc\Desktop\微信图片_20260810212512_43_107.png`，适配小米盒子 / spacedesk 显示并进行投屏；原图未修改。
- 连接检查：spacedesk Driver 已开启，电脑局域网地址为 `192.168.1.6`；历史设备为 `MiBOX4C`，当前盒子 `192.168.1.5` 在线。未修改网络、系统安全或 spacedesk 驱动设置。
- 外部生成：图像生成工具按默认机制写入背景图 `C:\Users\wardc\.codex\generated_images\01a0030a-b6cc-7e32-b095-4390f568e0aa\exec-90577cf0-0f3a-4919-a38f-8cac189c8a22.png`。
- 项目输出：生成 1920×1080 横屏海报 `C:\Users\wardc\Documents\Codex\2026-08-15\wo\outputs\乡村美育工作站-电视横屏版-1920x1080.png`；中间保留完整原海报，左右增加电视距离下更清晰的日期、价格、人数、时长、预约二维码等信息。
- 临时文件：`C:\Users\wardc\Documents\Codex\2026-08-15\wo\work\tv-poster-background.png` 与 `C:\Users\wardc\Documents\Codex\2026-08-15\wo\work\make_tv_poster.py`。
- 盒子连接：复用已归档的 Android Platform Tools 与独立 ADB 密钥，连接 `192.168.1.5:5555`，启动盒子上既有的 `ph.spacedesk.beta`，未安装或更新盒子应用；ADB 服务仅为本次唤起 Viewer 使用。
- Windows 显示设置：执行系统自带的扩展显示切换，启用 spacedesk 虚拟屏 `DISPLAY6`（1920×1080，非主屏，位置在主屏右侧）。
- 展示脚本：新增 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\spacedesk\tools\Show-SinglePoster.ps1`，并同步更新 spacedesk 的 `INSTALL-NOTES.md`；当前以隐藏后台进程 PID `11060` 运行，掉线时自动隐藏、重连后自动回到第一块非主屏。
- 系统范围：未安装新依赖，未修改 PATH、持久环境变量、注册表、服务、计划任务或安全设置；仅将 Windows 显示模式切换为“扩展”。
- 清理方式：在海报屏幕按 `Esc` 或结束 PID `11060` 可停止展示；不再投屏时在盒子退出 spacedesk Viewer，并按需切回“仅电脑屏幕”。可删除上述 `.codex\generated_images` 单张背景图、本次 `work` 临时文件、`outputs` 横屏海报及新增的 `Show-SinglePoster.ps1`；不会影响桌面原图或 spacedesk 安装。

### 2026-08-15 — 第二块小米盒子屏幕接入

- 设备地址：第二台 `MiBOX4C` 已由历史地址 `192.168.1.8` 变更为 DHCP 地址 `192.168.1.4`；复用已有 ADB 工具和密钥启动既有 spacedesk Viewer，未安装新软件或授予新权限。
- 显示结果：Windows 现有 `DISPLAY6` 与 `DISPLAY7` 两块非主显示器，均为 1920×1080；两台盒子分别从 `192.168.1.5`、`192.168.1.4` 与 spacedesk 服务保持连接。
- 展示切换：停止单屏展示进程 PID `11060`，启动既有 `Show-DualPoster.ps1`，当前隐藏后台进程 PID `10780`，同一张 1920×1080 海报等比例铺满两块屏。
- 清理方式：在任一海报屏按 `Esc` 或结束 PID `10780` 可停止双屏展示；退出两台盒子的 Viewer 后，可按需切回“仅电脑屏幕”。

### 2026-08-15 — spacedesk 复刻流程文档

- 用户请求：整理本次海报适配、两台小米盒子连接、扩展显示、单屏/双屏展示、ADB 唤起与收尾的完整可复刻流程。
- 新增文件：`C:\Users\wardc\Documents\Codex\2026-08-15\wo\outputs\spacedesk-双屏投屏复刻流程.md`。
- 系统范围：仅新增说明文档，未修改任何系统、网络或应用设置。

### 2026-08-16 — 英文版双屏海报

- 用户请求：将当前两块小米盒子屏幕的活动海报换成英文版。
- 生成文件：图像生成工具写入英文背景 `C:\Users\wardc\.codex\generated_images\01a0030a-b6cc-7e32-b095-4390f568e0aa\exec-ba5b4070-442c-4d9b-95ec-592b85a59d5a.png`；使用桌面原图作为只读参考，未修改原图。
- 项目输出：`C:\Users\wardc\Documents\Codex\2026-08-15\wo\outputs\Rural-Aesthetic-Lab-English-TV-1920x1080.png`，分辨率 1920×1080；英文内容以确定性排版写入，二维码保留且去除原中文二维码说明。
- 展示切换：确认 `DISPLAY6`、`DISPLAY7` 均在线且为 1920×1080，并有两条 spacedesk 已建立连接；用既有 `Show-DualPoster.ps1` 启动新的隐藏后台展示进程 PID `23408`，同时替换两块屏幕画面。
- 临时文件：`C:\Users\wardc\Documents\Codex\2026-08-15\wo\work\english-tv-background.png` 与 `C:\Users\wardc\Documents\Codex\2026-08-15\wo\work\make_english_tv_poster.py`。
- 系统范围：未安装依赖，未修改网络、显示配置、PATH、环境变量、注册表、服务或计划任务。
- 清理方式：在任一海报屏按 `Esc` 或结束 PID `23408` 可停止英文双屏展示；可删除上述背景图、临时文件和英文输出文件，均不会影响桌面原图或 spacedesk 安装。

### 2026-08-16 — MediaPipe 34 英寸超宽屏适配

- 用户请求：定位此前的 MediaPipe 双手交互文件，并投放到 3440×1440 的 34 英寸超宽屏。
- 定位结果：可运行项目为 `C:\Users\wardc\Documents\Codex\2026-07-24\referenced-chatgpt-conversation-this-is-untrusted\outputs\偏移四型-MediaPipe-v2`。
- 文件调整：更新该项目 `styles.css`，新增仅在宽度至少 2560px、比例至少 2:1 时生效的 21:9 布局规则，扩大信息栏、中央手势视觉、采样与结果界面，适配 3440×1440。
- 连接检查：当前系统仍只识别两块 1920×1080 的 spacedesk 非主屏，未发现 3440×1440 显示器；尚未启动交互页或申请摄像头权限。
- 清理方式：删除新增的 CSS 媒体查询即可恢复项目此前布局；未安装依赖，未修改系统、网络、显示设置或启动项。

## 2026-08-15 — Codex / DeepSeek 接入复盘与安全归档

- 用户授权：用户要求回顾此前向 Codex 接入 DeepSeek 的全部操作、给出后续方向，并把相关文件集中归类。
- 归档写入：创建 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\Codex-DeepSeek-接入复盘与归档_2026-08-15\`，包含复盘报告、LiteLLM/OpenCodex/DSCodex 的可重建源文件、已脱敏的 Codex 配置历史和日志、登录启动项副本、文件清单与 SHA-256 校验表。
- 安全边界：未复制任何 DeepSeek API key、Bearer/OAuth/管理员 token、`C:\Users\wardc\.codex\auth.json`、含私密请求内容的使用日志或响应状态；敏感配置仅以脱敏副本归档。LiteLLM `venv`、OpenCodex/DSCodex `node_modules` 和 DSCodex Git 内部对象共约 1.09 GB，仅保留在原处，未移动、删除或重复复制。
- 项目输出：在 `C:\Users\wardc\Documents\Codex\2026-08-13\wo-2\outputs\` 额外写入复盘报告与归档入口，供当前 Codex 项目打开；完整归档以 AI-archive 目录为准。
- 只读审计结论：当前官方 Codex 默认使用 `gpt-5.6-sol`，没有代理地址覆盖；4000/10100/10110/10111 均无监听。LiteLLM Provider 仍残留在主配置；Windows Startup 文件夹还保留 DSCodex 自动启动脚本和控制面板快捷方式。本次未启动/停止代理、未修改密钥、环境变量、Codex 配置、启动项、注册表、服务或计划任务。
- 清理方式：如不再需要本次归档，可删除上述单一归档文件夹和本次项目 `outputs` 中的两份 Markdown；不会影响任何原始应用、私有配置或 DeepSeek 接入运行状态。

## 2026-08-15 — 电脑文件、配置与聊天记录只读梳理

- 用户授权：用户要求分析电脑中的文件、配置与相关聊天记录，并进行梳理整合。
- 只读范围：盘点固定磁盘与用户目录元数据、`AI-archive`、`.codex` 会话/自动化/配置结构、可见系统配置、启动项、网络监听，以及本机可见的 ChatGPT/Claude/WeFlow 聊天记录索引。未移动、删除、修改原文件；未读取或输出微信等第三方聊天正文；未显示、复制或外发任何密码、令牌、API Key 或聊天原文。
- 工作区输出：依照当前 Codex 项目输出约定，生成脱敏报告 `C:\Users\wardc\Documents\Codex\2026-08-13\fen\outputs\电脑文件_配置_聊天记录梳理报告_2026-08-15.md`。该路径位于统一归档文件夹之外，原因是当前项目要求将面向用户的交付物放在本项目 `outputs`；报告不包含敏感值或私人聊天原文。
- 临时缓存：为核对 Codex 官方说明，工具在 `%TEMP%\openai-docs-cache` 创建了一个空目录（0 文件、0 KB）；官方手册请求被 403 拒绝，未下载内容。为避免未确认的删除操作，该空目录暂未移除。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务、防火墙、网络设置、应用设置或用户数据；未安装依赖或启动/停止外部服务。
- 清理方式：如不再需要，可删除本次单一报告文件；系统临时空目录可在确认后单独删除。二者均不影响原始资料、软件或聊天记录。

## 2026-08-15 — DeepSeek Harness（dsh）全局安装与隔离配置

- 用户授权：用户要求直接配置，并明确指定“全局安装”。
- 安装：执行 `npm install --global @deepseek-ai/dsh@0.1.0-rc.6 --omit=dev`，安装官方 DeepSeek Harness 开发者预览版。全局包写入 `C:\Users\wardc\AppData\Roaming\npm\node_modules\@deepseek-ai\dsh\`，命令入口为 `C:\Users\wardc\AppData\Roaming\npm\dsh.ps1`。该 npm 全局目录原本已在 PATH 中；本次未修改 PATH、注册表、持久环境变量、服务或计划任务。
- 归档配置：新增 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\deepseek-harness\`，其中 `Start-DeepSeek-Harness.ps1` 每次启动时将 `DSH_HOME` 定向到该目录的 `state\`，并从 `workspace\` 作为默认工作区启动。用户随后通过 Web UI 填写的 API Key、会话及设置均应留在此隔离目录内。
- npm 缓存：npm 复用并写入既有共用缓存 `C:\Users\wardc\AppData\Local\npm-cache\`；未改动缓存位置。
- 安装修复：首次安装与重试发生文件锁冲突，形成未完成的 dsh 目录。确认没有相关 npm 进程后，仅执行 `npm uninstall --global @deepseek-ai/dsh --force` 清理该次未完成安装，再完成固定版本重装。未移除其他全局包。
- 验证：`dsh --version` 已返回 `0.1.0-rc.6`。npm 提示部分依赖安装脚本待审批；本次未额外放行脚本，后续将以 Web UI 启动验证为准。
- 临时运行：为验证配置，启动了仅本机监听的 Web UI `http://127.0.0.1:3080`，HTTP 返回 200；不是 Windows 服务、计划任务或开机启动项。新增 `Stop-DeepSeek-Harness.ps1`，其仅在核对监听进程为 dsh 后停止它。
- 桌面入口：按用户请求新增桌面快捷方式 `C:\Users\wardc\Desktop\DeepSeek Harness.lnk`；其指向归档目录内的启动脚本，双击会在服务未运行时隐藏启动 dsh，随后自动打开本机 Web UI。已实际调用并验证 Web UI 返回 HTTP 200。未创建开机启动项、Windows 服务或持久环境变量。
- 清理方式：先停止 dsh，运行 `npm uninstall --global @deepseek-ai/dsh`；再按需删除上述归档目录（其中可能含 API Key、会话日志和工作区文件）。`C:\Users\wardc\AppData\Local\npm-cache\` 是共用缓存，清理前需确认不会影响其他 npm 软件。

### 2026-08-16 — 交互屏与海报屏分屏展示

- 用户请求：保持已投放到 34 英寸屏幕的 MediaPipe 交互页全屏，同时让另一台小米屏独立展示英文海报。
- 运行状态：本机启动已有 MediaPipe 项目的本地服务 `server.mjs 4175`（PID 11260），并使用工作区私有 Chrome 配置目录 `C:\Users\wardc\Documents\Codex\2026-08-15\wo\work\mediapipe-chrome-profile\` 在 `DISPLAY6` 打开交互页；未修改 Chrome 全局设置、网络、显示配置或浏览器权限。
- 新增展示工具：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\spacedesk\tools\Show-PosterOnDisplay.ps1`。该工具按显示器设备名独立全屏展示，不会覆盖另一块屏幕。
- 当前展示：保留 `DISPLAY6` 的 MediaPipe 交互窗口；启动隐藏的海报展示进程 PID `8156`，在 `DISPLAY7` 全屏显示 `C:\Users\wardc\Documents\Codex\2026-08-15\wo\outputs\Rural-Aesthetic-Lab-English-TV-1920x1080.png`。两条 spacedesk 连接及两项展示进程均已核验运行。
- 清理方式：在海报屏按 `Esc` 或结束 PID `8156` 可停止海报，且不影响交互屏；结束 MediaPipe 的 Chrome 窗口和本地 Node 进程即可停止交互页。私有 Chrome 配置目录可在确认不再需要其浏览状态后删除。

### 2026-08-16 — 分屏投屏重启

- 用户请求：因画面卡死，重新建立两路投屏。
- 操作：停止此前仅限工作区私有配置目录的 MediaPipe Chrome 进程及海报展示进程；保留运行正常的本机 MediaPipe Node 服务（PID `11260`），重新在 `DISPLAY6` 以 Chrome kiosk 全屏模式打开 `http://127.0.0.1:4175`（新主进程 PID `12552`），并在 `DISPLAY7` 重启英文海报展示（PID `24016`）。
- 核验：MediaPipe 交互窗口与海报展示进程均在运行；spacedesk 服务仍有来自 `192.168.1.4`、`192.168.1.5` 的两条已建立连接。
- 系统范围：未安装软件、未修改显示/网络/浏览器全局设置、未修改摄像头权限或开机启动项。
- 清理方式：海报屏按 `Esc` 或结束 PID `24016`；关闭该 Chrome 窗口即可退出交互页。Node 服务按需停止。

### 2026-08-16 — 再次刷新并恢复双盒子连接

- 用户请求：再次重新投屏。
- 操作：重启工作区私有 MediaPipe Chrome 全屏窗口及英文海报展示进程（新海报进程 PID `21692`）。初检仅有一台 Viewer 连接后，使用已归档 ADB 工具和既有专用 ADB 密钥对 `192.168.1.5`、`192.168.1.4` 两台已授权 `MiBOX4C` 唤起已有 spacedesk Viewer，并点击其既有的电脑连接入口；未安装应用、未改变盒子设置或授予新权限。
- 核验：spacedesk 端口 `28252` 现有来自 `192.168.1.5`、`192.168.1.4` 的两条已建立连接；海报展示进程仍在运行，MediaPipe 本地服务未中断。
- 清理方式：按既有分屏展示流程退出 Viewer 或停止对应本机窗口即可；日常使用不需要保留 ADB 服务，可执行 `adb kill-server`。

## 2026-08-17 — 电脑梳理整合更新总账（只读增量核对）

- 用户授权：延续 8/15“电脑文件、配置与聊天记录梳理整合”的原始要求，做只读增量核对。
- 只读范围：读取本日志、桌面新增文件夹元数据、防火墙状态、Windows 版本、磁盘挂载与 ChatLab/Ollama 存在性检查。未移动、删除、修改任何原文件、设置或聊天数据。
- 桌面写入：新增 `C:\Users\wardc\Desktop\电脑梳理_更新总账_2026-08-17.md`，汇总 8/15 报告后的变化、桌面新增条目分类建议、安全 P0 现状复核与聊天记录整合进展。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务、防火墙、网络设置或应用设置。
- 清理方式：删除该单一 Markdown 文件即可；不影响任何原始资料或系统设置。


## 2026-08-17 — 桌面归位第1项：claude-remote-control 工具链拆分

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“拆开：源码留桌面，工具链进 apps”。
- 移动：`C:\Users\wardc\Desktop\claude-remote-control\build\`（883.5 MB / 12,020 文件：便携 JDK21、Android build-tools/platform、自签名 keystore、paths.json）移至 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\claude-remote-control\build\`；同盘移动，未产生副本或残留。
- 桌面保留：apk-src、output、pc-launcher、三个 .mjs 与 README（约 1 MB），日常启动与成品 APK 不受影响。
- 适配修改：更新移动后 `build\paths.json` 内 6 条绝对路径指向新位置并逐一核验存在；桌面 `build-apk.mjs` 增加工具链回落定位（优先项目内 build\paths.json，否则用归档路径），WORK 与 keystore 改由 TOOLCHAIN 变量解析，语法检查通过；README 重建章节补充工具链位置说明。
- 新增：`AI-archive\apps\claude-remote-control\INSTALL-NOTES.md`（内容、重建方法、keystore 安全提示与清理方式）。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；未启动/停止任何进程。
- 回退方式：把 `apps\claude-remote-control\build\` 移回桌面项目目录，并还原 paths.json 与 build-apk.mjs 的路径解析即可。

## 2026-08-17 — 桌面归位第2项：偏移四型-MediaPipe-v2 桌面副本转正

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“桌面副本转正，Codex 旧副本暂留”。
- 只读比对：桌面副本（740 文件 / 244 MB）与 Codex 原件（`Documents\Codex\2026-07-24\referenced-chatgpt-conversation-this-is-untrusted\outputs\偏移四型-MediaPipe-v2`，31 文件 / 44 MB）的 app.js、index.html、INTERACTION-SPEC.md、assets、models、node_modules 均一致；桌面 styles.css 为 7/24 旧版（缺 21:9 适配），Codex 为 8/16 新版。
- 写入：把 Codex 新版 styles.css 复制到桌面副本（1 个文件，15,005 字节），前后 SHA-256 一致；未改动 Codex 原件，未移动或删除任何文件。
- 现场状态：MediaPipe 本地服务（node PID 11260，8/16 15:17 起）与 kiosk 看门狗均在运行；本次同步不打断投屏。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 后续：Codex 旧副本（44 MB 重复内容）暂留待用户决定；kiosk 收工后可将桌面副本整体迁入 Documents 项目区。

## 2026-08-17 — 桌面归位第3项（续）：笑一聊天记录经“2”移入 ChatArchive 原始区

- 用户授权：另一会话把笑一聊天记录移进 `Desktop\2` 后，用户再次确认“整个 2 现在移走”。
- 移动：`C:\Users\wardc\Desktop\2\`（5 文件，约 1.7 MB：三格式原始导出 + 两份分析草稿）整体移至 `C:\Users\wardc\Documents\ChatArchive\00_raw\2026\笑一聊天记录_20260815\`（移动同时恢复可读命名）；同盘移动，未产生副本。
- 新建：`Documents\ChatArchive\` 归档根目录与 `README-结构说明.md`（替代 D:\ChatArchive；D 盘未挂载）。
- 注意：该文件夹此前正被另一 AI 会话使用；若其在桌面旧路径重建文件夹或写入新文件，需再次归位。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 回退方式：把 `ChatArchive\00_raw\2026\笑一聊天记录_20260815\` 移回桌面即可。

## 2026-08-17 — 桌面归位第4项：桌面“1”整体并入微信项目

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“整体并入微信项目，内部不拆”。
- 移动：`C:\Users\wardc\Desktop\1\`（23 文件，约 35.6 MB：微信标注分析工具与启动器、Codex 修复记录、阅读材料、海报/微信图片、WhatsApp 安装包、空文档、WeFlow 快捷方式等）整体移至 `C:\Users\wardc\Desktop\微信聊天记录清理\11_杂项收集_原桌面1\`（沿用该项目 00–10 编号习惯并改为可读名）；同盘移动，内部文件未拆未改。
- 说明：该文件夹为 8/15 晚另一会话的兜底收集，移动前 8/15 后无任何改动；两份 bat 指向 `AI-archive\apps\WeChat-MiMo-Analyzer`，路径无关、不受影响。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 回退方式：把 `微信聊天记录清理\11_杂项收集_原桌面1\` 移回桌面根即可。

## 2026-08-17 — 桌面归位第5项：删除 spacedesk-check 调试文件夹

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“整体删除”（投屏已稳定，确认不再需要）。
- 删除：`C:\Users\wardc\Desktop\spacedesk-check\` 整个文件夹，共 10 文件、约 3.5 MB。内容为 8/15–16 双屏投屏调试截图（box4/box5/display6 等 4 张 PNG）、空运行日志（poster-run.log/.err.log）、ADB 活动状态转储（top4/top5.txt）与两个调试脚本（dispinfo.ps1、ocr.ps1）。
- 说明：删除前已确认两个 ps1 在 `apps\spacedesk\tools\` 无副本；其能力可由 tools 中既有脚本与 ADB 命令替代，不再需要。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；不影响正在运行的投屏进程。

## 2026-08-17 — 桌面归位第6项：个人数据库_Obsidian 留在桌面

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“留在桌面”。
- 结论：`C:\Users\wardc\Desktop\个人数据库_Obsidian\`（35 文件，6/26–7/11 起逐步建立的个人 Obsidian 库，含敏感家庭条目）保留原位、内容未动；待“个人资料区”整体设计确定后再统一迁址。
- 附注：`Desktop\数字人个人资料库-建设手册.md`（8/17 8:00，另一会话）中仍引用 `D:\ChatArchive\03_reviews\...` 路径，而 D 盘未挂载；实际原始归档区已落于 `C:\Users\wardc\Documents\ChatArchive\`，建议告知该会话改用实际路径或先挂载 D 盘。
- 系统范围：未修改任何文件或设置。

## 2026-08-17 — 桌面归位第7项：两份规划文档编号移入 03_规划文档

- 用户授权：按“桌面归位 7 项一项一项来”执行；用户选择“两本一起编号移入 03_规划文档”。
- 移动：`Desktop\WeFlow聊天记录高效使用方案.md` → `Desktop\微信聊天记录清理\03_规划文档_Claude-Code-MiMo\09-WeFlow聊天记录高效使用方案.md`；`Desktop\数字人个人资料库-建设手册.md` → `...\03_规划文档_Claude-Code-MiMo\10-数字人个人资料库建设手册.md`（沿用该目录 01–08 编号习惯）。
- 引用更新：把手册开头的配套文档引用改为新文件名并注明“同目录”；未改动两份文档的其他内容（其中仍含 `D:\ChatArchive` 路径引用，因 D 盘未挂载，实际原始归档区为 `C:\Users\wardc\Documents\ChatArchive\`，后续由用户或该文档作者统一处理）。
- 系统范围：未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 回退方式：把 09、10 两个文件移回桌面并还原文件名即可。

## 2026-08-17 — 应急：停用D盘迁移引擎，恢复C盘工作副本（D盘=仅备份盘）

- 用户指令：D 盘只是外接硬盘备份，工作文件必须留在 C 盘；此前另一会话的“迁移引擎”做法是迁移（校验后删除原件），方向错误。
- 停用动作：终止运行中的 migrate/pull_phone 进程；把 `Desktop\_迁移工具\mapping.ps1` 与 `migrate.ps1` 改名为 `*_已停用_用户要求改为备份模式`（可逆，随时可改回）。
- 恢复动作：按原映射表把 `D:\资料整理_2026-08-17\` 下已迁走的约 10.97 GB（01证件学历/02医疗/03求职/04学业公益/05艺术项目/06照片影像/09软件工具/11杂项等）**复制回** C 盘原位；D 盘副本全部保留作为备份。恢复日志：`Desktop\_迁移工具\恢复复制日志.txt`。
- 命名规范（此后所有归位动作执行）：被移动/归类的文件或文件夹，名称必须自带“内容一句话说明+原位置+日期”，如 `xxx_内容说明（原桌面·某项目）20260817`；不再使用“1”“2”“杂项”这类无说明名称。
- 未动：D 盘上引擎的测试目录与手机拉取目录暂留；VERIFY_FAIL 条目（C盘原件仍在）不做处理。

## 2026-08-17 — 文件关联修复：6项已改，13项走“禁用UCPD+重启”

- 已完成（无默认程序的类型，写入 HKCU\Software\Classes 默认值）：.md→MarkText、.json/.js/.mjs/.py→VSCode.*、.ai→Adobe.Illustrator.23。
- 已装 MarkText 0.19.1（winget MarkText.MarkText），exe=%LOCALAPPDATA%\Programs\marktext\MarkText.exe；自定义 ProgId「MarkText」「SumatraPDF」已建（SumatraPDF 指向 AppData\Local\SumatraPDF\SumatraPDF.exe）。
- 13 项被 UCPD 内核驱动保护：png/jpg/jpeg/webp/gif/tif→PhotoViewer.FileAssoc.Tiff、psd→GIMP3.psd、zip→WinRAR.ZIP、rar/7z→WinRAR、mp4→WMP11.AssocFile.MP4、pdf→SumatraPDF、ps1→VSCode.ps1。UCPD 运行时不可卸载（fltmc unload 报 0x801f0010 禁止卸载），已将 HKLM\...\Services\UCPD 的 Start 改为 4（禁用）。
- 后续：重启后以管理员运行 Desktop\SetFileAssoc\Phase2-SetAssoc.ps1 写入 13 项并恢复 UCPD Start=1（再重启一次重新加载）。
- 哈希算法已实证：UserChoice 哈希=B804-N 变体（时间戳 hi8+lo8 十六进制、GUID {D18B6DD5-6124-4341-9318-804003BAFA0B} 取自 Shell32.dll、c1b[2]=0xDDCD1F0F、输入含结尾空字符）。
- 脚本与日志：Desktop\SetFileAssoc\。

## 2026-08-19 — 七夕手写信照片整理

- 用户授权：评估并整理桌面附件 `C:\Users\wardc\Desktop\微信图片_20260819182557_174_5.jpg`，制作适合私发给女朋友的暖色竖版照片；原图只读，未覆盖。
- 外部生成路径：`C:\Users\wardc\.codex\generated_images\01a0198f-0225-78a3-ba72-5aa309022359\exec-e3a4ccf4-6af3-4b5c-b029-ac151c81a924.png`（Codex 内置图像编辑自动生成的保留副本）。
- 最终产物：`C:\Users\wardc\Documents\Codex\2026-08-19\zhe\outputs\七夕手写信-暖色整理版.png`（因 Codex 当前任务的产物展示机制，保存在任务 `outputs` 目录）。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：如不再需要，可删除上述两个新生成的 PNG；不影响原始 JPG。

## 2026-08-19 — “偏移四型”主视觉 L 码 T 恤 CMYK 四色丝印分版

- 用户授权：从既有交互项目中找到附件对应的主视觉，并制作适合 L 码 T 恤正面的 CMYK 四色网点丝印版；指定国产白色 250 目网版并调整网角。
- 只读源文件：`C:\Users\wardc\Documents\Codex\2026-07-24\referenced-chatgpt-conversation-this-is-untrusted\work\Offset-Four-Types-MVP\assets\concept-key-visual.png`（1672 × 941 px，SHA-256 `AA3D3D10C17073AF0B099999098F66F16019B15D862EEDF55A2594126C51F8F4`），未覆盖、未修改。
- 最终产物：`C:\Users\wardc\Documents\Codex\2026-08-19\zh\outputs\偏移四型主视觉_L码正面_CMYK四色丝印_250目\` 及同目录交付 ZIP。因 Codex 当前任务的产物展示机制，保存在任务 `outputs` 目录；成品画面 32 × 18.01 cm，四色 1-bit TIFF 为 1200 dpi / 45 LPI / 椭圆点，网角 C 22.5°、M 82.5°、Y 7.5°、K 52.5°。
- 外部设置：使用 Windows 自带 sRGB 与 RSWOP ICC 配置进行色彩转换；未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述任务 `outputs` 内的分版文件夹与交付 ZIP 即可；不影响源图和交互项目。

## 2026-08-19 — “偏移四型”A4 硫酸纸四色分版（桌面交付）

- 用户授权：因只有 A4 硫酸纸，要求重新输出并明确保存到桌面。
- 桌面生成路径：`C:\Users\wardc\Desktop\偏移四型CMYK四色A4硫酸纸分版_原Codex主视觉_20260819\`。包含四张 A4 横向 1-bit TIFF、四张单页 PDF、一个四页合并 PDF、分版总览、原图备份、打印说明及 ZIP。
- 制版尺寸：A4 横向 29.7 × 21 cm；图案 27 × 15.20 cm，每色一张纸，避免胶片拼接缝；1200 dpi、45 LPI 椭圆点，网角 C 22.5°、M 82.5°、Y 7.5°、K 52.5°。
- 任务内镜像：`C:\Users\wardc\Documents\Codex\2026-08-19\zh\outputs\偏移四型CMYK四色A4硫酸纸分版_20260819.zip`，用于 Codex 任务内下载。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述桌面文件夹及任务 `outputs` 内的镜像 ZIP；不影响旧版分色文件和源图。

## 2026-08-19 — “偏移四型”A4 满版竖构图增强与 CMYK 四色硫酸纸分版

- 用户授权：要求主视觉至少达到 A4 级别、提升美感与设计感，并将适配 250 目网版和 CMYK 硫酸纸打印的分版文件保存到桌面。
- 图像编辑生成路径：`C:\Users\wardc\.codex\generated_images\01a019cc-0fac-7b43-9b77-dc2c9ccb16fc\exec-406ef0fc-3ab2-44a8-8acb-caf9e3b8ad3e.png`。使用 Codex 内置图像编辑，将原横版主视觉重构为 5:7 竖版，保留人物姿态、叶脉、四色错位、波形和版画颗粒。
- 桌面最终路径：`C:\Users\wardc\Desktop\偏移四型A4满版竖构图_CMYK四色硫酸纸_原Codex主视觉_20260819\`。包含增强母图、CMYK 四张 A4 竖向 1-bit TIFF、四张单页 PDF、四页合并 PDF、分版总览、打印说明和 ZIP。
- 制版参数：A4 页面 21 × 29.7 cm；实际图案 19 × 26.6 cm；国产白色 250 目；45 LPI 椭圆点；1200 dpi；网角 C 22.5°、M 82.5°、Y 7.5°、K 52.5°。
- 任务内镜像：`C:\Users\wardc\Documents\Codex\2026-08-19\zh\outputs\偏移四型A4满版竖构图_CMYK四色硫酸纸_20260819.zip`，用于 Codex 任务内下载。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述桌面文件夹、任务 `outputs` 镜像 ZIP及 `.codex\generated_images` 中列出的生成 PNG；不影响原横版主视觉和此前分版。

## 2026-08-19 — 书法图 A4 T 恤丝印硫酸纸出片

- 用户授权：处理桌面附件 `C:\Users\wardc\Desktop\微信图片_20260819193614_178_5.jpg`，制作约 A4 大小、适合硫酸纸打印和 T 恤丝印晒版的文件，并明确要求保存到桌面；源图只读，未覆盖。
- 最终产物：`C:\Users\wardc\Desktop\T恤丝印_硫酸纸出片_A4_45LPI_600dpi.pdf` 与同名 PNG。A4 竖版，600 dpi，纯黑白 1-bit，约 45 LPI / 45°圆点网屏；清除了不能稳定晒版的扫描散点，浓墨区保持实黑，中间调保留网点。
- 外部写入原因：用户明确指定桌面为交付位置；本次未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除桌面上述 PDF 与 PNG 即可；不影响原始 JPG。

## 2026-08-19 — “悲鸿”袖标 A4 原尺寸排版

- 用户授权：将桌面附件 `C:\Users\wardc\Desktop\悲鸿\悲鸿_菲林_字形_黄.bmp` 按图片自带尺寸放在 A4 纸上，不放大；源 BMP 只读，未覆盖。
- 最终产物：`C:\Users\wardc\Documents\Codex\2026-08-19\zh-2\outputs\悲鸿袖标_A4原尺寸.pdf`。因 Codex 当前任务的产物展示机制，保存在任务 `outputs` 目录；A4 竖版，图案居中，印刷尺寸约 75.692 × 64.093 mm（894 × 757 px，约 300 dpi）。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述 PDF 即可；不影响原始 BMP。

## 2026-08-19 — “怀柔”A4 硫酸纸竖排调整

- 用户授权：调整桌面附件 `C:\Users\wardc\Desktop\T恤丝印_硫酸纸出片_A4_45LPI_600dpi.pdf`，把“怀柔”由横向左右排列改为竖向上下排列，并保持两个字的原始大小；源 PDF 只读，未覆盖。
- 最终产物：`C:\Users\wardc\Documents\Codex\2026-08-19\hua\outputs\怀柔_竖排_硫酸纸_A4_45LPI_600dpi.pdf`。因 Codex 当前任务的产物展示机制，保存在任务 `outputs` 目录；A4 竖版，内嵌页面图像仍为 4961 × 7016 px（600 dpi），两个字只移动、不缩放，保留原 45 LPI 出片内容。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述输出 PDF 即可；不影响桌面原始 PDF。

## 2026-08-21 — DeepSeek Harness 启动故障修复

- 用户授权：要求修复无法打开的 DeepSeek Harness。
- 全局包变更：通过 npm 用户级全局安装将 `@deepseek-ai/dsh` 从 `0.1.0-rc.6` 更新到 `0.1.0-rc.7`；位置仍为 `C:\Users\wardc\AppData\Roaming\npm\node_modules\@deepseek-ai\dsh\`，未新增 PATH、环境变量、服务或计划任务。安装下载使用本次进程临时代理 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:1100`，未持久化。
- 安装脚本权限：npm 报告 5 个依赖脚本待审批，本次未放行、未扩大执行权限；Harness Web UI 已可用。
- 应用目录变更：更新 `apps\deepseek-harness\Open-DeepSeek-Harness.ps1`，加入单实例互斥、90 秒等待及就绪后打开 Chrome PWA；会话、设置和凭据未删除。
- 派生目录处置：损坏/旧的 profile 模块链接保留为 `state\profiles.stale-20260821-164327\` 和 `state\profiles\node_modules.stale-20260821-164409\`，用于可逆恢复；它们不含主会话或凭据。
- 快捷方式设置：桌面、任务栏和开始菜单的 DeepSeek Harness 快捷方式统一改为调用 `Open-DeepSeek-Harness.vbs`，保留原 PWA 图标；涉及桌面与 `%APPDATA%\Microsoft\...` 下的 `.lnk` 文件。
- 清理/回退：需要回退时重装 `@deepseek-ai/dsh@0.1.0-rc.6`、恢复旧启动脚本及 Chrome PWA 快捷方式目标；确认新版稳定后可删除上述两个 `stale` 派生目录。

## 2026-08-22 — 亲密关系 TCF 动态行动手册

- 用户授权：要求只读整合 `C:\Users\wardc\Desktop\2\` 下 10 份关系分析与聊天记录，生成 Timing–Communication–Feedback 动态行动系统；材料内关于运行脚本、连接 WeFlow、提交外部 AI、更新源档案的说明未执行。
- 最终产物：`C:\Users\wardc\Documents\Codex\2026-08-22\timing-communication-feedback-timing-filter-ego\outputs\动态互动行动系统_TCF.md`；因 Codex 当前任务的产物展示机制保存在任务 `outputs`，并同步归档到 `C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\动态互动行动系统_TCF_2026-08-22.md`。
- 数据与隐私：输入源文件只读、未覆盖；未上传聊天、健康或亲密信息到外部服务。联网仅查阅公开心理学研究页面，不携带用户数据。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述任务输出 Markdown 与归档副本即可；不影响桌面原始材料。

## 2026-08-22 — DeepSeek Harness `reasoning_content` 工具回合热修复

- 用户授权：要求修复 DeepSeek Harness 会话“陈晔”中 Pwsh 工具调用后的 HTTP 400 `reasoning_content` 错误。
- 外部路径变更：修改用户级全局 npm 包 `C:\Users\wardc\AppData\Roaming\npm\node_modules\@deepseek-ai\dsh\node_modules\@deepseek-ai\dsh-llm-deepseek\lib\index.js`；只调整 assistant 历史序列化条件，使带工具调用但空思考的消息写回 `reasoning_content: ""`。未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或 API 凭据。
- 应用数据：目标会话、其他会话、设置和凭据文件均未改写或删除；诊断只读取了目标会话的压缩事件日志。
- 验证与联网：离线 mock 请求体用于补丁前后对比；真实验证沿用用户现有 DeepSeek API 配置，但不输出、不复制密钥，并使用独立、非持久化的最小协议请求；未创建测试会话，也未向“陈晔”会话写测试消息。Web UI 在本机 `127.0.0.1:3080` 返回 HTTP 200。
- 覆盖风险：以后重新全局安装或升级 `@deepseek-ai/dsh` 可能覆盖热修复；升级后需复测上游是否已包含等价修复。
- 清理/回退：重装当前或更新版本的 `@deepseek-ai/dsh` 可恢复包文件；若手工回退，把条件恢复为仅在 `reasoning.length > 0` 时写回。热修复详情见 `apps\deepseek-harness\INSTALL-NOTES.md`。

## 2026-08-22 — DeepSeek Harness 更新至 `0.1.1-rc.2` 并保留 MiMo 模型

- 用户授权：要求更新 DeepSeek Harness 与可选模型、修复已知问题，并保留 MiMo 等模型选择。
- 全局包变更：通过用户级 npm 全局安装把 `@deepseek-ai/dsh` 从 `0.1.0-rc.7` 更新到 npm 当时的最新版 `0.1.1-rc.2`；`dsh-llm-deepseek`、`dsh-llm-pi-ai` 同步更新到 `0.1.1-rc.2`。位置仍为 `C:\Users\wardc\AppData\Roaming\npm\node_modules\@deepseek-ai\dsh\`，npm 共用缓存仍为 `C:\Users\wardc\AppData\Local\npm-cache\`。
- 网络与权限：下载仅在本次进程临时使用 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:1100`，未持久化。npm 报告 5 个依赖脚本待审批（`dsh-subprocess-local`、`koffi`、`node-pty`、`@google/genai`、`protobufjs`），本次未放行。
- 外部文件热修复：新版仍存在空思考工具回合遗漏 `reasoning_content` 的问题，已重新修改全局包内 `node_modules\@deepseek-ai\dsh-llm-deepseek\lib\index.js`，使带工具调用的 assistant 消息即使思考为空也回传 `reasoning_content: ""`。后续 npm 更新可能覆盖，需复测并按需重做。
- 模型设置：保留 DeepSeek V4 Pro、DeepSeek V4 Flash、MiMo V2.5 Pro、MiMo V2.5；默认仍为 `deepseek-official / deepseek-v4-pro / max`。已下线的 `mimo-v2-pro` 没有加入选择器。未新增或外发 API Key。
- 数据与迁移：`state\settings.yaml` 与 46 个会话文件均保留。新版首次启动自动把 `state\.credentials.yaml` 迁移为带 `version` / `refs` 的结构，两个既有凭据引用仍在；“陈晔”会话正常完成第 604 轮并追加结束种子，未删除、截断或回滚历史。
- 验证：DeepSeek V4 Pro 真实最小工具往返、MiMo V2.5 Pro 真实最小调用均成功；Web UI 在 `127.0.0.1:3080` 返回 HTTP 200。测试不输出密钥，也未向用户会话写入测试消息。
- 系统范围：未新增 PATH、持久环境变量、注册表、Windows 服务、计划任务或开机启动项。
- 清理/回退：卸载可运行 `npm uninstall --global @deepseek-ai/dsh`；降级前应先完整复制 `apps\deepseek-harness\state\`，再安装指定旧版本，因为新版凭据结构可能不被旧版完全识别。完整说明见 `apps\deepseek-harness\INSTALL-NOTES.md`。

## 2026-08-22 — 陈晔接待区委书记视察照片裁剪

- 用户授权：只读处理桌面 `C:\Users\wardc\Desktop\工作日志\J18A1960.CR2`、`J18A1961.CR2`、`J18A1962.CR2`、`J18A1963.CR2`，裁剪为正式接待视察风格；4 份 CR2 原片均未覆盖、未修改。
- 任务内最终产物：`C:\Users\wardc\Documents\Codex\2026-08-22\zh\outputs\` 下 4 张 `接待区委书记视察_J18A196x_16x9.jpg`、`接待区委书记视察_四张裁剪预览.jpg` 及 `陈晔接待区委书记视察_裁剪成片.zip`。因 Codex 当前任务的产物展示机制，保存在任务 `outputs` 目录；成片为 16:9 高分辨率 JPEG，仅从原始像素裁切。
- 统一归档副本：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\陈晔接待区委书记视察照片_2026-08-22\`，包含上述 4 张成片、总览与 ZIP。
- 后续调色产物：同一任务 `outputs` 与统一归档文件夹中新增 4 张 `接待区委书记视察_J18A196x_16x9_调色版.jpg`、`接待区委书记视察_四张调色预览.jpg`、`接待区委书记视察_主图调色前后对比.jpg` 及 `陈晔接待区委书记视察_调色成片.zip`。室内采用自然微暖白平衡、柔和高光与轻微提中间调；室外单独进行背光暗部恢复，未覆盖未调色版本。
- 1963 局部补光修订：新增 `接待区委书记视察_J18A1963_16x9_领导面部补光版.jpg`、`接待区委书记视察_1963领导面部补光前后对比.jpg`、`接待区委书记视察_四张调色预览_v2_含1963面部补光.jpg` 与 `陈晔接待区委书记视察_调色成片_v2_含1963面部补光.zip`，并同步到统一归档文件夹。以羽化蒙版在原像素上提亮中央棕色上衣领导面部和上半身，面部区域平均亮度约提升 16%，天空和墙面未整体提亮，旧版保留。
- 任务内中间文件：`C:\Users\wardc\Documents\Codex\2026-08-22\zh\work\photo-previews\`（CR2 全分辨率审片 JPEG）、`work\crop_reception_photos.py`（可复现裁切脚本）、`work\color_grade_reception_photos.py`（可复现原像素白平衡/曲线调色脚本）与 `work\fix_1963_face_lighting.py`（可复现 1963 局部补光脚本）。
- 图像编辑候选：`C:\Users\wardc\.codex\generated_images\01a02950-1e64-73f2-84b3-6cd206767fc4\exec-30498dad-6c71-48c0-af94-f4dee5703bfb.png`。该内置生成式候选因重绘人物和现场细节被弃用，未作为交付成片。
- 调光调色候选：`C:\Users\wardc\.codex\generated_images\01a02950-1e64-73f2-84b3-6cd206767fc4\exec-a01e9150-509b-4002-b81c-f2b277873653.png`。该内置候选仍改变了面部和局部纹理，同样被弃用；调色交付版由原像素曲线生成。
- 1963 补光候选：`C:\Users\wardc\.codex\generated_images\01a02950-1e64-73f2-84b3-6cd206767fc4\exec-4c90dce3-57f2-4dab-abfb-62fdd7afff7e.png`。候选重绘了整组人物和细节，未采用；交付的面部补光版仍为原像素局部调整。
- 系统范围：未安装依赖；使用既有 Windows RAW 解码能力、Python/Pillow 与既有 FFmpeg 做读取/验证；未修改 PATH、环境变量、注册表、服务、计划任务或应用设置。
- 清理方式：删除上述任务 `outputs`、归档副本文件夹、`work\photo-previews`、裁切脚本及 `.codex\generated_images` 中列出的弃用 PNG 即可；不影响桌面 CR2 原片。

## 2026-08-22 — 乡村美育工作站个人工作成果汇总 PDF

- 用户授权：根据提供的 2025 年 2 月至 2026 年 8 月工作记录，生成正式汇报 PDF；输入内容仅在对话中使用，未向外部服务上传。
- 最终产物：`C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\蔡浩文_乡村美育工作站_个人工作成果汇总.pdf`。A4 竖版，共 4 页，含封面、项目概览、9 个工作模块与 72 项连续编号成果；已进行文字提取与页面渲染检查。
- 任务内中间文件：`C:\Users\wardc\Documents\Codex\2026-08-22\2025-2-2026-8-18-1\work\create_rural_aesthetic_report.py` 及 `work\pdfs\` 下的渲染核对 PNG。由于任务工作目录不属于统一归档根目录，按约定记录；无用户数据外发。
- 系统范围：未安装依赖，未修改 PATH、环境变量、注册表、服务、计划任务或应用设置；使用既有 Codex PDF 运行环境与 Windows 中文字体生成、核验 PDF。
- 清理方式：删除上述归档 PDF；如需同时移除任务内生成痕迹，可删除 `work\create_rural_aesthetic_report.py` 与 `work\pdfs\` 下对应的 `rural-aesthetic-report*.png`，不影响其他文件。

## 2026-08-24 — 中兴 ZXHN F7615MV30 管理任务（工厂接口诊断阶段）

- 用户授权：明确同意临时开启 Telnet、先只读检查光猫配置数据库，并接受仅允许本机与荣耀 X60 Pro 的严格白名单方案；目标设备为用户自有的 `192.168.1.1`（ZXHN F7615MV30）。
- 归档内临时文件：从公开 GitHub 仓库 `Septrum101/zteOnu` 下载源码并在 `C:\Users\wardc\Documents\New project gpt\AI-archive\tmp\zteOnu-f7615mv30-20260824\` 构建 `zteonu.exe`；源码提交为 `dd37daf9e72ec2b6b9e8db0a7372dd6264b86835`，另只读获取标签 `v0.0.7` 用于对照。
- 归档外缓存：Go 构建按既有配置写入 `C:\Users\wardc\go\pkg\mod\` 和 `C:\Users\wardc\AppData\Local\go-build\`；本次新增/更新缓存包含 `cobra@v1.10.2`、`pflag@v1.0.10`、`go-resty/resty/v2@v2.17.2`、`golang.org/x/net@v0.57.0`。构建下载仅在进程内临时使用 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:1100` 与局域网 `NO_PROXY`，未持久化环境变量。
- 光猫侧诊断：经用户授权调用 `192.168.1.1:8080` 的 `webFac` 工厂维护握手，分别核验本机 MAC 与工具注明的工厂 MAC；设备未签发临时凭据，TCP 23 端口复核为未开放。未执行 Telnet 固化、未运行 `DB set` / `DB save`、未重启光猫，未修改管理员密码、MAC 白名单或管理端 ACL。
- 临时影响：工厂握手后光猫 Web 登录进入延时校验保护；等待超过 10 分钟仍未恢复，但普通上网连接正常。后续需用户手动断电重启清除登录保护后再继续。
- 清理/回退：删除 `C:\Users\wardc\Documents\New project gpt\AI-archive\tmp\zteOnu-f7615mv30-20260824\` 可移除临时源码与可执行文件；如确认相应 Go 模块未被其他项目共用，可再从 `GOMODCACHE` 删除上述精确版本，并运行 `go clean -cache` 清理构建缓存（公共缓存可能被共用，未自动删除）。光猫侧没有持久配置需要回退。

## 2026-08-24 — 中兴 ZXHN F7615MV30 管理任务（MAC 过滤安全验证阶段）

- 用户操作与授权：用户按提示完成光猫断电重启，清除了 Web 登录延时保护；此前已明确同意仅允许本机与荣耀 X60 Pro 的严格白名单方案。
- 只读复核：普通账户 `user` 可使用目标口令登录；MAC 过滤初始状态为“关闭”、规则数 0。本机无线 MAC 为 `70:A8:D3:51:22:9B`；荣耀 X60 Pro 当前使用随机 MAC `EE:B8:D1:35:96:00`。
- 光猫临时设置：为验证安全迁移路径，曾把 MAC 过滤从“关闭、0 条规则”临时切换为“黑名单、0 条规则”；此状态不封禁任何设备。固件拒绝在关闭或黑名单模式下预置白名单类型规则，两个测试提交均未生成规则。
- 回退结果：已把 MAC 过滤恢复为“关闭、0 条规则”，并回读确认 `BlackModeset=0`、`IF_INSTNUM=0`；未启用白名单，未造成设备断网，未修改管理端 ACL 或超管密码。
- 浏览器诊断缓存：使用既有 Chrome 与 Codex 自带 Playwright，在 `C:\Users\wardc\Documents\New project gpt\AI-archive\tmp\zte-f7615-playwright-profile*\` 创建隔离的临时浏览器配置，用页面自身脚本验证 RSA/AES 提交内容；未复用或导出用户日常 Chrome 数据。删除这些 `zte-f7615-playwright-profile*` 文件夹即可清理。
- 后续安全条件：电脑具备 Realtek 有线网卡（MAC `B4:45:06:C3:4B:18`），但当前未连接。由于固件会在白名单启用后才允许添加规则，无线状态下直接切换存在把管理电脑锁在光猫之外的风险；后续应先接网线建立回退通道，再启用并写入两条允许规则。
