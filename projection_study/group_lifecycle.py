"""Editable membership and independent group copies, including native clipboard copies."""
import json
import bpy
from mathutils import Matrix,Vector
from . import blend_groups as groups
from .projector_object import create as create_projector
from .utils import new_uuid

_FIELDS=('layout','columns','rows','input_mode','previous_mode','overlap_h','overlap_v','reference_width','reference_height','reference_distance','show_overlap','preview_edge_blend','combined','notes')
_SKIP={'rna_type','is_projector','uuid','identifier','colour','target','has_target','target_point_m','target_distance_m'}
_reconciling=False
_snapshot_state={}


def resize(group):
    count=len(group.members)
    if group.layout=='HORIZONTAL': group.columns=max(1,count)
    elif group.layout=='VERTICAL': group.columns=1
    group.rows=max(1,(count+group.columns-1)//group.columns)


def sort_members(group):
    """Capture spatial order on membership edits; never resort while moving a rig."""
    if not group.controller:return
    inverse=group.controller.matrix_world.inverted_safe()
    records=[]
    for i,member in enumerate(group.members):
        if not member.projector:continue
        pos=inverse@member.projector.matrix_world.translation
        key=(pos.x,) if group.layout=='HORIZONTAL' else (-pos.y,) if group.layout=='VERTICAL' else (round(-pos.y,4),pos.x)
        records.append((key,i,member.projector.as_pointer()))
    for dest,(_,_,identity) in enumerate(sorted(records)):
        current=next(i for i,m in enumerate(group.members) if m.projector and m.projector.as_pointer()==identity)
        group.members.move(current,dest)
    resize(group)


def add_member(group,obj,context,sort=True):
    if not obj.ps.is_projector or obj.name not in context.scene.objects:raise ValueError('Choose a Beam projector in this scene')
    if groups.group_for(obj,context.scene):raise ValueError('Projector already belongs to a Blend Group; remove it first')
    if not group.controller:raise ValueError('Group controller is missing')
    context.view_layer.update();world=obj.matrix_world.copy()
    slot=bpy.data.objects.new(f'{group.name} · {obj.ps.identifier} Layout',None)
    context.scene.collection.objects.link(slot);slot['beam_layout_slot']=True;slot.hide_select=True;slot.empty_display_size=.01
    slot.parent=group.controller;slot.matrix_parent_inverse=Matrix.Identity(4)
    slot.location=group.controller.matrix_world.inverted()@world.translation
    member=group.members.add();member.projector=obj;member.projector_uuid=obj.ps.uuid;member.slot=slot
    obj.parent=slot;obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.matrix_basis=(group.controller.matrix_world@slot.matrix_basis).inverted()@world
    context.view_layer.update()
    if sort:sort_members(group)
    resize(group)
    snapshot(group,context)
    return member


def add_new(group,context):
    template=next((m.projector for m in group.members if m.projector and m.projector.ps.uuid==group.anchor_uuid),None)
    if not template:raise ValueError('Group has no valid anchor')
    from . import runtime
    runtime.refresh(True)
    obj=create_projector(context,template)
    add_member(group,obj,context,sort=False)
    # Place only the new member. Existing projectors must not be silently reflowed.
    values=groups.dimensions(group,context)
    _,h,v=values;unit=context.scene.unit_settings.scale_length
    spacing=Vector(((group.reference_width-h['metres'])/unit,-(group.reference_height-v['metres'])/unit,0))
    cells=groups.cells(group.layout,len(group.members),group.columns)
    anchor_index=next(i for i,m in enumerate(group.members) if m.projector==template)
    base=group.members[anchor_index].slot.location-Vector((cells[anchor_index][0]*spacing.x,cells[anchor_index][1]*spacing.y,0))
    member=group.members[-1];col,row=cells[-1]
    member.slot.location=base+Vector((col*spacing.x,row*spacing.y,0));obj.matrix_basis=Matrix.Identity(4)
    context.view_layer.update();runtime.invalidate();snapshot(group,context)
    return obj


def reset_member(group,obj,context):
    """Reposition only this member; reset its manual basis, preserving peers."""
    values=groups.dimensions(group,context)
    if not values:return
    anchor,h,v=values;unit=context.scene.unit_settings.scale_length
    positions=groups.cells(group.layout,len(group.members),group.columns)
    ai=next(i for i,m in enumerate(group.members) if m.projector==anchor)
    index=next(i for i,m in enumerate(group.members) if m.projector==obj)
    dx=(group.reference_width-h['metres'])/unit;dy=-(group.reference_height-v['metres'])/unit
    base=group.members[ai].slot.location-Vector((positions[ai][0]*dx,positions[ai][1]*dy,0))
    col,row=positions[index];group.members[index].slot.location=base+Vector((col*dx,row*dy,0))
    obj.matrix_basis=Matrix.Identity(4)


def prune(context):
    settings=context.scene.ps_study
    for i in reversed(range(len(settings.blend_groups))):
        group=settings.blend_groups[i]
        for j in reversed(range(len(group.members))):
            obj=group.members[j].projector
            if not obj or obj.name not in context.scene.objects or not obj.ps.is_projector:
                groups.remove_member(group,j)
        if not group.controller or not group.members:
            while group.members:groups.remove_member(group,len(group.members)-1)
            if group.controller:
                for child in list(group.controller.children):
                    world=child.matrix_world.copy();child.parent=None;child.matrix_world=world
                bpy.data.objects.remove(group.controller,do_unlink=True)
            if groups.solo_uuid==group.uuid:groups.solo_uuid=None
            settings.blend_groups.remove(i)
    index=min(settings.blend_group_index,max(0,len(settings.blend_groups)-1))
    if settings.blend_group_index!=index:settings.blend_group_index=index


def snapshot_if_needed(group,context,force=False):
    if not group.controller:return
    key=group.controller.as_pointer()
    state=(group.uuid,group.anchor_uuid,tuple(getattr(group,k) for k in _FIELDS),tuple(m.projector_uuid for m in group.members))
    if force or _snapshot_state.get(key)!=state or not group.controller.get('beam_group_recipe'):
        snapshot(group,context)
        _snapshot_state[key]=state


def snapshot(group,context):
    """Portable controller recipe lets a copied controller carry the complete rig."""
    if not group.controller:return
    unit=context.scene.unit_settings.scale_length
    members=[]
    for i,m in enumerate(group.members):
        obj=m.projector
        if not obj or not m.slot:return
        settings={}
        for prop in obj.ps.bl_rna.properties:
            key=prop.identifier
            if key in _SKIP or prop.is_readonly or prop.type=='POINTER':continue
            value=getattr(obj.ps,key)
            settings[key]=list(value) if getattr(prop,'is_array',False) else value
        members.append(dict(source_uuid=obj.ps.uuid,settings=settings,slot=groups.matrix_metres(group.controller.matrix_world.inverted_safe()@m.slot.matrix_world,unit),
            basis=groups.matrix_metres(obj.matrix_basis,unit),parent_inverse=groups.matrix_metres(obj.matrix_parent_inverse,unit),anchor=obj.ps.uuid==group.anchor_uuid))
        image_key=f'beam_member_image_{i}'
        if group.controller.get(image_key)!=obj.ps.image:
            if obj.ps.image:group.controller[image_key]=obj.ps.image
            elif image_key in group.controller:del group.controller[image_key]
    data=dict(version=1,settings={k:getattr(group,k) for k in _FIELDS},world=groups.matrix_metres(group.controller.matrix_world,unit),members=members)
    for key in list(group.controller.keys()):
        if key.startswith('beam_member_image_') and key.rsplit('_',1)[-1].isdigit() and int(key.rsplit('_',1)[-1])>=len(members):del group.controller[key]
    encoded=json.dumps(data,sort_keys=True)
    if group.controller.get('beam_group_recipe')!=encoded:group.controller['beam_group_recipe']=encoded
    if group.controller.get('beam_group_uuid')!=group.uuid:group.controller['beam_group_uuid']=group.uuid


def matrix_units(rows,unit):
    m=Matrix(rows)
    m.translation/=unit
    return m


def instantiate(recipe,context,source_controller,controller=None,offset=True):
    settings=context.scene.ps_study;unit=context.scene.unit_settings.scale_length
    name=groups.next_group_name(context.scene)
    group=settings.blend_groups.add();group.uuid=new_uuid();group.name=name
    if controller is None:
        controller=bpy.data.objects.new(name,None);context.scene.collection.objects.link(controller)
        controller.matrix_world=matrix_units(recipe['world'],unit)
    else:controller.name=name
    group.controller=controller;controller['beam_group_uuid']=group.uuid
    controller.empty_display_type='PLAIN_AXES';controller.empty_display_size=.5;controller.lock_scale=(True,)*3
    if offset:controller.matrix_world.translation+=controller.matrix_world.to_quaternion()@Vector((1/unit,0,0))
    old=groups._updating;groups._updating=True
    try:
        for key,value in recipe['settings'].items():setattr(group,key,value)
        for i,item in enumerate(recipe['members']):
            obj=create_projector(context)
            for key,value in item['settings'].items():setattr(obj.ps,key,value)
            image=source_controller.get(f'beam_member_image_{i}')
            if image:obj.ps.image=image.copy()
            slot=bpy.data.objects.new(f'{name} · {obj.ps.identifier} Layout',None);context.scene.collection.objects.link(slot)
            slot['beam_layout_slot']=True;slot.hide_select=True;slot.empty_display_size=.01
            slot.parent=controller;slot.matrix_parent_inverse=Matrix.Identity(4);slot.matrix_basis=matrix_units(item['slot'],unit)
            obj.parent=slot;obj.matrix_parent_inverse=matrix_units(item['parent_inverse'],unit);obj.matrix_basis=matrix_units(item['basis'],unit)
            member=group.members.add();member.projector=obj;member.projector_uuid=obj.ps.uuid;member.slot=slot
            if item['anchor']:group.anchor_uuid=obj.ps.uuid
    finally:groups._updating=old
    resize(group);settings.blend_group_index=len(settings.blend_groups)-1
    context.view_layer.update()
    for obj in context.selected_objects:obj.select_set(False)
    controller.select_set(True);context.view_layer.objects.active=controller
    snapshot(group,context)
    return group


def duplicate(group,context):
    context.view_layer.update();snapshot(group,context)
    return instantiate(json.loads(group.controller['beam_group_recipe']),context,group.controller)


def defer_native_copy(context):
    """Never replace native duplicate objects while a modal transform owns them."""
    registered={g.controller.as_pointer() for scene in bpy.data.scenes for g in scene.ps_study.blend_groups if g.controller}
    pending=any(o.get('beam_group_recipe') and o.get('beam_group_uuid') and o.as_pointer() not in registered for o in context.scene.objects)
    if not pending:return False
    return any(any(word in (getattr(op,'bl_idname','')+' '+op.bl_rna.identifier).upper() for word in ('TRANSFORM','DUPLICATE'))
               for window in context.window_manager.windows for op in getattr(window,'modal_operators',()))


def reconcile(context):
    """Convert native Shift-D/Alt-D/pasted controllers into complete new groups.

    Rebuild only Beam-owned descendants of the copied controller. This avoids
    sharing source members and avoids counting hierarchy duplicates twice.
    """
    global _reconciling
    if _reconciling:return
    _reconciling=True
    try:
        registered={g.controller.as_pointer() for scene in bpy.data.scenes for g in scene.ps_study.blend_groups if g.controller}
        for controller in [o for o in context.scene.objects if o.get('beam_group_uuid') and o.get('beam_group_recipe')]:
            if controller.as_pointer() in registered or not controller.get('beam_group_uuid') or not controller.get('beam_group_recipe'):continue
            recipe=json.loads(controller['beam_group_recipe'])
            if recipe.get('version')!=1:continue
            # Preserve a native/user-provided translation; offset coincident copies.
            original=matrix_units(recipe['world'],context.scene.unit_settings.scale_length)
            coincident=(controller.matrix_world.translation-original.translation).length<1e-5
            descendants=list(controller.children_recursive)
            # Hidden layout slots may not be selected by native hierarchy duplication.
            # Those new projectors still point to source slots: identify their copied
            # UUIDs, excluding every registered source member, before identity repair.
            source_ids={m.get('source_uuid') for m in recipe['members']}
            owned={m.projector.as_pointer() for g in context.scene.ps_study.blend_groups for m in g.members if m.projector}
            extras=[o for o in context.selected_objects if o.ps.is_projector and o.ps.uuid in source_ids and o.as_pointer() not in owned and o not in descendants]
            for obj in extras:
                descendants.extend([obj,*obj.children_recursive])
            # Recipe image dependencies belong to the controller and survive cleanup.
            deleting=[o for o in descendants if o.ps.is_projector or o.get('beam_layout_slot') or o.get('ps_helper')]
            for obj in descendants:
                if obj not in deleting and obj.parent in deleting:
                    world=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=world
            for obj in reversed(deleting):bpy.data.objects.remove(obj,do_unlink=True)
            instantiate(recipe,context,controller,controller,offset=coincident)
    finally:_reconciling=False


class BEAM_OT_select_member(bpy.types.Operator):
    bl_idname='beam.select_member';bl_label='Select Blend Member';bl_options={'UNDO'}
    index:bpy.props.IntProperty()
    def execute(self,context):
        group=groups.active_group(context)
        if not group or not 0<=self.index<len(group.members):return {'CANCELLED'}
        obj=group.members[self.index].projector
        if not obj:return {'CANCELLED'}
        for item in context.selected_objects:item.select_set(False)
        obj.hide_set(False);obj.select_set(True);context.view_layer.objects.active=obj;context.scene.ps_study.active_projector=obj
        from .local_orientation import sync
        sync(context)
        return {'FINISHED'}

CLASSES=(BEAM_OT_select_member,)
