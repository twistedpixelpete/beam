import bpy
from projection_study import runtime
from projection_study.projection_math import calculate
bpy.ops.ps.add()
o=bpy.context.object
o.ps.preview_distance=10
o.ps.shift_h=20
o.ps.shift_v=30
bpy.context.view_layer.update()
runtime.refresh(True)
m=runtime.CACHE[o.as_pointer()]['metrics']
assert abs(m.width-10)<1e-6 and abs(m.height-5.625)<1e-6
cam=runtime.optics(o)
bpy.context.scene.render.resolution_x=1920
bpy.context.scene.render.resolution_y=1080
frame=cam.data.view_frame(scene=bpy.context.scene)
points=[v*(-10/v.z) for v in frame]
assert abs(max(v.x for v in points)-7)<1e-5
assert abs(max(v.y for v in points)-4.5)<1e-5
assert abs(calculate(10,1,1920,1200).height-6.25)<1e-8
print('MILESTONE 2 PASS')
