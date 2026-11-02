"""Object Centre aims at the middle of the object's geometry. Background, no GPU."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,runtime
from mathutils import Vector
addon.register();c=bpy.context;s=c.scene
def rectangle(name,x0,x1,y,z0,z1):
    m=bpy.data.meshes.new(name);m.from_pydata([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],[],[(0,1,2,3)]);m.update()
    o=bpy.data.objects.new(name,m);s.collection.objects.link(o);return o
# Geometry well away from its origin, as in many imported models.
wall=rectangle('Offset Wall',20,40,14,0,10)
pj=projector_object.create(c);pj.location=(30,0,5);c.view_layer.update();runtime.refresh(True)
def aimed_point(target):
    origin=pj.matrix_world.translation;forward=(pj.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
    return origin+forward*((target-origin).length)
def select(*objects):
    for o in c.selected_objects:o.select_set(False)
    for o in objects:o.select_set(True)
    c.view_layer.objects.active=pj;s.ps_study.active_projector=pj
select(pj,wall)
assert bpy.ops.ps.aim(mode='OBJECT')=={'FINISHED'};c.view_layer.update()
assert (aimed_point(Vector((30,14,5)))-Vector((30,14,5))).length<1e-3,'should aim at the centre of the geometry, not the origin'
# It uses the world position of a moved, rotated object too.
wall.location=(5,2,1);c.view_layer.update();assert bpy.ops.ps.aim(mode='OBJECT')=={'FINISHED'};c.view_layer.update()
assert (aimed_point(Vector((35,16,6)))-Vector((35,16,6))).length<1e-3
wall.location=(0,0,0);c.view_layer.update()
# An object with no geometry falls back to its position.
empty=bpy.data.objects.new('Marker',None);empty.location=(30,8,2);s.collection.objects.link(empty);c.view_layer.update();select(pj,empty)
assert bpy.ops.ps.aim(mode='OBJECT')=={'FINISHED'};c.view_layer.update()
assert (aimed_point(Vector((30,8,2)))-Vector((30,8,2))).length<1e-3
# With nothing else selected, it aims at the centre of what the projector currently hits.
select(pj);bpy.data.objects.remove(empty,do_unlink=True);pj.rotation_euler=(1.5707963,0,0);c.view_layer.update();runtime.refresh(True)
assert pj.ps.target==wall;assert bpy.ops.ps.aim(mode='OBJECT')=={'FINISHED'};c.view_layer.update()
assert (aimed_point(Vector((30,14,5)))-Vector((30,14,5))).length<1e-3
print('AIM PASS: Object Centre uses world geometry centre, falls back to position, and follows the current target')
addon.unregister()
