# -*- coding: utf-8 -*-
"""修正匹配规则：
旧规则  mid 键只接受「无后缀」文件 → 大量 _h.dat 被排除（MISS 的主因）
新规则  同月：按 hd → mid → thumb 依次，对**任意后缀**取候选（hd 优先 _h.dat，thumb 优先 _t.dat）
        跨月：同上，但必须通过长宽比校验
"""
import io
p = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\rebuild_imgs_v2.py"
s = io.open(p, encoding="utf-8").read()

old = '''def cl(key, sfx, ym, any_ym=False):
    if not key or int(key) <= 0: return []
    out = []
    for r in by_dec.get(int(key), []):
        if not any_ym and r["ym"] != ym: continue
        n = r["name"]
        if sfx == "_h.dat" and not n.endswith("_h.dat"): continue
        if sfx == "_t.dat" and not n.endswith("_t.dat"): continue
        if sfx is None and n.endswith(("_t.dat", "_h.dat")): continue
        out.append(r)
    return out'''

new = '''def cl(key, pref, ym, any_ym=False):
    """pref: 'h' → 优先 _h.dat；'t' → 优先 _t.dat；'m' → 优先无后缀。不排除任何后缀。"""
    if not key or int(key) <= 0: return []
    cand = [r for r in by_dec.get(int(key), []) if any_ym or r["ym"] == ym]
    def rank(r):
        n = r["name"]
        if pref == "h":
            return 0 if n.endswith("_h.dat") else (1 if not n.endswith("_t.dat") else 2)
        if pref == "t":
            return 0 if n.endswith("_t.dat") else (1 if not n.endswith("_h.dat") else 2)
        return 0 if not n.endswith(("_t.dat", "_h.dat")) else (1 if n.endswith("_h.dat") else 2)
    cand.sort(key=rank)
    return cand'''
assert old in s, "cl 未命中"
s = s.replace(old, new)

old2 = '''    if not hit:
        for tag, key, sfx in (("H", m["hd"], "_h.dat"), ("M", m["length"], None), ("T", m["thumb"], "_t.dat")):
            for r in cl(key, sfx, m["ym"]):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                hit, img, kind, note, lvl = r, i2, k2, "同月·" + nt, "同月-" + tag
                break
            if hit: break

    if not hit:
        for tag, key, sfx in (("H", m["hd"], "_h.dat"), ("M", m["length"], None), ("T", m["thumb"], "_t.dat")):
            for r in cl(key, sfx, m["ym"], True):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                if not ok: continue
                hit, img, kind, note, lvl = r, i2, k2, "跨月·" + nt, "跨月-" + tag
                break
            if hit: break'''

new2 = '''    if not hit:
        for tag, key, pref in (("H", m["hd"], "h"), ("M", m["length"], "m"), ("T", m["thumb"], "t")):
            for r in cl(key, pref, m["ym"]):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                hit, img, kind, note, lvl = r, i2, k2, "同月·" + nt + "·" + r["name"][-8:], "同月-" + tag
                break
            if hit: break

    if not hit:
        for tag, key, pref in (("H", m["hd"], "h"), ("M", m["length"], "m"), ("T", m["thumb"], "t")):
            for r in cl(key, pref, m["ym"], True):
                try:
                    i2 = decode(open(r["path"], "rb").read()); k2 = kind_of(i2)
                except Exception: continue
                if not k2: continue
                ok, nt = aspect_ok(i2, k2, want)
                if not ok: continue
                hit, img, kind, note, lvl = r, i2, k2, "跨月·" + nt, "跨月-" + tag
                break
            if hit: break'''
assert old2 in s, "匹配段未命中"
s = s.replace(old2, new2)

io.open(p, "w", encoding="utf-8").write(s)
print("patched OK")
