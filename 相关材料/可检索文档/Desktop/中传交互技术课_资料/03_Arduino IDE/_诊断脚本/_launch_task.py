# -*- coding: utf-8 -*-
"""通过 Windows 计划任务启动 Arduino IDE —— 任务由 Task Scheduler 服务拉起，
完全脱离当前 shell 的进程树/job object，因此不会被回收。"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CMD = os.path.join(HERE, "启动Arduino.cmd")
TN = "ArduinoIDE_Launch"

def run(args):
    return subprocess.run(args, capture_output=True, text=True,
                          errors="replace", encoding="utf-8")

# 1) 清掉同名旧任务
run(["schtasks", "/delete", "/tn", TN, "/f"])

# 2) 建一次性任务（时间设当天 23:59，仅作占位，随后手动 /run）
r = run(["schtasks", "/create", "/tn", TN, "/tr", f'"{CMD}"',
         "/sc", "once", "/st", "23:59", "/f"])
print("[create]", r.returncode, (r.stdout or r.stderr).strip()[:200])
if r.returncode != 0:
    sys.exit(1)

# 3) 立即运行
r = run(["schtasks", "/run", "/tn", TN])
print("[run]", r.returncode, (r.stdout or r.stderr).strip()[:200])

time.sleep(15)

# 4) 检查进程
r = run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"])
alive = "Arduino IDE.exe" in r.stdout
print("ALIVE" if alive else "DEAD")
if alive:
    for line in r.stdout.splitlines():
        if "Arduino" in line:
            print("  ", line.strip())

# 5) 清理任务
run(["schtasks", "/delete", "/tn", TN, "/f"])
