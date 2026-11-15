# 双手成曲｜Gesture Synth × 井邻投影复现交接

交接版本：2026-10-03 · Windows 11 · 中文本地改编版

## 1. 接手后先做什么

本次采用的是带左上角 GESTURE SYNTH / 双手成曲标识的旧版 Gesture Synth。现场展示入口为 http://127.0.0.1:4176/。左手选择和弦，右手改变和弦形态、音量和音色，视觉随演奏变化。页面提供自由演奏、声音预演、原创 16 小节和弦引导、录音与回放。

最短启动流程：打开应用文件夹 → 双击 START.cmd → 先试声音 → 开启摄像头并授权 → 井邻 Viewer 连接本机 → Windows 切换复制显示 → 在投影上检查画面和声音。

应用位置：
```text
C:\Users\wardc\Documents\New project gpt\AI-archive\apps\gesture-synth
```

另一项目 apps\handscore / 4177 是此前的新设计，目前用户未选作展示版本。交接与后续修改均以 gesture-synth / 4176 为准。

## 2. 复现需要保留的材料

| 材料 | 用途 |
| --- | --- |
| index.html、style.css、main.js | 中文界面、标识、页面流程与事件连接 |
| src\music.js | 调性、和弦、音符与手势图形 |
| src\tracking.js | 手指姿态、左右手、稳定与停音逻辑 |
| src\synth.js | Web Audio 合成器与输出增益 |
| src\visual.js | 摄像头背景、骨架、和弦色彩与声波 |
| src\song.js | 《小旅程》16 小节和弦顺序与速度 |
| public\models\hand_landmarker.task | 本地 MediaPipe 手部识别模型 |
| public\wasm\ | 同版本 MediaPipe JS / WASM 运行文件 |
| package.json、package-lock.json | 固定的本地依赖与构建命令 |
| dist\、serve.mjs | 已构建页面与本机网页服务 |
| START.cmd、STOP.cmd、start.ps1、stop.ps1 | 启动、停止及运行日志定位 |
| LICENSE、README-CN.md、INSTALL-NOTES.md、.upstream\ | 授权、说明和原始源码参考 |

推荐将整个 gesture-synth 文件夹复制到新电脑的同名应用目录，能够同时带走本地改编源码、模型与构建结果。迁移时不要带走 .runtime\ 下的旧进程编号和日志：在复制目标中省略这个目录，启动器会自动重建。node_modules 可省略，联网后按锁文件重新安装；同一 Windows 架构的完整副本可尝试复用依赖，但构建报错时应重新安装。

**只 clone 原 GitHub 仓库不能复现当前中文本地版。** 原仓库只是改编基础；本地中文引导、16 小节练习、应用音量调整与恢复后的标识都需要这些本地文件。不要用 .upstream 全量覆盖本地源码，否则会丢失本地改编。

原站：https://gesture-synth-weld.vercel.app/

原源码：https://github.com/ericwei97-cloud/gesture-synth

改编基准提交：7ee25ba8c30f0a0cf544835a2dae199e4b7b9484。当前页面不是原站最新版的逐像素复刻，保留的是公开源码的核心手势与合成器基础。

## 3. 在新电脑运行

已记录的原环境：Node.js v24.18.0、npm 11.16.0；@mediapipe/tasks-vision 0.10.35、Vite 8.1.3。为减少版本差异，优先使用相同 Node 版本。只运行现有 dist 时不需要 npm 安装，但仍需要 Node 来运行 serve.mjs。

### A. 完整复制后直接启动

1. 确认 Node 已安装，PowerShell 中 node --version 有输出。
2. 双击 START.cmd。它会启动隐藏的本地服务并打开浏览器。
3. 访问 http://127.0.0.1:4176/，应看到左上角标识和“开启摄像头演奏”“先试试声音”。
4. 在 Chrome 或 Edge 中先点击“先试试声音”，选择 C 和弦，确认声音输出。
5. 结束预演后开启摄像头，允许此 localhost 页面的摄像头权限；不需要麦克风。

网页服务只监听 127.0.0.1。井邻设备通过 spacedesk 接收 Windows 画面，不是通过井邻浏览器访问 127.0.0.1；在另一设备上输入这个地址只会访问它自己。

### B. 需要重建或修改源码

以下命令在 PowerShell 执行；路径按实际复制位置调整。

```powershell
Set-Location -LiteralPath 'C:\Users\wardc\Documents\New project gpt\AI-archive\apps\gesture-synth'
node --version
npm --version
npm ci --ignore-scripts --cache .cache\npm
npm run build
.\START.cmd
```

npm ci 需要联网，会按 package-lock.json 重装本地 node_modules；不安装全局包。若保留的依赖已经可用，可跳过安装，直接构建。代理是原电脑的环境条件：HTTP 1100 / SOCKS 1099，换电脑后应按那台电脑的真实网络配置，不要照抄一个不存在的代理。

本地开发命令是 npm run dev，地址为 http://127.0.0.1:5176/；现场展示仍使用构建后的 4176。修改源码后必须 npm run build，再刷新展示页，才能让 4176 使用新版本。

运行状态可检查：
```powershell
Invoke-RestMethod 'http://127.0.0.1:4176/health'
```
预期 app 为 gesture-synth-local，port 为 4176。日志位置：.runtime\server.log 与 .runtime\server-error.log。

### C. 离线条件

已经带齐 dist、模型、WASM 和 Node 时，页面运行与手部识别不需要 CDN 或在线 AI API。首次 npm 安装、下载 Node、下载 spacedesk 仍需要网络。双手追踪使用摄像头，不调用麦克风；网页中的录音只采集合成器声音。

## 4. 如何演奏与引导完整一轮

### 双手自由演奏

| 左手姿势 | 级数 | C 调示例（配合大小调） |
| --- | --- | --- |
| 1 根手指 | I | C / Cm |
| 2 根手指 | II | D / Dm |
| 3 根手指 | III | E / Em |
| 4 根手指 | IV | F / Fm |
| 5 根手指 | V | G / Gm |
| 食指＋小指 | VI | A / Am |
| 拇指＋食指＋小指 | VII | B / Bm |

左手手腕内倾切换大调，外倾切换小调。右手 1 指为原位、2 指为第一转位、3 指为大七 / 小七、4 指为属七 / 减七；右手伸出拇指降一个八度，上下移动控制音量，倾斜改变明亮度。保持手势持续发声，握拳或移出镜头停音。

两手放在摄像头内，掌心朝向镜头，保持间距和均匀光照。若左右手提示与实际相反，在“设置”中开启“交换左右手”。现场入门优先选“单手入门”，只用左手选和弦，音量固定为应用最大值，避免右手尚未识别时没有声音。

### 《小旅程》整曲提示

点击右上角“整曲提示”，选择摄像头引导或预演。引导自动准备单手入门、原位和弦、标准八度与无半音偏移。以 C 调开始，速度 80 BPM，4/4 拍，共 16 小节，理想情况下每小节约 3 秒，总计约 48 秒；等待首次匹配会延长实际用时。

| 小节 | 段落 | 和弦顺序 |
| --- | --- | --- |
| 1–2 | 引子 | C → G |
| 3–6 | 第一段 | Am → Em → F → C |
| 7–12 | 副歌 | F → G → C → G → Am → Em |
| 13–16 | 尾声 | F → C → G → C |

C：1 指内倾；G：5 指内倾；Am：食指＋小指外倾；Em：3 指外倾；F：4 指内倾。跟随屏幕的手势文字、和弦名称和四拍圆点演奏，完成后可重弹。

当前代码每小节首次匹配后启动四拍计时；计时启动后即使中途换错和弦也会继续推进。它没有持续校验每一拍是否正确，因此不能将“完成”当作准确演奏评分。这是一段原创和弦伴奏练习；没有内置 Yesterday 原唱、旋律、歌词或完整谱面。若要演奏 Yesterday，需要另外准备合法取得的曲谱并按其和弦自由演奏。

## 5. 井邻 spacedesk 投屏复现

### 角色与连接顺序

运行 Gesture Synth 的 Windows 电脑安装 spacedesk DRIVER / Server；井邻的接收设备打开 spacedesk VIEWER。两端位于同一局域网，**Viewer 必须点选服务器或手动输入主机地址并连接**，仅打开 Viewer 不会自动完成投屏。

2026-10-03 本次主机 WLAN 地址为 192.168.1.4；这是当时地址，重连网络或换电脑后可能变化。在主机 PowerShell 查看当前地址：
```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
  Select-Object InterfaceAlias, IPAddress
```

### 主机服务

本次发现 spacedeskService 原为 Disabled / Stopped，已改为 Manual / Running。重启 Windows 后它不会因这个设置自动启动。接手者可在 spacedesk Driver Console 中将服务打开；若仍被禁用，在管理员 PowerShell 中执行：
```powershell
sc.exe config spacedeskService start= demand
sc.exe start spacedeskService
sc.exe queryex spacedeskService
```

预期 STATE 为 RUNNING。本次已有名为 spacedeskService 的入站 Allow 防火墙规则，适用于 Private / Public；没有新增防火墙规则或修改网络分类。换电脑后应检查自己的安装与防火墙配置。

连接判断：查看 spacedesk Driver Console 的 Active Connections；或在主机执行：
```powershell
$projectionProcess = Get-Process -Name spacedeskService
Get-NetTCPConnection -OwningProcess $projectionProcess.Id |
  Select-Object LocalPort, RemoteAddress, State
```

本次观察到服务在 28252 端口监听。Listen 只是准备就绪；出现远端地址及 Established 才说明 Viewer 已建立连接。不要把服务 Running 或浏览器正常显示当成井邻投影已经成功。

### 复制显示与全屏

Viewer 连上后，优先使用 Win + P → 复制；若是扩展显示，投影可能只有空桌面。必要时进入 Windows“设置 → 系统 → 显示”，确认 spacedesk 虚拟屏并选择复制。在浏览器打开本地演奏页，点击右上角全屏或使用独立 Chrome / Edge 的 F11；内嵌浏览器全屏可能受宿主窗口限制，需看投影画面实际是否占满。

本次 DisplaySwitch.exe /clone 没有实际改变拓扑，之后调用 Windows 显示 API 才成功。若普通切换无效，可用以下管理员 PowerShell 后备方法：
```powershell
$displaySwitchSource = @'
using System;
using System.Runtime.InteropServices;
public static class GestureProjectionMode {
  [DllImport("user32.dll")]
  public static extern int SetDisplayConfig(uint pathCount, IntPtr paths,
    uint modeCount, IntPtr modes, uint flags);
}
'@
if (-not ('GestureProjectionMode' -as [type])) {
  Add-Type -TypeDefinition $displaySwitchSource
}
$projectionResult = [GestureProjectionMode]::SetDisplayConfig(
  0, [IntPtr]::Zero, 0, [IntPtr]::Zero, 0x82)
"复制显示返回码：$projectionResult"
```

0x82 表示应用复制拓扑；返回 0 表示 Windows 接受请求。仍要在接收屏查看结果。恢复扩展模式可用 Win + P → 扩展，或在上述脚本已定义类型的同一 PowerShell 中调用：
```powershell
[GestureProjectionMode]::SetDisplayConfig(
  0, [IntPtr]::Zero, 0, [IntPtr]::Zero, 0x84)
```

本次最终查询确认三个活动显示路径共享同一画面源，图形输出报告 1920×1080。两个 Viewer 地址为 192.168.1.3 和 192.168.1.5，反向名称均为 mibox4c 系列；当时没有收到用户对两台设备归属的确认，交接时需要现场核对目标接收屏。

### 声音

画面复制不等于音频一定已传到井邻。先在本机点击“先试试声音”确认合成器；再确认实际使用的 Windows 输出设备、外接音箱 / 投影音响，以及 Viewer 的 Audio Speaker / 音频选项。各平台入口不同，按当前 Viewer 操作。

当前应用输出增益上限为 1.0、预演音量默认最大；这不等于 Windows 主音量、音箱或接收设备音量也为最大。本次没有修改 Windows 音量，远端声音未现场核验。现场应从较低的扬声器音量开始确认输出，再调整到合适响度。

官方参考：
- https://manual.spacedesk.net/EstablishingTheNetworkConnection.html
- https://manual.spacedesk.net/VerifyNetworkConnectionandadditi.html
- https://manual.spacedesk.net/DesktopExtensionorDesktopDuplic1.html
- https://manual.spacedesk.net/AudioSpeaker.html

## 6. 常见问题与处理顺序

| 现象 | 处理 |
| --- | --- |
| 4176 无法访问 | 双击 START.cmd；查看 .runtime\server-error.log；确认 Node 与 dist 存在，以及端口是否被其他程序占用 |
| 页面可开但旧改动没出现 | 执行 npm run build，再刷新 4176；不要把 5176 开发页面与展示服务混淆 |
| 没有声音 | 先点“先试试声音”解锁 Web Audio，点击和弦；确认静音关闭、Windows 输出设备正确；双手模式要右手入镜并伸指，入门可改为单手模式 |
| 摄像头打不开 | 允许此站点摄像头、关闭其他占用摄像头的程序；检查 USB 摄像头是否接好 |
| 手势不稳定或左右反了 | 改善光照、避免遮挡、两手分开；设置里交换左右手；先用单手与 C 和弦练习 |
| Viewer 已打开但没画面 | 在 Viewer 点选本机或输入当前 IP；确认同网、服务 RUNNING、防火墙许可；检查是否有 Established 连接 |
| 接收屏是空桌面 | Windows 可能处于扩展模式，切复制，或将独立浏览器窗口移到接收屏 |
| 投影黑屏或 Display OFF | 在 Windows 显示设置确认虚拟屏已附加、不是断开的显示器；必要时重新连 Viewer 后再切复制 |
| 画面有延迟 | 先降低接收端分辨率、改善 Wi-Fi / 改有线；手势在主机计算，Wi-Fi 投影会额外增加画面延迟，未做端到端延迟实测 |
| 提示完成但弹错了 | 当前整曲引导只在每小节首次匹配时启动计时，没有逐拍持续校验；按第 4 节说明理解其边界 |
| 录音刷新后没了 | 录音先存于当前会话；刷新前点击“保存录音”；下载只含合成器声音 |

## 7. 现场开场与收场

开场依次确认：带标识的 4176 页面、C 和弦有声音、摄像头与手势、Viewer 的 Established 连接、目标屏复制显示、全屏、现场音响。《小旅程》建议先用单手引导，熟悉后再切双手自由演奏。复制模式会显示本机当前桌面内容；演出期间将演奏页面置于前台。

收场：先保存需要的录音 → 页面“结束演奏”释放摄像头 → Viewer 断开 → 按需求恢复扩展 / 仅主屏 → 双击 STOP.cmd 停止本地网页服务。停止项目服务不会自动停止 spacedesk，两者分别处理。

如果要恢复本次准备之前的 spacedesk Disabled / Stopped 状态，在管理员 PowerShell 中执行：
```powershell
sc.exe stop spacedeskService
sc.exe config spacedeskService start= disabled
```

这会断开所有 spacedesk Viewer；仍需使用投屏时不要执行。复制目标中的 .runtime 可重新生成；录音下载文件、浏览器站点数据与摄像头许可在应用文件夹之外，完整清理时需另行处理。Node 与 Git 是共用软件，不能随项目删除。

## 8. 已确认与尚未确认

| 项目 | 证据与边界（截至本次交接） |
| --- | --- |
| 标识与页面 | 2026-10-03 已恢复，重新构建通过，首页 HTTP 200，health 为 gesture-synth-local |
| 演奏界面 | 摄像头演奏阶段已运行，页面静音状态为 false；主观听感和真人准确性需现场判断 |
| 本地材料 | 源码、dist、模型与 WASM 均在 gesture-synth 应用目录；模型与源码关键哈希见附录 |
| 投屏连接 | 已观察到两个 MiBox Viewer 的 Established 连接；两台是否均属于井邻尚未确认 |
| Windows 复制 | API 返回 0，随后查询显示三个活动路径共享同一 source；不能代替接收屏的现场目视检查 |
| 全屏 | 内嵌浏览器全屏状态未稳定确认，现场需检查边缘是否仍显示宿主界面 |
| 远端音频 | 未确认井邻端实际出声；需要检查 Viewer 音频选项与现场音响 |
| 新电脑复现 | 文档基于现有应用文件与本次操作记录，未在另一台全新电脑完成安装与现场验收 |

## 9. 修改、授权与交接记录

修改界面主要看 index.html / style.css；修改手势看 src\tracking.js；音色与输出看 src\synth.js；视觉看 src\visual.js；和弦引导看 src\song.js 及 main.js 中的 updateSongPrompt。变更后重新构建并检查 4176。不要把 UI 中的“最大音量”当成系统音量控制。

若后续需要严格完整音乐演奏，可在当前基础上增加逐拍匹配、错误提示、旋律音轨 / 授权谱面和节拍伴奏。它们属于待开发能力，当前版本未实现。

原 LICENSE 允许个人、教学和非商业使用、修改与分享，须署名 Gesture Synth / Eric Wei。商业使用需取得作者许可。保留 LICENSE、页面作者链接与源码来源；音乐曲谱与录音的授权另行确认。

应用安装记录：apps\gesture-synth\INSTALL-NOTES.md。

统一设置变更记录：C:\Users\wardc\Documents\New project gpt\AI-archive\permissions-settings-log.md。

本交接资料默认归档到：C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\双手成曲_井邻投影复现交接_20261003。

## 附录：当前关键文件 SHA-256

用于确认复制的是本地改编版本；哈希在本次生成文档时读取。

| 文件 | SHA-256 |
| --- | --- |
| index.html | F40442F9568865CDE67699F76F735A097792BDCDE61D1C7644B93046689651DD |
| main.js | 94EA612242B19DCD1E80CF5DFB6780A63C88A7C166ABEF6A7B1437F28A0D5577 |
| style.css | 7C1FE737D0C7404B909C82CE1B082A5B78A2DA2BEB4B9632DC97E5B851671AB2 |
| src/song.js | B3D7BAD471D4EA37AB436100093FA647A38B6B831508642F9C387745670C8C0C |
| src/tracking.js | 0E12492E286EA897F4F0964E684E777F467D97F13E5CBCAF76D3CA5709E0A6A9 |
| src/synth.js | 9074291177A467CDF9B47826C9B332C8C761DF56CB3D16D6481BC1AF742B6995 |
| src/visual.js | A06E004688C1AD59FC43A1AEF6AAD157622E41C430CDD611ADEAC5BFEEAD45DF |
| package-lock.json | 6FFAF18AB1A328B9CCEDE7F069F8E2858ECC115B966ECC27B994D221376CF44F |
| public/models/hand_landmarker.task | FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1 |
