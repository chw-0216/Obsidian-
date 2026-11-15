# -*- coding: utf-8 -*-
"""
生成：总索引 README、原始记录汇总、会话关系速查卡
"""
import json, io, os, sys, csv
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT1 = os.path.join(ROOT, "01_关联证据")
OUT2 = os.path.join(ROOT, "02_结构化分析")
OUT3 = os.path.join(ROOT, "03_报告")
CST = timezone(timedelta(hours=8))
TYPE_MAP = {1: "文本", 3: "图片", 34: "语音", 42: "名片", 43: "视频", 47: "表情",
            48: "位置", 49: "链接/卡片/文件", 50: "语音通话", 51: "视频通话", 10000: "系统"}


def fmt(ts):
    return datetime.fromtimestamp(int(ts), CST).strftime("%Y-%m-%d %H:%M:%S")


def basetype(t):
    v = int(t)
    return v % 4294967296 if v > 4294967295 else v


def load(fn):
    with io.open(os.path.join(RAW, fn), encoding="utf-8") as f:
        return json.load(f)


# ---------- 1. 原始记录汇总（全部消息，含关联人） ----------
L = []
L.append("# 刘华赞及相关人 · 微信原始记录汇总\n")
L.append("> 本文件为「一次看全」版：把与刘华赞本人、及其母亲华天雪的全部消息按时间并入一份。\n")
L.append("> 采集：WeFlow 本地 HTTP API `/api/v1/messages`（`hasMore=false`，即全量）\n")
L.append("> 生成时间：2026-09-26\n\n---\n\n")

for fn, label, who_label in [("刘华赞（赞赞姐）_聊天记录.json", "刘华赞（赞赞姐）· 本人会话", "赞赞姐"),
                             ("华天雪_聊天记录.json", "华天雪 · 其母会话", "华天雪")]:
    d = load(fn)
    msgs = sorted(d["messages"], key=lambda m: int(m["createTime"]))
    L.append(f"## {label}\n\n")
    L.append(f"- wxid：`{d['talker']}`　消息数：**{len(msgs)}**　")
    if msgs:
        L.append(f"时间范围：{fmt(msgs[0]['createTime'])} ~ {fmt(msgs[-1]['createTime'])}\n\n")
    L.append("| # | 时间 | 方向 | 类型 | 内容 |\n|---|------|------|------|------|\n")
    for i, m in enumerate(msgs, 1):
        who = "我" if int(m["isSend"]) == 1 else who_label
        c = (m["content"] or "").replace("\n", " ").replace("|", "\\|")[:300]
        L.append(f"| {i} | {fmt(m['createTime'])} | {who} | {TYPE_MAP.get(basetype(m['localType']), '类型' + str(basetype(m['localType'])))} | {c} |\n")
    L.append("\n")

with io.open(os.path.join(OUT1, "原始记录_全部消息汇总.md"), "w", encoding="utf-8") as f:
    f.write("".join(L))

# ---------- 2. 关系速查卡 ----------
CARD = """# 关系速查卡 · 刘华赞（赞赞姐）

| 项目 | 内容 |
|------|------|
| **是谁** | 刘华赞，我称「**赞赞姐**」；从小认识，母亲**华天雪**是我母亲**刘丽萍**的老朋友 |
| **wxid** | `wxid_ltqmzbyc87cp22` |
| **微信备注** | `*`（被人为改成星号 → 用「刘华赞」搜不到，只能按 wxid / Isa-ise 找） |
| **昵称 / 微信号** | 👍 懒瓒 / `Isa-ise` |
| **签名 / 地区** | 明天会更好 / 阿根廷 Buenos Aires（待确认） |
| **她母亲** | 华天雪 `wxid_jycd1ii1qxro22`（alias `HTX-2013`，地区 北京 East） |
| **她怎么叫我** | 「**文文**」；她母亲叫我「**宝宝**」 |
| **我怎么称呼** | 对她：「赞赞姐」；对她母亲：「华天雪阿姨 / 华阿姨」 |
| **生日** | **6 月 5 日**（据 2025-06-05 我发的生日祝福） |
| **消息总量** | 21 条（我 14 / 她 7），604 天，4 个日子，0 次日常闲聊 |
| **数据口径** | **ChatTrace 实时索引**（`_im_tmp/wechat-mcp/index.sqlite`），不再依赖 WeFlow；两条路径核对一致（21 条），截至 2026-10-01 无新增 |
| **朋友圈** | **19 条 / 212 天**（2026-02-24 ~ 2026-09-25）；月均 2.7 条；全部带图，共 93 个媒体 |
| **朋友圈互动** | **我点赞 15 次**（79%）、**母亲点赞 5 次 + 评论 2 次**；她**从不给任何人点赞/评论**（全量 259 条中 0 次） |
| **朋友圈内容** | 古建/伪满建筑专题（6）、城市漫游（6）、艺术展与讣告（3）、节日情绪（3）、视频（4）、美食（1） |
| **发起方** | **永远是我**（4 次节点问候 4 次我开头） |
| **她的回复节奏** | 中位 **3.9 分钟**，模板式回礼（「谢谢文文」+「也祝…」），不延展话题 |
| **共同群** | **0 个**（287 群全量比对） |
| **关系定性** | **节点型世交**：靠节日/生日 + 两家长辈往来维持 |
| **最佳维护动作** | 节日双份问候（她 + 她母亲）；**平时给她朋友圈点赞**（她唯一在意"被看见"的渠道） |
| **数据风险** | 她不产生新消息，21 条一旦被清理即永久丢失 → 换机前先跑导出脚本 |

## 已确认的互动日期

| 日期 | 场合 | 概况 |
|------|------|------|
| 2025-01-29 | 春节 | 我发起，6 条，双方祝福闭环 |
| 2025-06-05 | 她生日 | 我单方 6 条（祝福/约饭/补礼物/有时间），对方无回复记录 |
| 2026-02-17 | 春节 | 我发起，5 条，双方闭环 |
| 2026-09-25 | 中秋 | 我发起，4 条，她回「祝你和丽萍阿姨中秋快乐」★ |
| 2026-04-20 | （家长线） | 母亲与她母亲同游王府井，我请母亲代问好 |
| 2026-08-09 | （口碑） | 母亲：「越找越差，还没赞赞靠谱。」 |
| 2026-02 ~ 09 | （朋友圈） | 她 19 条动态：昆明、长春伪满建筑群、八大山人展、霍克尼/草间弥生讣告、中秋 |

## 待你确认（3 条）

1. 微信地区「阿根廷 Buenos Aires」是否属实（**朋友圈动态全在昆明/长春/北京，与"阿根廷"冲突**）
2. 她的学校/专业（2025-07-18 宿舍话题里她是「本地学生」，但具体院校未明）
3. 母亲口中的「**佳佳**」（会打电话通报央美人事消息）是否就是她？

## 朋友圈补充要点

- 内容风格：**知识型标题 + 极短配文**（最长 27 字），有建筑审美判断（「集宏伟精致阴湿蜿蜒于一体」「多即是多」）
- 两次 `R.I.P.`（霍克尼、草间弥生）都是**艺术界讣告**，母亲都在下面留了 `[合十]`
- 发布高峰：**2026-08-25 一天连发 4 条**长春伪满专题，全在 00:00-03:13
- 四个月度空白：**2026-04 整月 0 条**
"""

with io.open(os.path.join(OUT3, "00_关系速查卡.md"), "w", encoding="utf-8") as f:
    f.write(CARD)

# ---------- 3. README 总索引 ----------
files = []
for base, _, fns in os.walk(ROOT):
    for fn in fns:
        p = os.path.join(base, fn)
        rel = os.path.relpath(p, ROOT)
        files.append((rel, os.path.getsize(p)))

README = f"""# 刘华赞 微信分析 · 2026-10-01（已切换 ChatTrace 实时口径）

> 对象：**刘华赞（赞赞姐）** —— 从小认识的朋友；母亲**华天雪**是本人母亲**刘丽萍**的老朋友。
> 采集：**ChatTrace 实时索引**（`_im_tmp\\wechat-mcp\\index.sqlite`）—— 不再依赖 WeFlow、不用回拨系统时钟。
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
#    等价于双击 C:\\Users\\wardc\\Desktop\\_im_tmp\\wechat-mcp\\刷新实时数据.cmd
cd C:\\Users\\wardc\\Desktop\\_im_tmp\\chattrace
python -m chattrace.cli data decrypt --account-dir "C:\\Users\\wardc\\xwechat_files\\wxid_zn4ozsnn8esr21_db45"
cd C:\\Users\\wardc\\Desktop\\_im_tmp\\wechat-mcp
python index-incremental.py
python gen_live_json.py

# ② 从实时索引导出刘华赞 + 华天雪
python "{ROOT}\\scripts\\export_from_live_index.py"

# ③ 统计 + 证据链 + 朋友圈 + 重建本索引
python "{ROOT}\\scripts\\moments_stats.py"
python "{ROOT}\\scripts\\build_evidence.py"
python "{ROOT}\\scripts\\build_docs.py"
```

## 备选：WeFlow 口径（需先启动 WeFlow 并回拨时钟）

```powershell
pwsh -File "{ROOT}\\scripts\\导出-刘华赞及关联人.ps1"     # 需 WeFlow 运行 + API 已启用(5031)
python "{ROOT}\\scripts\\analyze_liuhuazan.py"
python "{ROOT}\\scripts\\fetch_moments.py"                # 朋友圈（依赖 WeFlow sns 接口）
```
# 3) 朋友圈：抓取 → 深度解析 → 统计 → 媒体下载
python "{ROOT}\\scripts\\fetch_moments.py"
python "{ROOT}\\scripts\\moments_deep.py"
python "{ROOT}\\scripts\\moments_stats.py"
python "{ROOT}\\scripts\\download_moments_media.py"   # 需 WeFlow 媒体代理可用
# 4) 重新生成本索引与速查卡
python "{ROOT}\\scripts\\build_docs.py"
```

## 文件清单（{len(files)} 个）

| 文件 | 大小 |
|------|------|
"""
for rel, size in sorted(files):
    README += f"| `{rel}` | {size:,} B |\n"

README += """
## 数据缺口（重要）

本报告是**关系结构与互动模式分析**，不是完整人格侧写——可得语料只有 21 条私聊 + 19 条朋友圈。
若要升级为人物侧写 / 数字分身，需要补：**语音转写**（母亲会话中有她的语音条）、**更早的朋友圈（现只到 2026-02-24）**、**朋友圈图片（CDN token 已过期）**。
详见主报告第七节与朋友圈报告第七节。

## 数据源与已知坑（2026-10-01）

- 已切换到 **ChatTrace 实时索引**：`C:\\Users\\wardc\\Desktop\\_im_tmp\\wechat-mcp\\index.sqlite`
- 本次修掉了索引的历史去重缺陷：**删除 26,248 行重复**（345,111 → 318,863），并重建 FTS
  - 修复脚本：`_im_tmp\\wechat-mcp\\repair_index_dedupe.py`（支持 `--dry-run`）
  - 备份：`index.sqlite.bak-dedupe-20261001-223534`
- 实时索引坑：`time_text` 167,850 行为空（**用 `ts` 换算时间**）；`sessions.message_count` 偏大（**以 `count(*)` 为准**）
- 详情见 `03_报告/刘华赞_分析操作手册_ChatTrace实时口径.md`

---

*生成：2026-10-01 ｜ 采集：ChatTrace 实时索引（WeFlow 已归档） ｜ DeepSeek Harness 分析*
"""

with io.open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write(README)

print("已生成：")
print("  03_报告/00_关系速查卡.md")
print("  01_关联证据/原始记录_全部消息汇总.md")
print("  README.md  （文件数 %d）" % len(files))
