"""Fresh GUI process: persisted workspace, rail/fallback, receiver warnings, Presentation."""
import bpy,sys,traceback
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import ui,ui_workspace,ui_context,study_data,runtime,presentation,reverse_mapping
bpy.context.preferences.view.show_splash=False
addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'work/refinement-workspace/Beam-Workspace.blend'))
bpy.ops.script.execute_preset(filepath=str(root/'projection_study/themes/Beam.xml'),menu_idname='USERPREF_MT_interface_theme_presets')
out=root/'work/refinement-restart';out.mkdir(exist_ok=True);state={'phase':0};seen=[]
def select(obj):
 for o in bpy.context.selected_objects:o.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj;study_data.sync_selection(bpy.context)
def step():
 try:
  c=bpy.context;area=next(a for a in c.screen.areas if a.type=='VIEW_3D');s=c.scene.ps_study
  phase=state['phase']
  if phase==0:
   assert ui_workspace.is_beam(c);count=len(bpy.data.workspaces)
   bpy.ops.beam.workspace();bpy.ops.beam.workspace();assert len(bpy.data.workspaces)==count
   assert ui.rail_visible(c);seen.append('Fresh process reopens Beam; repeated Open creates no duplicate')
   pj=next(o for o in c.scene.objects if o.ps.is_projector);select(pj);s.inspector='PROJECTOR'
   s.pin_context=True;receiver=next(o for o in c.scene.objects if o.beam_screen.is_screen);select(receiver)
   assert study_data.active(c)==pj and s.inspector=='PROJECTOR'
   if receiver.beam_reverse.enabled:reverse_mapping.disable(receiver)
   receiver.beam_reverse.source='SELECTED';receiver.beam_reverse.projector=None;s.reverse_receiver=receiver
   assert ui.receiver_warning(c,receiver)=='No Reverse Mapping source'
   with patch.object(ui,'bpy',SimpleNamespace(app=SimpleNamespace(background=True))):assert ui.receiver_warning(c,receiver)=='GPU viewport required'
   seen.append('Missing source and simulated GPU-unavailable warnings; pinned projector remains separate')
  elif phase==1:pass
  elif phase==2:
   capture('missing-source');area.spaces.active.show_region_toolbar=False;assert not ui.rail_visible(c)
  elif phase==3:pass
  elif phase==4:
   capture('navigation-fallback');area.spaces.active.show_region_toolbar=True;s.pin_context=False
   select(study_data.active(c));s.inspector='PROJECTOR';s.reverse_receiver=None
   assert bpy.ops.beam.ui_action(action='PRESENTATION')=={'FINISHED'};assert presentation.active(area)
   seen.append('Hidden toolbar restores inspector navigation')
  elif phase==5:pass
  elif phase==6:
   capture('presentation');assert bpy.ops.beam.ui_action(action='PRESENTATION')=={'FINISHED'};assert not presentation.active(area)
   seen.append('Presentation and Technical round trip')
  elif phase==7:pass
  elif phase==8:
   capture('technical');outliner=next(a for a in c.screen.areas if a.type=='OUTLINER')
   with c.temp_override(area=outliner):bpy.ops.screen.screenshot_area(filepath=str(out/'outliner.png'))
   bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Refinement.blend'))
   projectors=sorted((o for o in c.scene.objects if o.ps.is_projector),key=lambda o:o.name)
   projectors[0].keyframe_insert(data_path='location',frame=1)
   projectors[1].hide_set(True);projectors[2].hide_render=True
   outliner.spaces.active.show_restrict_column_render=True
   with c.temp_override(area=outliner,region=next(r for r in outliner.regions if r.type=='WINDOW')):bpy.ops.outliner.show_active()
  elif phase==9:pass
  elif phase==10:
   outliner=next(a for a in c.screen.areas if a.type=='OUTLINER')
   with c.temp_override(area=outliner):bpy.ops.screen.screenshot_area(filepath=str(out/'outliner-states.png'))
   seen.append('Outliner fixture with active, hidden, render-disabled and keyframed projectors')
   (out/'result.txt').write_text('PASS\n'+'\n'.join(seen));addon.unregister();bpy.ops.wm.quit_blender();return
  for a in c.screen.areas:a.tag_redraw()
  bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
  state['phase']+=1;return .8
 except:
  (out/'result.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);bpy.ops.wm.quit_blender()
def capture(name):bpy.ops.screen.screenshot(filepath=str(out/(name+'.png')))
bpy.app.timers.register(step,first_interval=3)
