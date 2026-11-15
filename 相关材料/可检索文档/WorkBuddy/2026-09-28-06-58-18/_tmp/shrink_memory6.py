# -*- coding: utf-8 -*-
"""第六轮压缩 MEMORY.md —— §十 由 5 行压到 2 行。"""
import io

p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
orig = len(s.encode("utf-8"))

a = s.index("## 十、已完成工程资产")
b = s.index("\n## 十一、")
new10 = """## 十、已完成工程资产（索引 · 细节见 `2026-10-0X.md` 与交付 HTML）
- **批处理**：`_tmp\\batch\\batch.sqlite`（materials 64,109 / weeks 81 / experiences 2,207）· 子命令 9 个（`all` 是重活）· ★ 四态分开，重跑前先 delete 本阶段行。**照片证据层**（10-06）：`photos` 68,158 张 → `Desktop` 汇总（285 张 / 11 主题）· ★ 微信剥 EXIF、**群转发图不得直接进 PPT** · 手机取证 `tools/usb_present.py`。**运镜分析**（10-08）：`tools/cinema_shot_analyzer.py`（**判据创新＝视差残差比**）；权威分类学＝CameraBench。⬜《绝对者》未拿到。
- **结缔组织 · 阶段 B 已部署**（10-08）：`build_connective_tissue.py` + `recheck_stale.py`。★ **红线：激进只作用在「提假设」，不作用在「下裁定」**。⚠️ 该脚本原 `delete…like 'hyp:%'` 全删重建（**会抹掉人工增量**）→ 已改为只删种子 id。⬜ **阶段 A 未开始**：装 QMD 中文版（`G0-0000/qmd-chinese`，BGE-M3）→ 索引 Vault + references → 配 MCP → 实测。
"""
s = s[:a] + new10 + s[b:]

io.open(p, "w", encoding="utf-8").write(s)
print("bytes: %d -> %d" % (orig, len(s.encode("utf-8"))))
