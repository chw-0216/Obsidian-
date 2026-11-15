# -*- coding: utf-8 -*-
import os, subprocess, time, ctypes

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")

def run(a, **kw):
    return subprocess.run(a, capture_output=True, text=True,
                          errors="replace", encoding="utf-8", **kw)

def alive():
    r = run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"])
    return "Arduino IDE.exe" in r.stdout

print("=== A) ShellExecuteW（等价于资源管理器里双击）===")
try:
    r = ctypes.windll.shell32.ShellExecuteW(None, "open", EXE, None, HERE, 1)
    print("   ShellExecute 返回:", r, "(>32 = 成功)")
except Exception as e:
    print("   失败:", e)
time.sleep(18)
print("   ", "ALIVE" if alive() else "DEAD")

if not alive():
    print("\n=== B) VBScript WshShell.Run（真正异步独立启动）===")
    vbs = os.path.join(HERE, "_run.vbs")
    with open(vbs, "w", encoding="gbk") as f:
        f.write('Set ws = CreateObject("WScript.Shell")\r\n')
        f.write(f'ws.CurrentDirectory = "{HERE}"\r\n')
        f.write(f'ws.Run """{EXE}""", 1, False\r\n')
    r = run(["cscript", "//nologo", vbs])
    print("   cscript:", r.returncode, (r.stdout or r.stderr).strip()[:200])
    time.sleep(18)
    print("   ", "ALIVE" if alive() else "DEAD")

print("\n=== C) 带日志诊断（拿崩溃原因）===")
env = dict(os.environ)
env.pop("NODE_OPTIONS", None)
env.pop("ELECTRON_RUN_AS_NODE", None)
env["ELECTRON_ENABLE_LOGGING"] = "1"
log = os.path.join(HERE, "_boot2.log")
try:
    p = subprocess.run([EXE, "--log-level", "debug"], cwd=HERE, env=env,
                       capture_output=True, text=True, errors="replace",
                       timeout=30)
    print("   exit:", p.returncode)
    out = (p.stdout or "") + (p.stderr or "")
    print("   输出:", out[:1500] if out.strip() else "(空)")
except subprocess.TimeoutExpired as e:
    print("   timeout(说明进程持续运行)")
    out = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""))
    print("   输出:", out[:1500] if out.strip() else "(空)")

print("\n=== 配置目录 ===")
for d in [r"C:\Users\wardc\AppData\Roaming\Arduino IDE",
          r"C:\Users\wardc\AppData\Local\Arduino15",
          r"C:\Users\wardc\Documents\Arduino"]:
    print(f"  {'OK ' if os.path.isdir(d) else 'NO '} {d}")
