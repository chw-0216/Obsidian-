# -*- coding: utf-8 -*-
"""MEMORY.md 第 6 次维护：并入「校友会工作线」+ 腾出空间。
★ 铁律：带 \1 反向引用一律用 re.sub（str.replace 不解析反向引用）。
★ 读写均 newline="" 防止 CRLF 虚增字节。
"""
import io, os, re, sys, shutil, datetime

ROOT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
MEM = os.path.join(ROOT, ".workbuddy-ai", "memory", "MEMORY.md")
LIMIT = 16143

s = io.open(MEM, encoding="utf-8", newline="").read()
before = len(s.encode("utf-8"))
print("压缩前字节：", before, " 上限：", LIMIT)

# 备份
bak = os.path.join(ROOT, "_tmp", "memory_backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(bak, exist_ok=True)
shutil.copy2(MEM, os.path.join(bak, "MEMORY.md"))
print("备份 ->", bak)

OPS = []

# ---- 腾空间 ----
# 1) 55–58 行瘦身（细节在 05 三·补·55–58）
OPS.append((
    r"(\| 55–58 \|)[^\r\n]*",
    r"\1 **10-09 数据链路修复 + 补料②③**（细节见 `05` 三·补·55–58）：水位过滤丢迟到消息 → `--reconcile`；占位符永久化 + FTS 孤儿 33 → 对账报 0；¥630＝**她索要的补偿** · 中关村 **8.5h**；**旭峰＝母友·曾在人事处** · **林茂＝院长·旧识/利益同盟**",
))

# 2) 十·《绝对者》未拿到 —— 已完成项里的悬空尾注，删
OPS.append((r"⬜《绝对者》未拿到。", r""))

# 3) 十二·当兵年龄那句去掉「（假设性）」尾注（闸门节已声明"每轮至少找 1 个假设性约束"）
OPS.append((r"· \*\*当兵年龄政策核实过吗\*\*（假设性）", r"· **当兵年龄政策核实过吗**"))

# 3b) §四 数据源行瘦身 + 同步为 392,297
OPS.append((
    r"消息 \*\*392,198\*\*（★ 已排除 2 刷单群 北京家教 527,295 \+ 泰语群 88,493，10-09 清 4,121；源库 954,855 行\*\*未去重\*\*）✅",
    r"消息 **392,297**（★ 已排除 2 刷单群；源库 954,855 行**未去重**）✅",
))

# 3c) §五 54 行瘦身
OPS.append((
    r"(\| 54 \|)[^\r\n]*",
    r"\1 **补料①（10-09）**（见 `05` 三·补·54）：¥630＝给笑一买粉底·中关村过夜 · **院里书记代管** · 笑一前男友＝**曹庆辉** · 机会线＝**林茂**+武脉仪/叶敏（可能性）· 井邻×3D＝《在场与回应》",
))

# 3d) §五 59 行去掉出处括注
OPS.append((r"· 10-13（周二）13:00\*\*（10-09 研究生群）：", r"· 10-13（周二）13:00**："))

# 3e) §七 台账行去掉根因细节
OPS.append((
    r"（原 `delete…like 'hyp:%'` 抹增量）。",
    r"。",
))

# 3f) §九 索引维护 / 中传线 / 舒泽林 三行瘦身
OPS.append((r"\*\*每周跑一次\*\* `index-incremental\.py --reconcile`（19 秒，捞迟到消息）。",
            r"**每周一次** `index-incremental.py --reconcile`。"))
OPS.append((r"\*\*每周三前\*\*入校预约（被访人王利敏 1146）", r"**每周三前**入校预约（王利敏 1146）"))
OPS.append((r"极狐三笔返款卡 12 天\+。", r"极狐三笔返款卡 13 天+。"))

# 3g) §十 阶段 A 去掉包名
OPS.append((r"装 QMD 中文版（`G0-0000/qmd-chinese`，BGE-M3）", r"装 QMD 中文版（BGE-M3）"))

# 3h) §十二 CSH 全称缩写
OPS.append((r"（CSH 边界批判 · POET/OMNI", r"（CSH · POET/OMNI"))

# 3i) §九 工作台人工字段那句删
OPS.append((r"⬜ 工作台人工字段全空（仅本人能填）· ", r"⬜ "))

# ---- 追加腾空间（第二组）----
# 3j) §五 48/50/51/52 行去掉出处括注与尾注
OPS.append((r"\| 48 \| 决策中枢四线（10-07）：", r"| 48 | 决策中枢四线："))
OPS.append((r"\*\*陈晔—临汾已闭环\*\*（10-08）：", r"**陈晔—临汾已闭环**："))
OPS.append((r"→ 22 天零往来；引擎原记录止于 05-26 \|", r"→ 22 天零往来 |"))
OPS.append((r"\*\*中传交互技术课旁听线并入引擎\*\*（10-08）：", r"**中传交互技术课旁听线并入引擎**："))
# 3k) §七 台账行压空格
OPS.append((r"（open 22 / conf 6 / sup 2）", r"（open 22/conf 6/sup 2）"))
# 3l) §九 年度重建 / 全量经历 两行瘦身
OPS.append((r"9 个零候选日人工过 · 178 候选升级为事件", r"178 候选升级为事件"))
OPS.append((r"3 条待核实（《未来之阈》/创客市集/集美）。", r"3 条待核实。"))
# 3m) §九 待本人答行去掉流程尾注
OPS.append((r"；答一条同时写 05 → 00 → Obsidian。", r"。"))
# 3n) §十 去掉子命令计数
OPS.append((r"· 子命令 9 个 · ★ 四态分开", r"· ★ 四态分开"))

# ---- 新增 ----
# 4) §五 加一行 60：校友会工作线
OPS.append((
    r"(\| 59 \|[^\r\n]*\r?\n)",
    r"\1| 60 | ★★ **校友会工作线并入**（10-10）：**周冉＝会长**（`zhouran68` 1,242 条·文案终审）＋ **Darwin＝活动负责人**（1,157 条·**18 家跨校友会资源**）；9 群 4,884 条；发布主推 **10:00–11:30** → Obsidian `01_个人信息\\项目\\格拉斯哥北京校友会-文案与传播.md` |\r\n",
))

# 5) §六 加第 16 条红线
# ★★ 必须用 \g<1> —— `\1` 后紧跟数字（这里是 16）会被 Python 当八进制转义（\116 → 'N'）
OPS.append((
    r"(15\. ★ 沐茜妍线[^\r\n]*\r?\n)",
    r"\g<1>" + r"16. ★ **校友会线**：不得把 Darwin 定性为「职场PUA」（那是情绪层描述；行为层＝**三次爆发·零次被替换**）→ 定性待本人拍板；**不得写入周冉发的身份证号/手机号/邮箱密码**。\r\n",
))

# 6) §十一 会话名对照补 周冉 + 日期改 10-10
OPS.append((
    r"## 十一、会话名对照（2026-10-09）",
    r"## 十一、会话名对照（2026-10-10）",
))
OPS.append((
    r"(`wxid_id1nfp5f20e122`=\*\*沐茜妍\*\*。)",
    r"\1 `zhouran68`=**周冉**（校友会**会长** · 上级）· `Darwin480015`=**Darwin/曹总**（校友会**活动负责人** · 上级）。",
))

# 执行（逐条校验唯一命中）
for i, (pat, rep) in enumerate(OPS, 1):
    n = len(re.findall(pat, s, flags=re.S))
    if n != 1:
        print("!! OP%d 命中 %d 次（应为 1）" % (i, n)); sys.exit(1)
    s = re.sub(pat, rep, s, count=1, flags=re.S)

after = len(s.encode("utf-8"))
print("压缩后字节：", after, " 余量：", LIMIT - after)
if after > LIMIT:
    print("!! 仍超限，未写盘"); sys.exit(1)

io.open(MEM, "w", encoding="utf-8", newline="").write(s)
print("已写盘")
print("节数：", len(re.findall(r"^## ", s, flags=re.M)))
print("异常表格行（含字面 \\1 或 \\r\\n）：", len(re.findall(r"\\r\\n|\\1", s)))
