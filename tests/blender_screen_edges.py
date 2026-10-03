"""Focused failure, selected-face, distance-UV and detailed-export checks."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects as so,screen_surface as ss,screen_uv as uv,screen_export as ex,screen_data as sd,screen_math as sm
addon.register();scene=bpy.context.scene;p=scene.beam_screen_draft
p.screen_type='ARC';p.radius=10;p.angle=90
arc=so.create(bpy.context,p)
assert arc.data.vertices[0].co.y<arc.data.vertices[len(arc.data.vertices)//4].co.y # concave endpoints closer to viewer -Y
p.screen_type='CLOSED';p.angle=360
ring=so.create(bpy.context,p)
for f in ring.data.polygons:assert f.normal.dot(Vector((-f.center.x,-f.center.y,0)))>0
# Selected-face extraction from Edit Mode preserves source mesh and live selection.
p.screen_type='FLAT';p.segments=4;p.vertical_segments=3;p.height=4;p.width=6
src=so.create(bpy.context,p);src.beam_screen.is_screen=False
for f in src.data.polygons:f.select=f.index in {0,1,4,5}
so.select(bpy.context,src);bpy.ops.object.mode_set(mode='EDIT')
import bmesh
bm=bmesh.from_edit_mesh(src.data);bm.faces.ensure_lookup_table()
for v in bm.verts:v.select_set(False)
for f in bm.faces:f.select_set(f.index in {0,1,4,5})
bmesh.update_edit_mesh(src.data)
p.screen_type='SURFACE';p.source=src;p.selected_faces=True;p.uv_method='PROJECTED'
extracted=so.create(bpy.context,p);assert len(extracted.data.polygons)==4 and len(src.data.polygons)==12
assert src.mode=='EDIT';bpy.ops.object.mode_set(mode='OBJECT')
# Failure cleans up temporary datablocks.
n=(len(bpy.data.objects),len(bpy.data.meshes));p.uv_method='EXISTING';src.data.uv_layers.remove(src.data.uv_layers.active)
try:so.create(bpy.context,p);raise AssertionError('Missing UV should fail')
except ValueError:pass
assert n==(len(bpy.data.objects),len(bpy.data.meshes))
# Explicitly reject ambiguous topology; diagnostics detect overlap/mirrors/zero UV.
mesh=bpy.data.meshes.new('triangle');mesh.from_pydata([(0,0,0),(1,0,0),(0,0,1)],[],[(0,1,2)])
try:uv.distance_grid(mesh);raise AssertionError('Non-quad grid must reject')
except ValueError:pass
uv.assign(mesh,[[(0,0),(0,1),(1,0)]]);assert any('reversed' in e for e in uv.diagnose(mesh)['errors'])
uv.assign(mesh,[[(0,0),(0,0),(0,0)]]);assert any('zero-area UV' in e for e in uv.diagnose(mesh)['errors'])
# Poly and NURBS paths use evaluated distances.
for kind in ('POLY','NURBS'):
 c=bpy.data.curves.new(kind,'CURVE');c.dimensions='3D';s=c.splines.new(kind);s.points.add(3)
 for point,co in zip(s.points,[(0,0,0,1),(1,1,0,1),(4,1,0,1),(6,0,0,1)]):point.co=co
 if kind=='NURBS':s.order_u=3;s.use_endpoint_u=True
 o=bpy.data.objects.new(kind,c);scene.collection.objects.link(o);p.screen_type='CURVE';p.source=o;p.selected_faces=False
 result=so.create(bpy.context,p);assert len(result.data.polygons)>0 and not uv.diagnose(result.data)['errors']
# Cabinet detail export is independent of visibility and distinct from production.
p.screen_type='ARC';p.category='LED';p.columns=20;p.rows=8;p.led_geometry='FACETED';p.show_detail=False
led=so.create(bpy.context,p);led.location=(2,4,1);bpy.context.view_layer.update()
folder=root/'work/screen-edges';folder.mkdir(exist_ok=True)
for fmt in ('OBJ','FBX'):
 path=ex.export(bpy.context,led,folder/('detailed.'+fmt.lower()),fmt,'DETAILED',overwrite=True)
 if fmt=='OBJ':bpy.ops.wm.obj_import(filepath=str(path),forward_axis='Y',up_axis='Z')
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 selected=list(bpy.context.selected_objects);assert len(selected)==2,(fmt,len(selected));assert sum(len(o.data.polygons) for o in selected)==20*8*6
 for o in selected:d=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(d)
assert not any(s.name.startswith('.Beam export') for s in bpy.data.scenes)
# Scene units export roundtrip at centimetres, non-unit and mirrored scale.
scene.unit_settings.scale_length=.01;p.screen_type='FLAT';p.category='PROJECTION';p.source=None
small=so.create(bpy.context,p);small.scale=(2,1,1);small.location=(100,200,300);bpy.context.view_layer.update()
for fmt in ('OBJ','FBX'):
 path=ex.export(bpy.context,small,folder/('centimetres.'+fmt.lower()),fmt,overwrite=True)
 clean=bpy.data.scenes.new('Roundtrip SI');bpy.context.window.scene=clean
 if fmt=='OBJ':bpy.ops.wm.obj_import(filepath=str(path),forward_axis='Y',up_axis='Z')
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 o=next(o for o in clean.objects if o.type=='MESH');bpy.context.view_layer.update();assert abs(o.dimensions.x-12)<1e-4,(fmt,o.dimensions.x)
 points=[o.matrix_world@v.co for v in o.data.vertices];assert abs(min(v.z for v in points)-3)<1e-4
 bpy.context.window.scene=scene
 for item in list(clean.objects):d=item.data;bpy.data.objects.remove(item,do_unlink=True);bpy.data.meshes.remove(d)
 bpy.data.scenes.remove(clean)
# Clipboard duplication including fresh UUID after scene switch.
so.select(bpy.context,small);original=small.beam_screen.uuid;bpy.ops.view3d.copybuffer()
new=bpy.data.scenes.new('Paste');bpy.context.window.scene=new;bpy.ops.view3d.pastebuffer();so.reconcile()
copy=bpy.context.object;assert copy.beam_screen.uuid!=original and copy.data!=small.data
bpy.context.window.scene=scene
# Save/reload metadata and monotonic identifier counter.
path=folder/'reload.blend';ids={o.beam_screen.identifier for o in scene.objects if o.beam_screen.is_screen};counter=scene.get('beam_screen_counter')
bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path));so.reconcile()
assert {o.beam_screen.identifier for o in bpy.context.scene.objects if o.beam_screen.is_screen}==ids
assert bpy.context.scene.get('beam_screen_counter')==counter
print('SCREEN EDGE ACCEPTANCE PASS',flush=True)
