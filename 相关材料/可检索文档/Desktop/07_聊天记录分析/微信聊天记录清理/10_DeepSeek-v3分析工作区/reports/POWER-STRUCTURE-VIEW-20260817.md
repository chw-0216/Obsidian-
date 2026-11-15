# 全量权力结构视图 · 微信聊天深度分析

> 生成：2026-08-17 · 模型：deepseek-v4-flash · 提示词版本：deep-v1（含权力结构专项分析）
> 范围：11 个 keep 事件 · 38 位联系人 · 结果表 `_v3_event_deep_analysis`
> 消耗：输入 150,174 / 输出 24,222 ≈ 17.4 万 token

## 一、权力结构分层总览

### A. 女性上位（用户下位）——「异性 + 权力结构」核心

| 联系人 | 事件数 | 权力判定 | 不对称维度 | 用户行为模式 |
|---|---|---|---|---|
| Sīrius R（周冉学姐） | 3 | unequal / them 主导 | decision·information·status | 反复道歉、绝对服从、求认可 |
| 李明嘉（明嘉姐） | 1 | slightly unequal / them | information·resource·status | 亦师亦友，配合 |
| 陈文君、yl.w（学姐称谓） | 各1 | equal / me 主导 | information | 用户提供报名信息（角色反转） |
| 李紫懿（女同学） | 1 | equal / mutual | resource | 互惠：信息换选票信息 |

### B. 男性上位（用户下位）

| 联系人 | 事件数 | 权力判定 | 不对称维度 | 关系性质 |
|---|---|---|---|---|
| 舒泽林（舒哥） | 2 | unequal / them | decision·emotional·information·status | 兄弟情+尊重，情感依附 |
| Darwin（学长） | 2 | 1 unequal + 1 equal / them | decision·information·status | 审批方 |
| 罗文迪（迪哥） | 1 | unequal / them | resource | |
| Maxwell、Flùr na h-Alba（学长） | 各1 | equal / them | information·status / resource | 学长 |
| 蒲公英（哥） | 1 | equal / them | information | 朋友 |

### C. 师生权力（性别未确认，模型如实标 unknown）

| 联系人 | 事件数 | 权力判定 | 不对称维度 |
|---|---|---|---|
| 方列丰（方老师） | 3 | unequal / them | decision·information·resource·status |
| 陈老师（显示名"导！急速回…"） | 3 | unequal / them | decision·emotional·information·resource·status |
| ZHAO（赵老师） | 1 | unequal / them | decision·information·resource·status |
| 高世强（客座教授）、冯梦波（学院领导）、章燕紫、祁震、Jia Yunbo、管壮壮、野三无、momo | 各1 | unequal / them | 教学/行政主导 |

### D. 招聘方权力

| 联系人 | 权力判定 | 说明 |
|---|---|---|
| 菜（HR/内推）、Tintin、💕（HR）、AUCA小助手 | unequal / them | decision·resource 主导 |

### E. 平级 / 互惠

| 联系人 | 权力判定 | 说明 |
|---|---|---|
| 王若彤（t哥） | equal / them+mutual | 合作搭档，互称二爷/哥 |
| 琢、会、🍬🍬、智晓律 | equal | 同级协作 |

### F. 用户主导（罕见，值得注意）

| 联系人 | 权力判定 | 说明 |
|---|---|---|
| 树_（亲密朋友，蔡哥为照顾者） | unequal / me | 用户是照顾方——权力反转 |
| 报名咨询者（冰橙子、yaifKei、Lee🇨🇳 等） | equal / me | 用户作为组织者提供信息 |

## 二、跨事件模式洞察（推断，待你确认）

1. **默认位置是"服务者/执行者"**：在几乎全部权威关系（学姐学长/老师/导师/招聘方）中，用户处于下位（unequal/them），主导方是对面。11 个事件里用户主导的关系仅 2 类（照顾朋友、报名组织）。
2. **对女性上位的特殊性**：对周冉学姐（Sīrius R）的行为带有明显**认可诉求**——反复道歉、致歉、"显示绝对服从与配合"；而对老师的服从更像任务驱动。这是"异性+权力结构"里最值得深挖的一条。
3. **用户的社交资本是"信息提供"**：在平级关系中（报名咨询者），用户几乎都是 me 主导 + information 不对称——用"提供活动信息/资源"换取关系位置。
4. **情感不对称仅出现在两条关系**：陈老师（师生+情感）与舒哥（兄弟+情感）。其余权威关系无 emotional 维度，是纯任务/地位驱动。
5. **用户主导的例外**：照顾生病朋友（树_）时权力反转（unequal/me），说明用户在"被需要/付出照顾"的角色里才会占据主导。

## 三、诚实边界（重要）

- 全部结论为**模型推断**（fact_status=inferred），置信度 0.6–0.8；不是事实判定。
- 性别线索**仅基于称谓证据**（学姐/学长/姐/哥/女性名），无证据的一律 unknown，未臆测。
- 反证已记录并保留（如中秋事件：用户自称"打工的/不是负责人"，与"追求地位"推断矛盾）。
- 各事件的「需用户确认项」（是否负责人、是否上下级等）已存于 `_v3_event_deep_analysis.result_json`。
- 稳定模式判定规则：跨事件模式需 ≥3 个独立事件支撑；本视图仅 Sīrius R（3 事件）、方老师（3 事件）、陈老师（3 事件）达到，其余均视为**单事件观察**。

## 四、数据回链

- 深度结果：`_v3_event_deep_analysis`（11 行，含 token/模型/prompt 版本/证据覆盖率）
- 事件包：`runs/deep_alumni/`（校友会 3）、`runs/deep_keep_rest/`（其余 8）
- 分析模块：`src/v3_deep_analyzer.py`（prompt deep-v1，power_dynamic 字段）
- 未覆盖：2 个 pending 事件（和舒哥聚会、打折机票/托运咨询）无最终判断，未纳入。
