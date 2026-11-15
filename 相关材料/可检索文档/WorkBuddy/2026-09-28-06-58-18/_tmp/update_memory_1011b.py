# -*- coding: utf-8 -*-
"""MEMORY.md 第 8 次维护：自我模型层第四轮 + 「死数据」判别法（压回限内）。"""
import io
import sys

P = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md'

OPS = [
    # 压缩：去冗余括注
    ("**朋友圈 tid**：`>>23`（非 >>32）。",
     "**朋友圈 tid**：`>>23`。"),

    ("- ★ **生成器必须幂等**：任何「读旧文件→重写」的 render，必须断言**连续两次字节数一致**（漏围栏行 → 每轮 +4 字节）。",
     "- ★ **生成器必须幂等**：任何「读旧文件→重写」的 render，必须断言**连续两次字节数一致**。\r\n"
     "- ★ **死数据判别**：字段能填≠有用 —— 问「它改变了哪次输出？说不出＝死数据」。"),

    ("回 10-08 22:06 AIGC 问题（框架已产出·待填留白）· **10-11 前交版画工坊 2 分钟横屏视频** · 问落地赛日期/天数/群。",
     "回 10-08 22:06 AIGC 问题（框架已出·待填留白）· **10-11 前交版画工坊 2 分钟横屏视频** · 问落地赛日期/群。"),

    ("- ⬜ 依恋类型待裁定 · 知识库 PII 57 处待脱敏（`tools\\sanitize_vault_pii.py`）。",
     "- ⬜ 依恋类型待裁定 · 知识库 PII 57 处待脱敏。"),
]


def main():
    s = io.open(P, encoding='utf-8', newline='').read()
    old_n = len(s.encode('utf-8'))
    print('原字节:', old_n)
    bad = 0
    for i, (a, b) in enumerate(OPS, 1):
        n = s.count(a)
        if n != 1:
            print('  !! OP%-2d 命中 %d 次 :: %s' % (i, n, a[:52]))
            bad += 1
            continue
        s = s.replace(a, b, 1)
    if bad:
        print('\n有 %d 处异常 → 未写入。' % bad)
        return 1
    new_n = len(s.encode('utf-8'))
    print('新字节:', new_n, '(限 16143)')
    print('节标题数:', s.count('\r\n## '))
    if new_n > 16143:
        print('!! 仍超限 %d 字节，未写入。' % (new_n - 16143))
        return 1
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('★ 已写入，余量 %d 字节' % (16143 - new_n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
