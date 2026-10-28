"""CPU-generated, packed test patterns usable by background Cycles renders."""
import hashlib
import json
import tempfile
from pathlib import Path
import bpy
import numpy as np


def ensure(p, identifiers=True):
    key=json.dumps((p.output_mode,p.resolution_x,p.resolution_y,tuple(p.colour),p.identifier,identifiers,p.show_grid))
    name='.Beam Render '+hashlib.sha256(key.encode()).hexdigest()[:20]
    existing=bpy.data.images.get(name)
    if existing and existing.get('beam_render_pattern'):return existing
    width=min(2048,p.resolution_x);height=max(1,round(width*p.resolution_y/p.resolution_x))
    if height>2048:width=max(1,round(width*2048/height));height=2048
    u=(np.arange(width,dtype=np.float32)+.5)/width;v=(np.arange(height,dtype=np.float32)+.5)/height
    x,y=np.meshgrid(u,v);alpha=np.zeros((height,width),np.float32)
    aspect=p.resolution_y/p.resolution_x
    nx=16;ny=max(2,round(16*aspect))
    if p.output_mode=='SOLID':alpha[:]=1
    elif p.output_mode=='CHECKER':alpha=((np.floor(x*nx)+np.floor(y*ny))%2==0).astype(np.float32)
    elif p.output_mode=='GRID' and p.show_grid:
        grid=(np.abs((x*nx+.5)%1-.5)<max(.008,.6*nx/width))|(np.abs((y*ny+.5)%1-.5)<max(.008,.6*ny/height))
        edge=np.minimum(np.minimum(x,1-x),np.minimum(y,1-y)*aspect)<.006
        diagonal=(abs(x-y)<max(.0005,.5/width))|(abs(x+y-1)<max(.0005,.5/width))
        cross=((abs(x-.5)<.002)&(abs(y-.5)<.07))|((abs(y-.5)<.002)&(abs(x-.5)<.04))
        alpha=np.maximum(grid.astype(np.float32)*.8,(edge|diagonal|cross).astype(np.float32))
    if identifiers or (p.output_mode=='GRID' and p.show_grid):
        import blf,imbuf
        buffer=imbuf.new((width,height))
        try:
            with blf.bind_imbuf(0,buffer):
                def label(text,at,size):
                    blf.size(0,size);w,h=blf.dimensions(0,text)
                    if w>width*.85:blf.size(0,size*width*.85/w);w,h=blf.dimensions(0,text)
                    blf.color(0,1,1,1,1);blf.position(0,(width-w)/2,height*at-h/2,0);blf.draw_buffer(0,text)
                if identifiers:label(p.identifier,.68 if p.output_mode=='GRID' else .5,height*.14)
                if p.output_mode=='GRID':label(f'{p.resolution_x} × {p.resolution_y}',.09,height*.045)
            with tempfile.TemporaryDirectory(prefix='beam-pattern-') as folder:
                path=str(Path(folder)/'text.png');imbuf.write(buffer,filepath=path)
                text=bpy.data.images.load(path,check_existing=False)
                try:
                    values=np.empty(width*height*4,np.float32);text.pixels.foreach_get(values)
                    alpha=np.maximum(alpha,values.reshape(height,width,4)[:,:,3])
                finally:bpy.data.images.remove(text)
        finally:buffer.free()
    pixels=np.zeros((height,width,4),np.float32);pixels[:,:,:3]=tuple(p.colour);pixels[:,:,3]=alpha
    image=bpy.data.images.new(name,width=width,height=height,alpha=True,float_buffer=True)
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(pixels.ravel());image.update();image.pack()
    image['beam_render_pattern']=True
    return image


def black():
    name='.Beam Render Missing Image'
    image=bpy.data.images.get(name)
    if image is None or not image.get('beam_render_pattern'):
        image=bpy.data.images.new(name,width=1,height=1,alpha=True,float_buffer=True)
        image.pixels[:]=(0,0,0,0);image.pack();image['beam_render_pattern']=True
    return image
