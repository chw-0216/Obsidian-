# -*- coding: utf-8 -*-
"""项目材料 · 现状清点（只读）"""
import os, io

ROOTS = [
    r"C:\Users\wardc\Desktop\文件传输助手_导出_2026-10-12",
    r"C:\Users\wardc\Desktop\在场与回应_三方向研究交接_2026-10-13",
    r"C:\Users\wardc\Desktop\留光回声_LED声音装置_交接_2026-10-13",
    r"C:\Users\wardc\Desktop\井邻_现场素材_2026-10-11",
    r"C:\Users\wardc\Desktop\导",
    r"C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live",
    r"C:\Users\wardc\Desktop\07_聊天记录分析\_桌面导出",
    r"C:\Users\wardc\Desktop\07_聊天记录分析\tools",
    r"C:\Users\wardc\Desktop\07_聊天记录分析\all_sessions",
    r"C:\Users\wardc\Desktop\_定稿图_1002晚",
    r"C:\Users\wardc\Desktop\_素材预览",
    r"C:\Users\wardc\Documents\New project gpt\AI-archive\outputs\在场与回应_中期汇报",
    r"C:\Users\wardc\Documents\Codex\2026-09-22\ban\midterm_build",
    r"C:\Users\wardc\WorkBuddy AI\2026-09-26-22-54-19\outputs",
    r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21",
]

def size(p):
    s = 0; c = 0
    for dp, dn, fn in os.walk(p):
        dn[:] = [d for d in dn if d not in ("node_modules", "__pycache__", ".git")]
        for f in fn:
            try:
                s += os.path.getsize(os.path.join(dp, f)); c += 1
            except Exception:
                pass
    return c, s

for R in ROOTS:
    print("=" * 96)
    print(R)
    print("=" * 96)
    if not os.path.isdir(R):
        print("   ✗ 不存在")
        print()
        continue
    c, s = size(R)
    print("   合计: %d 文件 / %.1f MB" % (c, s / 1048576))
    try:
        ents = sorted(os.listdir(R))
    except Exception as e:
        print("   读取失败:", e); print(); continue
    for e in ents[:60]:
        fp = os.path.join(R, e)
        if os.path.isdir(fp):
            c2, s2 = size(fp)
            print("   [DIR ] %-56s %6d 文件 %9.1f MB" % (e, c2, s2 / 1048576))
        else:
            try: print("   [FILE] %-56s            %9.2f MB" % (e, os.path.getsize(fp) / 1048576))
            except Exception: print("   [FILE] %-56s            ?" % e)
    if len(ents) > 60:
        print("   ... 还有 %d 项" % (len(ents) - 60))
    print()
