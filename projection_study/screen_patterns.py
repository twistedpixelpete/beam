"""Beam Clean screen chart, packed with Blender's bundled sans-serif typography.

CPU rasterization also works in background Blender. This is display content only;
no geometry, UVs, screen parameters or production export are changed.
"""
import json
import tempfile
from pathlib import Path
import bpy
import blf
import imbuf
import numpy as np
from . import typography


def text_layer(width,height,labels):
    """Rasterize BLF text without requiring a GPU or a platform-specific font."""
    buffer=imbuf.new((width,height))
    font=typography.font()
    try:
        with blf.bind_imbuf(font,buffer):
            for text,x,y,size,colour,align in labels:
                blf.size(font,size)
                extent=blf.dimensions(font,text)[0]
                if align=='CENTER':x-=extent/2
                elif align=='RIGHT':x-=extent
                blf.color(font,*colour);blf.position(font,x,y,0)
                blf.draw_buffer(font,text)
        if hasattr(buffer,'with_buffer'):
            with buffer.with_buffer() as pixels:
                return np.asarray(pixels,dtype=np.float32).copy()/255
        # Blender 4.5 has BLF image drawing but no Python pixel-buffer accessor.
        with tempfile.TemporaryDirectory(prefix='beam-type-') as directory:
            path=str(Path(directory)/'type.png');imbuf.write(buffer,filepath=path)
            image=bpy.data.images.load(path,check_existing=False)
            try:
                pixels=np.empty(width*height*4,dtype=np.float32)
                image.pixels.foreach_get(pixels)
                return pixels.reshape(height,width,4)
            finally:bpy.data.images.remove(image)
    finally:buffer.free()


def apply(obj):
    p=obj.beam_screen;m=json.loads(p.metrics);rx=m.get('rx',p.resolution_x);ry=m.get('ry',p.resolution_y)
    w=1536;h=max(256,min(1536,round(w*ry/rx)))
    a=np.empty((h,w,4),dtype=np.float32);a[:]=(.055,.064,.075,1)
    labels=[]
    def line(x0,y0,x1,y1,c,thick=1):
        a[max(0,int(y0)):min(h,int(y1)+thick),max(0,int(x0)):min(w,int(x1)+thick)]=(*c,1)
    def text(value,x,y,size,colour=(.9,.92,.94),align='CENTER'):
        labels.append((value,x,y,size,(*colour,1),align))
    # Quiet minor grid, clearer major divisions, and a precise outer boundary.
    for i in range(1,16):line(i*w/16,0,i*w/16,h-1,(.105,.12,.135))
    for j in range(1,8):line(0,j*h/8,w-1,j*h/8,(.105,.12,.135))
    for i in (4,8,12):line(i*w/16,0,i*w/16,h-1,(.21,.24,.27))
    for j in (2,4,6):line(0,j*h/8,w-1,j*h/8,(.21,.24,.27))
    for x in (3,w-5):line(x,3,x,h-5,(.59,.64,.68),2)
    for y in (3,h-5):line(3,y,w-5,y,(.59,.64,.68),2)
    # Small centre cross and ring; no giant target or decorative colour blocks.
    yy,xx=np.ogrid[:h,:w];radius=max(9,min(18,h*.023))
    ring=np.abs(np.sqrt((xx-w/2)**2+(yy-h/2)**2)-radius)<.8
    a[ring]=(.48,.58,.6,1)
    line(w/2-28,h/2,w/2+28,h/2,(.63,.7,.72))
    line(w/2,h/2-28,w/2,h/2+28,(.63,.7,.72))
    # A quiet, centred title field gives typography breathing room over the grid.
    title_size=max(32,min(76,h*.095));small=max(17,min(28,h*.034))
    y=h*.74;half= min(w*.38,max(260,title_size*len(p.identifier)*.4))
    line(w/2-half,y-small*1.9,w/2+half,y+title_size*1.12,(.055,.064,.075))
    text(p.identifier,w/2,y,title_size)
    text(f"{m.get('width',0):.2f} × {m.get('height',0):.2f} m",w/2,y-small*1.5,small,(.64,.7,.74))
    # Resolution remains secondary; corner labels provide orientation references.
    footer=max(18,h*.09)
    line(w/2-220,footer-8,w/2+220,footer+small+6,(.055,.064,.075))
    text(f'{rx:,} × {ry:,} px',w/2,footer,small,(.57,.64,.68))
    margin=26;corner_size=max(14,min(20,h*.027))
    for label,x,y,align,colour in (
        ('TL',margin,h-margin-corner_size,'LEFT',(.5,.64,.75)),
        ('TR',w-margin,h-margin-corner_size,'RIGHT',(.72,.68,.52)),
        ('BL',margin,margin,'LEFT',(.7,.55,.53)),
        ('BR',w-margin,margin,'RIGHT',(.52,.68,.61))):
        text(label,x,y,corner_size,colour,align)
    layer=text_layer(w,h,labels);alpha=layer[:,:,3:4]
    a[:,:,:3]=layer[:,:,:3]*alpha+a[:,:,:3]*(1-alpha)
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
