"""Run through live MCP after blender_screen_builder.run(), then inspect PNGs."""
from pathlib import Path
import bpy
from mathutils import Vector
from projection_study import screen_objects,screen_patterns,study_views,presentation
root=Path(__file__).resolve().parents[1];out=root/'examples/0.8';out.mkdir(exist_ok=True)
scene=bpy.context.scene
for view in list(scene.ps_study.views):
 camera=view.camera
 if camera and camera.name in scene.objects:
  data=camera.data;bpy.data.objects.remove(camera,do_unlink=True)
  if data.users==0:bpy.data.cameras.remove(data)
scene.ps_study.views.clear()
overlap_state=[g.show_overlap for g in scene.ps_study.blend_groups]
for group in scene.ps_study.blend_groups:group.show_overlap=False
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
objects=[o for o in scene.objects if o.beam_screen.is_screen];screens={o.beam_screen.name:o for o in objects}
# Showcase retains exact reference cases after the update acceptance checks.
for name,h in [('Flat Projection',3.375),('90 Degree Arc',4),('S Curve',3),('360 Cylinder',3)]:
 o=screens[name];o.beam_screen.height=h;screen_objects.update(bpy.context,o)
for name in ('Flat LED','Faceted LED'):
 o=screens[name];o.beam_screen.rows=8;screen_objects.update(bpy.context,o)
conform=screens.get('Conformed Display')
if conform:
 conform.location=(0,-15,0);conform.beam_screen.conform_target.location=(0,-15,0)
with bpy.context.temp_override(area=area,region=region):
 space=area.spaces.active
 if not presentation.active(area):bpy.ops.beam.presentation()
 for index,(name,obj) in enumerate(screens.items()):
  if name=='Conformed Display':screen_patterns.apply(obj)
  for other in scene.objects:
   other.hide_set(other!=obj and other.parent!=obj)
  bpy.context.view_layer.update()
  screen_objects.select(bpy.context,obj)
  centre=obj.matrix_world@Vector((0,0,2));size=max(obj.dimensions.x,obj.dimensions.y,obj.dimensions.z,6)
  eye=centre+Vector((size*.3,-size*1.4,size*.45))
  if name=='360 Cylinder':eye=centre+Vector((size*.8,-size*.9,size*.9))
  rv=space.region_3d;rv.view_location=centre;rv.view_rotation=(centre-eye).to_track_quat('-Z','Y');rv.view_distance=(eye-centre).length;rv.view_perspective='PERSP';rv.update();area.tag_redraw()
  view=study_views.create_view(bpy.context,name);view.resolution_x=1600;view.resolution_y=1000
  study_views.export_view(bpy.context,view,out/(name.lower().replace(' ','-')+'.png'))
 for other in scene.objects:
  other.hide_set(other.type=='CURVE' or other.name.startswith('Uneven Source') or other.type=='CAMERA')
 # A clean final inspection view centres the faceted wall.
 obj=screens['Faceted LED'];screen_objects.select(bpy.context,obj);centre=obj.matrix_world@Vector((0,0,2));rv.view_location=centre;rv.view_rotation=Vector((-5,16,-6)).to_track_quat('-Z','Y');rv.view_distance=17;rv.view_perspective='PERSP';rv.update()
 if presentation.active(area):bpy.ops.beam.presentation()
 for group,show in zip(scene.ps_study.blend_groups,overlap_state):group.show_overlap=show
 for other in scene.objects:
  if other.get('beam_baked_screen_id'):other.hide_set(True)
 bpy.data.libraries.write(str(out/'Beam-Screen-Builder.blend'),{scene},fake_user=True)
result={'screenshots':str(out),'scene':scene.name,'count':len(screens)}
