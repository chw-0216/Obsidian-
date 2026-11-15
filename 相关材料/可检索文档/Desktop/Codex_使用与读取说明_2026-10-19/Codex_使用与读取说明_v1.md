# Codex 使用与读取说明（本机版）

版本 v1.0 ｜ 整理日期 2026-10-19 ｜ 适用环境：Windows 11 + OpenAI Codex 桌面端 / CLI

> 本文按本机实际安装与数据整理：桌面端 `OpenAI.Codex 26.1013.4894.0`（开始菜单显示为 **ChatGPT**），CLI `codex-cli 0.163.0-alpha.10.2`，数据目录 `C:\Users\wardc\.codex`。
> 说明里提到的数据库、会话数量、插件清单等，都是 2026-10-19 当天读取到的快照，后续会变化。

---

## 一、一分钟上手

1. **打开 Codex**
   - 桌面端：开始菜单搜「**ChatGPT**」（应用包名是 `OpenAI.Codex`），这就是 Codex 桌面端；
   - 或在终端执行 `codex app <目录>` 直接打开某个工作目录；
   - 纯终端交互：`codex`（TUI），或 `codex "帮我检查这个项目"`。
2. **新任务**：选一个工作目录（建议一个任务一个文件夹），用中文描述目标；把要读的文件路径直接写在对话里。
3. **权限**：本机默认 `approval_policy = "on-request"`，模型拿不准时会弹权限请求；允许/拒绝即可。
4. **继续历史会话**：`codex resume --last` 继续最近一次；`codex resume` 弹出选择器；桌面端左侧会话列表也可直接点开。
5. **读取记录**：会话数据都在 `C:\Users\wardc\.codex`，用本文附带的 `codex_read_sessions.py` 或 §7 的 SQL 读取。
6. **安全**：`.codex` 里有登录凭据、第三方密钥和大量私人内容，**不要整体外发或上传公开仓库**。

---

## 二、本机环境概览

| 项目 | 实际值 |
| --- | --- |
| 桌面端 | `OpenAI.Codex 26.1013.4894.0`（MSIX 安装，开始菜单显示名「ChatGPT」） |
| 桌面端安装位置 | `C:\Program Files\WindowsApps\OpenAI.Codex_26.1013.4894.0_x64__2p2nqsd0c76g0` |
| CLI 版本 | `codex-cli 0.163.0-alpha.10.2` |
| CLI 可执行文件 | `C:\Users\wardc\AppData\Local\OpenAI\Codex\bin\896a0166b774037a\codex.exe` |
| 数据目录 | `C:\Users\wardc\.codex`（可用环境变量 `CODEX_HOME` 改变） |
| 全局规则 | `C:\Users\wardc\.codex\AGENTS.md` |
| 默认模型 | `gpt-6-astra`，推理强度 `ultra`（见 `config.toml`） |
| 审批 / 沙箱 | `on-request` / `danger-full-access` |
| 联网搜索 | `web_search = "live"`（模型可直接联网搜索） |
| 工作目录约定 | `Documents\Codex\<日期>\<会话名>\`，内含 `work\`、`outputs\` |
| 当前会话规模 | 799 个会话（其中 30 个已归档）、41,759 条 item、2,696 个 turn |

**注意：`codex` 命令当前不在 PATH 里**（`Get-Command codex` 找不到）。三种调用方式任选：

```powershell
# 1) 用完整路径
& "C:\Users\wardc\AppData\Local\OpenAI\Codex\bin\896a0166b774037a\codex.exe" --version

# 2) 临时别名（只对当前 PowerShell 窗口有效）
Set-Alias codex "C:\Users\wardc\AppData\Local\OpenAI\Codex\bin\896a0166b774037a\codex.exe"

# 3) 永久加到用户 PATH（设置后重开终端）
[Environment]::SetEnvironmentVariable(
  "Path",
  [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\Users\wardc\AppData\Local\OpenAI\Codex\bin\896a0166b774037a",
  "User")
```

---

## 三、启动与基本使用

### 3.1 三种入口

| 入口 | 用法 | 适合场景 |
| --- | --- | --- |
| 桌面端（ChatGPT / Codex App） | 开始菜单打开，或 `codex app <目录>` | 日常对话、看 diff、管理会话、用插件/电脑操作 |
| 终端交互 TUI | `codex`、`codex "提示词"`、`codex -C <目录>` | 在项目目录里快速干活 |
| 非交互 | `codex exec "任务"`、`codex exec resume <id>`、`codex review --uncommitted` | 脚本、批处理、CI、定时任务 |

### 3.2 一次典型使用流程

1. 把任务目录准备好（例如 `C:\Users\wardc\Documents\Codex\2026-10-19\new-chat`）。
2. 打开 Codex 并选择该目录，或在终端 `codex -C <目录>`。
3. 用中文写明：背景、目标、输入文件路径、验收标准。要读的文件直接写路径，Codex 会自行读取。
4. 遇到权限请求（`on-request`）时确认；涉及删除、外发、系统设置的操作建议先仔细看命令。
5. 完成后看 diff / 产物；终端可用 `codex apply` 应用最近一次 diff。
6. 下次继续：`codex resume --last`，或 `codex resume <会话ID/名称>`。
7. 需要分支尝试：`codex fork`；需要排队追加：`codex queue --thread <id> --message "..."`。

### 3.3 本机 profile（按场景切换）

`config.toml` 之外，`~/.codex` 下还有若干 `<名字>.config.toml`，用 `-p/--profile <名字>` 叠加加载：

| Profile | 用途 | 关键配置 |
| --- | --- | --- |
| `aigc` | 创意 / 数字媒体项目，全权限 | `approval_policy="never"`、`danger-full-access` |
| `finance` | 财经 / CFA 研究，更稳妥 | `approval_policy="on-request"`、`workspace-write` |
| `hermes` | 本地 Ollama 模型 `hermes3:8b` | `model_provider="ollama"` |
| `offline` | 断网时走本地模型 | `model_provider="ollama-local"` |
| `opencodex`、`claude-code-router` | 第三方路由 / 本地代理配置 | 见对应文件 |

```powershell
codex -p aigc          # 创意项目，全权限
codex -p finance       # 财经研究，保留审批 + 只写工作区
codex -p offline       # 断网时用本地 Ollama
```

### 3.4 常用启动参数

| 参数 | 作用 |
| --- | --- |
| `-C, --cd <DIR>` | 指定工作根目录 |
| `-m, --model <MODEL>` | 本次使用指定模型 |
| `-p, --profile <NAME>` | 叠加 `~/.codex/<NAME>.config.toml` |
| `-s, --sandbox <MODE>` | `read-only` / `workspace-write` / `danger-full-access` |
| `-a, --ask-for-approval <POLICY>` | `on-request` / `never` |
| `--search` | 开启实时联网搜索（无需逐次批准） |
| `-i, --image <FILE>` | 附带图片 |
| `--add-dir <DIR>` | 追加可写目录 |
| `--worktree` | 在独立的 Git worktree 中运行 |
| `--no-alt-screen` | 终端用内联模式，保留滚动历史 |
| `-c key=value` | 临时覆盖配置，如 `-c model="gpt-6-astra"` |

---

## 四、配置与规则

### 4.1 关键文件

| 文件 / 目录 | 作用 | 是否含敏感信息 |
| --- | --- | --- |
| `~/.codex/config.toml` | 主配置：模型、审批、沙箱、插件、MCP、项目信任 | 是（含第三方凭据类环境变量） |
| `~/.codex/<名字>.config.toml` | profile 配置（aigc / finance / hermes / offline…） | 个别含密钥 |
| `~/.codex/AGENTS.md` | 全局行为约定（中文回答、归档路径、权限登记等） | 否 |
| `~/.codex/auth.json` | 登录凭据 | 是，**绝对不要外发** |
| `~/.codex/secrets/` | 密钥存放 | 是 |
| `~/.codex/plugins/`、`skills/` | 插件与技能 | 否 |
| 项目根目录的 `AGENTS.md` | 项目级规则，优先生效 | 视内容而定 |

### 4.2 `config.toml` 里值得知道的配置

- **模型**：`model = "gpt-6-astra"`、`model_reasoning_effort = "ultra"`；
- **审批与沙箱**：`approval_policy = "on-request"`、`sandbox_mode = "danger-full-access"`；
- **联网**：`web_search = "live"`；
- **桌面端设置**：`[desktop]` 下会话详情模式、字号、终端 shell（PowerShell）、推理档位（low/medium/high/xhigh/ultra/persistent/max）、队列模式等；
- **插件**：`[plugins."documents@openai-primary-runtime"]` 等；
- **MCP**：`[mcp_servers.hyper3d]`、`[mcp_servers.node_repl]`；
- **项目信任**：`[projects.'c:\...']` 的 `trust_level = "trusted"`；
- **Windows 沙箱**：`[windows] sandbox = "elevated"`；
- **环境变量**：`[shell_environment_policy.set]` 里包含第三方服务的凭据类变量（本文不展示原值）。

### 4.3 AGENTS.md（全局规则）

当前 `~/.codex/AGENTS.md` 的主要内容：

- 默认中文回答，代码/命令/报错保留原文；
- 最看重 GitHub 软件部署与清理：统一装到 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\<软件>\`，写 `INSTALL-NOTES.md`，并登记到 `permissions-settings-log.md`；
- 个人背景：经济/金融转 AIGC / 数字媒体艺术，摄影爱好者；
- 常做：生活与情感分析、视觉设计、文档打磨；
- 环境：Windows 11 + PowerShell，代理 v2rayN（SOCKS 1099 / HTTP 1100），本地 Ollama；
- 习惯：项目放在 `Documents/codex/日期/` 或桌面新建文件夹；破坏性操作先确认。

### 4.4 审批与沙箱（重点）

| 模式 | 含义 | 风险 |
| --- | --- | --- |
| `on-request` | 模型认为需要时向你申请 | 较可控，推荐日常使用 |
| `never` | 从不询问，失败直接返回给模型 | 可能直接执行破坏性命令 |
| `read-only` | 只能读，不能写 | 最安全 |
| `workspace-write` | 只能写工作区 | 推荐处理敏感任务 |
| `danger-full-access` | 全盘可读写 + 可联网 | 最高风险，注意别误删 |

- 本机默认组合是 **`on-request` + `danger-full-access`**：审批还在，但一旦批准就是全盘权限。
- `aigc` profile 是 `never + danger-full-access`，等于完全不拦；用于一次性创意项目可以，处理重要文件前请先备份。
- 极端参数 `--dangerously-bypass-approvals-and-sandbox` 会同时跳过审批和沙箱，**除非在外部隔离环境，否则不要用**。

### 4.5 登录

```powershell
codex login status     # 查看登录状态
codex login            # 交互式登录
codex logout           # 退出并删除本地凭据
```

`codex doctor --summary` 里显示 `auth is configured`，说明当前已登录可用。

---

## 五、能力清单：插件、MCP、电脑操作、自动化、记忆

### 5.1 已安装并启用的插件（部分）

| 类别 | 插件 |
| --- | --- |
| 文档办公 | `documents`、`pdf`、`spreadsheets`、`presentations`、`template-creator` |
| 浏览器 / 电脑操作 | `browser`、`chrome`、`computer-use`、`unified-computer-use` |
| 开发辅助 | `code-review`、`codex-app-tools`、`visualize` |
| 连接器（远程） | `gmail`、`google-drive`、`github`（已安装）；`slack`、`notion`、`outlook` 等可装未装 |

查看与安装：

```powershell
codex plugin list                 # 列出市场与已安装插件
codex plugin marketplace list     # 查看插件市场
codex plugin add <插件@市场>       # 安装（示例，按列表里的名称）
```

### 5.2 MCP 服务

```powershell
codex mcp list
```

| 名称 | 类型 | 状态 |
| --- | --- | --- |
| `hyper3d` | 远程 MCP（OAuth） | 启用 |
| `node_repl` | 本地 Node REPL | 启用 |
| `cua_repl` | 电脑操作（Computer Use） | 启用 |
| `code-review`、`codex_app` | 本地 MCP 脚本 | 当前为 disabled |

`codex doctor --summary` 提示 MCP 配置有可选问题（缺环境变量或需禁用某个服务）；不影响聊天时可以先忽略，遇到具体工具报错再按提示处理。

### 5.3 自动化、记忆、技能

- **自动化**：`~/.codex/automations/` 下有若干自动化任务（如 `automation-5`「Obsidian每日复盘」，每晚 21:00 运行）。
- **记忆**：`~/.codex/memories/` 与 `memories_1.sqlite`，Codex 会跨会话积累摘要。
- **技能**：`~/.codex/skills/`（`.system` 内置技能），插件也会自带 skills。
- **附件 / 图片**：`~/.codex/attachments/`、`generated_images/`。

---

## 六、CLI 命令速查

| 命令 | 作用 |
| --- | --- |
| `codex` | 进入交互式 TUI |
| `codex "提示词"` | 直接带首条提示词启动 |
| `codex exec "任务"` | 非交互执行，适合脚本 |
| `codex exec resume <id>` | 非交互继续某个会话 |
| `codex resume [--last] [--all]` | 恢复会话；默认按当前目录过滤，`--all` 看全部 |
| `codex fork` | 从历史会话复制出新会话（分支尝试） |
| `codex queue --thread <id> --message "..."` | 给运行中的会话排队追加消息 |
| `codex agents` | 浏览共享 app-server 上的所有 agent 会话 |
| `codex review --uncommitted` / `--base main` | 非交互代码审查 |
| `codex apply` | 把最近一次 agent diff 应用到本地工作树 |
| `codex archive <id/名称>` | 归档会话（不删除） |
| `codex unarchive <id/名称>` | 取消归档 |
| `codex delete <id/名称>` | 永久删除会话（先备份） |
| `codex migrate-rollouts [--json] [--apply]` | 检查/迁移旧 rollout 到分页历史 |
| `codex mcp list / add / remove / login` | 管理 MCP |
| `codex plugin list / add / remove / marketplace` | 管理插件 |
| `codex features list / enable / disable` | 功能开关 |
| `codex doctor [--summary] [--json]` | 诊断安装、配置、登录、网络 |
| `codex update` | 更新 Codex |
| `codex login status` | 登录状态 |
| `codex app [路径]` | 启动桌面端并打开目录 |
| `codex sandbox <命令>` | 在 Codex 沙箱内执行命令 |
| `codex debug models` / `debug prompt-input` | 查看模型目录 / 模型实际收到的提示词 |
| `codex completion` | 生成 shell 补全脚本 |

---

## 七、会话与数据地图

### 7.1 `.codex` 目录总览

| 路径 | 内容 | 体量（本机） |
| --- | --- | --- |
| `state_5.sqlite` | 会话索引：`threads`、`projects`、附件、子代理关系等 | 约 18.5 MB |
| `thread_history_1.sqlite` | 会话正文：`thread_items`、`thread_turns` | 约 691.6 MB |
| `logs_2.sqlite` | 运行日志（按 thread_id 记录） | 约 97.7 MB |
| `session_index.jsonl` | 轻量索引：`id`、`thread_name`、`updated_at` | 约 50 KB |
| `sessions\YYYY\MM\DD\rollout-*.jsonl.zst` | 原始事件流（zstd 压缩的 JSONL） | 按日期分布 |
| `archived_sessions\` | 已归档的 rollout 文件 | — |
| `memories_1.sqlite` / `memories\` | 记忆摘要 | 约 0.8 MB |
| `goals_1.sqlite` | 会话目标（thread_goals） | 很小 |
| `queue_1.sqlite` | 排队消息 | 很小 |
| `auth.json` / `config.toml` / `secrets\` | 登录与配置（敏感） | — |
| `plugins\` / `skills\` / `automations\` / `attachments\` | 插件、技能、自动化、附件 | 较大 |
| `_backup_before_session_import_20261013\` | 历史备份 | — |

### 7.2 三个核心数据源

1. **`state_5.sqlite` 的 `threads` 表**——会话列表与元数据：`id`、`title`、`cwd`、`model`、`tokens_used`、`archived`、`updated_at`、`first_user_message`、`git_branch` 等。
2. **`thread_history_1.sqlite` 的 `thread_items` 表**——真正的对话内容：每条 item 有 `item_type` 和 `item_json`。
3. **`sessions\**\rollout-*.jsonl.zst`**——最原始的完整事件流，适合追溯工具调用细节。

本机 `thread_items` 的类型分布（截至 2026-10-19）：`reasoning` 14,019、`agentMessage` 12,332、`commandExecution` 6,074、`userMessage` 2,568、`mcpToolCall` 2,082、`webSearch` 1,482、`imageView` 1,262、`fileChange` 1,055、`subAgentActivity` 404、`imageGeneration` 150、`functionCallOutput` 144、`contextCompaction` 112、`collabAgentToolCall` 37、`sleep` 27、`dynamicToolCall` 11。

---

## 八、读取说明（重点）

### 8.1 在应用里读

- 桌面端左侧会话列表：按时间/项目浏览，点开即可看完整对话、diff、命令记录；
- 终端选择器：`codex resume`（默认只显示当前目录的会话，`--all` 显示全部，`--last` 直接继续最近一个）；
- 浏览共享守护进程上的所有 agent 会话：`codex agents`；
- 归档/删除：`codex archive` / `codex delete`（删除不可恢复）。

### 8.2 读 `session_index.jsonl`（最快）

每行一个 JSON，适合做会话清单：

```powershell
Get-Content "$env:USERPROFILE\.codex\session_index.jsonl" -Tail 20
```

字段：`id`（会话 UUID）、`thread_name`（标题）、`updated_at`（UTC 时间）。

### 8.3 读 SQLite（推荐，能拿全文）

**只读打开**，不要在 Codex 运行时写库：

```python
import sqlite3, os
db = os.path.expanduser(r"~/.codex/state_5.sqlite")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
```

常用查询：

```sql
-- 1) 最近 10 个会话
SELECT datetime(updated_at,'unixepoch','localtime') AS 更新时间,
       title, model, tokens_used, cwd, id
FROM threads
ORDER BY updated_at DESC
LIMIT 10;

-- 2) 某个会话里的用户消息与 Codex 回复
SELECT item_type,
       CASE item_type
         WHEN 'userMessage'  THEN json_extract(item_json,'$.content[0].text')
         WHEN 'agentMessage' THEN json_extract(item_json,'$.text')
       END AS 内容,
       datetime(created_at_ms/1000,'unixepoch','localtime') AS 时间
FROM thread_items
WHERE thread_id = '01a1504f-06b7-7130-9e14-bd1199e5a8eb'
  AND item_type IN ('userMessage','agentMessage')
ORDER BY rollout_ordinal;

-- 3) 按关键词找会话（标题或首条用户消息）
SELECT id, title, datetime(updated_at,'unixepoch','localtime') AS 更新时间
FROM threads
WHERE title LIKE '%关键词%' OR first_user_message LIKE '%关键词%'
ORDER BY updated_at DESC
LIMIT 20;

-- 4) token 使用最多的 10 个会话
SELECT title, model, tokens_used,
       datetime(updated_at,'unixepoch','localtime') AS 更新时间
FROM threads
ORDER BY tokens_used DESC
LIMIT 10;

-- 5) 查某个会话每一轮的状态与耗时
SELECT turn_id, status,
       datetime(started_at,'unixepoch','localtime') AS 开始,
       duration_ms
FROM thread_turns
WHERE thread_id = '<THREAD_ID>'
ORDER BY rollout_ordinal;
```

> 提示：`thread_items` 的 `item_json` 是各类型自己的 JSON 结构，例如 `userMessage` 的正文在 `content` 数组里、`agentMessage` 在 `text` 字段、`commandExecution` 在 `command` 字段。直接 `SELECT item_type, item_json` 看原始结构最直观。

### 8.4 读原始 rollout（`*.jsonl.zst`）

- 路径规则：`~/.codex/sessions/<年>/<月>/<日>/rollout-<时间戳>-<会话UUID>.jsonl.zst`
- 内容：压缩的 JSONL，每行一个事件：

| 字段 | 含义 |
| --- | --- |
| `timestamp` | 事件时间 |
| `ordinal` | 事件序号（与 `thread_items.rollout_ordinal` 对应） |
| `type` | `session_meta` / `event_msg` / `response_item` 等 |
| `payload` | 具体内容；`response_item` 里是模型消息，`event_msg` 里是 `item_completed` 等 |

- 解压方式：**用系统 Python 的 `zstandard`**（本机已装 0.25.0），或直接用附带脚本：

```powershell
python codex_read_sessions.py rollout "C:\Users\wardc\.codex\sessions\2026\08\08\rollout-2026-08-08T02-48-50-019fdd8e-7d90-78f0-b5c7-9b1ea957a92f.jsonl.zst"
```

> 注意：Windows 自带 `tar` 虽然带 libzstd，但**实测不能直接解 `.zst` 单文件**，不要用 `tar -xf`。

### 8.5 直接使用附带脚本（推荐）

本说明同目录附带 `codex_read_sessions.py`，只读、不修改任何 Codex 数据：

```powershell
# 1) 列出最近 10 个会话
python codex_read_sessions.py list --limit 10

# 2) 按 ID 前缀或标题关键词导出为 Markdown
python codex_read_sessions.py export --thread 01a1504f --out 会话.md
python codex_read_sessions.py export --thread "博导" --diffs

# 3) 解压 rollout 原始记录为 .jsonl
python codex_read_sessions.py rollout "路径\rollout-xxx.jsonl.zst" --out 记录.jsonl
```

导出文件包含：标题、会话 ID、工作目录、模型、更新时间、Tokens，以及按时间排列的「用户 / Codex / 执行命令 / 文件变更 / MCP 工具调用 / 联网搜索 / 图片」内容。

### 8.6 日志与排错

```powershell
codex doctor --summary      # 分组健康检查
codex doctor                # 详细诊断（会输出更多路径信息）
codex doctor --json         # 脱敏的机器可读报告
```

日志在 `logs_2.sqlite` 的 `logs` 表，字段包括 `ts`、`level`、`target`、`feedback_log_body`、`thread_id` 等。查某个会话的错误：

```sql
SELECT datetime(ts,'unixepoch','localtime') AS 时间, level, target, substr(feedback_log_body,1,300)
FROM logs
WHERE thread_id = '<THREAD_ID>' AND level IN ('ERROR','WARN')
ORDER BY ts DESC
LIMIT 50;
```

当前诊断快照（2026-10-19）：**21 ok · 1 idle · 4 notes · 3 warn · 0 fail**。提示项：

1. 沙箱为「文件系统不受限 + 网络开启」（默认配置，属预期）；
2. Microsoft Defender 可能干扰 Codex（如遇文件被拦，可自行评估是否加排除项）；
3. MCP 配置有可选问题（缺环境变量或需禁用某个服务）；
4. **3 个会话在状态数据库里有记录，但 rollout 文件缺失**。

### 8.7 关于「3 个会话的 rollout 缺失」

这是本机目前唯一的实质告警。安全处理顺序：

```powershell
# 先只检查，不修改（会列出可迁移/有问题的会话）
codex migrate-rollouts --json

# 确认无误、并备份 .codex 之后，再执行迁移
codex migrate-rollouts --apply
```

不要手动删 `state_5.sqlite` 里的行，也不要在 Codex 运行时直接改数据库。

---

## 九、备份、归档、迁移与清理

### 9.1 备份

关闭 Codex 桌面端/所有 `codex` 进程后，再复制数据目录（至少包含会话数据）：

```powershell
$src = "$env:USERPROFILE\.codex"
$dst = "D:\backup\codex-$(Get-Date -Format yyyyMMdd-HHmm)"
robocopy $src $dst /E /XJ /XD cache plugins .tmp .sandbox-bin .sandbox-secrets
```

最小备份集：`state_5.sqlite`、`thread_history_1.sqlite`、`session_index.jsonl`、`sessions\`、`archived_sessions\`、`memories_1.sqlite`、`goals_1.sqlite`、`auth.json`（如需保留登录）、`config.toml`。

### 9.2 归档 / 恢复 / 删除

```powershell
codex archive <会话ID或名称>     # 归档（可在归档中找到）
codex unarchive <会话ID或名称>   # 取消归档
codex delete <会话ID或名称>      # 永久删除，先备份
```

### 9.3 迁移旧会话

```powershell
codex migrate-rollouts           # 只报告
codex migrate-rollouts --apply   # 执行迁移（先备份）
```

### 9.4 清理空间

优先级建议：`logs_2.sqlite`（约 98 MB）→ `sessions\` 里很旧的 rollout → `archived_sessions\` → 插件缓存 `plugins\cache\`。清理前先备份；不要删除 `state_5.sqlite`、`thread_history_1.sqlite` 这类主库。

---

## 十、安全与隐私

1. `auth.json`、`config.toml`（含第三方 token 类变量）、`secrets\`、`*.config.toml` 里的密钥**不要外发**、不要提交到公开仓库。
2. 本文附带的读取脚本只读打开 SQLite；导出的 Markdown 会包含完整对话与命令，注意保存位置。
3. `danger-full-access` + `never` 组合可以删除任意文件；重要目录操作前先确认，必要时切换 `finance` profile 或 `-s workspace-write`。
4. Computer Use / 浏览器插件会读取屏幕与页面内容；处理敏感窗口前先关闭其他窗口。
5. `codex doctor --json` 输出是脱敏的，可安全用于排查；普通 `codex doctor` 会显示更多本机路径，分享前先看一眼。

---

## 十一、附录

### 11.1 本机快照（2026-10-19）

| 项目 | 值 |
| --- | --- |
| 桌面端 | OpenAI.Codex 26.1013.4894.0（显示名 ChatGPT） |
| CLI | 0.163.0-alpha.10.2 |
| 会话 / 归档 | 799 / 30 |
| thread_items / thread_turns | 41,759 / 2,696 |
| state_5.sqlite | 18.5 MB |
| thread_history_1.sqlite | 691.6 MB |
| logs_2.sqlite | 97.7 MB |
| 诊断 | 21 ok · 1 idle · 4 notes · 3 warn · 0 fail |
| 已启用插件 | documents、pdf、spreadsheets、presentations、template-creator、codex-app-tools、browser、unified-computer-use、chrome、computer-use、code-review、visualize、gmail、google-drive、github |
| MCP | hyper3d（OAuth）、node_repl、cua_repl |

### 11.2 参考入口

- `codex --help`、`codex <子命令> --help`（本文命令均以本机 CLI 为准）；
- 各子命令的完整参数以 `--help` 输出为准，版本升级后可能有变化；
- 全局行为约定：`C:\Users\wardc\.codex\AGENTS.md`；
- 主配置：`C:\Users\wardc\.codex\config.toml`（修改前先备份）。
