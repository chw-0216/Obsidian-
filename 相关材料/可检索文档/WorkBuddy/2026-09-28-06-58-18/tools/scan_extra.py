# -*- coding: utf-8 -*-
"""第二批候选：额外可清理的纯缓存（只读扫描）。"""
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


def sub(*parts, top=14):
    p = os.path.join(H, *parts)
    if not os.path.exists(p):
        return
    print(f"\n### {os.sep.join(parts)}   [{human(dir_size(p))}]")
    rows = []
    for e in os.scandir(p):
        try:
            rows.append((dir_size(e.path) if e.is_dir(follow_symlinks=False) else e.stat().st_size,
                         e.name + ('/' if e.is_dir(follow_symlinks=False) else '')))
        except OSError:
            pass
    for s, n in sorted(rows, reverse=True)[:top]:
        print(f"  {human(s):>10}  {n}")


if __name__ == '__main__':
    sub('AppData', 'Roaming', 'Adobe')
    sub('AppData', 'Local', 'JianyingPro')
    sub('AppData', 'Roaming', 'Tencent')
    sub('AppData', 'Local', 'Feishu')
    sub('AppData', 'Roaming', 'adspower_global')
    sub('AppData', 'Roaming', 'Zoom')
    sub('AppData', 'Local', 'Discord')
    sub('AppData', 'Roaming', '360browser')
    sub('.cache')
    sub('Documents', '.accelerate')
    sub('AppData', 'Local', 'NVIDIA')
    sub('AppData', 'Local', 'NVIDIA Corporation')
    sub('AppData', 'Local', 'D3DSCache')
    sub('AppData', 'Local', 'CrashDumps')
    sub('Documents', '.tmp.driveupload')
    sub('Desktop', '_im_tmp')
    sub('AppData', 'Local', 'OpenAI')
    sub('AppData', 'Local', 'Tencent')
