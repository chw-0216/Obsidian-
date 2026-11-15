# -*- coding: utf-8 -*-
"""shrink_memory_1010a.py —— 把工作区 MEMORY.md 压回注入上限，并加入「自我模型层」。

★ 铁律：读写均 newline="" （否则 Windows 把 \n 翻成 \r\n，每行凭空 +1 字节）
"""
import io
import re
import shutil
import sys
import time
from pathlib import Path

P = Path(r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md")
LIMIT = 16143

s = io.open(P, encoding="utf-8", newline="").read()
before = len(s.encode("utf-8"))
print("压缩前：%d 字节（上限 %d，超 %d）" % (before, LIMIT, before - LIMIT))

OPS = []

# ── OP1 §八 同步链路 bullet：细节已在 SKILL.md，此处只留判据
OPS.append((
    r"\*\*同步链路\*\*：.*?两刷单群进 `NOISE_SESSIONS`。",
    "**同步链路**：`chattrace.cli data decrypt` → `index-incremental.py` → `gen_live_json.py`"
    "（手动跑比 `.cmd` 快）。★ `chattrace` **只在系统 Python 3.12**（受管 3.13 报 `No module named`）。"
    "★ `time_text` 为空 → 时间一律用 **`ts`**。★ **第①层必须跑两次**（否则整天增量全丢）。"
    "★ **第②层三根因**（见 `05` 三·补·57）：水位过滤丢迟到消息 → `--reconcile` ·"
    " `ins_fts` 孤儿 → 逐行 `rowcount` · 占位符永久化 → `upgrade_placeholder_content.py`。"
    "★ **`messages` ↔ `messages_fts` 必须 1:1**；刷单群进 `NOISE_SESSIONS`。"))

# ── OP2 §五 55–58 行压缩
OPS.append((
    r"(\| 55–58 \|)[^\r\n]*",
    r"\1 **10-09 数据链路修复 + 补料②③**：① 水位过滤静默丢迟到消息 → `--reconcile`；"
    "刷单群 4,121 已清 ② 占位符永久化 + FTS 孤儿 33 已清 → 对账报 0；"
    "恢复笑一 10-07 原话 ③ ¥630＝**她索要的补偿** · 中关村 **8.5h** ④ 笑一自述心率「抽着疼」"
    " ⑤ **旭峰＝母友·曾在人事处**（非现职）· **林茂＝院长·旧识/利益同盟** |"))

# ── OP3 §五 59 行压缩
OPS.append((
    r"(\| 59 \|)[^\r\n]*",
    r"\1 ★★ **中期汇报＝「研二综合测评汇报」· 10-13（周二）13:00**（10-09 研究生群）："
    "**6 分钟 + 2 分钟问答** · 分两组（资料室/讲堂，分组待「工部」发）· 本人已回「收到」 |"))

# ── OP4 §七 微信同步行：数字更新 + 压缩
OPS.append((
    r"- ✅ \*\*微信同步（10-09 22:07）\*\*：[^\r\n]*",
    "- ✅ **微信同步（10-10 09:07）**：**392,297 条** · 会话 **1,806** · 零发言 46.0%；"
    "三层 41 秒 + 对账 19 秒。★ 刷单群 4,121 已清 · **FTS 孤儿 33 已清** → "
    "**`messages` 与 `messages_fts` 现 1:1**。"))

# ── OP5 §九 中期汇报行（与 §五 59 重复）→ 删
OPS.append((
    r"- ✅ \*\*中期汇报 → 10-13（周二）13:00\*\*（见 59）· 分组待「工部」发。\r?\n",
    ""))

# ── OP6 §十一 去掉 live 条数（会过期）
OPS.append((
    r"- `deerluna`=陈晔（7,282）· `wxid_wdnk6ue9kiyn22`=\*\*笑一\*\*（6,650）· "
    r"`wxid_0gb0smyjaoyk22`=\*\*陈昶文\*\*（6,382）· ",
    "- `deerluna`=陈晔 · `wxid_wdnk6ue9kiyn22`=**笑一** · `wxid_0gb0smyjaoyk22`=**陈昶文** · "))

OPS.append((
    r"· `wxid_1wa75s1kze3o22`=\*\*刘丽萍\*\*（母 · 16,538）· ",
    "· `wxid_1wa75s1kze3o22`=**刘丽萍**（母）· "))

# ── OP7 §三 文件位置表：加「自我模型层」行
OPS.append((
    r"(\| 产出 \| 工作区（本目录）[^\r\n]*\r?\n)",
    r"\1| **自我模型层**（10-10 新增） | `analysis.sqlite` 5 新表（`self_claims`/`claim_evidence`/`choice_episodes`/`understanding_views`/`learning_questions`）+ `tools\\selfmodel.py` + `Vault\\06_自我模型\\`（4 视图） |\r\n"))

# ── OP8 §七 系统状态：加自我模型层一行 + 更新 05 行数
OPS.append((
    r"- ✅ 引擎行数：`05` \*\*5,139 行\*\* · `04` \*\*458 行\*\* · `00-真相源` 17 项。",
    "- ✅ **自我模型层（10-10）**：`self_claims` **25** · `choice_episodes` **12**（**理由待本人补**）·"
    " `learning_questions` **12** · `claim_evidence` 7。★ **「证明有用」已从总解释降级为有条件假设**"
    "（`SC-MECH-002`）。见 `05` 三·补·61。\r\n"
    "- ✅ 引擎行数：`05` **5,367 行** · `04` **458 行** · `00-真相源` 17 项。"))

# ── OP9 §七 标题日期更新
OPS.append((
    r"## 七、系统状态（截至 10-09 22:07）",
    r"## 七、系统状态（截至 10-10 12:00）"))

for i, (pat, rep) in enumerate(OPS, 1):
    n = len(re.findall(pat, s, flags=re.S))
    if n != 1:
        print("!! OP%d 命中 %d 次（期望 1），中止" % (i, n))
        sys.exit(1)
    # ★ 必须用 re.sub —— str.replace 不解析 \1 反向引用（会把字面量写进文件）
    s = re.sub(pat, rep, s, count=1, flags=re.S)

after = len(s.encode("utf-8"))
print("压缩后：%d 字节（%+d）" % (after, after - before))
secs = sum(1 for l in s.replace("\r\n", "\n").splitlines() if l.startswith("## "))
print("节数：%d" % secs)
if after > LIMIT:
    print("!! 仍超上限，中止")
    sys.exit(1)
if secs != 13:
    print("!! 节数不是 13，中止")
    sys.exit(1)

bk = Path(r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp") / (
    "memory_backup_" + time.strftime("%Y%m%d_%H%M%S"))
bk.mkdir(parents=True, exist_ok=True)
shutil.copy2(P, bk / "MEMORY.md")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("备份：%s" % bk)
print("✅ 已写回 · 余量 %d 字节" % (LIMIT - after))
