import os, sys, datetime, collections, csv

ROOTS = [
    r"C:\Users\wardc\Documents",
    r"C:\Users\wardc\Desktop",
    r"C:\Users\wardc\Pictures",
    r"C:\Users\wardc\Downloads",
    r"C:\Users\wardc\Videos",
    r"C:\Users\wardc\Music",
    r"C:\Users\wardc\OneDrive",
]
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", ".obsidian",
        ".workbuddy-ai", ".cache", "AppData", ".next", "dist", "build", ".idea"}

bymonth = collections.Counter()
size_bymonth = collections.Counter()
byfolder = collections.Counter()
size_byfolder = collections.Counter()
total = 0
errs = 0

for root in ROOTS:
    if not os.path.isdir(root):
        continue
    base = os.path.basename(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        rel = os.path.relpath(dirpath, root)
        top = base if rel == "." else base + "/" + rel.split(os.sep)[0]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                errs += 1
                continue
            try:
                dt = datetime.datetime.fromtimestamp(st.st_ctime)
            except (OverflowError, OSError, ValueError):
                errs += 1
                continue
            key = f"{dt.year}-{dt.month:02d}"
            bymonth[key] += 1
            size_bymonth[key] += st.st_size
            if 2019 <= dt.year <= 2026:
                byfolder[(dt.year, top)] += 1
                size_byfolder[(dt.year, top)] += st.st_size
            total += 1

print(f"TOTAL_FILES {total}")
print(f"ERRORS {errs}")
print("=== BY_MONTH (year-month count GB) ===")
for k in sorted(bymonth):
    print(k, bymonth[k], round(size_bymonth[k] / 1024 / 1024 / 1024, 2))

print("=== BY_YEAR ===")
byyear = collections.Counter()
size_byyear = collections.Counter()
for k, v in bymonth.items():
    y = k[:4]
    byyear[y] += v
    size_byyear[y] += size_bymonth[k]
for y in sorted(byyear):
    print(y, byyear[y], round(size_byyear[y] / 1024 / 1024 / 1024, 2))

print("=== TOP FOLDERS PER YEAR (year count GB folder) ===")
years = sorted({y for (y, _) in byfolder})
for y in years:
    items = [(c, f) for (yy, f), c in byfolder.items() if yy == y]
    items.sort(reverse=True)
    print(f"--- {y} ---")
    for c, f in items[:12]:
        print("   ", y, c, round(size_byfolder[(y, f)] / 1024 / 1024 / 1024, 2), f)

out = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\file_density.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["年-月", "文件数", "GB"])
    for k in sorted(bymonth):
        w.writerow([k, bymonth[k], round(size_bymonth[k] / 1024 / 1024 / 1024, 2)])
print("WROTE", out)
