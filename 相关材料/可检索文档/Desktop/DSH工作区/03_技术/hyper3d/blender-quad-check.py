# 判定 Quad 模式的计数口径：导入后看面类型与数量
# 用法: blender.exe -b -P blender-quad-check.py -- <glb> [glb...]

import bpy
import sys
import os

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

print("=" * 78)
print("[口径判定] 面类型统计 —— 用于回答「--quality 的目标是三角面还是四边形面」")
print("=" * 78)

for f in args:
    if not os.path.exists(f):
        print(f"[跳过] 不存在: {f}")
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=f)
    except Exception as e:
        print(f"[失败] {os.path.basename(f)} -> {e!r}")
        continue

    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    total_polys = 0
    total_tris = 0
    by_size = {}
    for o in objs:
        me = o.data
        counts = {}
        for p in me.polygons:
            counts[len(p.vertices)] = counts.get(len(p.vertices), 0) + 1
        for k, v in counts.items():
            by_size[k] = by_size.get(k, 0) + v
        total_polys += len(me.polygons)
        me.calc_loop_triangles()
        total_tris += len(me.loop_triangles)

    sizes = ", ".join(f"{k}边形×{v}" for k, v in sorted(by_size.items()))
    print(f"文件: {os.path.basename(f)}")
    print(f"  对象 {len(objs)}  多边形总数 {total_polys}  三角化后 {total_tris}")
    print(f"  面类型分布: {sizes}")
    if by_size.get(3, 0) == total_polys:
        print("  判定: 全部为三角面 → 该产物是三角网格，--quality 口径应按三角面理解")
    elif by_size.get(4, 0) == total_polys:
        print("  判定: 全部为四边形面 → Quad 模式确实输出四边面，--quality 口径应按四边形理解")
    else:
        print("  判定: 混合面型")
    print("-" * 78)
