"""Independent analytic checks against evaluated ray casts, no GPU required."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,analysis_runtime,runtime
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
p=projector_object.create(c);p.matrix_world=Matrix.Rotation(math.pi/2,4,'X');p.ps.resolution_x=2000;p.ps.resolution_y=1000;p.ps.lumens=20000
mesh=bpy.data.meshes.new('Plane');wall=bpy.data.objects.new('Plane',mesh);c.scene.collection.objects.link(wall)
mesh.from_pydata([(-4,10,-2),(4,10,-2),(4,10,2),(-4,10,2)],[],[(0,1,2,3)]);mesh.update()
def run(objects=[p]):
 c.view_layer.update();runtime.invalidate();return analysis_runtime.analyse(c,wall,objects,512)
r=run();assert abs(r['statistics']['illuminance_average_lux']-400)<.001
for s in r['samples']:assert abs(s['distance_m']-math.sqrt(sum(x*x for x in (s['point'][0],10,s['point'][2]))))<1e-5
p.ps.lumens=40000;assert abs(run()['statistics']['illuminance_average_lux']-800)<.001
p.ps.lumens=20000;p.ps.stack=2;assert abs(run()['statistics']['illuminance_average_lux']-800)<.001;p.ps.stack=1
q=projector_object.create(c);q.matrix_world=p.matrix_world;q.ps.resolution_x=2000;q.ps.resolution_y=1000;q.ps.lumens=17500
assert abs(run([p,q])['statistics']['illuminance_average_lux']-750)<.001
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,5,0));block=c.object;block.scale=(10,.1,10)
r=run([p,q]);assert r['statistics']['illuminance_max_lux']==0;assert r['statistics']['distance_min_m'] is None
bpy.data.objects.remove(block,do_unlink=True)
a=run();b=run();assert a['samples']==b['samples']
# Analytic tilted receiver: E = flux * ratio² * aspect * |n·delta| / axial_depth³.
wall.rotation_euler.z=math.radians(30)
r=run();normal=wall.matrix_world.to_3x3() @ __import__('mathutils').Vector((0,-1,0))
for sample in r['samples']:
 if not sample['visible']:continue
 point=sample['position_m'];depth=point[1]
 expected=20000*2*abs(sum(normal[i]*point[i] for i in range(3)))/depth**3
 assert abs(sample['illuminance_lux']-expected)<.01,(sample['illuminance_lux'],expected)
 assert abs(sample['distance_m']-math.sqrt(sum(v*v for v in point)))<1e-5
wall.rotation_euler.z=0
for label,verts,faces in [
 ('stepped',[(-3,8,-1),(0,8,-1),(0,8,1),(-3,8,1),(0,10,-1),(3,10,-1),(3,10,1),(0,10,1)],[(0,1,2,3),(4,5,6,7)]),
 ('curved',[(x,8+.1*x*x,z) for x in (-3,-2,-1,0,1,2,3) for z in (-1,1)],[(i*2,i*2+2,i*2+3,i*2+1) for i in range(6)])]:
 mesh.clear_geometry();mesh.from_pydata(verts,[],faces);mesh.update();r=run()
 for sample in r['samples']:
  if sample['visible']:assert abs(sample['distance_m']-math.sqrt(sum(v*v for v in sample['position_m'])))<1e-5,label
 assert r['statistics']['distance_variation_m']>0
print('SURFACE INTELLIGENCE A/B: PASS (flat, radial distance, lumens, stack, additive overlap, blocked, deterministic)')
addon.unregister()
