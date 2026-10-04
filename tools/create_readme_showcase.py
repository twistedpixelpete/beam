"""Create the README demo in a disposable Blender UI process, then quit.
Run: blender --factory-startup --python tools/create_readme_showcase.py
"""
import bpy,sys,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import projection_study as addon
from projection_study import screen_objects,projector_object,runtime,study_views,presentation
OUT=ROOT/'examples/0.8.1';OUT.mkdir(parents=True,exist_ok=True)
(ROOT/'work').mkdir(exist_ok=True)
def run():
 try:
  addon.register()
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  scene=bpy.context.scene;scene.name='Beam · Three Projector Study';scene.unit_settings.system='METRIC'
  settings=scene.ps_study;settings.project_name='Beam';settings.revision='Beta';settings.display_units='m'
  p=scene.beam_screen_draft;p.width=16;p.height=4.5;p.name='Main Screen';p.segments=8
  wall=screen_objects.create(bpy.context,p);wall.location=(0,8,.4);wall.beam_screen.show_label=False;wall.beam_screen.show_dimensions=False
  wall.active_material.diffuse_color=(.19,.21,.24,1)
  def box(name,loc,size,colour):
   bpy.ops.mesh.primitive_cube_add(size=1,location=loc);obj=bpy.context.object;obj.name=name;obj.dimensions=size
   bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   mat=bpy.data.materials.new(name);mat.diffuse_color=(*colour,1);obj.data.materials.append(mat)
   return obj
  box('Stage',(0,8,-.02),(17,2,.4),(.1,.12,.15))
  box('Floor',(0,3,-.28),(40,36,.1),(.13,.15,.18))
  for i,x in enumerate((-4.8,0,4.8)):
   obj=projector_object.create(bpy.context);obj.location=(x,0,2.65);obj.ps.throw_ratio=1.4;obj.ps.show_centre_ray=False;obj.ps.show_target_marker=False
   box('Projector Stand '+str(i+1),(x,-.4,1.15),(.12,.12,2.3),(.12,.14,.17))
   box('Stand Base '+str(i+1),(x,-.4,-.1),(.8,.7,.15),(.12,.14,.17))
   box('Mount '+str(i+1),(x,-.4,2.44),(.55,.65,.08),(.12,.14,.17))
  bpy.context.view_layer.update();runtime.refresh(True)
  assert all(r['hit'] for r in runtime.CACHE.values())
  area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with bpy.context.temp_override(area=area,region=region):
   bpy.ops.beam.presentation();space=area.spaces.active;space.shading.color_type='MATERIAL';space.shading.show_shadows=True;space.shading.show_cavity=True;space.shading.cavity_type='BOTH'
   space.shading.background_color=(.035,.043,.055)
   for obj in bpy.context.selected_objects:obj.select_set(False)
   for name,eye,target in [('projector-showcase',(10,-22,12),(0,4,2))]:
    rv=space.region_3d;eye=Vector(eye);target=Vector(target);rv.view_location=target;rv.view_rotation=(target-eye).to_track_quat('-Z','Y');rv.view_distance=(eye-target).length;rv.view_perspective='PERSP';rv.update()
    view=study_views.create_view(bpy.context,name);view.resolution_x=2200;view.resolution_y=1300
    view.camera.data.lens=48
    study_views.export_view(bpy.context,view,ROOT/'work/showcase-warmup.png')
    study_views.export_view(bpy.context,view,OUT/(name+'.png'))
   bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Beam-Projector-Showcase.blend'))
  print('SHOWCASE PASS',flush=True)
 except Exception:print(traceback.format_exc(),flush=True)
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=2)
