# -*- coding: utf-8 -*-
"""工作区中间文件盘点（只读扫描，绝不删除）
输出：CSV 明细 + 分类汇总
"""
import os, io, csv, datetime, sys
from pathlib import Path

WS = Path(r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18")
TMP = WS / "_tmp"
OUT = WS / "_tmp" / ("scan_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
OUT.mkdir(parents=True, exist_ok=True)

def dsize(p):
    if p.is_file():
        try: return p.stat().st_size
        except: return 0
    t = 0
    for r, ds, fs in os.walk(p):
        for f in fs:
            try: t += os.path.getsize(os.path.join(r, f))
            except: pass
    return t

def human(n):
    for u in ["B","K","M","G"]:
        if n < 1024: return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}T"

def mtime(p):
    try: return datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    except: return ""

rows = []

# ---------- 1. _tmp 一级子目录 ----------
print("=== _tmp 子目录 ===")
subdirs = sorted([p for p in TMP.iterdir() if p.is_dir()], key=lambda p: -dsize(p))
for p in subdirs:
    sz = dsize(p)
    n = sum(len(fs) for _,_,fs in os.walk(p))
    rows.append(("_tmp子目录", p.name, sz, n, mtime(p), ""))
    print(f"  {human(sz):>7}  {n:>6} 文件  {p.name}")

# ---------- 2. _tmp 一级文件 ----------
print("\n=== _tmp 一级文件（按扩展名）===")
files = [p for p in TMP.iterdir() if p.is_file()]
byname = {}
for p in files:
    e = (p.suffix or "(无扩展名)").lower()
    byname.setdefault(e, []).append(p)
for e, lst in sorted(byname.items(), key=lambda kv: -sum(dsize(x) for x in kv[1])):
    sz = sum(dsize(x) for x in lst)
    rows.append(("_tmp文件", e, sz, len(lst), "", ""))
    print(f"  {human(sz):>7}  {len(lst):>4} 个  {e}")

# ---------- 3. tools ----------
print("\n=== tools ===")
for p in sorted((WS/"tools").iterdir(), key=lambda p: -dsize(p)):
    sz = dsize(p)
    rows.append(("tools", p.name, sz, 1 if p.is_file() else sum(len(fs) for _,_,fs in os.walk(p)), mtime(p), ""))
print(f"  合计 {human(dsize(WS/'tools'))}")

# ---------- 4. 工作区顶层产出 ----------
print("\n=== 顶层产出文件 ===")
tops = [p for p in WS.iterdir() if p.is_file()]
print(f"  共 {len(tops)} 个，合计 {human(sum(dsize(p) for p in tops))}")
byext = {}
for p in tops:
    e = (p.suffix or "(无)").lower()
    byext.setdefault(e, []).append(p)
for e, lst in sorted(byext.items(), key=lambda kv: -len(kv[1])):
    print(f"    {len(lst):>4} 个  {e}")
    for p in lst:
        rows.append(("顶层产出", p.name, dsize(p), 1, mtime(p), ""))

# ---------- 5. 备份目录单独标 ----------
print("\n=== 备份类（必须保留）===")
for p in subdirs:
    nm = p.name.lower()
    if any(k in nm for k in ["backup","_bak","noise_"]):
        print(f"  {human(dsize(p)):>7}  {p.name}")

with io.open(OUT/"workspace_scan.csv","w",encoding="utf-8-sig",newline="") as f:
    w = csv.writer(f)
    w.writerow(["类别","名称","字节","文件数","修改日","备注"])
    for r in rows: w.writerow(r)

tot_tmp = dsize(TMP)
print(f"\n=== 汇总 ===")
print(f"  工作区总大小 : {human(dsize(WS))}")
print(f"  _tmp 合计    : {human(tot_tmp)}")
print(f"  tools 合计   : {human(dsize(WS/'tools'))}")
print(f"  顶层产出合计 : {human(sum(dsize(p) for p in tops))}")
print(f"\nCSV -> {OUT/'workspace_scan.csv'}")
