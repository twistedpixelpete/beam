# Workflow state, targeted invalidation, display units and interchange.
exec((root/'tests/blender_m3.py').read_text())
from projection_study import study_data, export_json, display_units
from projection_study.projector_object import selected
from projection_study.export_disguise import rows_for_scene
import json
scene=bpy.context.scene
# Keep PJ01 while selecting and moving venue geometry.
o.ps.target=wall
scene.ps_study.active_projector=o
for item in bpy.context.selected_objects: item.select_set(False)
wall.select_set(True); bpy.context.view_layer.objects.active=wall
runtime.refresh()
assert selected(bpy.context)==o
before=runtime.CACHE[o.as_pointer()]['metrics']
wall.location.y+=3
bpy.context.view_layer.update(); runtime.refresh()
after=runtime.CACHE[o.as_pointer()]['metrics']
assert after.distance>before.distance and after.pixel_size_m>before.pixel_size_m
assert after.pixels_per_metre<before.pixels_per_metre and after.lux<before.lux
# New selection changes the persistent projector; clear survives idle selected object.
bpy.ops.ps.add(); other=bpy.context.object
runtime.refresh(); assert selected(bpy.context)==other
bpy.ops.ps.active_projector(clear=True)
assert selected(bpy.context) is None
bpy.ops.ps.active_projector(); assert selected(bpy.context)==other
# Geometry changes reconsider automatic first-hit targets for every projector.
mesh=bpy.data.meshes.new('Other receiver')
mesh.from_pydata([(-20,25,-20),(20,25,-20),(20,25,20),(-20,25,20)],[],[(0,1,2,3)])
wall2=bpy.data.objects.new('Other wall',mesh); scene.collection.objects.link(wall2)
other.ps.target=wall2
bpy.context.view_layer.update(); runtime.refresh(True)
other_cached=runtime.CACHE[other.as_pointer()]
wall.location.y+=1
bpy.context.view_layer.update(); runtime.refresh()
assert runtime.CACHE[other.as_pointer()]['hit'][3]==wall.name
assert other.ps.target==wall, 'Legacy manual target must not restrict automatic targeting'
# Units never change calculations or disguise rows.
scene.ps_study.display_units='mm'
rows_mm=rows_for_scene(bpy.context)
scene.ps_study.display_units='m'
rows_m=rows_for_scene(bpy.context)
assert rows_mm==rows_m and rows_m[0][-3]=='mm'
assert display_units.pixel_size(10/3840,'mm')=='2.60 mm/px'
o.ps.notes='Front screen — check trim'
data=export_json.document(bpy.context)
json.dumps(data,allow_nan=False)
pj=next(p for p in data['projectors'] if p['uuid']==o.ps.uuid)
assert pj['target']['object_name']==wall.name
assert pj['notes']==o.ps.notes and pj['calculated']['pixel_size_mm_per_px']>0
assert data['units']['internal_length']=='m' and data['units']['disguise_length']=='mm'
# State and notes survive a .blend library round trip.
scene.ps_study.active_projector=o
path=str(root/'work/workflow-roundtrip.blend')
bpy.data.libraries.write(path,{scene})
with bpy.data.libraries.load(path,link=False) as (src,dst): dst.scenes=[scene.name]
loaded=dst.scenes[0]
assert loaded.ps_study.active_projector.ps.uuid==o.ps.uuid
assert loaded.ps_study.active_projector.ps.notes==o.ps.notes
for item in list(loaded.objects): bpy.data.objects.remove(item,do_unlink=True)
bpy.data.scenes.remove(loaded)
print('MILESTONE 9 workflow / targeted invalidation / JSON PASS')
