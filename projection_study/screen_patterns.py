"""Packed orientation test charts; no pixel geometry or external dependencies."""
import bpy,json
import numpy as np
from .output_patterns import FONT

GLYPHS=dict(FONT)
GLYPHS.update({
'S':['01111','10000','10000','01110','00001','00001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'.':['00000','00000','00000','00000','00000','00100','00100'],
'>':['10000','01000','00100','00010','00100','01000','10000'],
'^':['00100','01010','10001','00000','00000','00000','00000'],
})


def apply(obj):
    p=obj.beam_screen;m=json.loads(p.metrics);rx=m.get('rx',p.resolution_x);ry=m.get('ry',p.resolution_y)
    w=1536;h=max(256,min(1536,round(w*ry/rx)));a=np.empty((h,w,4),dtype=np.float32);a[:]=(.035,.04,.05,1)
    def line(x0,y0,x1,y1,c,thick=2):
        a[max(0,int(y0)):min(h,int(y1)+thick),max(0,int(x0)):min(w,int(x1)+thick)]=c
    def text(s,x,y,scale=3,c=(.9,.92,.95,1)):
        for i,ch in enumerate(s.upper()):
            for row,bits in enumerate(GLYPHS.get(ch,GLYPHS[' '])):
                for col,bit in enumerate(bits):
                    if bit=='1':line(x+(i*6+col)*scale,y+(6-row)*scale,x+(i*6+col)*scale,y+(6-row)*scale,c,scale)
    for i in range(17):line(i*(w-3)/16,0,i*(w-3)/16,h-1,(.17,.2,.23,1))
    for j in range(9):line(0,j*(h-3)/8,w-1,j*(h-3)/8,(.17,.2,.23,1))
    for x in (1,w-5):line(x,1,x,h-3,(.8,.83,.86,1),4)
    for y in (1,h-5):line(1,y,w-3,y,(.8,.83,.86,1),4)
    line(w/2,0,w/2,h-1,(.55,.65,.65,1),3);line(0,h/2,w-1,h/2,(.55,.65,.65,1),3)
    for x in (.25,.75):
        for y in (.25,.75):line(x*w-10,y*h,x*w+10,y*h,(.7,.7,.7,1));line(x*w,y*h-10,x*w,y*h+10,(.7,.7,.7,1))
    if p.category=='LED':
        for i in range(1,p.columns):line(i*w/p.columns,0,i*w/p.columns,h-1,(.25,.38,.3,1),1)
        for j in range(1,p.rows):line(0,j*h/p.rows,w-1,j*h/p.rows,(.25,.38,.3,1),1)
        if p.columns<=30 and p.rows<=20:
            for j in range(p.rows):
                for i in range(p.columns):text(str(j*p.columns+i+1),int((i+.2)*w/p.columns),int((j+.2)*h/p.rows),1)
    text('BL 0 0',20,20,3,(.9,.4,.32,1));text(f'BR {rx} 0',w-330,20,3,(.35,.7,.4,1))
    text(f'TL 0 {ry}',20,h-45,3,(.35,.55,.9,1));text(f'TR {rx} {ry}',w-400,h-45,3,(.8,.7,.35,1))
    text(p.identifier,w//2-len(p.identifier)*15,h*3//4,5)
    text(f'{rx} X {ry}',w//2-150,h//4,3)
    text('U >',w//2+25,h//2+15,3);text('V ^',w//2-90,h//2+55,3)
    text(f'{m.get("width",0):.2f} M',w//2-110,65,3)
    old=bpy.data.materials.get('.Beam Pattern '+p.uuid)
    image=next((n.image for n in old.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if old and old.use_nodes else None
    if image is None:image=bpy.data.images.new('.Beam Chart '+p.uuid,width=w,height=h)
    elif tuple(image.size)!=(w,h):image.scale(w,h)
    image.pixels.foreach_set(a.ravel());image.pack();image['beam_screen_pattern']=True
    mat=old or bpy.data.materials.new('.Beam Pattern '+p.uuid);mat.use_nodes=True;mat['beam_screen_pattern']=True
    nodes=mat.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear'
    mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],output.inputs['Surface'])
    obj.data.materials.clear();obj.data.materials.append(mat)
    for face in obj.data.polygons:face.material_index=0
    return image
