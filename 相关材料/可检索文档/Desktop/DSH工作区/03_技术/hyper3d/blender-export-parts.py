# 分件导出工具：GLB → STL / OBJ / PLY / GLB，并把 Y-up 转为 Z-up（3D 打印常规朝向）
#
# 背景（本机实测）：
#   Blender 5.1 的导出算子已改名，STL/OBJ/PLY 在 wm 命名空间下：
#     bpy.ops.wm.stl_export / wm.obj_export / wm.ply_export / wm.usd_export
#   旧的 bpy.ops.export_mesh.stl 在本版本不存在。
#
# 用法:
#   blender.exe -b -P blender-export-parts.py -- <输入目录或glb> <输出目录> [stl|obj|ply|glb|all] [--zup]
#
# 说明：
#   - 默认对每个输入文件输出同名 STL，直接可拖进切片器
#   - --zup 会把模型绕 X 轴旋转 +90°，把 glTF 的 Y-up 转为打印常规的 Z-up
#   - STL 是单位无关的，切片器里再按毫米缩放即可（本模型原始高度约 1.9 单位）

import bpy
import sys
import os
import glob
import math
import time

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 2:
    print("用法: blender -b -P blender-export-parts.py -- <输入> <输出目录> [格式] [--zup]")
    sys.exit(1)

src = args[0]
outdir = args[1]
fmt = args[2] if len(args) > 2 and not args[2].startswith("--") else "stl"
zup = "--zup" in args

os.makedirs(outdir, exist_ok=True)

targets = []
if os.path.isdir(src):
    targets = sorted(glob.glob(os.path.join(src, "*.glb")))
elif os.path.exists(src):
    targets = [src]

print("=" * 70)
print(f"[导出] 输入 {len(targets)} 个文件  →  {outdir}  格式={fmt}  Z-up={zup}")
print("=" * 70)

ok = 0
fail = 0
for t in targets:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=t)
    except Exception as e:
        print(f"[失败-导入] {os.path.basename(t)} -> {e!r}")
        fail += 1
        continue

    objs = [o for o in bpy.data.objects if o.type == "MESH"]

    # Y-up → Z-up：绕 X 轴 +90°
    if zup:
        for o in objs:
            o.rotation_mode = "XYZ"
            o.rotation_euler.x += math.radians(90)
        bpy.context.view_layer.update()
        # 应用变换，让导出结果直接是最终朝向
        for o in objs:
            o.select_set(True)
        if objs:
            bpy.context.view_layer.objects.active = objs[0]
            try:
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            except Exception as e:
                print(f"[警告] 应用旋转失败（不影响导出）: {e!r}")

    base = os.path.splitext(os.path.basename(t))[0]
    written = []
    t0 = time.time()

    def try_export(label, fn):
        try:
            fn()
            return True
        except Exception as e:
            print(f"[失败-{label}] {base} -> {e!r}")
            return False

    if fmt in ("stl", "all"):
        p = os.path.join(outdir, base + ".stl")
        if try_export("stl", lambda: bpy.ops.wm.stl_export(filepath=p, export_selected_objects=False)):
            written.append(p)
    if fmt in ("obj", "all"):
        p = os.path.join(outdir, base + ".obj")
        if try_export("obj", lambda: bpy.ops.wm.obj_export(filepath=p, export_selected_objects=False)):
            written.append(p)
    if fmt in ("ply", "all"):
        p = os.path.join(outdir, base + ".ply")
        if try_export("ply", lambda: bpy.ops.wm.ply_export(filepath=p, export_selected_objects=False)):
            written.append(p)
    if fmt in ("glb", "all"):
        p = os.path.join(outdir, base + ".glb")
        if try_export("glb", lambda: bpy.ops.export_scene.gltf(filepath=p, export_format="GLB")):
            written.append(p)

    dt = time.time() - t0
    if written:
        sizes = ", ".join(f"{os.path.splitext(w)[1][1:]}:{os.path.getsize(w)}B" for w in written)
        verts = sum(len(o.data.vertices) for o in objs)
        print(f"[OK] {base:32s} 对象 {len(objs)}  顶点 {verts:7d}  {dt:5.2f}s  {sizes}")
        ok += 1
    else:
        print(f"[失败] {base} 未产出任何文件")
        fail += 1

print("=" * 70)
print(f"[导出] 成功 {ok} / 失败 {fail}")
print(f"[提示] STL 无单位，导入切片器后按成品高度缩放：本模型原始高约 1.9 单位 → 缩放系数 = 目标毫米高 ÷ 1.9")
sys.exit(0 if fail == 0 else 2)
