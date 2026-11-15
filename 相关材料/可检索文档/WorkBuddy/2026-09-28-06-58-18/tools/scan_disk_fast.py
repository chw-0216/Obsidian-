# -*- coding: utf-8 -*-
"""快速磁盘占用扫描 —— os.scandir 递归，比 du 快得多。
用法: python scan_disk_fast.py <root> [--depth N] [--top K]
"""
import os, sys, heapq, time

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
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
    return total

def human(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wardc"
    top = 30
    if '--top' in sys.argv:
        top = int(sys.argv[sys.argv.index('--top') + 1])
    budget = 900  # 单目录最多 15 分钟

    print(f"扫描: {root}\n")
    results = []
    try:
        entries = [e for e in os.scandir(root)]
    except OSError as ex:
        print("无法读取:", ex); return

    for e in entries:
        if not e.is_dir(follow_symlinks=False):
            continue
        try:
            sz = dir_size(e.path, time.time() + budget)
        except TimeoutError:
            sz = -1
        results.append((sz, e.name))
        print(f"  {human(sz) if sz >= 0 else '超时':>10}  {e.name}", flush=True)

    print("\n=== Top ===")
    for sz, name in sorted(results, reverse=True)[:top]:
        print(f"{human(sz) if sz >= 0 else '超时':>10}  {name}")

if __name__ == '__main__':
    main()
