# -*- coding: utf-8 -*-
"""
weflow_export.py — 从 WeFlow 本地 HTTP API 增量导出微信消息

用途：把主库事件断点（2026-07-24）之后的聊天补进来；顺带覆盖「最近一年」。

设计：
  - 全程本地（127.0.0.1:5031），数据不出本机
  - 支持断点续传：已存在的会话 JSON 跳过（除非 --force）
  - 输出格式对齐 08_WeFlow增量导出：每个会话一个目录 + 一个 JSON

用法：
  python weflow_export.py --probe                 # 只探测规模，不落盘
  python weflow_export.py --start 1759075200      # 拉最近一年
  python weflow_export.py --start 1784822400      # 只拉 2026-07-24 之后
"""
import json
import os
import re
import sys
import time
import argparse
import urllib.request
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TK = "wf-04eb74eee9324f5a918832b955384c25"
BASE = "http://127.0.0.1:5031"
OUTDIR = r"C:\Users\wardc\Desktop\07_聊天记录分析\微信聊天记录清理\09_WeFlow增量导出_2026-09-29"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# 商业/服务号：不是真人，跳过（省时间）
SKIP_RE = re.compile(
    r"美团|链家|客服|售后|广告|图文|打印|健身|教育|培训|招生|保险|贷款|中介|"
    r"助理|助手|通知|订阅|公众号|极狐|汽车|酒店|旅行社|维修|网约车|司机|"
    r"代录|代下载|P图|设计师|西装|高定|丝印|建材|开锁|驾校|签证|律所|律师|"
    r"服务员|招聘|兼职|求职|家教中心|服务中心|居委会|派出所|警官|掌厅|"
    r"拼车|团购|内购|秒杀|优惠|商城|工厂|批发|闲鱼|小红书|AI｜|AI摄影师|"
    r"词元|彭于晏|Penny|华住|哈啰|锦溪|星源|星铂|万绿|利世隆|都阳|A~|A0|A恒|A老王|A高强|A信审|A北京正己"
)


def api(path, **params):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TK})
    last = None
    for attempt in range(3):
        try:
            with OPENER.open(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def get_sessions():
    d = api("/api/v1/sessions", limit=2000)
    return d.get("sessions") or []


def fetch_all(talker, start, page=500, hard_cap=300000):
    """翻页拉取 talker 在 start 之后的所有消息（返回按时间正序）"""
    out, offset = [], 0
    while True:
        d = api("/api/v1/messages", talker=talker, start=start, limit=page, offset=offset)
        ms = d.get("messages") or []
        out.extend(ms)
        if not ms or not d.get("hasMore") or len(out) >= hard_cap:
            break
        offset += len(ms)
    out.sort(key=lambda m: (m.get("createTime") or 0, m.get("sortSeq") or 0))
    return out


def safe_name(s):
    """目录名安全化：去掉 Windows 非法字符"""
    s = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", s or "未命名")
    s = s.strip().strip(".")
    return s[:60] or "未命名"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1784822400, help="起始 Unix 秒（默认 2026-07-24）")
    ap.add_argument("--probe", action="store_true", help="只探测规模")
    ap.add_argument("--kind", default="private", choices=["private", "group", "all"])
    ap.add_argument("--force", action="store_true", help="已存在也重拉")
    args = ap.parse_args()

    sess = get_sessions()
    todo = [s for s in sess if (s.get("lastTimestamp") or 0) >= args.start]
    if args.kind != "all":
        todo = [s for s in todo if s.get("sessionType") == args.kind]
    todo.sort(key=lambda s: -(s.get("lastTimestamp") or 0))

    if args.kind == "private":
        skipped = [s for s in todo if SKIP_RE.search(s.get("displayName") or "")]
        todo = [s for s in todo if not SKIP_RE.search(s.get("displayName") or "")]
        print(f"跳过商业/服务号：{len(skipped)} 个")

    print(f"待处理会话：{len(todo)} 个（kind={args.kind}, start={args.start}）")
    print()

    total_msgs = 0
    manifest = []
    for i, s in enumerate(todo, 1):
        name = s.get("displayName") or s.get("username")
        uname = s.get("username")
        d = os.path.join(OUTDIR, "01_WeFlow可读导出", f"私聊_{safe_name(name)}" if args.kind == "private" else f"群聊_{safe_name(name)}")
        fp = os.path.join(d, f"{'私聊' if args.kind=='private' else '群聊'}_{safe_name(name)}.json")

        if args.probe:
            ms = fetch_all(uname, args.start, page=500)
            n = len(ms)
            span = ""
            if ms:
                span = "%s ~ %s" % (
                    time.strftime("%Y-%m-%d", time.localtime(ms[0]["createTime"])),
                    time.strftime("%Y-%m-%d", time.localtime(ms[-1]["createTime"])),
                )
            total_msgs += n
            print(f"[{i:>3}/{len(todo)}] {n:>6} 条  {str(name)[:24]:<26} {span}")
            continue

        if os.path.exists(fp) and not args.force:
            try:
                n = len(json.load(open(fp, encoding="utf-8")).get("messages") or [])
                total_msgs += n
                print(f"[{i:>3}/{len(todo)}] 已存在，跳过（{n} 条）  {str(name)[:24]}")
                manifest.append({"name": name, "username": uname, "count": n, "file": fp, "status": "cached"})
                continue
            except Exception:
                pass

        ms = fetch_all(uname, args.start)
        os.makedirs(d, exist_ok=True)
        payload = {
            "success": True, "talker": uname, "count": len(ms), "hasMore": False,
            "displayName": name, "sessionType": s.get("sessionType"),
            "exportedAt": int(time.time()), "startTs": args.start,
            "messages": ms,
        }
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        total_msgs += len(ms)
        manifest.append({"name": name, "username": uname, "count": len(ms), "file": fp, "status": "ok"})
        print(f"[{i:>3}/{len(todo)}] {len(ms):>6} 条  {str(name)[:26]}")

    print()
    print(f"合计消息：{total_msgs}")

    if not args.probe:
        os.makedirs(OUTDIR, exist_ok=True)
        mf = os.path.join(OUTDIR, f"manifest_{'private' if args.kind=='private' else args.kind}_{args.start}.json")
        with open(mf, "w", encoding="utf-8") as f:
            json.dump({"start": args.start, "kind": args.kind, "total": total_msgs, "sessions": manifest}, f, ensure_ascii=False, indent=2)
        print(f"→ {mf}")


if __name__ == "__main__":
    main()
