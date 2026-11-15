---
tags: [资产, 管道, ChatTrace, 交接文档, 复现, 微信]
created: 2026-10-03
source: 用户提供（2026-10-03）
verified: 2026-10-03 12:07 全项通过
---

# 微信聊天数据实时分析系统 · 复现交接文档

> 生成：2026-10-03 ｜ 用途：在另一台机器/另一个环境重建整套「微信实时数据 → 分析」流程
> 方案代号：**ChatTrace**（替代 WeFlow）
> **本文件已在本机逐项验证，验证结果见下方。**

---

## ✅ 本机验证结果（2026-10-03 12:07）

| 验证项 | 结果 |
|---|---|
| ChatTrace 主程序 `Desktop\_im_tmp\chattrace\` | ✅ 存在（RELEASE_NOTES 至 v0.5.1） |
| 三件套 `index-incremental.py` / `gen_live_json.py` / `刷新实时数据.cmd` | ✅ 齐全 |
| DPAPI 密钥 `wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo` | ✅ 存在（494 B，10-01 20:25） |
| 解密输出 `%LOCALAPPDATA%\ChatTrace\accounts\...\decrypted\` | ✅ 存在（bizchat/contact/emoticon/favorite/general…） |
| `index.sqlite` | ✅ **323,186 条** / 1,826 会话 / 最新 **10-03 12:05**（链路活跃） |
| `role` 字段分布 | ✅ me 81,124 / them 235,672 / system 6,436 |
| 笑一会话读取 | ✅ 正常（`session_key='wxid_wdnk6ue9kiyn22'`） |
| 笑一目录 `Desktop\笑一\` | ✅ 存在 |

**与原文的两处偏差（以实测为准）**：
1. 原文写「34.5 万条」→ 实测 **32.3 万条**
2. 原文未提及 `messages_fts` **全文检索表**（`messages_fts` / `_data` / `_idx` / `_content` / `_docsize` / `_config`）—— 这是**额外能力**，可用于关键词秒搜

---

## 一、系统总览

```
微信手机端
    ↓（电脑微信接收并写库）
[1] 加密库  C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\   （22 个 SQLCipher 库）
    ↓ ChatTrace 解密（密钥 DPAPI 加密存储）
[2] 解密库  %LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\
    ↓ 增量索引
[3] 索引库  C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite      （320MB / 32.3 万条）
    ↓ 两条出口
    ├─[4a] 秒级查询  C:\Users\wardc\Desktop\笑一\查最新消息.py          （0.2 秒）
    └─[4b] 全量 JSON  C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\*.json  （分析脚本用）
```

**核心优势**：不依赖 WeFlow、不改系统时钟、不需要重新抓密钥（密钥永久有效）

---

## 二、目录与文件清单

| 用途 | 路径 |
|------|------|
| **ChatTrace 主程序** | `C:\Users\wardc\Desktop\_im_tmp\chattrace\` |
| **索引/导出工具** | `C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\` |
| ├ 增量索引脚本 | `wechat-mcp\index-incremental.py` |
| ├ JSON 生成脚本 | `wechat-mcp\gen_live_json.py` |
| ├ 一键刷新（三层） | `wechat-mcp\刷新实时数据.cmd` |
| └ 索引库 | `wechat-mcp\index.sqlite` |
| **密钥（DPAPI）** | `%LOCALAPPDATA%\ChatTrace\keys\wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo` |
| **密钥原件（敏感）** | `apps\WeFlow\key-export-20261001\weflow-keys.txt` |
| **解密输出** | `%LOCALAPPDATA%\ChatTrace\accounts\<wxid>_db45\decrypted\` |
| **微信加密库** | `C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\` |
| **实时 JSON** | `C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\` |
| **秒查工具** | `C:\Users\wardc\Desktop\笑一\查最新消息.py` |
| **笑一档案** | `C:\Users\wardc\Desktop\笑一\` |

---

## 三、复现步骤（从零开始）

### 前置条件

- Windows 10/11（DPAPI 依赖）
- Python 3.12（`C:\Users\wardc\AppData\Local\Programs\Python\Python312\python.exe`）
- 电脑微信已登录目标账号（微信 4.1.12.26）
- **ChatTrace 程序目录**（`_im_tmp\chattrace`）与 **wechat-mcp 工具目录** 已就位

### 步骤 1：确认微信库存在

```powershell
Test-Path "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
# 应返回 True；里面应有 db_storage\message\message_0.db 等
```

### 步骤 2：确认/获取密钥

```powershell
Test-Path "$env:LOCALAPPDATA\ChatTrace\keys\wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo"
```

- **存在** → 直接可用（DPAPI 加密，绑定当前 Windows 用户）
- **不存在** → 需重新抓密钥（从微信进程内存读取 SQLCipher 主密钥）

> ⚠️ **跨机器限制**：DPAPI 密钥**不能直接复制到另一台机器/另一个 Windows 账户**（DPAPI 与用户凭据绑定）。换机器需重新抓密钥。同机同账户则永久有效。

### 步骤 3：解密

```powershell
$env:PYTHONIOENCODING='utf-8'
cd 'C:\Users\wardc\Desktop\_im_tmp\chattrace'
python -m chattrace.cli data decrypt --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
```

预期输出：`result: N decrypted, M fresh, 0 failed of 22 DBs`

### 步骤 4：增量索引

```powershell
cd 'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp'
python index-incremental.py
```

预期输出：`并入后: 32xxxx 条 (+N), 最新 yyyy-mm-dd HH:MM`

### 步骤 5：生成 JSON（可选，分析脚本用）

```powershell
python gen_live_json.py
# 产出：C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\*.json
```

### 步骤 6：秒级查询

```powershell
python 'C:\Users\wardc\Desktop\笑一\查最新消息.py'
```

---

## 四、一键刷新脚本（三层）

`C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd`

```bat
@echo off
setlocal
set CT=C:\Users\wardc\Desktop\_im_tmp\chattrace
set MCP=C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
set ACCT=C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45
set PY=python
set PYTHONIOENCODING=utf-8
cd /d "%CT%"
%PY% -m chattrace.cli data decrypt --account-dir "%ACCT%"
if errorlevel 1 exit /b 1
cd /d "%MCP%"
%PY% index-incremental.py
if errorlevel 1 exit /b 1
%PY% gen_live_json.py
if errorlevel 1 exit /b 1
echo 完成
pause
```

> ⚠️ **必须保存为 CRLF 行尾 + GBK 编码**。纯 LF 会让 cmd 吞字符报错（如 `'ING' 不是内部命令`）。

### 4.1 定时任务（自动化）

本机已挂一个**每 2 小时**的自动化：**「笑一聊天自动同步+回复建议」**
- ID：`eeffa7ac-63be-4b63-9acf-b20bab0acb49`
- 频率：`FREQ=HOURLY;INTERVAL=2`（24 小时每 2 小时一次）
- 动作：跑 `sync_chattrace.py` → 读 `笑一.json` 最后 20 条 → 对比 `_live_status.md` → 有新消息才给回复建议，无则只回「无新消息」
- 背景：2026-10-03 从旧的 `sync_weflow.py`（WeFlow 链路）迁移过来

> ⚠️ **RRULE 限制**：本调度器**不支持多值 BYHOUR**（`BYHOUR=8,10,12` 会报错），
> 想限定时段只能靠 HOURLY 的 INTERVAL 或改 DAILY（单点）。

### 4.2 脚本层的解释器自适应

`sync_chattrace.py` 内置 `pick_python()`：优先用当前解释器（若它能 `import chattrace`），
否则自动回退到系统 Python 3.12（`C:\Users\wardc\AppData\Local\Programs\Python\Python312\python.exe`）。
**原因**：`chattrace` 是 **editable 装在系统 3.12** 里，托管版 3.13 **没有**这个包——
直接用 3.13 跑会报 `ModuleNotFoundError: No module named 'chattrace'`。

---

## 五、索引库结构（index.sqlite）

**表：`messages`**

| 字段 | 说明 | 示例 |
|------|------|------|
| `id` | 自增主键 | 123456 |
| `session_key` | 会话标识（私聊=对方 wxid；群=xxx@chatroom；公众号=gh_xxx） | `wxid_wdnk6ue9kiyn22` |
| `ts` | Unix 时间戳（秒） | 1787497407 |
| `time_text` | 原始时间文本 | `2026-09-30 21:33` |
| `role` | **发送者角色：`me` / `them` / `system`** | `them` |
| `sender` | 发送者（me 的显示为"我"） | `wxid_wdnk6ue9kiyn22` |
| `type` | 消息类型 | `0`=文本 |
| `content` | 消息内容 | `老公` |

**关键查询示例：**

```sql
-- 某会话最新 20 条
SELECT role, ts, content FROM messages
WHERE session_key = 'wxid_wdnk6ue9kiyn22'
ORDER BY ts DESC LIMIT 20;

-- 最近活跃会话
SELECT session_key, COUNT(*), MAX(ts) FROM messages
GROUP BY session_key ORDER BY MAX(ts) DESC LIMIT 15;

-- 全文检索（原文未提及的额外能力）
SELECT session_key, ts, content FROM messages_fts
WHERE messages_fts MATCH '关键词' LIMIT 20;
```

---

## 六、秒查脚本（完整代码）

`C:\Users\wardc\Desktop\笑一\查最新消息.py`

```python
# 用法:
#   python 查最新消息.py              -> 默认会话(笑一) 最新20条，秒级(不刷新)
#   python 查最新消息.py -r           -> 先增量刷新(约30秒)再查看
#   python 查最新消息.py -r 30        -> 刷新后显示30条
#   python 查最新消息.py wxid_xxx 30  -> 指定会话
import sqlite3, sys, datetime, subprocess, os
DB = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEFAULT_TALKER = 'wxid_wdnk6ue9kiyn22'
ME = 'wxid_zn4ozsnn8esr21'

def do_refresh():
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    subprocess.run(['python', '-m', 'chattrace.cli', 'data', 'decrypt',
                    '--account-dir', r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45'],
                   cwd=r'C:\Users\wardc\Desktop\_im_tmp\chattrace', env=env,
                   capture_output=True, timeout=180)
    subprocess.run(['python', 'index-incremental.py'],
                   cwd=r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp', env=env,
                   capture_output=True, timeout=120)

def show(talker, limit):
    c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    cur = c.cursor()
    cur.execute("SELECT role, ts, content FROM messages WHERE session_key LIKE ? ORDER BY ts DESC, id DESC LIMIT ?",
                (f'%{talker}%', limit * 4))
    rows = cur.fetchall(); c.close()
    seen, out = set(), []
    for role, ts, content in rows:
        key = (ts, content)
        if key in seen: continue
        seen.add(key); out.append((role, ts, content))
        if len(out) >= limit: break
    print(f"=== {talker} 最新 {len(out)} 条 ===")
    for role, ts, content in reversed(out):
        who = '我' if role == 'me' else ('系统' if role == 'system' else '她')
        try: dt = datetime.datetime.fromtimestamp(int(ts)).strftime('%m-%d %H:%M:%S')
        except Exception: dt = str(ts)
        text = (content or '').replace('\n', ' ')
        if len(text) > 120: text = text[:117] + '...'
        print(f"[{dt}] {who}: {text}")

if __name__ == '__main__':
    args = list(sys.argv[1:])
    refresh = '-r' in args or '--refresh' in args
    args = [a for a in args if not a.startswith('-')]
    talker, limit = DEFAULT_TALKER, 20
    for a in args:
        if a.isdigit(): limit = int(a)
        else: talker = a
    if refresh: do_refresh()
    show(talker, limit)
```

---

## 七、JSON 格式映射（weflow_live → 笑一档案）

`weflow_live\笑一.json` 字段：

```json
{ "displayName": "笑一", "username": "wxid_wdnk6ue9kiyn22",
  "syncAt": "2026-10-01 20:54:28", "totalCount": 6109,
  "messages": [ { "sender": "wxid_...", "accountName": "笑一",
                  "timestamp": 1778243247, "type": 80,
                  "content": "...", "platformMessageId": "..." } ] }
```

**转换为分析用格式（json/md/txt）：**

| 源字段 | 目标字段 | 转换 |
|--------|----------|------|
| `sender` | `isSend` | `sender == 自己wxid` → 1，否则 0 |
| `timestamp` | `createTime` | 直接赋值（Unix 秒） |
| `type` | `localType` | `type==0` → 1（文本），其他保留 |
| `content` | `content` | 直接赋值 |
| `platformMessageId` | `serverId` | 直接赋值 |

---

## 八、故障速查

| 症状 | 原因 | 处理 |
|------|------|------|
| `ModuleNotFoundError: No module named 'chattrace'` | 用托管 3.13 跑（chattrace 只装在系统 3.12） | 用 `sync_chattrace.py`（自动回退）或显式用 Python312 |
| `刷新实时数据.cmd` 报 `'ING' 不是命令` | 文件是纯 LF 行尾 | 转 CRLF + GBK 保存 |
| 解密报 `0 decrypted, 0 failed` | 微信库无更新 | 正常（无新消息） |
| 解密报密钥错误 | 微信换账号/退出登录 | 重新抓密钥 |
| 索引报"找不到库" | 解密未完成 | 先跑 step 3 |
| 秒查混入别的会话 | 参数解析错误 | 纯数字=条数，非数字=会话wxid |
| 发送者全显示"她" | 用了 `sender` 字段 | 改用 `role` 字段 |
| 消息重复 | 索引有重复记录 | 按 `(ts, content)` 去重 |
| `python` 不是命令 | PATH 未含 Python | 用 `C:\Users\wardc\AppData\Local\Programs\Python\Python312\python.exe` |

---

## 九、安全红线

1. ❌ **不要**同步 `decrypted\` 到网盘（那是**明文**聊天记录）
2. ❌ **不要**外传 `weflow-keys.txt`（SQLCipher 主密钥）
3. ❌ **不要**删 `%LOCALAPPDATA%\ChatTrace\keys\`（删了要重新抓密钥）
4. ❌ **不要**删 `index.sqlite`（重建需全量索引，很慢）
5. ✅ 密钥只在本机、当前 Windows 账户下有效（DPAPI 绑定）

---

## 十、与旧方案（WeFlow）的对比

| 维度 | WeFlow 方案 | ChatTrace 方案 |
|------|-------------|----------------|
| 系统时钟 | 需回拨 -1 天（假时钟） | **不用改** |
| 依赖 | WeFlow + DLL 破解 + 时钟接力脚本 | 只要密钥 |
| 全量拉取 | 33 秒 + 重启 WeFlow | 28 秒（增量） |
| 秒级查询 | 无 | **0.2 秒** |
| 稳定性 | 报 -101 / -105 常见 | 稳定 |
| 计划任务 | 需禁用"锚点漂移自愈" | 无关 |

**结论：WeFlow 已不必要。** 保留它只为了偶尔用它的 GUI 功能（此时需成对使用时钟接力脚本 + 恢复真实时间脚本）。

---

## 十一、本库内的关联文档

| 文档 | 说明 |
|---|---|
| [[WeFlow数据读取路径总表]] | 旧方案（WeFlow HTTP API）的四条链路总表，仍可作为**实时 API** 的参考 |
| [[WeFlow更新部署方案]] | WeFlow 增量链路 SOP |
| [[微信联系人分析-复刻手册]] | 换人照做（9 步） |
| `Desktop\_im_tmp\wechat-mcp\README_交接文档.md` | 微信接 Agent（DSH + clawbot）交接文档 |

> **两套链路的分工**：
> - **ChatTrace**（本文档）→ 解密 + 索引 + 秒查 + JSON 导出，**不依赖 WeFlow**
> - **WeFlow HTTP API** → 仅用于**实时拉取单会话 / 群成员 / 朋友圈**（`/api/v1/sns/timeline` 等 ChatTrace 未覆盖的接口）

---

*本文件可独立用于复现整套流程。核心三件套：`chattrace`（解密）+ `index-incremental.py`（索引）+ `查最新消息.py`（查询）。*
*验证记录：2026-10-03 12:07（本机全项通过）*
