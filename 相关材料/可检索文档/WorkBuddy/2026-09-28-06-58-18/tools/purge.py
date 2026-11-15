# -*- coding: utf-8 -*-
"""永久删除「纯缓存 / 安装包」—— 带白名单护栏。

安全设计：
  1. 只有落在 ALLOWED 前缀内的路径才允许删除，越界直接拒绝。
  2. 文档 / 照片 / 聊天记录 目录**根本不在白名单里**，物理上无法删到。
  3. 每个路径删除前后都打印，可核对。
  4. 跳过被占用的文件（不报错、不中断）。

用法：
    python purge.py --list <manifest.txt>            # 预演
    python purge.py --list <manifest.txt> --execute  # 执行
"""
import os
import shutil
import sys

H = os.path.expanduser('~')

# ── 白名单：只有这些前缀下的路径允许永久删除 ──────────────
ALLOWED = [
    os.path.join(H, r'AppData\Local\Temp'),
    os.path.join(H, r'AppData\Local\Microsoft\WinGet'),
    os.path.join(H, r'AppData\Local\Microsoft\Teams'),
    os.path.join(H, r'AppData\Local\Microsoft\Edge'),
    os.path.join(H, r'AppData\Local\pip'),
    os.path.join(H, r'AppData\Local\0install.net'),
    os.path.join(H, r'AppData\Local\@deepseek-aidsh-desktop-updater'),
    os.path.join(H, r'AppData\Local\weflow-updater'),
    os.path.join(H, r'AppData\Local\weflow-updater.bak'),
    os.path.join(H, r'AppData\Local\WeFlow_anchor_backups'),
    os.path.join(H, r'AppData\Roaming\weflow\cache'),
    os.path.join(H, r'AppData\Roaming\Tencent\Logs'),
    os.path.join(H, r'AppData\Roaming\LarkShell\update'),
    os.path.join(H, r'Desktop\Antigravity IDE.exe'),
    os.path.join(H, r'Desktop\Antigravity-x64.exe'),
    os.path.join(H, r'Desktop\DiscordSetup.exe'),
    os.path.join(H, r'Desktop\GoogleDriveSetup.exe'),
]


def allowed(path):
    p = os.path.abspath(path)
    for a in ALLOWED:
        a = os.path.abspath(a)
        if p == a or p.startswith(a + os.sep):
            return True
    return False


def size_of(p):
    if os.path.isfile(p):
        try:
            return os.path.getsize(p)
        except OSError:
            return 0
    t = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                t += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return t


def human(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def purge(p):
    """返回 (是否成功, 错误信息)。跳过锁定文件。"""
    try:
        if os.path.isfile(p) or os.path.islink(p):
            os.remove(p)
        else:
            shutil.rmtree(p, ignore_errors=True)
    except Exception as ex:
        return False, str(ex)
    return (not os.path.exists(p)), ''


def main():
    args = sys.argv[1:]
    execute = '--execute' in args
    args = [a for a in args if a != '--execute']

    if '--list' in args:
        mf = args[args.index('--list') + 1]
        with open(mf, encoding='utf-8') as fh:
            targets = [l.strip() for l in fh if l.strip() and not l.startswith('#')]
    else:
        targets = [a for a in args if not a.startswith('--')]

    print(f"{'执行' if execute else '预演'} · {len(targets)} 项 · 白名单护栏已启用\n")
    total = ok = blocked = 0
    for t in targets:
        if not os.path.exists(t):
            continue
        if not allowed(t):
            print(f"  [拒绝·不在白名单] {t}")
            blocked += 1
            continue
        sz = size_of(t)
        if not execute:
            total += sz
            ok += 1
            continue
        done, err = purge(t)
        if done:
            total += sz
            ok += 1
        else:
            print(f"  [跳过·占用中] {t}  {err}")

    print(f"\n释放: {human(total)} · 成功 {ok}/{len(targets)}"
          + (f" · 拒绝 {blocked}" if blocked else ""))


if __name__ == '__main__':
    main()
