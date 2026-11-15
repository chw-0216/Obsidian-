# -*- coding: utf-8 -*-
"""清理结果终验：核对第一/二档每一项的最终状态。"""
import os
import shutil

H = r'C:\Users\wardc'


def P(*p):
    return os.path.join(H, *p)


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


def size_of(path):
    if not os.path.exists(path):
        return 0
    return os.path.getsize(path) if os.path.isfile(path) else dir_size(path)


CHECK = [
    # (说明, 路径, 原始大小MB)
    ('Temp 内容', P('AppData', 'Local', 'Temp'), 4900),
    ('Chrome 本地 AI 模型', P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'OptGuideOnDeviceModel'), 4072),
    ('pip 缓存', P('AppData', 'Local', 'pip'), 776),
    ('桌面安装包 ×4', None, 790),
    ('0install 包缓存', P('AppData', 'Local', '0install.net'), 718),
    ('deepseek 更新残留', P('AppData', 'Local', '@deepseek-aidsh-desktop-updater'), 552),
    ('WeFlow 浏览器缓存', P('AppData', 'Roaming', 'weflow', 'cache'), 534),
    ('WeFlow 快照备份', P('AppData', 'Local', 'WeFlow_anchor_backups'), 474),
    ('WeFlow 旧安装包 ×2', None, 405),
    ('腾讯日志', P('AppData', 'Roaming', 'Tencent', 'Logs'), 131),
    ('飞书更新包', P('AppData', 'Roaming', 'LarkShell', 'update'), 105),
    ('Teams 缓存', P('AppData', 'Local', 'Microsoft', 'Teams'), 778),
    ('Edge 缓存', P('AppData', 'Local', 'Microsoft', 'Edge'), 504),
    ('豆包缓存', P('AppData', 'Local', 'Doubao'), 2000),
    ('百度网盘缓存', P('AppData', 'Roaming', 'baidunetdisk'), 276),
]

if __name__ == '__main__':
    u = shutil.disk_usage('C:/')
    print(f"C盘: 总 {human(u.total)} / 已用 {human(u.used)} / 剩余 {human(u.free)}\n")

    desk = P('Desktop')
    exes = ['Antigravity IDE.exe', 'Antigravity-x64.exe', 'DiscordSetup.exe', 'GoogleDriveSetup.exe']
    wf = [P('AppData', 'Local', 'weflow-updater', 'installer.exe'),
          P('AppData', 'Local', 'weflow-updater.bak', 'installer.exe')]

    print(f"{'项目':<22}{'原':>9}{'现':>9}   状态")
    print('-' * 62)
    for desc, path, orig in CHECK:
        if path is None:
            if desc.startswith('桌面'):
                cur = sum(size_of(os.path.join(desk, x)) for x in exes)
            else:
                cur = sum(size_of(x) for x in wf)
        else:
            cur = size_of(path)
        pct = (1 - cur / (orig * 1048576)) * 100 if orig else 0
        state = '✅ 已清' if cur < orig * 1048576 * 0.05 else ('⚠️ 部分' if cur < orig * 1048576 * 0.8 else '⏸ 保留')
        print(f"{desc:<22}{human(orig*1048576):>9}{human(cur):>9}   {state}")
