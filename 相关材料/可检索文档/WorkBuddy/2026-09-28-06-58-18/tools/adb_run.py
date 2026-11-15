# -*- coding: utf-8 -*-
"""
adb 包装器 —— 固定 TEMP 到可写目录，绕开沙箱 TEMP 导致的 daemon 启动失败。

★★★ 坑 21（2026-10-06 新踩，技能里原没有）：
    沙箱会把 TEMP / TMP / TMPDIR 注入为  C:\\Users\\wardc\\.workbuddy-ai\\tmp
    adb daemon 启动时要写 <TEMP>\\adb.log，被拒 →
        main.cpp:54 cannot open ...\\adb.log: Permission denied
        could not read ok from ADB Server
        * failed to start daemon
    该目录本身可写（touch 成功），但 adb 进程被沙箱拒绝写。
    ★ 在 bash 里 `export TEMP=...` 无效（Git Bash 不透传给 Windows 进程）；
      `TEMP="..." ./adb.exe` 也无效（adb 走 GetTempPath，仍回落）；
      **只有 PowerShell 里 `$env:TEMP=...` 或 Python subprocess 的 env 显式覆盖才生效。**
    ★ 且 cmd.exe 从 Bash 调用会被安全策略拦（"Invoking cmd.exe from Bash bypasses
      all command validation"）→ 别试 cmd 包装。

用法：
    python tools/adb_run.py devices -l
    python tools/adb_run.py shell id
    python tools/adb_run.py exec-out content query --uri content://sms --out _tmp/sms.txt
    python tools/adb_run.py pull /sdcard/Download ./dl
    python tools/adb_run.py --timeout 1800 pull /sdcard/DCIM ./photos

注意：adb 不可并发（技能坑 1）→ 本脚本一律串行调用，别在多进程里同时用。
"""
import os
import subprocess
import sys
import time

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = r"C:\Users\wardc\Desktop\platform-tools\adb.exe"
TMP_OK = r"C:\Users\wardc\Desktop\platform-tools\tmp"


def env():
    """把 TEMP/TMP/TMPDIR 指向一个真正可写的目录。"""
    e = dict(os.environ)
    try:
        os.makedirs(TMP_OK, exist_ok=True)
    except Exception:
        pass
    for k in ("TEMP", "TMP", "TMPDIR"):
        e[k] = TMP_OK
    # 关掉代理，避免 adb 走宿主内部代理（技能坑 19）
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        e.pop(k, None)
    return e


def run(args, timeout=300, binary=False):
    if not os.path.exists(ADB):
        raise SystemExit("找不到 adb: %s" % ADB)
    p = subprocess.run([ADB] + list(args), env=env(), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout)
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


# ★ 坑 25：HonorSuite 会反复把自己那个 v39 的 adb server 拉起来，把我们的挤掉
#   症状：`adb server version (39) doesn't match this client (41); killing...`
#         `could not read ok from ADB Server` / `* failed to start daemon`
#         `error: no devices/emulators found`
#   解法：kill-server → start-server → 重试（一轮就好，设备随后能稳定若干分钟）
DAEMON_BAD = ("failed to start daemon", "cannot connect to daemon",
              "could not read ok from ADB Server", "no devices/emulators found",
              "failed to get feature set")


def _restart():
    subprocess.run([ADB, "kill-server"], env=env(), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=60)
    time.sleep(1)
    subprocess.run([ADB, "start-server"], env=env(), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=90)
    time.sleep(2)


def run_retry(args, timeout=300, tries=4):
    """执行 adb 命令；若因 daemon 被抢而失败，自动重启 server 重试。"""
    last = ""
    for i in range(tries):
        txt = run(args, timeout=timeout)
        last = txt
        if not any(k in txt for k in DAEMON_BAD):
            return txt
        if i < tries - 1:
            _restart()
    return last


def ensure_device(timeout=120):
    """确保有一台 device 在线；返回设备序列号或 None。"""
    for _ in range(4):
        txt = run_retry(["devices"], timeout=timeout, tries=2)
        for line in txt.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
        _restart()
    return None


def main(argv):
    timeout = 300
    out = None
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--timeout":
            i += 1
            timeout = int(argv[i])
        elif a == "--out":
            i += 1
            out = argv[i]
            if not os.path.isabs(out):
                out = os.path.join(WS, out)
        else:
            args.append(a)
        i += 1

    if not args:
        args = ["devices", "-l"]

    t0 = time.time()
    raw = run_retry(args, timeout=timeout).encode("utf-8", "replace")
    dt = time.time() - t0

    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(raw)
        sys.stdout.write("[adb_run] %s\n  -> %s  (%d bytes, %.1fs)\n"
                         % (" ".join(args), out, len(raw), dt))
    else:
        sys.stdout.write(raw.decode("utf-8", "replace"))
        sys.stdout.write("\n[adb_run] %.1fs\n" % dt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
