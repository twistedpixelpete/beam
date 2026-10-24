"""Controlled live-MM CSV, evaluated-surface and constrained-optics acceptance."""
import sys,math,csv,json,tempfile,copy
from pathlib import Path
from types import SimpleNamespace
import bpy
from mathutils import Matrix,Euler,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,runtime,analysis_runtime,optics_validation,inverse_solver,auto_layout,study_reporting
from projection_study.export_disguise import rows_for_scene
from projection_study.export_table import HEADER,write_table
addon.register();c=bpy.context
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
mesh=bpy.data.meshes.new('Receiver');mesh.from_pydata([(-8,6,0),(8,6,0),(8,6,3.375),(-8,6,3.375)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Receiver',mesh);c.scene.collection.objects.link(wall)
wall['beam_receiver_uuid']='64e6f25d-1164-4d78-949f-2d26186e7ea0'
pj=projector_object.create(c);p=pj.ps
comparisons=[]
for fixture in sorted((root/'tests/fixtures/mapping_matter').glob('*.csv')):
    row=list(csv.DictReader(fixture.open()))[-1]
    p.resolution_x=int(row['Projector_Native-Rez-X']);p.resolution_y=int(row['Projector_Native-Rez-Y'])
    p.throw_ratio=float(row['Projector_Trow-Ratio']);p.shift_h=float(row['Lens_Shift-H(%)'])/2;p.shift_v=float(row['Lens_Shift-V(%)'])/2
    p.lumens=float(row['Projector_Lumens(lux)'])
    rotation=Euler(tuple(math.radians(float(row[k])) for k in ('Pitch(deg)','Roll(deg)','Yaw(deg)')),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X')
    matrix=rotation.to_4x4();matrix.translation=Vector(tuple(float(row[k])/1000 for k in ('Lens_X','Lens_Y','Lens_Z')));pj.matrix_world=matrix
    c.view_layer.update();runtime.refresh(True)
    exported=rows_for_scene(c)
    output=root/'work/parity/beam-csv';output.mkdir(parents=True,exist_ok=True)
    with (output/fixture.name).open('w') as handle:write_table(handle,exported)
    actual=dict(zip(HEADER,exported[0]));differences={}
    for key in ('Lens_X','Lens_Y','Lens_Z','Pitch(deg)','Yaw(deg)','Roll(deg)','Target_X','Target_Y','Target_Z','Target_Distance','Target_Width','Target_Height','Lens_Shift-H(%)','Lens_Shift-V(%)','Projector_Trow-Ratio','Projector_Native-Rez-X','Projector_Native-Rez-Y'):
        delta=float(actual[key])-float(row[key]);differences[key]=delta
        assert abs(delta)<.02,(fixture.name,key,actual[key],row[key])
    comparisons.append(dict(fixture=fixture.name,max_error=max(abs(v) for v in differences.values()),differences=differences))
# Flat reference: three projectors, 16 x 3.375 m, native 2716 x 1528.
p.shift_h=p.shift_v=0;p.throw_ratio=1
projectors=[pj]
for i in range(2):projectors.append(projector_object.create(c,pj))
for obj,x in zip(projectors,(-5,0,5)):
    m=Matrix.Rotation(math.pi/2,4,'X');m.translation=(x,0,1.6875);obj.matrix_world=m
c.view_layer.update()
r=analysis_runtime.analyse(c,wall,projectors,8192);st=r['statistics']
assert abs(st['density_average_px_m']-2716/6)<.01,st
assert st['coverage_percent']>99.9 and abs(st['overlap_percent']-12.5)<1,st
assert abs(st['max_anisotropy']-1)<.001,st
baseline={k:v for k,v in r.items() if k not in ('samples','_batches')}
# Exact angled Mapping Matter receiver, centred at (0,6,1.6875).
centre=Vector((0,6,1.6875));turn=Matrix.Rotation(math.radians(25),3,'Z')
original=[v.co.copy() for v in mesh.vertices]
for v,co in zip(mesh.vertices,original):v.co=centre+turn@(co-centre)
mesh.update();c.view_layer.update()
angled=analysis_runtime.analyse(c,wall,projectors,8192)
angled_summary={k:v for k,v in angled.items() if k not in ('samples','_batches')}
for v,co in zip(mesh.vertices,original):v.co=co
mesh.update();c.view_layer.update()
# Foreground occluder covers a real part of the screen.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,3,1.6875));blocker=c.object;blocker.scale=(2,.1,4)
c.view_layer.update();runtime.invalidate()
r=analysis_runtime.analyse(c,wall,projectors,4096)
occluded_summary={k:v for k,v in r.items() if k not in ('samples','_batches')}
assert r['statistics']['coverage_percent']<95 and r['statistics']['occluded_sample_count']>0,r['statistics']
assert r['statistics']['nominal_covered_area_m2']>r['statistics']['visible_covered_area_m2']
bpy.data.objects.remove(blocker,do_unlink=True)
# Angled receiving plane, density varies over actual geometry.
wall.rotation_euler.z=math.radians(25);c.view_layer.update()
r=analysis_runtime.analyse(c,wall,projectors,2048)
assert r['statistics']['density_variation_percent']>10,r['statistics']
# Stepped receiver: depths differ between halves.
wall.rotation_euler.z=0
mesh.clear_geometry();mesh.from_pydata([(-8,6,0),(0,6,0),(0,6,3.375),(-8,6,3.375),(0,8,0),(8,8,0),(8,8,3.375),(0,8,3.375)],[],[(0,1,2,3),(4,5,6,7)])
mesh.update();c.view_layer.update()
r=analysis_runtime.analyse(c,wall,projectors,2048)
assert r['statistics']['density_variation_percent']>5,r['statistics']
analysis_runtime.invalidate();assert r['stale']
r=analysis_runtime.analyse(c,wall,projectors,128)
wall.hide_set(True);runtime.refresh();assert r['stale'],'Visibility change did not invalidate'
wall.hide_set(False);runtime.refresh()
r=analysis_runtime.analyse(c,wall,projectors,128)
pj.location.x+=.1;c.view_layer.update();runtime.refresh();assert r['stale'],'Projector transform did not invalidate'
pj.location.x-=.1;c.view_layer.update();runtime.refresh()
# Invalid budgets must fail before allocating; real preset limits remain conservative.
for budget in (0,-1,1.5,100001):
 try:analysis_runtime.analyse(c,wall,projectors,budget)
 except ValueError:pass
 else:raise AssertionError('Invalid budget accepted')
assert not optics_validation.validate('christie_4k10','christie_085',.9,0,0,(2716,1528))
assert optics_validation.validate('christie_4k10','christie_085',.9,1,0,(2716,1528))
assert optics_validation.validate('christie_4k10','christie_085',.9,0,0,(1920,1080))
# Explicit optics constraints and transactional failure.
p=pj.ps;p.optics_model='synthetic';p.optics_lens='synthetic_120';p.resolution_x=1920;p.resolution_y=1080;p.throw_ratio=1.4;p.shift_h=p.shift_v=0
optics_validation.require(p)
for ratio,h,v in [(1.1,0,0),(1.7,0,0),(1.4,26,0),(1.4,0,56)]:
 assert optics_validation.validate('synthetic','synthetic_120',ratio,h,v,(1920,1080))
p.solve_lock_target=False;p.solve_by='LENS';c.view_layer.update();runtime.refresh(True)
inverse_solver.solve(c,pj,'RATIO',1.5);assert abs(p.throw_ratio-1.5)<1e-5
try:inverse_solver.solve(c,pj,'RATIO',2)
except ValueError:pass
else:raise AssertionError('Impossible optics solve accepted')
assert abs(p.throw_ratio-1.5)<1e-5
runtime.refresh(True);height=runtime.CACHE[pj.as_pointer()]['metrics'].distance/1.45*1080/1920
inverse_solver.solve(c,pj,'HEIGHT',height);assert abs(p.throw_ratio-1.45)<1e-4
# Reporting metadata and UUID authority, no hidden external dependencies.
c.scene.ps_study.project_name='Mapping Matter validation';c.scene.ps_study.venue='Controlled fixture'
package=Path(tempfile.mkdtemp())/'Study';data=study_reporting.export(c,package,False)
assert json.loads((package/'beam-study.json').read_text())['schema']=='beam-study'
assert (package/'index.html').is_file()
bad=copy.deepcopy(data);bad['optics'][0]['projector_uuid']='00000000-0000-0000-0000-000000000000'
try:study_reporting.validate(bad)
except ValueError:pass
else:raise AssertionError('Dangling optics accepted')
bad=copy.deepcopy(data);bad['projectors'][1]['uuid']=bad['projectors'][0]['uuid']
try:study_reporting.validate(bad)
except ValueError:pass
else:raise AssertionError('Duplicate UUID accepted')
try:study_reporting.export(c,package,False)
except ValueError:pass
else:raise AssertionError('Existing package replaced')
# Auto Blend must propagate the selected constrained optics into generated projectors.
from projection_study import screen_objects
bpy.data.objects.remove(wall,do_unlink=True)
s=c.scene.ps_study;draft=c.scene.beam_screen_draft;draft.width=16;draft.height=4;draft.aspect='FREE'
screen=screen_objects.create(c,draft);screen.location=(0,10,0);s.active_screen=screen;s.active_projector=pj;c.view_layer.update()
op=SimpleNamespace(use_template=True,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
group,_=auto_layout.create(c,op)
for member in group.members:
 assert member.projector.ps.optics_model=='synthetic' and member.projector.ps.optics_lens=='synthetic_120'
 optics_validation.require(member.projector.ps)
out=root/'work/parity';out.mkdir(exist_ok=True)
(out/'angled-analysis.json').write_text(json.dumps(angled_summary,indent=2));(out/'occluded-analysis.json').write_text(json.dumps(occluded_summary,indent=2))
(out/'csv-comparison.json').write_text(json.dumps(comparisons,indent=2));(out/'baseline-analysis.json').write_text(json.dumps(baseline,indent=2))
print('PARITY PASS: 10 live CSV fixtures; flat/angled/occluded/stepped surface; optics constraints and rollback; study package',flush=True)
addon.unregister()
