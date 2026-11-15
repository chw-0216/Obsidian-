# -*- coding: utf-8 -*-
"""第二批候选：逐项打开看内容（只读）。"""
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


def show(*parts, depth=2, top=14):
    p = os.path.join(H, *parts)
    print(f"\n{'='*72}\n### {os.sep.join(parts)}   [{human(dir_size(p)) if os.path.exists(p) else '不存在'}]")
    if not os.path.exists(p):
        return
    base = p.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(p):
        d = root.count(os.sep) - base
        if d >= depth:
            dirs[:] = []
        ind = '  ' * d
        try:
            fsz = sum(os.path.getsize(os.path.join(root, f)) for f in files if os.path.exists(os.path.join(root, f)))
        except OSError:
            fsz = 0
        print(f"{ind}{os.path.basename(root) or root}/  [{len(files)}f {human(fsz)}]")
        if d < depth:
            for f in sorted(files)[:8]:
                try:
                    print(f"{ind}   - {f}  {human(os.path.getsize(os.path.join(root, f)))}")
                except OSError:
                    pass


if __name__ == '__main__':
    show('.cache', 'codex-runtimes')
    show('Documents', '.accelerate', depth=1)
    show('Desktop', '_im_tmp')
    show('Documents', '.tmp.driveupload', depth=1)
    show('AppData', 'Local', 'OpenAI', 'Codex', depth=2)
    show('AppData', 'Roaming', '360browser')
