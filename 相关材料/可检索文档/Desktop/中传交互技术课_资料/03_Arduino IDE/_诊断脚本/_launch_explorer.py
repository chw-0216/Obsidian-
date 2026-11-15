# -*- coding: utf-8 -*-
import os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")

def run(a):
    return subprocess.run(a, capture_output=True, text=True,
                          errors="replace", encoding="utf-8")

def alive():
    r = run(["tasklist", "/FI", "IMAGENAME eq Arduino IDE.exe"])
    return "Arduino IDE.exe" in r.stdout

print("=== 方式1: explorer.exe 拉起（借用用户交互会话）===")
subprocess.Popen(["explorer.exe", EXE], close_fds=True)
time.sleep(18)
print("  ", "ALIVE" if alive() else "DEAD")

if not alive():
    print("=== 方式2: 通过 explorer 打开目录（等同用户双击文件夹）===")
    subprocess.Popen(["explorer.exe", HERE], close_fds=True)
    time.sleep(5)
    print("  已打开文件夹，等待用户双击")

# 检查是否生成了 IDE 配置目录（启动成功的硬证据）
print("\n=== 配置目录生成情况 ===")
for d in [r"C:\Users\wardc\AppData\Roaming\Arduino IDE",
          r"C:\Users\wardc\AppData\Local\Arduino15",
          r"C:\Users\wardc\Documents\Arduino"]:
    print(f"  {'✅' if os.path.isdir(d) else '❌'} {d}")
