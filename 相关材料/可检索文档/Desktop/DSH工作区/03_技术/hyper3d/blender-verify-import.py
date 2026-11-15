# Blender 导入验证 + 导出算子探测
# 用法: blender.exe -b -P blender-verify-import.py -- <目录或glb> [更多...]
# 只做导入与探测，不渲染（避免内存压力）。

import bpy
import sys
import os
import glob
import time

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

print("=" * 64)
print("[验证] Blender", bpy.app.version_string)

# 1. 探测可用的导出算子
ops = [o for o in dir(bpy.ops.export_scene)] + [o for o in dir(bpy.ops.export_mesh)]
cands = sorted({o for o in ops if not o.startswith("_")})
print("[验证] export_scene 算子:", ", ".join(sorted(o for o in dir(bpy.ops.export_scene) if not o.startswith("_"))))
try:
    print("[验证] export_mesh 算子:", ", ".join(sorted(o for o in dir(bpy.ops.export_mesh) if not o.startswith("_"))))
except Exception as e:
    print("[验证] export_mesh 读取失败:", e)

# 2. 逐个导入
targets = []
for a in args:
    if os.path.isdir(a):
        targets += sorted(glob.glob(os.path.join(a, "*.glb")))
    elif os.path.exists(a):
        targets.append(a)

print(f"[验证] 待导入 {len(targets)} 个文件")
ok = 0
fail = 0
for t in targets:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    t0 = time.time()
    try:
        bpy.ops.import_scene.gltf(filepath=t)
        dt = time.time() - t0
        objs = [o for o in bpy.data.objects if o.type == "MESH"]
        verts = sum(len(o.data.vertices) for o in objs)
        tris = 0
        for o in objs:
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
        mats = len(bpy.data.materials)
        imgs = len(bpy.data.images)
        print(f"[验证] OK   {os.path.basename(t):36s} {dt:5.2f}s  对象 {len(objs)}  顶点 {verts:7d}  三角面 {tris:7d}  材质 {mats}  贴图 {imgs}")
        ok += 1
    except Exception as e:
        print(f"[验证] FAIL {os.path.basename(t):36s} -> {e!r}")
        fail += 1

print("=" * 64)
print(f"[验证] 成功 {ok} / 失败 {fail}")
sys.exit(0 if fail == 0 else 3)
