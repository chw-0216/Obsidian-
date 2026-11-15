# Codex Config 回滚 / 恢复方法

## 快速恢复：一步还原到修复前状态

如果修复后出现新问题，可从备份恢复：

```powershell
# 恢复修复前的 DSCodex 注入版（路由到 10110）
Copy-Item "$env:USERPROFILE\.codex\config.toml.bak-before-native-route-restore-20260808-190927" `
          "$env:USERPROFILE\.codex\config.toml" -Force
```

---

## 恢复 DSCodex 完整功能

如果要重新启用 DSCodex（DeepSeek V4 Pro + GPT 路由）：

```powershell
cd C:\Users\wardc\tools\dscodex

# 1. 重新注入 Codex 配置
node src/cli.mjs install

# 2. 启动路由器
node src/cli.mjs start

# 3. 验证
node src/cli.mjs doctor

# 4. （可选）开机自启
node src/cli.mjs autostart enable
```

---

## 恢复 DSCodex 前的干净状态

如果 DSCodex install 失败（配置已被修改），先恢复干净状态：

```powershell
# 恢复到 DSCodex 安装前的快照
Copy-Item "$env:USERPROFILE\.codex\config.toml.pre-dscodex.bak" `
          "$env:USERPROFILE\.codex\config.toml" -Force
```

然后重新运行 `node src/cli.mjs install`。

---

## 完全移除 DSCodex

```powershell
cd C:\Users\wardc\tools\dscodex

# 停止路由器并清理配置
node src/cli.mjs uninstall
node src/cli.mjs stop
node src/cli.mjs autostart disable
```

---

## 关键文件速查

| 文件 | 路径 |
|---|---|
| 当前配置 | `~/.codex/config.toml` |
| 修复前快照 | `~/.codex/config.toml.bak-before-native-route-restore-20260808-190927` |
| DSCodex 安装前 | `~/.codex/config.toml.pre-dscodex.bak` |
| OpenCodex 配置 | `~/.opencodex/config.json` |
| OpenCodex profile | `~/.codex/opencodex.config.toml` |
| DSCodex 源码 | `C:\Users\wardc\tools\dscodex\` |
| 回滚目录 | `~/.codex/rollback-20260808/` |

---

## DSCodex 常用命令

```powershell
cd C:\Users\wardc\tools\dscodex

node src/cli.mjs status        # 路由器运行状态
node src/cli.mjs doctor        # 完整诊断（6 项检查）
node src/cli.mjs start         # 启动路由器
node src/cli.mjs stop          # 停止路由器
node src/cli.mjs install       # 注入 Codex 配置
node src/cli.mjs uninstall     # 移除 Codex 配置注入
node src/cli.mjs key status    # DeepSeek API Key 状态
node src/cli.mjs proxy status  # 代理状态
node src/cli.mjs sync          # 刷新 GPT 模型目录
```
