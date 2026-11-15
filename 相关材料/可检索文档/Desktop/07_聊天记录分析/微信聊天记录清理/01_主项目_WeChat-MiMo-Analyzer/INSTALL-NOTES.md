# WeChat MiMo Analyzer 安装与变更记录

## 概况

- 创建日期：2026-08-02
- 类型：本地自建私聊清洗、检索与 MiMo 标注框架
- 项目目录：`C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer`
- 数据源：`C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出`
- 数据源权限：只读扫描；未移动、修改或删除 WeFlow 导出和微信原始数据。

## 使用的现有环境

- Python 3.12.10
- SQLite 3.49.1，FTS5 可用
- Claude Code 2.1.195
- MiMo 模型：`mimo-v2.5-pro`

本项目没有安装 Python 包、全局包、服务、计划任务或系统驱动，没有修改 PATH、注册表或永久环境变量。

## 生成内容

- 源代码、配置、测试和说明均位于项目目录。
- 当前数据库：`data\wechat-private-v2.sqlite3`。
- 首次调试产生的不完整派生数据库已移动至 `data\obsolete\wechat-private-initial-obsolete.sqlite3`，仍可恢复或删除。
- 报告：`reports\overview.md` 和 `reports\overview.json`。

## 数据验证

- 发现私聊目录：3025 个。
- 有文件且含详细 JSON：725 个。
- 空目录：2300 个。
- 有效 JSON：725；无效 JSON：0。
- 消息：71,550 条。
- 对话片段：6,303 个。
- FTS5 索引：71,550 条。
- SQLite `integrity_check`：`ok`。
- 单元测试：2 项全部通过。
- Claude Code + MiMo 严格 JSON Schema 测试：通过。
- 真实小样本：3 个片段标注成功，结果已写入数据库。

## 隐私与外部传输

- `ingest`、`report` 和原文 `search` 只在本机运行。
- `pilot` 和 `analyze` 会通过 Claude Code 把选中的聊天片段发送至已配置的小米 MiMo Token Plan 接口。
- 默认不发送真实联系人名称，并对常见手机号、邮箱、身份证号、银行卡号和 IP 做确定性脱敏。
- 自动脱敏不能保证识别全部个人信息；不要把项目数据库或报告公开上传。
- MiMo Token 沿用用户级 Claude Code 配置，本项目没有保存 Token 明文。

## 清理方式

1. 退出正在运行的分析命令。
2. 删除整个 `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer` 文件夹，即可移除代码、派生数据库和报告。
3. 删除本项目不会影响 WeFlow、Claude Code、MiMo 配置、桌面 WeFlow 导出或微信原始数据。
4. 若只需重新分析，可保留项目并删除 `data` 中的派生数据库后重新运行 `ingest`；删除前应先确认是否需要保留既有标注。
