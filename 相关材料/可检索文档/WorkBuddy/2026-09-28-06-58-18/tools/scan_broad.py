# -*- coding: utf-8 -*-
"""C 盘重点目录大项扫描（只读）。"""
import os, sys, time

def dir_size(path, deadline=None):
    total = 0
    stack = [path]
    while stack:
        if deadline and time.time() > deadline:
            raise TimeoutError
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        else:
                            total += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total

def human(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def scan(root, top=20, exclude=()):
    print(f"\n{'='*70}\n### {root}")
    if not os.path.exists(root):
        print("  (不存在)"); return
    try:
        ents = list(os.scandir(root))
    except OSError as ex:
        print("  ", ex); return
    rows = []
    for e in ents:
        if e.name in exclude:
            continue
        try:
            if e.is_dir(follow_symlinks=False):
                rows.append((dir_size(e.path), e.name + os.sep))
            else:
                rows.append((e.stat(follow_symlinks=False).st_size, e.name))
        except OSError:
            pass
    tot = sum(r[0] for r in rows)
    for sz, name in sorted(rows, reverse=True)[:top]:
        print(f"  {human(sz):>10}  {name}")
    print(f"  {'-'*10}\n  {human(tot):>10}  合计(不含排除项)")

if __name__ == '__main__':
    H = r'C:\Users\wardc'
    scan(r'C:\Users\wardc\AppData\Local', 30)
    scan(r'C:\Users\wardc\AppData\Roaming', 20)
    scan(r'C:\ProgramData', 15)
    scan(r'C:\Windows\Temp', 10)
    scan(r'C:\Windows\SoftwareDistribution\Download', 5)
    scan(r'C:\Users\wardc\Downloads', 15)
    scan(r'C:\Users\wardc\Documents', 15)
    scan(r'C:\Users\wardc\Desktop', 15)
    scan(r'C:\Users\wardc\Videos', 10)
    scan(r'C:\Users\wardc\Pictures', 10)
    scan(r'C:\Users\wardc', 25)
