---
name: machine-health-g15
description: "User's Dell G15 5520 laptop — known hardware/stability issues and maintenance history"
metadata: 
  node_type: memory
  type: project
  originSessionId: 65140ce9-17ec-4f88-8d7e-58b493c9bb09
---

User's PC is a **Dell G15 5520** (i7-12700H, RTX 3050 Laptop + Intel Iris Xe, 16GB RAM, 512GB SK hynix NVMe SSD, Win11 22H2 build 22621).

Known issues (as of 2026-06-25):
- **Recurring NVIDIA GPU BSODs**: bugcheck 0x113 (VIDEO_DXGKRNL_FATAL_ERROR, param 0x10de = NVIDIA), 5 crashes in one month (6/1, 6/3, 6/6, 6/20, 6/21) + nvlddmkm event 153. Attempted fix: clean-installed NVIDIA driver **581.95 → 610.62** (WHQL, 2026-06-11). **If BSODs recur after this, suspect GPU hardware (overheating/solder) → underclock or RMA.**
- **Battery health ~49.7%** (design 54,891 mWh, full charge only 27,292 mWh) — significantly worn, consider replacement if mobility needed. Usually on AC.
- **Windows not updated since 2024-10** — not policy-blocked, just never run. Recommend running Windows Update.

Maintenance done 2026-06-25 (see also [[user-profile]]):
- Removed bloat: TeamViewer, ToDesk, 向日葵, WIN电脑助手, Wondershare, 迅雷, 数据蛙录屏.
- **Removed 360 全家桶** (卫士 + 浏览器 + 清理Pro) — required Safe Mode + killing self-protecting drivers Q360AMPPL/360reskit64. **Windows Defender restored as the AV.** User dislikes 360.
- Freed ~30GB on C: (WPS/剪映/Claude/Adobe caches, Temp, DISM component cleanup).
- SFC found & repaired corrupted system files.

Maintenance done 2026-06-30 (archive/compression cleanup → 正版合规):
- Uninstalled 搜狗压缩 (`压缩` by Sogou, kzip_sogou) and old vulnerable **WinRAR 5.40**.
- Purged **GoodZip** leftovers — the orphaned association tail of "WIN电脑助手"/WinAssist (removed 6/25): program files already gone, but 142 dead GoodZip.* ProgIds in HKCU\Software\Classes still hijacked 35 archive extensions. Re-pointed all to WinRAR, cleared stale FileExts UserChoice keys, deleted the dead ProgIds.
- Installed **WinRAR 7.22 official SC** (winget RARLab.WinRAR, `winrar-x64-722sc.exe`, genuine non-cracked). Noted to user: free version is perpetual-trial (nag screen); buy personal license for full compliance.
- All GoodZip residue = 0; HKLM Classes was clean (Windows built-ins).
- Installed **SumatraPDF** (winget, open-source) as the intended PDF default. NOTE: `.pdf` UserChoice is still `KWPS.PDF.9` (WPS) — Win11's kernel-level UserChoice hash protection blocked programmatic override even with owner+FullControl on the key; Settings-UI route was hampered by screenshot masking. Left the final flip to the user via right-click → 打开方式 → 选择其他应用 → SumatraPDF → 始终. HKCU\Software\Classes\.pdf already points to SumatraPDF.pdf. **Verify UserChoice = SumatraPDF.pdf next session.**
- Decided NOT to install 7-Zip: WinRAR 7.22 covers compress+decompress; one tool avoids association fights.
- Cleaned 360 leftovers (from 6/25 uninstall): removed orphan RegisteredApplications entries 360zip (HKLM), 360Chrome + 360ChromeX (HKCU) — all pointed to non-existent Capabilities keys and made "360安全浏览器" show in Settings; deleted residual C:\Users\wardc\AppData\Local\360Chrome (13MB browser leftover).
- Trimmed startup: disabled scheduled tasks WpsUpdateLogonTask_wardc + NvNodeLauncher (GeForce Experience); removed HKCU Run\Weixin (微信 -autorun). Kept ctfmon/SecurityHealth/Realtek/iGoAudio (system), AdsPower + CodeMeter (user's work tools). No new bundleware found — machine clean post-6/25.
