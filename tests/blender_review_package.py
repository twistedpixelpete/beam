"""Fresh background Blender: Review metre conversion, camera parity and failure restoration."""
import bpy,sys,json,tempfile,struct
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import review_export,projector_object,screen_objects,runtime
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
c.scene.unit_settings.scale_length=.01
# A real 6 x 3 metre receiver, with world coordinates in centimetres.
d=c.scene.beam_screen_draft;d.width=6;d.height=3;d.aspect='FREE';d.origin='CENTRE'
# Use mesh fixture to avoid depending on screen draft origin enum versions.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,1000,0),rotation=(1.57079632679,0,0));wall=c.object;wall.scale=(300,150,1);wall.name='Metre fixture'
p=projector_object.create(c);p.ps.preview_distance=10
camdata=bpy.data.cameras.new('Review ortho');cam=bpy.data.objects.new('Review ortho',camdata);c.scene.collection.objects.link(cam);cam.location=(0,-500,500);cam.rotation_euler=(Vector((0,1000,0))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=1200;camdata.shift_x=.15;camdata.shift_y=-.1
v=c.scene.ps_study.views.add();v.uuid='d97d5ca6-138f-49d0-9f4a-e92eeb8bc377';v.name='Shifted orthographic';v.camera=cam;v.resolution_x=1600;v.resolution_y=1000
c.view_layer.update();runtime.refresh(True)
state=(c.scene,c.view_layer.objects.active,tuple(c.selected_objects),len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.cameras),len(bpy.data.scenes))
with tempfile.TemporaryDirectory(prefix='beam-review-test-') as tmp:
 path=Path(tmp)/'R01';m=review_export.export(c,path);doc=json.loads((path/'beam.json').read_text());projection=doc['review']['views'][v.uuid]['projection_matrix_row_major']
 assert abs(projection[0][0]-2/12)<1e-6,projection
 assert abs(doc['views'][0]['camera']['position_m'][1]+5)<1e-6
 blob=(path/'scene.glb').read_bytes();length=struct.unpack_from('<I',blob,12)[0];gltf=json.loads(blob[20:20+length]);node=next(n for n in gltf['nodes'] if n.get('extras',{}).get('beam_name')=='Metre fixture');assert abs(node['translation'][2]+10)<1e-5,node
 assert state==(c.scene,c.view_layer.objects.active,tuple(c.selected_objects),len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.cameras),len(bpy.data.scenes))
 try:review_export.export(c,path)
 except ValueError:pass
 else:raise AssertionError('Overwrite allowed')
 assert bpy.ops.beam.export_review(directory=str(Path(tmp)/'R03'))=={'FINISHED'}
 second=json.loads((Path(tmp)/'R03/manifest.json').read_text());assert second['project_uuid']==m['project_uuid'] and second['revision_uuid']!=m['revision_uuid']
 # Inject a serialization failure after GLB creation; no partial package or temp scene remains.
 original_dumps=review_export.json.dumps
 def failure(*args,**kwargs):raise ValueError('Injected failure')
 review_export.json.dumps=failure
 try:
  try:review_export.export(c,Path(tmp)/'R02')
  except ValueError:pass
  else:raise AssertionError('Expected failed export')
 finally:review_export.json.dumps=original_dumps
 assert not (Path(tmp)/'R02').exists()
 assert not list(Path(tmp).glob('.beam-review-*'))
 assert state==(c.scene,c.view_layer.objects.active,tuple(c.selected_objects),len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.cameras),len(bpy.data.scenes))
print('PASS Review Package: centimetre scene to metre GLB/JSON; shifted orthographic projection; identity; context restoration; immutable revision and failed-export cleanup')
addon.unregister()
