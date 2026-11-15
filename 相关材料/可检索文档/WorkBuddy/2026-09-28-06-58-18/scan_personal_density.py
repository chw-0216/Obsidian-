import os, datetime, collections, csv

# 只取「个人产出」目录，排除数据导出/缓存类目录
PERSONAL = [
    r"C:\Users\wardc\Documents\WPSDrive",
    r"C:\Users\wardc\Documents\WPS Cloud Files",
    r"C:\Users\wardc\Documents\Tencent Files",
    r"C:\Users\wardc\Documents\Codex",
    r"C:\Users\wardc\Documents\New project gpt\AI-archive",
    r"C:\Users\wardc\Desktop\10_个人资料与旧文件",
    r"C:\Users\wardc\Desktop\03_学历与求职",
    r"C:\Users\wardc\Desktop\04_证件与健康",
    r"C:\Users\wardc\Desktop\05_井邻项目_视觉与丝网印刷",
    r"C:\Users\wardc\Desktop\DSH工作区",
    r"C:\Users\wardc\Desktop\中期汇报_2026-09",
    r"C:\Users\wardc\Pictures\Capture One Catalog",
]
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", ".obsidian", ".cache", ".next", "dist"}

ct = collections.Counter(); mt = collections.Counter()
sizes = collections.Counter()
total = 0

for root in PERSONAL:
    if not os.path.isdir(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            try:
                c = datetime.datetime.fromtimestamp(st.st_ctime)
                m = datetime.datetime.fromtimestamp(st.st_mtime)
            except (OverflowError, OSError, ValueError):
                continue
            ct[f"{c.year}-{c.month:02d}"] += 1
            mt[f"{m.year}-{m.month:02d}"] += 1
            sizes[f"{m.year}-{m.month:02d}"] += st.st_size
            total += 1

print(f"PERSONAL_TOTAL {total}")
print("=== 年（创建 / 修改 / GB）===")
cy = collections.Counter(); my = collections.Counter(); sy = collections.Counter()
for k, v in ct.items(): cy[k[:4]] += v
for k, v in mt.items(): my[k[:4]] += v; sy[k[:4]] += sizes[k]
for y in sorted(set(list(cy) + list(my))):
    if 2017 <= int(y) <= 2026:
        print(f"{y}  创建 {cy[y]:>6}   修改 {my[y]:>6}   {round(sy[y]/1024/1024/1024,2):>6} GB")

print("=== 按月（修改时间，2019-2026）===")
for k in sorted(mt):
    if 2019 <= int(k[:4]) <= 2026:
        print(k, mt[k])

out = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\personal_density.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["年-月", "创建数", "修改数", "GB(按修改月)"])
    for k in sorted(set(list(ct) + list(mt))):
        w.writerow([k, ct[k], mt[k], round(sizes[k]/1024/1024/1024, 2)])
print("WROTE", out)
