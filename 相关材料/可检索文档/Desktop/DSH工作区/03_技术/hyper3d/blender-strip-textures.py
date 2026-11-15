# 去贴图 / 重导出工具：读取任意 GLB，剥离全部贴图与材质纹理引用，导出纯几何 GLB
#
# 用法: blender.exe -b -P blender-strip-textures.py -- <输入glb> <输出glb>
#
# 适用场景：网页快速预览、场景占位、3D 打印（均不需要贴图）
# 注意：材质会保留但删除所有 image/texture 引用，因此 glTF 合法且 Blender 可解析。

import bpy
import sys
import os

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
if len(args) < 2:
    print("用法: blender -b -P blender-strip-textures.py -- <输入glb> <输出glb>")
    sys.exit(1)

src, dest = args[0], args[1]
os.makedirs(os.path.dirname(dest), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

# 记录导入后的规模
tris = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
imgs_before = len(bpy.data.images)

# 断开所有材质节点里的图像纹理连接并删除纹理节点
removed_nodes = 0
for mat in bpy.data.materials:
    if not mat.use_nodes or not mat.node_tree:
        continue
    nt = mat.node_tree
    for node in list(nt.nodes):
        if node.type in {"TEX_IMAGE", "TEX_ENVIRONMENT"}:
            nt.nodes.remove(node)
            removed_nodes += 1

# 移除全部图像数据块
for img in list(bpy.data.images):
    try:
        bpy.data.images.remove(img)
    except Exception:
        pass

bpy.ops.export_scene.gltf(filepath=dest, export_format="GLB")

import os as _os
print("=" * 66)
print(f"[去贴图] {os.path.basename(src)} → {os.path.basename(dest)}")
print(f"[去贴图] 三角面 {tris:,}   图像 {imgs_before} → {len(bpy.data.images)}   删除纹理节点 {removed_nodes}")
print(f"[去贴图] 文件 {os.path.getsize(src):,} → {os.path.getsize(dest):,} 字节 "
      f"({os.path.getsize(src)/1e6:.2f} → {os.path.getsize(dest)/1e6:.2f} MB)")
