# AI 对话统一归档索引

> 生成于 2026-09-01 | 数据仓库: `unified.db` (SQLite + FTS5) | 169.5 MB

## 数据总览

| 来源 | 消息数 | 会话数 | 用户/助手/工具 | 标题覆盖率 | 存储格式 |
|------|--------|--------|---------------|-----------|----------|
| **Codex** (OpenAI) | 12,988 | 475 | 3,817 / 9,171 / 0 | 92.4% | JSONL rollout + SQLite |
| **Claude Code** | 3,520 | 38 | 36 / 1,652 / 1,832 | 57.9% | JSONL projects |
| **DSH** (DeepSeek Harness) | 3,477 | 85 | 736 / 2,741 / 0 | 94.0% | JSONL Zstd |
| **ZCode** (Trae) | 243 | 6 | 0 / 243 / 0 | 100% | SQLite |
| **Grok** | 5 | 5 | 5 / 0 / 0 | 0% | JSONL prompt_history |

**总计: 20,233 条消息 | 608 个会话**

## 快速入口

### 全文搜索
- **Datasette Web UI:** http://127.0.0.1:8001
- 9 个预置查询: 数据总览、时间线、模型分布、跨工具搜索、工具间引用等
- 搜索框支持中英文关键词

### 常用 SQL 查询

```sql
-- 跨工具搜索
SELECT source, session_id, session_title, substr(content, 1, 300) as preview
FROM conversations WHERE content LIKE '%微信%' ORDER BY timestamp DESC LIMIT 20;

-- 工具间引用
SELECT source, COUNT(*) FROM conversations
WHERE source != 'claude' AND content LIKE '%claude%' GROUP BY source;

-- 会话密度
SELECT source, COUNT(*) as msgs, COUNT(DISTINCT session_id) as sessions,
       ROUND(CAST(COUNT(*) AS REAL) / COUNT(DISTINCT session_id), 1) as avg
FROM conversations GROUP BY source;

-- Claude 工具调用结果
SELECT session_id, timestamp, substr(content, 1, 500) as preview
FROM conversations WHERE source = 'claude' AND role = 'tool' LIMIT 20;
```

## 目录结构
```
conversations/
├── unified.db              ← 统一 SQLite 数据仓库 (169.5 MB, FTS5)
├── metadata.json           ← Datasette 预置查询 (9个)
├── etl.py                  ← 规范 ETL 脚本 (可重复运行, 幂等)
├── README.md               ← 本文件
├── codex/                  ← 硬链接自 ~/.codex/
│   ├── session_index.jsonl
│   ├── state_5.sqlite
│   └── thread_history_1.sqlite
├── claude/                 ← 硬链接自 ~/.claude/
│   ├── history.jsonl
│   └── projects/
├── zcode/                  ← 硬链接自 ~/.zcode/
│   ├── db.sqlite
│   └── rollout/
├── grok/                   ← 硬链接自 ~/.grok/
└── dsh/                    ← 硬链接自 $DSH_HOME/sessions/
    └── sessions/
```

## 模型分布

| 模型 | 出现次数 | 主要来源 |
|------|---------|---------|
| deepseek-v4-pro | 2,587 | DSH + Claude |
| deepseek-v4-flash | 692 | Claude + DSH |
| mimo-v2.5-pro | 621 | Claude + DSH |
| claude-fable-5 | 137 | Claude |
| glm-5.3-flash | 165 | DSH |
| GPT-5.6-Sol / GPT-5 | ~12,000 | Codex |

## 时间线

```
2026-07-01 ───────────────────────────────────── 2026-09-01
  Codex ████████████████████████████████████████████████ (主力)
  Claude     ████████████████████ (7/11 ~ 8/15)
  DSH                    ████████████ (8/15 ~ 9/1)
  Grok               ▌ (8/2 一次性)
  ZCode                         ██ (8/29 ~ 8/31 短暂)
```

## 交叉引用效果

任意关键词可同时命中 3-4 个工具:
- "微信/聊天记录" → 8,709 条 (Codex 7,219 + Claude 706 + DSH 747 + ZCode 35)
- "丝网印刷" → 1,984 条 (Codex 1,568 + Claude 128 + DSH 245 + ZCode 43)
- "人物关系" → 640 条 (Codex 325 + Claude 190 + DSH 125)

工具间引用链路:
- Codex → Claude: 1,347 条
- Codex → DSH: 971 条
- Claude → Codex: 567 条
- DSH → Codex: 153 条

## 更新数据库

```bash
# 完全重建 (所有数据重新导入, 幂等)
python etl.py

# 重建 FTS5 索引
sqlite-utils enable-fts unified.db conversations content session_title --replace

# 重启 Datasette
python -m datasette unified.db --metadata metadata.json --port 8001
```