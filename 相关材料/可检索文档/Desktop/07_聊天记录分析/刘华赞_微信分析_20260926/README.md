# 刘华赞 微信分析 · 2026-10-01（已切换 ChatTrace 实时口径）

> 对象：**刘华赞（赞赞姐）** —— 从小认识的朋友；母亲**华天雪**是本人母亲**刘丽萍**的老朋友。
> 采集：**ChatTrace 实时索引**（`_im_tmp\wechat-mcp\index.sqlite`）—— 不再依赖 WeFlow、不用回拨系统时钟。
> 历史采集口径：WeFlow 本地 HTTP API（已归档，见 `00_原始导出/`），两条路径核对结果一致。
> 数据截止：2026-10-01（刘华赞本人最新消息仍为 2026-09-25 18:50，无新增）

## 一句话结论

微信里她叫「**赞赞姐**」，wxid `wxid_ltqmzbyc87cp22`，**备注被改成了「*」**（所以用「刘华赞」永远搜不到）。
两人是**节点型世交**：604 天只有 **21 条**消息、**4 个日子**（两次春节 + 生日 + 中秋）、**0 个共同群**，**每次都是我主动**；两家真正的主线在母辈（刘丽萍 ↔ 华天雪，2026-04-20 还同游王府井）。
**朋友圈才是她真正的表达出口**：212 天 19 条动态，互动 100% 来自我和我母亲。

## 目录

| 目录 / 文件 | 内容 |
|-------------|------|
| `00_原始导出/` | **实时口径**：`实时_刘华赞（赞赞姐）_聊天记录.*`、`实时_华天雪_聊天记录.*`；**WeFlow 历史档（已归档）**；联系人卡片；朋友圈原始 JSON（她 19 条 / 全量 259 条） |
| `01_关联证据/` | 母亲（刘丽萍）会话中的全部相关提及（带上下文）+ 全部消息汇总 |
| `02_结构化分析/` | **实时**：`metrics_live.json`、`messages_live.csv`；历史：`metrics.json`、`messages.csv`、18 条证据链、8 条事件时间轴、共同群普查、朋友圈统计 |
| `03_报告/` | ⭐ 主报告 + 朋友圈分析报告 + **ChatTrace 操作手册** + 关系速查卡 |
| `04_朋友圈媒体/` | 朋友圈媒体（19 个子目录；图片因 CDN token 过期仅取到 2 张，视频 2 条已下载） |
| `scripts/` | 实时导出脚本 + WeFlow 导出脚本（可复跑）+ 统计脚本 + 证据构建脚本 |

## 先看哪几个

1. **`03_报告/00_关系速查卡.md`** —— 一页纸，先掌握全部要点
2. **`03_报告/刘华赞_微信人物与关系分析报告.md`** —— 完整分析（含置信度、数据缺口、维护建议）
3. **`03_报告/刘华赞_朋友圈分析报告.md`** —— 朋友圈专题（19 条动态、双人互动闭环、内容主题）
4. **`03_报告/刘华赞_分析操作手册_ChatTrace实时口径.md`** —— 怎么刷新、坑在哪、源一致性核验
5. **`02_结构化分析/evidence_chain.csv`** —— 18 条证据，每条可回溯到原始消息

## 复跑方式（新口径，推荐）

```powershell
# ① 刷新微信数据（三层：解密 → 索引 → JSON），约 33 秒
#    等价于双击 C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\刷新实时数据.cmd
cd C:\Users\wardc\Desktop\_im_tmp\chattrace
python -m chattrace.cli data decrypt --account-dir "C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
cd C:\Users\wardc\Desktop\_im_tmp\wechat-mcp
python index-incremental.py
python gen_live_json.py

# ② 从实时索引导出刘华赞 + 华天雪
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\export_from_live_index.py"

# ③ 统计 + 证据链 + 朋友圈 + 重建本索引
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\moments_stats.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\build_evidence.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\build_docs.py"
```

## 备选：WeFlow 口径（需先启动 WeFlow 并回拨时钟）

```powershell
pwsh -File "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\导出-刘华赞及关联人.ps1"     # 需 WeFlow 运行 + API 已启用(5031)
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\analyze_liuhuazan.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\fetch_moments.py"                # 朋友圈（依赖 WeFlow sns 接口）
```
# 3) 朋友圈：抓取 → 深度解析 → 统计 → 媒体下载
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\fetch_moments.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\moments_deep.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\moments_stats.py"
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\download_moments_media.py"   # 需 WeFlow 媒体代理可用
# 4) 重新生成本索引与速查卡
python "C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926\scripts\build_docs.py"
```

## 文件清单（46 个）

| 文件 | 大小 |
|------|------|
| `00_原始导出\刘华赞（赞赞姐）_聊天记录.json` | 12,355 B |
| `00_原始导出\刘华赞（赞赞姐）_聊天记录.md` | 2,041 B |
| `00_原始导出\刘华赞（赞赞姐）_聊天记录.txt` | 1,775 B |
| `00_原始导出\华天雪_聊天记录.json` | 1,761 B |
| `00_原始导出\华天雪_聊天记录.md` | 662 B |
| `00_原始导出\华天雪_聊天记录.txt` | 543 B |
| `00_原始导出\实时_刘华赞（赞赞姐）_聊天记录.json` | 5,890 B |
| `00_原始导出\实时_刘华赞（赞赞姐）_聊天记录.md` | 2,118 B |
| `00_原始导出\实时_刘华赞（赞赞姐）_聊天记录.txt` | 1,759 B |
| `00_原始导出\实时_华天雪_聊天记录.json` | 1,215 B |
| `00_原始导出\实时_华天雪_聊天记录.md` | 688 B |
| `00_原始导出\实时_华天雪_聊天记录.txt` | 483 B |
| `00_原始导出\朋友圈_全量快照_raw.json` | 1,920,110 B |
| `00_原始导出\朋友圈_刘华赞_raw.json` | 374,639 B |
| `00_原始导出\联系人卡片.json` | 733 B |
| `01_关联证据\原始记录_全部消息汇总.md` | 3,042 B |
| `01_关联证据\母亲会话_相关提及.json` | 11,071 B |
| `01_关联证据\母亲会话_相关提及.md` | 7,198 B |
| `02_结构化分析\event_timeline.csv` | 1,267 B |
| `02_结构化分析\evidence_chain.csv` | 6,385 B |
| `02_结构化分析\messages.csv` | 2,757 B |
| `02_结构化分析\messages_live.csv` | 2,767 B |
| `02_结构化分析\metrics.json` | 2,330 B |
| `02_结构化分析\metrics_live.json` | 2,102 B |
| `02_结构化分析\moments_media_manifest.json` | 13,464 B |
| `02_结构化分析\moments_stats.json` | 8,443 B |
| `02_结构化分析\moments_刘华赞.csv` | 2,444 B |
| `02_结构化分析\共同群普查.json` | 1,064 B |
| `03_报告\00_关系速查卡.md` | 3,754 B |
| `03_报告\刘华赞_分析操作手册_ChatTrace实时口径.md` | 6,378 B |
| `03_报告\刘华赞_微信人物与关系分析报告.md` | 26,809 B |
| `03_报告\刘华赞_朋友圈分析报告.md` | 12,846 B |
| `04_朋友圈媒体\03_20260308_142645_无文字\01.jpg` | 68,813 B |
| `04_朋友圈媒体\04_20260315_193833_COMPLICATED\01.mp4` | 5,683,777 B |
| `04_朋友圈媒体\05_20260315_194012_FLASHLIGHT\01.mp4` | 3,687,334 B |
| `04_朋友圈媒体\18_20260915_143716_无文字\01.jpg` | 17,062 B |
| `README.md` | 9,059 B |
| `scripts\analyze_liuhuazan.py` | 6,228 B |
| `scripts\build_docs.py` | 12,467 B |
| `scripts\build_evidence.py` | 11,838 B |
| `scripts\download_moments_media.py` | 2,631 B |
| `scripts\export_from_live_index.py` | 8,013 B |
| `scripts\fetch_moments.py` | 4,068 B |
| `scripts\moments_deep.py` | 5,855 B |
| `scripts\moments_stats.py` | 4,491 B |
| `scripts\导出-刘华赞及关联人.ps1` | 5,362 B |

## 数据缺口（重要）

本报告是**关系结构与互动模式分析**，不是完整人格侧写——可得语料只有 21 条私聊 + 19 条朋友圈。
若要升级为人物侧写 / 数字分身，需要补：**语音转写**（母亲会话中有她的语音条）、**更早的朋友圈（现只到 2026-02-24）**、**朋友圈图片（CDN token 已过期）**。
详见主报告第七节与朋友圈报告第七节。

## 数据源与已知坑（2026-10-01）

- 已切换到 **ChatTrace 实时索引**：`C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite`
- 本次修掉了索引的历史去重缺陷：**删除 26,248 行重复**（345,111 → 318,863），并重建 FTS
  - 修复脚本：`_im_tmp\wechat-mcp\repair_index_dedupe.py`（支持 `--dry-run`）
  - 备份：`index.sqlite.bak-dedupe-20261001-223534`
- 实时索引坑：`time_text` 167,850 行为空（**用 `ts` 换算时间**）；`sessions.message_count` 偏大（**以 `count(*)` 为准**）
- 详情见 `03_报告/刘华赞_分析操作手册_ChatTrace实时口径.md`

---

*生成：2026-10-01 ｜ 采集：ChatTrace 实时索引（WeFlow 已归档） ｜ DeepSeek Harness 分析*
