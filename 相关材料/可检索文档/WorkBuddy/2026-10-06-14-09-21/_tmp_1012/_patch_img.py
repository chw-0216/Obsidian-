# -*- coding: utf-8 -*-
import io
p = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012\final_chenye_img_index.py"
s = io.open(p, encoding="utf-8").read()

old1 = '''            if mm:
                h = os.path.join(IMG_DIR, "_t.h265"); open(h, "wb").write(img[mm.start():])
                dst = os.path.join(mdir, prefix + "_补.jpg"); os.makedirs(mdir, exist_ok=True)
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dst], capture_output=True)
                if os.path.exists(dst) and os.path.getsize(dst) > 0: saved = dst
                os.remove(h)'''
new1 = '''            if mm:
                h = os.path.join(TMPD, "_t.h265")
                with open(h, "wb") as fh: fh.write(img[mm.start():])
                dst = os.path.join(mdir, prefix + "_补.jpg"); os.makedirs(mdir, exist_ok=True)
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", h, "-frames:v", "1", dst], capture_output=True)
                if os.path.exists(dst) and os.path.getsize(dst) > 0: saved = dst'''
assert old1 in s, "h265 段未命中"
s = s.replace(old1, new1)

marker = 'AES_KEY = b"d24287c68e6e3244"; XOR_KEY = 0xE1'
assert marker in s, "AES 行未命中"
s = s.replace(marker, 'import tempfile\nTMPD = tempfile.gettempdir()\n' + marker)

old3 = '''            q = os.path.join(QUAR, ym); os.makedirs(q, exist_ok=True)
            shutil.move(os.path.join(d, f), os.path.join(q, f)); moved += 1'''
new3 = '''            q = os.path.join(QUAR, ym); os.makedirs(q, exist_ok=True)
            try:
                shutil.move(os.path.join(d, f), os.path.join(q, f)); moved += 1
            except Exception: pass'''
assert old3 in s, "隔离段未命中"
s = s.replace(old3, new3)

io.open(p, "w", encoding="utf-8").write(s)
print("patched OK")
