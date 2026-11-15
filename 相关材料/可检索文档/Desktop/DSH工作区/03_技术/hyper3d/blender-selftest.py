# Headless Blender 能力自检
# 目的：确认本机能否用 Blender 命令行完成「导入 GLB -> 探测 -> 导出 STL -> 渲染单帧」
# 用法: & "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b -P blender-selftest.py -- <glb路径> <输出目录>
#
# 注意：本脚本只做只读探测与少量输出，不修改任何源文件。

import bpy
import sys
import os
import time

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
glb = args[0] if len(args) > 0 else None
outdir = args[1] if len(args) > 1 else os.path.expanduser("~")

print("=" * 60)
print("[自检] Blender 版本:", bpy.app.version_string)
print("[自检] 输出目录:", outdir)
print("=" * 60)

# 1. 可用渲染引擎
try:
    engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    print("[自检] 可用渲染引擎:", ", ".join(engines))
except Exception as e:
    print("[自检] 读取引擎列表失败:", e)

# 2. 导出器插件
for mod in ("io_scene_gltf2", "io_scene_fbx", "io_mesh_stl", "io_scene_obj"):
    enabled = mod in bpy.context.preferences.addons
    print(f"[自检] 插件 {mod}: {'已启用' if enabled else '未启用'}")

# 3. 清空默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 4. 导入 GLB（若提供）
if glb and os.path.exists(glb):
    t0 = time.time()
    try:
        bpy.ops.import_scene.gltf(filepath=glb)
        dt = time.time() - t0
        objs = [o for o in bpy.data.objects if o.type == "MESH"]
        tris = 0
        verts = 0
        for o in objs:
            me = o.data
            verts += len(me.vertices)
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
        print(f"[自检] GLB 导入成功: {os.path.basename(glb)}  耗时 {dt:.2f} 秒")
        print(f"[自检]   网格对象 {len(objs)} 个  顶点 {verts}  三角面 {tris}")
        dims = []
        for o in objs:
            dims.append(tuple(round(v, 4) for v in o.dimensions))
        print(f"[自检]   各对象尺寸(Blender 坐标系): {dims[:8]}")
    except Exception as e:
        print("[自检] GLB 导入失败:", repr(e))
else:
    print("[自检] 未提供 GLB 或文件不存在，跳过导入测试")

# 5. 导出 STL 测试
try:
    stl = os.path.join(outdir, "_selftest_export.stl")
    bpy.ops.export_mesh.stl(filepath=stl)
    size = os.path.getsize(stl) if os.path.exists(stl) else -1
    print(f"[自检] STL 导出成功: {size} 字节")
    if os.path.exists(stl):
        os.remove(stl)
except Exception as e:
    print("[自检] STL 导出失败:", repr(e))

# 6. 渲染单帧测试（EEVEE 最小场景，不依赖上面的导入）
try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 0))
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, -5, 1)
    cam.rotation_euler = (1.4, 0, 0)
    bpy.context.scene.camera = cam
    scn = bpy.context.scene
    scn.render.resolution_x = 320
    scn.render.resolution_y = 240
    scn.render.image_settings.file_format = "PNG"
    png = os.path.join(outdir, "_selftest_render.png")
    scn.render.filepath = png

    engine_used = None
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scn.render.engine = eng
            engine_used = eng
            break
        except Exception:
            continue
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    size = os.path.getsize(png) if os.path.exists(png) else -1
    print(f"[自检] 渲染成功: 引擎={engine_used}  320x240 耗时 {dt:.2f} 秒  输出 {size} 字节")
    if os.path.exists(png):
        os.remove(png)
except Exception as e:
    print("[自检] 渲染失败:", repr(e))

print("=" * 60)
print("[自检] 结束")
