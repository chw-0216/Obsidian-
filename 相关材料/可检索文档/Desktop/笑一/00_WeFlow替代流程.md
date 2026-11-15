# WeFlow → ChatTrace 替代流程（日常操作手册）

> 更新：2026-10-04 | 目标：不用 WeFlow、不改系统时钟，完成原有全部数据读取工作

---

## 一、功能映射（WeFlow 有什么 → 现在用什么替代）

| WeFlow 原功能 | WeFlow 用法 | ChatTrace 替代 | 耗时 |
|--------------|------------|---------------|------|
| **拉单会话消息** | `GET http://127.0.0.1:5031/api/v1/messages?talker=xxx` | `python 查最新消息.py wxid_xxx 50` | **0.2秒** |
| **全量导出 JSON** | 脚本分页拉取 + 写文件 | `python gen_live_json.py` | 0.4秒 |
| **刷新数据** | 重启 WeFlow（22秒）+ 拉取 | 三层刷新（解密+索引） | ~30秒 |
| **关键词搜索** | 不支持（需自己遍历） | `messages_fts` 全文索引 | 秒级 |
| **群消息** | `talker=xxx@chatroom` | SQL 查 `session_key LIKE '%chatroom%'` | 0.2秒 |
| **会话列表** | `/api/v1/sessions` | SQL: `GROUP BY session_key` | 0.2秒 |
| **朋友圈** | `/api/v1/sns/timeline` | `sns.db` 已解密，可直接查 | — |
| **群成员** | `/api/v1/group/members` | `contact.db` 已解密 | — |

**结论：日常的"读消息/导出/搜索"全部可替代，且更快。** 只有朋友圈/群成员这类 WeFlow 独有接口需要时，才临时启用 WeFlow。

---

## 二、日常三条命令（覆盖 95% 场景）

### 1. 看最新消息（最常用，0.2秒）
```powershell
python C:\Users\wardc\Desktop\笑一\查最新消息.py           # 笑一 最新20条
python C:\Users\wardc\Desktop\笑一\查最新消息.py 50        # 最新50条
python C:\Users\wardc\Desktop\笑一\查最新消息.py wxid_xxx 30  # 指定会话
```

### 2. 刷新数据（约30秒，看新消息前跑一次）
```powershell
python C:\Users\wardc\Desktop\笑一\查最新消息.py -r 20     # 刷新+查看（一条命令搞定）
```
或双击：`C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd`

### 3. 导出全量 JSON（分析脚本用）
```powershell
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
python gen_live_json.py
# 产出：C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\*.json
```

---

## 三、底层三层（出问题时才需要单独跑）

```powershell
$env:PYTHONIOENCODING='utf-8'

# [1] 解密（微信加密库 → 明文库）
cd C:\Users\wardc\Desktop\_im_tmp\chattrace
python -m chattrace.cli data decrypt --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
# 预期：result: N decrypted, M fresh, 0 failed of 22 DBs

# [2] 索引（明文库 → index.sqlite）
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
python index-incremental.py
# 预期：并入后: 32xxxx 条 (+N), 最新 yyyy-mm-dd HH:MM

# [3] JSON（index.sqlite → weflow_live/*.json）
python gen_live_json.py
```

---

## 四、常用 SQL（替代 WeFlow 的 API 查询）

**连接**：`C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite`（只读打开）

```sql
-- ① 某会话最新 20 条
SELECT role, ts, content FROM messages
WHERE session_key = 'wxid_wdnk6ue9kiyn22'
ORDER BY ts DESC LIMIT 20;

-- ② 某会话某天的消息
SELECT role, datetime(ts,'unixepoch','localtime'), content FROM messages
WHERE session_key = 'wxid_wdnk6ue9kiyn22'
  AND ts BETWEEN strftime('%s','2026-10-03 00:00:00') AND strftime('%s','2026-10-04 00:00:00')
ORDER BY ts;

-- ③ 最近活跃会话 TOP15
SELECT session_key, COUNT(*) AS n, datetime(MAX(ts),'unixepoch','localtime') AS last
FROM messages GROUP BY session_key ORDER BY MAX(ts) DESC LIMIT 15;

-- ④ 关键词全文搜索（messages_fts）
SELECT session_key, datetime(ts,'unixepoch','localtime'), content
FROM messages_fts WHERE messages_fts MATCH '蓝色港湾' LIMIT 20;

-- ⑤ 我只发的消息 / 她只发的消息
SELECT datetime(ts,'unixepoch','localtime'), content FROM messages
WHERE session_key='wxid_wdnk6ue9kiyn22' AND role='me' ORDER BY ts DESC LIMIT 20;

-- ⑥ 统计某会话双方消息量
SELECT role, COUNT(*) FROM messages
WHERE session_key='wxid_wdnk6ue9kiyn22' GROUP BY role;
```

---

## 五、数据位置对照

| 数据 | WeFlow 时代 | ChatTrace 现在 |
|------|------------|---------------|
| 加密库 | `C:\Users\wardc\xwechat_files\...` | 同左（源头不变） |
| 解密库 | WeFlow 内部处理 | `%LOCALAPPDATA%\ChatTrace\accounts\...\decrypted\` |
| 索引 | 无 | `_im_tmp\wechat-mcp\index.sqlite`（320MB） |
| 单会话 JSON | `weflow_live\笑一.json` | **同路径**（格式同构，分析脚本不用改） |
| 笑一档案 | `Desktop\笑一\01_最新聊天记录\` | 同左（从 weflow_live 转换） |

---

## 六、仍需 WeFlow 的场景（少数）

| 场景 | 做法 |
|------|------|
| 朋友圈时间线 | 查 `decrypted\sns\sns.db`（已解密） |
| 群成员名单 | 查 `decrypted\contact\contact.db` |
| WeFlow GUI 界面 | 需成对跑：`WeFlow应急启动_时钟接力.ps1`（时钟-1天）→ 用完 → `恢复真实时间.bat`（+1天） |

**⚠️ 时钟脚本必须成对使用**，只回拨不恢复会让系统时间一直错。

---

## 七、故障速查

| 症状 | 处理 |
|------|------|
| 查不到新消息 | 先跑 `-r` 刷新；仍没有 → 电脑微信打开该聊天窗口同步 |
| `刷新实时数据.cmd` 报 `'ING' 不是命令` | 文件被存成 LF 行尾 → 转 CRLF + GBK |
| 解密报密钥错误 | 微信换账号了 → 需重新抓密钥 |
| 解密 `N failed` | 微信正在写库 → 等几秒重跑 |
| 发送者显示全"她" | 应用 `role` 字段而非 `sender` |
| 消息重复 | 按 `(ts, content)` 去重 |

---

## 八、一页速查（存这个）

```powershell
# 看最新（0.2秒）
python C:\Users\wardc\Desktop\笑一\查最新消息.py

# 刷新+看（30秒）
python C:\Users\wardc\Desktop\笑一\查最新消息.py -r 20

# 全量导出
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp; python gen_live_json.py
```

**核心：日常不再需要 WeFlow、不再需要改时钟。三件套 = chattrace（解密）+ index-incremental.py（索引）+ 查最新消息.py（查询）。**
