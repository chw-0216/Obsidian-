# wechat-personal-ai 项目规则

## 目标

为数据所有者蔡浩文设计并实现本地优先的微信聊天多轮分析系统：记忆系统 + 沟通教练 + 数字分身。

## 当前模式

`DESIGN_ONLY` — 只生成框架文件，不运行数据分析，不读取聊天正文，不调用远程模型，不安装依赖。

## 数据边界

- WeFlow 导出目录（只读）：`C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出`
- 旧系统数据库：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3`
- 用户已确认：全部私聊正文可分析、联系人姓名可保留、不做脱敏
- Token 不写入日志或 Git

## 模式门

切换运行模式必须在 `config/permissions.yaml` 中显式修改 `RUN_MODE`，并由用户审批。

## 六轮分析顺序

R0 → R1 → R2 → R3 → R4 → R5，每轮需用户确认后才能进入下一轮。

## 证据链要求

每个结论必须可追溯到 `segment_id` 或 `evidence_message_ids`。不能把模型推测当作事实。

## 禁止事项

- 不做心理/医学诊断
- 不推断政治、宗教、性取向、健康等敏感身份
- 不对联系人做"价值评分"
- 不生成操控、PUA、欺骗或逼迫策略
- 不自动发送消息或回复
