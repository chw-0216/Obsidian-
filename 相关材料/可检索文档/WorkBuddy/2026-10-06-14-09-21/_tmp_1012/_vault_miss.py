# -*- coding: utf-8 -*-
"""把桌面版待补清单做成 Obsidian 可携副本（手机端 Obsidian 可直接看）。"""
import io, os, datetime

SRC = r"C:\Users\wardc\Desktop\07_聊天记录分析\陈晔会话图片_2026-10-14\03_待补图片_手机点开清单.md"
DST = r"C:\Users\wardc\Documents\Obsidian Vault\01_个人信息\项目\陈晔会话-图片待补清单.md"
MIR = r"C:\Users\wardc\Documents\Obsidian Vault\08_多维导航\项目\陈晔会话-图片待补清单.md"

s = io.open(SRC, encoding="utf-8").read()
# 去掉原 H1，换成带 frontmatter 的版本
s = s.split("\n", 1)[1].lstrip("\n")

FM = """---
type: 项目
note_role: 待补工作清单
project: 在场与回应
tags: [项目, 微信聊天, 图片, 待补, 清单, P1]
created: 2026-10-14
updated: 2026-10-14
as_of: 2026-10-14
privacy_scope: private
lifecycle: 当前
status: 54 张待补（★ 项目相关 14 张）
---

# 🖼️ 陈晔会话 · 图片待补清单（可携版）

[[00_个人信息总览|← 总览]] ｜ [[陈晔会话-井邻全梳]] ｜ [[在场与回应-材料与位置总表]]

> [!tip] 怎么用
> **本页专为手机端 Obsidian 准备** —— 在手机上打开这一页，照着表里的日期去微信点开图片。
> 运行时副本（脚本读写）在 `Desktop\\07_聊天记录分析\\陈晔会话图片_2026-10-14\\03_待补图片_手机点开清单.md`。
> 补完后在电脑上重跑 `_tmp_1012\\rebuild_imgs_v2.py`，本页可重新生成。

"""

io.open(DST, "w", encoding="utf-8").write(FM + s)

MIR_T = """---
type: 导航项目
generated_by: 人工补录（2026-10-14）
schema_version: 1
source_audit_version: 2026-10-14-manual
source_note: '[[01_个人信息/项目/陈晔会话-图片待补清单]]'
original_status: 54 张待补（★ 项目相关 14 张）
protected_source: true
relation_count: 3
---

# 陈晔会话 · 图片待补清单（可携版）

来源：[[01_个人信息/项目/陈晔会话-图片待补清单]]

原页状态：54 张待补（★ 项目相关 14 张）。这是原页记载，不代表今天已重新核实。

## 资料与关联

- [[01_个人信息/00_个人信息总览]]
- [[01_个人信息/项目/陈晔会话-井邻全梳]]
- [[01_个人信息/项目/在场与回应-材料与位置总表]]

## 哪些笔记使用它

- [[01_个人信息/项目/在场与回应-材料与位置总表]]

## 调度边界

待补的 54 张**必须靠手机端点开触发下载**，脚本无法代劳。
补完前，任何「陈晔图片已全量归档」的表述都不成立（当前 600/654）。
"""
io.open(MIR, "w", encoding="utf-8").write(MIR_T)

print("写出:", DST)
print("写出:", MIR)
print("字节:", os.path.getsize(DST), os.path.getsize(MIR))
