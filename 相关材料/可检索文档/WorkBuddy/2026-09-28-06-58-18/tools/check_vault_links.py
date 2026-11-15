# -*- coding: utf-8 -*-
"""Obsidian Vault 断链体检 v2（只读）

修正 v1 的误报：v1 把 `[text](../../Desktop/xx.md)` 这类**相对路径 Markdown 链接**
也当成了 wiki 链接目标，导致大量假断链。

v2 分开处理：
- wiki 链接 [[目标]]      → 与全库 .md 文件名（不含扩展名）比对
- Markdown 链接 [t](p.md) → 按「源文件所在目录」解析相对路径，检查磁盘是否存在
- 跳过 ``` 代码块内的内容
- 跳过 http(s) / 锚点

输出：vault_link_report.csv（type 列区分 wiki / md）
"""
import os, re, csv, collections

VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\vault_link_report.csv"
SKIP_DIRS = {".obsidian", ".trash", ".git"}

WIKI_RE = re.compile(r"\[\[(.+?)\]\]")
MD_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+?\.md)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"```.*?```", re.S)


def parse_wiki(inner: str) -> str:
    """从 [[目标|别名#锚点]] 里取出目标。
    注意：表格内 Obsidian 用 `\\|` 转义竖线 —— 先还原成 `|` 再切分
    （Windows 文件名不含 `|`，所以还原后切分是安全的）。"""
    inner = inner.replace("\\|", "|")
    target = inner.split("|")[0]
    target = target.split("#")[0]
    return target.strip()


def strip_md_ext(name: str) -> str:
    """只剥掉结尾的 .md —— 不能用 splitext！
    文件名里可能含点（如 `AAA.麻辣自嗨锅女士`），splitext 会在最后一个点切错。"""
    return name[:-3] if name.lower().endswith(".md") else name


def strip_code(txt: str) -> str:
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), txt)


files, all_files = [], []
for root, dirs, fnames in os.walk(VAULT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fn in fnames:
        ap = os.path.join(root, fn)
        rp = os.path.relpath(ap, VAULT)
        all_files.append((rp, ap))
        if fn.lower().endswith(".md"):
            files.append((rp, ap))

# ★ wiki 链接可以指向**任意类型**的文件（.base / .canvas / .png / .pdf …），
#   不能只索引 .md —— 否则 `[[① 待本人确认.base]]` 会被误判成断链。
by_name = collections.defaultdict(list)
for rp, ap in all_files:
    b = os.path.basename(rp)
    by_name[b].append(rp)                    # 带扩展名的原名
    by_name[strip_md_ext(b)].append(rp)      # 去掉 .md 的名字

rows = []
for rp, ap in files:
    try:
        txt = open(ap, encoding="utf-8").read()
    except UnicodeDecodeError:
        txt = open(ap, encoding="gbk", errors="ignore").read()
    txt = strip_code(txt)

    # 1) wiki 链接
    for inner in WIKI_RE.findall(txt):
        t = parse_wiki(inner)
        if not t or t.startswith("http"):
            continue
        bn = os.path.basename(t)
        if bn in by_name or strip_md_ext(bn) in by_name:
            continue
        rows.append({"type": "wiki", "source": rp, "target": t, "resolved": ""})

    # 2) markdown 相对链接
    for t in MD_RE.findall(txt):
        t = t.strip()
        if t.startswith(("http://", "https://", "#")):
            continue
        t2 = t.replace("/", os.sep)
        cand = os.path.normpath(os.path.join(os.path.dirname(ap), t2))
        if os.path.exists(cand):
            continue
        # 也许写成了 vault 内的相对路径
        cand2 = os.path.normpath(os.path.join(VAULT, t2.lstrip(os.sep)))
        if os.path.exists(cand2):
            continue
        rows.append({"type": "md", "source": rp, "target": t, "resolved": cand})

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["type", "source", "target", "resolved"])
    w.writeheader()
    w.writerows(rows)

wiki = [r for r in rows if r["type"] == "wiki"]
md = [r for r in rows if r["type"] == "md"]
print(f"扫描文件数 : {len(files)}")
print(f"真·断链总数: {len(rows)}   （wiki {len(wiki)} / md {len(md)}）")
print()
print("=== wiki 断链（全库找不到同名笔记）===")
c = collections.Counter(r["target"] for r in wiki)
for name, cnt in c.most_common(40):
    print(f"{cnt:>3}  [[{name}]]")
print()
print("=== md 断链（相对路径在磁盘上不存在）===")
seen = set()
for r in md:
    key = (r["source"], r["target"])
    if key in seen:
        continue
    seen.add(key)
    print(f"  [{r['source']}]\n      -> {r['target']}")
