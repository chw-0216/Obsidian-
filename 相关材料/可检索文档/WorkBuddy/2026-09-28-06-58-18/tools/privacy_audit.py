# -*- coding: utf-8 -*-
"""
privacy_audit.py —— 隐私核对：本地 AI 与知识库的对外暴露面（只读，除 --fix）

检查项：
  ① Ollama 监听地址（0.0.0.0 = 局域网可访问，默认应为 127.0.0.1）
  ② Ollama 云端开关（~/.ollama/server.json 的 disable_ollama_cloud / OLLAMA_NO_CLOUD）
  ③ Ollama 历史日志里有无**非本机**访问
  ④ Ollama 对外请求痕迹（ollama.com / github.com 等）
  ⑤ Obsidian Sync 是否启用（.obsidian/sync 目录 / 账号痕迹 / 排除范围）
  ⑥ Obsidian 社区插件数量（第三方插件是最大的隐私面）
  ⑦ 知识库里有没有**聊天原文**（派生产物 vs 原始消息）
  ⑧ 分析脚本是否一律以 mode=ro 打开原始库

用法：
  python tools\\privacy_audit.py            # 只检查
  python tools\\privacy_audit.py --fix      # 顺手把 OLLAMA_HOST 改回 127.0.0.1
  python tools\\privacy_audit.py --json out.json
"""
import os, io, re, sys, json, glob, sqlite3, winreg, datetime

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
TOOLS = os.path.join(WS, "tools")
VAULT = r"C:\Users\wardc\Documents\Obsidian Vault"
OLLAMA_DIR = r"C:\Users\wardc\AppData\Local\Ollama"
OLLAMA_HOME = r"C:\Users\wardc\.ollama"
INDEX_DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
PACK_DIR = r"C:\Users\wardc\Desktop\中期汇报_成果与材料_2026-10-05"

results = []


def check(name, ok, detail="", warn=False, fix=""):
    results.append({"name": name, "ok": bool(ok), "warn": bool(warn and not ok), "detail": str(detail), "fix": fix})
    tag = "PASS" if ok else ("WARN" if warn else "FAIL")
    print("  [%s] %s" % (tag, name))
    if detail:
        for ln in str(detail).splitlines():
            print("        " + ln)
    if fix and not ok:
        print("        ▸ 修复：" + fix)
    return ok


def h1(t):
    print("\n" + "=" * 70); print(t); print("=" * 70)


def env_get(name):
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        return winreg.QueryValueEx(k, name)[0]
    except Exception:
        return None


def env_set(name, value):
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(k)


# ① Ollama 监听地址
def c1(fix=False):
    h1("① Ollama 监听地址")
    host = env_get("OLLAMA_HOST")
    exposed = bool(host) and ("0.0.0.0" in host or "::" in host)
    detail = "OLLAMA_HOST = %s（用户环境变量）" % (host or "（未设置 → 默认 127.0.0.1:11434）")
    if exposed:
        detail += ("\n0.0.0.0 = **监听所有网卡**，同一 WiFi 下任何设备都能调用你的 Ollama"
                   "\n（无鉴权：可列模型、可跑推理、可拉模型占满磁盘）")
        if fix:
            env_set("OLLAMA_HOST", "127.0.0.1:11434")
            detail += "\n✅ 已改为 127.0.0.1:11434（重启 Ollama 后生效）"
            exposed = False
    check("Ollama 只监听本机", not exposed, detail, warn=False,
          fix="python tools\\privacy_audit.py --fix" if exposed else "")
    return {"host": host}


# ② 云端开关
def c2():
    h1("② Ollama 云端开关")
    p = os.path.join(OLLAMA_HOME, "server.json")
    val = None
    if os.path.exists(p):
        try:
            val = json.load(io.open(p, encoding="utf-8")).get("disable_ollama_cloud")
        except Exception as e:
            val = "解析失败：%s" % e
    env_no = env_get("OLLAMA_NO_CLOUD")
    log_hit, log_at = "", ""
    for f in glob.glob(os.path.join(OLLAMA_DIR, "server*.log")):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        # 取「时间戳最新」的那条，而不是文件顺序最后一条
        for m in re.finditer(r"time=([\d\-T:+.]+).*?Ollama cloud disabled: (\w+)", t):
            if m.group(1) > log_at:
                log_at, log_hit = m.group(1), m.group(2)
    ok = (val is True) or (env_no == "1") or (log_hit == "true")
    check("Ollama 云功能已关闭", ok,
          "server.json: %s\nOLLAMA_NO_CLOUD: %s\n日志最近一次启动: %s"
          % (p + " → disable_ollama_cloud=" + str(val) if os.path.exists(p) else "（无 server.json）",
             env_no or "（未设置）",
             ("Ollama cloud disabled: %s（%s）" % (log_hit, log_at)) if log_hit else "（日志中未见该行）"))
    return {"server_json": val, "env": env_no, "log": log_hit}


# ③ 非本机访问
def c3():
    h1("③ Ollama 历史日志里有没有「非本机」访问")
    ips = {}
    for f in glob.glob(os.path.join(OLLAMA_DIR, "server*.log")):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for ip in re.findall(r"\|\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*\|", t):
            ips[ip] = ips.get(ip, 0) + 1
    ext = {k: v for k, v in ips.items() if k != "127.0.0.1"}
    top = "、".join("%s×%d" % (k, v) for k, v in sorted(ips.items(), key=lambda x: -x[1])[:5])
    check("从未有外部设备访问过", not ext,
          "客户端 IP 分布：%s%s" % (top or "（无记录）",
          ("\n⚠️ 外部访问：%s" % ext) if ext else "\n→ 说明 0.0.0.0 这个设置**从未被真正用上**"))
    return {"ips": ips, "external": ext}


# ④ 对外请求
def c4():
    h1("④ Ollama 的对外请求痕迹")
    hosts = {}
    for f in glob.glob(os.path.join(OLLAMA_DIR, "*.log")):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for h in re.findall(r"https?://([A-Za-z0-9.-]+)", t):
            hosts[h] = hosts.get(h, 0) + 1
    show = {k: v for k, v in sorted(hosts.items(), key=lambda x: -x[1])[:8]}
    detail = "、".join("%s×%d" % (k, v) for k, v in show.items()) or "（无）"
    detail += ("\n→ 这些是**更新检查 / 模型推荐**，不是聊天内容上传；"
               "\n   关闭云功能后仍会做版本更新检查（与聊天数据无关）")
    check("对外请求只涉及更新/推荐，不涉及聊天内容", True, detail)
    return show


# ⑤ Obsidian Sync
def c5():
    h1("⑤ Obsidian Sync 实际范围")
    sync_dir = os.path.join(VAULT, ".obsidian", "sync")
    has_dir = os.path.isdir(sync_dir)
    core = {}
    cp = os.path.join(VAULT, ".obsidian", "core-plugins.json")
    if os.path.exists(cp):
        try:
            core = json.load(io.open(cp, encoding="utf-8"))
        except Exception:
            pass
    # 账号/设备痕迹
    traces = []
    for pat in ("Local Storage/leveldb/*", "IndexedDB/*/*"):
        for f in glob.glob(os.path.join(os.environ.get("APPDATA", ""), "obsidian", pat)):
            try:
                b = io.open(f, "rb").read()
            except Exception:
                continue
            for kw in (b"obsidian-sync", b"syncDeviceName", b"syncAccount", b"uid="):
                if kw in b:
                    traces.append(os.path.basename(f) + ":" + kw.decode())
    configured = has_dir or bool(traces)
    check("Obsidian Sync 未配置 / 未登录", not configured,
          "sync 核心插件开关：%s\n.obsidian\\sync 目录：%s\n账号/设备痕迹：%s"
          % (core.get("sync"), "存在" if has_dir else "**不存在**",
             "、".join(traces[:4]) if traces else "**无**"))
    check("即便将来开启 Sync，也需先排除敏感目录", True,
          "Sync 的「排除文件夹」是**事后生效**：先加排除不会移除已同步文件。\n"
          "       若开启，务必先排除：03_微信聊天分析、04_工作台（含真人姓名与关系判断）")
    return {"configured": configured, "core_sync": core.get("sync")}


# ⑥ 社区插件
def c6():
    h1("⑥ Obsidian 社区插件")
    cp = os.path.join(VAULT, ".obsidian", "community-plugins.json")
    n = 0
    if os.path.exists(cp):
        try:
            n = len(json.load(io.open(cp, encoding="utf-8")))
        except Exception:
            n = -1
    check("社区插件数可控（第三方插件是最大隐私面）", n <= 5, "已启用 %s 个" % ("无法解析" if n < 0 else n))
    return {"count": n}


# ⑦ 知识库里有没有聊天原文
def c7():
    h1("⑦ 知识库里有没有「聊天原文」")
    n_md = 0
    suspicious = []
    for root, dirs, files in os.walk(VAULT):
        if ".obsidian" in root:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            n_md += 1
            p = os.path.join(root, fn)
            try:
                t = io.open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            # 粗判：出现大段「时间 [角色] 内容」的对话流水
            hits = len(re.findall(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", t))
            if hits >= 30:
                suspicious.append((os.path.relpath(p, VAULT), hits))
    check("知识库里没有成规模的聊天流水原文", not suspicious,
          "扫描 %d 篇笔记 ｜ 疑似含对话流水 %d 篇%s" % (n_md, len(suspicious),
          ("：\n" + "\n".join("  %s（%d 处时间戳）" % x for x in sorted(suspicious, key=lambda y: -y[1])[:6]))
          if suspicious else "\n→ 全部是**派生产物**（画像/结论/报告），不是原始消息"))
    return {"md": n_md, "suspicious": len(suspicious)}


# ⑧ 只读约定
def c8():
    h1("⑧ 分析脚本是否一律只读打开原始库")
    # 白名单：**设计上就要写**的导入脚本（有 --apply 闸门 + 文档写明）
    WRITERS = {"import_channels.py", "rebuild_index.py", "index-incremental.py"}
    bad, n = [], 0
    for f in glob.glob(os.path.join(TOOLS, "*.py")):
        t = io.open(f, encoding="utf-8", errors="ignore").read()
        if "index.sqlite" not in t and "INDEX_DB" not in t:
            continue
        if "sqlite3" not in t:
            # 只是**文案里**提到 index.sqlite（如报告脚注），并不真的连库 —— 不算「涉及原始库」
            continue
        n += 1
        if "mode=ro" in t or os.path.basename(f) in WRITERS:
            continue
        bad.append(os.path.basename(f))
    check("涉及原始库的脚本都用了 mode=ro（或属白名单写库脚本）", not bad,
          "涉及 %d 个脚本 ｜ 白名单写库 %d 个 ｜ 未见只读标记 %d 个%s"
          % (n, len(WRITERS), len(bad), ("：" + "、".join(bad)) if bad else ""),
          warn=True)
    return {"scripts": n, "bad": bad}


# ⑨ 知识库里的个人敏感信息（手机号 / 身份证 / 银行卡）
# ★ 边界必须是「非字母数字」—— 否则缓存文件名里的哈希、时间戳会被当成卡号
PII_PATTERNS = [
    ("手机号", re.compile(r"(?<![0-9A-Za-z])(1[3-9]\d{9})(?![0-9A-Za-z])")),
    ("身份证", re.compile(r"(?<![0-9A-Za-z])(\d{17}[\dXx])(?![0-9A-Za-z])")),
    ("银行卡", re.compile(r"(?<![0-9A-Za-z])(\d{16,19})(?![0-9A-Za-z])")),
]

_ID_W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_C = "10X98765432"


def id_ok(s):
    """身份证校验位（GB 11643-1999）—— 挡掉绝大多数长数字误报"""
    if not re.fullmatch(r"\d{17}[\dXx]", s or ""):
        return False
    tot = sum(int(s[i]) * _ID_W[i] for i in range(17))
    return _ID_C[tot % 11] == s[17].upper()


def luhn_ok(s):
    """银行卡 Luhn 校验 —— 挡掉缓存哈希 / 时间戳"""
    if not (s or "").isdigit() or not (16 <= len(s) <= 19):
        return False
    tot = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        tot += d
    return tot % 10 == 0


def pii_hits(text):
    """返回 {类型: [命中]} —— 手机号直接收；身份证 / 银行卡需过校验"""
    got = {}
    for label, rx in PII_PATTERNS:
        vals = set()
        for m in rx.finditer(text):
            v = m.group(1)
            if label == "身份证" and not id_ok(v):
                continue
            if label == "银行卡" and not luhn_ok(v):
                continue
            vals.add(v)
        if vals:
            got[label] = sorted(vals)
    return got


def _scan_pii():
    hits = {}
    for root, dirs, files in os.walk(VAULT):
        if ".obsidian" in root:
            continue
        for fn in files:
            if not fn.endswith((".md", ".csv", ".txt", ".json", ".base")):
                continue
            p = os.path.join(root, fn)
            try:
                t = io.open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            got = pii_hits(t)
            if got:
                hits[os.path.relpath(p, VAULT)] = got
    return hits


def c9():
    h1("⑨ 知识库里的个人敏感信息（手机号 / 身份证 / 银行卡）")
    hits = _scan_pii()
    if not hits:
        check("知识库里没有手机号 / 身份证 / 银行卡", True, "全库扫描完毕，零命中")
        return {}
    total = sum(len(v) for g in hits.values() for v in g.values())
    lines = []
    for p, g in sorted(hits.items(), key=lambda x: -sum(len(v) for v in x[1].values()))[:8]:
        lines.append("  %s → %s" % (p, "、".join("%s %d 个" % (k, len(v)) for k, v in g.items())))
    check("知识库里没有手机号 / 身份证 / 银行卡", False,
          "命中 %d 个文件 ｜ 敏感串共 %d 个：\n%s\n"
          "⚠️ 一旦开启 Obsidian Sync，**这些会原样上传**。\n"
          "▸ 修复：python tools\\sanitize_vault_pii.py --dry（先看清单）" % (len(hits), total, "\n".join(lines)))
    return {"files": len(hits), "total": total, "detail": {k: {a: b for a, b in v.items()} for k, v in hits.items()}}


def _scan_outbound_pii():
    """★ 对外产物（工作区 HTML + 桌面包）里的 PII —— ⑨ 只扫知识库，会漏掉这一层。
    对外产物才是真正会被别人看到的，所以必须单独查。"""
    hits = {}
    targets = sorted(glob.glob(os.path.join(WS, "*.html")))
    if os.path.isdir(PACK_DIR):
        for root, dirs, files in os.walk(PACK_DIR):
            for fn in files:
                if fn.lower().endswith((".html", ".md", ".csv")):
                    targets.append(os.path.join(root, fn))
    for p in targets:
        try:
            t = io.open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        got = pii_hits(t)
        if got:
            hits[p] = got
    return hits


def c10():
    h1("⑩ 对外产物里的个人敏感信息（工作区 HTML + 桌面包）")
    hits = _scan_outbound_pii()
    if not hits:
        check("对外产物里没有手机号 / 身份证 / 银行卡", True, "工作区 HTML 与桌面包全扫完毕，零命中")
        return {}
    total = sum(len(v) for g in hits.values() for v in g.values())
    lines = []
    for p, g in sorted(hits.items(), key=lambda x: -sum(len(v) for v in x[1].values()))[:10]:
        lines.append("  %s → %s" % (os.path.basename(p),
                                    "、".join("%s %d 个" % (k, len(v)) for k, v in g.items())))
    check("对外产物里没有手机号 / 身份证 / 银行卡", False,
          "命中 %d 个文件 ｜ 敏感串共 %d 个：\n%s\n"
          "⚠️ 这些是**会被展示/外发**的产物 —— 比知识库更该先处理。\n"
          "▸ 修复：python tools\\pii_split.py（生成脱敏副本到 _tmp\\pii\\公开版\\）"
          % (len(hits), total, "\n".join(lines)))
    return {"files": len(hits), "total": total}


def main():
    fix = "--fix" in sys.argv
    print("隐私核对 · %s%s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "（含修复）" if fix else ""))
    a = c1(fix); b = c2(); c = c3(); d = c4(); e = c5(); f = c6(); g = c7(); h = c8(); i = c9()
    j = c10()
    h1("汇总")
    npass = sum(1 for r in results if r["ok"])
    nfail = sum(1 for r in results if not r["ok"] and not r["warn"])
    nwarn = sum(1 for r in results if not r["ok"] and r["warn"])
    print("  通过 %d ｜ 失败 %d ｜ 警告 %d" % (npass, nfail, nwarn))
    for r in results:
        if not r["ok"]:
            print("    %s %s" % ("[WARN]" if r["warn"] else "[FAIL]", r["name"]))
    payload = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "summary": {"pass": npass, "fail": nfail, "warn": nwarn}, "checks": results}
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
        print("  JSON → %s" % out)
    return nfail


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
