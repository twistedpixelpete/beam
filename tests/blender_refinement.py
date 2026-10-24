"""Cross-process theme restore and UI-only planning adapter regression checks.
Run with an isolated BLENDER_USER_CONFIG. Phase apply saves test preferences;
phase restore must run in a fresh Blender process without --factory-startup.
"""
import bpy,sys,json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import ui_theme,ui_planning,auto_layout,screen_objects,ui
addon.register();phase=sys.argv[-1];record=root/'work/refinement-theme-state.json'
if phase=='apply':
 t=bpy.context.preferences.themes[0];t.user_interface.wcol_regular.inner=(.17,.23,.29,1);t.view_3d.space.gradients.high_gradient=(.31,.32,.33)
 before={'inner':list(t.user_interface.wcol_regular.inner),'gradient':list(t.view_3d.space.gradients.high_gradient),'filepath':t.filepath}
 record.write_text(json.dumps(before))
 assert bpy.ops.beam.apply_theme()=={'FINISHED'}
 backup=(ui_theme.folder()/'previous.xml').read_bytes()
 assert bpy.ops.beam.apply_theme()=={'FINISHED'}
 assert (ui_theme.folder()/'previous.xml').read_bytes()==backup,'Repeat Apply overwrote original backup'
 assert ui_theme._ready
 bpy.ops.wm.save_userpref()
 print('REFINEMENT APPLY PASS: custom theme backed up once; applied theme saved to isolated preferences')
else:
 assert ui_theme._ready,'Restore was lost across process restart'
 before=json.loads(record.read_text());assert list(bpy.context.preferences.themes[0].user_interface.wcol_regular.inner)!=before['inner']
 assert bpy.ops.beam.restore_theme()=={'FINISHED'}
 t=bpy.context.preferences.themes[0]
 for key,value in [('inner',t.user_interface.wcol_regular.inner),('gradient',t.view_3d.space.gradients.high_gradient)]:
  assert all(abs(a-b)<1/255+.00001 for a,b in zip(value,before[key])),(key,value,before[key])
 assert t.filepath==before['filepath'];assert not ui_theme._ready
 assert bpy.ops.beam.apply_theme()=={'FINISHED'};assert bpy.ops.beam.restore_theme()=={'FINISHED'}
 # New UI dialog delegates the exact same options to the stable planner.
 p=bpy.context.scene.beam_screen_draft;p.width=16;p.height=4;p.aspect='FREE';screen=screen_objects.create(bpy.context,p);bpy.context.scene.ps_study.active_screen=screen;bpy.context.view_layer.update()
 options=dict(use_template=False,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,input_mode='PIXELS',overlap_h=200,overlap_v=200,distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
 preview=SimpleNamespace(**options);ui_planning.BEAM_OT_plan_new.update_preview(preview,bpy.context)
 expected,*_=auto_layout.calculate(bpy.context,preview);assert preview._result==expected
 large=SimpleNamespace(**{**options,'layout_type':'ARRAY','columns':8,'rows':4,'count':32})
 ui_planning.BEAM_OT_plan_new.update_preview(large,bpy.context)
 assert large._result['count']==32 and len(large._pairs)>32
 before_groups=len(bpy.context.scene.ps_study.blend_groups)
 assert bpy.ops.beam.plan_new(**options)=={'FINISHED'}
 assert len(bpy.context.scene.ps_study.blend_groups)==before_groups+1
 # Background/GPU and missing source remain visible without material mutation.
 receiver=bpy.context.scene.ps_study.active_screen
 assert ui.receiver_warning(bpy.context,receiver)=='GPU viewport required'
 print('REFINEMENT RESTORE PASS: restored custom theme after process restart; planning parity and execution; GPU warning')
addon.unregister()
