# 刘华赞 微信分析 · 操作手册（ChatTrace 实时口径）

> 建立时间：2026-10-01
> 状态：✅ 已切换到 **ChatTrace 实时索引**，不再依赖 WeFlow
> 适用对象：本目录（`07_聊天记录分析\刘华赞_微信分析_20260926`）的全部分析与复跑

---

## 一、为什么要切

| | 旧口径（WeFlow） | 新口径（ChatTrace 实时索引） |
|---|---|---|
| 依赖 | WeFlow 客户端必须运行 | **不需要 WeFlow** |
| 系统时钟 | 必须**回拨 -1 天**绕过 DLL 到期 | **不需要改时钟** |
| 权限 | 需要管理员 / UAC | 普通权限 |
| 数据新鲜度 | 手动点导出 | `刷新实时数据.cmd` 三层全刷，≈33 秒 |
| 本次实测 | **WeFlow 未运行，API 5031 拒绝连接** | ✅ 索引最新到 22:53 |

**结论：分析全部改走新口径。** WeFlow 只在"要用它界面"时按用户既有手册临时启动（时钟接力 + 用后恢复），与分析流程解耦。

---

## 二、一条命令刷新 + 一条命令分析

```powershell
# ① 刷新数据（三层：解密 → 索引 → JSON），约 33 秒
#    等价于双击 C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd
cd C:\Users\wardc\Desktop\_im_tmp\chattrace
python -m chattrace.cli data decrypt --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
python index-incremental.py
python gen_live_json.py

# ② 从实时索引导出刘华赞 + 华天雪（本目录专用）
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\export_from_live_index.py"

# ③ 重新统计（可选）
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\moments_stats.py"
```

产物：

| 产物 | 路径 |
|------|------|
| 原始消息档 | `00_原始导出\实时_刘华赞（赞赞姐）_聊天记录.{json,md,txt}` |
| 原始消息档（其母） | `00_原始导出\实时_华天雪_聊天记录.{json,md,txt}` |
| 统计 | `02_结构化分析\metrics_live.json` |
| 消息表 | `02_结构化分析\messages_live.csv` |

---

## 三、本次已做的修复（重要）

### 3.1 索引历史去重缺陷（已修）

**症状**：`index.sqlite` 由两个写入者先后写入，历史区间同一消息存了两份。

| 组 | id 区间 | type 标签 | time_text | 行数 |
|----|---------|-----------|-----------|------|
| A（旧索引） | 1 ~ 151064 | 中文（文本消息…） | 完整 | 151,064 |
| B（增量索引） | 151065 ~ | 英文（text…） | **全空** | 194,047 |

`index-incremental.py` 的去重集合只回溯 `before_max - 86400*3`（3 天），**历史区间拦不住**，于是 A、B 各存一份。

**修法**：只删除"两边计数相同（1:1）"的 B 组那一份，保留 A 组（`time_text` 完整、type 为中文标签）。

```powershell
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
python repair_index_dedupe.py --dry-run   # 先看要删什么
python repair_index_dedupe.py --apply     # 备份 + 删除 + 重建 FTS
```

**本次结果**：

```
messages: 345111 → 318863  （删除 26248 行）
messages_fts: 318863       （rowid 对不上的: 0）
A 组独有键仍保留: 124697    （未被误删）
[wxid_ltqmzbyc87cp22] 22 行（= 21 条唯一消息）
[wxid_jycd1ii1qxro22] 3 行
```

备份：`index.sqlite.bak-dedupe-20261001-223534`（可整文件还原）。

### 3.2 建议给 `index-incremental.py` 打的补丁

**(a) 最小改动**：把去重集合从"近 3 天"改成"该会话全部"。
在循环内按会话取已存在的键，而不是全局回溯 3 天：

```python
# 现在（第 120-124 行）：全局、只回溯 3 天
for sk, ts, ct in idx.execute(
        "SELECT session_key, ts, substr(content,1,80) FROM messages WHERE ts >= ?", (before_max - 86400 * 3,)):

# 建议：按会话懒加载（第一次遇到某 sid 时把该会话的键全读进来）
def load_seen(sid):
    return {(r[0], r[1]) for r in idx.execute(
        "SELECT ts, substr(content,1,80) FROM messages WHERE session_key=?", (sid,))}
```

**(b) 更彻底**：加真正的唯一约束，让重复插入直接失败。

> ⚠️ 注意：**SQLite 不支持在 UNIQUE INDEX 里用表达式**（`substr(...)` 会报
> `expressions prohibited in PRIMARY KEY and UNIQUE constraints`），所以不能直接对
> `substr(content,1,120)` 建唯一索引。可行做法是**新增一列显式存去重键**：

```sql
ALTER TABLE messages ADD COLUMN dedup_key TEXT;
UPDATE messages SET dedup_key = session_key || char(1) || ts || char(1) || substr(content,1,120);
CREATE UNIQUE INDEX IF NOT EXISTS ux_msg_dedup ON messages(dedup_key);
-- 之后写入改为：INSERT OR IGNORE INTO messages(..., dedup_key) VALUES (..., ?)
```

（已建的 `repair_index_dedupe.py` 就是按同样的键定义做的一次性清理，两者口径一致。）

---

## 四、实时索引的已知特性（踩坑记录）

| 现象 | 事实 | 应对 |
|------|------|------|
| `time_text` 大量为空（167,850 / 318,914） | 增量写入的行没写 `time_text`，但 **`ts` 全部有效** | **一律用 `ts` 换算时间**，不要用 `time_text` 过滤 |
| `sessions.message_count` 偏大（刘华赞显示 24，实际 22） | 增量 upsert 是 `message_count = 原值 + 新增` 累加，叠加了重复插入 | 以 `count(*) from messages` 为准 |
| 同一秒出现两行相同内容 | 微信原始库确有重复行 + 增量重扫 | 导出脚本已按 `(ts, content)` 去重 |
| `LIKE '%赞赞%'` 命中群聊 | 群里"赞赞赞"是夸奖词，非人名 | 检索后用 `role <> 'system'` + 会话名人工过滤 |
| 索引文件被别处持续写入 | 观察到 22:44-22:53 有新消息实时进库（另一会话） | 跑分析时**只读**（`mode=ro`），不要并发整库重建 |

---

## 五、源一致性核验（2026-10-01）

同一对象，两条独立路径得到一致结果：

| 项 | WeFlow API（旧，历史采集） | ChatTrace 实时索引（新） | 一致？ |
|----|---------------------------|--------------------------|--------|
| 刘华赞消息数 | 21 | 22 行 → 去重 21 条 | ✅（差 1 行是同秒重复的表情包） |
| 我 / 对方 | 14 / 7 | 14 / 8 → 去重后 14 / 7 | ✅ |
| 时间范围 | 2025-01-29 ~ 2026-09-25 | 同 | ✅ |
| 华天雪消息数 | 3 | 3 | ✅ |
| 上游地面真值（解密库 `Msg_<md5>`） | — | 刘华赞 17+4=21 行、华天雪 3 行 | ✅ 与两边都吻合 |
| **2026-09-25 之后是否有新消息** | — | **无**（刘华赞最新仍为 09-25 18:50） | — |

> 也就是说：**换了数据源，结论不变**；刘华赞在过去 5 天没有新的互动。

---

## 六、下次要跑什么

1. **日常**：跑第二节的 ①②，30 秒内拿到最新消息；如果 `metrics_live.json` 的"消息总数"从 21 变多，就说明她有新互动了。
2. **朋友圈**：朋友圈不走这套（走 `sns.db` / WeFlow `sns` 接口），别忘她朋友圈才是信息量大的地方。
3. **换机/清理前**：本目录 `00_原始导出\` 与 `02_结构化分析\` 整体备份——她不产生新消息，丢了就永久丢失。

---

*手册版本 v1.0 ｜ 2026-10-01 ｜ 与用户既有《运行手册 · 微信实时分析 + WeFlow 共存》配套使用*
