# -*- coding: utf-8 -*-
r"""
usb_present.py —— 用 SetupAPI 枚举「当前在场」的设备实例 ID（不依赖 WMIC / PowerShell）

背景：本机 WMIC 被安全策略拉黑、PowerShell 工具输出通道不可用、Shell.Application COM 被拦。
所以用 ctypes 直调 cfgmgr32 的 CM_Get_Device_ID_ListW 拿在场设备列表。

用法：
  python tools\usb_present.py                 # 列出含 339B / ADB / MTP 的设备
  python tools\usb_present.py --all           # 全量在场设备（很长）
  python tools\usb_present.py --grep 339B,ADB
"""
import sys, ctypes, argparse
from ctypes import wintypes

cfgmgr32 = ctypes.WinDLL("cfgmgr32")

CM_GETIDLIST_FILTER_PRESENT = 0x00000100
CM_GETIDLIST_FILTER_ENUMERATOR = 0x00000001

def enum_present():
    flags = CM_GETIDLIST_FILTER_PRESENT
    size = wintypes.ULONG(0)
    r = cfgmgr32.CM_Get_Device_ID_List_SizeW(ctypes.byref(size), None, flags)
    if r != 0:
        raise OSError("CM_Get_Device_ID_List_SizeW rc=%d" % r)
    buf = ctypes.create_unicode_buffer(size.value)
    r = cfgmgr32.CM_Get_Device_ID_ListW(None, buf, size.value, flags)
    if r != 0:
        raise OSError("CM_Get_Device_ID_ListW rc=%d" % r)
    return [x for x in buf[:].split("\x00") if x]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--grep", default="339B,ADB,18D1,MTP,WPD,BRP")
    a = ap.parse_args()
    ids = enum_present()
    print("在场设备总数: %d" % len(ids))
    if a.all:
        for i in ids:
            print(" ", i)
        return
    kws = [k.strip().lower() for k in a.grep.split(",") if k.strip()]
    hit = [i for i in ids if any(k in i.lower() for k in kws)]
    print("命中 %d 条：" % len(hit))
    for i in hit:
        print(" ", i)
    # 按 VID 汇总
    from collections import Counter
    c = Counter()
    for i in ids:
        if i.upper().startswith("USB\\"):
            parts = i.split("\\")
            c[parts[1] if len(parts) > 1 else i] += 1
    print("\nUSB 枚举器分组（在场）:")
    for k, v in c.most_common(40):
        print("  %4d  %s" % (v, k))

if __name__ == "__main__":
    main()
