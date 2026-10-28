"""Body visibility preserves optics, edited meshes, copies and saved files."""
import bpy, sys, tempfile
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import projection_study as addon
from projection_study import runtime, scene_geometry, target_raycast
from projection_study.projector_object import create
addon.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
p=create(bpy.context)
assert p.ps.show_body and len(p.data.polygons)>0
mesh=p.data; mesh.vertices[0].co.x=-.7
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,10,0), rotation=(1.5707963267948966,0,0))
wall=bpy.context.object; wall.name='Receiver'
def refresh():
    bpy.context.view_layer.update(); runtime.refresh(True)
    return runtime.CACHE[p.as_pointer()]
before=refresh()
p.ps.show_body=True
assert p.data==mesh  # Reapplying the same value must not rebuild edited geometry.
p.ps.show_body=False
after=refresh()
assert p.visible_get() and not p.data.vertices and p.ps.hidden_body_mesh==mesh
for key in ('metrics','hit','origin','rotation','corners','beam_corners'):
    assert before[key]==after[key], key
assert runtime.optics(p)
p.ps.show_body=True
assert p.data==mesh and p.data.vertices[0].co.x<-.69
p.ps.show_body=False
copy=create(bpy.context, source=p)
assert not copy.ps.show_body and copy.ps.hidden_body_mesh!=mesh
copy.ps.show_body=True
copy.data.vertices[0].co.x=-2
p.ps.show_body=True
assert p.data.vertices[0].co.x> -1
scene.ps_study.create_projector_body=False
empty=create(bpy.context)
assert not empty.ps.show_body and not empty.data.vertices and not empty.data.materials
assert empty.ps.hidden_body_mesh is None
empty.ps.show_body=True
assert empty.data.polygons and len(empty.data.materials)==2
# A custom child in front of the projector must not block the receiver.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,3,0))
custom=bpy.context.object; world=custom.matrix_world.copy()
custom.parent=p; custom.matrix_world=world
refresh(); scene_geometry.prepare()
assert custom.as_pointer() not in scene_geometry.SURFACES
assert target_raycast.cast(Vector((0,0,0)), Vector((0,1,0)))[3]=='Receiver'
# Nested parts are excluded too; detaching restores their receiver role.
bpy.ops.object.empty_add(); holder=bpy.context.object; holder.parent=p
custom.parent=holder; custom.matrix_world=world
refresh(); assert custom.as_pointer() not in scene_geometry.SURFACES
custom.parent=None; custom.matrix_world=world
refresh(); assert custom.as_pointer() in scene_geometry.SURFACES
assert target_raycast.cast(Vector((0,0,0)), Vector((0,1,0)))[3]==custom.name
custom.parent=p; custom.matrix_world=world
# Blender-native copies must not share the preserved body.
p.ps.show_body=False
native=p.copy(); native.data=p.data.copy(); scene.collection.objects.link(native)
refresh()
assert native.ps.hidden_body_mesh!=p.ps.hidden_body_mesh
# Old files: absent property defaults to visible without changing their mesh.
legacy=create(bpy.context); legacy.ps.show_body=True
if 'show_body' in legacy.ps: del legacy.ps['show_body']
legacy_mesh=legacy.data
refresh(); assert legacy.ps.show_body and legacy.data==legacy_mesh
# Save/reopen with a hidden edited body and attached model.
pname=p.name; meshname=p.ps.hidden_body_mesh.name
with tempfile.TemporaryDirectory() as folder:
    path=str(Path(folder)/'body-check.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    p=bpy.data.objects[pname]
    assert not p.ps.show_body and not p.data.vertices
    assert p.ps.hidden_body_mesh.name==meshname
    p.ps.show_body=True
    assert p.data.vertices[0].co.x<-.69
print('PASS: body controls, unchanged optics, custom model exclusion, independent duplicates, legacy defaults and reopen')
addon.unregister()
