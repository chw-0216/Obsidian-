---
name: iphone-photo-archive
description: 2026-07-17 iPhone 全量照片已备份整理到希捷1T硬盘 D:\iPhone照片整理; mimo API 无视觉能力
metadata: 
  node_type: memory
  type: project
  originSessionId: 6a8c0e4a-f657-4cab-bfa9-f1d16fb7711c
---

2026-07-17 完成 iPhone→希捷 Expansion 1TB (D:) 全量照片备份整理，共 22,051 个文件 / 169 个 MTP 相册文件夹（_raw 原始副本 53GB）。

结构：`D:\iPhone照片整理\{照片|视频|截图|自拍}\年\年-月\日期_时间_地点.ext`，GPS→城市名用 reverse_geocoder 离线反查，无GPS标"无定位"；AAE 编辑文件在 `_编辑数据\`；`_raw\` 为未改名安全副本（确认无误后可删省 53GB）。手机原件未动。

**经验教训：**
- MTP 拷贝用 Shell.Application COM + CopyHere；iPhone 插拔后 COM 句柄失效会无限挂起，且锁定状态下相册枚举返回 0 个文件——脚本必须做锁定探测，空文件夹不可标记完成
- 整理脚本在 scratchpad `organize_photos.py` / `full_run.ps1`（会话结束可能被清理）
- **小米 mimo API (mimo-v2.5-pro) 不支持图片输入**（"No endpoints found that support image input"），语义分类需本地 CLIP 等方案；国内域名要 `--noproxy` 绕过 v2rayN 代理否则超时
- 手机里有 26 个字节级重复文件；整理时已去重

**下一步（2026-07-17 中断待续）：** 用本地 CLIP 做语义分类（用户已同意下载约850MB依赖）。脚本已归档 `Claude工作区\02_脚本与工具\classify_clip.py`：14个分类，先 `index`（生成 _分类索引.csv，可加 limit 试跑）后 `apply`（文件名追加分类词），断点续跑。**PyTorch CPU 版当时未装完**，续做时先 `pip install torch --index-url https://download.pytorch.org/whl/cpu` + `open_clip_torch`；权重走 HF_ENDPOINT=hf-mirror.com（脚本内已设）。先跑 limit=50 给用户看效果再放全量（CPU 预计1-2小时）。

相关：[[clash-verge-setup]] [[claude-code-model-config]] [[seagate-500g-recovery]]
