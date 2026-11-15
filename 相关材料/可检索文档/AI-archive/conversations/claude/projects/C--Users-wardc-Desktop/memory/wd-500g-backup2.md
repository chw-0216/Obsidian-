---
name: wd-500g-backup2
description: "WD5000AAKX 500GB via USB — user's second backup drive \"BACKUP2\", SMART baseline 2026-07-13"
metadata: 
  node_type: memory
  type: project
  originSessionId: 51988418-9805-44ef-bca8-00f36cc9cab5
---

User's second backup drive: WDC WD5000AAKX-00ERMA0 (WD Blue CMR 500GB, ~2011-13 era, S/N WD-WMC2E4569985), connected via the same JMicron USB dock as the Seagate in [[seagate-500g-recovery]] (only one drive fits at a time — they share the dock and the D: letter). On 2026-07-13 it arrived as MBR/exFAT label "系统", verified empty, then wiped → GPT → NTFS, label **BACKUP2**, D:, with folders 照片/文档/其他.

SMART baseline 2026-07-13 (counters genuine, not reset): PASSED; Power_On_Hours=5004, Power_Cycle_Count=1908, Reallocated=0, Pending=0, Offline_Uncorrectable=0, CRC=0, no error log, temp 29°C. Healthier and more trustworthy history than the Seagate. Extended self-test started 22:02, expected done ~23:28 same day — result not yet checked.

Check SMART with: `smartctl -a -d usbjmicron /dev/sdb` (needs admin elevation; smartctl 7.5 at C:\Program Files\smartmontools\bin). Retire the drive if 05/197/198 ever grow past 0.
