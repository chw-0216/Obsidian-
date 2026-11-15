# -*- coding: utf-8 -*-
import io
P = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
b0 = len(s.encode('utf-8'))
nl = '\r\n' if '\r\n' in s else '\n'

R = []
# 压缩（为并入腾空间）
R.append((
 '## 十一、会话名对照（2026-10-11 · 全表见 `tools\\session_map.md`）',
 '## 十一、会话名对照（2026-10-11）'))
R.append((
 '| 38 | **井邻·洞台村＝读研真正主线**（515 条/99 会话/18 月）· 导师划界·母亲兜底·他淡化 |',
 '| 38 | **井邻·洞台村＝读研真正主线**（515 条/99 会话/18 月）· 导师划界·母亲兜底 |'))
# 并入 75 的新定论
R.append((
 '· 给 **笑一** 讲澜沧（★ **她汇报＝10-15**）',
 '· 给 **笑一** 讲澜沧（★ **她汇报＝10-15**·已定＝**帮她准备组会**·**先给结构**）'))
R.append((
 '（**A13·B3·E8·I10**）★ **唯一入口**',
 '（**A13·B3·E8·I9·I10**）★ **唯一入口**'))

for i, (o, n) in enumerate(R, 1):
    c = s.count(o)
    if c != 1:
        raise SystemExit('ABORT R%d: count=%d\n%s' % (i, c, o[:90]))
    s = s.replace(o, n, 1)

b1 = len(s.encode('utf-8'))
print('MEMORY: %d -> %d B  (delta %+d)  budget 16143  margin %d' % (b0, b1, b1-b0, 16143-b1))
if b1 > 16143:
    raise SystemExit('TOO BIG')
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('WROTE OK')
