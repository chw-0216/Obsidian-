---
tags: [资产, 管道, WeFlow, 路径总表, 读取]
created: 2026-10-01
updated: 2026-10-01
---

# WeFlow 数据读取路径总表

> **一页查全所有微信数据的读取入口。** 复制即用。
> 相关：[[WeFlow更新部署方案]] · [[微信联系人分析-复刻手册]] · [[分析流水线]]

> 🔴 **2026-10-03 重要变更**：**实时链路已迁移至 ChatTrace**（解密+索引+秒查，不依赖 WeFlow、不改系统时钟）。
> 见 → **[[ChatTrace复现交接文档]]**。
> **本表的新定位**：链路 A（WeFlow HTTP API）**仅保留用于 ChatTrace 未覆盖的接口**——
> 即**实时拉单会话 / 群成员 / 朋友圈**（`/api/v1/sns/timeline`）。
> 链路 B/C/D（本地 JSON / SQL 索引 / 静态导出）**仍然有效**，但索引库改由 ChatTrace 维护。

---

## 0. 四条链路总览

| 链路 | 用途 | 时效 | 入口 |
|---|---|---|---|
| **A. WeFlow 实时 API** | 拉最新消息、群成员、朋友圈 | **实时** | `http://127.0.0.1:5031` |
| **B. 本地 JSON 落点** | 脚本同步后的分析数据 | 手动同步 | `Desktop\07_聊天记录分析\weflow_live\` |
| **C. SQL 索引库** | 跨会话聚合、历史检索 | 快照（需刷新） | `Desktop\_im_tmp\wechat-mcp\index.sqlite` |
| **D. 静态导出** | 归档、批量分析 | 2026-07-24 快照 | `…\07_WeFlow原始导出_2026-07-24\` |

**数据源头**：微信 4.0 数据目录 `C:\Users\wardc\xwechat_files`（WeFlow 解密读取）

---

## 1. 链路 A：WeFlow 实时 API（首选）

### 1.1 基础信息

| 项 | 值 |
|---|---|
| **程序** | `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeFlow\app\WeFlow.exe` |
| **配置** | `C:\Users\wardc\AppData\Roaming\weflow\WeFlow-config.json` |
| **API 地址** | `http://127.0.0.1:5031`（**仅监听 127.0.0.1**） |
| **Token** | `wf-04eb74eee9324f5a918832b955384c25` |
| **配置字段** | `httpApiToken` / `httpApiPort` / `httpApiHost` / `httpApiEnabled` |
| **鉴权** | `Authorization: Bearer <token>` 或 `?access_token=` 或 body `access_token` |
| **只读性** | ✅ 已反查 `app.asar` 全部路由：**无任何发送接口** |
| **日志** | `AppData\Roaming\weflow\logs\`（`agentDebugLogEnabled = true`） |

### 1.2 接口清单

| 接口 | 用途 | 关键参数 |
|---|---|---|
| `GET /health` · `/api/v1/health` | 健康检查 | 免 Token |
| `GET /api/v1/sessions` | 会话列表 | `limit`、`keyword` |
| `GET /api/v1/sessions/:id/messages` | 增量拉取（ChatLab） | `since`、`offset`、`limit` |
| `GET /api/v1/messages` | 按条件拉消息 | `talker`（必填）、`limit`(1~10000)、`offset`、`start`、`end`、`keyword`、`media` |
| `GET /api/v1/contacts` | 联系人 | `limit` |
| `GET /api/v1/group-members` | 群成员 | `chatroomId`、`includeMessageCounts`、`forceRefresh` |
| `GET /api/v1/sns/timeline` | 朋友圈 | `usernames`、`limit`(≤200)、`start`、`end`、`keyword` |
| `GET /api/v1/sns/media/proxy` | 朋友圈图片代理 | `url`（腾讯 CDN 常 502） |
| `GET /api/v1/push/messages` | **SSE 实时推送** | `access_token`（需开 `messagePushEnabled`） |

### 1.3 curl 速查

```bash
# 健康检查
curl -s --noproxy '*' http://127.0.0.1:5031/api/v1/health

# 会话列表
curl -s --noproxy '*' -H "Authorization: Bearer wf-04eb74eee9324f5a918832b955384c25" \
  "http://127.0.0.1:5031/api/v1/sessions?limit=2000"

# 拉某会话消息（talker = 对方 wxid 或 xxx@chatroom）
curl -s --noproxy '*' -H "Authorization: Bearer wf-04eb74eee9324f5a918832b955384c25" \
  "http://127.0.0.1:5031/api/v1/messages?talker=wxid_xxx&limit=100"

# 群成员
curl -s --noproxy '*' -H "Authorization: Bearer wf-04eb74eee9324f5a918832b955384c25" \
  "http://127.0.0.1:5031/api/v1/group-members?chatroomId=xxx@chatroom"

# 朋友圈
curl -s --noproxy '*' -H "Authorization: Bearer wf-04eb74eee9324f5a918832b955384c25" \
  "http://127.0.0.1:5031/api/v1/sns/timeline?usernames=wxid_xxx&limit=200"
```

> **⚠️ 必加 `--noproxy '*'`**：本机 `http_proxy=http://127.0.0.1:55423` 会劫持所有本地请求，
> 报 `os error 10061 积极拒绝`（看着像 WeFlow 没启动）。

---

## 2. 链路 B：本地 JSON 落点

### 2.1 脚本目录

```
C:\Users\wardc\.workbuddy-ai\skills\wechat-data-forensics\scripts\
├─ sync_chattrace.py       # ★ 首选：ChatTrace 三层同步（解密+索引+出 JSON）
├─ live.py                 # ★ 一键：同步 + 指标 + 红线 + 状态卡
├─ sync_weflow.py          # 🔵 旧：WeFlow 增量同步（已被 sync_chattrace.py 取代）
├─ find_common_groups.py   # 遍历全部群找共同群
├─ dump_group.py           # 打印群对话（带成员名映射）
└─ （另有 build_*/render_*/mine_* 等分析脚本）
```

**常用命令：**

```bash
cd "C:/Users/wardc/.workbuddy-ai/skills/wechat-data-forensics/scripts"

python sync_chattrace.py                      # ★ ChatTrace 三层同步
python live.py --who 笑一 --n 15              # 同步+分析（最常用）
python live.py --who 笑一 --no-sync           # 只读本地，更快
python find_common_groups.py --who "名字"      # 找共同群
python dump_group.py --chatroom xxx@chatroom --who 名字
```

### 2.2 数据落点

```
C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\
├─ 笑一.json                    # 私聊消息（6,110 条）
├─ Ealthy 李梓燏.json           # 私聊消息
├─ _sync_state.json             # 水位（= 最后一条消息 timestamp）
├─ _live_status.md              # ★ 状态卡（新会话先读这个）
├─ _sessions.json               # 会话列表快照
├─ _common_groups_<wxid>.json   # 共同群
├─ _grp_<chatroomId>.json       # 群消息
└─ _sns_<名字>.json             # 朋友圈
```

**消息字段**：`sender / accountName / timestamp / type / content / platformMessageId`
- ⚠️ 判发送方用 **`sender`**（值 = wxid），**不是 `isSender`**
- ⚠️ **文本类型 `type` 不统一**（笑一.json 是 1，李梓燏.json 是 0）→ 先 `Counter` 验证，别硬编码

---

## 3. 链路 C：SQL 索引库（历史聚合）

### 3.1 dbhub MCP 配置

| 项 | 路径 |
|---|---|
| **MCP 注册** | `C:\Users\wardc\.workbuddy-ai\mcp.json` |
| **dbhub 配置** | `C:\Users\wardc\.workbuddy-ai\mcp-config\dbhub-wechat.toml` |
| **dbhub 程序** | `C:\Users\wardc\.workbuddy-ai\mcp-servers\node_modules\@bytebase\dbhub\dist\index.js` |

### 3.2 两个数据源

| id | 库 | 规模 |
|---|---|---|
| `wechat` | `C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite`（**320 MB**） | 33.7 万条 / 1,821 会话 |
| `analysis` | `…\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3`（**197 MB**） | 7.1 万条 / 725 会话 / 6,303 片段 |

**安全设置**：`readonly = true` + `max_rows = 500`（禁止写操作）

> ⚠️ **索引是快照**。**2026-10-03 起索引库改由 ChatTrace 维护**（`Desktop\_im_tmp\wechat-mcp\index.sqlite`，
> 最新 32.3 万条 / 1,826 会话）→ 刷新用 `Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd` 或 `index-incremental.py`。
> 旧 WeFlow 刷新脚本 `刷新微信索引.cmd` 已过时。见 [[ChatTrace复现交接文档]]。
> **实时场景用 ChatTrace 秒查 / 历史聚合用 dbhub。**

---

## 4. 链路 D：静态导出（2026-07-24 快照）

```
C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\
├─ 01_WeFlow可读导出\        # 私聊_xxx\ 群聊_xxx\ 公众号_xxx\ 朋友圈\
├─ 02_原始数据备份\
├─ 03_说明与清单\
├─ 人际网络标注.csv
└─ 人际网络标注.json
```

**规模**：33.6 GB（群聊占绝大多数体积，多数是死群）

---

## 5. 数据源头

| 项 | 路径 |
|---|---|
| **微信数据目录** | `C:\Users\wardc\xwechat_files`（WeFlow 的 `dbPath`） |
| **WeFlow 导出默认路径** | `C:\Users\wardc\Desktop`（`exportPath`） |

---

## 6. 六条铁律（踩过的坑）

1. **代理拦截**：所有本地请求必须 `--noproxy '*'`（curl）或清 `http_proxy`（Python）
2. **水位语义**：水位 = **最后一条消息的 `timestamp`**，不是 API 的 `sync.watermark`（那是"数据库同步游标≈当前时刻"）
3. **字段名**：判发送方用 `sender`，不是 `isSender`
4. **`type` 不统一**：文本可能是 0 或 1，先验证再统计
5. **落点文件名 ≠ 搜索词**：文件按**显示名**命名（`Ealthy 李梓燏.json`），`--who` 是子串匹配
6. **只读**：WeFlow 无发送接口；dbhub `readonly=true`。**发送动作必须人工完成**

---

## 7. 其他相关入口

| 项 | 路径 |
|---|---|
| dbhub/微信 Agent 交接文档 | `C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\README_交接文档.md` |
| 微信接 Agent（DSH + clawbot） | 同上（微信里直接与 Agent 对话，含历史检索 MCP） |
| 🟢 **ChatTrace 复现交接文档** | [[ChatTrace复现交接文档]]（实时链路主力 · 2026-10-03 起） |
| 技能主文档 | `C:\Users\wardc\.workbuddy-ai\skills\wechat-data-forensics\SKILL.md` |
| API 完整文档 | `…\skills\wechat-data-forensics\references_weflow_api.md` |
| Obsidian 分析库 | `C:\Users\wardc\Documents\Obsidian Vault\03_微信聊天分析\` |

---

*最后更新：2026-10-03（实时链路迁移至 ChatTrace 后同步修订）*
