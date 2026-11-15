# -*- coding: utf-8 -*-
"""脱离进程树启动 Arduino IDE（供自动化环境使用）。
关键：DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP，并清掉 NODE_OPTIONS。
"""
import os, sys, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")

env = dict(os.environ)
for k in ("NODE_OPTIONS", "ELECTRON_RUN_AS_NODE"):
    env.pop(k, None)

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_BREAKAWAY_FROM_JOB = 0x01000000

flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
try:
    p = subprocess.Popen([EXE], cwd=HERE, env=env,
                         creationflags=flags | CREATE_BREAKAWAY_FROM_JOB,
                         close_fds=True,
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    mode = "breakaway"
except OSError:
    p = subprocess.Popen([EXE], cwd=HERE, env=env,
                         creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    mode = "detached"

print(f"pid={p.pid} mode={mode}")
time.sleep(12)

r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"],
                   capture_output=True, text=True, errors="replace")
alive = "Arduino IDE.exe" in r.stdout
print("ALIVE" if alive else "DEAD")
