import bpy
from projection_study import operators, runtime
bpy.ops.ps.add()
o=bpy.context.object
o.ps.resolution_x=1920; o.ps.resolution_y=1200
bpy.context.view_layer.update(); runtime.refresh(True)
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
scene=bpy.context.scene
before=(scene.render.resolution_x,scene.render.resolution_y,scene.render.pixel_aspect_x,scene.render.pixel_aspect_y)
with bpy.context.temp_override(area=area,region=region):
    assert bpy.ops.ps.look('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
    assert area.spaces.active.region_3d.view_perspective=='CAMERA'
    assert scene.render.resolution_y==1200
    operators.restore_views()
    assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.pixel_aspect_x,scene.render.pixel_aspect_y)==before
    assert not operators._view_sessions
print('MILESTONE 8 camera-view restoration PASS')
