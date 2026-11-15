---
name: claude-workspace-rule
description: 永久规则 — Claude 所有创建/下载/安装/部署的文件必须归入 Desktop\Claude工作区 并在登记册.md 登记
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 99dc6bc0-589d-481a-ac8c-900371f306a6
---

用户于 2026-07-10 定下的永久规则：凡是 Claude / Claude Code 产出的文件（GitHub 克隆、生成的图片、写的脚本、部署建立的文件、下载安装的东西），一律放进 **`C:\Users\wardc\Desktop\Claude工作区\`**，不要散落在桌面或别处。

子文件夹：`01_GitHub项目`、`02_脚本与工具`、`03_文档与说明`、`04_图片与输出`、`05_维护与记录`。

每次产生新文件后，必须同步更新 **`Claude工作区\登记册.md`**：
- **表一（文件登记表）**：日期 + 文件名 + 位置 + 干什么用的（写详细）。
- **表二（权限与设置变更表）**：任何权限授予、系统设置、注册表、启动项、环境变量、软件安装卸载等改动，都要记日期 + 变更内容 + 目的。

**Why:** 用户此前 Claude 产出的文件散落桌面各处，难以追溯哪个文件是什么、什么时候改过什么设置；要求集中归口 + 台账管理，永久执行。

**How to apply:** 新建文件时直接以 Claude工作区 对应子文件夹为目标路径（临时中间文件仍用 scratchpad）；会话结束前检查是否有新文件/设置改动未登记。例外：`.claude` 项目配置必须留在项目根目录；用户个人内容文档（如简历）按用户指定位置放。绝不移动/删除父亲的医疗资料，见 [[do-not-delete-father-medical]]。相关：[[dev-environment]]、[[machine-health-g15]]。
