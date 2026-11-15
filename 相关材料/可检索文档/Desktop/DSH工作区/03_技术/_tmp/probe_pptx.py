# -*- coding: utf-8 -*-
import sys
from collections import Counter
from pptx import Presentation
from pptx.util import Emu
p = Presentation(sys.argv[1])
print("slide_w_in=%.3f slide_h_in=%.3f" % (p.slide_width/914400, p.slide_height/914400))
print("slides=%d" % len(p.slides._sldIdLst))
pics = tables = boxes = shapes_total = 0
fonts = Counter(); sizes = Counter(); colors = Counter()
for sl in p.slides:
    for sh in sl.shapes:
        shapes_total += 1
        if sh.shape_type is not None and "PICTURE" in str(sh.shape_type):
            pics += 1
        if getattr(sh, "has_table", False) and sh.has_table:
            tables += 1
        if sh.has_text_frame:
            boxes += 1
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    if r.font.name: fonts[r.font.name] += 1
                    if r.font.size: sizes[int(r.font.size.pt)] += 1
                    try:
                        if r.font.color and r.font.color.rgb: colors[str(r.font.color.rgb)] += 1
                    except Exception: pass
print("shapes=%d textframes=%d pictures=%d tables=%d" % (shapes_total, boxes, pics, tables))
print("fonts=%s" % fonts.most_common(3))
print("sizes=%s" % sorted(sizes.items(), key=lambda x: -x[1])[:5])
print("colors=%s" % colors.most_common(4))
