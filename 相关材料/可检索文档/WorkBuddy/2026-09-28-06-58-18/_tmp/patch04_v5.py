# -*- coding: utf-8 -*-
import io
P = r'C:/Users/wardc/.workbuddy-ai/skills/self-understanding-engine/references/04-人际地图.md'
S = r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\_tmp\sec04_class10.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
assert '第十类关系' not in s, 'already present'
sec = io.open(S, 'r', encoding='utf-8', newline='').read().replace('\r\n', '\n')
nl = '\r\n' if '\r\n' in s else '\n'
b0 = len(s.encode('utf-8'))
s2 = s.rstrip(nl) + nl + nl + sec.replace('\n', nl)
io.open(P, 'w', encoding='utf-8', newline='').write(s2)
print('04 OK: %d -> %d B  lines %d' % (b0, len(s2.encode('utf-8')), s2.count(nl)+1))
