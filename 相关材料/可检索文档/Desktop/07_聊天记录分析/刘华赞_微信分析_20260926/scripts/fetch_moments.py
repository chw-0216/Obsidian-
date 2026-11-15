# -*- coding: utf-8 -*-
"""
朋友圈（Moments）抽取：刘华赞 wxid_ltqmzbyc87cp22 及关联人
输出：00_原始导出/朋友圈_*.json、02_结构化分析/moments_*.csv
"""
import json, io, os, sys, urllib.request, csv
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
CFG = r"C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json"
BASE = "http://127.0.0.1:5031"
ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
OUT2 = os.path.join(ROOT, "02_结构化分析")
CST = timezone(timedelta(hours=8))

with io.open(CFG, encoding="utf-8") as f:
    raw = f.read()
import re
token = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', raw).group(1)


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
MOTHER_OF = "wxid_jycd1ii1qxro22"

print("=== 1) 拉取刘华赞的朋友圈（usernames 过滤，分页） ===")
posts, offset, page = [], 0, 0
while page < 20:
    d = api(f"/api/v1/sns/timeline?usernames={TARGET}&limit=200&offset={offset}&media=1")
    batch = d.get("timeline") or []
    mine = [p for p in batch if p.get("username") == TARGET]
    print(f"  page{page} offset={offset}: 返回 {len(batch)} 条，其中本人 {len(mine)} 条（total count={d.get('count')}）")
    posts += mine
    if len(batch) < 200 or not batch:
        break
    offset += len(batch)
    page += 1

# 去重
seen, uniq = set(), []
for p in posts:
    k = p.get("id") or p.get("tid")
    if k in seen:
        continue
    seen.add(k)
    uniq.append(p)
uniq.sort(key=lambda p: int(p.get("createTime") or 0))
print(f"  → 去重后 {len(uniq)} 条")

with io.open(os.path.join(RAW, "朋友圈_刘华赞_raw.json"), "w", encoding="utf-8") as f:
    json.dump({"exportedAt": datetime.now(CST).isoformat(), "username": TARGET,
               "count": len(uniq), "timeline": uniq}, f, ensure_ascii=False, indent=2)


def text_of(p):
    if p.get("contentDesc"):
        return p["contentDesc"]
    c = p.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, dict):
        for k in ("desc", "title", "text"):
            if c.get(k):
                return c[k]
    return ""


rows = []
for p in uniq:
    rows.append({
        "发布时间": fmt(p["createTime"]),
        "类型type": p.get("type"),
        "正文": (text_of(p) or "").replace("\n", " ")[:800],
        "媒体数": len(p.get("media") or []),
        "图片": "、".join(m.get("resolvedUrl", "") for m in (p.get("media") or []) if "image" in str(m.get("type", "")) or True)[:0] or len(p.get("media") or []),
        "位置": json.dumps(p.get("location") or p.get("poi") or "", ensure_ascii=False)[:200],
        "点赞": json.dumps(p.get("likes") or p.get("likeList") or "", ensure_ascii=False)[:400],
        "评论": json.dumps(p.get("comments") or p.get("commentList") or "", ensure_ascii=False)[:600],
        "postId": p.get("id"),
        "tid": p.get("tid"),
    })

with io.open(os.path.join(OUT2, "moments_刘华赞.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["发布时间"])
    w.writeheader()
    w.writerows(rows)

print("\n=== 2) 字段结构（第一条的全部键） ===")
if uniq:
    print("  ", sorted(uniq[0].keys()))
    print("\n=== 3) 逐条摘要 ===")
    for p in uniq:
        print(f"  [{fmt(p['createTime'])}] type={p.get('type')} media={len(p.get('media') or [])} | {text_of(p)[:200]!r}")
        for k in ("likes", "likeList", "comments", "commentList", "location", "poi", "nickname"):
            if p.get(k):
                print(f"        {k}: {json.dumps(p[k], ensure_ascii=False)[:400]}")
