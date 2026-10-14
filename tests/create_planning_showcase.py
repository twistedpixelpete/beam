"""Disposable 0.9 example and genuine Blender sidebar/dialog screenshots."""
import bpy,sys,traceback
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects,auto_layout,runtime,study_views,ui
from types import SimpleNamespace
out=root/'examples/0.9';out.mkdir(exist_ok=True,parents=True);state={}
from projection_study import inverse_solver
_original_invoke=inverse_solver.BEAM_OT_solve.invoke
def capture_operator(self,context,event):
 state['solver_operator']=self
 return _original_invoke(self,context,event)
inverse_solver.BEAM_OT_solve.invoke=capture_operator
def fail():
 text=traceback.format_exc();print(text,flush=True);(root/'work/showcase-result.txt').write_text(text);bpy.ops.wm.quit_blender()
def setup():
 try:
  addon.register()
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  c=bpy.context;s=c.scene;s.ps_study.project_name='Beam · Planning Beta';s.ps_study.venue='Flat screen study';s.ps_study.revision='R01';s.ps_study.display_units='m'
  p=s.beam_screen_draft;p.width=16;p.height=3.375
  wall=screen_objects.create(c,p);wall.location=(0,10,1);screen_objects.select(c,wall);s.ps_study.active_screen=wall
  op=SimpleNamespace(use_template=False,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=6,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
  group,result=auto_layout.create(c,op);state['group_uuid']=group.uuid;state['wall']=wall;group.show_overlap=False
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');state['area']=area;space=area.spaces.active;space.show_region_ui=True
  rv=space.region_3d;target=Vector((0,7,2));eye=Vector((17,-18,14));rv.view_location=target;rv.view_rotation=(target-eye).to_track_quat('-Z','Y');rv.view_distance=23;rv.view_perspective='PERSP';rv.update()
  region=next(r for r in area.regions if r.type=='WINDOW');state['region']=region
  with c.temp_override(area=area,region=region):
   bpy.ops.beam.presentation();view=study_views.create_view(c,'Three-projector Auto Blend');view.resolution_x=1600;view.resolution_y=1000;state['view']=view
   runtime.refresh(True);study_views.export_view(c,view,out/'auto-blend.png')
  area.tag_redraw();bpy.app.timers.register(focus,first_interval=1)
 except:fail()
def focus():
 try:
  region=next(r for r in state['area'].regions if r.type=='UI')
  if region.active_panel_category=='Beam' and region.width>200:
   bpy.app.timers.register(capture,first_interval=1);return
  step=state.get('step',0)
  if step>45:raise AssertionError('Beam tab not found')
  state['step']=step+1;x=region.x+region.width-28;y=region.y+region.height-20-step*16
  for kind,value in [('MOUSEMOVE','NOTHING'),('LEFTMOUSE','PRESS'),('LEFTMOUSE','RELEASE')]:bpy.context.window.event_simulate(type=kind,value=value,x=x,y=y)
  return .08
 except:fail()
def capture():
 try:
  with bpy.context.temp_override(area=state['area'],region=state['region']):
   study_views.export_view(bpy.context,state['view'],out/'auto-blend.png')
   bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Auto-Blend.blend'))
   bpy.ops.screen.screenshot(filepath=str(out/'blend-inspector.png'))
   screen_objects.select(bpy.context,state['wall']);runtime.refresh()
   bpy.ops.beam.auto_blend('INVOKE_DEFAULT',use_template=False,count=3,overlap_h=200)
  bpy.app.timers.register(dialog,first_interval=1)
 except:fail()
def dialog():
 try:
  bpy.ops.screen.screenshot(filepath=str(out/'auto-blend-dialog.png'))
  bpy.context.window.event_simulate(type='ESC',value='PRESS');bpy.context.window.event_simulate(type='ESC',value='RELEASE')
  bpy.app.timers.register(solver,first_interval=.5)
 except:fail()
def solver():
 try:
  with bpy.context.temp_override(area=state['area'],region=state['region']):
   pj=bpy.context.scene.ps_study.active_projector;screen_objects.select(bpy.context,pj);runtime.refresh()
   bpy.ops.beam.solve('INVOKE_DEFAULT',field='HEIGHT')
  bpy.app.timers.register(finish,first_interval=1)
 except:fail()
def finish():
 with bpy.context.temp_override(area=state['area'],region=state['region']):
  op=state['solver_operator'];op.value=2.5;op.check(bpy.context)
  pj=bpy.context.scene.ps_study.active_projector
  assert abs(runtime.CACHE[pj.as_pointer()]['metrics'].height-2.5)<.001
  op.cancel(bpy.context);assert abs(runtime.CACHE[pj.as_pointer()]['metrics'].height-3.375)<.001
  print('PASS live target callback and Cancel rollback',flush=True)
 bpy.ops.screen.screenshot(filepath=str(out/'inverse-dialog.png'))
 bpy.context.window.event_simulate(type='ESC',value='PRESS');bpy.context.window.event_simulate(type='ESC',value='RELEASE')
 (root/'work/showcase-result.txt').write_text('PASS: actual Auto Blend scene, inspector and inverse/layout dialogs')
 bpy.app.timers.register(lambda:bpy.ops.wm.quit_blender() and None,first_interval=.5)
bpy.app.timers.register(setup,first_interval=2)
