# -*- coding: utf-8 -*-
"""清理目标现状核对（只读）。
输出：每个目标的 是否存在 / 大小，以及 C 盘剩余空间。
"""
import os, sys, ctypes

H = r'C:\Users\wardc'

TARGETS = [
    # ---- 第一档 ----
    ('L1', r'AppData\Local\Temp'),
    ('L1', r'AppData\Local\Microsoft\WinGet'),
    ('L1', r'AppData\Local\Microsoft\Teams'),
    ('L1', r'AppData\Local\Microsoft\Edge'),
    ('L1', r'AppData\Local\pip'),
    ('L1', r'AppData\Local\0install.net'),
    ('L1', r'AppData\Local\@deepseek-aidsh-desktop-updater'),
    ('L1', r'AppData\Local\weflow-updater'),
    ('L1', r'AppData\Local\weflow-updater.bak'),
    ('L1', r'AppData\Local\WeFlow_anchor_backups'),
    ('L1', r'AppData\Roaming\weflow\cache'),
    ('L1', r'AppData\Roaming\Tencent\Logs'),
    ('L1', r'AppData\Roaming\LarkShell\update'),
    ('L1', r'Desktop\Antigravity IDE.exe'),
    ('L1', r'Desktop\Antigravity-x64.exe'),
    ('L1', r'Desktop\DiscordSetup.exe'),
    ('L1', r'Desktop\GoogleDriveSetup.exe'),
    # ---- 第二档 ----
    ('L2', r'AppData\Local\Google\Chrome\User Data\OptGuideOnDeviceModel'),
    ('L2', r'AppData\Local\Google\Chrome\User Data\Default\Cache'),
    ('L2', r'AppData\Local\Google\Chrome\User Data\Default\Code Cache'),
    ('L2', r'AppData\Local\Google\Chrome\User Data\Default\GPUCache'),
    ('L2', r'AppData\Local\Google\Chrome\User Data\Default\Service Worker'),
    ('L2', r'AppData\Local\Doubao'),          # 豆包
    ('L2', r'AppData\Local\Baidu'),           # 百度网盘
    ('L2', r'AppData\Local\baidu'),
    ('L2', r'AppData\Local\Temp\baidu'),
    # ---- 大件（只看，不动）----
    ('BIG', r'xwechat_files'),
    ('BIG', r'Documents\WeChat Files'),
    ('BIG', r'Desktop\07_聊天记录分析'),
    ('BIG', r'Documents\Obsidian Vault'),
]


def dir_size(path, deadline=None):
    import time
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


def free_space(drive='C:\\'):
    try:
        free, total, _ = ctypes.c_ulonglong(0), ctypes.c_ulonglong(0), ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(drive),
            ctypes.byref(free), ctypes.byref(total), ctypes.byref(free))
        return free.value, total.value
    except Exception as e:
        return None, None


if __name__ == '__main__':
    f, t = free_space()
    if f:
        print(f"C盘: 总 {human(t)} / 剩 {human(f)} / 已用 {human(t-f)} ({100*(t-f)/t:.0f}%)\n")

    print(f"{'档':<4}{'状态':<8}{'大小':>10}  路径")
    print('-' * 78)
    for lvl, rel in TARGETS:
        p = os.path.join(H, rel)
        if not os.path.exists(p):
            print(f"{lvl:<4}{'已清':<8}{'--':>10}  {rel}")
            continue
        if os.path.isfile(p):
            sz = os.path.getsize(p)
        else:
            try:
                sz = dir_size(p, deadline=None)
            except Exception:
                sz = -1
        print(f"{lvl:<4}{'存在':<8}{human(sz) if sz>=0 else '?':>10}  {rel}")
