"""Subtle nominal-plane intersection overlays; not a dense surface analysis."""
import bpy,gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from . import blend_groups,typography

_shader=None

def pairs():
    from .viewport_display import isolate_uuid
    for group in bpy.context.scene.ps_study.blend_groups:
        if not group.show_overlap or (blend_groups.solo_uuid and blend_groups.solo_uuid!=group.uuid): continue
        if isolate_uuid: continue
        for pair in blend_groups.pair_data(group,bpy.context):
            if len(pair['polygon'])>=3: yield group,pair

def draw():
    global _shader
    if _shader is None: _shader=gpu.shader.from_builtin('UNIFORM_COLOR')
    shader=_shader
    gpu.state.blend_set('ALPHA'); gpu.state.depth_test_set('NONE'); gpu.state.depth_mask_set(False)
    for group,pair in pairs():
        points=pair['polygon']
        batch=batch_for_shader(shader,'TRIS',{'pos':points},indices=[(0,i,i+1) for i in range(1,len(points)-1)])
        shader.bind(); shader.uniform_float('color',(.6,.72,.68,.14)); batch.draw(shader)
    gpu.state.blend_set('NONE'); gpu.state.depth_mask_set(True)

def labels(projection,width,height):
    for group,pair in pairs():
        projected=[]
        for point in pair['polygon']:
            clip=projection@Vector((*point,1))
            if clip.w>0: projected.append(((clip.x/clip.w+1)*width/2,(clip.y/clip.w+1)*height/2))
        if not projected: continue
        x=sum(p[0] for p in projected)/len(projected)
        y=max(p[1] for p in projected)+40
        typography.label(f"{group.name} · {pair['a']}/{pair['b']} · {pair['actual']['pixels']:.0f} px",x-60,y,14,(.6,.72,.68,1))
