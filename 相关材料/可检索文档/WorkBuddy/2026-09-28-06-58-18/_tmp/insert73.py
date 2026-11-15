# -*- coding: utf-8 -*-
import io
P = r'C:/Users/wardc/.workbuddy-ai/skills/self-understanding-engine/references/05-纠偏层.md'
S = r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\sec73.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
sec = io.open(S, 'r', encoding='utf-8', newline='').read().replace('\r\n', '\n')
assert '三·补·73' not in s, 'already present'
anchor = '## 四、使用方式'
assert s.count(anchor) == 1, s.count(anchor)
nl = '\r\n' if '\r\n' in s else '\n'
b0 = len(s.encode('utf-8'))
new = s.replace(anchor, sec.replace('\n', nl) + anchor, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(new)
print('05 OK: %d -> %d B  lines %d' % (b0, len(new.encode('utf-8')), new.count(nl)+1))
