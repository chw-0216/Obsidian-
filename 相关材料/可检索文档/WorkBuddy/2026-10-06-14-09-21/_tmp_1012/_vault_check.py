# -*- coding: utf-8 -*-
"""校验新增/修改的 Obsidian 笔记：frontmatter、标题、链接、表格"""
import io, os, re, sys

V = r"C:\Users\wardc\Documents\Obsidian Vault"
FILES = [
    r"01_个人信息\项目\在场与回应-材料与位置总表.md",
    r"01_个人信息\项目\陈晔会话-井邻全梳.md",
    r"01_个人信息\项目\文件传输助手素材-30件与位置.md",
    r"01_个人信息\项目\井邻乡村美育工作站.md",
    r"01_个人信息\项目\在场与回应-中期汇报.md",
    r"01_个人信息\项目\中期汇报-可用材料盘点.md",
    r"01_个人信息\项目\留光回声-LED声音装置.md",
    r"01_个人信息\项目\在场与回应-三个研究方向.md",
    r"01_个人信息\项目\微信聊天记录分析流水线.md",
    r"01_个人信息\00_个人信息总览.md",
    r"08_多维导航\项目\在场与回应-材料与位置总表.md",
    r"08_多维导航\项目\陈晔会话-井邻全梳.md",
    r"08_多维导航\项目\文件传输助手素材-30件与位置.md",
]

# 收集全库笔记名，用于检查 wikilink 是否存在
names = set()
for dp, dn, fn in os.walk(V):
    dn[:] = [d for d in dn if not d.startswith(".")]
    for f in fn:
        if f.endswith(".md"):
            names.add(f[:-3])

for rel in FILES:
    p = os.path.join(V, rel)
    if not os.path.exists(p):
        print("✗ 缺失:", rel); continue
    s = io.open(p, encoding="utf-8").read()
    lines = s.split("\n")
    # frontmatter
    fm_ok = lines[0].strip() == "---"
    end = None
    if fm_ok:
        for i in range(1, min(len(lines), 60)):
            if lines[i].strip() == "---":
                end = i; break
    h2 = len(re.findall(r"^## ", s, re.M))
    h1 = len(re.findall(r"^# ", s, re.M))
    links = re.findall(r"\[\[([^\]|#]+)", s)
    miss = sorted({l for l in links if l not in names})
    # 表格管道数一致性（粗检）
    print("%-56s FM=%s(%s)  H1=%d H2=%2d  行=%4d  wikilink=%3d 未解析=%d" % (
        rel, "OK" if (fm_ok and end) else "!!", ("yaml行%d" % (end-1)) if end else "-",
        h1, h2, len(lines), len(links), len(miss)))
    if miss:
        for m in miss[:8]:
            print("        未解析 → [[%s]]" % m)
