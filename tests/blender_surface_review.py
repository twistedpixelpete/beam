import bpy,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import projection_study as addon
from projection_study import projector_object,analysis_runtime,runtime
from mathutils import Matrix
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
p=projector_object.create(c);p.matrix_world=Matrix.Rotation(math.pi/2,4,'X')
bpy.ops.mesh.primitive_plane_add(size=4,location=(0,10,0),rotation=(math.pi/2,0,0));wall=c.object
collection=bpy.data.collections.new('blocker collection')
bpy.ops.mesh.primitive_cube_add(size=2);block=c.object
for col in list(block.users_collection):col.objects.unlink(block)
collection.objects.link(block)
inst=bpy.data.objects.new('blocking instance',None);c.scene.collection.objects.link(inst);inst.instance_type='COLLECTION';inst.instance_collection=collection;inst.location=(10,5,0)
c.view_layer.update();r=analysis_runtime.analyse(c,wall,[p],512)
inst.location.x=0;c.view_layer.update();runtime.refresh()
assert r['stale'], 'Moving instanced occluder must invalidate cached analysis'
r2=analysis_runtime.analyse(c,wall,[p],512)
assert r['statistics']['coverage_percent']==100 and r2['statistics']['coverage_percent']==0
print('SURFACE REVIEW PASS: collection-instance occlusion invalidation')
addon.unregister()
