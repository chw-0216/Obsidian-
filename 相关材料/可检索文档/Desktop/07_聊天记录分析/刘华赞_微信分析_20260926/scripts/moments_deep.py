# -*- coding: utf-8 -*-
"""朋友圈深度抽取：完整点赞/评论名单、链接类正文、媒体清单、互动网络交叉"""
import json, io, os, sys, urllib.request, re
from datetime import datetime, timedelta, timezone
sys.stdout.reconfigure(encoding="utf-8")

CFG = r"C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT2 = os.path.join(ROOT, "02_结构化分析")
CST = timezone(timedelta(hours=8))
token = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding="utf-8").read()).group(1)


def api(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))


def fmt(ts):
    ts = int(ts)
    if ts > 10 ** 12:
        ts //= 1000
    return datetime.fromtimestamp(ts, CST).strftime("%Y-%m-%d %H:%M:%S")


TARGET = "wxid_ltqmzbyc87cp22"
ME = "wxid_zn4ozsnn8esr21"
MOM = "wxid_1wa75s1kze3o22"

posts = json.load(io.open(os.path.join(RAW, "朋友圈_刘华赞_raw.json"), encoding="utf-8"))["timeline"]

print("=" * 70)
print("A. 刘华赞 19 条动态的完整互动与链接解析")
print("=" * 70)
detail = []
for p in posts:
    r = {
        "时间": fmt(p["createTime"]),
        "type": p.get("type"),
        "正文": (p.get("contentDesc") or "").replace("\n", " ⏎ "),
        "媒体数": len(p.get("media") or []),
        "点赞": p.get("likes") or [],
        "评论": [{"人": c.get("nickname"), "内容": c.get("content")} for c in (p.get("comments") or [])],
        "postId": p.get("id"),
    }
    xml = p.get("rawXml") or ""
    if p.get("type") in (7, 15, 3) or not r["正文"]:
        urls = re.findall(r"<url>(.*?)</url>", xml) or re.findall(r'url="(http[^"]+)"', xml)
        titles = re.findall(r"<title>(.*?)</title>", xml)
        singer = re.findall(r"<singer>(.*?)</singer>", xml)
        r["链接"] = (urls[0][:160] if urls else "")
        r["卡片标题"] = (titles[0][:120] if titles else "")
        r["歌手"] = (singer[0] if singer else "")
    detail.append(r)
    print(f"\n[{r['时间']}] type={r['type']} 媒体={r['媒体数']}")
    print(f"   正文: {r['正文'][:220]}")
    if r.get("卡片标题"):
        print(f"   卡片: {r['卡片标题']}  歌手={r.get('歌手','')}")
    if r.get("链接"):
        print(f"   链接: {r['链接']}")
    print(f"   点赞: {r['点赞']}")
    if r["评论"]:
        print(f"   评论: {r['评论']}")

with io.open(os.path.join(OUT2, "moments_刘华赞_完整.csv"), "w", encoding="utf-8-sig", newline="") as f:
    import csv
    w = csv.writer(f)
    w.writerow(["时间", "type", "正文", "媒体数", "点赞人", "评论", "卡片标题", "歌手", "链接", "postId"])
    for r in detail:
        w.writerow([r["时间"], r["type"], r["正文"], r["媒体数"], "|".join(r["点赞"]),
                    "||".join(f"{c['人']}:{c['内容']}" for c in r["评论"]),
                    r.get("卡片标题", ""), r.get("歌手", ""), r.get("链接", ""), r["postId"]])

print("\n" + "=" * 70)
print("B. 互动网络：谁在给她点赞 / 评论")
print("=" * 70)
like_ct, cmt_ct = {}, {}
for r in detail:
    for n in r["点赞"]:
        like_ct[n] = like_ct.get(n, 0) + 1
    for c in r["评论"]:
        cmt_ct[c["人"]] = cmt_ct.get(c["人"], 0) + 1
print("点赞榜:", dict(sorted(like_ct.items(), key=lambda kv: -kv[1])))
print("评论榜:", dict(sorted(cmt_ct.items(), key=lambda kv: -kv[1])))
print("总动态:", len(detail), "｜有互动的:", sum(1 for r in detail if r["点赞"] or r["评论"]),
      "｜零互动的:", sum(1 for r in detail if not r["点赞"] and not r["评论"]))

print("\n" + "=" * 70)
print("C. 反向核查：我 / 母亲 / 华天雪 的朋友圈里她是否出现")
print("=" * 70)
for who, name in [(ME, "蔡浩文（我）"), (MOM, "刘丽萍（母亲）"), ("wxid_jycd1ii1qxro22", "华天雪")]:
    try:
        d = api(f"/api/v1/sns/timeline?usernames={who}&limit=200&media=0")
        tl = [p for p in (d.get("timeline") or []) if p.get("username") == who]
        hits_like = sum(1 for p in tl if any(n in ("*", "懒瓒", "刘华赞", "赞赞") for n in (p.get("likes") or [])))
        hits_cmt = []
        for p in tl:
            for c in (p.get("comments") or []):
                if c.get("nickname") in ("*", "懒瓒", "刘华赞", "赞赞"):
                    hits_cmt.append((fmt(p["createTime"]), c.get("content"), (p.get("contentDesc") or "")[:60]))
        print(f"  {name}: 朋友圈 {len(tl)} 条；她点赞 {hits_like} 次；她评论 {len(hits_cmt)} 次")
        for h in hits_cmt:
            print("      ", h)
    except Exception as e:
        print(f"  {name}: 查询失败 {e}")

print("\n" + "=" * 70)
print("D. 全量朋友圈快照里她出现的次数（含所有朋友圈，不限发布者）")
print("=" * 70)
allp, offset = [], 0
while True:
    d = api(f"/api/v1/sns/timeline?limit=200&offset={offset}&media=0")
    b = d.get("timeline") or []
    allp += b
    if len(b) < 200:
        break
    offset += len(b)
print("  全量条数:", len(allp))
n_like = sum(1 for p in allp if any(x in ("*", "懒瓒", "刘华赞", "赞赞") for x in (p.get("likes") or [])))
n_cmt = 0
for p in allp:
    for c in (p.get("comments") or []):
        if c.get("nickname") in ("*", "懒瓒", "刘华赞", "赞赞"):
            n_cmt += 1
print(f"  她给别人的点赞总数: {n_like}；她的评论总数: {n_cmt}")
print("  发布者昵称为 '*' 的动态数:", sum(1 for p in allp if p.get("nickname") == "*"))
json.dump(allp, io.open(os.path.join(RAW, "朋友圈_全量快照_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
