# Hyper3D / Rodin 全流程交接文档

**撰写日期：** 2026-09-24
**交接范围：** Hyper3D 生成的全链路（登录 → 生成 → 分件 → 体检 → 组装 → 展示 → 打印导出）
**验证状态：** 本文档所有命令、参数与数字均为**本机实测**，非推测。凡未实测的能力已明确标注。

---

## 0. 三十秒速览

| 项 | 值 |
| --- | --- |
| 可用入口 | `@hyper3d/cli@0.2.0`（已登录）· MCP（Codex 侧已配置）· 官方 HTTP API（**未开通**） |
| CLI 路径 | `C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd` |
| 账号 | 蔡浩文（uuid `66f6416a-6b20-4dd7-9623-ed4d9452d0a4`），personal 工作区 |
| 当前额度 | `subscription_balance` **4967** · `balance` 15 · `frozen` 0 |
| 累计消耗 | **16 次生成 = 8.0 额度**（起始 4979） |
| 单价 | generate **0.5 额度/次**、bang **0.5 额度/次** |
| 单项耗时 | generate 68–126 秒 · bang 122–177 秒（含下载） |
| 单次产出 | **始终 2 份 GLB**：`base_basic_pbr.glb`（3 贴图）+ `base_basic_shaded.glb`（1 贴图） |
| 核心限制 | 无骨骼、无动画、无表情、无口型、无 seed（CLI 侧）· 生成物不含场景/光照/相机 |
| 本机瓶颈 | 内存仅约 1.2 GB 可用 · EEVEE 渲染 36.8 秒/帧（480×480）→ **不能做视频渲染** |

---

## 1. 环境与凭据

### 1.1 已装组件（实测）

| 组件 | 版本/路径 | 状态 |
| --- | --- | --- |
| Hyper3D CLI | `@hyper3d/cli@0.2.0` | ✅ 已登录 |
| 凭据文件 | `C:\Users\wardc\.hyper3d\d3aa2860….json` | ✅ 含 `access_token`/`refresh_token`/`expiresAt`，**自动刷新** |
| Blender | `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`（5.1.2） | ✅ headless 可用，**不在 PATH** |
| ffmpeg | `…\AI-archive\apps\FFmpeg\package\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe` | ✅ `libx264`/`libx265`/`prores`/`png` |
| Node.js | v24.18.0 | ✅ 所有 `.cjs` 脚本纯 Node、无第三方依赖 |
| model-viewer | 项目内 `@google/model-viewer@4.3.1` | ✅ 本地加载，不依赖 CDN |

**注意：`hyper3d` 与 `blender` 都不在 PATH 上**，脚本里一律用完整路径。

### 1.2 凭据边界

- CLI 登录与 Codex MCP OAuth 是**两套独立凭据**，各自授权、各自失效。
- **直连官方 HTTP API 需要单独的 Bearer key**（在 Hyper3D API Dashboard 申请），CLI 的 OAuth 不通用。**目前未开通**，因此材质生成、姿态约束、视图标签、seed 等 API 专属能力当前均不可用。
- 凭据文件不要复制进项目或对话。项目内任何文件都不含 token。

### 1.3 登录（如需重来）

```powershell
$cli = "C:\Users\wardc\Documents\New project gpt\AI-archive\apps\hyper3d-cli\hyper3d.cmd"
& $cli auth login --no-browser     # 打印链接与码，在浏览器完成授权
& $cli auth status --output json    # 核对账号与额度
```

设备码有效期约 10 分钟。会话内可挂后台看守脚本自动等待（见 `hyper3d-login-watch.ps1`）。

---

## 2. CLI 命令全表（全部已实测）

| 命令 | 作用 | 计费 | 实测结果 |
| --- | --- | --- | --- |
| `auth login [--no-browser]` | 设备码授权 | 否 | ✅ 成功，凭据落 `~/.hyper3d` |
| `auth status\|info` | 账号与额度 | 否 | ✅ 返回 uuid/username/wallet |
| `auth logout` | 清除本机凭据 | 否 | 未测（不必要） |
| `generate` | 生成模型 | **是 0.5** | ✅ 16 次全部成功 |
| `status <id>` | 查一次状态 | 否 | ✅ `pack 5/5`；伪造 ID 报 `Generation was not found`（exit 1） |
| `poll <id> --timeout N` | 轮询到终态 | 否 | ✅ 每项都返回 `timed_out:false` |
| `result <id>` | 取下载链接 | 否 | ✅ **幂等**，重复调用返回同一签名，**不计费** |
| `bang <id>` | 分件 | **是 0.5** | ✅ 2 次，语义拆 8 件 / 自动拆 2 件 |
| `update [--check]` | 升级 CLI | 否 | ✅ `Current 0.2.0 / Target 0.2.0 / Available No` |

全局选项：`--output human|json`、`--base-url <url>`、`-h`、`-V`。

### 2.1 `generate` 参数（实测语义）

| 选项 | 取值 | 默认 | 实测结论 |
| --- | --- | --- | --- |
| `--prompt` | 文本 | — | 可与 `--image` 并用；**单独使用即纯文本生成**（已验证） |
| `--image` | 路径，可重复 1–5 次 | — | **多视图拼版会导致"合面"缺陷，务必用单人单图** |
| `--tier` | `Gen-2.5-Medium` / `Gen-2.5-High` / `Gen-2.5-Extreme-Low` | Medium | 仅三档，无 `Low`/`Extreme-High` |
| `--mesh-mode` | `Raw` / `Quad` | Raw | **见 2.2，Quad 名不副实** |
| `--quality` | Raw `500–1,000,000`；Quad `1,000–50,000` | Raw 500000 / Quad 18000 | **Raw=目标三角面数，精确命中** |
| `--format` | `glb`/`usdz`/`fbx`/`obj`/`stl` | glb | 未逐格式实测 |
| `--texture-delight` | 开关 | false | 未测（高反光参考图去光照用） |

### 2.2 两条最重要的参数结论

**① `--quality` 在 Raw 模式下精确等于目标三角面数**（6 项实测全部命中，误差为零）：

| 目标 | 实得三角面 | 索引 | 顶点 |
| --- | --- | --- | --- |
| 40,000 | **40,000** | 120,000 | 40,980 |
| 100,000 | **100,000** | 300,000 | 87,739 / 105,095（High 档） |
| 300,000 | **300,000** | 900,000 | 222,124 |
| 500,000 | **500,000** | 1,500,000 | 316,317 |

索引数恒为三角面数的 3 倍。**不要按索引数设值。**

**② `--mesh-mode Quad` 名不副实——交付的是三角网格，且面数约为目标的 1.8 倍：**

| 目标 | 实得三角面 | 倍数 | 顶点 |
| --- | --- | --- | --- |
| 6,000 | 11,245 | 1.87× | 6,279 |
| 12,000 | 21,060 | 1.76× | 11,400 |
| 30,000 | 54,640 | 1.82× | 30,086 |
| 50,000 | 89,062 | 1.78× | 47,574 |

决定性证据是**顶点价数分析**（每个顶点连几条边）：

| 文件 | 内部顶点价数均值 | 4 价占比 | 6 价占比 |
| --- | --- | --- | --- |
| raw-40k | 6.004 | 8.2% | 34.2% |
| raw-100k | 6.000 | 7.3% | 35.0% |
| **quad-12k** | **5.999** | **7.8%** | 26.9% |

若 `Quad` 真产出四边形网格，三角化后内部顶点应以 **4 价**为主。实测仅 7.8%，与 Raw 无差别 → **两种模式都仍需重拓扑才能绑定**。Quad 的唯一价值是用更少三角面换更紧凑形体。

---

## 3. 全部生成任务记录（16 次，8.0 额度）

### 3.1 前期（4 次生成 + 2 次分件 = 4.0 额度）

| 用途 | 参数 | generation_id |
| --- | --- | --- |
| 参数扫描 A | Medium / Raw / 500k | `76079c6a-1bd3-4282-9546-b9a445545eb4` |
| 参数扫描 B | Medium / Quad / 18k | `90b6c33b-2963-4b47-b630-698ff3a851fa` |
| 参数扫描 C | Medium / Quad / 50k | `d32591d4-9dec-44d9-9b6d-f9f53db65456` |
| 参数扫描 D | High / Raw / 500k | `1832542d-ac07-4957-83f3-7c6a30e2813c` |
| 参数扫描 E | Medium / Raw / 100k | `60396154-9a18-49c2-aa45-37962fba2345` |
| 单人绑定底模 | Medium / Raw / 100k | `cd20c16e-1bd8-47ab-8463-e7a72214ef04` |
| BANG 语义分件 | strength 5 + instruction → **8 件** | `fe8a565b-9810-4e8c-b242-5a429e155298` |
| BANG 自动分件 | strength 5，无 instruction → **2 件** | `065bf3f9-23b5-48a9-b098-7e8536de1f9e` |

> ⚠️ 参数扫描 A–E **全部使用三视图拼版**，带"三面合一"缺陷，仅参数结论有效，产物不可用。

### 3.2 角色资产矩阵（8 次 = 4.0 额度，871 秒）

参考图 `assets/layered-witness-single-view-v2.png`：

| 项 | 参数 | generation_id |
| --- | --- | --- |
| w1-01-raw-40k | Medium / Raw / 40k | `9d00676f-48f7-4d32-bf4d-fbfa2886e45f` |
| w1-02-raw-100k | Medium / Raw / 100k | `f844db0f-2a09-4719-b339-e31dba7bbc9c` |
| w1-03-raw-300k | Medium / Raw / 300k | `1bbd5832-8835-4bda-9267-58a100f4756b` |
| w1-04-quad-6k | Medium / Quad / 6k | `c24cec6d-7c86-46d4-99e4-a7148413949f` |
| w1-05-quad-12k | Medium / Quad / 12k | `782a8414-5cf9-48e1-b3f5-6f60cae5abef` |
| w1-06-quad-30k | Medium / Quad / 30k | `6c78ef48-2c4f-42be-9582-cb517fc32994` |
| w1-07-quad-50k | Medium / Quad / 50k | `ffad041f-fd85-4eb7-8a8a-2c4d9c8a915d` |
| w1-08-high-raw-100k | High / Raw / 100k | `ac45747d-dd7a-4224-8c2c-13adf403f00a` |

### 3.3 场景道具（8 次 = 4.0 额度，691 秒，纯文本生成）

| 项 | generation_id |
| --- | --- |
| s1-01-pedestal（展台） | `1165ba36-7626-4994-8930-5b9921d731e1` |
| s1-02-bench（长凳） | `9eaff85c-ec5e-41ac-b408-0439a0508c4b` |
| s1-03-lamp（落地灯） | `65ef5c9c-b3d1-4083-888b-0f7bfb78cb72` |
| s1-04-barrier（隔离柱） | `8d2dccb4-286c-4fa0-a79a-bb45c334e91f` |
| s1-05-reel（线轴） | `094f5e85-6b4d-4b9f-ab5e-1d04d7ad4ebc` |
| s1-06-crate（木箱） | `e290dafa-bbf0-4707-ab09-83a477e79b63` |
| s1-07-headphones（耳机） | `cc61ef8a-9636-4cc0-9718-221bb45f393b` |
| s1-08-camera（双反相机） | `edf0a8a5-7d5f-47c6-931c-2e82feb939cc` |

**重新取回任何任务的产物**（不计费、幂等）：

```powershell
& $cli result <generation_id> --output json    # files[] 内含 PBR 与着色两份的签名链接
```

签名链接有效期 `X-Tos-Expires=604800`（7 天），过期后重新调 `result` 即可。

---

## 4. 验证过的事实与踩过的坑

### 4.1 必须知道的三条结论

1. **三视图拼版会产生"合面"缺陷。** 把正/侧/背拼在一张图作为单一参考图提交时，Rodin 会把三个头像合进同一个网格，而 `node/mesh = 1` 完全看不出来。**必须用单人单图**。本项目首轮产物即为此缺陷样本，已作废保留对照。
2. **`--instruction` 决定分件方式，不是装饰。** 同一模型：给语义描述 → 8 件；不给 → 2 件。`--strength` 只是软目标（设 5 实得 8）。
3. **BANG 输出是"多部件单文件"，不是多个文件。** `result` 只返回 2 个条目（与普通生成同名），拆分结果在**文件内部**：9 nodes / 8 meshes / 8 materials。**看文件个数会误判成"没拆"。**

### 4.2 几何质量实测

| 资产 | 水密 | 边界边 | 非流形边 | 连通分量 |
| --- | --- | --- | --- | --- |
| v2 主角色（50 万面） | ✅ | 0 | 0 | 2 |
| bind-100k | ✅ | 0 | 0 | 2 |
| BANG 8 件（逐件） | ✅ 全部 | 0 | 0 | 1–3 |
| 场景道具 s1-01/02/06/08 | ✅ | 0 | 0 | 1 |
| 场景道具 s1-03/05/07 | ✅ | 0 | 0 | 2 |
| **场景道具 s1-04 隔离柱** | **❌** | **6** | 0 | 3 |

**Rodin 生成物普遍是闭合流形网格**，这是它适合打印的关键。但 **s1-04 隔离柱有 6 条边界边（孔洞），不可直接打印**，展示可用。

### 4.3 其它坑

| 坑 | 现象 | 正解 |
| --- | --- | --- |
| Blender 5.1 导出算子改名 | `bpy.ops.export_mesh.stl` 不存在 | 用 `bpy.ops.wm.stl_export`（同族 `wm.obj_export`/`wm.ply_export`/`wm.usd_export`） |
| Cycles 不可靠 | 引擎枚举里只有 `BLENDER_EEVEE` | 不要依赖 Cycles GPU 渲染 |
| 贴图副本导致体积爆炸 | 8 个分件各带一份 12.78 MB 贴图 → 102 MB | 用 `glb-split-parts.cjs --geometry-only` → 4.77 MB（21 倍） |
| 几何减面省不了体积 | 10 万面→2.5 万面，文件仅 11.9→9.0 MB | 体积大头是贴图；用 `blender-strip-textures.py` 剥离（11.66→0.50 MB，23 倍） |
| glTF 材质空对象非法 | `"normalTexture": {}` 会让 Blender 拒绝解析 | 贴图复制失败时必须**删除整个键**，不能只置 `undefined` |
| 嵌套键删除写错层 | `delete m['baseColorTexture']` 删的是外层同名键 | 必须从父对象删：`delete p['baseColorTexture']` |
| `--quality` 单位误解 | 曾误以为索引数 | 是**三角面数**，索引恒为 3 倍 |

---

## 5. 产物清单

项目总计 **1,046.80 MB**，C 盘剩余 26.93 GB。

### 5.1 展示页（项目根目录）

| 文件 | 大小 | 用途 |
| --- | --- | --- |
| `index.html` | 31.1 KB | 原有交互数字人页（**未改动**） |
| `layers.html` | 15.5 KB | **分层查看器**：8 图层可隔离/展开/调透明度 |
| `scene.html` | 10.2 KB | **分层记忆展厅**：角色 + 8 道具完整空间场景，三档切换 |
| `serve.mjs` | 6.2 KB | 原有预览服务（端口 8000） |
| `serve-layers.mjs` | 2.5 KB | 新页面专用服务（端口 8100），同时提供 node_modules 与 work/ |

**当前运行中**：<http://127.0.0.1:8000/>（原页）、<http://127.0.0.1:8100/layers.html>、<http://127.0.0.1:8100/scene.html>

### 5.2 关键产物目录

| 目录 | 大小 | 内容 |
| --- | --- | --- |
| `work/batch-char/` | 175.90 MB | 角色矩阵 16 个 GLB + `BATCH-CHAR-REPORT.md` |
| `work/hyper3d-scan/` | 162.74 MB | 参数扫描 10 个 GLB（**带合面缺陷，可清理**） |
| `work/batch-scene/` | 136.85 MB | 场景道具 16 个 GLB + 逐项 prompt |
| `work/bang-split/` | 132.73 MB | BANG 8 件（`parts-pbr/` 102 MB 带贴图 · `parts-print/` 4.77 MB 无贴图）+ `BANG-REPORT.md` |
| `work/scene-lite/` | 62.79 MB | 道具减面版（2.5 万面，带贴图） |
| `work/scene-assembled/` | 58.04 MB | **组装完成的场景**：`gallery-scene-geo2.glb`（9.63 MB，默认）/ `gallery-scene-lite.glb`（20.80 MB 贴图版） |
| `work/scene-geo/` | 8.68 MB | 道具纯几何版 |
| `work/print-ready/` | 4.77 MB | **8 个 STL，Z-up 朝向，可直接进切片器** |
| `work/bang-auto/` | 24.12 MB | 自动分件对照（2 件） |
| `work/singlescan-bind100k/` | 23.31 MB | 单人绑定底模 |
| `work/npm-cache-hyper3d/` | 48.74 MB | npm 缓存（**可清理**） |

### 5.3 报告

| 文件 | 内容 |
| --- | --- |
| `HYPER3D-HARNESS-HANDOFF.md` | 项目手册（含 5.5 CLI 脚本化、5.5.1 实测结论） |
| `work/batch-char/BATCH-CHAR-REPORT.md` | 角色矩阵 + Quad 拓扑判定 |
| `work/bang-split/BANG-REPORT.md` | BANG 分件 + 语义/自动对照 |
| `work/HYPER3D-PARAM-SCAN-2026-09-24.md` | 参数扫描报告 |
| `work/scene-assembled/` `geo/split-manifest.json` | 组装场景的节点清单 |

---

## 6. 脚本清单（全部实测可用）

位置：`C:\Users\wardc\Desktop\DSH工作区\03_技术\hyper3d\`

### 6.1 生成与流程

| 脚本 | 功能 | 验证 |
| --- | --- | --- |
| `hyper3d-login-watch.ps1` | 后台持有设备码授权窗口直到成功 | ✅ 实际完成登录 |
| `hyper3d-param-scan.ps1` | A–E 参数扫描 | ✅ 跑完 5 项 |
| `hyper3d-gen-bind-100k.ps1` | 单次生成绑定底模 | ✅ 90 秒 |
| `hyper3d-bang-split.ps1` | BANG 语义分件 | ✅ 8 件 |
| `hyper3d-bang-auto.ps1` | BANG 自动分件（对照） | ✅ 2 件 |
| `hyper3d-batch.ps1` | **清单驱动批量生成**（图片参考），支持 `-Only` / `-DryRun` | ✅ 8 项 |
| `hyper3d-batch-scene.ps1` | **纯文本批量生成场景道具** | ✅ 8 项 |

### 6.2 分析与加工（纯 Node，无依赖）

| 脚本 | 功能 |
| --- | --- |
| `check-scan-glb.cjs` | 批量结构核对（面数/顶点/材质/贴图/骨骼） |
| `mesh-doctor.cjs` | **打印体检**：水密性、非流形、退化面、连通分量、体积、尺寸 |
| `parts-report.cjs` | 多部件 GLB 逐件分析 |
| `valence-report.cjs` | **顶点价数分析**：判定拓扑规律性（4 价=四边形残留 / 6 价=纯三角） |
| `glb-split-parts.cjs` | 多部件 GLB → 一部件一文件；`--geometry-only` 去贴图 |

### 6.3 Blender 脚本

| 脚本 | 功能 |
| --- | --- |
| `blender-verify-import.py` | 批量导入验证 + 导出算子探测 |
| `blender-export-parts.py` | **GLB → STL/OBJ/PLY/GLB，含 Y-up→Z-up 转换** |
| `blender-quad-check.py` | 面型统计（三角/四边形分布） |
| `blender-decimate.py` | 批量减面（保留 UV 与材质） |
| `blender-strip-textures.py` | 剥离全部贴图，导出纯几何 GLB |
| `blender-scene-assemble.py` | **场景组装**：角色置原点 + 道具环形布列 + 地面 → 单一 GLB |
| `blender-export-probe.py` | 导出能力探测 + 渲染性能实测 |
| `blender-selftest.py` | ⚠️ 含已知错误（用了旧算子名），**不建议使用**，请改用 `blender-export-probe.py` |

---

## 7. 标准作业流程

### 7.1 生成一批资产

```powershell
# 1) 先干跑确认计划与额度
pwsh -File hyper3d-batch.ps1 -DryRun

# 2) 真跑（每项只提交一次，失败即停，绝不自动重跑）
pwsh -File hyper3d-batch.ps1

# 3) 核对结构
node check-scan-glb.cjs <产物目录>
node mesh-doctor.cjs <每个glb>          # 若要打印必做
```

**费用纪律（重要）**：一次 `generate` 就是一次计费提交。脚本必须做到"每项只提交一次、失败即停并交人工判断、绝不自动重跑"。提交超时先查已有任务，不要重复提交。

### 7.2 分件

```powershell
& $cli bang <generation_id> --instruction "<语义描述>" --strength 5 --format glb --output json
& $cli poll <bang_id> --timeout 1200 --output json
& $cli result <bang_id> --output json

# 拆成一部件一文件
node glb-split-parts.cjs <多部件.glb> <输出目录> lw-part                 # 带贴图
node glb-split-parts.cjs <多部件.glb> <输出目录> lw-print --geometry-only # 打印用
```

### 7.3 3D 打印

```powershell
# 几何精简 + 转 STL（Z-up）
& blender.exe -b -P blender-export-parts.py -- <parts-print目录> <输出> stl --zup
```

STL 无单位，导入切片器后按成品高度缩放：本模型原始高约 1.9 单位 → **缩放系数 = 目标毫米高 ÷ 1.9**。

### 7.4 组装场景

```powershell
& blender.exe -b -P blender-scene-assemble.py -- <角色glb> <道具目录> <输出glb> 4.0
```

### 7.5 启动展示

```powershell
node serve-layers.mjs      # 项目根目录，端口 8100
```

---

## 8. 边界与未验证项

### 8.1 CLI 做不到

- **无材质开关**（不需要：每次都返回 PBR + 着色两份）
- **无 seed、无 resolution、无 escore、无 reference_scale**（这些在 MCP 的 BANG 或 API 侧，**CLI 未暴露，未实测**）
- **无 image_label 视图方向标记**（仅官方 API 有，**未实测**）
- **无 TAPose 姿态约束**（仅 API，**未实测**）
- **`--tier` 仅三档**，无 `Low`/`Extreme-High`

### 8.2 生成物本身没有

无骨骼、无权重、无动画、无表情 blendshape、无口型数据。全部 30+ 份产物实测 `skins=0 animations=0`。

**"闭合流形"只证明几何有效，不等于可动画**——动画需要变形友好的拓扑（均匀四边形、合理循环边、腋下与裆部不粘连），本项目所有产物均需重拓扑。

### 8.3 未验证项（交接后需注意）

| 项 | 状态 |
| --- | --- |
| 官方 HTTP API（Bearer key） | **未开通**，材质/姿态/seed/image_label 等全部不可用 |
| Generate Texture 端点 | 未测（需 API key） |
| `rodin_import_images`（ChatGPT 附件专用） | 未测（DSH 无 MCP） |
| 多视图分开上传（前/侧/背各一张） | **未测**，是修复背面质量的正解，值得优先验证 |
| ChatAvatar 的面部/口型能力 | 未测，需单独核实导出资产格式 |
| Cycles GPU 渲染 | 仅确认可切换，**引擎枚举只有 EEVEE** |
| 页面视觉效果 | **未验证**（我只能验 HTTP 与语法，看不到页面） |
| 场景道具风格一致性 | **未验证**（用了统一风格前缀，但需人眼判断） |
| 3D 打印实际切片/壁厚/装配 | **未做**（已有 STL，但无切片器验证） |

---

## 9. 下一步建议

### 9.1 立即可做（0 额度）

1. **打开两个页面亲自验收**：<http://127.0.0.1:8100/layers.html> 与 <http://127.0.0.1:8100/scene.html>。重点看：8 图层是否对齐、道具朝向是否正确、风格是否像同一个世界。
2. **变形测试**：在 Blender 里对 `work/batch-char/w1-01-raw-40k/` 或 `bind-100k` 试着抬臂、屈膝，看是否塌陷撕裂 → 判断能否绑定。
3. **打印验证**：把 `work/print-ready/` 的 8 个 STL 拖进切片器，先只打 `lw-print-08-root.7.stl`（体积占 98.4%）做 12–15 cm 小样。

### 9.2 值得花额度的三个实验（各 0.5 额度）

| 实验 | 唯一变量 | 通过标准 |
| --- | --- | --- |
| **多视图分开上传** | 单图 vs 前/侧/背三张**独立**图 | 背面合理、无合面、特征一致 |
| **Generate Texture**（需先开 API key） | 同一几何两种表面风格 | 形体保持、接缝与光照伪影可接受 |
| **更低面数 Quad** | Quad 目标 3000 / Raw 目标 15000 | 找到可接受的最低面数 |

### 9.3 若要视频

本机**不可行**（EEVEE 480×480 单帧 36.8 秒，10 秒 30fps 视频需约 3 小时且内存不足）。需租带 GPU 的云主机（16–32 GB 内存 + T4/A10 级），把本目录与脚本搬过去即可——所有脚本不依赖本机特性。**注意：生成无需 GPU（在 Hyper3D 云端），租机器只为渲染。**

### 9.4 可清理项（释放约 211 MB）

- `work/hyper3d-scan/`（162.74 MB）——带合面缺陷，仅参数结论有价值
- `work/npm-cache-hyper3d/`（48.74 MB）——npm 缓存
- `work/blender-test/`、`work/v2-check/`——探测残留

---

## 10. 一句话交接

**已打通"生成 → 分件 → 体检 → 组装 → 展示 → 打印导出"全链路，16 次生成花掉 8.0 额度，产出 30+ 个 GLB、8 个 STL、2 个可交互页面。**

**最大的认知修正：`--mesh-mode Quad` 不产出四边形拓扑，`--quality` 单位是三角面数，三视图拼版会合面。**

**最该接着做的：先用 0 额度验收两个页面 + 做变形测试，再花 0.5 额度验证"多视图分开上传"——这是唯一可能实质改善几何质量的方向。**
