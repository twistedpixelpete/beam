"""Disposable native-sidebar screenshot; start with --enable-event-simulate."""
import bpy,sys,traceback
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
state={}
def failure():
 text=traceback.format_exc();print(text,flush=True);(root/'work/screen-ui-result.txt').write_text(text);bpy.ops.wm.quit_blender()
def setup():
 try:
  addon.register()
  factory_scenes=list(bpy.data.scenes)
  for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
  with bpy.data.libraries.load(str(root/'examples/0.8/Beam-Screen-Builder.blend')) as (source,dest):dest.scenes=[n for n in source.scenes if n.startswith('Beam Screen Builder')]
  scene=dest.scenes[0];bpy.context.window.scene=scene
  for old_scene in factory_scenes:bpy.data.scenes.remove(old_scene)
  from projection_study import screen_objects
  obj=next(o for o in scene.objects if o.beam_screen.is_screen and o.beam_screen.name=='Faceted LED');screen_objects.select(bpy.context,obj)
  area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');state['area']=area;space=area.spaces.active;space.show_region_ui=True
  rv=space.region_3d;centre=obj.matrix_world@Vector((0,0,2));rv.view_location=centre;rv.view_rotation=Vector((-4,15,-6)).to_track_quat('-Z','Y');rv.view_distance=17;rv.view_perspective='PERSP';rv.update();area.tag_redraw()
  bpy.app.timers.register(focus,first_interval=.5)
 except Exception:failure()
def focus():
 try:
  ui=next(r for r in state['area'].regions if r.type=='UI')
  if ui.active_panel_category=='Beam' and ui.width>200:
   state['area'].spaces.active.show_region_ui=True;state['area'].tag_redraw();bpy.app.timers.register(capture,first_interval=.7);return None
  step=state.get('step',0)
  if step>45:raise AssertionError('Beam sidebar tab not found')
  state['step']=step+1;x=ui.x+ui.width-28;y=ui.y+ui.height-20-step*16
  for kind,value in [('MOUSEMOVE','NOTHING'),('LEFTMOUSE','PRESS'),('LEFTMOUSE','RELEASE')]:bpy.context.window.event_simulate(type=kind,value=value,x=x,y=y)
  return .08
 except Exception:failure()
def capture():
 try:
  bpy.ops.screen.screenshot(filepath=str(root/'examples/0.8/sidebar.png'))
  bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/Beam-Screen-Builder-ready.blend'))
  # Exercise every collapsed draw branch as real native panels, not a mock layout.
  from projection_study import screen_ui
  original=screen_ui.section
  def expanded(layout,key,title,closed=False):return original(layout,key+'_qa_expanded',title,False)
  screen_ui.section=expanded;state['area'].tag_redraw();bpy.app.timers.register(finish,first_interval=.6)
 except Exception:failure()
def finish():
 import shutil
 shutil.copy2(root/'work/Beam-Screen-Builder-ready.blend',root/'examples/0.8/Beam-Screen-Builder.blend')
 bpy.ops.screen.screenshot(filepath=str(root/'work/screen-ui-expanded.png'))
 (root/'work/screen-ui-result.txt').write_text('PASS: native Screen Builder sidebar drawn; expanded sections exercised')
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(setup,first_interval=2)
