# -*- coding: utf-8 -*-
"""materials 表覆盖的图片文件分布 —— 找被 photo_index 漏掉的照片目录"""
import sqlite3, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\batch\batch.sqlite"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== materials 列 ===")
for r in c.execute("pragma table_info(materials)"):
    print(" ", r[1], r[2])

print("\n=== materials 总数 ===", c.execute("select count(*) from materials").fetchone()[0])

IMG = "('jpg','jpeg','png','bmp','tif','tiff','gif','webp','heic','hevc')"
print("\n=== 图片类文件：按顶层目录 ===")
for r in c.execute("""select
      case when instr(path,'\\')>0 then substr(path,1,instr(substr(path,instr(path,'\\')+1),'\\')+instr(path,'\\')-1) else path end top,
      count(*) n
    from materials
    where lower(ext) in %s
    group by top order by n desc limit 40""" % IMG):
    print("  %-70s %d" % ((r[0] or "")[:70], r[1]))
