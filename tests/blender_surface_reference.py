"""Beam counterparts to the authenticated Mapping Matter photometric controls."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,analysis_runtime,runtime
from projection_study.utils import new_uuid
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
height=6*1528/2716;m=bpy.data.meshes.new('MM receiver');m.from_pydata([(-3,0,-height/2),(3,0,-height/2),(3,0,height/2),(-3,0,height/2)],[],[(0,1,2,3)]);m.update()
wall=bpy.data.objects.new('MM equivalent receiver',m);c.scene.collection.objects.link(wall);wall.location=(0,6,1.6875);wall['beam_receiver_uuid']=new_uuid()
def projector(x):
 p=projector_object.create(c);p.matrix_world=Matrix.Rotation(math.pi/2,4,'X');p.location=(x,0,1.6875);p.ps.resolution_x=2716;p.ps.resolution_y=1528;p.ps.lumens=10000;return p
p=projector(0)
def run(objects):
 c.view_layer.update();runtime.invalidate();return analysis_runtime.analyse(c,wall,objects,8192)
report={};r=run([p]);report['flat']=r['statistics'];assert abs(report['flat']['illuminance_average_lux']-10000/(6*height))<.01
wall.rotation_euler.z=math.pi/6;r=run([p]);report['angled']=r['statistics'];report['angled_centre_analytic_lux']=10000/(6*height)*math.cos(math.pi/6)
wall.rotation_euler.z=0;q=projector(.5);r=run([p,q]);report['overlap']=r['statistics'];assert abs(report['overlap']['illuminance_max_lux']-20000/(6*height))<.01
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,3,1.6875));r=run([p,q]);report['occluder']=r['statistics'];assert report['occluder']['illuminance_min_lux']==0
bpy.ops.beam.add_observer();eye=c.scene.ps_study.analysis_observer;eye.location=(0,-5,0);eye.beam_observer.eye_height=1.65
bpy.data.objects.remove(c.scene.objects.get('Cube'),do_unlink=True)
r=run([p]);report['observer']=r['statistics']
out=root/'examples/surface-intelligence';(out/'reference/beam-counterparts.json').write_text(json.dumps(report,indent=2))
print('PASS Mapping Matter counterpart fixtures: flat, tilted, overlap, shadow, Observer')
addon.unregister()
