"""One-click saved-view navigation and visibility, including restoration."""
import bpy
from projection_study import study_views
scene=bpy.context.scene
space=bpy.context.area.spaces.active; rv=space.region_3d
original=(scene.camera,rv.view_perspective,scene.render.resolution_x,scene.render.resolution_y,rv.view_location.copy(),rv.view_rotation.copy())
a=study_views.create_view(bpy.context,'First'); a.resolution_x=1200; a.resolution_y=800
b=study_views.create_view(bpy.context,'Second'); b.resolution_x=800; b.resolution_y=1200
assert bpy.ops.ps.view_study(index=0)=={'FINISHED'}
assert scene.camera==a.camera and rv.view_perspective=='CAMERA'
assert (scene.render.resolution_x,scene.render.resolution_y)==(1200,800)
assert bpy.ops.ps.view_study(action='NEXT')=={'FINISHED'}
assert scene.camera==b.camera and scene.ps_study.view_index==1
assert bpy.ops.ps.view_study(action='PREVIOUS')=={'FINISHED'}
assert scene.camera==a.camera
scene.ps_study.show_study_cameras=False
assert a.camera.hide_get() and b.camera.hide_get()
assert bpy.ops.ps.view_study(index=1)=={'FINISHED'}
assert scene.camera==b.camera
assert bpy.ops.ps.view_study(action='EXIT')=={'FINISHED'}
assert (scene.camera,rv.view_perspective,scene.render.resolution_x,scene.render.resolution_y)==original[:4]
assert (rv.view_location-original[4]).length<1e-5
assert rv.view_rotation.rotation_difference(original[5]).angle<1e-5
scene.ps_study.show_study_cameras=True
assert not a.camera.hide_get()
# Missing references fail without replacing the user's camera.
b.camera=None
assert bpy.ops.ps.view_study(index=1)=={'CANCELLED'}
assert scene.camera==original[0]
print('MILESTONE 13 view/next/previous/exit + hidden cameras + restoration PASS')
