# -*- coding: utf-8 -*-
import os
from docx import Document

p = r"C:\Users\wardc\Desktop\星球展宣传片_整理_2026-10-19\寻星展宣传片_拍摄执行方案_v0.1.docx"
doc = Document(p)
print("paragraphs:", len(doc.paragraphs), "tables:", len(doc.tables))
print("\n=== headings / first lines ===")
for i, para in enumerate(doc.paragraphs):
    t = para.text.strip()
    if not t:
        continue
    if len(t) < 60 and (t[0].isdigit() or t.startswith("一、") or t.startswith("二、") or para.runs and para.runs[0].font.size and para.runs[0].font.size.pt >= 11.5):
        print(f"[{i}] {t[:80]}")
print("\n=== tables ===")
for ti, tbl in enumerate(doc.tables):
    print(f"table {ti}: rows={len(tbl.rows)} cols={len(tbl.columns)} | header={[c.text for c in tbl.rows[0].cells]}")
    if len(tbl.rows) > 1:
        print("   row1:", [c.text[:40] for c in tbl.rows[1].cells])

full = "\n".join(x.text for x in doc.paragraphs)
for txt in ["寻星——系外行星主题科普艺术展", "2026 年全国科普月", "2148", "923", "B1", "S22", "待补充信息清单"]:
    print(f"contains {txt!r}:", txt in full or any(txt in c.text for tb in doc.tables for row in tb.rows for c in row.cells))
