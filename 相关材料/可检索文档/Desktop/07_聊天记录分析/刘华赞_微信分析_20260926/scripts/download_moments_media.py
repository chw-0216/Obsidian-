# -*- coding: utf-8 -*-
"""下载刘华赞朋友圈图片/封面，并按动态生成拼图（contact sheet）"""
import json, io, os, sys, re, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\wardc\Desktop\07_聊天记录分析\刘华赞_微信分析_20260926"
RAW = os.path.join(ROOT, "00_原始导出")
MED = os.path.join(ROOT, "04_朋友圈媒体")
os.makedirs(MED, exist_ok=True)
CST = timezone(timedelta(hours=8))

posts = json.load(io.open(os.path.join(RAW, "朋友圈_刘华赞_raw.json"), encoding="utf-8"))["timeline"]

# 媒体代理地址需要 Bearer Token（WeFlow /api/v1/sns/media/proxy 受鉴权保护）
CFG = r"C:\Users\wardc\AppData\Roaming\WeFlow\WeFlow-config.json"
TOKEN = re.search(r'"httpApiToken"\s*:\s*"([^"]*)"', io.open(CFG, encoding="utf-8").read()).group(1)


def fmt(ts):
    return datetime.fromtimestamp(int(ts), CST).strftime("%Y%m%d_%H%M%S")


def fetch(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                  "Authorization": "Bearer " + TOKEN})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        return f"ERR {e}"


manifest = []
for idx, p in enumerate(posts, 1):
    stamp = fmt(p["createTime"])
    desc = re.sub(r"[^\w\u4e00-\u9fff]+", "_", (p.get("contentDesc") or "无文字"))[:20] or "无文字"
    d = os.path.join(MED, f"{idx:02d}_{stamp}_{desc}")
    os.makedirs(d, exist_ok=True)
    urls = []
    for m in (p.get("media") or []):
        u = m.get("resolvedUrl") or m.get("url")
        if u:
            urls.append(u)
    got = []
    for k, u in enumerate(urls, 1):
        ext = ".mp4" if "video" in u.lower() else ".jpg"
        fp = os.path.join(d, f"{k:02d}{ext}")
        n = fetch(u, fp)
        got.append({"file": os.path.basename(fp), "bytes": n})
    manifest.append({"序号": idx, "时间": p["createTime"], "正文": p.get("contentDesc") or "",
                     "type": p.get("type"), "目录": os.path.relpath(d, ROOT), "媒体": got})
    ok = sum(1 for g in got if isinstance(g["bytes"], int))
    print(f"[{idx:02d}] {stamp} type={p.get('type')} 媒体 {ok}/{len(urls)} 下载成功  -> {os.path.basename(d)}")

json.dump(manifest, io.open(os.path.join(ROOT, "02_结构化分析", "moments_media_manifest.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n媒体根目录:", MED)
