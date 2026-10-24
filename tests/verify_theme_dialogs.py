"""Disposable native dialog and color/state fixture captures; no files exported."""
import bpy,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,study_data,ui_planning,auto_layout
from unittest.mock import patch
original_plan_draw=ui_planning.BEAM_OT_plan_new.draw
def checked_plan_draw(self,context):
 assert getattr(self,'_result',None),'Auto Blend result missing on first draw'
 with patch.object(auto_layout,'calculate',side_effect=AssertionError('Planning inside dialog draw')):
  original_plan_draw(self,context)
ui_planning.BEAM_OT_plan_new.draw=checked_plan_draw
refined='--beam-refinement' in sys.argv
out=root/('work/refinement-dialogs' if refined else 'work/theme-dialogs');out.mkdir(exist_ok=True)
bpy.context.preferences.view.show_splash=False
addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/('work/refinement-workspace/Beam-Workspace.blend' if refined else 'work/theme-workspace/Beam-Workspace.blend')))
bpy.ops.script.execute_preset(filepath=str(root/'projection_study/themes/Beam.xml'),menu_idname='USERPREF_MT_interface_theme_presets')
class States(bpy.types.Operator):
 bl_idname='beam_test.states';bl_label='Theme state inspection'
 value:bpy.props.FloatProperty(default=1.0)
 colour:bpy.props.FloatVectorProperty(subtype='COLOR',size=3,default=(.2,.4,.5),min=0,max=1)
 def execute(self,c):return {'FINISHED'}
 def invoke(self,c,e):return c.window_manager.invoke_props_dialog(self,width=420)
 def draw(self,c):
  l=self.layout;l.prop(self,'value',text='Editable');r=l.row();r.enabled=False;r.prop(self,'value',text='Disabled')
  r=l.row();r.alert=True;r.prop(self,'value',text='Invalid')
  l.label(text='Warning: check settings',icon='ERROR');l.label(text='Complete',icon='CHECKMARK')
  l.template_color_picker(self,'colour',value_slider=True);l.prop(self,'colour',text='Colour')
class Confirm(bpy.types.Operator):
 bl_idname='beam_test.confirm';bl_label='Confirm test action'
 def execute(self,c):return {'FINISHED'}
 def invoke(self,c,e):return c.window_manager.invoke_confirm(self,e)
bpy.utils.register_class(States);bpy.utils.register_class(Confirm)
phases=['auto-blend','inverse-solve','states-colour-picker','confirmation','export-file-browser'];state={'i':0,'stage':0}
def step():
 try:
  c=bpy.context;name=phases[state['i']];win=c.window_manager.windows[0]
  if state['stage']==0:
   area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
   with c.temp_override(window=win,area=area,region=region):
    obj=next(o for o in c.scene.objects if o.beam_screen.is_screen) if name=='auto-blend' else next(o for o in c.scene.objects if o.ps.is_projector)
    for o in c.selected_objects:o.select_set(False)
    obj.select_set(True);c.view_layer.objects.active=obj;study_data.sync_selection(c);runtime.refresh(True)
    win.event_simulate(type='MOUSEMOVE',value='NOTHING',x=800,y=700)
    if name=='auto-blend':c.scene.ps_study.inspector='SCREEN';result=bpy.ops.beam.plan_new('INVOKE_DEFAULT') if refined else bpy.ops.beam.auto_blend('INVOKE_DEFAULT')
    elif name=='inverse-solve':result=bpy.ops.beam.solve('INVOKE_DEFAULT')
    elif name=='states-colour-picker':result=bpy.ops.beam_test.states('INVOKE_DEFAULT')
    elif name=='confirmation':result=bpy.ops.beam_test.confirm('INVOKE_DEFAULT')
    else:result=bpy.ops.ps.export_json('INVOKE_DEFAULT',filepath=str(out/'cancelled.json'))
    assert result=={'RUNNING_MODAL'},(name,result)
   state['stage']=1;return 1.5
  if state['stage']==1:
   for w in c.window_manager.windows:
    with c.temp_override(window=w):
     for a in w.screen.areas:a.tag_redraw()
     bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
   state['stage']=2;return .5
  if state['stage']==2:
   w=c.window_manager.windows[-1] if name=='export-file-browser' else win
   with c.temp_override(window=w):bpy.ops.screen.screenshot(filepath=str(out/(name+'.png')))
   w.event_simulate(type='ESC',value='PRESS');w.event_simulate(type='ESC',value='RELEASE')
   state['stage']=3;return 1
  state['i']+=1;state['stage']=0
  if state['i']==len(phases):
   assert not (out/'cancelled.json').exists();(out/'result.txt').write_text('PASS: native dialogs opened, captured, cancelled; no export written.');addon.unregister();bpy.ops.wm.quit_blender();return
  return .5
 except:
  (out/'result.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);bpy.ops.wm.quit_blender()
bpy.app.timers.register(step,first_interval=2)
