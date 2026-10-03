exec((root/'tests/blender_m3.py').read_text())
original_uuid=o.ps.uuid
o.ps.colour=(.3,.4,.5)
bpy.ops.ps.duplicate()
duplicate=bpy.context.object
assert duplicate.ps.uuid!=original_uuid
assert duplicate.ps.identifier=='PJ02'
assert tuple(duplicate.ps.colour)!=tuple(o.ps.colour)
assert len(duplicate.children)==1
bpy.context.view_layer.update(); runtime.refresh(True)
old=duplicate.matrix_world.translation.copy()
bpy.ops.ps.move(distance=-1,maintain_aim=True)
bpy.context.view_layer.update()
assert abs((duplicate.matrix_world.translation-old).length-1)<1e-5
bpy.ops.ps.lock()
assert all(duplicate.lock_location)
assert bpy.ops.ps.move(distance=1)=={'CANCELLED'}
bpy.ops.ps.lock()
# Native Shift-D copies structured properties: scheduler repairs identity and helper.
bpy.ops.object.duplicate()
native=bpy.context.object
bpy.context.view_layer.update(); runtime.refresh(True)
assert len({x.ps.uuid for x in (o,duplicate,native)})==3
assert len({x.ps.identifier for x in (o,duplicate,native)})==3
assert runtime.optics(native)
o.name='Renamed by user'
bpy.context.view_layer.update(); runtime.refresh(True)
assert o.ps.uuid==original_uuid and o.ps.identifier=='PJ01'
print('MILESTONE 5 PASS')
