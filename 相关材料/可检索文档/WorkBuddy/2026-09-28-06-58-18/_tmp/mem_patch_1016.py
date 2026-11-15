# -*- coding: utf-8 -*-
"""MEMORY.md：更新 3500 事件行 + 新增教材大系（待办 + 项目索引）· 保持 CRLF"""
import io

P = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
b0 = len(s)
print('BEFORE chars', len(s))

R = []

# ① 3500 行：状态已被推翻，改为实证结论
R.append((
    '- ⬜ **3500 事件**：`Vault\\04_工作台\\母亲-3500处置卡_20261014.md` · ⚠️ 母亲**未在微信提**（有窗口）· 三句话＝承认+金额+去向。',
    '- ⬜ **3500 事件**：★ 10-14 16:42 已主动认错（对母口径＝**买内存**）· **钱过了**（母只「应先和我说一声」）· ❌ **信任没过**（「真能骗」「电话不接」＝**地点歧义**）· 用途两说待对齐 → `母亲-3500处置卡_20261014.md`'
))

# ② 待办：新增教材大系
R.append((
    '- ⬜ 依恋类型待裁定',
    '- ⬜ ★★ **教材大系《主观色彩》**：死线 **2026-12-30** · 草稿缺「预计完成时间」· 风险 **¥80,000** → `Vault\\04_工作台\\教材大系延期-主观色彩_盯办卡_20261015.md`\r\n- ⬜ 依恋类型待裁定'
))

# ③ 项目索引：新增教材大系线
R.append((
    '- ★ **美术馆实习线**（10-14 报到 · 吕越展待核 · 陈晔讲座 10-17）',
    '- ★ **美术馆实习线**（10-14 报到 · 吕越展待核 · 陈晔讲座 10-17）\r\n- ★ **教材大系线**（《主观色彩》延期 · 死线 **2026-12-30** · **8 万**风险 · private）'
))

for i, (a, b) in enumerate(R, 1):
    n = s.count(a)
    if n != 1:
        print('ABORT R%d: count=%d' % (i, n)); print(repr(a[:90])); raise SystemExit(1)
    s = s.replace(a, b, 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('AFTER  chars', len(s), '| 预算 8192 | 余', 8192 - len(s))
