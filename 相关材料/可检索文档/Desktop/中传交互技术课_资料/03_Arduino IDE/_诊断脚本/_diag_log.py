# -*- coding: utf-8 -*-
import os, subprocess, time, winreg

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")
LOG = os.path.join(HERE, "_ide_boot.log")
TN = "WBDiag_Log"

def run(a, **kw):
    return subprocess.run(a, capture_output=True, text=True,
                          errors="replace", encoding="utf-8", **kw)

print("=== 1) 环境变量里有没有 NODE_OPTIONS / ELECTRON_RUN_AS_NODE ===")
for hive, path, tag in [
    (winreg.HKEY_CURRENT_USER, r"Environment", "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "HKLM"),
]:
    try:
        k = winreg.OpenKey(hive, path)
        i = 0
        found = False
        while True:
            try:
                n, v, _ = winreg.EnumValue(k, i); i += 1
            except OSError:
                break
            if n.upper() in ("NODE_OPTIONS", "ELECTRON_RUN_AS_NODE"):
                print(f"  !! {tag}: {n} = {v}")
                found = True
        if not found:
            print(f"  {tag}: 无（干净）")
    except OSError as e:
        print(f"  {tag}: 打不开 {e}")

print("\n=== 2) 计划任务 + 清 NODE_OPTIONS + 抓日志 启动 IDE ===")
if os.path.exists(LOG):
    os.remove(LOG)
inner = f'cd /d "{HERE}" && set NODE_OPTIONS= && set ELECTRON_RUN_AS_NODE= && "{EXE}" > "{LOG}" 2>&1'
run(["schtasks", "/delete", "/tn", TN, "/f"])
r = run(["schtasks", "/create", "/tn", TN, "/tr", f'cmd /c {inner}',
         "/sc", "once", "/st", "23:59", "/f"])
print("[create]", r.returncode)
r = run(["schtasks", "/run", "/tn", TN])
print("[run]", r.returncode)
time.sleep(14)

r = run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"])
print("[进程]", "ALIVE" if "Arduino IDE.exe" in r.stdout else "DEAD")
r = run(["schtasks", "/query", "/tn", TN, "/fo", "LIST", "/v"])
for line in r.stdout.splitlines():
    s = line.strip()
    if s.startswith(("Last Result", "Last Run Time")):
        print("   ", s)

print("\n=== 3) 启动日志 ===")
if os.path.exists(LOG):
    txt = open(LOG, encoding="utf-8", errors="replace").read()
    print(txt[:2500] if txt.strip() else "(空)")
else:
    print("(日志文件未生成)")

print("\n=== 4) 对照：同一任务机制跑非 GUI 长命令 ===")
TN2 = "WBDiag_NonGUI"
run(["schtasks", "/delete", "/tn", TN2, "/f"])
r = run(["schtasks", "/create", "/tn", TN2, "/tr", "cmd /c ping -n 20 127.0.0.1",
         "/sc", "once", "/st", "23:59", "/f"])
run(["schtasks", "/run", "/tn", TN2])
time.sleep(8)
r = run(["tasklist", "/FI", "IMAGENAME eq PING.EXE"])
print("[非GUI长命令 8s后]", "ALIVE" if "PING.EXE" in r.stdout else "DEAD(说明任务树被回收)")
run(["schtasks", "/delete", "/tn", TN2, "/f"])
run(["schtasks", "/delete", "/tn", TN, "/f"])
