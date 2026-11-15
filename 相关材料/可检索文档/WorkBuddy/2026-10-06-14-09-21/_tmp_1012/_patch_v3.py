# -*- coding: utf-8 -*-
"""让「复用已有文件」的记录也带上真实匹配层级：
把「已有」检查从匹配之前移到匹配之后 —— 先算出层级，若磁盘上已有同前缀文件则复用不重写。
"""
import io
p = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\rebuild_imgs_v2.py"
s = io.open(p, encoding="utf-8").read()

old = '''    have = [f for f in os.listdir(mdir) if f.startswith(prefix + "_")] if os.path.isdir(mdir) else []
    if have:
        stat["已有"] += 1
        records.append({"时间": tstr, "发送方": who, "月份": m["ym"], "清晰度档": "已有",
                        "匹配层级": "复用", "来源会话": "", "本地源文件": "",
                        "解密产物": os.path.join(mdir, sorted(have)[0]), "校验": "—"})
        continue

    want'''
new = '''    have = [f for f in os.listdir(mdir) if f.startswith(prefix + "_")] if os.path.isdir(mdir) else []

    want'''
assert old in s, "have 段未命中"
s = s.replace(old, new)

old2 = '''    saved = ""
    if hit:'''
new2 = '''    saved = ""
    if have:
        stat["复用"] += 1
        records.append({"时间": tstr, "发送方": who, "月份": m["ym"],
                        "清晰度档": (lvl.split("-")[-1] if lvl else "复用"),
                        "匹配层级": (lvl or "") + "+复用", "来源会话": hit["conv"] if hit else "",
                        "本地源文件": hit["path"] if hit else "",
                        "解密产物": os.path.join(mdir, sorted(have)[0]), "校验": note or ""})
        if idx % 100 == 0:
            log("    %d/%d · 已归档 %d" % (idx, len(imgs), sum(1 for r in records if r["解密产物"])))
        continue

    if hit:'''
assert old2 in s, "saved 段未命中"
s = s.replace(old2, new2)

io.open(p, "w", encoding="utf-8").write(s)
print("patched OK")
