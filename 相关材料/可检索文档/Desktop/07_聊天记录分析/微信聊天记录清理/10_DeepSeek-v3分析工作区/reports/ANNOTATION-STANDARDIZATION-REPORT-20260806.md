# 标注标准化与可用性分析 · 2026-08-06

> 只读分析，未改动任何数据、未调用 API。范围：`data/scale/wechat-analysis-scale.sqlite3`。
> 覆盖三类标注：历史 `annotations`（1.0）、历史 `aggressive_annotations`（2.0/3.0）、v3 标注 + 人工复核判定。

## 0. 一句话结论

历史标注（227 段）确实不标准——**三套互不兼容的 schema**，且与 v3 校准的 50 段**零重叠**，无法直接交叉验证；v3 标注 schema 100% 合格，但潜伏一个 `importance` 恒 0 的陷阱（提示词从未要求该字段）；你的复核判定总体自洽，有 11 段低分/无分却「保留」值得确认（其中 5 段可从备注看出是人脉/关系价值的刻意判断）。

---

## 1. 历史标注：227 段 / 6303 段（3.6%）

### 1.1 三套互不兼容的 schema

| 表 | 行数 | schema_version | 结构特征 |
|---|---|---|---|
| `annotations` | 87 | `1.0` | 扁平：action_items / key_events / relationship_signals / topics / summary，单一 result_json |
| `aggressive_annotations` | 94 | `2.0-aggressive` | 深度嵌套：entities/events/messages/relationship_signals + real_goal / underlying_need / semantic_deep / identity_signal / memory_significance 等 |
| `aggressive_annotations` | 46 | `3.0-async` | 与 2.0 同表混存但改键：aliases / entity_type / name / role_or_description（替代 identity_signal），新增 time_reference / outcome / people_involved，删除 semantic_deep / uncertainty_flags |

- **`aggressive_annotations` 一张表里混了 2.0 和 3.0 两套结构**——按 schema_version 字段区分，但共用同一列族，任何按列直接聚合的查询都会语义错乱。
- 全部来自 `mimo-v2.5-pro`（旧模型）。

### 1.2 覆盖与回链

- 三段集合互不重叠（87 / 94 / 46 完全不交），并集 227 段。
- 227/227 都能回链到 `segments` 表（主键 `id`）。
- `aggressive_message_annotations`（140 条）列填充度高：仅 `memory_candidate`（116/140）与 `ambiguity_notes`（133/140）有缺失，其余 19 个字段全填充。
- **与 v3 校准的 50 段零重叠** → 历史标注无法作为 v3 结果的交叉验证，只能独立备查。

### 1.3 可用性判断

- **不宜直接并入 v3 表**：schema 与证据口径均不兼容、模型旧。
- **可选利用方式**：写一次性只读映射脚本，把三套历史结构归一化到 `v3_annotations` 兼容结构（`_v3_hist_*` 版本化表，不覆盖任何历史表），供全文检索 / 备查 / 抽样参照。成本低（227 段）、0 API。

---

## 2. v3 标注：82 单元 / 765 消息

- Schema 100% 合格、证据回链 100%（校准报告已确认）。
- 质量指标：置信度均值 0.89（0.70–1.00）；平均每单元 实体 1.7、事件 1.0、关系信号 1.3。
- **潜伏陷阱：`importance` 列曾 82/82 全为 0 → 已修复（2026-08-06）**。
  - 根因：提示词 `base_annotation.v1.1.compact.md` 的输出 schema **从未要求模型输出 `importance`**，executor 用 `obj.get("importance") or 0` 兜底 → 恒 0。
  - 修复（0 API）：executor 新增 `_coerce_importance()`，模型未输出时如实存 **NULL**（不再假 0）；`UnitOutcome.importance` 默认改为 `None`；schema 列去掉 `DEFAULT 0` 并注明「未填充时 NULL」。两库全部 127 行历史假 0 已修正为 NULL（`wechat-analysis-v3.sqlite3` 45 + `wechat-analysis-scale.sqlite3` 82）。新增 2 个回归测试（`_coerce_importance` + recorder 落库 NULL），共 40 测试通过。
  - 未做项：若需真实重要度，须升级提示词（新 `prompt_version`，会使去重失效）并重跑——**消耗 API，需授权**。

---

## 3. 人工复核判定：50 段

### 3.1 分数 × 保留建议 大体自洽

- 0–19 分：13 清理 / 1 保留 / 2 待定 → 低分以清理为主 ✅
- 60–79 分：16 保留 / 3 待定 → 高分以保留为主 ✅
- 无分：6 段（5 保留 / 1 清理）

### 3.2 11 段「低分/无分却保留」——两类

**A. 有备注、可见是人脉/关系价值的刻意保留（5 段，符合"关系价值判断"本意）：**
- `seg_393310b3` 无分 keep · 备注「老师交流」
- `seg_705a1cac` 27 分 keep · 备注「健身教练」
- `seg_3eacc80b` 无分 keep · 备注「情感本恋陪dm妮可可泡」
- `seg_a1e7c09c` 无分 keep · 备注「李镜，研一同学，40岁宝石猎人中介」
- `seg_beb8bde7` 38 分 keep · 备注「之前试过泡过」（潜在可维护关系）

**B. 无备注、无法判断有意与否（6 段，建议确认/补备注）：**
- `seg_0db8e7d4` 21 分 keep · 无备注
- `seg_3ab34257` 无分 keep · 无备注
- `seg_09fc1f2a` 无分 cleanup · 无备注
- `seg_718fc221` 27 分 keep · 无备注
- `seg_6106b389` 19 分 keep · 无备注
- `seg_cc3f87c9` 无分 keep · 无备注

### 3.3 价值标签几乎未使用

44 段已打分，仅 4 段打了标签（工作 1 / 生意 2 / 友情 1）。若标签用于后续按关系类型检索，建议补打；否则可考虑从 UI 移除以简化。

---

## 4. 建议（按成本排序）

1. **补 6 段无备注的 keep/cleanup 说明**（0 API）：重开 review.html → 刷新恢复 → 补备注或改建议 → 导出 → 重跑 finalize。
2. **处理 importance 缺口**：本版先标注「未填充」；若要真实重要度，升级提示词重跑（需授权 + 预算确认）。
3. **历史标注归一化到 `_v3_hist_*`**（0 API，一次性只读脚本）：把 227 段转成可检索的版本化结构，供备查与抽样参照，不并入 v3 主表。
4. **扩大复核**（0 API）：基于库中其他已标注片段（现覆盖 227+82 段，全库 6303 段）生成更大的复核包。

---
*生成：2026-08-06T21:2x+08:00 · 0 API · 只读*
