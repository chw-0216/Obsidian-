---
tags: [管道, WeFlow, 部署方案, SOP]
created: 2026-09-27
updated: 2026-09-27
---

# 🔄 WeFlow 聊天记录更新 · 部署方案

> 目标：把「微信加密库 → 可分析 JSON」这条链路的**更新动作**固化下来，随时可跑、跑完可验证、坏了能修。
> 相关：[[分析流水线]]（批量 472 人链路）｜[[原始数据源索引]]｜[[数据源地图]]｜[[笑一-沟通作战手册_20260927]]

---

## 0. 一句话结论

> **日常更新 = 跑 `sync_weflow.py --who 笑一`（增量、秒级、不重启 WeFlow）。**
> **只有换 token / 修 -105 / 全量重拉时，才动 `一键更新聊天记录.bat`（会重启 WeFlow，约 1 分钟）。**

---

## 1. 环境事实（已实测核对 2026-09-27 21:24）

| 项目 | 值 |
|---|---|
| API 基址 | `http://127.0.0.1:5031`（仅监听 127.0.0.1，外网不可达） |
| Token | `wf-04eb74eee9324f5a918832b955384c25` |
| 健康检查 | `GET /api/v1/health` → `{"status":"ok"}` |
| 进程 | `WeFlow.exe`（本次 PID 18908），端口 5031 LISTENING |
| 可执行文件 | `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe` |
| 配置文件 | `C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json` |
| 我的 wxid | `wxid_zn4ozsnn8esr21` |
| 笑一 wxid | `wxid_wdnk6ue9kiyn22` |
| 数据落点 | `C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\笑一.json` |
| 水位文件 | 同目录 `_sync_state.json` |
| 会话列表 | `GET /api/v1/sessions?limit=1000` |
| 消息接口 | `GET /api/v1/sessions/{wxid}/messages?limit=5000[&since=][&offset=]` |
| ⚠️ 只读性 | 已反查 `app.asar` 全部路由：**无任何发送接口**。此链路只能读，不能发 |

---

## 2. 三条链路对比（选哪条）

| | **A. 一键 bat**（重量级） | **B. sync_weflow.py**（推荐·日常） | **C. 手工 API**（排查用） |
|---|---|---|---|
| 入口 | `Desktop\笑一\一键更新聊天记录.bat` | `python sync_weflow.py --who 笑一` | `curl` 直连 |
| 是否重启 WeFlow | **是**（杀进程 → 等 22s 重启） | 否 | 否 |
| 耗时 | ~1 分钟 | **< 2 秒** | 秒级 |
| 模式 | 全量覆盖 | **增量**（水位推进） | 任意 |
| 输出 | `Desktop\笑一\01_最新聊天记录\`（json+md+txt） | `Desktop\07_聊天记录分析\weflow_live\笑一.json` | 临时文件 |
| 适用 | 换 token / 修 -105 / 全量重拉 / 数据落点搬家 | **每天日常更新** | 定位问题、验水位 |
| 风险 | 重启中断正在进行的导出；22s 等待期内 API 不可用 | 无 | 无 |

> **判断规则**：只要 WeFlow 还开着、`/health` 返回 ok → **永远走 B**。A 是"重锤"，别当日常用。

---

## 3. 标准操作 SOP

### 3.1 日常更新（每天 1 次，30 秒）

```bash
cd "C:/Users/wardc/.workbuddy-ai/skills/wechat-data-forensics/scripts"

# 关键：先清代理变量，否则 urllib 会被 http_proxy 劫持
http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= all_proxy= ALL_PROXY= \
  "C:/Users/wardc/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe" \
  sync_weflow.py --who 笑一
```

**预期输出**：
```
✅ WeFlow API 在线
待同步 1 个会话
  ✓ 笑一                            N 条 (累计 M)
本次新增 N 条 → ...\weflow_live
```
- `无新消息` = 她没发也没收（正常，不代表故障）
- 跑完立刻做 §7 的四项校验

### 3.2 全量重拉（数据错乱 / 首次建库时）

```bash
python sync_weflow.py --who 笑一 --full
```
> `--full` 会**覆盖** `笑一.json`。跑前先复制一份备份。

### 3.3 只列会话（确认 wxid / 昵称变了没）

```bash
python sync_weflow.py --list
```

### 3.4 重量级修复（-105 / 换 token / 落点搬家）

双击 `Desktop\笑一\一键更新聊天记录.bat`。它会：
1. 读 `WeFlow-config.json`，备份原状态
2. 生成新 token 并写入配置、开启 `httpApiEnabled`
3. **杀掉 WeFlow 进程 → 等 2s → 重启 → 等 22s**
4. 分页拉全量 → 覆盖写 `01_最新聊天记录\`
5. 还原配置

> ⚠️ 跑之前确认 WeFlow 里没有正在进行的导出/清理任务。重启会打断它。

---

## 4. 代理绕过（**最大的坑，必须记牢**）

本机环境变量：

```
http_proxy  = http://127.0.0.1:55423
https_proxy = http://127.0.0.1:55423
```

`curl`、`urllib`、`requests` 默认都读这两个变量 → **所有本地 API 请求会被送去代理，返回 `os error 10061 目标计算机积极拒绝`**，看起来像"WeFlow 没开"，其实是代理在拦。

三种绕过写法：

```bash
# bash / Git Bash
curl -s --noproxy '*' http://127.0.0.1:5031/api/v1/health

# 运行 Python 脚本前清空
http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= all_proxy= ALL_PROXY= python sync_weflow.py --who 笑一
```

```powershell
# PowerShell
$env:http_proxy=''; $env:https_proxy=''
Invoke-RestMethod -Uri 'http://127.0.0.1:5031/api/v1/health' -Proxy $null
```

```python
# Python 内强制不走代理（脚本内已可加）
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
```

> **判据**：报 `10061` 先查代理，再怀疑 WeFlow 没开。`netstat -ano | findstr :5031` 显示 LISTENING 就说明服务是活的。

---

## 5. 水位机制（本次已修复一个真实缺陷）

### 5.1 设计

- `_sync_state.json` 存每个会话的 `watermark`
- 下次跑时 `since=watermark` → 只取新消息 → 与本地 JSON 按 `platformMessageId` 去重合并

### 5.2 ⚠️ 已修复的缺陷（2026-09-27）

**问题**：旧版脚本把 API 返回的 `sync.watermark` 直接当增量水位。但经实测：

| 概念 | 语义 |
|---|---|
| `/messages` 的 `sync.watermark` | **数据库同步游标 ≈ 当前时刻**（本次实测 `1790515350` = 09-27 21:22:30） |
| `/messages` 的 `since` 参数 | **按消息时间戳过滤**（`>=` 语义） |

两者混用 → 水位被推到"当前时刻"，**会跳过「上次同步时刻之前、但尚未拉取」的消息窗口**。

**实证**：
- `since=1790428106`（旧水位=9/26 21:08 同步时刻）→ 返回 **0 条**
- `since=1790357029`（9/26 01:23 最后一条消息）→ 返回 **1 条**（边界那条"爱你"）

若 9/26 01:23 ~ 21:08 之间有过消息，旧逻辑会**永久漏掉**。

**修复**（`sync_weflow.py`）：水位改为**最后一条消息的 timestamp**，而不是 sync 游标。

```python
# 水位推进：以「最后一条消息的时间戳」为准
if msgs:
    wm = msgs[-1].get("timestamp") or wm
```

`since` 是 `>=` 语义，边界那条会重复返回，由 `platformMessageId` 去重兜底 → 安全。

**修复后验证**（21:24）：水位正确停在 `1790357029`，不再被推高。

### 5.3 水位语义速查

- `watermark` = **该会话最后一条消息的 Unix 时间戳**
- 新增消息后水位自动前移；无新消息则**保持不变**
- 怀疑漏消息 → `--full` 重拉，或手工把水位改小一点再跑增量

---

## 6. 故障排查表

| 症状 | 根因 | 处置 |
|---|---|---|
| `os error 10061 积极拒绝` | **代理拦截**（最常见） | 见 §4，加 `--noproxy '*'` / 清 `http_proxy` |
| `/health` 无响应，但 `netstat` 显示 5031 LISTENING | 代理拦截 | 同上 |
| WeFlow 报 **-105** | `wcdb_api.dll` 防回拨锚点漂移 | ① 关 WeFlow ② 重命名三处 Runtime 目录（注册表 `HKCU\Software\WeFlow\Runtime` + `AppData\Local\WeFlow\Runtime` + `Security\State`）③ 重启 WeFlow。或直接跑 `一键更新聊天记录.bat` |
| 一直"无新消息"但你确定有新消息 | 水位被推高 / 消息未落库 | ① 查 `_sync_state.json` 水位 ② 用 §3.1 的 curl 手工验 `since=最后一条消息ts` ③ 仍无 → `--full` |
| 条数比预期少 | 分页中断 / LIMIT 边界 | 重跑；脚本判"还有没有"看 `len(got) < 5000`，不信 `hasMore` |
| 端口 5031 被别的进程占 | 端口冲突 | `netstat -ano | findstr :5031` 找到 PID，或改 `WeFlow-config.json` 的 `httpApiPort` |
| Token 失效 | 配置被重置 | 跑 `一键更新聊天记录.bat`（会自动生成新 token） |

---

## 7. 数据校验 SOP（跑完必做，4 步）

```bash
PY="C:/Users/wardc/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe"
$PY -c "
import json,time,sys
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open(r'C:/Users/wardc/Desktop/07_聊天记录分析/weflow_live/笑一.json',encoding='utf-8'))
ms=d['messages']
print('① 总条数:',d['totalCount'])
print('② syncAt:',d['syncAt'])
t=ms[-1]['timestamp']
print('③ 最后一条:',time.strftime('%Y-%m-%d %H:%M',time.localtime(t)))
print('④ 静默时长: %.1f 小时'%((time.time()-t)/3600))
"
```

| 校验项 | 健康值 | 异常含义 |
|---|---|---|
| ① 总条数 | 只增不减 | 减少 = 被覆盖，需 `--full` 重建 |
| ② syncAt | 为本次运行时刻 | 旧值 = 脚本没跑成功 |
| ③ 最后一条时间 | 与预期一致 | 明显偏旧 = 水位/代理问题 |
| ④ 静默时长 | **> 48h 触发预警** | 见 [[笑一-沟通作战手册_20260927]] 当下预警 |

---

## 8. 自动化建议

### 8.1 现状（不推荐无人值守）

`sync_weflow.py` 依赖 WeFlow **常驻运行** + **代理变量被清空**。若做成开机定时任务，需保证：
- WeFlow 随系统启动并登录
- 任务的环境里没有 `http_proxy`

### 8.2 若要做定时（建议）

每天固定时间跑一次增量 + 输出校验摘要：

> **推荐落法**：用 WorkBuddy 的定时任务（automation），prompt 写"运行 WeFlow 增量同步拉取笑一会话最新消息，输出总条数/最后一条时间/静默时长，静默超 48 小时则预警"。
> **不建议**用 Windows 计划任务直接挂 `.bat`（重量级、会重启 WeFlow，且 22s 等待期内不可用）。

### 8.3 手动节奏（当前采用）

- **每天晚上 21:00 左右**跑一次增量（正好在"时段纪律"的哄睡窗口前，拿到当天数据）
- 跑完做 §7 校验 → 决定当天沟通动作

---

## 9. 本次实测记录（2026-09-27 21:24）

| 项 | 结果 |
|---|---|
| `/health` | `{"status":"ok"}` ✅ |
| 增量同步 | **新增 0 条**，累计 5,759 条 |
| 最后一条消息 | **2026-09-26 01:23**（她："爱你"） |
| **静默时长** | **≈ 44.0 小时**（⚠️ 逼近 48h 预警线） |
| 水位 | 修正 `1790428106` → `1790357029`，脚本 bug 已修 |
| 9/26 凌晨语境 | 她主动示好（"我也最爱你了"／"快起休息吧宝贝"／"睡啦"／"爱你"）→ 中秋那笔账她当天给过台阶 |

> **结论**：链路健康、数据无漏；当下问题不是数据，是 **44 小时无互动**。行动见 [[笑一-最新分析成果与行动方案_20260927]]。

---

## 10. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-09-27 | 建立本文档；修复 `sync_weflow.py` 水位语义缺陷（sync 游标 → 最后一条消息 timestamp）；重置本地水位 |

---

## 🔗 相关

- [[分析流水线]] — 批量 472 人链路（另一层）
- [[原始数据源索引]] · [[数据源地图]] · [[DSH工作区]]
- [[笑一-沟通作战手册_20260927]] · [[笑一-最新分析成果与行动方案_20260927]]
