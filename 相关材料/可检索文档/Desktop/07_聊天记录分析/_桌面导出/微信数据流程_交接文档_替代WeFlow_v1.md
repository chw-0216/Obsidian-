# 微信数据流程 · 交接文档（ChatTrace 方案 · 替代 WeFlow）

| 项 | 值 |
|----|-----|
| 文档版本 | v1.0 |
| 编写时间 | 2026-10-02 05:25 |
| 适用账号 | `wxid_zn4ozsnn8esr21_db45`（微信 4.1.12.26） |
| 状态 | ✅ 生产可用 —— **已完全替代 WeFlow** |
| 前置阅读 | 本文档可独立交接，无需其他背景 |

---

# 一、一句话结论

> **WeFlow 已不必再用。** 它的 DLL 内置有效期止于 2026-09-30 23:59:59，到期后原生层硬性拒绝（错误码 -101），且不可通过任何常规手段修复。
>
> 现在改用 **ChatTrace**：直接用**已拿到的 SQLCipher 主密钥**解密微信库 → 建索引 → 出 JSON。
> **不依赖 WeFlow、不改系统时钟、不需要重新抓密钥。**

---

# 二、为什么必须替代 WeFlow（故障史，避免重走弯路）

## 2.1 现象

| 时间点 | 现象 |
|--------|------|
| 2026-09-30 23:59 之前 | WeFlow 正常 |
| 2026-10-01 起 | API 全部 `HTTP 500 {"error":"错误码: -101"}` |
| 日志 | `[bootstrap] native runtime policy mismatch value=-101` |

## 2.2 官方释义（从 `app.asar` 内 `wcdbWorker.js` 解出）

```
-101  当前电脑环境异常，请关闭杀毒软件和安全防护后重试；仍然失败请更换电脑
-102  检测到系统时间回拨，离线运行状态无法验证
-104  检测到调试或分析环境，组件已拒绝运行
-105  离线防回拨状态损坏或无法安全保存，请检查当前用户目录权限
```

## 2.3 已逐一验证无效的修复手段（**不要再试**）

| 手段 | 结果 |
|------|------|
| 重建状态目录 `Runtime/Security/State` | ❌ 无效 |
| 删除注册表锚点 `HKCU\Software\WeFlow` | ❌ 无效（已备份 .reg） |
| 打补丁越过 JS 侧检查（`t!==1464206081` → 容忍） | ❌ 越过第一道后，DLL 在第二道 `wcdb_authenticate` **同样返回 -101** 硬拒绝 |
| 关闭杀毒软件 | ❌ 已排除（仅 Windows Defender，且非根因） |
| 检查微信版本变动 | ❌ 已排除（4.1.12.26，7/25 至今未变） |

## 2.4 唯一有效的"续命"手段（仅作历史记录）

回拨系统时钟 1 天 → DLL 落回有效期内 → 可临时使用。
**但这已不必要**，因为密钥已拿到。相关脚本仍保留在：
`C:\Users\wardc\Desktop\07_聊天记录分析\weflow_extract\WeFlow修复_20260824\脚本\`

---

# 三、新架构（数据链路）

```
微信手机端
   ↓（电脑微信接收）
C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\     ← 加密库（22 个）
   ↓ ① ChatTrace 解密（用已保存的 SQLCipher 主密钥）
%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\
   ↓ ② 建索引
C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite      ← 检索索引（机器人/MCP）
   ↓ ③ 出 JSON
C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\*.json    ← 与原 WeFlow 同构，下游脚本零改动
```

**三条出口互不影响**，任一出问题不影响其他两条。

---

# 四、核心资产清单

## 4.1 🔑 密钥（最高保护级别）

| 项 | 值 |
|----|-----|
| 路径 | `%LOCALAPPDATA%\ChatTrace\keys\wxid_zn4ozsnn8esr21_db45@4.1.12.26.keyinfo` |
| 大小 | 0.48 KB |
| 保护方式 | **Windows DPAPI 加密**（绑定当前用户） |
| 有效期 | **永久** —— SQLCipher 主密钥，不绑时间、不绑 WeFlow |
| 备份 | 另有一份明文在 `apps\WeFlow\key-export-20261001\weflow-keys.txt` ⚠️**敏感，勿外传** |

**唯一失效情形**：微信退出登录 / 换账号 → 微信重新生成密钥，需重新抓取。

## 4.2 解密库

| 项 | 值 |
|----|-----|
| 根目录 | `%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\` |
| 子目录 | `message / session / contact / sns / head_image / general / emoticon / favorite / hardlink / migrate / solitaire / bizchat` |
| 关键库 | `message\message_0.db`（962MB，历史主体）、`message\message_1.db`（95MB，最新增量）、`biz_message_0.db`（73MB） |
| ⚠️ 注意 | **明文聊天记录，禁止同步到网盘** |

## 4.3 索引库

| 项 | 值 |
|----|-----|
| 路径 | `C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite` |
| 大小 | 约 319 MB |
| 表 | `messages`（id, session_key, ts, time_text, role, sender, type, content）+ `messages_fts` + `sessions` |
| 用途 | 微信机器人 / MCP 检索 |
| ⚠️ 注意 | **不要删** —— 重建需重新全量索引 |

## 4.4 主程序

| 项 | 值 |
|----|-----|
| ChatTrace 版本 | **0.5.1** |
| 位置 | `C:\Users\wardc\Desktop\_im_tmp\chattrace` |
| 调用 | `python -m chattrace.cli <子命令>` |
| 子命令 | `doctor / key / keyagent / data / chat / export / webui` |

---

# 五、日常操作（三个场景）

## 场景 A：刷新数据（最常用）

```powershell
# 双击或命令行
C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd
```

三层全刷，实测约 **30 秒**：

| 步骤 | 命令 | 产物 |
|------|------|------|
| 1 解密 | `python -m chattrace.cli data decrypt --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"` | `decrypted\` |
| 2 索引 | `python index-incremental.py` | `index.sqlite` |
| 3 JSON | `python gen_live_json.py` | `weflow_live\*.json` |

> 手动跑时注意：`刷新实时数据.cmd` 末尾有 `pause`，非交互场景请分步执行上面三条命令。

## 场景 B：秒查某个人的最新消息

**两个联系人要用不同工具**（原因见第七节）：

```powershell
# 导（陈晔）—— 直读原始解密库
cd C:\Users\wardc\Desktop\导
python 查最新消息.py            # 最新20条，0.5秒
python 查最新消息.py 30         # 最新30条
python 查最新消息.py -r         # 先刷新再查
python 查最新消息.py -j         # 导出完整JSON

# 笑一 —— 读索引库
python C:\Users\wardc\Desktop\笑一\查最新消息.py
```

## 场景 C：导出某会话的完整记录（含图片媒体）

```powershell
cd C:\Users\wardc\Desktop\_im_tmp\chattrace
python -m chattrace.cli export ^
  --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45" ^
  --user deerluna --format html --media ^
  --since "<起始unix秒>,0" --out "C:\输出路径\xxx.html"
```

`--media` 会把图片/语音/视频解出到同名的 `_assets` 文件夹。

---

# 六、迁移对照表（WeFlow 操作 → 新方案）

| 原 WeFlow 操作 | 新方案 | 备注 |
|----------------|--------|------|
| 启动 WeFlow 界面 | **不需要** | 如确需，用时钟接力脚本 |
| 导出聊天记录（GUI） | `chattrace export` | 支持 txt/json/html |
| 导出含媒体 | `chattrace export --media` | 出 `_assets` 文件夹 |
| HTTP API `/api/v1/messages` | `查最新消息.py` 或直查 `index.sqlite` | 更快 |
| HTTP API `/api/v1/contacts` | `sessions` 表 或 `contact` 库 | — |
| 微信实时刷新 | `刷新实时数据.cmd` | 30 秒 |
| 年度报告 | 解析 `index.sqlite` / `weflow_live\*.json` | 数据同构 |

---

# 七、⚠️ 各会话的取数方式差异（**最容易踩的坑**）

| 联系人 | 推荐数据源 | 原因 |
|--------|-----------|------|
| **导（deerluna）** | **直读原始解密库** | 索引里只有约 **5,100 条**，原始库有 **7,100+ 条** —— 索引对导不完整 |
| 笑一（wxid_wdnk6ue9kiyn22） | 索引库 `index.sqlite` | 索引完整（6,100+ 条） |
| 米雪 / 立项2群 | `gen_live_json_extra.py` | 用 `_sync_state.json` 之外的独立导出 |
| 其他私聊/群 | 先查 `sessions` 表确认 `message_count`，再决定 | 对比原始库条数校验 |

**通用判据**：`sessions.message_count` 明显小于原始库表行数 → 用直读原始库的方式。

---

# 八、已修复的缺陷（含日期与修法，勿重复踩坑）

## 8.1 【严重】索引发送者错标 —— 2026-10-01 修复

| 项 | 内容 |
|----|------|
| 现象 | 9/30 起的消息 **`role` 全部变成 `them`**（连自己发的"我错了"也标成对方）；私聊里出现**群号当发送者** |
| 根因1 | `index-incremental.py` 第 27 行 `MY = "wxid_zn4ozsnn8esr21_db45"`，但解密库里自己的 wxid 是 **`wxid_zn4ozsnn8esr21`**（无 `_db45`）→ `who == MY` 恒为假 |
| 根因2 | 同一会话表 `Msg_<md5(talker)>` **分布在多个库**，各库 `Name2Id` 的 rowid 空间不同（导：message_0 是 10/395，message_1 是 2/107）→ 用错库的映射就会解析成群号 |
| 修复1 | `MY` 改前缀匹配 `MY_ROOT`，并加私聊兜底（非我即对方，绝不写群号） |
| 修复2 | 索引历史错标 **191 条 / 7 个会话** 全部回写修正，剩余 0 |
| 备份 | `index.sqlite.bak-before-repair-20261001_205601` |
| 验证 | 修复后导出导 7,102 条，与 WeFlow 窗口版 7,090 条吻合 |

## 8.2 其他

| 问题 | 原因 | 修复 |
|------|------|------|
| `刷新实时数据.cmd` 报错 `'ING' 不是命令` | 文件是**纯 LF 行尾**，cmd 解析吞字符 | 改 CRLF + GBK，备份 `.bak-lf` |
| 秒查混入其他会话 | 参数解析 bug（`-r 15` 被当成会话名） | 纯数字=条数，非数字=会话 |
| 重复消息 | 索引有多条相同记录 | 按 `(ts, content)` 去重 |
| 发送者显示全为"她" | 误用 `sender` 字段 | 改用 `role`（me/them/system） |

---

# 九、故障速查

| 症状 | 原因 | 处理 |
|------|------|------|
| `chattrace` 报密钥错误 | 微信换账号/退出登录 | 重新抓密钥（见 4.1） |
| 解密失败 | 微信未登录 | 登录电脑微信后重跑 |
| 索引条数不增 | 无新消息 / 解密未跑 | 先跑 ① 解密，再跑 ② 索引 |
| 查导条数明显偏少 | 用了 `index.sqlite` | **改用 `导\查最新消息.py`**（直读原始库） |
| 消息角色颠倒 | 索引器旧 bug 复发 | 检查 `index-incremental.py` 的 `MY_ROOT` 是否在位 |
| JSON 缺某个会话 | `_sync_state.json` 未含该会话 | 用 `gen_live_json_extra.py` 或加进水位 |
| 机器人查不到新消息 | 网关读旧数据 | 重跑刷新；必要时重启网关（`server.mjs`，端口 3080） |
| 时间显示差 8 小时 | 用了 UTC 渲染 | 检查 `server.mjs` 的 `fmtTime` 应为本地时区 |
| WeFlow 报 -101 | DLL 到期（历史问题） | **不用管，已弃用** |

---

# 十、红线（不要做的事）

| ❌ 不要 | 原因 |
|--------|------|
| 删 `%LOCALAPPDATA%\ChatTrace\keys\` | 密钥丢了要重新抓（需 Frida 注入运行中的微信） |
| 删 `index.sqlite` | 重建需全量索引 |
| 把 `decrypted\` 同步到网盘 | 那是**全部聊天记录的明文** |
| 把 `weflow-keys.txt` 外传 | 明文密钥，等同账号 |
| 用局域网 IP 访问网关 | 系统代理会截胡，用 `127.0.0.1:3080` |
| 重新启用 `WeFlow锚点漂移自愈` 计划任务 | 会每分钟偷改系统时间 |
| 为了用 WeFlow 而回拨系统时钟 | 已无必要；且会让文件时间戳、证书校验出错 |

---

# 十一、回滚方案（仅当你确实要用 WeFlow 界面）

旧方案**仍可用但已不必要**。需要时：

```powershell
# 1) 启动（系统时间 -1 天，需管理员/UAC）
C:\Users\wardc\Desktop\07_聊天记录分析\weflow_extract\WeFlow修复_20260824\脚本\WeFlow应急启动_时钟接力.ps1

# 2) 用完必须成对恢复
...\脚本\恢复真实时间.bat
```

⚠️ **两个脚本必须成对使用**，只回拨不恢复会让时钟一直错 1 天。

---

# 十二、交接最小集（新接手人/新 Agent 只需知道这些）

1. **别再修 WeFlow。** DLL 到期，已弃用。
2. **主流程**：`刷新实时数据.cmd`（30 秒，三层全刷）。
3. **查导**：`C:\Users\wardc\Desktop\导\查最新消息.py`（**不要**用索引库，会少 2000 条）。
4. **查笑一**：`C:\Users\wardc\Desktop\笑一\查最新消息.py`。
5. **查媒体**：`chattrace export --media`。
6. **密钥永不删**（`%LOCALAPPDATA%\ChatTrace\keys\`）。
7. **明文不外传**（`decrypted\`、`weflow-keys.txt`）。

---

# 附录 A：文件清单速查

| 类别 | 路径 |
|------|------|
| 主程序 | `C:\Users\wardc\Desktop\_im_tmp\chattrace` |
| 密钥 | `%LOCALAPPDATA%\ChatTrace\keys\` |
| 解密库 | `%LOCALAPPDATA%\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\` |
| 索引 | `C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite` |
| JSON 出口 | `C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\` |
| 刷新脚本 | `...\wechat-mcp\刷新实时数据.cmd` |
| 索引器 | `...\wechat-mcp\index-incremental.py`（**已打补丁**） |
| JSON 生成 | `...\wechat-mcp\gen_live_json.py` / `gen_live_json_extra.py` |
| 网关 | `...\wechat-mcp\server.mjs`（端口 3080） |
| 导出工具（导） | `C:\Users\wardc\Desktop\导\查最新消息.py` |
| 新媒体导出 | `chattrace export --media`（见场景 C） |
| 微信源库 | `C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45\` |
| 微信附件 | `...\xwechat_files\...\msg\attach\<md5(talker)>\<年-月>\Img\` |

# 附录 B：实测性能

| 操作 | 耗时 |
|------|------|
| 秒查最新消息 | **0.5 秒** |
| 全量刷新（解密+索引+JSON） | **约 30 秒** |
| 其中：解密 | 22—27 秒（22 个库，只处理有变化的） |
| 其中：索引 | 4—6 秒 |
| 其中：JSON | <1 秒 |
