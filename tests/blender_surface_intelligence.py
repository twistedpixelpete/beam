"""End-to-end observer, export, stale/display invariants and 12 workload matrix."""
import bpy,sys,math,json,time,platform
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,analysis_runtime,runtime,study_reporting,observer
from projection_study.utils import new_uuid
out=root/'examples/surface-intelligence';out.mkdir(parents=True,exist_ok=True)
addon.register();c=bpy.context;s=c.scene.ps_study
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
def mesh(name,verts,faces):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);c.scene.collection.objects.link(o);o['beam_receiver_uuid']=new_uuid();return o
wall=mesh('Flat Receiver',[(-4,10,0),(4,10,0),(4,10,4),(-4,10,4)],[(0,1,2,3)])
p=projector_object.create(c);p.matrix_world=Matrix.Rotation(math.pi/2,4,'X');p.location=(0,0,2);p.ps.resolution_x=2000;p.ps.resolution_y=1000;p.ps.lumens=20000
bpy.ops.beam.add_observer();eye=s.analysis_observer;eye.location=(0,-5,0);eye.beam_observer.eye_height=2
s.analysis_receiver=wall;s.analysis_detail='512'
def run(objects=[p],count=512):
 c.view_layer.update();runtime.refresh(True);return analysis_runtime.analyse(c,wall,objects,count)
r=run();assert r['observer']['name']=='OBS01';assert r['statistics']['acuity_evaluated_area_m2']>31
assert r['statistics']['acuity_max_arcmin']<1.2
# Higher raster density reduces angular pixel pitch; farther Observer reduces it.
a=r['statistics']['acuity_average_arcmin'];p.ps.resolution_x*=2;p.ps.resolution_y*=2
r=run();assert .49<r['statistics']['acuity_average_arcmin']/a<.51
p.ps.resolution_x//=2;p.ps.resolution_y//=2;eye.location.y=-20
r=run();assert r['statistics']['acuity_average_arcmin']<a
# Coarser overlapping source governs apparent pixel structure, not best-density source.
eye.location.y=-5;q=projector_object.create(c);q.matrix_world=p.matrix_world.copy();q.ps.resolution_x=1000;q.ps.resolution_y=500
r=run([p,q]);assert r['statistics']['acuity_average_arcmin']>1.9*a
assert all(x['acuity_projector_uuid']==q.ps.uuid for x in r['samples'] if x['observer_visible'])
bpy.data.objects.remove(q,do_unlink=True);r=run()
copy=eye.copy();c.scene.collection.objects.link(copy);runtime.refresh(True);assert copy.beam_observer.uuid!=eye.beam_observer.uuid
bpy.data.objects.remove(copy,do_unlink=True)
p.ps.lumens*=2;c.view_layer.update();runtime.refresh();assert analysis_runtime.stale(r,'ILLUMINANCE') and not analysis_runtime.stale(r,'DISTANCE')
r=run();eye.beam_observer.threshold=2;assert analysis_runtime.stale(r,'ACUITY') and not analysis_runtime.stale(r,'ILLUMINANCE')
r=run();eye.location.x=1;c.view_layer.update();assert analysis_runtime.stale(r,'ACUITY')
r=run();s.illuminance_scale='FIXED';s.illuminance_max=1000;s.use_target_illuminance=True;s.target_illuminance=300
assert not analysis_runtime.stale(r,'ILLUMINANCE');assert r['display']['target_illuminance_lux']==300
p.ps.show_frustum=False;c.view_layer.update();runtime.refresh();assert not analysis_runtime.stale(r,'DENSITY')
# A blocker behind projector but ahead of observer blocks viewing, not light.
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,-2,2));block=c.object;block.scale=(10,.1,10)
r=run();assert r['statistics']['illuminance_min_lux']>0;assert r['statistics']['acuity_evaluated_area_m2']==0
bpy.data.objects.remove(block,do_unlink=True)
r=run();study_reporting.validate(study_reporting.document(c))
# Persistent empty observer and enum values survive reopening; caches must not.
s.active_projector=p;s.analysis_mode='ACUITY';bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/surface-intelligence-roundtrip.blend'))
bpy.ops.wm.open_mainfile(filepath=str(root/'work/surface-intelligence-roundtrip.blend'));c=bpy.context;s=c.scene.ps_study
assert s.analysis_mode=='ACUITY' and s.analysis_observer.beam_observer.threshold==2
assert not analysis_runtime.CACHE
p=s.active_projector;wall=s.analysis_receiver;eye=s.analysis_observer
# Workload shares samples/visibility across every mode, so one solve is the cost for all five.
report={'blender':bpy.app.version_string,'platform':platform.platform(),'method':'One explicit shared solve computes all five metrics; identical solve cost for each selectable mode. CPU, GPU batch build excluded.','runs':[]}
objects=[p]
for count in (1,3,16,32):
 while len(objects)<count:
  q=projector_object.create(c);q.matrix_world=p.matrix_world.copy();q.location.x=(len(objects)%3-1)*.1;objects.append(q)
 for budget in (512,2048,8192):
  c.view_layer.update();t=time.perf_counter();r=analysis_runtime.analyse(c,wall,objects,budget);elapsed=time.perf_counter()-t
  assert r['statistics']['sample_count']==budget
  report['runs'].append(dict(projectors=count,samples=budget,shared_solve_seconds=elapsed,mode_seconds={mode:elapsed for mode in ('DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY')}))
  (out/'performance.json').write_text(json.dumps(report,indent=2));print('BENCH',count,budget,elapsed,flush=True)
# Dedicated multi-geometry fixture. Keep three projectors, place two additional receiver shapes outside flat area.
for q in objects[3:]:bpy.data.objects.remove(q,do_unlink=True)
for i,q in enumerate(objects[:3]):q.location.x=(-3,0,3)[i];q.ps.lumens=20000;q.ps.throw_ratio=.7
mesh('Angled Receiver',[(-8,9,0),(-4.5,11,0),(-4.5,11,4),(-8,9,4)],[(0,1,2,3)])
verts=[];faces=[]
for i in range(17):
 x=4.5+4*i/16;y=10+.8*math.sin(i*math.pi/16);verts.extend([(x,y,0),(x,y,4)])
for i in range(16):faces.append((i*2,i*2+2,i*2+3,i*2+1))
mesh('Curved Receiver',verts,faces)
mesh('Stepped Receiver',[(-3,12,4),(-1,12,4),(-1,12,5),(-3,12,5),(0,13,4),(2,13,4),(2,13,5),(0,13,5)],[(0,1,2,3),(4,5,6,7)])
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,6,1.5));c.object.name='Movable Occluder';c.object.scale=(.4,.15,1.5)
eye.location=(0,-5,0);eye.beam_observer.threshold=1;eye.beam_observer.eye_height=1.6
for selected in c.selected_objects:selected.select_set(False)
objects[1].select_set(True);c.view_layer.objects.active=objects[1];s.active_projector=objects[1]
s.analysis_detail='2048';s.reverse_receiver=wall
s.analysis_mode='ILLUMINANCE';s.display_units='m';s.project_name='Beam Surface Intelligence';s.author='Twisted Pixel'
c.view_layer.update();r=analysis_runtime.analyse(c,wall,objects[:3],2048)
data=study_reporting.document(c);study_reporting.validate(data);(out/'fixture-analysis.json').write_text(json.dumps(data,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Surface-Intelligence.blend'))
print('SURFACE INTELLIGENCE INTEGRATION PASS')
addon.unregister()
