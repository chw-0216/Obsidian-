# -*- coding: utf-8 -*-
import os, re
from pathlib import Path

ROOTS = [
    Path(r"C:/Users/wardc/Documents/New project gpt/AI-archive/outputs"),
    Path(r"C:/Users/wardc/Desktop/05_井邻项目_视觉与丝网印刷"),
    Path(r"C:/Users/wardc/Desktop/06_井邻项目_宣传申报与合作"),
    Path(r"C:/Users/wardc/Desktop/中期汇报_2026-09"),
    Path(r"C:/Users/wardc/WorkBuddy AI/2026-10-06-14-09-21"),
]
EXT = {".md",".txt",".html",".htm",".json",".csv",".svg",".js",".py",".yaml",".yml",".doc"}
KW = ["五感","五种感官","感官体验","通感","嗅觉","气味","香味","触觉","听觉","味觉","栗子香","在地性","具身"]

hits = {}
for root in ROOTS:
    if not root.exists(): continue
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ("node_modules",".git","__pycache__")]
        for fn in fns:
            p = Path(dp)/fn
            if p.suffix.lower() not in EXT: continue
            if p.stat().st_size > 3_000_000: continue
            try:
                s = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            found = [k for k in KW if k in s]
            if found:
                hits[str(p)] = found

print(f"命中文件数: {len(hits)}\n")
for p, ks in sorted(hits.items(), key=lambda x: -len(x[1]))[:60]:
    print(f"[{','.join(ks)}]")
    print(f"   {p}")
