#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点转订阅 —— 离线把任意常见格式的代理节点/订阅地址转换成 Clash 订阅文档，并自动导入 Clash Verge Rev。
不依赖任何 AI/云端 API，全部本地解析。

用法:
  python 节点转订阅.py "节点地址1" ["节点地址2" ...]      # 转换+导入+实测 全流程
  python 节点转订阅.py --convert-only "节点地址"          # 只生成订阅文档,不动 Clash Verge
  python 节点转订阅.py                                    # 交互模式,逐行粘贴,空行结束
  python 节点转订阅.py 文件.txt                            # 从文本文件读入(每行一个地址)

支持的地址格式:
  IP:端口:用户名:密码 / IP:端口     (自动生成 SOCKS5/HTTP × 直连/经v2rayN前置 候选)
  ss:// vmess:// trojan:// vless:// hysteria2:// hy2:// tuic:// socks5://
  http(s)://订阅链接                (自动下载,base64/明文均可,失败自动改走v2rayN)
  base64 整段订阅内容
"""
import sys, os, re, json, base64, socket, subprocess, time, urllib.request, urllib.parse
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

APPDIR   = os.path.join(os.environ.get("APPDATA", ""), "io.github.clash-verge-rev.clash-verge-rev")
MIHOMO   = r"C:\Program Files\Clash Verge\verge-mihomo.exe"
APPEXE   = r"C:\Program Files\Clash Verge\clash-verge.exe"
UID      = "lclaude0001"
CTRL     = 19091
TESTPORT = 17890
SECRET   = "claude-import-test"
TEST_URL = "http://www.gstatic.com/generate_204"
FRONT    = "前置-v2rayN"
FRONT_PORT = 1099          # v2rayN SOCKS 端口
STATE    = {"interactive": False}
OUTDIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "订阅输出")

# ---------------- 基础工具 ----------------

def b64d(s):
    s = s.strip().replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    return base64.b64decode(s)

def port_open(host, port, ms=1200):
    try:
        with socket.create_connection((host, port), timeout=ms / 1000):
            return True
    except Exception:
        return False

def no_proxy_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))

def yaml_scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def yaml_dump(obj, indent=0):
    """极简 YAML 序列化(仅覆盖 dict/list/标量,足够 Clash proxies 使用)"""
    sp = "  " * indent
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{sp}{k}:")
                out.append(yaml_dump(v, indent + 1))
            else:
                out.append(f"{sp}{k}: {yaml_scalar(v)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                lines = yaml_dump(item, indent + 1).splitlines()
                first = lines[0].strip()
                out.append(f"{sp}- {first}")
                out.extend(lines[1:])
            else:
                out.append(f"{sp}- {yaml_scalar(item)}")
    return "\n".join(out)

# ---------------- 各格式解析器 ----------------

def _hostport(netloc_host, netloc_port, default=443):
    return netloc_host, int(netloc_port or default)

def parse_cred(line):
    """IP:端口:用户名:密码 或 IP:端口 -> SOCKS5/HTTP 两种猜测,标记可加前置链"""
    parts = line.split(":")
    ip, port = parts[0], int(parts[1])
    user = parts[2] if len(parts) == 4 else None
    pw   = parts[3] if len(parts) == 4 else None
    res = []
    for typ, label in (("socks5", "SOCKS5"), ("http", "HTTP")):
        p = {"name": f"{ip}-{label}直连", "type": typ, "server": ip, "port": port}
        if user:
            p["username"] = user
            p["password"] = pw
        if typ == "socks5":
            p["udp"] = True
        p["_chain"] = True
        res.append(p)
    return res

def parse_ss(u):
    body = u[5:]
    name = None
    if "#" in body:
        body, frag = body.split("#", 1)
        name = urllib.parse.unquote(frag)
    plugin_q = ""
    if "@" in body:
        userinfo, hostpart = body.rsplit("@", 1)
        if "?" in hostpart:
            hostpart, plugin_q = hostpart.split("?", 1)
        if "/" in hostpart:
            hostpart = hostpart.split("/", 1)[0]
        try:
            mp = b64d(userinfo).decode("utf-8")
        except Exception:
            mp = urllib.parse.unquote(userinfo)
        method, password = mp.split(":", 1)
        host, port = hostpart.rsplit(":", 1)
    else:
        decoded = b64d(body).decode("utf-8")
        m = re.match(r"(.+?):(.+)@(.+):(\d+)$", decoded)
        if not m:
            raise ValueError("ss 链接格式无法识别")
        method, password, host, port = m.groups()
    host = host.strip("[]")
    p = {"name": name or f"ss-{host}", "type": "ss", "server": host, "port": int(port),
         "cipher": method, "password": password, "udp": True}
    if plugin_q:
        q = dict(urllib.parse.parse_qsl(plugin_q))
        pl = urllib.parse.unquote(q.get("plugin", ""))
        if pl.startswith("obfs") or "simple-obfs" in pl:
            opts = dict(kv.split("=", 1) for kv in pl.split(";")[1:] if "=" in kv)
            p["plugin"] = "obfs"
            p["plugin-opts"] = {"mode": opts.get("obfs", "http")}
            if opts.get("obfs-host"):
                p["plugin-opts"]["host"] = opts["obfs-host"]
        elif pl:
            print(f"  [警告] ss 插件 {pl.split(';')[0]} 暂不支持,已忽略插件参数")
    return [p]

def parse_vmess(u):
    j = json.loads(b64d(u[8:]).decode("utf-8", "replace"))
    p = {"name": j.get("ps") or f"vmess-{j['add']}", "type": "vmess", "server": j["add"],
         "port": int(j["port"]), "uuid": j["id"], "alterId": int(j.get("aid") or 0),
         "cipher": j.get("scy") or "auto", "udp": True}
    net = j.get("net") or "tcp"
    if str(j.get("tls") or "") in ("tls", "true", "1"):
        p["tls"] = True
        sni = j.get("sni") or j.get("host")
        if sni:
            p["servername"] = sni
    if net == "ws":
        p["network"] = "ws"
        p["ws-opts"] = {"path": j.get("path") or "/"}
        if j.get("host"):
            p["ws-opts"]["headers"] = {"Host": j["host"]}
    elif net == "grpc":
        p["network"] = "grpc"
        p["grpc-opts"] = {"grpc-service-name": j.get("path") or ""}
    elif net == "h2":
        p["network"] = "h2"
        p["h2-opts"] = {"path": j.get("path") or "/"}
        if j.get("host"):
            p["h2-opts"]["host"] = [j["host"]]
    return [p]

def parse_trojan(u):
    s = urllib.parse.urlsplit(u)
    q = dict(urllib.parse.parse_qsl(s.query))
    pw = urllib.parse.unquote(s.username or "")
    if s.password:
        pw += ":" + urllib.parse.unquote(s.password)
    p = {"name": urllib.parse.unquote(s.fragment) or f"trojan-{s.hostname}", "type": "trojan",
         "server": s.hostname, "port": s.port or 443, "password": pw, "udp": True}
    if q.get("sni"):
        p["sni"] = q["sni"]
    if q.get("allowInsecure") in ("1", "true"):
        p["skip-cert-verify"] = True
    if q.get("type") == "ws":
        p["network"] = "ws"
        p["ws-opts"] = {"path": q.get("path", "/")}
        if q.get("host"):
            p["ws-opts"]["headers"] = {"Host": q["host"]}
    elif q.get("type") == "grpc":
        p["network"] = "grpc"
        p["grpc-opts"] = {"grpc-service-name": q.get("serviceName", "")}
    return [p]

def parse_vless(u):
    s = urllib.parse.urlsplit(u)
    q = dict(urllib.parse.parse_qsl(s.query))
    p = {"name": urllib.parse.unquote(s.fragment) or f"vless-{s.hostname}", "type": "vless",
         "server": s.hostname, "port": s.port or 443, "uuid": s.username, "udp": True}
    sec = q.get("security", "")
    if sec in ("tls", "reality"):
        p["tls"] = True
    if q.get("sni"):
        p["servername"] = q["sni"]
    if sec == "reality":
        p["reality-opts"] = {"public-key": q.get("pbk", "")}
        if q.get("sid"):
            p["reality-opts"]["short-id"] = q["sid"]
        p["client-fingerprint"] = q.get("fp") or "chrome"
    elif q.get("fp"):
        p["client-fingerprint"] = q["fp"]
    if q.get("flow"):
        p["flow"] = q["flow"]
    net = q.get("type", "tcp")
    if net == "ws":
        p["network"] = "ws"
        p["ws-opts"] = {"path": q.get("path", "/")}
        if q.get("host"):
            p["ws-opts"]["headers"] = {"Host": q["host"]}
    elif net == "grpc":
        p["network"] = "grpc"
        p["grpc-opts"] = {"grpc-service-name": q.get("serviceName", "")}
    return [p]

def parse_hysteria2(u):
    s = urllib.parse.urlsplit(u)
    q = dict(urllib.parse.parse_qsl(s.query))
    pw = urllib.parse.unquote(s.username or "")
    if s.password:
        pw += ":" + urllib.parse.unquote(s.password)
    p = {"name": urllib.parse.unquote(s.fragment) or f"hy2-{s.hostname}", "type": "hysteria2",
         "server": s.hostname, "port": s.port or 443, "password": pw}
    if q.get("sni"):
        p["sni"] = q["sni"]
    if q.get("insecure") in ("1", "true"):
        p["skip-cert-verify"] = True
    if q.get("obfs"):
        p["obfs"] = q["obfs"]
        if q.get("obfs-password"):
            p["obfs-password"] = q["obfs-password"]
    return [p]

def parse_tuic(u):
    s = urllib.parse.urlsplit(u)
    q = dict(urllib.parse.parse_qsl(s.query))
    p = {"name": urllib.parse.unquote(s.fragment) or f"tuic-{s.hostname}", "type": "tuic",
         "server": s.hostname, "port": s.port or 443,
         "uuid": s.username, "password": urllib.parse.unquote(s.password or "")}
    if q.get("sni"):
        p["sni"] = q["sni"]
    if q.get("alpn"):
        p["alpn"] = q["alpn"].split(",")
    if q.get("congestion_control"):
        p["congestion-controller"] = q["congestion_control"]
    if q.get("allow_insecure") in ("1", "true"):
        p["skip-cert-verify"] = True
    return [p]

def parse_proxy_uri(u):
    s = urllib.parse.urlsplit(u)
    typ = "socks5" if s.scheme.startswith("socks") else "http"
    p = {"name": urllib.parse.unquote(s.fragment) or f"{typ}-{s.hostname}", "type": typ,
         "server": s.hostname, "port": s.port or (1080 if typ == "socks5" else 8080)}
    if s.username:
        p["username"] = urllib.parse.unquote(s.username)
        p["password"] = urllib.parse.unquote(s.password or "")
    if typ == "socks5":
        p["udp"] = True
    if s.scheme == "https":
        p["tls"] = True
    p["_chain"] = True
    return [p]

def fetch_subscription(url):
    req = urllib.request.Request(url, headers={"User-Agent": "clash-verge/2.5.1"})
    try:
        text = no_proxy_opener().open(req, timeout=20).read().decode("utf-8", "replace")
        return text
    except Exception as e1:
        if port_open("127.0.0.1", 1100):
            print(f"  直连下载失败({e1}),改走 v2rayN HTTP 代理重试...")
            op = urllib.request.build_opener(urllib.request.ProxyHandler(
                {"http": "http://127.0.0.1:1100", "https": "http://127.0.0.1:1100"}))
            return op.open(req, timeout=30).read().decode("utf-8", "replace")
        raise

CRED_RE = re.compile(r"^\[?[\w.\-:]+\]?:\d{1,5}(:[^:\s]+:[^:\s]+)?$")

def parse_any(line, depth=0):
    """返回 (proxies列表, raw_profile文本或None)"""
    line = line.strip()
    if not line or line.startswith(("#", "//")):
        return [], None
    if line.startswith("ss://"):
        return parse_ss(line), None
    if line.startswith("vmess://"):
        return parse_vmess(line), None
    if line.startswith("trojan://"):
        return parse_trojan(line), None
    if line.startswith("vless://"):
        return parse_vless(line), None
    if line.startswith(("hysteria2://", "hy2://")):
        return parse_hysteria2(line), None
    if line.startswith("tuic://"):
        return parse_tuic(line), None
    if line.startswith(("socks://", "socks5://")) or \
       (line.startswith(("http://", "https://")) and "@" in line.split("?")[0].split("#")[0]):
        return parse_proxy_uri(line), None
    if line.startswith(("http://", "https://")):
        if depth > 2:
            raise ValueError("订阅嵌套过深")
        print(f"  下载订阅: {line[:80]}...")
        text = fetch_subscription(line)
        if "proxies:" in text:
            return [], text          # 已是 Clash YAML 订阅
        try:
            decoded = b64d(text).decode("utf-8", "replace")
            if "://" in decoded:
                text = decoded
        except Exception:
            pass
        proxies = []
        for ln in text.splitlines():
            ps, _ = parse_any(ln, depth + 1)
            proxies.extend(ps)
        return proxies, None
    if CRED_RE.match(line):
        return parse_cred(line), None
    # 最后一搏: 整段可能是 base64 订阅内容
    try:
        decoded = b64d(line).decode("utf-8")
        if "://" in decoded:
            proxies = []
            for ln in decoded.splitlines():
                ps, _ = parse_any(ln, depth + 1)
                proxies.extend(ps)
            if proxies:
                return proxies, None
    except Exception:
        pass
    raise ValueError("无法识别的格式")

# ---------------- mihomo 校验与实测 ----------------

def front_node():
    return {"name": FRONT, "type": "socks5", "server": "127.0.0.1", "port": FRONT_PORT, "udp": True}

def validate_proxy(p, tmpdir):
    """用 mihomo -t 校验单个节点写法是否合法"""
    nodes = [front_node()] if p.get("dialer-proxy") else []
    nodes.append({k: v for k, v in p.items() if not k.startswith("_")})
    cfg = "log-level: silent\nproxies:\n" + yaml_dump(nodes, 0) + "\n"
    f = os.path.join(tmpdir, "validate.yaml")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(cfg)
    r = subprocess.run([MIHOMO, "-t", "-f", f, "-d", tmpdir],
                       capture_output=True, text=True, timeout=30)
    return r.returncode == 0, (r.stdout + r.stderr).strip().splitlines()[-1] if r.returncode else ""

def ctrl_get(path, timeout=12):
    req = urllib.request.Request(f"http://127.0.0.1:{CTRL}{path}",
                                 headers={"Authorization": f"Bearer {SECRET}"})
    return json.loads(no_proxy_opener().open(req, timeout=timeout).read().decode())

def delay_test_all(proxies, tmpdir):
    clean = [{k: v for k, v in p.items() if not k.startswith("_")} for p in proxies]
    has_front = any(p.get("dialer-proxy") for p in proxies)
    all_nodes = ([front_node()] if has_front else []) + clean
    cfg = (f"mixed-port: {TESTPORT}\nmode: rule\nlog-level: warning\n"
           f"external-controller: 127.0.0.1:{CTRL}\nsecret: {SECRET}\n"
           "proxies:\n" + yaml_dump(all_nodes, 0) + "\n"
           "proxy-groups:\n  - name: TESTGROUP\n    type: select\n    proxies:\n"
           + "\n".join(f'      - "{p["name"]}"' for p in clean)
           + "\nrules:\n  - MATCH,TESTGROUP\n")
    f = os.path.join(tmpdir, "delaytest.yaml")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(cfg)
    proc = subprocess.Popen([MIHOMO, "-f", f, "-d", tmpdir],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        up = False
        for _ in range(24):
            try:
                ctrl_get("/version", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(0.5)
        if not up:
            print("  [错误] 临时内核启动失败,跳过实测")
            return {}
        delays = {}
        enc_url = urllib.parse.quote(TEST_URL, safe="")
        for p in proxies:
            name = p["name"]
            try:
                r = ctrl_get(f"/proxies/{urllib.parse.quote(name)}/delay?timeout=6000&url={enc_url}")
                delays[name] = int(r.get("delay", -1))
                print(f"  [通] {name}  {delays[name]}ms")
            except Exception:
                delays[name] = -1
                print(f"  [不通] {name}")
        return delays
    finally:
        proc.terminate()

# ---------------- 写入 Clash Verge ----------------

def build_profile(proxies, order_names):
    clean = [{k: v for k, v in p.items() if not k.startswith("_")} for p in proxies]
    has_front = any(p.get("dialer-proxy") for p in proxies)
    all_nodes = ([front_node()] if has_front else []) + clean
    y = (f"# 由 节点转订阅.py 于 {datetime.now():%Y-%m-%d %H:%M} 生成(离线转换,无AI)\n"
         "proxies:\n" + yaml_dump(all_nodes, 0) + "\n"
         'proxy-groups:\n  - name: "选择节点"\n    type: select\n    proxies:\n'
         + "\n".join(f'      - "{n}"' for n in order_names)
         + "\n      - DIRECT\n"
         "rules:\n  - GEOIP,CN,DIRECT\n  - MATCH,选择节点\n")
    return y

def install_profile(profile_text):
    os.makedirs(os.path.join(APPDIR, "profiles"), exist_ok=True)
    with open(os.path.join(APPDIR, "profiles", f"{UID}.yaml"), "w", encoding="utf-8") as f:
        f.write(profile_text)
    idx = os.path.join(APPDIR, "profiles.yaml")
    ts = int(time.time())
    item = (f"- uid: {UID}\n  type: local\n  name: Claude导入-节点转订阅\n"
            f"  file: {UID}.yaml\n  desc: 节点转订阅.py 自动生成\n  updated: {ts}")
    if os.path.exists(idx):
        txt = open(idx, encoding="utf-8").read()
        if f"uid: {UID}" not in txt:
            if re.search(r"(?m)^items:\s*(null)?\s*$", txt):
                txt = re.sub(r"(?m)^items:\s*(null)?\s*$", "items:\n" + item, txt, count=1)
            else:
                txt = re.sub(r"(?m)^items:", "items:\n" + item, txt, count=1)
        if re.search(r"(?m)^current:", txt):
            txt = re.sub(r"(?m)^current:.*$", f"current: {UID}", txt, count=1)
        else:
            txt = f"current: {UID}\n" + txt
    else:
        txt = f"# Profiles Config for Clash Verge\n\ncurrent: {UID}\nitems:\n{item}\n"
    with open(idx, "w", encoding="utf-8") as f:
        f.write(txt)

def restart_verge():
    for exe in ("clash-verge.exe", "verge-mihomo.exe"):
        subprocess.run(["taskkill", "/IM", exe, "/F"], capture_output=True)
    time.sleep(2)
    os.startfile(APPEXE)

def e2e_check():
    op = urllib.request.build_opener(urllib.request.ProxyHandler(
        {"http": f"http://127.0.0.1:7897", "https": f"http://127.0.0.1:7897"}))
    try:
        return op.open("https://api.ipify.org", timeout=25).read().decode().strip()
    except Exception:
        return None

# ---------------- 主流程 ----------------

def main():
    args = [a for a in sys.argv[1:]]
    convert_only = "--convert-only" in args
    no_test = "--no-test" in args
    inputs = [a for a in args if not a.startswith("--")]

    if len(inputs) == 1 and os.path.isfile(inputs[0]):
        inputs = [ln for ln in open(inputs[0], encoding="utf-8-sig").read().splitlines() if ln.strip()]
    if not inputs:
        STATE["interactive"] = True
        print("粘贴节点地址(每行一个,支持 ss/vmess/trojan/vless/hy2/tuic/订阅链接/IP:端口:用户:密码)")
        print("粘贴完成后,在空行上按回车开始转换:")
        while True:
            try:
                ln = input()
            except EOFError:
                break
            ln = ln.strip().strip('"').strip("'").strip()
            if not ln:
                if inputs:
                    break      # 已有内容,空行=开始转换
                continue       # 开头的空行(粘贴自带的换行)直接忽略
            inputs.append(ln)
    if not inputs:
        print("没有输入,退出。")
        return 1

    # 1. 解析
    proxies, raw_profile = [], None
    for item in inputs:
        try:
            ps, raw = parse_any(item)
            if raw:
                raw_profile = raw
                print(f"  [OK] 识别为完整 Clash 订阅文档")
            for p in ps:
                print(f"  [OK] {p['type']}: {p['name']}")
            proxies.extend(ps)
        except Exception as e:
            print(f"  [失败] {item[:60]} -> {e}")
    # 名称去重
    seen = {}
    for p in proxies:
        if p["name"] in seen:
            seen[p["name"]] += 1
            p["name"] = f"{p['name']}-{seen[p['name']]}"
        else:
            seen[p["name"]] = 1

    # 2. 为可链式节点生成"经v2rayN前置"变体
    if proxies and port_open("127.0.0.1", FRONT_PORT):
        extra = []
        for p in [x for x in proxies if x.get("_chain")]:
            c = dict(p)
            c["name"] = p["name"].replace("直连", "") + "经前置"
            c["dialer-proxy"] = FRONT
            c.pop("_chain", None)
            extra.append(c)
        if extra:
            print(f"  检测到 v2rayN({FRONT_PORT}),追加 {len(extra)} 个'经前置'候选(应对封中国IP的服务商)")
            proxies.extend(extra)

    if not proxies and not raw_profile:
        print("没有解析出任何节点,退出。")
        return 1

    os.makedirs(OUTDIR, exist_ok=True)
    tmpdir = os.path.join(os.environ.get("TEMP", "."), "node2sub-test")
    os.makedirs(tmpdir, exist_ok=True)

    if raw_profile:
        if proxies:
            print("  [警告] 同时给了订阅文档和散装节点,本次只处理订阅文档")
        profile_text = raw_profile
        order = []
    else:
        # 3. 逐个校验写法
        ok_proxies = []
        for p in proxies:
            valid, err = validate_proxy(p, tmpdir)
            if valid:
                ok_proxies.append(p)
            else:
                print(f"  [剔除] {p['name']} 配置不合法: {err}")
        if not ok_proxies:
            print("所有节点都未通过 mihomo 校验,退出。")
            return 1
        proxies = ok_proxies

        # 4. 实测延迟排序
        order = [p["name"] for p in proxies]
        if not no_test:
            print(f"启动临时内核实测 {len(proxies)} 个节点...")
            delays = delay_test_all(proxies, tmpdir)
            winners = sorted([n for n in order if delays.get(n, -1) > 0], key=lambda n: delays[n])
            losers  = [n for n in order if delays.get(n, -1) <= 0]
            order = winners + losers
            print(f"实测结果: {len(winners)}/{len(order)} 可用" + (f", 最快: {winners[0]}" if winners else ""))
        profile_text = build_profile(proxies, order)

    # 5. 保存订阅文档
    out = os.path.join(OUTDIR, f"订阅-{datetime.now():%Y%m%d-%H%M%S}.yaml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(profile_text)
    print(f"订阅文档已保存: {out}")
    if convert_only:
        print("(--convert-only 模式,未写入 Clash Verge)")
        return 0

    # 6. 写入 Clash Verge 并重启验证
    print("写入 Clash Verge 并重启...")
    install_profile(profile_text)
    restart_verge()
    time.sleep(8)
    ip = e2e_check()
    if ip:
        print(f"=== 全部完成 === 经 Clash(7897) 出口 IP: {ip}")
        print("如需全局上网,请在 Clash Verge 主页打开「系统代理」。")
    else:
        print("配置已写入,但经 7897 端口验证未通(节点可能都不可用),请打开 Clash Verge「代理」页手动检查。")
    return 0

if __name__ == "__main__":
    code = 1
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n已取消")
        code = 130
    except Exception:
        import traceback
        traceback.print_exc()
    if STATE["interactive"]:
        try:
            input("\n按回车键关闭窗口...")
        except Exception:
            pass
    sys.exit(code)
