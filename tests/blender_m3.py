import bpy
from mathutils import Vector
from projection_study import runtime, target_raycast
from projection_study.operators import aim
# Wide wall at world Y=10, facing default projector at origin.
mesh=bpy.data.meshes.new('test wall')
mesh.from_pydata([(-20,10,-20),(20,10,-20),(20,10,20),(-20,10,20)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Test wall',mesh)
bpy.context.scene.collection.objects.link(wall)
bpy.ops.ps.add()
o=bpy.context.object
bpy.context.view_layer.update()
target_raycast.invalidate()
runtime.refresh(True)
r=runtime.CACHE[o.as_pointer()]
assert r['hit'] is not None
assert abs(r['metrics'].distance-10)<1e-5
assert abs(r['metrics'].width-10)<1e-5
o.ps.shift_h=20
bpy.context.view_layer.update()
runtime.refresh(True)
r=runtime.CACHE[o.as_pointer()]
assert abs(r['hit'][0].x-2)<1e-5
assert abs(r['metrics'].distance-10)<1e-5
assert r['slant']>10
assert aim(o,Vector((0,10,0)))
bpy.context.view_layer.update()
runtime.refresh(True)
assert (runtime.CACHE[o.as_pointer()]['hit'][0]-Vector((0,10,0))).length<1e-4
wall.location.y=5
bpy.context.view_layer.update()
runtime.refresh(True)
assert runtime.CACHE[o.as_pointer()]['metrics'].distance>14
print('MILESTONE 3 PASS')
