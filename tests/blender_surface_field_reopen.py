"""Fresh-process field persistence, regenerated metrics, Observer Undo/Redo."""
import bpy,sys,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));out=root/'examples/surface-intelligence/field'
import projection_study as addon
from projection_study import analysis_runtime,runtime
state={}
def run():
 try:
  addon.register();bpy.ops.wm.open_mainfile(filepath=str(out/'Beam-Civic-Hall-Field.blend'))
  bpy.app.timers.register(verify,first_interval=.5)
 except Exception:fail()
def verify():
 try:
  c=bpy.context;s=c.scene.ps_study;expected=json.loads((out/'results.json').read_text());p=expected['persistent']
  assert not analysis_runtime.CACHE
  viewer=s.analysis_observer;assert viewer.beam_observer.uuid==p['observer_uuid'] and viewer.beam_observer.threshold==1 and abs(viewer.beam_observer.eye_height-1.65)<1e-6
  assert s.analysis_mode=='ILLUMINANCE' and s.illuminance_scale=='AUTO' and s.target_illuminance==100
  projectors=[o for o in c.scene.objects if o.ps.is_projector];assert {o.ps.uuid for o in projectors}==set(p['projectors'])
  assert all(o.ps.optics_model=='christie_4k10' and o.ps.optics_lens=='christie_085' for o in projectors)
  assert s.active_screen.beam_screen.uuid==p['screen_uuid'] and s.blend_groups[0].uuid==p['group_uuid']
  assert [v.uuid for v in s.views]==p['view_uuids']
  c.view_layer.update();r=analysis_runtime.analyse(c,s.analysis_receiver,projectors,8192)
  for key,value in expected['baseline'].items():
   if value is not None:assert abs(r['statistics'][key]-value)<1e-5,(key,r['statistics'][key],value)
  for o in c.selected_objects:o.select_set(False)
  viewer.select_set(True);c.view_layer.objects.active=viewer
  state['position']=list(viewer.location);state['uuid']=viewer.beam_observer.uuid
  bpy.ops.ed.undo_push(message='Observer before field movement')
  viewer.location.y-=2;c.view_layer.update();assert analysis_runtime.stale(r,'ACUITY')
  bpy.ops.ed.undo_push(message='Observer after field movement')
  bpy.app.timers.register(undo,first_interval=.3)
 except Exception:fail()
def fail():
 text=traceback.format_exc();print(text,flush=True);(out/'reopen-result.txt').write_text(text);bpy.ops.wm.quit_blender()
def undo():
 try:
  bpy.ops.ed.undo();s=bpy.context.scene.ps_study
  assert list(s.analysis_observer.location)==state['position'] and s.analysis_observer.beam_observer.uuid==state['uuid']
  assert not analysis_runtime.CACHE
  bpy.app.timers.register(redo,first_interval=.3)
 except Exception:fail()
def redo():
 try:
  bpy.ops.ed.redo();s=bpy.context.scene.ps_study
  assert abs(s.analysis_observer.location.y-(state['position'][1]-2))<1e-6
  assert s.analysis_observer.beam_observer.uuid==state['uuid'] and not analysis_runtime.CACHE
  (out/'reopen-result.txt').write_text('PASS fresh-process persistence, deterministic regeneration, Observer Undo/Redo identity and cache clearing')
  print('FIELD REOPEN / OBSERVER UNDO REDO PASS',flush=True);bpy.ops.wm.quit_blender()
 except Exception:fail()
bpy.app.timers.register(run,first_interval=1)
