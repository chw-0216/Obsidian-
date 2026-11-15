# -*- coding: utf-8 -*-
"""对高风险目录做「子目录级」精确计量，找出真正可删的缓存子目录。"""
import os

H = r'C:\Users\wardc'


def dir_size(path):
    total = 0
    stack = [path]
    while stack:
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


def breakdown(rel, depth=1):
    p = os.path.join(H, rel)
    print(f"\n### {rel}   [{human(dir_size(p)) if os.path.exists(p) else 'N/A'}]")
    if not os.path.exists(p):
        return
    try:
        entries = sorted(os.scandir(p), key=lambda e: e.name.lower())
    except OSError as ex:
        print('  ', ex); return
    rows = []
    for e in entries:
        try:
            if e.is_dir(follow_symlinks=False):
                rows.append((dir_size(e.path), e.name + os.sep, 'd'))
            else:
                rows.append((e.stat(follow_symlinks=False).st_size, e.name, 'f'))
        except OSError:
            pass
    for sz, name, kind in sorted(rows, reverse=True):
        print(f"   {human(sz):>10}  {name}")


if __name__ == '__main__':
    breakdown(r'AppData\Local\Microsoft\Edge\User Data')
    breakdown(r'AppData\Local\Doubao\User Data')
    breakdown(r'AppData\Local\Doubao\Application')
    breakdown(r'AppData\Local\Microsoft\WinGet\Packages')
    breakdown(r'AppData\Local\Microsoft\WinGet\Links')
    breakdown(r'AppData\Local\WeFlow_anchor_backups\Security_20261001_043106')
    breakdown(r'AppData\Local\Microsoft\Teams')
