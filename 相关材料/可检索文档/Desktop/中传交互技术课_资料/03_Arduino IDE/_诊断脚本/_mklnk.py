# -*- coding: utf-8 -*-
"""创建桌面快捷方式（用 UTF-16 BOM 的 VBScript，绕开 cscript 的中文路径编码坑）"""
import os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "Arduino IDE.exe")
LNK = r"C:\Users\wardc\Desktop\Arduino IDE.lnk"

vbs = f'''Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set lnk = ws.CreateShortcut("{LNK}")
lnk.TargetPath = "{EXE}"
lnk.WorkingDirectory = "{HERE}"
lnk.Description = "Arduino IDE 2.3.10"
lnk.IconLocation = "{EXE}, 0"
lnk.Save
WScript.Echo "OK"
'''
p = os.path.join(tempfile.gettempdir(), "mk_arduino_lnk.vbs")
with open(p, "w", encoding="utf-16") as f:
    f.write(vbs)

r = subprocess.run(["cscript", "//nologo", p], capture_output=True, text=True,
                   errors="replace", encoding="utf-8")
print("cscript:", r.returncode, (r.stdout or r.stderr).strip()[:200])
print("快捷方式已创建:", os.path.exists(LNK), "->", LNK)
try:
    os.remove(p)
except OSError:
    pass
