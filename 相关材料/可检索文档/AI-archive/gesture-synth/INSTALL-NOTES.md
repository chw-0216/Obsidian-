# Gesture Synth 本地复现安装记录

## 来源与版本
- 用户指定参考：<https://gesture-synth-weld.vercel.app/>。
- 原项目：<https://github.com/ericwei97-cloud/gesture-synth>，clone 基准 `7ee25ba8c30f0a0cf544835a2dae199e4b7b9484`。
- 本地改编根目录：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\gesture-synth`。
- 保留原始顶层源码副本在 `.upstream`，Git 元数据保留于 `.git`。
- 原仓库 LICENSE 规定个人、教育和非商业用途并署名；商业用途需联系作者。package.json 中 ISC 字段与实际 LICENSE 不一致，按 LICENSE 执行。

## 运行依赖
- 复用已安装系统 Node.js `v24.18.0`、npm `11.16.0`、Git `2.54.0`；本任务未安装或更新这些系统程序。
- npm 包局限于此应用的 `node_modules`：`@mediapipe/tasks-vision@0.10.35`、`vite@8.1.3`。缓存位于应用 `.cache\npm`。安装使用 `--ignore-scripts` 与命令级代理 `http://127.0.0.1:1100`；未运行包安装脚本，未修改持久代理或环境变量。
- Google 官方 Hand Landmarker float16 模型在 `public\models\hand_landmarker.task`，SHA256 `FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1`；同版本 WASM 位于 `public\wasm`。运行时不需要 CDN。
- 网页服务由内置 Node HTTP 模块在 `127.0.0.1:4176` 提供，仅接受本机连接，无系统服务或计划任务。

## 运行和验证
- `START.cmd` 或 `start.ps1` 启动后台服务；启动器在 `.runtime\server.pid` 和日志文件记录进程。`STOP.cmd` 会比对精确脚本路径后停止本项目 Node 进程。
- `npm run build` 已通过。6 项 Node 自动检查通过，涉及和弦、调性、八度、七种指形、手势稳定和停音条件。
- 浏览器试奏确认 C 与 Am 和弦音符显示更新，录制/停止/回放控件可用；矮窗口布局已修正。摄像头和本地模型已成功进入追踪状态。真人演奏的准确性和主观听感需实际操作判断。
- 本机运行没有调用外部 API、统计分析或麦克风。摄像头权限只供这个本地网页在用户启动后使用。录音仅采集合成器输出。

## 本地数据与外部路径
- 本次直接的应用文件改动全在上述应用目录内。浏览器可保存合成声音文件到浏览器默认下载目录（只有用户点“保存录音”时才生成）。站点设置键为 `gesture-synth-local-settings`，位于本机 `http://127.0.0.1:4176` 的浏览器 localStorage；浏览器摄像头授权由浏览器按站点保存。
- 用户要求将项目指南放在桌面：`$desktopGuide`。同一份文件另有 Codex 交付副本 `C:\Users\wardc\Documents\Codex\2026-09-26\ni\outputs\双手成曲_Gesture_Synth项目分析与演奏指南.html` 和 AI-archive 副本 `outputs\双手成曲_Gesture_Synth项目分析与演奏指南.html`。删除这些文档仅会清除此指南。
- 临时编辑目录在 `C:\Users\wardc\Documents\Codex\2026-09-26\ni\work\gesture-synth-local`，验收后可按此路径单独删除。早先暂存的概念稿在 `C:\Users\wardc\.codex\visualizations\2026\09\25\01a0d9c1-08e0-7233-8005-4b7514b610cb\gesture-resonance.html`，已停止采用。
- 无全局 npm 安装，无 PATH/系统环境变量、注册表、AppData、服务、计划任务改动。复用的系统 Node 与 Git 可能供其他软件使用，卸载本项目时不要移除它们。

## 清理
1. 网页点击“结束演奏”，然后双击 `STOP.cmd`。
2. 删除 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\gesture-synth` 可移除此项目源文件、缓存、模型、依赖、构建目录、日志与原始源码副本。
3. 如需完整清理，再删除上节中的指南副本、`work\gesture-synth-local`、已下载录音，并在浏览器设置中移除 `127.0.0.1` 的摄像头许可与站点数据。已下载录音需单独删除。
4. 不用反向清理系统 Node/Git 或任何全局软件，它们不是本次安装产生的。

## 2026-09-26 — 最大应用音量与整曲引导
- 按用户要求将合成器应用输出增益上限调到 1.0，并保留动态压缩；手势演奏与按钮预演的音量均置为最大。没有改动 Windows 主音量、设备音量或系统音频设置。
- 新增原创和弦练习《小旅程》整曲引导：16 小节、4/4 拍、80 BPM；按 C、G、Am、Em、F 的和弦顺序逐节提示单手姿势，匹配后显示四拍节奏并推进，完整一轮约 48 秒。它是一段和弦伴奏练习，不含自动播放的 Yesterday 旋律或歌词。
- 移除左上角品牌标识。重新构建 `dist`，`npm run build` 通过。本次未增加依赖或系统级设置。
- 同步指南副本至桌面 `C:\Users\wardc\Desktop\双手成曲 Gesture Synth 项目分析与演奏指南.html`、Codex outputs 与 AI-archive outputs。
- 回退时恢复本项目 `index.html`、`main.js`、`style.css`、`src\tracking.js`、`src\synth.js` 的 `.upstream` 版本并重建；删除新加的 `src\song.js`。指南副本可分别删除。无需清理全局依赖或系统设置。
## 2026-10-03 — 恢复旧版标识与投影准备
- 按用户最新选择，恢复左上角 Gesture Synth / 双手成曲标识和点击返回首页的交互；保留之前的整曲提示、声音设置与演奏功能。
- 重新执行 npm run build 并启动本机服务，页面 http://127.0.0.1:4176/ 的健康检查返回 gesture-synth-local，首页已显示标识与整曲提示。
- 另一个 HANDSCORE 项目未删除，也未将其作为本次展示页面。
- 为稍后连接井邻设备，已将现有 spacedeskService 从 Disabled/Stopped 改为 Manual/Running；没有安装或升级 spacedesk，没有修改防火墙、PATH 或网络配置。服务只在本次会话启动，重启后不会自动启动。
- spacedesk 更改的回退：以管理员权限执行 sc.exe stop spacedeskService，再执行 sc.exe config spacedeskService start= disabled；恢复此前 Disabled/Stopped 状态。仅在不再使用 spacedesk 时回退。
- 当前本机 WLAN IPv4 为 192.168.1.4/24；井邻设备需在同一局域网中打开 spacedesk Viewer 连接此电脑。投影端尚未连接，画面和远端声音待现场验证。
