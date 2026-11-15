# -*- coding: utf-8 -*-
"""把「李老师（海燕）」发过的文件归集到桌面资料夹。

原理：微信 4.0 收到文件后落在
      C:\\Users\\wardc\\xwechat_files\\<账号>\\msg\\file\\<YYYY-MM>\\<原文件名>
      本脚本从索引库读出老师发过的所有**文件类**消息（type=link），
      再去 xwechat_files 里按文件名找，找到就复制过来；没找到的列出来提醒你去微信点下载。

用法：
    python 收集老师发的文件.py            # 复制到桌面资料夹
    python 收集老师发的文件.py --dry-run  # 只看会复制什么，不动文件
    python 收集老师发的文件.py --list     # 只列老师发过哪些文件
"""
import sqlite3, os, sys, shutil, glob, argparse

sys.stdout.reconfigure(encoding="utf-8")

DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
TALKER = "guo647789"                    # 海燕（中传·李老师）
WX_ROOT = r"C:\Users\wardc\xwechat_files"
DEST = r"C:\Users\wardc\Desktop\中传交互技术课_资料"


def teacher_files():
    """从索引库读出老师发过的文件类消息（文件名 + 时间）。"""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = list(con.execute(
        "SELECT ts, content FROM messages WHERE session_key=? AND role='them' "
        "AND type='link' ORDER BY ts", (TALKER,)))
    con.close()
    import datetime
    out = []
    for ts, content in rows:
        name = (content or "").strip()
        if not name:
            continue
        t = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        out.append((t, name))
    return out


def find_local(fname):
    """在微信目录里找这个文件（可能带 (1) 之类的重名后缀）。"""
    stem, ext = os.path.splitext(fname)
    pats = [fname, f"{stem} (*){ext}", f"{stem}*{ext}"]
    for pat in pats:
        for hit in glob.glob(os.path.join(WX_ROOT, "**", pat), recursive=True):
            if os.path.isfile(hit):
                return hit
    return None


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只看会复制什么")
    ap.add_argument("--list", action="store_true", help="只列清单")
    args = ap.parse_args()

    files = teacher_files()
    if not files:
        print("老师没有发过文件（type=link 的消息为 0）")
        return

    print(f"李老师发过的文件共 {len(files)} 个：\n")
    found, missing = [], []
    for t, name in files:
        src = find_local(name)
        if src:
            found.append((t, name, src))
            print(f"  ✅ {t}  {name}  ({human(os.path.getsize(src))})")
        else:
            missing.append((t, name))
            print(f"  ❌ {t}  {name}  —— 本地没有，需在微信里点一下下载")

    if args.list:
        return

    if not found:
        print("\n⚠️ 一个都没落地。请在微信里点开这两个文件下载，然后重跑本脚本。")
        return

    dest_dir = os.path.join(DEST, "02_软件安装包")
    os.makedirs(dest_dir, exist_ok=True)
    print()
    for t, name, src in found:
        target = os.path.join(dest_dir, name)
        if args.dry_run:
            print(f"  [dry-run] {src}\n         -> {target}")
            continue
        shutil.copy2(src, target)
        print(f"  📦 已复制 -> {target}  ({human(os.path.getsize(target))})")

    if missing and not args.dry_run:
        print(f"\n⚠️ 还有 {len(missing)} 个没下载：")
        for t, name in missing:
            print(f"     {name}（{t} 发的）")
        print("   → 在微信里点开下载，再重跑本脚本即可补齐。")


if __name__ == "__main__":
    main()
