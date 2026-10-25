"""Run in a disposable UI Blender session; exports the validated onboarding scene."""
import bpy,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import analysis_runtime,review_export
out=root/'review/example'
def run():
 try:
  c=bpy.context;s=c.scene.ps_study
  s.analysis_receiver=bpy.data.objects['SCR001'];s.analysis_mode='ACUITY';s.analysis_scope='GROUP';s.analysis_detail='2048'
  assert bpy.ops.beam.analyse()=={'FINISHED'}
  state=(c.scene,c.view_layer.objects.active,tuple(c.selected_objects),len(bpy.data.scenes),len(bpy.data.objects),len(bpy.data.meshes))
  m=review_export.export(c,out)
  assert state==(c.scene,c.view_layer.objects.active,tuple(c.selected_objects),len(bpy.data.scenes),len(bpy.data.objects),len(bpy.data.meshes))
  try:review_export.export(c,out)
  except ValueError:pass
  else:raise AssertionError('Existing package was not protected')
  (root/'work/review-export-result.txt').write_text('PASS: training package with fresh Acuity/illuminance/distance results; authoring context restored; existing package refused\n')
  print('REVIEW EXPORT PASS',m,flush=True)
 except Exception:
  t=traceback.format_exc();print(t,flush=True);(root/'work/review-export-result.txt').write_text(t)
 bpy.ops.wm.quit_blender()
def load():
 addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'output/pdf/onboarding-0.13/Beam_Training_Project.blend'),load_ui=False);bpy.app.timers.register(run,first_interval=1)
bpy.app.timers.register(load,first_interval=1)
