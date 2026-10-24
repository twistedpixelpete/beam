"""Native GPU analysis overlay, report views and optics workflow acceptance."""
import bpy,sys,math,traceback,shutil,json
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,screen_objects,blend_groups,runtime,analysis_runtime,study_reporting,study_views,auto_layout
out=root/'work/parity-ui';out.mkdir(exist_ok=True)
state={}
def fail():
 text=traceback.format_exc();print(text,flush=True);(out/'result.txt').write_text(text);bpy.ops.wm.quit_blender()
def setup():
 try:
  addon.register();c=bpy.context
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  s=c.scene.ps_study;s.project_name='Beam / Mapping Matter comparison';s.venue='Controlled 16 m screen';s.author='Twisted Pixel';s.revision='Parity beta'
  draft=c.scene.beam_screen_draft;draft.width=16;draft.height=3.375;draft.aspect='FREE'
  wall=screen_objects.create(c,draft);wall.location=(0,6,0);state['wall']=wall
  projectors=[]
  for x in (-5,0,5):
   obj=projector_object.create(c);obj.ps.resolution_x=2716;obj.ps.resolution_y=1528;obj.ps.lumens=10000
   obj.ps.show_projected_identifier=False;obj.ps.show_centre_ray=False
   matrix=Matrix.Rotation(math.pi/2,4,'X');matrix.translation=(x,0,1.6875);obj.matrix_world=matrix;projectors.append(obj)
  state['projectors']=projectors
  c.view_layer.update();runtime.refresh(True)
  group=blend_groups.create(c,projectors,'HORIZONTAL',3,1,16.6667,'PERCENT',preserve=True);group.layout_screen=wall
  s.active_screen=wall;s.active_projector=projectors[0];s.analysis_receiver=wall;s.analysis_scope='ALL';s.inspector='SCREEN';s.pin_context=True
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with c.temp_override(area=area,region=region):bpy.ops.beam.workspace()
  bpy.app.timers.register(ready,first_interval=1)
 except Exception:fail()
def ready():
 try:
  c=bpy.context;workspace=next(w for w in bpy.data.workspaces if w.get('beam_workspace'));c.window.workspace=workspace
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');state['area']=area
  area.spaces.active.region_3d.view_distance=20;area.spaces.active.region_3d.view_location=(0,3,1.5)
  area.spaces.active.region_3d.view_rotation=Quaternion((.8205,.4247,.1759,.3399));area.spaces.active.region_3d.view_perspective='PERSP'
  with c.temp_override(area=area,region=region):
   view=study_views.create_view(c,'Overview');view.resolution_x=1200;view.resolution_y=700
  bpy.ops.script.execute_preset(filepath=str(root/'projection_study/themes/Beam.xml'),menu_idname='USERPREF_MT_interface_theme_presets')
  c.scene.ps_study.show_outputs=False;c.scene.ps_study.show_frustums=False;c.scene.ps_study.show_labels=False
  bpy.ops.beam.analyse();bpy.app.timers.register(capture,first_interval=2)
 except Exception:fail()
def capture():
 try:
  c=bpy.context;r=analysis_runtime.CACHE[c.scene.as_pointer()]
  assert not r['stale'],'Analysis invalidated without an engineering edit'
  assert r.get('_batches'),'GPU heatmap batches missing'
  bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2);bpy.ops.screen.screenshot(filepath=str(out/'density.png'))
  c.scene.ps_study.analysis_mode='STRETCH';bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2);bpy.ops.screen.screenshot(filepath=str(out/'stretch.png'))
  state['wall'].rotation_euler.z=math.radians(25);c.view_layer.update();bpy.ops.beam.analyse()
  c.scene.ps_study.analysis_mode='DENSITY';bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2);bpy.ops.screen.screenshot(filepath=str(out/'angled-density.png'))
  c.scene.ps_study.analysis_mode='STRETCH';bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2);bpy.ops.screen.screenshot(filepath=str(out/'angled-stretch.png'))
  state['wall'].rotation_euler.z=0;c.view_layer.update();bpy.ops.beam.analyse()
  package=out/'study-package'
  if package.exists():shutil.rmtree(package)
  c.scene.ps_study.show_outputs=True;c.scene.ps_study.show_frustums=True
  state['projectors'][0].ps.optics_model='christie_4k10';state['projectors'][0].ps.optics_lens='christie_085';bpy.ops.beam.analyse()
  data=study_reporting.export(c,package,True,state['area'])
  assert data['warnings'] and data['optics'][0]['projector_preset']
  c.scene.ps_study.show_outputs=False;c.scene.ps_study.show_frustums=False
  assert data['views'][0]['package_image'] and (package/data['views'][0]['package_image']).is_file()
  assert data['surface_analysis'] and data['blend_groups'] and data['screens']
  p=state['projectors'][0].ps;p.optics_model='synthetic';p.optics_lens='synthetic_120';p.resolution_x=1920;p.resolution_y=1080;p.throw_ratio=1.4
  c.scene.ps_study.active_projector=state['projectors'][0]
  op=SimpleNamespace(use_template=True,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
  auto_layout.calculate(c,op)
  p.throw_ratio=2
  try:auto_layout.calculate(c,op)
  except ValueError:pass
  else:raise AssertionError('Out-of-range lens accepted by Auto Blend')
  p.optics_model='MANUAL';p.resolution_x=2716;p.resolution_y=1528;p.throw_ratio=1
  bpy.ops.beam.analyse();c.scene.ps_study.analysis_mode='DENSITY'
  bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Parity.blend'))
  (out/'result.txt').write_text('PASS: native density/stretch overlays, no immediate stale cache, study package with rendered view and schedules, constrained Auto Blend')
  print('PARITY UI PASS',flush=True);bpy.ops.wm.quit_blender()
 except Exception:fail()
bpy.app.timers.register(setup,first_interval=2)
