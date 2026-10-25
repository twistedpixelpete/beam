"""Native GPU fixture capture and five-mode Study Package validation."""
import bpy,sys,traceback,json,time
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
def run():
 try:
  import projection_study as addon
  from projection_study import analysis_runtime,study_views,study_reporting,runtime
  addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'examples/surface-intelligence/Beam-Surface-Intelligence.blend'))
  def capture():
   try:
    c=bpy.context;s=c.scene.ps_study;area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
    with c.temp_override(area=area,region=region):
     rv=area.spaces.active.region_3d;rv.view_rotation=Vector((0,1,-.08)).to_track_quat('-Z','Y');rv.view_distance=17;rv.view_location=(0,9,2);rv.view_perspective='PERSP';rv.update()
     area.spaces.active.shading.type='SOLID';area.spaces.active.shading.light='STUDIO';area.spaces.active.overlay.show_floor=False
     area.spaces.active.overlay.show_axis_x=False;area.spaces.active.overlay.show_axis_y=False;area.spaces.active.overlay.show_cursor=False
     for obj in c.selected_objects:obj.select_set(False)
     s.show_frustums=False;s.show_outputs=False;s.show_labels=False;s.show_projected_identifiers=False
     projectors=[o for o in c.scene.objects if o.ps.is_projector];r=analysis_runtime.analyse(c,s.analysis_receiver,projectors,8192)
     s.analysis_show=True;s.views.clear();out=root/'examples/surface-intelligence'
     timings={}
     for mode in ('DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY'):
      view=study_views.create_view(c,mode.title());view.resolution_x=1400;view.resolution_y=900;view.analysis_overlay=mode
      view.include_labels=False;view.include_frustums=False;view.include_grids=False;view.include_projected_identifiers=False
      t=time.perf_counter();study_views.export_view(c,view,out/(mode.lower()+'.png'),area);timings[mode]=time.perf_counter()-t
     destination=out/'Study-Package'
     import shutil
     if destination.exists():shutil.rmtree(destination)
     study_reporting.export(c,destination,True,area)
     (out/'gpu-export-timings.json').write_text(json.dumps(timings,indent=2))
     bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Surface-Intelligence.blend'))
     print('SURFACE INTELLIGENCE GPU EXPORT PASS',flush=True)
   except Exception:traceback.print_exc()
   bpy.ops.wm.quit_blender()
  bpy.app.timers.register(capture,first_interval=1)
 except Exception:traceback.print_exc();bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=1)
