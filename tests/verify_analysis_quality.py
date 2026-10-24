"""Real PNG evidence for local analysis scale on light/dark venue shading."""
import bpy,sys,math,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,analysis_runtime,projector_object,study_views
out=root/'work/hardening/analysis-quality';out.mkdir(parents=True,exist_ok=True)
def run():
 try:
  c=bpy.context;s=c.scene.ps_study;area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);wall.rotation_euler.z=math.radians(15);c.view_layer.update();runtime.refresh(True)
  objects=list(projector_object.projectors(c.scene));analysis_runtime.analyse(c,wall,objects,8192)
  with c.temp_override(area=area,region=region):
   for appearance,colour in [('light',(.85,.85,.85)),('dark',(.06,.06,.06))]:
    area.spaces.active.shading.color_type='SINGLE';area.spaces.active.shading.single_color=colour
    for mode in ('DENSITY','STRETCH'):
     v=s.views[1];v.analysis_overlay=mode;study_views.export_view(c,v,out/f'{mode.lower()}-{appearance}.png',area)
  (out/'result.txt').write_text('PASS four angled receiver analysis images: local density scale and stretch, light/dark geometry')
 except Exception:(out/'result.txt').write_text(traceback.format_exc())
 addon.unregister();bpy.app.timers.register(lambda:bpy.ops.wm.quit_blender() and None,first_interval=.2)
def setup():
 addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'examples/production/Beam-PATCH-fixture.blend'));bpy.app.timers.register(run,first_interval=1)
bpy.app.timers.register(setup,first_interval=2)
