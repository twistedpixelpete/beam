"""Native duplicates, paste, independence, rename safety and CSV contract."""
exec((root/'tests/blender_m3.py').read_text())
from projection_study.utils import PALETTE
from projection_study.export_table import HEADER
from projection_study.projector_object import projectors
import csv
source=o
settings=dict(resolution_x=2560,resolution_y=1600,throw_ratio=1.4,shift_h=8,shift_v=-5,
              brightness=72,lumens=18000,stack=2,output_mode='COLOR_GRID',notes='Keep technical data')
for key,value in settings.items(): setattr(source.ps,key,value)
source.ps.colour=(.31,.42,.53)
identity=source.ps.uuid

def select(obj):
    for other in bpy.context.selected_objects: other.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    runtime.refresh()

def verify(obj):
    assert obj!=source and obj.ps.uuid!=identity
    assert obj.data!=source.data
    assert runtime.optics(obj).data!=runtime.optics(source).data
    expected=PALETTE[(int(obj.ps.identifier[2:])-1)%len(PALETTE)]
    assert all(abs(a-b)<1e-6 for a,b in zip(obj.ps.colour,expected))
    for key,value in settings.items():
        got=getattr(obj.ps,key)
        assert abs(got-value)<1e-5 if isinstance(value,(int,float)) else got==value,(key,got,value)
    obj.ps.throw_ratio=2.3
    assert abs(source.ps.throw_ratio-1.4)<1e-5
    assert obj.data.materials[0]!=source.data.materials[0]
    assert obj.ps.identifier==obj.name

for operation in ('ADDON','SHIFT_D','LINKED','PASTE'):
    select(source)
    if operation=='ADDON': bpy.ops.ps.duplicate()
    elif operation=='SHIFT_D': bpy.ops.object.duplicate(linked=False)
    elif operation=='LINKED': bpy.ops.object.duplicate(linked=True)
    else:
        assert bpy.ops.view3d.copybuffer()=={'FINISHED'}
        assert bpy.ops.view3d.pastebuffer()=={'FINISHED'}
    bpy.context.view_layer.update(); runtime.refresh(True)
    copy=bpy.context.view_layer.objects.active
    verify(copy)
all_projectors=projectors(bpy.context.scene)
assert len(all_projectors)==5
assert len({p.ps.uuid for p in all_projectors})==5
assert len({p.ps.identifier for p in all_projectors})==5
source.name='Renamed projector body'
bpy.context.view_layer.update(); runtime.refresh(True)
assert source.ps.uuid==identity and source.ps.identifier=='PJ01'
assert runtime.CACHE[source.as_pointer()]['hit']
select(source); bpy.ops.ps.lock()
assert all(source.lock_location) and all(source.lock_rotation)
assert bpy.ops.ps.move(distance=1)=={'CANCELLED'}
bpy.ops.ps.lock(); assert not any(source.lock_location)
path=root/'work/contract04.txt'
path.unlink(missing_ok=True)
assert bpy.ops.ps.export(filepath=str(path))=={'FINISHED'}
assert not path.exists()
with path.with_suffix('.csv').open() as stream: rows=list(csv.reader(stream))
assert rows[0]==list(HEADER) and len(rows)==6
assert rows[1][-3:-1]==['mm','lux'] and rows[1][-1]==identity
assert bpy.ops.ps.export.get_rna_type().name=='Export CSV'
print('MILESTONE 12 native Shift-D / Alt-D / copy-paste / colour / independence / rename / CSV PASS')

# A paste into another scene must not retain the source UUID/identifier.
select(source); bpy.ops.view3d.copybuffer()
original_scene=bpy.context.scene
new_scene=bpy.data.scenes.new('Paste destination')
bpy.context.window.scene=new_scene; runtime.refresh(True)
bpy.ops.view3d.pastebuffer()
bpy.context.view_layer.update(); runtime.refresh(True)
pasted=bpy.context.view_layer.objects.active
assert pasted.ps.uuid!=identity and pasted.ps.identifier!='PJ01'
assert tuple(pasted.ps.colour)!=tuple(source.ps.colour)
bpy.context.window.scene=original_scene
for item in list(new_scene.objects): bpy.data.objects.remove(item,do_unlink=True)
bpy.data.scenes.remove(new_scene); runtime.refresh(True)
print('Cross-scene paste identity PASS')
