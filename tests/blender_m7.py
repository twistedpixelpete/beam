exec((root/'tests/blender_m3.py').read_text())
import time
from projection_study.projector_object import create, projectors
from projection_study.export_disguise import rows_for_scene
from projection_study.projection_math import image_point
from mathutils import Matrix
# Metric scene scales: 1 Blender unit = 1 mm.
bpy.context.scene.unit_settings.scale_length=.001
o.ps.shift_h=0; o.rotation_euler=(1.5707963267948966,0,0)
wall.location.y=9990
bpy.context.view_layer.update(); target_raycast.invalidate(); runtime.refresh(True)
assert abs(runtime.CACHE[o.as_pointer()]['metrics'].distance-10)<1e-4
assert abs(rows_for_scene(bpy.context)[0][19]-10000)<.01
# Portrait camera view_frame matches full-image shift definition.
p=o.ps; p.resolution_x=1080; p.resolution_y=1920; p.shift_v=35
scene=bpy.context.scene
scene.render.resolution_x=p.resolution_x; scene.render.resolution_y=p.resolution_y
runtime.refresh(True)
points=[v*(-10/v.z) for v in runtime.optics(o).data.view_frame(scene=scene)]
assert abs(max(v.y for v in points)-image_point(1,1,10,1,1080,1920,0,35)[1])<1e-4
# Save/load through an isolated library file, without replacing current user file.
p.colour=(.31,.42,.57)
identity=p.uuid
path=str(root/'work/persistence-test.blend')
bpy.data.libraries.write(path,{scene})
with bpy.data.libraries.load(path,link=False) as (src,dst): dst.scenes=[scene.name]
loaded=dst.scenes[0]
try:
    q=next(obj.ps for obj in loaded.objects if obj.ps.is_projector)
    assert q.uuid==identity and tuple(q.colour)==tuple(p.colour)
finally:
    for obj in list(loaded.objects): bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(loaded)
# Benchmark cached receiver queries and transforms, excluding GPU draw time.
scene.unit_settings.scale_length=1; wall.location.y=0
p.resolution_x=1920; p.resolution_y=1080; p.shift_v=0
for i in range(31): create(bpy.context,o)
bpy.context.view_layer.update(); target_raycast.invalidate(); runtime.refresh(True)
samples=[]
for i in range(20):
    start=time.perf_counter()
    for obj in projectors(scene): obj.location.x += .0001
    bpy.context.view_layer.update(); runtime.refresh()
    samples.append((time.perf_counter()-start)*1000)
print('32-projector CPU update mean ms:',sum(samples)/len(samples))
assert runtime.refresh() is False
print('MILESTONE 7 persistence / units / portrait / performance PASS')
