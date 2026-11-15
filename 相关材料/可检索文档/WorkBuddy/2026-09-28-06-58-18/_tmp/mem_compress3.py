# -*- coding: utf-8 -*-
import io, sys
P = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
orig = s
def L(*lines): return '\r\n'.join(lines)

reps = []

# 1) 裁定 53–58 去重（笑一/陈昶文/中关村/身份风控 已在 §十一·§十三 各有一处）
reps.append((
 L('| 53–58 | **10-09 同步+补料①②③**：陈晔 10-08 22:06 提问未答 · 笑一 10-08 已兑现 · 陈昶文复活 · 「没领导查课就进去」＝身份风控第2次；¥630＝**她索要的补偿**（买粉底）· 中关村 **8.5h** · 前男友＝**曹庆辉** · **院里书记代管**；**旭峰＝母友·曾在人事处** · **林茂＝院长·旧识** · 井邻×3D＝《在场与回应》 |'),
 L('| 53–58 | **10-09 同步+补料①②③**：陈晔 10-08 22:06 提问未答；¥630＝**她索要的补偿**（买粉底）· 前男友＝**曹庆辉** · **院里书记代管**；**旭峰＝母友·曾在人事处** · **林茂＝院长·旧识** · 井邻×3D＝《在场与回应》（笑一·陈昶文见 §十一） |'),
))

# 2) 系统状态首行：C1/C2/C3 细节已在 05
reps.append((
 L('- ✅ `analysis.sqlite`：事件 2,864 / 证据 5,463 / **结论 68** · 年度重建 8 线×13 月 · 178 候选 · C1/C2 证伪 · C3-a 成立/C3-b 否。'),
 L('- ✅ `analysis.sqlite`：事件 2,864 / 证据 5,463 / **结论 68** · 年度重建 8 线×13 月 · 178 候选。'),
))

# 3) 自我模型层：去表名反引号 + 数字同步 12 / 26
reps.append((
 L('- ✅ **自我模型层（10-11·四轮）**：**8 表**（`self_claims` 29 · `claim_evidence` 16 · `choice_episodes` 13 · `learning_questions` 13 · `recommendations` 11 · `rec_deps` 22 · **`predictions` 1**）· 视图 **6** · `verify` **4/4** · 手填区 **7/7** + 预测校准 **11/11**。见 `05` 三·补·61–63。'),
 L('- ✅ **自我模型层（10-11·四轮）**：**8 表**（claims 29 · claim_evidence 16 · choice_episodes 13 · learning_questions 13 · recommendations **12** · rec_deps **26** · predictions 1）· 视图 **6** · `verify` **4/4** · 手填区 **7/7** + 预测校准 **11/11**。见 `05` 三·补·61–63。'),
))

# 4) 决策中枢状态行去重（与 §五 行 65 重叠）
reps.append((
 L('- ✅ **决策中枢（10-11）**：9 表 · 10 模块 · 6 视图 · `decision_hub verify` **10/10** · 建议 11→**12** / 依赖 22→**26**。见 `05` 三·补·65。'),
 L('- ✅ **决策中枢（10-11）**：`decision_hub verify` **10/10** · 6 视图 · 建议 11→**12** / 依赖 22→**26**。见 `05` 三·补·65。'),
))

# 5) 微信库坑：占位符一条细节在 SKILL.md
reps.append((
 L('- **微信库**（`wechat-data-forensics` §4.19/4.21）：中文相似度须 IDF 加权；索引时间窗仅 2 年（2024-11-10 起，早于此**不得读成没关系**）；`role` 只有 `me/them/system`；转账双倍记账；**视频定位＝按字节匹配 XML `length`**。★ **群名解析**：`sessions.display_name` 空（＝talker）时查解密库 `contact.db` 按 `username=\'xxx@chatroom\'` 取 **`nick_name`**。★ 新加群会话多为 `system` 行、content ＝ session_key 占位（正常）。'),
 L('- **微信库**（`wechat-data-forensics` §4.19/4.21）：中文相似度须 IDF 加权；索引时间窗仅 2 年（2024-11-10 起，早于此**不得读成没关系**）；`role` 只有 `me/them/system`；转账双倍记账；**视频定位＝按字节匹配 XML `length`**。★ **群名解析**：`sessions.display_name` 空（＝talker）时查解密库 `contact.db` 按 `username=\'xxx@chatroom\'` 取 **`nick_name`**。'),
))

# 6) 同步链路：三根因清单在 05
reps.append((
 L('- **同步链路**：`chattrace.cli data decrypt`（★ **只系统 Python 3.12**）→ `index-incremental.py` → `gen_live_json.py`。★ **第①层必须跑两次**；★ 第②层三根因见 `05` 三·补·57（`--reconcile` · 逐行 `rowcount` · `upgrade_placeholder_content.py`）。★ **`messages` ↔ `messages_fts` 必须 1:1**；`ins_fts` **必须显式写 rowid**（AUTOINCREMENT 跳号而 FTS 不跳 → 必错位 · `fix_fts_offset.py`）。★ `time_text` 空 → 用 **`ts`**；刷单群进 `NOISE_SESSIONS`。'),
 L('- **同步链路**：`chattrace.cli data decrypt`（★ **只系统 Python 3.12**）→ `index-incremental.py` → `gen_live_json.py`。★ **第①层必须跑两次**；★ **第②层三根因**见 `05` 三·补·57。★ **`messages` ↔ `messages_fts` 必须 1:1**；`ins_fts` **必须显式写 rowid**（AUTOINCREMENT 跳号而 FTS 不跳 → 必错位 · `fix_fts_offset.py`）。★ `time_text` 空 → 用 **`ts`**；刷单群进 `NOISE_SESSIONS`。'),
))

# 7) 待办末两行合并
reps.append((
 L('- ⬜ 依恋类型待裁定 · 知识库 PII 57 处待脱敏。',
   '- ⬜ 年度重建下一批：178 候选→事件 · 补 2025-11 缺口 · C3-a 待拍板 · 全量经历重建（图片 OCR / 视频 ASR / link 补录）。'),
 L('- ⬜ 依恋类型待裁定 · PII 57 处待脱敏 · 年度重建下一批：178 候选→事件 · 补 2025-11 缺口 · C3-a 待拍板 · 全量经历重建（OCR / ASR / link 补录）。'),
))

# 8) §十三 发现行去粗体
reps.append((
 L('> **★ 发现**：**Obsidian 侧早已打通**，**引擎侧四层全空** → **以 Obsidian 为准并入**。'),
 L('> **★ 发现**：Obsidian 侧早已打通，引擎侧四层全空 → **以 Obsidian 为准并入**。'),
))


# 9) 抬头去冗
reps.append((
 L('> 只记「跨会话必须遵守」的约定与铁律。**细节分流**：裁定→引擎 `05`；流水→`YYYY-MM-DD.md`；技术坑→各 SKILL.md。'),
 L('> 只记跨会话铁律。**细节分流**：裁定→引擎 `05`；流水→`YYYY-MM-DD.md`；技术坑→各 SKILL.md。'),
))
# 10) 数据源尾项
reps.append((
 L('消息 **393,107**（★ 已排除 2 刷单群；源库 954,855 行**未去重**）✅ · `contact.db` 人 42,708 / 群 714 🟡 · `general.db` FMessage/transfer/redEnvelope ✅ · `sns.db` 🟡 · `favorite.db` 230 ⬜ · `media_0.db` 语音 2,486 ⬜ · 表情/媒体/头像 ⬜'),
 L('消息 **393,107**（★ 已排除 2 刷单群；源库 954,855 行**未去重**）✅ · `contact.db` 人 42,708 / 群 714 🟡 · `general.db` FMessage/transfer/redEnvelope ✅ · `sns.db` 🟡 · `favorite.db` 230 ⬜ · `media_0.db` 语音 2,486 ⬜'),
))
# 11) 死数据判别去尾注
reps.append((
 L('- ★ **死数据判别**：字段能填≠有用 —— 问「它改变了哪次输出？说不出＝死数据」。'),
 L('- ★ **死数据判别**：字段能填≠有用 —— 问「它改变了哪次输出？」'),
))
# 12) 裁定 52 与 §十三 去重
reps.append((
 L('| 52 | ★★ **中传交互技术课旁听线并入引擎**：母亲→王利敏(1146)→李老师；起点 **2026-05-15**；**修正 Q7**（非「爱面子」，是「身份风控」）→ §十三 |'),
 L('| 52 | ★★ **中传交互技术课旁听线并入引擎**（起点 2026-05-15 · 修正 Q7＝「身份风控」）→ §十三 |'),
))

for i, (a, b) in enumerate(reps, 1):
    n = s.count(a)
    if n != 1:
        print('ABORT P%d: count=%d' % (i, n))
        print(repr(a[:120]))
        sys.exit(1)
    d = len(b.encode('utf-8')) - len(a.encode('utf-8'))
    s = s.replace(a, b, 1)
    print('ok P%d: %+d B' % (i, d))

b0, b1 = len(orig.encode('utf-8')), len(s.encode('utf-8'))
print('---')
print('bytes: %d -> %d  (delta %+d)' % (b0, b1, b1 - b0))
print('limit 16143 | over =', b1 - 16143)
assert s.count('\r\n') == s.count('\n'), 'CRLF 不一致'
import re
secs = re.findall(r'^## (.+)$', s, re.M)
print('sections =', len(secs))
if b1 <= 16143:
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('WROTE OK')
else:
    print('NOT WRITTEN (still over)')
