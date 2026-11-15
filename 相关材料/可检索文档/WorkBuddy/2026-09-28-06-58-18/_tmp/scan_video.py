import os, io, time, datetime
roots = [
 r"C:/Users/wardc/xwechat_files",
 r"C:/Users/wardc/AppData/Local/Tencent",
 r"C:/Users/wardc/AppData/Roaming/Tencent",
 r"C:/Users/wardc/Documents",
 r"C:/Users/wardc/AppData/Local/Temp",
]
CUT = time.mktime(time.strptime("2026-10-06","%Y-%m-%d"))
VID = (".mp4",".mov",".m4v",".mkv",".avi",".ts",".flv",".wmv")
hits=[]
t0=time.time()
for root in roots:
    for dp, dns, fns in os.walk(root):
        if time.time()-t0 > 600: break
        for f in fns:
            p = os.path.join(dp,f)
            try:
                st = os.stat(p)
            except Exception:
                continue
            if st.st_mtime < CUT: continue
            if st.st_size < 3*1024*1024: continue
            ext = os.path.splitext(f)[1].lower()
            tag = "VIDEO" if ext in VID else ("OTHER" if st.st_size>8*1024*1024 else "")
            if tag:
                hits.append((st.st_mtime, st.st_size, tag, p))
hits.sort(reverse=True)
with io.open(r"C:/Users/wardc/WorkBuddy AI/2026-09-28-06-58-18/_tmp/scan_video.out","w",encoding="utf-8") as fo:
    fo.write("扫描根: %s\n耗时 %.0fs  命中 %d\n\n" % (roots, time.time()-t0, len(hits)))
    for mt, sz, tag, p in hits[:300]:
        fo.write("%s  %8.1fMB  %-5s  %s\n" % (datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M"), sz/1048576, tag, p))
print("done", len(hits))
