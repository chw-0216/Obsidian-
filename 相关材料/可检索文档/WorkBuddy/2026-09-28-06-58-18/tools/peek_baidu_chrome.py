# -*- coding: utf-8 -*-
import os
H = r'C:\Users\wardc'


def sz(x):
    t = 0
    st = [x]
    while st:
        d = st.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            st.append(e.path)
                        else:
                            t += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return t


def sub(*parts, top=20):
    p = os.path.join(H, *parts)
    print('###', os.sep.join(parts))
    if not os.path.exists(p):
        print('  (不存在)')
        return
    rows = []
    for e in os.scandir(p):
        try:
            rows.append((sz(e.path) if e.is_dir(follow_symlinks=False) else e.stat().st_size,
                         e.name + ('/' if e.is_dir(follow_symlinks=False) else '')))
        except OSError:
            pass
    for s, n in sorted(rows, reverse=True)[:top]:
        print('  %10.1fMB  %s' % (s / 1048576, n))


sub('AppData', 'Roaming', 'baidu', 'BaiduNetdisk')
for prof in ['Profile 1', 'Profile 10', 'Profile 12', 'Default']:
    sub('AppData', 'Local', 'Google', 'Chrome', 'User Data', prof, top=10)
