# -*- coding: utf-8 -*-
import os, subprocess, time, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")
MARK = r"C:\Users\wardc\Desktop\_tasktest.txt"
TN = "WBDiag_Task"

def run(a):
    return subprocess.run(a, capture_output=True, text=True,
                          errors="replace", encoding="utf-8")

run(["schtasks", "/delete", "/tn", TN, "/f"])
if os.path.exists(MARK):
    os.remove(MARK)

# A) 任务能否执行？跑一个写文件的小命令
r = run(["schtasks", "/create", "/tn", TN,
         "/tr", f'cmd /c echo ok>"{MARK}"',
         "/sc", "once", "/st", "23:59", "/f"])
print("[A create]", r.returncode, (r.stdout or r.stderr).strip()[:120])
r = run(["schtasks", "/run", "/tn", TN])
print("[A run]", r.returncode, (r.stdout or r.stderr).strip()[:120])
time.sleep(6)
print("[A 标记文件存在]", os.path.exists(MARK))
r = run(["schtasks", "/query", "/tn", TN, "/fo", "LIST", "/v"])
for line in r.stdout.splitlines():
    s = line.strip()
    if s.startswith(("Last Run Time", "Last Result", "Status", "Run As User",
                     "Logon Mode", "Task To Run")):
        print("   ", s)
run(["schtasks", "/delete", "/tn", TN, "/f"])

# B) 直接跑 IDE（不经 cmd 包装），看 Last Result
TN2 = "WBDiag_IDE"
run(["schtasks", "/delete", "/tn", TN2, "/f"])
r = run(["schtasks", "/create", "/tn", TN2, "/tr", f'"{EXE}"',
         "/sc", "once", "/st", "23:59", "/f"])
print("[B create]", r.returncode, (r.stdout or r.stderr).strip()[:120])
r = run(["schtasks", "/run", "/tn", TN2])
print("[B run]", r.returncode, (r.stdout or r.stderr).strip()[:120])
time.sleep(12)
r = run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"])
print("[B 进程]", "ALIVE" if "Arduino IDE.exe" in r.stdout else "DEAD")
r = run(["schtasks", "/query", "/tn", TN2, "/fo", "LIST", "/v"])
for line in r.stdout.splitlines():
    s = line.strip()
    if s.startswith(("Last Run Time", "Last Result", "Status")):
        print("   ", s)
run(["schtasks", "/delete", "/tn", TN2, "/f"])
