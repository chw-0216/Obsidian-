# WeChat-MiMo-Analyzer 项目规则

## 目标
无上限全量标注蔡浩文全部微信聊天数据，构建个人记忆系统、深层关系分析、沟通改善和数字分身。

## 数据边界
- WeFlow 导出（只读）：`C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出`
- 数据库：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3`
- 725会话 / 71,550消息 / 6,303片段
- 不修改、移动或删除原始 WeFlow 导出
- 不自动发送微信消息
- Token/密码/密钥不得写入日志或 Git

## MiMo API 连接方式
- 端点：`https://token-plan-cn.xiaomimimo.com/anthropic/v1/messages`
- 认证头：`x-api-key: {ANTHROPIC_AUTH_TOKEN}`
- 版本头：`anthropic-version: 2023-06-01`
- Schema 不走 metadata 字段，必须嵌入 system prompt
- max_tokens 上限 16384
- 配置来源：`~/.claude/settings.json` 的 env 块

## 执行器入口
- 旧版同步：`src/aggressive_executor.py`（urllib，已验证可用，速率 ~9/min）
- 新版异步：`src/async_executor.py`（aiohttp，已完成 Pass A/B/C 验证，待全量部署）
- 诊断：`src/diagnostic.py`
- Stage 0 检查：`src/stage0_check.py`

## 核心约束
1. **成功结果必须保留** — 已入库的标注不得被覆盖或删除
2. **不允许多执行器同时写库** — 同一时间只能有一个进程写入 SQLite
3. **原始数据只读** — WeFlow 导出目录不可修改
4. **证据链完整** — 每个结论必须可追溯到 evidence_id
5. **推断与事实分离** — 模型推断必须标注为推断，不可混入确认事实

## 分析阶段固定优先级
1. 全量标注覆盖（Pass A 消息级 → Pass B 片段级 → Pass C 实体合并）
2. 个人记忆系统（8类记忆）
3. 深层自我与关系判断（五角色法庭 + 反证）
4. 沟通改善系统
5. 数字分身 T0-T2
6. 证据审计与质量评估

## 禁止事项
- 不做心理/医学诊断
- 不推断政治、宗教、性取向、健康等敏感身份
- 不对联系人做价值评分
- 不生成操控/PUA/欺骗策略
