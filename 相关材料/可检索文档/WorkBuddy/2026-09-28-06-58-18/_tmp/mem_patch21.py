# -*- coding: utf-8 -*-
import io
P = r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
b0 = len(s.encode('utf-8'))

R = [
 ('**微信同步 394,601 条**（10-13）', '**微信同步 394,601**（10-13）'),
 ('· **每周五上午** · **旁听生**。', '· **每周五上午** · 旁听生。'),
 ('（首付 8 万母亲出·车贷/指标均母亲）', '（首付 8 万母亲出·车贷指标均母亲）'),
]

for i, (o, n) in enumerate(R, 1):
    c = s.count(o)
    if c != 1:
        raise SystemExit('ABORT R%d: count=%d' % (i, c))
    s = s.replace(o, n, 1)

b1 = len(s.encode('utf-8'))
print('MEMORY: %d -> %d B  (delta %+d)  margin %d' % (b0, b1, b1-b0, 16143-b1))
if b1 > 16143:
    raise SystemExit('TOO BIG')
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('WROTE OK')
