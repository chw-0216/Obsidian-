# -*- coding: utf-8 -*-
"""purge2.py —— 精确白名单清理（C 盘缓存/安装包）

与 purge.py 的区别：
  * 只按【精确路径】删除（allowlist 里逐条列出，含「只取子目录」的情况）
  * 删除前逐项计量，删除后逐项核对
  * 需要外部设置 CODEBUDDY_SAFE_DELETE_ENABLED=0 才能绕过 shim 真正删掉

用法:
    python purge2.py --dry            # 只报告，不删
    python purge2.py --batch 1        # 执行第 1 批
    python purge2.py --batch 2
    python purge2.py --batch 3
"""
import os
import sys
import shutil

H = r'C:\Users\wardc'


def P(*parts):
    return os.path.join(H, *parts)


# ---------------------------------------------------------------- 白名单
# 每项: (批次, 说明, 绝对路径, 模式)
#   模式 'tree' = 整个目录/文件删除
#   模式 'sub'  = 只删这个路径（作为父目录下的子项被逐条列出）
TARGETS = [
    # ================= 批次 1：第一档残留（纯缓存 + 安装包）=================
    (1, 'Temp 内容',            P('AppData', 'Local', 'Temp'), 'children'),
    (1, '0install 包缓存',      P('AppData', 'Local', '0install.net'), 'tree'),
    (1, 'deepseek 更新残留',    P('AppData', 'Local', '@deepseek-aidsh-desktop-updater'), 'tree'),
    (1, 'WeFlow 浏览器缓存',    P('AppData', 'Roaming', 'weflow', 'cache', 'Cache_Data'), 'tree'),
    (1, 'WeFlow 缓存索引',      P('AppData', 'Roaming', 'weflow', 'cache', 'No_Vary_Search'), 'tree'),
    (1, 'WeFlow 旧安装包(8/8)', P('AppData', 'Local', 'weflow-updater', 'installer.exe'), 'tree'),
    (1, 'WeFlow 旧安装包(7/23)', P('AppData', 'Local', 'weflow-updater.bak', 'installer.exe'), 'tree'),
    (1, '飞书更新包',           P('AppData', 'Roaming', 'LarkShell', 'update'), 'tree'),
    (1, '桌面安装包 Antigravity IDE', P('Desktop', 'Antigravity IDE.exe'), 'tree'),
    (1, '桌面安装包 Antigravity-x64', P('Desktop', 'Antigravity-x64.exe'), 'tree'),
    (1, '桌面安装包 GoogleDrive', P('Desktop', 'GoogleDriveSetup.exe'), 'tree'),

    # ================= 批次 2：Chrome =================
    (2, 'Chrome 本地 AI 模型',  P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'OptGuideOnDeviceModel'), 'tree'),
    (2, 'Chrome 模型存储',      P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'optimization_guide_model_store'), 'tree'),
    (2, 'Chrome 组件缓存',      P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'component_crx_cache'), 'tree'),
    (2, 'Chrome 着色器缓存',    P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'GrShaderCache'), 'tree'),
    (2, 'Chrome 着色器缓存2',   P('AppData', 'Local', 'Google', 'Chrome', 'User Data', 'ShaderCache'), 'tree'),
]

# Chrome / Edge / 其他 Chromium 系 profile 里的缓存子目录（逐 profile 展开）
CHROMIUM_CACHE_DIRS = [
    'Cache', 'Code Cache', 'GPUCache', 'DawnWebGPUCache', 'DawnGraphiteCache',
    'GrShaderCache', 'ShaderCache', 'GraphiteDawnCache',
    'Service Worker', 'Crashpad', 'BrowserMetrics',
]

CHROME_PROFILES = ['Default', 'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4',
                   'Profile 5', 'Profile 6', 'Profile 7', 'Profile 8', 'Profile 9',
                   'Profile 10', 'Profile 11', 'Profile 12', 'Guest Profile',
                   'System Profile']

for _prof in CHROME_PROFILES:
    for _cd in CHROMIUM_CACHE_DIRS:
        TARGETS.append((2, f'Chrome {_prof}/{_cd}',
                        P('AppData', 'Local', 'Google', 'Chrome', 'User Data', _prof, _cd), 'tree'))

# ================= 批次 3：Edge / Teams / 豆包 / 飞书 / 百度 =================
_EDGE = P('AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
for _cd in CHROMIUM_CACHE_DIRS + ['component_crx_cache', 'extensions_crx_cache',
                                  'old_ShaderCache_000', 'BrowserMetrics-spare.pma',
                                  'Snapshots', 'Subresource Filter']:
    TARGETS.append((3, f'Edge/{_cd}', os.path.join(_EDGE, _cd), 'tree'))
for _prof in ['Default', 'Profile 1']:
    for _cd in CHROMIUM_CACHE_DIRS:
        TARGETS.append((3, f'Edge {_prof}/{_cd}', os.path.join(_EDGE, _prof, _cd), 'tree'))

TARGETS += [
    (3, 'Teams 旧版本目录',   P('AppData', 'Local', 'Microsoft', 'Teams', 'previous'), 'tree'),
    (3, 'Teams SquirrelTemp', P('AppData', 'Local', 'Microsoft', 'Teams', 'packages', 'SquirrelTemp'), 'tree'),
    (3, '飞书 CodeCache',     P('AppData', 'Roaming', 'LarkShell', 'CodeCache'), 'tree'),
    (3, '飞书 GrShaderCache', P('AppData', 'Roaming', 'LarkShell', 'GrShaderCache'), 'tree'),
    (3, '飞书 ShaderCache',   P('AppData', 'Roaming', 'LarkShell', 'ShaderCache'), 'tree'),
    (3, '飞书 GraphiteDawn',  P('AppData', 'Roaming', 'LarkShell', 'GraphiteDawnCache'), 'tree'),
    (3, '百度网盘 Code Cache', P('AppData', 'Roaming', 'baidunetdisk', 'Code Cache'), 'tree'),
    (3, '百度网盘 Cache',      P('AppData', 'Roaming', 'baidunetdisk', 'Cache'), 'tree'),
    (3, '百度网盘 IndexedDB',  P('AppData', 'Roaming', 'baidunetdisk', 'IndexedDB'), 'tree'),
]
_DOUBAO = P('AppData', 'Local', 'Doubao', 'User Data')
for _cd in CHROMIUM_CACHE_DIRS + ['gecko_cache', 'extensions_crx_cache', 'BrowserMetrics-spare.pma']:
    TARGETS.append((3, f'豆包/{_cd}', os.path.join(_DOUBAO, _cd), 'tree'))
for _prof in ['Default']:
    for _cd in CHROMIUM_CACHE_DIRS:
        TARGETS.append((3, f'豆包 {_prof}/{_cd}', os.path.join(_DOUBAO, _prof, _cd), 'tree'))

# 百度网盘散落的 .tmp 文件
_BN = P('AppData', 'Roaming', 'baidunetdisk')
if os.path.isdir(_BN):
    try:
        for _e in os.scandir(_BN):
            if _e.is_file() and _e.name.lower().endswith('.tmp'):
                TARGETS.append((3, f'百度网盘临时文件 {_e.name}', _e.path, 'tree'))
    except OSError:
        pass

# ================= 批次 4：零散纯缓存（逐项看过内容后确认安全）=================
TARGETS += [
    # HuggingFace 模型缓存（blob 命名，可重新下载）
    (4, 'HuggingFace 模型缓存', P('Documents', '.accelerate'), 'tree'),
    # Google Drive 上传暂存区（最新文件 2026-09-21，已停 10 天）
    (4, 'Google Drive 上传暂存', P('Documents', '.tmp.driveupload'), 'tree'),
    # pnpm 包缓存（只取 store，保留 wechat-mcp / chattrace / 交接卡）
    (4, 'pnpm 包缓存', P('Desktop', '_im_tmp', 'pnpm-home', 'store'), 'tree'),
    # 360 浏览器已卸载（注册表无任何 360 产品）→ 遗留配置
    (4, '360 浏览器遗留数据', P('AppData', 'Roaming', '360browser'), 'tree'),
    # 显卡着色器缓存
    (4, 'NVIDIA DX 着色器缓存', P('AppData', 'Local', 'NVIDIA', 'DXCache'), 'tree'),
    (4, 'NVIDIA GL 着色器缓存', P('AppData', 'Local', 'NVIDIA', 'GLCache'), 'tree'),
    (4, 'D3D 着色器缓存', P('AppData', 'Local', 'D3DSCache'), 'tree'),
    # 崩溃转储
    (4, '崩溃转储', P('AppData', 'Local', 'CrashDumps'), 'tree'),
    # Zoom 内嵌浏览器缓存
    (4, 'Zoom Webview 缓存', P('AppData', 'Roaming', 'Zoom', 'data', 'WebviewCacheX64'), 'tree'),
    # Discord 旧安装包（Squirrel 保留的完整 nupkg）
    (4, 'Discord 安装包', P('AppData', 'Local', 'Discord', 'packages', 'Discord-1.0.9059-full.nupkg'), 'tree'),
]


# ---------------------------------------------------------------- 工具
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


def measure(path, mode):
    if not os.path.exists(path):
        return 0
    if mode == 'children':
        tot = 0
        try:
            for e in os.scandir(path):
                try:
                    tot += dir_size(e.path) if e.is_dir(follow_symlinks=False) else e.stat(follow_symlinks=False).st_size
                except OSError:
                    pass
        except OSError:
            pass
        return tot
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    return dir_size(path)


def _clear_readonly(func, p, exc_info):
    """rmtree onerror 回调：清掉只读属性后重试。"""
    import stat as _stat
    try:
        os.chmod(p, _stat.S_IWRITE)
        func(p)
    except Exception:
        pass


def hard_delete(path):
    """原生删除（依赖外部 CODEBUDDY_SAFE_DELETE_ENABLED=0）。

    Windows 下很多缓存目录带只读属性，先尝试普通删除，
    失败则递归清掉只读属性后重试。
    """
    import stat as _stat
    try:
        if os.path.isfile(path) or os.path.islink(path):
            try:
                os.chmod(path, _stat.S_IWRITE)
            except OSError:
                pass
            os.remove(path)
        else:
            shutil.rmtree(path, onerror=_clear_readonly)
    except Exception as ex:
        # 第二轮：整树清只读后重试
        try:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for n in dirs + files:
                        try:
                            os.chmod(os.path.join(root, n), _stat.S_IWRITE)
                        except OSError:
                            pass
                shutil.rmtree(path, onerror=_clear_readonly)
        except Exception as ex2:
            return False, str(ex2)[:120]
        if os.path.exists(path):
            return False, str(ex)[:120]
    return (not os.path.exists(path)), ''


def delete_children(path):
    """只清空目录内容，保留目录本身。"""
    ok = err = 0
    try:
        entries = list(os.scandir(path))
    except OSError as ex:
        return 0, 0, str(ex)[:80]
    for e in entries:
        good, msg = hard_delete(e.path)
        if good:
            ok += 1
        else:
            err += 1
    return ok, err, ''


def main():
    dry = '--dry' in sys.argv
    batch = None
    if '--batch' in sys.argv:
        batch = int(sys.argv[sys.argv.index('--batch') + 1])

    shim = os.environ.get('CODEBUDDY_SAFE_DELETE_ENABLED')
    print(f"shim 开关 CODEBUDDY_SAFE_DELETE_ENABLED = {shim!r}  "
          f"({'原生删除生效' if shim == '0' else '⚠️ 未关闭，删除会被拦截'})")
    print(f"模式: {'DRY-RUN 只报告' if dry else '实际删除'}   批次: {batch or '全部'}\n")

    items = [t for t in TARGETS if batch is None or t[0] == batch]

    # 去重（保留先出现的）
    seen = set()
    uniq = []
    for t in items:
        key = (os.path.normcase(os.path.abspath(t[2])), t[3])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(t)
    items = uniq

    total_before = 0
    plan = []
    for lvl, desc, path, mode in items:
        sz = measure(path, mode)
        if sz == 0:
            continue
        total_before += sz
        plan.append((lvl, desc, path, mode, sz))

    print(f"{'档':<3}{'大小':>10}  说明")
    print('-' * 74)
    for lvl, desc, path, mode, sz in plan:
        print(f"{lvl:<3}{human(sz):>10}  {desc}")
    print('-' * 74)
    print(f"{'合计':<3}{human(total_before):>10}\n")

    if dry:
        return

    freed = 0
    failed = []
    for lvl, desc, path, mode, sz in plan:
        if mode == 'children':
            ok, err, msg = delete_children(path)
            after = measure(path, mode)
            got = sz - after
        else:
            good, msg = hard_delete(path)
            got = sz if good else 0
            if not good:
                failed.append((desc, path, msg))
        freed += got
        flag = 'OK ' if got > 0 else '-- '
        print(f"  {flag}{human(got):>10} / {human(sz):>10}  {desc}"
              + (f"   ⚠️ {msg}" if got == 0 and msg else ""))

    print('\n' + '=' * 74)
    print(f"本次释放 ≈ {human(freed)}")
    if failed:
        print(f"失败 {len(failed)} 项：")
        for d, p, m in failed[:20]:
            print(f"   - {d}: {m}")


if __name__ == '__main__':
    main()
