# 批量减面（Decimate）：把 Rodin 生成的 10 万面道具压到可进场景的规模
#
# 用法:
#   blender.exe -b -P blender-decimate.py -- <输入目录> <输出目录> <目标面数> [保留比例下限]
#
# 说明：
#   - 对每个 GLB 的每个网格对象添加 Decimate(COLLAPSE) 修改器，ratio = 目标面数 / 现有面数
#   - 保留 UV 与材质（Decimate 会保持 UV 展开，贴图仍可用）
#   - 导出 GLB，便于网页与引擎直接加载
#   - 输出文件名加 -lite 后缀，避免覆盖原件

import bpy
import sys
import os
import glob
import time

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 3:
    print("用法: blender -b -P blender-decimate.py -- <输入目录> <输出目录> <目标三角面数>")
    sys.exit(1)

src, outdir, target = args[0], args[1], int(args[2])
os.makedirs(outdir, exist_ok=True)
targets = sorted(glob.glob(os.path.join(src, "*.glb"))) if os.path.isdir(src) else [src]

print("=" * 74)
print(f"[减面] 输入 {len(targets)} 个   目标 {target:,} 三角面/件   → {outdir}")
print("=" * 74)

ok = fail = 0
for t in targets:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=t)
    except Exception as e:
        print(f"[失败-导入] {os.path.basename(t)} -> {e!r}")
        fail += 1
        continue

    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    if not objs:
        print(f"[跳过] {os.path.basename(t)} 无网格")
        fail += 1
        continue

    # 统计原始面数（三角化口径）
    before = 0
    for o in objs:
        o.data.calc_loop_triangles()
        before += len(o.data.loop_triangles)

    ratio = min(1.0, target / max(1, before))
    t0 = time.time()
    for o in objs:
        o.data.calc_loop_triangles()
        tris = len(o.data.loop_triangles)
        if tris == 0:
            continue
        r = min(1.0, target / before)  # 各对象按同一比例，保持相对密度
        bpy.context.view_layer.objects.active = o
        mod = o.modifiers.new(name="Decimate", type="DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = r
        mod.use_collapse_triangulate = True
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as e:
            print(f"[警告] 应用修改器失败 {o.name}: {e!r}")

    after = 0
    for o in objs:
        o.data.calc_loop_triangles()
        after += len(o.data.loop_triangles)

    base = os.path.splitext(os.path.basename(t))[0]
    dest = os.path.join(outdir, base + "-lite.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=dest, export_format="GLB")
    except Exception as e:
        print(f"[失败-导出] {base} -> {e!r}")
        fail += 1
        continue

    dt = time.time() - t0
    size_before = os.path.getsize(t)
    size_after = os.path.getsize(dest)
    print(f"[OK] {base:26s} {before:7,d} → {after:7,d} 面  (比例 {r:.3f})  "
          f"{size_before/1e6:7.2f} → {size_after/1e6:6.2f} MB  {dt:5.2f}s")
    ok += 1

print("=" * 74)
print(f"[减面] 成功 {ok} / 失败 {fail}")
sys.exit(0 if fail == 0 else 2)
