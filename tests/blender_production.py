"""Production regression: external fixtures, Euler edges and real optics rollback."""
import bpy,sys,math,csv,json
from pathlib import Path
from mathutils import Matrix,Euler
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import transform_conversion as t,projector_object,runtime,inverse_solver,optics_library as optics
from projection_study.export_designer import HEADER,csv_text
addon.register();c=bpy.context
# Every downloaded single-projector row retains the actual Mapping Matter schema.
fields=['Lens_X','Lens_Y','Lens_Z','Pitch(deg)','Yaw(deg)','Roll(deg)','Target_X','Target_Y','Target_Z','Target_Distance','Target_Width','Target_Height','Lens_Shift-H(%)','Lens_Shift-V(%)','Projector_Trow-Ratio','Projector_Native-Rez-X','Projector_Native-Rez-Y']
for fixture in (root/'tests/fixtures/designer').glob('MM-return-*.csv'):
 name=fixture.stem.removeprefix('MM-return-')
 original=list(csv.DictReader((root/'tests/fixtures/mapping_matter'/f'Beam-MM-{name}.csv').open()))[-1]
 returned=list(csv.DictReader(fixture.open()))[-1]
 assert returned['Projector_Name']=='Beam '+name,(name,returned)
 for key in fields:assert abs(float(original[key])-float(returned[key]))<.02,(name,key)
rows=list(csv.reader((root/'tests/fixtures/designer/Beam-Designer-fixtures.csv').open()));assert rows[0]==HEADER and len(rows)==11
for pitch in (-90,-89.999,-89,0,89,89.999,90):
 for yaw,roll in ((0,0),(173,71),(-179,-163),(383,377)):
  r=Euler(tuple(math.radians(x) for x in (pitch,roll,yaw)),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X')
  angles=t.orientation_degrees(r);d=t.designer_orientation_degrees(r)
  assert d==(angles[0],-angles[1],-angles[2]);assert angles==t.orientation_degrees(r)
  rebuilt=Euler(tuple(math.radians(x) for x in (angles[0],angles[2],angles[1])),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X')
  assert max(abs(r[i][j]-rebuilt[i][j]) for i in range(3) for j in range(3))<5e-5,(pitch,yaw,roll,angles,max(abs(r[i][j]-rebuilt[i][j]) for i in range(3) for j in range(3)))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
mesh=bpy.data.meshes.new('Receiver');mesh.from_pydata([(-100,10,-100),(100,10,-100),(100,10,100),(-100,10,100)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Receiver',mesh);c.scene.collection.objects.link(wall)
pj=projector_object.create(c);p=pj.ps;pj.matrix_world=Matrix.Rotation(math.pi/2,4,'X')
for key,model in optics.PROJECTORS.items():
 if key=='synthetic':continue
 for lens_id in model.lenses:
  lens=optics.LENSES[lens_id];p.optics_model=key;p.optics_lens=lens_id;p.resolution_x,p.resolution_y=model.resolution;p.throw_ratio=(lens.throw_min+lens.throw_max)/2;p.shift_h=p.shift_v=0
  pj.matrix_world=Matrix.Rotation(math.pi/2,4,'X');p.solve_by='LENS';p.solve_lock_position=p.solve_lock_lens=False
  c.view_layer.update();runtime.refresh(True)
  for field,value in [('WIDTH',10/p.throw_ratio),('HEIGHT',10/p.throw_ratio*p.resolution_y/p.resolution_x)]:inverse_solver.solve(c,pj,field,value)
  p.solve_by='POSITION';inverse_solver.solve(c,pj,'WIDTH',9/p.throw_ratio);p.solve_by='LENS'
  for ratio in (lens.throw_min*.9,lens.throw_max*1.1):
   before=pj.matrix_world.copy(),p.throw_ratio
   try:inverse_solver.solve(c,pj,'RATIO',ratio)
   except ValueError:pass
   else:raise AssertionError('Invalid lens accepted')
   assert pj.matrix_world==before[0] and p.throw_ratio==before[1]
  p.shift_h=1
  try:inverse_solver.solve(c,pj,'RATIO',p.throw_ratio)
  except ValueError:pass
  else:raise AssertionError('Unknown shift accepted')
  p.shift_h=0;p.solve_lock_position=p.solve_lock_lens=True
  try:inverse_solver.solve(c,pj,'WIDTH',1)
  except ValueError:pass
  else:raise AssertionError('Locked solve accepted')
from projection_study import screen_objects,auto_layout
from types import SimpleNamespace
bpy.data.objects.remove(wall,do_unlink=True)
draft=c.scene.beam_screen_draft;draft.width=16;draft.height=4;draft.aspect='FREE'
screen=screen_objects.create(c,draft);screen.location=(0,10,0);c.scene.ps_study.active_screen=screen;c.scene.ps_study.active_projector=pj
p.shift_h=p.shift_v=0;p.throw_ratio=1.7;p.optics_model='barco_g100w22';p.optics_lens='barco_gc150'
op=SimpleNamespace(use_template=True,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
group,_=auto_layout.create(c,op)
assert all(m.projector.ps.optics_lens=='barco_gc150' for m in group.members)
p.throw_ratio=2.2;c.scene.ps_study.active_projector=pj;before=len(c.scene.objects),len(c.scene.ps_study.blend_groups)
try:auto_layout.create(c,op)
except ValueError:pass
else:raise AssertionError('Auto Blend accepted invalid lens')
assert before==(len(c.scene.objects),len(c.scene.ps_study.blend_groups))
print('PRODUCTION REGRESSIONS PASS: ten actual roundtrips, 28 Euler edges, seven sourced lenses and rollback')
addon.unregister()
