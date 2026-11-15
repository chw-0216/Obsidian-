# -*- coding: utf-8 -*-
"""把文件/目录送进 Windows 回收站（可还原）—— 不用 rm / del 直删。

原理：调用 shell32.SHFileOperationW + FOF_ALLOWUNDO。
用法：
    python recycle.py --dry-run <path> [<path> ...]
    python recycle.py --list <manifest.txt>        # 每行一个路径（UTF-8）
    python recycle.py --list <manifest.txt> --execute
"""
import ctypes
import os
import sys
from ctypes import wintypes

FO_DELETE = 3
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040
FOF_NOERRORUI = 0x0400
FOF_NOCONFIRMMKDIR = 0x0200


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ('hwnd', wintypes.HWND),
        ('wFunc', wintypes.UINT),
        ('pFrom', wintypes.LPCWSTR),
        ('pTo', wintypes.LPCWSTR),
        ('fFlags', ctypes.c_uint16),
        ('fAnyOperationsAborted', wintypes.BOOL),
        ('hNameMappings', ctypes.c_void_p),
        ('lpszProgressTitle', wintypes.LPCWSTR),
    ]


def recycle(paths):
    """paths: list[str]。返回 (rc, aborted)。rc==0 表示成功。"""
    # pFrom 需要双 \0 结尾
    buf = '\0'.join(os.path.abspath(p) for p in paths) + '\0\0'
    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = buf
    op.pTo = None
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI | FOF_NOCONFIRMMKDIR
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return rc, bool(op.fAnyOperationsAborted)


def human(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def dir_size(path):
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def main():
    args = sys.argv[1:]
    execute = '--execute' in args
    args = [a for a in args if a != '--execute']

    if '--list' in args:
        i = args.index('--list')
        mf = args[i + 1]
        with open(mf, encoding='utf-8') as fh:
            targets = [l.strip() for l in fh if l.strip() and not l.startswith('#')]
    else:
        targets = [a for a in args if not a.startswith('--')]

    if not targets:
        print("没有目标。"); return

    print(f"{'执行' if execute else '预演(dry-run)'} · 共 {len(targets)} 项\n")
    total = 0
    ok = 0
    for t in targets:
        if not os.path.exists(t):
            print(f"  [跳过·不存在] {t}")
            continue
        sz = dir_size(t)
        total += sz
        if not execute:
            print(f"  {human(sz):>9}  {t}")
            ok += 1
            continue
        rc, aborted = recycle([t])
        # ⚠️ SHFileOperationW 的返回码不可靠（实测成功时也会返回 rc=2）。
        # 以「路径是否消失」为唯一判定标准；rc 仅作参考输出。
        gone = not os.path.exists(t)
        status = 'OK' if gone else f'失败(仍在,rc={rc})'
        if status == 'OK':
            ok += 1
        print(f"  {human(sz):>9}  [{status}]  {t}")

    print(f"\n小计: {human(total)} · 成功 {ok}/{len(targets)}")


if __name__ == '__main__':
    main()
