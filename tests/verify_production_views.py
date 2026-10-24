"""Disposable real-optics PATCH fixture, GPU legend and stale-export checks."""
import bpy,sys,math,traceback,json,shutil
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,screen_objects,blend_groups,runtime,analysis_runtime,study_reporting,study_views
out=root/'work/production';out.mkdir(parents=True,exist_ok=True)
def run():
 try:
  addon.register();c=bpy.context
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  s=c.scene.ps_study;s.project_name='PATCH development fixture';s.venue='Conference stage / four-projector panorama';s.author='Twisted Pixel';s.revision='Production validation beta'
  draft=c.scene.beam_screen_draft;draft.width=18;draft.height=3.75;draft.aspect='FREE'
  wall=screen_objects.create(c,draft);wall.location=(0,8,0)
  s.display_units='m'
  objects=[]
  for x in (-6.3,-2.1,2.1,6.3):
   obj=projector_object.create(c);p=obj.ps;p.optics_model='panasonic_rz990';p.optics_lens='panasonic_dle150';p.resolution_x=1920;p.resolution_y=1200;p.lumens=9400;p.throw_ratio=1.4;p.show_projected_identifier=False;p.show_centre_ray=False
   matrix=Matrix.Rotation(math.pi/2,4,'X');matrix.translation=(x,0,1.875);obj.matrix_world=matrix;objects.append(obj)
  c.view_layer.update();runtime.refresh(True)
  group=blend_groups.create(c,objects,'HORIZONTAL',4,1,26.5,'PERCENT',preserve=True);group.layout_screen=wall
  s.analysis_receiver=wall;s.analysis_scope='ALL'
  # Stage deck and auditorium floor are outside the optical path.
  for name,location,scale in [('Stage deck',(0,8,-.3),(10,2,.25)),('Venue floor',(0,1,-.65),(13,12,.1))]:
   bpy.ops.mesh.primitive_cube_add(size=2,location=location);o=c.object;o.name=name;o.scale=scale
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');rv=area.spaces.active.region_3d
  eye=Vector((18,-20,15));target=Vector((0,4,1.6));rv.view_location=target;rv.view_rotation=(target-eye).to_track_quat('-Z','Y');rv.view_distance=28;rv.view_perspective='PERSP';rv.update()
  for o in c.selected_objects:o.select_set(False)
  area.spaces.active.overlay.show_floor=False;area.spaces.active.overlay.show_axis_x=False;area.spaces.active.overlay.show_axis_y=False;area.spaces.active.overlay.show_relationship_lines=False
  with c.temp_override(area=area,region=region):
   for mode in ('NONE','DENSITY','STRETCH'):
    view=study_views.create_view(c,'Overview' if mode=='NONE' else mode.title());view.resolution_x=1400;view.resolution_y=850;view.analysis_overlay=mode
   result=analysis_runtime.analyse(c,wall,objects,8192)
   package=out/'PATCH-study-package'
   if package.exists():shutil.rmtree(package)
   data=study_reporting.export(c,package,True,area)
   assert len(data['projectors'])==4 and len(data['views'])==3
   for view in data['views'][1:]:
    meta=view['analysis_image'];assert meta['analysis_uuid']==result['analysis_uuid'];assert meta['statistics']['sample_count']==8192
    assert (package/view['package_image']).with_suffix('.analysis.json').exists()
   analysis_runtime.invalidate()
   rejected=out/'stale-must-not-exist.png'
   try:study_views.export_view(c,s.views[1],rejected,area)
   except ValueError:pass
   else:raise AssertionError('Stale analysis exported')
   assert not rejected.exists()
   bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-PATCH-fixture.blend'))
  (out/'views-result.txt').write_text('PASS: three rendered views, density/stretch metadata, first-hit overlay, stale rejection and four real-preset projectors')
 except Exception:
  text=traceback.format_exc();print(text,flush=True);(out/'views-result.txt').write_text(text)
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=2)
