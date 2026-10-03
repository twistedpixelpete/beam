"""Use Blender's bundled Inter sans-serif. No Apple fonts or external install."""
from pathlib import Path
import bpy
import blf
import gpu
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

_plate_shader=None

_font=None
_textures={}


def font():
    global _font
    if _font is None:
        path=Path(bpy.utils.system_resource('DATAFILES',path='fonts'))/'Inter.woff2'
        _font=blf.load(str(path)) if path.exists() else 0
        if _font<0: _font=0
    return _font


def pixel_matrix(width,height):
    return Matrix(((2/width,0,0,-1),(0,2/height,0,-1),(0,0,1,0),(0,0,0,1)))


def rectangle(x,y,w,h,colour):
    global _plate_shader
    if _plate_shader is None: _plate_shader=gpu.shader.from_builtin('UNIFORM_COLOR')
    shader=_plate_shader
    batch=batch_for_shader(shader,'TRIS',{'pos':[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]},indices=[(0,1,2),(0,2,3)])
    shader.bind(); shader.uniform_float('color',colour); batch.draw(shader)


def label(text,x,y,size,colour,active=False):
    f=font(); blf.size(f,size)
    width,height=blf.dimensions(f,text)
    gpu.state.blend_set('ALPHA'); gpu.state.depth_test_set('NONE')
    padding=max(5,size*.3)
    rectangle(x-padding,y-padding,width+2*padding,height+2*padding,(.025,.03,.04,.88 if active else .76))
    rectangle(x-padding,y-padding,max(2,size*.13),height+2*padding,colour)
    blf.color(f,.97,.98,1,1)
    # A subpixel second pass gives the bundled sans-serif a medium appearance.
    for offset in (0,.35):
        blf.position(f,x+offset,y,0); blf.draw(f,text)



def annotation(text,x,y,size=12,alpha=.65,align='LEFT'):
    """Neutral screen-space measurement text, without a plate or colour stripe."""
    f=font();blf.size(f,max(11,min(14,size)))
    gpu.state.blend_set('ALPHA');gpu.state.depth_test_set('NONE')
    width=blf.dimensions(f,text)[0]
    if align=='CENTER':x-=width/2
    elif align=='RIGHT':x-=width
    blf.color(f,.88,.90,.93,alpha)
    blf.position(f,x,y,0);blf.draw(f,text)


def texture(identifier,rx,ry,mode,colour,show_identifier=True):
    key=(identifier,rx,ry,mode,tuple(colour),show_identifier)
    if key in _textures: return _textures[key].texture_color
    # Bounded cache; only rebuilt for typography/resolution changes.
    if len(_textures)>=128:
        _,old=_textures.popitem(); old.free()
    width=1536; height=max(256,min(2048,round(width*ry/rx)))
    off=gpu.types.GPUOffScreen(width,height)
    viewport=gpu.state.viewport_get()
    with off.bind(),gpu.matrix.push_pop(),gpu.matrix.push_pop_projection():
        gpu.state.viewport_set(0,0,width,height)
        gpu.state.active_framebuffer_get().clear(color=(0,0,0,0))
        gpu.matrix.load_matrix(Matrix.Identity(4)); gpu.matrix.load_projection_matrix(pixel_matrix(width,height))
        gpu.state.depth_test_set('NONE'); gpu.state.blend_set('ALPHA')
        f=font()
        def centred(text,y,size):
            blf.size(f,size)
            w,h=blf.dimensions(f,text)
            if w>width*.85:
                size=size*width*.85/w
                blf.size(f,size); w,h=blf.dimensions(f,text)
            # Projected text is part of the raster, not a viewport UI badge.
            blf.color(f,1,1,1,1)
            for offset in (0,.35):
                blf.position(f,(width-w)/2+offset,y-h/2,0); blf.draw(f,text)
        if show_identifier: centred(identifier,height*(.68 if mode=='GRID' else .5),height*.14)
        if mode=='GRID': centred(f'{rx} × {ry}',height*.09,height*.045)
        gpu.state.blend_set('NONE')
    gpu.state.viewport_set(*viewport)
    _textures[key]=off
    return off.texture_color


def clear():
    global _font,_plate_shader
    _plate_shader=None
    for off in _textures.values(): off.free()
    _textures.clear()
    if _font not in (None,0): blf.unload(_font)
    _font=None
