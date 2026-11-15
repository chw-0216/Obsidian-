from pathlib import Path
import struct,zlib,math,json
import numpy as np,fitz
from native_svg_pdf import Renderer as BaseRenderer,arr
class MeshRenderer(BaseRenderer):
    def __init__(self,svg,mesh_files):
        super().__init__(svg);self.mesh_files=mesh_files;self.mesh_shadings={}
    def mesh_shading(self,key):
        if key in self.mesh_shadings:return self.mesh_shadings[key][0]
        a=np.load(self.mesh_files[key]);xy=a["xy"].astype(float);colors=a["rgb"].astype(np.uint8)
        xmin=float(xy[:,:,0].min());xmax=float(xy[:,:,0].max())
        ymin=float(xy[:,:,1].min());ymax=float(xy[:,:,1].max())
        coords=np.empty_like(xy,dtype=np.uint16)
        coords[:,:,0]=np.rint((xy[:,:,0]-xmin)/(xmax-xmin)*65535).clip(0,65535).astype(np.uint16)
        coords[:,:,1]=np.rint((xy[:,:,1]-ymin)/(ymax-ymin)*65535).clip(0,65535).astype(np.uint16)
        packed=np.empty((xy.shape[0],xy.shape[1],7),dtype=np.uint8)
        packed[:,:,0]=(coords[:,:,0]>>8).astype(np.uint8);packed[:,:,1]=(coords[:,:,0]&255).astype(np.uint8)
        packed[:,:,2]=(coords[:,:,1]>>8).astype(np.uint8);packed[:,:,3]=(coords[:,:,1]&255).astype(np.uint8)
        packed[:,:,4:7]=colors
        raw=packed.tobytes()
        ref=self.obj(f"<</ShadingType 5 /ColorSpace /DeviceRGB /BitsPerCoordinate 16 /BitsPerComponent 8 /VerticesPerRow {xy.shape[1]} /Decode [{arr([xmin,xmax,ymin,ymax])} 0 1 0 1 0 1] /AntiAlias true>>")
        self.doc.update_stream(ref,raw,compress=True)
        name=f"Mesh{len(self.mesh_shadings)}";self.mesh_shadings[key]=(name,ref)
        return name
    def walk(self,e,style=None):
        mesh=e.get("data-native-mesh")
        if mesh:
            from native_svg_pdf import matrix
            self.contents.append("q");self.contents.extend(matrix(e.get("transform","")))
            if e.get("clip-path"):
                import re
                gid=re.search(r"#([^)]+)",e.get("clip-path")).group(1)
                for ch in self.ids[gid]:
                    cmd,b=self.geometry(ch)
                    if cmd:self.contents.append(cmd)
                self.contents.append("W n")
            self.contents.append("/"+self.mesh_shading(mesh)+" sh")
            self.contents.append("Q")
            return
        return super().walk(e,style)
    def save(self,outpath):
        # Mirror BaseRenderer's final native resources, adding the gradient mesh dictionary.
        from native_svg_pdf import arr
        vx,vy,vw,vh=[float(x) for x in self.root.get("viewBox").split()]
        sx=self.w*self.mm/vw;sy=self.h*self.mm/vh
        self.contents=["q",arr((sx,0,0,-sy,-vx*sx,self.h*self.mm+vy*sy))+" cm"]
        self.walk(self.root);self.contents.append("Q")
        shades=list(self.shadings.values())+list(self.mesh_shadings.values())
        resources=self.obj("<</Shading <<"+" ".join("/"+n+" "+str(r)+" 0 R" for n,r in shades)+">> /ExtGState <<"+" ".join("/"+n+" "+str(r)+" 0 R" for n,r in self.alphas.values())+">> >>")
        stream=self.obj("<<>>");self.doc.update_stream(stream,"\n".join(self.contents).encode("ascii"))
        self.doc.xref_set_key(self.page.xref,"Resources",f"{resources} 0 R");self.doc.xref_set_key(self.page.xref,"Contents",f"{stream} 0 R")
        self.page.set_trimbox(fitz.Rect(3*self.mm,3*self.mm,(self.w-3)*self.mm,(self.h-3)*self.mm));self.page.set_bleedbox(self.page.mediabox)
        self.doc.set_metadata({"title":"PD2027 | Refined structure | photographic render review","author":"PD2027 design for Cai Haowen","subject":"Generated architectural render stored as native Type 5 color mesh, original vector type and marks. Source resolution 1086x1448. Review; dates pending confirmation."})
        self.doc.save(outpath,garbage=4,deflate=True);self.doc.close()
        print(json.dumps({"file":str(outpath),"native_mesh_shadings":len(self.mesh_shadings),"axial_gradients":len(self.shadings),"raster_images":0}),flush=True)

