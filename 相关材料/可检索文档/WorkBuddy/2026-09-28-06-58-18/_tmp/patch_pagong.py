# -*- coding: utf-8 -*-
import io, sys
P = r'C:\Users\wardc\Documents\Obsidian Vault\01_个人信息\自我理解引擎·打通页.md'
S = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\patch_pagong_68_72.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
sec = io.open(S, 'r', encoding='utf-8', newline='').read().replace('\r\n', '\n')
for n in ('68', '69', '70', '71', '72'):
    assert ('三·补·%s、' % n) not in s, 'already present: ' + n
anchor = '## 四、P0 前史 · 七条线索'
assert s.count(anchor) == 1, 'anchor count=%d' % s.count(anchor)
nl = '\r\n' if '\r\n' in s else '\n'
b0 = len(s.encode('utf-8'))
new = s.replace(anchor, sec.replace('\n', nl) + anchor, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(new)
print('打通页 OK: %d -> %d B  lines %d' % (b0, len(new.encode('utf-8')), new.count(nl) + 1))
