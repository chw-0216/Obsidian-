---
tags: [接入, AI, 说明, 导航]
created: 2026-10-04
updated: 2026-10-04
priority: 高
---

# 🤖 AI 接入说明（任何 harness 通用）

> **给谁看**：任何要读这套分析的 AI —— Claude Code / Cursor / Windsurf / Cline / Roo / Codex CLI / Aider / ChatGPT / 本地 Ollama …
> **怎么用**：把这个文件的**路径**（或内容）交给那个 AI，让它按下面顺序读。
> **一句话**：知识库是「内容」，引擎是「裁判」，产出是「成果」。

---

## 一、三层结构（先知道东西在哪）

| 层 | 路径 | 作用 | 体量 |
|---|---|---|---|
| **引擎** | `C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\` | **裁定层** —— 数字唯一出处 · 结论唯一裁定处 | 1.3 MB |
| **知识库** | `C:\Users\wardc\Documents\Obsidian Vault\` | **承载层** —— 人物档案 / 事件库 / 方法论 | 12 MB |
| **产出** | `C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\` | HTML 报告 / CSV / 脚本 | — |

---

## 二、读取顺序（照这个来，别乱读）

### 第一梯队 · 每次必读（约 25 KB）
1. `Obsidian Vault\01_个人信息\⭐个人使用画像.md` —— 我是谁 / 我要什么 / 该怎么服务我
2. `引擎\references\00-真相源·数字基准.md`（14.9 KB）—— **所有数字的出处**
3. `引擎\references\05-纠偏层.md`（198.5 KB）—— **引用任何结论前必读**（唯一裁定记录处）

### 第二梯队 · 按需
4. `引擎\references\01-人格核心.md`（27.5 KB）—— 我执 / 三态 / 距离定律
5. `引擎\references\04-人际地图.md`（21.9 KB）—— 谁离我多近
6. `引擎\references\07-事件档案.md`（49.6 KB）—— 2,864 事件 / 9 条因果链
7. `引擎\references\09-无人时档案.md`（7.3 KB）—— 朋友圈 / 搜索 / 收藏

### 第三梯队 · 找东西用
8. `Obsidian Vault\03_微信聊天分析\🗺️分析总览·全部文件地图.md` —— **找不到文件就查这里**
9. `Obsidian Vault\🏠主页.md` —— 知识库总入口
10. `Obsidian Vault\03_微信聊天分析\🎯成果总索引.md` —— 全部成果索引

---

## 三、五条硬规则（违反就是错的）

1. **数字只能从 `00-真相源·数字基准.md` 引用** —— 禁止从旧 HTML / 旧对话复制数字（会过期）
2. **结论必须先查 `05-纠偏层.md`** —— 那里有裁定、有红线、有「不得读成什么」
3. **距离档（零/近/中/远）只能从人工锚点出** —— 不可从消息量自动推断
4. **聊天内容不得送出本机** —— 数据主权硬约束
5. **报告含真人姓名与金额，不得外传**

---

## 四、可直接粘贴的提示词

### 给 Claude Code / Cursor / Cline（能读本地文件）
```
请先按顺序读这三个文件，读完再回答我：
1. C:\Users\wardc\Documents\Obsidian Vault\01_个人信息\⭐个人使用画像.md
2. C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\00-真相源·数字基准.md
3. C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references\05-纠偏层.md

规则：所有数字只能从第 2 个文件引用；所有结论先查第 3 个文件；
聊天内容不得上传到任何服务器；引用结论时标明来源文件。
```

### 给 ChatGPT / Claude 网页版（不能读本地文件）
⚠️ **绝对不要上传聊天原文**。只上传：
- `⭐个人使用画像.md`（不含聊天内容）
- 需要引用的**具体报告**（如某份 HTML 的正文）

---

## 五、各 harness 怎么接

| harness | 接法 |
|---|---|
| **Claude Code** | `cd "C:\Users\wardc\Documents\Obsidian Vault"` 后直接对话；引擎路径手动给 |
| **Cursor / Windsurf** | 把 Vault 作为项目目录打开 |
| **Cline / Roo Code** | 工作目录设为 Vault；引擎路径手动给 |
| **Codex CLI / Aider** | `cd` 到 Vault；用 `--read` 加载引擎文件 |
| **任何 MCP 客户端** | 用 filesystem MCP 指向上述三个路径 |
| **本地 Ollama** | 直接读文件（断网可用） |

### ★ 想让「引擎」也自动被读到？

默认情况下别的 harness **不会**扫 `~/.workbuddy-ai\`。两条路：

1. **手动给路径**（最简单，见上面提示词）
2. **建目录联接**，把引擎挂进 Vault（一次命令，永久生效）：
```cmd
mklink /J "C:\Users\wardc\Documents\Obsidian Vault\00_引擎镜像" "C:\Users\wardc\.workbuddy-ai\skills\self-understanding-engine\references"
```
> ⚠️ 目录联接在部分工具里可能不跟随。不确定就用第 1 条。

---

## 六、这套体系是什么（给 AI 的背景）

**对象**：蔡浩文（Aaron）—— 央美实验艺术与科技艺术学院 **硕士研究生（2025 级）**；导师陈晔。

**数据**：微信聊天记录全量索引 **388,712 条 / 1,802 会话**（2024-11-10 → 2026-10-04）。

**目标**：让任何 AI 像他本人一样读懂他。

**已有成果**：

| 资产 | 量 |
|---|---|
| 事件库 | **2,864 条**（5 阶段 · 9 条因果链） |
| 距离地图 | **98 人**（三锚点人工标定） |
| 逐日全维主表 | **699 天 × 26 列** |
| 人物档案 | **458 人** |
| HTML 报告 | **41 份**（7 组主题） |
| Obsidian 笔记 | **540+ 篇**（9 分区） |

---

> 本文件本身也是给 AI 读的。**改路径请同步改这里。**
> 上游：`🗺️分析总览·全部文件地图.md` ｜ 生成：2026-10-04
