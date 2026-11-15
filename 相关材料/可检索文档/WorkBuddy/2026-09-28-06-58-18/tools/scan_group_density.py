# -*- coding: utf-8 -*-
"""87 群：发言密度排行 + 分类聚合。只读。"""
import io, os, json, glob, datetime

ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\07_WeFlow原始导出_2026-07-24\01_WeFlow可读导出"

rows = []
for d in os.listdir(ROOT):
    if not (d.startswith("群聊_") and os.path.isdir(os.path.join(ROOT, d))):
        continue
    fs = glob.glob(os.path.join(ROOT, d, "*.json"))
    if not fs:
        continue
    j = json.load(io.open(fs[0], encoding="utf-8"))
    ms = j["messages"]
    sent = sum(1 for m in ms if m.get("isSend") == 1)
    spk = len({m.get("senderDisplayName") for m in ms})
    times = [m["createTime"] for m in ms if m.get("createTime")]
    rows.append(dict(name=j["session"].get("displayName") or d, n=len(ms), sent=sent,
                     spk=spk, first=min(times) if times else 0, last=max(times) if times else 0))

tot = sum(r["n"] for r in rows); tots = sum(r["sent"] for r in rows)
print("群 %d | 消息 %d | 我发 %d (%.2f%%)" % (len(rows), tot, tots, 100.0*tots/tot))

print("\n===== 发言密度 TOP15（我的条数占该群）=====")
rows2 = sorted(rows, key=lambda r: -(r["sent"]/max(r["n"],1)))
for r in rows2[:15]:
    print("  %5.1f%%  %4d/%-4d  %s" % (100.0*r["sent"]/r["n"], r["sent"], r["n"], r["name"][:36]))

print("\n===== 发言密度 BOTTOM10（大群里最沉默）=====")
big = [r for r in rows if r["n"] >= 300]
for r in sorted(big, key=lambda r: r["sent"]/r["n"])[:10]:
    print("  %5.2f%%  %4d/%-4d  %s" % (100.0*r["sent"]/r["n"], r["sent"], r["n"], r["name"][:36]))

print("\n===== 归属型大群（>=800 条，按规模）=====")
for r in sorted([x for x in rows if x["n"] >= 800], key=lambda r: -r["n"]):
    print("  %5d 条  我发 %3d (%.2f%%)  %s" % (r["n"], r["sent"], 100.0*r["sent"]/r["n"], r["name"][:40]))

print("\n===== 格拉斯哥校友会系（同一名目多群）=====")
gg = [r for r in rows if "校友会" in r["name"] or "格大" in r["name"] or "泛国贸" in r["name"]]
for r in sorted(gg, key=lambda r: r["name"]):
    f = datetime.datetime.fromtimestamp(r["first"]).strftime("%Y-%m-%d")
    l = datetime.datetime.fromtimestamp(r["last"]).strftime("%Y-%m-%d")
    print("  %-22s %4d条 我发%3d  %s~%s" % (r["name"][:22], r["n"], r["sent"], f, l))
print("  小计: %d 群, %d 条, 我发 %d 条" % (len(gg), sum(r["n"] for r in gg), sum(r["sent"] for r in gg)))
