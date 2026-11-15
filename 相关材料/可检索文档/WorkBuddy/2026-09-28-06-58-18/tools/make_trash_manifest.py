# -*- coding: utf-8 -*-
"""生成待回收清单（只生成文本，不删除任何东西）。"""
import os
import sys

H = os.path.expanduser('~')
out = []


def add(p, note=''):
    out.append((os.path.join(H, p) if not os.path.isabs(p) else p, note))


# ── 批 1a：Temp 内容（顶层每一项） ───────────────────────
TEMP = os.path.join(H, 'AppData', 'Local', 'Temp')
if os.path.isdir(TEMP):
    for e in os.scandir(TEMP):
        out.append((e.path, 'Temp'))

# ── 批 1b：WeFlow 更新快照 —— 保留最新 1 个 ─────────────
AB = os.path.join(H, 'AppData', 'Local', 'WeFlow_anchor_backups')
if os.path.isdir(AB):
    items = sorted([e.path for e in os.scandir(AB) if e.is_dir()],
                   key=lambda p: os.path.getmtime(p), reverse=True)
    for p in items[1:]:
        out.append((p, 'WeFlow快照'))

# ── 批 1c：其余缓存 / 安装包 ────────────────────────────
for p, note in [
    ('AppData/Local/Microsoft/WinGet', 'WinGet缓存'),
    ('AppData/Local/pip', 'pip缓存'),
    ('AppData/Local/0install.net', '0install缓存'),
    ('AppData/Local/@deepseek-aidsh-desktop-updater', '更新包'),
    ('AppData/Roaming/weflow/cache', 'WeFlow缓存'),
    ('AppData/Roaming/Tencent/Logs', '日志'),
    ('Desktop/Antigravity IDE.exe', '安装包'),
    ('Desktop/Antigravity-x64.exe', '安装包'),
    ('Desktop/DiscordSetup.exe', '安装包'),
    ('Desktop/GoogleDriveSetup.exe', '安装包'),
    ('AppData/Local/weflow-updater/installer.exe', '安装包'),
    ('AppData/Local/weflow-updater.bak/installer.exe', '安装包'),
]:
    add(p, note)

# ── 批 2：应用缓存 ──────────────────────────────────────
for p, note in [
    ('AppData/Local/Microsoft/Teams', 'Teams缓存'),
    ('AppData/Local/Microsoft/Edge', 'Edge缓存'),
    ('AppData/Roaming/LarkShell/update', '飞书更新包'),
]:
    add(p, note)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    sel = out
    if mode == 'b1':
        sel = [x for x in out if x[1] != 'Teams缓存' and x[1] != 'Edge缓存' and x[1] != '飞书更新包']
    elif mode == 'b2':
        sel = [x for x in out if x[1] in ('Teams缓存', 'Edge缓存', '飞书更新包')]

    mf = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_tmp',
                      f'trash_manifest_{mode}.txt')
    os.makedirs(os.path.dirname(mf), exist_ok=True)
    with open(mf, 'w', encoding='utf-8') as f:
        for p, note in sel:
            f.write(p + '\n')
    print(f"清单已写: {os.path.normpath(mf)}  ({len(sel)} 项)")
    for p, note in sel[:8]:
        print(f"  [{note}] {p}")
    if len(sel) > 8:
        print(f"  ... 其余 {len(sel) - 8} 项")
