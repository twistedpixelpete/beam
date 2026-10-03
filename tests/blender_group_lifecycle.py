"""Beam lifecycle acceptance, in a disposable background process."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,blend_groups as groups,group_lifecycle as life,local_orientation
from projection_study.projector_object import create
from projection_study.export_json import document
from projection_study.utils import PALETTE
addon.register();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.transform_orientation_slots[0].type='NORMAL'
def refresh():bpy.context.view_layer.update();runtime.refresh(True)
def same(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))<1e-5
def select(o):
    for x in bpy.context.selected_objects:x.select_set(False)
    o.select_set(True);bpy.context.view_layer.objects.active=o
    refresh()
a=create(bpy.context);a.ps.throw_ratio=1.3;a.ps.shift_h=7;a.ps.notes='Per-member note';a.ps.brightness=73;a.ps.stack=2
assert scene.transform_orientation_slots[0].type=='LOCAL'
a.ps.image=bpy.data.images.new('Independent content',width=8,height=8)
objects=[a,create(bpy.context,a),create(bpy.context,a)];refresh()
g=groups.create(bpy.context,objects,'HORIZONTAL',3,1,17,'PERCENT');g.notes='Group note';g.preview_edge_blend=True
g.controller.rotation_euler.z=.4;objects[2].location.x=.15;objects[2].rotation_euler.z=.12;refresh()
original_ids={o.ps.uuid for o in objects};original_world=[o.matrix_world.copy() for o in objects]
# Existing membership addition preserves every setting, identity, colour and pose.
four=create(bpy.context,a);four.location=(31,-4,3);four.rotation_euler=(.8,.3,.2);refresh()
world=four.matrix_world.copy();identity=four.ps.uuid;colour=tuple(four.ps.colour)
life.add_member(g,four,bpy.context);refresh()
assert same(world,four.matrix_world) and four.ps.uuid==identity and tuple(four.ps.colour)==colour
for o,w in zip(objects,original_world):assert same(o.matrix_world,w)
assert len(g.members)==4
# Reflow preserves manual offsets; removal preserves world transforms and UUIDs.
basis=objects[2].matrix_basis.copy();groups.apply_layout(g,bpy.context);refresh();assert same(objects[2].matrix_basis,basis)
def remove(group,obj):
    world=obj.matrix_world.copy();identity=obj.ps.uuid
    groups.remove_member(group,next(i for i,m in enumerate(group.members) if m.projector==obj));refresh()
    assert obj.parent is None and same(world,obj.matrix_world) and obj.ps.uuid==identity
remove(g,objects[1]);remove(g,a)
assert g.anchor_uuid==g.members[0].projector.ps.uuid
assert len(document(bpy.context)['blend_groups'][0]['members'])==2
# New projector adds one member in layout without moving existing members.
before=[m.projector.matrix_world.copy() for m in g.members]
new=life.add_new(g,bpy.context);refresh()
for m,w in zip(g.members,before):assert same(m.projector.matrix_world,w)
assert new.ps.uuid not in original_ids and new.ps.notes=='Per-member note'
# Dedicated duplication retains each member's basis and independent mutable data.
source_members=groups.member_objects(g);g.members[0].projector.location.x+=.15;refresh()
copy=life.duplicate(g,bpy.context);refresh()
assert copy.name=='BG02' and copy.uuid!=g.uuid and copy.controller!=g.controller
assert copy.overlap_h==g.overlap_h and copy.notes==g.notes and copy.preview_edge_blend
for source,member in zip(g.members,copy.members):
    x,y=source.projector,member.projector
    assert x.ps.image!=y.ps.image
    assert x.ps.uuid!=y.ps.uuid and x.data!=y.data and same(x.matrix_basis,y.matrix_basis)
    assert y.ps.throw_ratio==x.ps.throw_ratio and y.ps.shift_h==x.ps.shift_h and y.ps.notes==x.ps.notes
    expected=PALETTE[(int(y.ps.identifier[2:])-1)%len(PALETTE)]
    assert max(abs(a-b) for a,b in zip(y.ps.colour,expected))<1e-6
    assert all(a.material!=b.material for a,b in zip(x.material_slots,y.material_slots))
worlds=[m.projector.matrix_world.copy() for m in g.members];copy.controller.location.y+=3;refresh()
assert all(same(m.projector.matrix_world,w) for m,w in zip(g.members,worlds))
copy.members[1].projector.ps.throw_ratio=2.5;assert g.members[1].projector.ps.throw_ratio!=2.5
old_pixel=g.members[1].projector.ps.image.pixels[0]
copy.members[1].projector.ps.image.pixels[0]=.75
assert g.members[1].projector.ps.image.pixels[0]==old_pixel
# Native controller duplication must instantiate an independent complete rig.
select(g.controller);bpy.ops.object.duplicate(linked=True);native=bpy.context.object;refresh()
assert len(scene.ps_study.blend_groups)==3
ng=next(x for x in scene.ps_study.blend_groups if x.controller==native)
assert ng.name=='BG03' and len(ng.members)==len(g.members)
assert {m.projector.ps.uuid for m in ng.members}.isdisjoint({m.projector.ps.uuid for m in g.members})
# Native hierarchy duplication should neither detach nor double-count its copies.
select(g.controller)
for obj in g.controller.children_recursive:obj.select_set(True)
bpy.ops.object.duplicate();refresh()
assert len(scene.ps_study.blend_groups)==4
assert len([o for o in scene.objects if o.ps.is_projector])==2+sum(len(x.members) for x in scene.ps_study.blend_groups)
# Native clipboard controller copy/paste including a different scene.
select(g.controller);bpy.ops.view3d.copybuffer()
other=bpy.data.scenes.new('Paste target');bpy.context.window.scene=other
bpy.ops.view3d.pastebuffer();refresh()
assert len(other.ps_study.blend_groups)==1
pasted=other.ps_study.blend_groups[0]
assert pasted.uuid!=g.uuid and len(pasted.members)==len(g.members)
assert all(m.projector.ps.image is not None for m in pasted.members)
assert {m.projector.ps.uuid for m in pasted.members}.isdisjoint({m.projector.ps.uuid for m in g.members})
document(bpy.context)
# Normal object selection restores previous scene orientation, including after save.
bpy.context.window.scene=scene
normal=bpy.data.objects.new('Non-Beam',None);scene.collection.objects.link(normal)
select(objects[2]);assert scene.transform_orientation_slots[0].type=='LOCAL'
select(normal);assert scene.transform_orientation_slots[0].type=='NORMAL'
select(objects[2]);local_orientation.cleanup();assert scene.transform_orientation_slots[0].type=='NORMAL'
local_orientation.resume();assert scene.transform_orientation_slots[0].type=='LOCAL'
# Reset active member clears manual translation and rotation only.
scene.ps_study.blend_group_index=0;select(objects[2]);objects[2].location.x=.9;objects[2].rotation_euler.z=.3;refresh()
id_before=objects[2].ps.uuid;notes=objects[2].ps.notes
bpy.ops.beam.group_action(action='RESET');refresh()
assert same(objects[2].matrix_basis,Matrix.Identity(4)) and objects[2].ps.uuid==id_before and objects[2].ps.notes==notes
# Native translate/rotate operators obey actual projector-local axes, parented or free.
for obj in (a,objects[2]):
    select(obj);obj.rotation_euler=(.7,.4,.2);refresh()
    before=obj.matrix_world.copy();axis=before.to_3x3().col[0].normalized()
    bpy.ops.transform.translate(value=(.4,0,0),orient_type='LOCAL',constraint_axis=(True,False,False));refresh()
    assert (obj.matrix_world.translation-before.translation-axis*.4).length<1e-5
    for axis_name in ('X','Y','Z'):
        before=obj.matrix_world.to_3x3().copy()
        bpy.ops.transform.rotate(value=.2,orient_axis=axis_name,orient_type='LOCAL');refresh()
        expected=before@Matrix.Rotation(.2,3,axis_name)
        assert max(abs(obj.matrix_world[i][j]-expected[i][j]) for i in range(3) for j in range(3))<1e-5
# Export every group with unique, resolvable identities.
data=document(bpy.context);(root/'work/lifecycle-export.json').write_text(json.dumps(data,indent=2))
# Ungroup copy leaves members intact; deleting last member retires its empty group.
scene.ps_study.blend_group_index=1;survivors=groups.member_objects(copy);uuids=[o.ps.uuid for o in survivors]
bpy.ops.beam.group_action(action='UNGROUP');refresh()
assert all(o.parent is None and o.ps.uuid==uid for o,uid in zip(survivors,uuids))
while g.members:groups.remove_member(g,len(g.members)-1)
life.prune(bpy.context);refresh();document(bpy.context)
# Exercise the actual panel operators, not just their helpers.
scene.ps_study.blend_group_index=0;select(a);pose=a.matrix_world.copy()
assert bpy.ops.beam.group_action(action='ADD_SELECTED')=={'FINISHED'}
assert same(a.matrix_world,pose)
assert bpy.ops.beam.group_action(action='ADD_NEW')=={'FINISHED'}
added=bpy.context.object;identity=added.ps.uuid;pose=added.matrix_world.copy()
assert bpy.ops.beam.group_action(action='REMOVE')=={'FINISHED'}
assert added.parent is None and added.ps.uuid==identity and same(added.matrix_world,pose)
assert bpy.ops.beam.group_action(action='DUPLICATE')=={'FINISHED'}
refresh();document(bpy.context)
# Non-default units and save/reload preserve the copy recipe and local basis.
scaled_scene=bpy.data.scenes.new('Centimetre rig');scaled_scene.unit_settings.scale_length=.01;bpy.context.window.scene=scaled_scene
scaled_objects=[create(bpy.context),create(bpy.context)];refresh()
sg=groups.create(bpy.context,scaled_objects,'VERTICAL',1,2,20,'PERCENT')
scaled_objects[1].location.x=15;refresh()
sg_copy=life.duplicate(sg,bpy.context);refresh()
assert same(sg.members[1].projector.matrix_basis,sg_copy.members[1].projector.matrix_basis)
assert abs((sg_copy.controller.matrix_world.translation-sg.controller.matrix_world.translation).length*.01-1)<1e-5
path=root/'work/lifecycle-roundtrip.blend';bpy.data.libraries.write(str(path),{scaled_scene})
with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.scenes=[scaled_scene.name]
loaded=dst.scenes[0];bpy.context.window.scene=loaded;refresh()
loaded_group=loaded.ps_study.blend_groups[0]
assert abs(loaded_group.members[1].projector.location.x-15)<1e-5
loaded_copy=life.duplicate(loaded_group,bpy.context);refresh()
loaded_group=loaded.ps_study.blend_groups[0]
assert same(loaded_group.members[1].projector.matrix_basis,loaded_copy.members[1].projector.matrix_basis)
document(bpy.context)
bpy.context.window.scene=scene;select(normal)
print('GROUP LIFECYCLE PASS: membership, anchor promotion, new projectors, offsets, independent duplicate, native linked/hierarchy/clipboard, local orientation, reset, ungroup, UUID export')
addon.unregister();assert scene.transform_orientation_slots[0].type=='NORMAL'
