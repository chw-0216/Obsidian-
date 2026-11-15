from pathlib import Path
from mesh_pdf import MeshRenderer
B=Path(__file__).resolve().parent
maps={"rendered_background":B/"render_color_mesh.npz"}
for xml,pdf in [
    ("poster_small.xml","PD2027_V2_Vector_210x280mm.pdf"),
    ("poster_large.xml","PD2027_V2_Vector_600x800mm.pdf"),
    ("background_large.xml","PD2027_V2_Background_Vector_600x800mm.pdf")]:
    MeshRenderer(B/xml,maps).save(B.parent/pdf)
