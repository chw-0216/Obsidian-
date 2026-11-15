# -*- coding: utf-8 -*-
"""把 MEMORY.md 的「会话名对照 + 四条项目线」拆到 PROJECTS.md，主文件只留铁律 + 指针"""
import io
B = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory'
s = io.open(r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\MEMORY_new.md', 'r', encoding='utf-8', newline='').read()
s = s.replace('\r\n', '\n')
print('src chars', len(s))

a = s.index('## 十、会话名对照')
b = s.index('## 十一、★ 前置闸门')
c = s.index('## 十二、★★★ 中传旁听线')

part1 = s[:a]
part2 = s[b:c].replace('## 十一、★ 前置闸门', '## 十、★ 前置闸门')
pointer = (
    '## 十一、项目细则 → 同目录 `PROJECTS.md`\n'
    '- ★ **会话名对照**（talker↔真名 · **显示名≠真名**：陈晔私聊名是「导！急速回，三思回得体！」）\n'
    '- ★ **中传旁听线**（工号/入校/「动画学院」口径 · 严禁外传）\n'
    '- ★ **本科圈 +「身份先行」**（城院/公三/区经2 · 分圈版本管理 · private）\n'
    '- ★ **婚恋线**（徐嘉良＋朱子涵 · 柯益盈 · 欠舒泽林 ¥300 · 跨关系「回复不及时」）\n'
    '- ★ **美术馆实习线**（10-14 报到 · 吕越展待核 · 陈晔讲座 10-17）\n'
    '- → 细则全在 `PROJECTS.md`（与 MEMORY.md 同目录）；**裁定原文**见引擎 `05-纠偏层.md`。\n'
)

out = part1 + part2 + pointer
out = out.replace('\r\n', '\n').replace('\n', '\r\n')
io.open(B + r'\MEMORY.md', 'w', encoding='utf-8', newline='').write(out)
print('AFTER chars', len(out), '| bytes', len(out.encode('utf-8')), '| budget 8192')
