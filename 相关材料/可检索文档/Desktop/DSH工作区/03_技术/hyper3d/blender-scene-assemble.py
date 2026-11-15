# 场景组装：把主角色与道具按空间关系摆成一个展厅，导出单一 GLB
#
# 布局逻辑：
#   - 主角色置于原点，按原始尺寸（最长边约 1.9 单位）
#   - 8 件道具各缩放到约 1 米高，均匀分布在半径 R 的圆环上，正面朝向中心
#   - 铺一块地面接收阴影
#
# 用法:
#   blender.exe -b -P blender-scene-assemble.py -- <角色glb> <道具目录> <输出glb> [半径]
#
# 说明：
#   GLB/glTF 是 Y 轴向上；本脚本在 Blender 的 Z-up 空间内摆好后，
#   导出时由 glTF 导出器统一转回 Y-up，因此网页中朝向正常。

import bpy
import sys
import os
import glob
import math
import time

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 3:
    print("用法: blender -b -P blender-scene-assemble.py -- <角色glb> <道具目录> <输出glb> [半径]")
    sys.exit(1)

charPath, propDir, outPath = args[0], args[1], args[2]
radius = float(args[3]) if len(args) > 3 else 4.0
propTarget = 1.0   # 每件道具最长边目标（与角色同处一个尺度）

print("=" * 76)
print(f"[组装] 角色 {os.path.basename(charPath)}")
print(f"[组装] 道具目录 {propDir}")
print(f"[组装] 输出 {outPath}  环半径 {radius}  道具目标高度 {propTarget}")

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------- 1. 主角色 ----------
try:
    bpy.ops.import_scene.gltf(filepath=charPath)
except Exception as e:
    print(f"[失败] 角色导入失败: {e!r}")
    sys.exit(1)

charObjs = [o for o in bpy.data.objects if o.type == "MESH"]
for o in charObjs:
    o.name = "character_" + o.name
print(f"[组装] 角色网格 {len(charObjs)} 个")

# ---------- 2. 道具：缩放到统一尺度并布环 ----------
props = sorted(glob.glob(os.path.join(propDir, "*.glb")))
placed = []
if props:
    step = (2 * math.pi) / len(props)
    for i, p in enumerate(props):
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=p)
        except Exception as e:
            print(f"[警告] 道具导入失败 {os.path.basename(p)}: {e!r}")
            continue
        new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
        if not new:
            continue

        # 计算该道具整体的包围盒（世界坐标）
        mins = [math.inf] * 3
        maxs = [-math.inf] * 3
        for o in new:
            for c in o.bound_box:
                w = o.matrix_world @ __import__("mathutils").Vector(c)
                for k in range(3):
                    mins[k] = min(mins[k], w[k])
                    maxs[k] = max(maxs[k], w[k])
        dims = [maxs[k] - mins[k] for k in range(3)]
        longest = max(dims) or 1.0
        s = propTarget / longest

        ang = i * step
        tx, ty = math.cos(ang) * radius, math.sin(ang) * radius

        for o in new:
            o.name = f"prop{i+1}_" + os.path.splitext(os.path.basename(p))[0]
            o.scale = (o.scale[0] * s, o.scale[1] * s, o.scale[2] * s)
            # 摆到环上，并让它正面朝向中心（绕 Z 轴旋转）
            o.rotation_mode = "XYZ"
            o.rotation_euler.z += ang + math.pi
            o.location.x += tx
            o.location.y += ty
            # 落地：把底部对齐到 z=0
            o.location.z -= mins[2] * s
        placed.append((os.path.basename(p), s, (tx, ty)))

bpy.context.view_layer.update()
print(f"[组装] 已摆放道具 {len(placed)} 件")

# ---------- 3. 地面 ----------
bpy.ops.mesh.primitive_plane_add(size=max(12.0, radius * 3.2), location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "ground"
gm = bpy.data.materials.new("ground_material")
gm.use_nodes = True
bsdf = gm.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.78, 0.75, 0.70, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.92
ground.data.materials.append(gm)

# ---------- 4. 统计与导出 ----------
total_tris = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.calc_loop_triangles()
        total_tris += len(o.data.loop_triangles)
print(f"[组装] 场景合计三角面 {total_tris:,}")

os.makedirs(os.path.dirname(outPath), exist_ok=True)
t0 = time.time()
bpy.ops.export_scene.gltf(filepath=outPath, export_format="GLB")
dt = time.time() - t0
size = os.path.getsize(outPath)

print("=" * 76)
print(f"[组装] 导出成功 {outPath}")
print(f"[组装] 文件 {size:,} 字节 ({size/1e6:.2f} MB)  耗时 {dt:.2f}s  三角面 {total_tris:,}")
for name, s, pos in placed:
    print(f"    {name:34s} 缩放 {s:.4f}  位置 ({pos[0]:+.2f}, {pos[1]:+.2f})")
