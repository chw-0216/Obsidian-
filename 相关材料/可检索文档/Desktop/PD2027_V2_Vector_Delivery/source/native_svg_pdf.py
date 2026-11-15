"""Small native PDF renderer for the controlled SVG print master.
Supports paths, groups, glyph uses, rectangles, ellipses, clipping and linear gradients.
No rasterization, fonts, browser or external converter are involved.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import re,math,json
import fitz
from fontTools.svgLib.path import parse_path
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.teePen import TeePen

def fmt(v):
 s=f'{v:.8f}'.rstrip('0').rstrip('.')
 return s if s and s!='-0' else '0'
def arr(vals):return ' '.join(fmt(v) for v in vals)
class PDFPen(BasePen):
 def __init__(self):super().__init__(None);self.commands=[]
 def _moveTo(self,p):self.commands.append(arr(p)+' m')
 def _lineTo(self,p):self.commands.append(arr(p)+' l')
 def _curveToOne(self,a,b,c):self.commands.append(arr((*a,*b,*c))+' c')
 def _closePath(self):self.commands.append('h')
 def _endPath(self):pass

def rgb(c):
 if c.startswith('#'):
  c=c[1:]
  if len(c)==3:c=''.join(x*2 for x in c)
  return [int(c[i:i+2],16)/255 for i in (0,2,4)]
 return [0,0,0] if c in ('black','none') else [1,1,1]
def matrix(s):
 out=[]
 for cmd,args in re.findall(r'(matrix|translate|scale|rotate)\(([^)]+)\)',s):
  a=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][-+]?\d+)?',args)]
  if cmd=='matrix':m=a
  elif cmd=='translate':m=[1,0,0,1,a[0],a[1] if len(a)>1 else 0]
  elif cmd=='scale':m=[a[0],0,0,a[1] if len(a)>1 else a[0],0,0]
  else:
   t=math.radians(a[0]);m=[math.cos(t),math.sin(t),-math.sin(t),math.cos(t),0,0]
  out.append(arr(m)+' cm')
 return out

class Renderer:
 def __init__(self,svg):
  self.root=E.parse(svg).getroot();self.ids={e.get('id'):e for e in self.root.iter() if e.get('id')}
  self.doc=fitz.open();self.mm=72/25.4
  self.w=float(re.search(r'[\d.]+',self.root.get('width')).group())
  self.h=float(re.search(r'[\d.]+',self.root.get('height')).group())
  self.page=self.doc.new_page(width=self.w*self.mm,height=self.h*self.mm)
  self.contents=[];self.path_cache={};self.funcs={};self.shadings={};self.alphas={}
 def obj(self,data):
  x=self.doc.get_new_xref();self.doc.update_object(x,data);return x
 def geometry(self,e):
  t=e.tag.split('}')[-1];a=e.attrib
  if t=='path':
   d=a.get('d','')
   if not d:return '',None
   if d not in self.path_cache:
    pen=PDFPen();bp=BoundsPen(None);parse_path(d,TeePen([pen,bp]));self.path_cache[d]=('\n'.join(pen.commands),bp.bounds)
   return self.path_cache[d]
  if t=='rect':
   x,y,w,h=[float(a.get(k,'0')) for k in ('x','y','width','height')]
   return arr((x,y,w,h))+' re',(x,y,x+w,y+h)
  if t in ('ellipse','circle'):
   x=float(a.get('cx','0'));y=float(a.get('cy','0'));rx=float(a.get('rx',a.get('r','0')));ry=float(a.get('ry',a.get('r','0')));k=.5522847498307936
   cmds=[arr((x+rx,y))+' m',arr((x+rx,y+ry*k,x+rx*k,y+ry,x,y+ry))+' c',arr((x-rx*k,y+ry,x-rx,y+ry*k,x-rx,y))+' c',arr((x-rx,y-ry*k,x-rx*k,y-ry,x,y-ry))+' c',arr((x+rx*k,y-ry,x+rx,y-ry*k,x+rx,y))+' c','h']
   return '\n'.join(cmds),(x-rx,y-ry,x+rx,y+ry)
  return '',None
 def alpha(self,opacity):
  key=round(float(opacity),6)
  if key not in self.alphas:self.alphas[key]=(f'A{len(self.alphas)}',self.obj(f'<</Type /ExtGState /ca {fmt(key)} /CA {fmt(key)}>>'))
  return '/'+self.alphas[key][0]+' gs'
 def shading(self,gid,bbox):
  key=(gid,tuple(round(x,5) for x in bbox))
  if key in self.shadings:return self.shadings[key][0]
  g=self.ids[gid];stops=[(float(s.get('offset')),rgb(s.get('stop-color'))) for s in g]
  if gid not in self.funcs:
   fs=[]
   for (o,c),(o2,c2) in zip(stops,stops[1:]):fs.append(self.obj(f'<</FunctionType 2 /Domain [0 1] /C0 [{arr(c)}] /C1 [{arr(c2)}] /N 1>>'))
   if len(fs)==1:fx=fs[0]
   else:fx=self.obj(f'<</FunctionType 3 /Domain [0 1] /Functions [{" ".join(str(f)+" 0 R" for f in fs)}] /Bounds [{arr([s[0] for s in stops[1:-1]])}] /Encode [{"0 1 "*len(fs)}]>>')
   self.funcs[gid]=fx
  x0,y0,x1,y1=bbox;w=x1-x0;h=y1-y0
  coords=[x0+float(g.get('x1','0'))*w,y0+float(g.get('y1','0'))*h,x0+float(g.get('x2','1'))*w,y0+float(g.get('y2','0'))*h]
  ref=self.obj(f'<</ShadingType 2 /ColorSpace /DeviceRGB /Coords [{arr(coords)}] /Domain [0 1] /Function {self.funcs[gid]} 0 R /Extend [true true]>>')
  name=f'S{len(self.shadings)}';self.shadings[key]=(name,ref);return name
 def walk(self,e,style=None):
  t=e.tag.split('}')[-1]
  if t in ('defs','title','desc','metadata','style'):return
  if e.get('fill')=='url(#sunlit-air)':return
  st=dict(style or {'fill':'#000000','stroke':'none','stroke-width':'1'})
  for k in ('fill','stroke','stroke-width','fill-rule','stroke-linecap','stroke-linejoin'):
   if k in e.attrib:st[k]=e.get(k)
  out=self.contents;out.append('q');out.extend(matrix(e.get('transform','')))
  if e.get('opacity') is not None:out.append(self.alpha(e.get('opacity')))
  if e.get('clip-path'):
   gid=re.search(r'#([^)]+)',e.get('clip-path')).group(1);cp=self.ids[gid]
   for child in cp:
    commands,b=self.geometry(child)
    if commands:out.append(commands)
   out.append('W n')
  if t=='use':
   href=e.get('{http://www.w3.org/1999/xlink}href',e.get('href'))
   out.append(arr((1,0,0,1,float(e.get('x','0')),float(e.get('y','0'))))+' cm')
   self.walk(self.ids[href[1:]],st)
  elif t in ('g','svg'):
   for child in e:self.walk(child,st)
  else:
   commands,b=self.geometry(e)
   if commands and b:
    fill=st.get('fill','none');stroke=st.get('stroke','none');evenodd=st.get('fill-rule')=='evenodd'
    dofill=fill!='none';dostroke=stroke!='none'
    if dostroke:
     out.extend([arr(rgb(stroke))+' RG',fmt(float(st.get('stroke-width','1')))+' w',str({'butt':0,'round':1,'square':2}.get(st.get('stroke-linecap'),0))+' J',str({'miter':0,'round':1,'bevel':2}.get(st.get('stroke-linejoin'),0))+' j'])
    if dofill and fill.startswith('url('):
     gid=re.search(r'#([^)]+)',fill).group(1)
     if b[2]-b[0]>.000001 and b[3]-b[1]>.000001:
      sh=self.shading(gid,b);out.extend(['q',commands,'W* n' if evenodd else 'W n','/'+sh+' sh','Q'])
     if dostroke:out.extend([commands,'S'])
    else:
     if dofill:out.append(arr(rgb(fill))+' rg')
     out.append(commands)
     out.append(('B*' if evenodd else 'B') if dofill and dostroke else ('f*' if evenodd else 'f') if dofill else 'S' if dostroke else 'n')
  out.append('Q')
 def save(self,outpath):
  vx,vy,vw,vh=[float(x) for x in self.root.get('viewBox').split()];sx=self.w*self.mm/vw;sy=self.h*self.mm/vh
  self.contents=['q',arr((sx,0,0,-sy,-vx*sx,self.h*self.mm+vy*sy))+' cm']
  self.walk(self.root);self.contents.append('Q')
  resources=self.obj('<</Shading <<'+' '.join('/'+n+' '+str(r)+' 0 R' for n,r in self.shadings.values())+'>> /ExtGState <<'+' '.join('/'+n+' '+str(r)+' 0 R' for n,r in self.alphas.values())+'>> >>')
  stream=self.obj('<<>>');self.doc.update_stream(stream,'\n'.join(self.contents).encode('ascii'))
  self.doc.xref_set_key(self.page.xref,'Resources',f'{resources} 0 R');self.doc.xref_set_key(self.page.xref,'Contents',f'{stream} 0 R')
  self.page.set_trimbox(fitz.Rect(3*self.mm,3*self.mm,(self.w-3)*self.mm,(self.h-3)*self.mm));self.page.set_bleedbox(self.page.mediabox)
  self.doc.set_metadata({'title':'PD2027 | refined vector architectural poster','author':'PD2027 poster for Cai Haowen','subject':'Native paths, native PDF gradient shadings and outlined text. 3 mm bleed.'})
  self.doc.save(outpath,garbage=4,deflate=True);self.doc.close()
  print(json.dumps({'file':str(outpath),'gradient_shadings':len(self.shadings),'paths_cached':len(self.path_cache)}),flush=True)

if __name__=='__main__':
 B=Path(__file__).resolve().parent;O=B/'PD2027_Refined_Vector';mm=72/25.4
 for source,output in [(O/'PD2027_Refined_Vector_Print.svg',O/'PD2027_Refined_Print_210x280mm.pdf'),(B/'tmp/large.svg',O/'PD2027_Refined_Print_600x800mm.pdf')]:Renderer(source).save(output)
 doc=fitz.open(O/'PD2027_Refined_Print_210x280mm.pdf');p=doc[0]
 assert not p.get_images(full=True);assert not p.get_fonts(full=True)
 p.get_pixmap(dpi=150,clip=p.trimbox,alpha=False).save(O/'PD2027_Refined_Preview.png')
 p.get_pixmap(dpi=300,clip=p.trimbox,alpha=False).save(B/'tmp/print_300dpi.png')
 for label,box in [('Roof_detail',(109,75,207,156)),('Stone_detail',(77,214,199,252)),('Logo_detail',(109,257,201,273))]:p.get_pixmap(dpi=300,clip=fitz.Rect(*[(v+3)*mm for v in box]),alpha=False).save(O/(label+'.png'))
 print('Render complete',flush=True)
