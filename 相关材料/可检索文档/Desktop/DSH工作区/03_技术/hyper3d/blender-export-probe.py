# Blender 5.1 导出算子全量探测 + 真实渲染性能实测
# 用法: blender.exe -b -P blender-export-probe.py -- <glb> <outdir> [分辨率] [帧数]

import bpy
import sys
import os
import time

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
glb = args[0] if len(args) > 0 else None
outdir = args[1] if len(args) > 1 else os.path.expanduser("~")
res = int(args[2]) if len(args) > 2 else 480
frames = int(args[3]) if len(args) > 3 else 3

print("=" * 68)
print("[探测] Blender", bpy.app.version_string)

# 1. 枚举所有可能的导出算子族
for ns in ("export_scene", "export_mesh", "wm"):
    try:
        names = sorted(o for o in dir(getattr(bpy.ops, ns)) if not o.startswith("_"))
        print(f"[探测] bpy.ops.{ns}: {', '.join(names)}")
    except Exception as e:
        print(f"[探测] bpy.ops.{ns} 读取失败: {e}")

# 2. 专门找 stl / obj / ply 相关算子
found = []
for ns in dir(bpy.ops):
    if ns.startswith("_"):
        continue
    try:
        for op in dir(getattr(bpy.ops, ns)):
            if any(k in op.lower() for k in ("stl", "obj", "ply", "usd")):
                found.append(f"bpy.ops.{ns}.{op}")
    except Exception:
        pass
print(f"[探测] 与 stl/obj/ply/usd 相关的算子: {', '.join(sorted(set(found))) if found else '（一个都没有）'}")

# 3. 检查 io_mesh_stl 之类的插件是否存在但未启用
import addon_utils
mods = [m.__name__ for m in addon_utils.modules()]
rel = [m for m in mods if any(k in m.lower() for k in ("stl", "obj", "ply"))]
print(f"[探测] 已安装的相关插件模块: {', '.join(rel) if rel else '（无）'}")

# 4. glTF 导出能力（打印可用 GLB 交切片器）
bpy.ops.wm.read_factory_settings(use_empty=True)
if glb and os.path.exists(glb):
    t0 = time.time()
    bpy.ops.import_scene.gltf(filepath=glb)
    print(f"[实测] 导入 {os.path.basename(glb)} 耗时 {time.time()-t0:.2f}s")

    test_glb = os.path.join(outdir, "_probe_export.glb")
    try:
        t0 = time.time()
        bpy.ops.export_scene.gltf(filepath=test_glb, export_format="GLB")
        print(f"[实测] GLB 导出成功 {os.path.getsize(test_glb)} 字节，耗时 {time.time()-t0:.2f}s")
        os.remove(test_glb)
    except Exception as e:
        print(f"[实测] GLB 导出失败: {e!r}")

    test_fbx = os.path.join(outdir, "_probe_export.fbx")
    try:
        t0 = time.time()
        bpy.ops.export_scene.fbx(filepath=test_fbx)
        print(f"[实测] FBX 导出成功 {os.path.getsize(test_fbx)} 字节，耗时 {time.time()-t0:.2f}s")
        os.remove(test_fbx)
    except Exception as e:
        print(f"[实测] FBX 导出失败: {e!r}")

# 5. 真实渲染性能：EEVEE + Cycles(CPU) 各渲一帧同分辨率
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))
mat = bpy.data.materials.new("M")
mat.use_nodes = True
bpy.context.object.data.materials.append(mat)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0, -6, 1.5)
cam.rotation_euler = (1.35, 0, 0)
bpy.context.scene.camera = cam
light_data = bpy.data.lights.new("L", type="SUN")
light = bpy.data.objects.new("L", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.8, 0.2, 0.5)

scn = bpy.context.scene
scn.render.resolution_x = res
scn.render.resolution_y = res
scn.render.image_settings.file_format = "PNG"
scn.render.film_transparent = True

engines = []
try:
    engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
except Exception:
    pass
print(f"[探测] 引擎清单: {', '.join(engines)}")

for eng in engines:
    try:
        scn.render.engine = eng
        scn.render.filepath = os.path.join(outdir, f"_probe_{eng}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        size = os.path.getsize(scn.render.filepath) if os.path.exists(scn.render.filepath) else -1
        print(f"[实测] 渲染 {eng} @ {res}x{res}: {dt:.2f} 秒/帧  输出 {size} 字节  预估 120 帧需 {dt*120/60:.1f} 分钟")
        if os.path.exists(scn.render.filepath):
            os.remove(scn.render.filepath)
    except Exception as e:
        print(f"[实测] 渲染 {eng} 失败: {e!r}")

print("=" * 68)
