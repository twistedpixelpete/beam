"""Beam deterministic groups: spacing, actual overlap, parent offsets and ungroup."""
import bpy
from mathutils import Vector
from projection_study import runtime,blend_groups as groups
from projection_study.projector_object import create
from projection_study.utils import PALETTE
from projection_study.export_json import document
scene=bpy.context.scene
mesh=bpy.data.meshes.new('Wall'); mesh.from_pydata([(-100,10,-100),(100,10,-100),(100,10,100),(-100,10,100)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Wall',mesh); scene.collection.objects.link(wall)
a=create(bpy.context); a.ps.resolution_x=3840; a.ps.resolution_y=2160; a.ps.output_mode='COLOR_GRID'; a.ps.notes='Anchor rig'
bpy.context.view_layer.update(); runtime.refresh(True)
origin=a.matrix_world.copy()
assert bpy.ops.beam.create_group(layout_type='HORIZONTAL',count=4,overlap=400)=={'FINISHED'}
g=groups.active_group(bpy.context); members=groups.member_objects(g)
assert len(members)==4 and g.anchor_uuid==a.ps.uuid
assert len({o.ps.uuid for o in members})==4
for i,obj in enumerate(members):
    assert obj.ps.identifier==f'PJ{i+1:02d}'
    assert obj.ps.resolution_x==3840 and obj.ps.output_mode=='COLOR_GRID' and obj.ps.notes=='Anchor rig'
    assert all(abs(x-y)<1e-6 for x,y in zip(obj.ps.colour,PALETTE[i]))
assert (a.matrix_world.translation-origin.translation).length<1e-5
for obj in members:
    assert obj.matrix_world.to_quaternion().rotation_difference(origin.to_quaternion()).angle<1e-5
    assert runtime.CACHE[obj.as_pointer()]['hit'], 'Group parenting must preserve projector aim'
for overlap in (600,800):
    g.overlap_h=overlap
    bpy.context.view_layer.update(); runtime.refresh(True)
    spacing=10*(1-overlap/3840)
    for i,obj in enumerate(members): assert abs(obj.matrix_world.translation.x-i*spacing)<1e-4
    pairs=groups.pair_data(g,bpy.context)
    assert len(pairs)==3
    assert all(abs(p['actual']['pixels']-overlap)<.01 for p in pairs),pairs
before=g.overlap_h
g.input_mode='PERCENT'
assert abs(g.overlap_h-before/3840*100)<1e-4
g.input_mode='METRES'; assert abs(g.overlap_h-before/3840*10)<1e-4
g.input_mode='PIXELS'; assert abs(g.overlap_h-before)<1e-3
members[2].location.x=.1
bpy.context.view_layer.update(); runtime.refresh(True)
actual=groups.pair_data(g,bpy.context)
assert abs(actual[1]['actual']['pixels']-800)>1
relative=members[2].matrix_basis.copy()
g.controller.location.x+=2; g.controller.rotation_euler.z+=.15
bpy.context.view_layer.update(); runtime.refresh(True)
assert (members[2].matrix_basis.translation-relative.translation).length<1e-6
g.overlap_h=500
assert abs(members[2].location.x-.1)<1e-5
scene.ps_study.active_projector=members[2]
# Select the member so selection synchronization cannot replace the explicit active.
for obj in bpy.context.selected_objects: obj.select_set(False)
members[2].select_set(True); bpy.context.view_layer.objects.active=members[2]; runtime.refresh()
bpy.ops.beam.group_action(action='RESET'); assert members[2].location.length<1e-6
# Native duplication of a grouped member becomes independent, not another
# object attached to the source member's mutable layout slot.
bpy.ops.object.duplicate(linked=True)
clone=bpy.context.object
bpy.context.view_layer.update(); runtime.refresh(True)
assert clone.parent is None and groups.group_for(clone) is None
assert clone.ps.uuid!=members[2].ps.uuid
bpy.data.objects.remove(clone,do_unlink=True)
metadata=scene.ps_study; metadata.project_name='Melbourne Town Hall'; metadata.revision='R02'
data=document(bpy.context)
assert data['product']=='Beam' and data['project_metadata']['project_name']=='Melbourne Town Hall'
assert len(data['blend_groups'][0]['members'])==4
# Rename and save/reload preserve stable group/member pointers and notes.
g.name='Main canvas'; group_id=g.uuid
path=str(root/'work/beam-group-roundtrip.blend'); bpy.data.libraries.write(path,{scene})
with bpy.data.libraries.load(path,link=False) as (src,dst): dst.scenes=[scene.name]
loaded=dst.scenes[0]; saved=loaded.ps_study.blend_groups[0]
assert saved.uuid==group_id and len(saved.members)==4 and saved.members[0].projector.ps.notes=='Anchor rig'
for obj in list(loaded.objects): bpy.data.objects.remove(obj,do_unlink=True)
bpy.data.scenes.remove(loaded)
world=[o.matrix_world.copy() for o in members]
bpy.ops.beam.group_action(action='UNGROUP')
bpy.context.view_layer.update()
assert not scene.ps_study.blend_groups
for obj,matrix in zip(members,world): assert obj.parent is None and (obj.matrix_world.translation-matrix.translation).length<1e-5
# Existing selection grouping preserves every transform.
g=groups.create(bpy.context,members,'HORIZONTAL',4,1,200,'PIXELS',preserve=True)
for obj,matrix in zip(members,world): assert (obj.matrix_world.translation-matrix.translation).length<1e-5
bpy.ops.beam.group_action(action='UNGROUP')
# Vertical and 3x2 array; the anchor remains fixed and both spacings are uniform.
for layout,count,cols,rows in [('VERTICAL',3,1,3),('ARRAY',6,3,2)]:
    anchor=create(bpy.context); anchor.location=(0,0,0)
    bpy.context.view_layer.update(); runtime.refresh(True)
    assert bpy.ops.beam.create_group(layout_type=layout,count=count,columns=cols,rows=rows,overlap=20,input_mode='PERCENT')=={'FINISHED'}
    group=groups.active_group(bpy.context); objs=groups.member_objects(group)
    assert len(objs)==count
    group.overlap_h=25; group.overlap_v=30
    bpy.context.view_layer.update(); runtime.refresh(True)
    inv=group.controller.matrix_world.inverted()
    for obj,(x,y) in zip(objs,groups.cells(layout,count,cols)):
        local=inv@obj.matrix_world.translation
        assert abs(local.x-x*7.5)<1e-4 and abs(local.y+y*5.625*.7)<1e-4
    bpy.ops.beam.group_action(action='UNGROUP')
print('MILESTONE 14 Beam groups / horizontal / vertical / array / offsets / actual overlap / persistence PASS')

wall.hide_set(True); bpy.context.view_layer.update(); runtime.refresh(True)
preview_group=groups.create(bpy.context,members,'HORIZONTAL',4,1,200,'PIXELS',preserve=True)
assert all(pair['reference_status']=='preview' for pair in groups.pair_data(preview_group,bpy.context))
assert groups.pair_data(preview_group,bpy.context)
bpy.ops.beam.group_action(action='UNGROUP'); wall.hide_set(False)
print('No-target group preview is explicitly marked PASS')
