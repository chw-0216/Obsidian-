# -*- coding: utf-8 -*-
"""第八轮压缩 MEMORY.md —— 目标 ≤15,950 字节。"""
import io

p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
orig = len(s.encode("utf-8"))


def swap(o, n):
    global s
    if o in s:
        s = s.replace(o, n, 1)
        return True
    print("MISS:", o[:45].replace("\n", " "))
    return False


# §八：合并 81–84 四行为两行
swap(
    "- **本机闸门** `SAFE_DELETE_BULK_CONFIRM_REQUIRED`（50/轮，**覆盖已存在文件也算删除**）→ 产物写**独立时间戳目录**；删除走 `tools\\recycle.py`。\n"
    "- **`HTML_ARTIFACTS` 必须列全所有对外 HTML**（漏一个＝版本对不上）。**数字不写死**；**打包脚本排在打戳之后**。\n"
    "- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。**朋友圈 tid**：`ts_ms=(tid & 0xFFFF...FFFF) >> 23`（**不是 >>32**）。\n"
    "- **FTS 用 trigram，查询词 ≥3 字**（2 字人名用 `LIKE`）；导师 `display_name` 是备注名。\n",
    "- **本机闸门** `SAFE_DELETE_BULK_CONFIRM_REQUIRED`（50/轮，**覆盖已存在文件也算删除**）→ 产物写**独立时间戳目录**；删除走 `tools\\recycle.py`。**`HTML_ARTIFACTS` 必须列全所有对外 HTML**（漏一个＝版本对不上）· **数字不写死** · **打包脚本排在打戳之后**。\n"
    "- **Windows 控制台中文/emoji 会截断** → 长结果写文件再 Read。**朋友圈 tid**：`>>23`（**不是 >>32**）。**FTS 用 trigram，查询词 ≥3 字**（2 字人名用 `LIKE`）；导师 `display_name` 是备注名。\n",
)

# §九：合并最后三行
swap(
    "- ⬜ 工作台人工字段全空（`verdict`/`load_self`）——只有本人能填 · 依恋类型待裁定 · 知识库 PII 57 处待脱敏（`tools\\sanitize_vault_pii.py` 已就绪）。\n"
    "- ⬜ 年度重建下一批：9 个零候选日人工过 · 178 候选升级为事件 · 补 2025-11 缺口 · 待拍板 C3-a 升级裁定 / C3-b 进已推翻清单。\n"
    "- ⬜ 全量经历重建：图片 OCR / 视频 ASR / link 卡片补录 · 3 条待核实（《未来之阈》/创客市集/厦门集美）。C 盘回收站可清 ~1.5GB。\n",
    "- ⬜ 工作台人工字段全空（`verdict`/`load_self`）——只有本人能填 · 依恋类型待裁定 · 知识库 PII 57 处待脱敏（`tools\\sanitize_vault_pii.py` 已就绪）。\n"
    "- ⬜ 年度重建下一批：9 个零候选日人工过 · 178 候选升级为事件 · 补 2025-11 缺口 · C3-a 待拍板 / C3-b 进已推翻清单。\n"
    "- ⬜ 全量经历重建：图片 OCR / 视频 ASR / link 卡片补录 · 3 条待核实（《未来之阈》/创客市集/厦门集美）。\n",
)

io.open(p, "w", encoding="utf-8").write(s)
print("chars: %d -> %d | bytes -> %d" % (len(orig), len(s), len(s.encode("utf-8"))))
