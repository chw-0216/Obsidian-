# -*- coding: utf-8 -*-
"""
87 个有消息的群聊 -> 活跃时间轴
输出：群名 / 消息数 / 我发的条数 / 首条时间 / 末条时间 / 跨度天数
按末条时间排序，用于看「每个阶段他靠哪些群定位自己」。
只读。
"""
import io, os, json, datetime, glob

ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出"

def ts(x):
    try:
        return datetime.datetime.fromtimestamp(int(x))
    except Exception:
        return None

rows = []
dirs = [d for d in os.listdir(ROOT) if d.startswith("群聊_") and os.path.isdir(os.path.join(ROOT, d))]
for d in dirs:
    jp = None
    for f in glob.glob(os.path.join(ROOT, d, "*.json")):
        jp = f; break
    if not jp:
        continue
    try:
        j = json.load(io.open(jp, encoding="utf-8"))
    except Exception as e:
        print("!! 读取失败", d, e); continue
    sess = j.get("session", {})
    msgs = j.get("messages", [])
    times = [m.get("createTime") for m in msgs if m.get("createTime")]
    if not times:
        first = last = None
    else:
        first, last = min(times), max(times)
    sent = sum(1 for m in msgs if m.get("isSend") == 1)
    rows.append({
        "name": sess.get("displayName") or sess.get("nickname") or d,
        "dir": d,
        "count": len(msgs),
        "sent": sent,
        "first": first,
        "last": last,
    })

rows.sort(key=lambda r: (r["last"] or 0))
print("群聊目录数:", len(dirs), " 成功读取:", len(rows))
print()
print("%-34s %5s %5s %-11s %-11s" % ("群名", "总数", "我发", "首条", "末条"))
print("-" * 78)
for r in rows:
    f = ts(r["first"]); l = ts(r["last"])
    fs = f.strftime("%Y-%m-%d") if f else "—"
    ls = l.strftime("%Y-%m-%d") if l else "—"
    nm = r["name"]
    if len(nm) > 32:
        nm = nm[:31] + "…"
    print("%-34s %5d %5d %-11s %-11s" % (nm, r["count"], r["sent"], fs, ls))

# 汇总
tot = sum(r["count"] for r in rows)
totsent = sum(r["sent"] for r in rows)
print("\n合计消息 %d 条，其中我发 %d 条（%.1f%%）" % (tot, totsent, 100.0*totsent/max(tot,1)))
allt = [r["first"] for r in rows if r["first"]] + [r["last"] for r in rows if r["last"]]
if allt:
    print("时间覆盖: %s ~ %s" % (ts(min(allt)).strftime("%Y-%m-%d"), ts(max(allt)).strftime("%Y-%m-%d")))
