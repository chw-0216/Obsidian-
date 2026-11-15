# -*- coding: utf-8 -*-
import io
P = r'C:/Users/wardc/WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'
s = io.open(P, 'r', encoding='utf-8', newline='').read()
b0 = len(s.encode('utf-8'))
nl = '\r\n' if '\r\n' in s else '\n'

R = [
 ('- ⬜ **陈晔线**：回 10-13 追问 · **论文待发**', '- ⬜ **陈晔线**：**论文待发**'),
 ('**数字不写死**·**打包在打戳后**。', '**数字不写死**。'),
 ('陈晔备注＝「**导！急速回**」（本人自知）。', '陈晔备注＝「**导！急速回**」。'),
 ('· **下限 2024-11-10** → §十四 |', '· **下限 2024-11-10** |'),
 ('讲澜沧（★ 她汇报＝**10-15** 非今天）→ §十五 |', '讲澜沧（★ 她汇报＝**10-15** 非今天）|'),
 ('`09` 第六节（赞 **473/3,534＝13.4%**）。', '`09` 第六节（赞 473/3,534＝13.4%）。'),
 ('（首付 8 万母亲出·车贷指标均母亲）', '（首付 8 万母亲出·车贷指标母亲）'),
 ('度小满/英国笔。', '度小满/英国。'),
 ('**不得**与「身份先行」混谈 · **不得**反推「北京台实习不存在」。',
  '不得与「身份先行」混谈 · 不得反推「北京台实习不存在」。'),
 ('- ⬜ 依恋类型待裁定 · PII 57 处脱敏',
  '- ⬜ **美术馆实习**：**10-14 报到** · 排班**周一到周四** · 对接**何一沙**（媒体部主任）· ⚠️ PR/AE 待补。' + nl +
  '- ⬜ 依恋类型待裁定 · PII 57 处脱敏'),
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
