# -*- coding: utf-8 -*-
"""
sanitize_vault_pii.py —— 知识库 PII 脱敏（默认 dry-run，绝不自动改文件）

为什么需要：Obsidian Sync 一旦开启，**知识库里的手机号 / 身份证 / 银行卡会原样上传**。
Sync 的「排除文件夹」是**事后生效**的 —— 先加排除不会移除已同步的文件。

默认只**列清单**，不动任何文件：
  python tools\\sanitize_vault_pii.py                 # 列出命中（默认）
真正改写（**会先备份到 _backup_pii_<时间戳>\\**）：
  python tools\\sanitize_vault_pii.py --apply         # 手机号 → 138****1234
  python tools\\sanitize_vault_pii.py --apply --hard  # 手机号 → [手机号已脱敏]

安全约束（对齐《个人文件安全规则》）：
  · 默认只读；--apply 才写
  · 写前整目录备份到工作区 `_tmp/_backup_pii_<ts>/`，路径清单落盘
  · 逐文件改写，改完复核；单批 ≤ 10 个文件，超了分批
  · **不删文件**，只替换文本
"""
import os, io, re, sys, json, shutil, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
BACKUP_ROOT = os.path.join(WS, "_tmp")
BATCH = 10

# ★ 边界必须非字母数字；身份证过校验位、银行卡过 Luhn（否则会把缓存文件名哈希当卡号）
PATTERNS = [
    ("手机号", re.compile(r"(?<![0-9A-Za-z])(1[3-9]\d{9})(?![0-9A-Za-z])")),
    ("身份证", re.compile(r"(?<![0-9A-Za-z])(\d{17}[\dXx])(?![0-9A-Za-z])")),
    ("银行卡", re.compile(r"(?<![0-9A-Za-z])(\d{16,19})(?![0-9A-Za-z])")),
]
_ID_W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_C = "10X98765432"


def id_ok(s):
    if not re.fullmatch(r"\d{17}[\dXx]", s or ""):
        return False
    return _ID_C[sum(int(s[i]) * _ID_W[i] for i in range(17)) % 11] == s[17].upper()


def luhn_ok(s):
    if not (s or "").isdigit() or not (16 <= len(s) <= 19):
        return False
    tot = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        tot += d
    return tot % 10 == 0


def valid(label, v):
    if label == "身份证":
        return id_ok(v)
    if label == "银行卡":
        return luhn_ok(v)
    return True


def mask(label, hard, v):
    if hard:
        return "[%s已脱敏]" % label
    if label == "手机号":
        return v[:3] + "****" + v[7:]
    if label == "身份证":
        return v[:6] + "********" + v[14:]
    return v[:4] + "****" + v[-4:]                 # 银行卡


def scan():
    hits = {}
    for root, dirs, files in os.walk(VAULT):
        if ".obsidian" in root:
            continue
        for fn in files:
            if not fn.endswith((".md", ".csv", ".txt", ".json", ".base")):
                continue
            p = os.path.join(root, fn)
            try:
                t = io.open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            got = {}
            for label, rx in PATTERNS:
                vals = {m.group(1) for m in rx.finditer(t) if valid(label, m.group(1))}
                if vals:
                    got[label] = len(vals)
            if got:
                hits[p] = got
    return hits


def main():
    apply_ = "--apply" in sys.argv
    hard = "--hard" in sys.argv
    hits = scan()
    print("知识库 PII 扫描 · %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("库：%s" % VAULT)
    print()
    if not hits:
        print("✅ 零命中，无需脱敏。")
        return 0
    total = sum(sum(v.values()) for v in hits.values())
    print("命中 %d 个文件 ｜ 敏感串 %d 个：" % (len(hits), total))
    for p, g in sorted(hits.items(), key=lambda x: -sum(x[1].values())):
        print("  %-64s %s" % (os.path.relpath(p, VAULT),
                              "、".join("%s %d" % (k, v) for k, v in g.items())))
    print()
    if not apply_:
        print("▸ 这是**只读清单**，没有改动任何文件。")
        print("▸ 确认要脱敏：python tools\\sanitize_vault_pii.py --apply")
        print("  （会先把整库备份到 _tmp\\_backup_pii_<时间戳>\\，再逐文件替换）")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = os.path.join(BACKUP_ROOT, "_backup_pii_" + ts)
    os.makedirs(bdir, exist_ok=True)
    files = sorted(hits)
    print("备份 → %s（%d 个文件）" % (bdir, len(files)))
    manifest = []
    for p in files:
        rel = os.path.relpath(p, VAULT)
        dst = os.path.join(bdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        manifest.append(rel)
    io.open(os.path.join(bdir, "_manifest.txt"), "w", encoding="utf-8").write("\n".join(manifest))

    done, changed = 0, 0
    for i in range(0, len(files), BATCH):
        batch = files[i:i + BATCH]
        for p in batch:
            t = io.open(p, encoding="utf-8", errors="ignore").read()
            new = t
            for label, rx in PATTERNS:
                new = rx.sub(lambda m, l=label: mask(l, hard, m.group(1)) if valid(l, m.group(1)) else m.group(0), new)
            if new != t:
                io.open(p, "w", encoding="utf-8").write(new)
                changed += 1
            done += 1
        print("  批次 %d：已处理 %d 个（累计改写 %d）" % (i // BATCH + 1, done, changed))

    # 复核
    left = scan()
    print()
    print("复核：剩余命中文件 %d 个" % len(left))
    if left:
        for p, g in left.items():
            print("  ⚠️ %s %s" % (os.path.relpath(p, VAULT), g))
    print("✅ 完成 ｜ 改写 %d 个文件 ｜ 备份在 %s" % (changed, bdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
