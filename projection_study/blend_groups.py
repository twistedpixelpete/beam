"""Blend controllers own layout slots; projector local transforms remain editable."""
import bpy
from mathutils import Matrix,Vector
from bpy.props import StringProperty,PointerProperty,CollectionProperty,EnumProperty,IntProperty,FloatProperty,BoolProperty
from .utils import new_uuid
from .blend_math import overlap_values,cells,adjacent,intersection

solo_uuid=None
_updating=False

def redraw(self,context):
    if context and context.screen:
        for area in context.screen.areas:
            if area.type=='VIEW_3D': area.tag_redraw()


def changed(self,context):
    if context and not _updating:
        apply_layout(self,context)

def units_changed(self,context):
    global _updating
    if _updating: return
    members=member_objects(self)
    if not members: self.previous_mode=self.input_mode; return
    anchor=next((o for o in members if o.ps.uuid==self.anchor_uuid),members[0])
    old=self.previous_mode; _updating=True
    try:
        for key,pixels,length in [('overlap_h',anchor.ps.resolution_x,self.reference_width),('overlap_v',anchor.ps.resolution_y,self.reference_height)]:
            values=overlap_values(getattr(self,key),old,pixels,length)
            field={'PIXELS':'pixels','PERCENT':'percent','METRES':'metres'}[self.input_mode]
            setattr(self,key,values[field])
        self.previous_mode=self.input_mode
    finally: _updating=False
    redraw(self,context)

class BeamMember(bpy.types.PropertyGroup):
    projector: PointerProperty(type=bpy.types.Object)
    slot: PointerProperty(type=bpy.types.Object)
    projector_uuid: StringProperty()

class BeamBlendGroup(bpy.types.PropertyGroup):
    uuid: StringProperty()
    name: StringProperty(name='Group Name')
    controller: PointerProperty(type=bpy.types.Object)
    members: CollectionProperty(type=BeamMember)
    anchor_uuid: StringProperty()
    layout: EnumProperty(name='Layout',items=[('HORIZONTAL','Horizontal',''),('VERTICAL','Vertical',''),('ARRAY','Array','')])
    columns: IntProperty(name='Columns',default=2,min=1,max=32)
    rows: IntProperty(name='Rows',default=1,min=1,max=32)
    input_mode: EnumProperty(name='Overlap Units',description='Desired overlap in pixels, percent of the anchor image, or metres on its nominal plane',items=[('PIXELS','Pixels',''),('PERCENT','Percent',''),('METRES','Metres','')],default='PIXELS',update=units_changed)
    previous_mode: StringProperty(default='PIXELS')
    overlap_h: FloatProperty(name='Horizontal Overlap',default=200,min=0,update=changed)
    overlap_v: FloatProperty(name='Vertical Overlap',default=200,min=0,update=changed)
    reference_width: FloatProperty(default=10)
    reference_height: FloatProperty(default=5.625)
    reference_distance: FloatProperty(default=10)
    show_overlap: BoolProperty(name='Show Nominal Overlap',default=True,update=redraw)
    preview_edge_blend: BoolProperty(name='Preview Edge Blend',default=False,update=redraw)
    combined: BoolProperty(name='Combined Blend Preview',default=False,update=redraw)
    notes: StringProperty(name='Group Notes')


def member_objects(group):
    return [m.projector for m in group.members if m.projector and m.projector.ps.is_projector]

def group_for(obj,scene=None):
    return next((g for g in (scene or bpy.context.scene).ps_study.blend_groups if any(m.projector==obj for m in g.members)),None)

def active_group(context):
    s=context.scene.ps_study
    return s.blend_groups[s.blend_group_index] if 0<=s.blend_group_index<len(s.blend_groups) else None

def dimensions(group,context):
    from . import runtime
    anchor=next((m.projector for m in group.members if m.projector and m.projector.ps.uuid==group.anchor_uuid),None)
    if not anchor: return None
    record=runtime.CACHE.get(anchor.as_pointer())
    if record:
        group.reference_width=record['metrics'].width
        group.reference_height=record['metrics'].height
        group.reference_distance=record['metrics'].distance
    p=anchor.ps
    return anchor,overlap_values(group.overlap_h,group.input_mode,p.resolution_x,group.reference_width),overlap_values(group.overlap_v,group.input_mode,p.resolution_y,group.reference_height)


def apply_layout(group,context,reset=False):
    global _updating
    if _updating or not group.controller or not group.members: return
    _updating=True
    try:
        from . import runtime
        context.view_layer.update(); runtime.refresh()
        values=dimensions(group,context)
        if not values: return
        anchor,h,v=values; unit=context.scene.unit_settings.scale_length
        spacing=Vector(((group.reference_width-h['metres'])/unit,-(group.reference_height-v['metres'])/unit,0))
        positions=cells(group.layout,len(group.members),group.columns)
        anchor_index=next(i for i,m in enumerate(group.members) if m.projector==anchor)
        anchor_slot=group.members[anchor_index].slot
        anchor_position=anchor_slot.location-Vector((positions[anchor_index][0]*spacing.x,positions[anchor_index][1]*spacing.y,0))
        for member,(column,row) in zip(group.members,cells(group.layout,len(group.members),group.columns)):
            obj=member.projector; slot=member.slot
            if not obj or not slot or obj==anchor: continue
            slot.location=anchor_position+Vector((column*spacing.x,row*spacing.y,0))
            if reset: obj.matrix_basis=Matrix.Identity(4)
            runtime.invalidate(obj)
        context.view_layer.update(); runtime.refresh()
    finally: _updating=False


def next_group_name(scene):
    names=[g.name for g in scene.ps_study.blend_groups]+list(bpy.data.objects.keys())
    number=max([int(name[2:]) for name in names if name.startswith('BG') and name[2:].isdigit()]+[0])+1
    return f'BG{number:02d}'


def create(context,objects,layout,columns,rows,overlap,mode,preserve=False):
    global _updating
    from . import runtime
    runtime.refresh(True)
    if any(group_for(o,context.scene) for o in objects): raise ValueError('Remove projectors from their existing group first')
    settings=context.scene.ps_study
    name=next_group_name(context.scene)
    group=settings.blend_groups.add(); group.uuid=new_uuid(); group.name=name
    _updating=True
    try:
        group.layout=layout; group.columns=len(objects) if layout=='HORIZONTAL' else 1 if layout=='VERTICAL' else columns
        group.rows=(len(objects)+group.columns-1)//group.columns; group.input_mode=mode; group.previous_mode=mode
        group.overlap_h=group.overlap_v=overlap; group.anchor_uuid=objects[0].ps.uuid
    finally: _updating=False
    controller=bpy.data.objects.new(group.name,None); context.scene.collection.objects.link(controller)
    controller['beam_group_uuid']=group.uuid; controller.empty_display_type='PLAIN_AXES'; controller.empty_display_size=.5
    controller.matrix_world=objects[0].matrix_world.copy(); controller.lock_scale=(True,)*3
    group.controller=controller
    for obj in objects:
        world=obj.matrix_world.copy()
        slot=bpy.data.objects.new(f'{group.name} · {obj.ps.identifier} Layout',None)
        context.scene.collection.objects.link(slot); slot['beam_layout_slot']=True; slot.hide_select=True
        slot.empty_display_size=.01; slot.parent=controller; slot.matrix_parent_inverse=Matrix.Identity(4)
        slot.location=controller.matrix_world.inverted()@world.translation
        member=group.members.add(); member.projector=obj; member.projector_uuid=obj.ps.uuid; member.slot=slot
        obj.parent=slot; obj.matrix_parent_inverse=Matrix.Identity(4)
        obj.matrix_basis=(controller.matrix_world@slot.matrix_basis).inverted()@world
    settings.blend_group_index=len(settings.blend_groups)-1
    if not preserve: apply_layout(group,context,reset=True)
    else: dimensions(group,context)
    from . import group_lifecycle
    if preserve: group_lifecycle.sort_members(group)
    group_lifecycle.resize(group)
    group_lifecycle.snapshot(group,context)
    return group


def remove_member(group,index):
    member=group.members[index]; obj=member.projector; slot=member.slot
    if obj:
        world=obj.matrix_world.copy(); obj.parent=None; obj.matrix_world=world
    group.members.remove(index)
    if slot:
        # A native duplicate may still share this layout parent. Keep it in place.
        for child in list(slot.children):
            world=child.matrix_world.copy(); child.parent=None; child.matrix_world=world
        bpy.data.objects.remove(slot,do_unlink=True)
    valid=[m.projector for m in group.members if m.projector and m.projector.ps.is_projector]
    if not any(o.ps.uuid==group.anchor_uuid for o in valid):
        group.anchor_uuid=valid[0].ps.uuid if valid else ''
    from .group_lifecycle import resize
    resize(group)


def pair_data(group,context):
    from . import runtime
    values=next((runtime.CACHE.get(m.projector.as_pointer()) for m in group.members if m.projector and m.projector.ps.uuid==group.anchor_uuid),None)
    if not values: return []
    anchor=next(m.projector for m in group.members if m.projector and m.projector.ps.uuid==group.anchor_uuid)
    rotation=values['rotation']; origin=values['origin']; unit=context.scene.unit_settings.scale_length
    depth=values['metrics'].distance/unit
    plane_origin=origin+rotation@Vector((0,0,-depth)); inverse=rotation.transposed()
    polygons=[]
    for member in group.members:
        obj=member.projector; record=runtime.CACHE.get(obj.as_pointer()) if obj else None
        polygon=[]
        if record:
            from .projection_math import image_point
            eye=inverse@(record['origin']-plane_origin)
            for u,v in ((0,0),(1,0),(1,1),(0,1)):
                ray=inverse@record['rotation']@Vector(image_point(u,v,1,obj.ps.throw_ratio,obj.ps.resolution_x,obj.ps.resolution_y,obj.ps.shift_h,obj.ps.shift_v))
                if abs(ray.z)<1e-8 or -eye.z/ray.z<=0: polygon=[]; break
                point=eye+ray*(-eye.z/ray.z); polygon.append((point.x*unit,point.y*unit))
        polygons.append(polygon)
    result=[]
    for a,b,axis in adjacent(group.layout,len(group.members),group.columns):
        if not polygons[a] or not polygons[b]: continue
        poly=intersection(polygons[a],polygons[b]); dimension=0 if axis=='H' else 1
        length=max((p[dimension] for p in poly),default=0)-min((p[dimension] for p in poly),default=0)
        full=values['metrics'].width if axis=='H' else values['metrics'].height
        pixels=anchor.ps.resolution_x if axis=='H' else anchor.ps.resolution_y
        desired=overlap_values(group.overlap_h if axis=='H' else group.overlap_v,group.input_mode,pixels,full)
        result.append(dict(a=group.members[a].projector.ps.identifier,b=group.members[b].projector.ps.identifier,a_uuid=group.members[a].projector.ps.uuid,b_uuid=group.members[b].projector.ps.uuid,axis=axis,
                           reference_status='target' if values['hit'] else 'preview',actual_plane_distance_m=values['metrics'].distance,desired=desired,actual=dict(metres=length,pixels=length/full*pixels,percent=length/full*100),
                           polygon=[plane_origin+rotation@Vector((x/unit,y/unit,0)) for x,y in poly]))
    return result


def preview(obj):
    group=group_for(obj)
    if not group: return (0,0,0,0),(0,0,1,1),False
    members=member_objects(group)
    if obj not in members: return (0,0,0,0),(0,0,1,1),False
    anchor=next((o for o in members if o.ps.uuid==group.anchor_uuid),members[0]); width=group.reference_width; height=group.reference_height
    h=overlap_values(group.overlap_h,group.input_mode,anchor.ps.resolution_x,width)['fraction']
    v=overlap_values(group.overlap_v,group.input_mode,anchor.ps.resolution_y,height)['fraction']
    positions=cells(group.layout,len(members),group.columns); column,row=positions[members.index(obj)]
    columns=max(x for x,y in positions)+1; rows=max(y for x,y in positions)+1
    feather=(h if (column-1,row) in positions else 0,h if (column+1,row) in positions else 0,
             v if (column,row+1) in positions else 0,v if (column,row-1) in positions else 0)
    if not group.preview_edge_blend: feather=(0,0,0,0)
    canvas_w=1+(columns-1)*(1-h); canvas_h=1+(rows-1)*(1-v)
    mapping=(column*(1-h)/canvas_w,(rows-1-row)*(1-v)/canvas_h,1/canvas_w,1/canvas_h)
    return feather,mapping,group.combined


class BEAM_OT_create_group(bpy.types.Operator):
    bl_idname='beam.create_group'; bl_label='Create Blend Group'; bl_options={'REGISTER','UNDO'}
    from_selection: BoolProperty(default=False)
    layout_type: EnumProperty(name='Layout',items=[('HORIZONTAL','Horizontal',''),('VERTICAL','Vertical',''),('ARRAY','Array','')])
    count: IntProperty(name='Projector Count',default=4,min=2,max=32)
    columns: IntProperty(name='Columns',default=3,min=1,max=16)
    rows: IntProperty(name='Rows',default=2,min=1,max=16)
    overlap: FloatProperty(name='Overlap',default=200,min=0)
    input_mode: EnumProperty(name='Units',items=[('PIXELS','Pixels',''),('PERCENT','Percent',''),('METRES','Metres','')])
    def invoke(self,context,event): return context.window_manager.invoke_props_dialog(self)
    def draw(self,context):
        box=self.layout
        box.prop(self,'layout_type')
        if self.layout_type=='ARRAY':
            box.prop(self,'columns')
            if not self.from_selection: box.prop(self,'rows')
        elif not self.from_selection: box.prop(self,'count')
        box.prop(self,'input_mode'); box.prop(self,'overlap')
        if self.from_selection: box.label(text='Keep existing transforms; use Apply to align later')
    def execute(self,context):
        from .projector_object import selected,create as create_projector
        anchor=selected(context)
        if not anchor: self.report({'WARNING'},'Choose an active Beam projector'); return {'CANCELLED'}
        if group_for(anchor): self.report({'WARNING'},'Anchor already belongs to a blend group'); return {'CANCELLED'}
        if self.from_selection:
            objects=[anchor]+sorted([o for o in context.selected_objects if o.ps.is_projector and o!=anchor],key=lambda o:o.ps.identifier)
            if len(objects)<2 or any(group_for(o) for o in objects):
                self.report({'WARNING'},'Select at least two ungrouped projectors'); return {'CANCELLED'}
        else:
            count=self.columns*self.rows if self.layout_type=='ARRAY' else self.count
            if count>64: self.report({'WARNING'},'Use at most 64 projectors in one group'); return {'CANCELLED'}
            objects=[anchor]+[create_projector(context,anchor) for _ in range(count-1)]
        create(context,objects,self.layout_type,self.columns,self.rows,self.overlap,self.input_mode,self.from_selection)
        if not self.from_selection:
            for item in context.selected_objects: item.select_set(False)
        anchor.select_set(True); context.view_layer.objects.active=anchor
        context.scene.ps_study.active_projector=anchor
        return {'FINISHED'}

class BEAM_OT_group_action(bpy.types.Operator):
    bl_idname='beam.group_action'; bl_label='Blend Group Action'; bl_options={'REGISTER','UNDO'}
    action: EnumProperty(items=[(x,x.title(),'') for x in ('APPLY','RESET','REMOVE','UNGROUP','SOLO','SELECT','ADD_SELECTED','ADD_NEW','DUPLICATE')])
    @classmethod
    def description(cls,context,properties):
        return {'ADD_SELECTED':'Join the selected projector without moving it or changing its settings',
                'ADD_NEW':'Create an independent Beam projector in the next group slot',
                'REMOVE':'Leave the group without deleting or moving the selected projector',
                'APPLY':'Align layout slots to the desired overlap; preserve manual local offsets',
                'RESET':'Reset only the selected member to its layout slot, clearing local position and rotation',
                'DUPLICATE':'Copy this rig with independent projectors and new UUIDs'}.get(properties.action,'Manage this Blend Group')
    def execute(self,context):
        global solo_uuid
        group=active_group(context)
        if not group: return {'CANCELLED'}
        from . import group_lifecycle as lifecycle
        if self.action in {'ADD_SELECTED','ADD_NEW','DUPLICATE'}:
            try:
                if self.action=='ADD_SELECTED':
                    obj=context.view_layer.objects.active
                    if not obj or not obj.select_get() or not obj.ps.is_projector: raise ValueError('Select an existing Beam projector')
                    lifecycle.add_member(group,obj,context)
                elif self.action=='ADD_NEW': lifecycle.add_new(group,context)
                else: lifecycle.duplicate(group,context)
            except ValueError as exc:
                self.report({'WARNING'},str(exc));return {'CANCELLED'}
        elif self.action=='APPLY': apply_layout(group,context)
        elif self.action in {'RESET','REMOVE'}:
            obj=context.view_layer.objects.active
            index=next((i for i,m in enumerate(group.members) if obj and obj.select_get() and m.projector==obj),None)
            if index is None: self.report({'WARNING'},'Choose a member projector'); return {'CANCELLED'}
            if self.action=='RESET':
                lifecycle.reset_member(group,obj,context)
            else: remove_member(group,index)
        elif self.action=='UNGROUP':
            while group.members: remove_member(group,len(group.members)-1)
            if group.controller: bpy.data.objects.remove(group.controller,do_unlink=True)
            context.scene.ps_study.blend_groups.remove(context.scene.ps_study.blend_group_index)
            context.scene.ps_study.blend_group_index=max(0,context.scene.ps_study.blend_group_index-1)
            solo_uuid=None
        elif self.action=='SOLO':
            from . import viewport_display
            viewport_display.isolate_uuid=None
            solo_uuid=None if solo_uuid==group.uuid else group.uuid
        elif self.action=='SELECT' and group.controller:
            for obj in context.selected_objects: obj.select_set(False)
            group.controller.select_set(True); context.view_layer.objects.active=group.controller
        from . import runtime
        lifecycle.prune(context)
        context.view_layer.update(); runtime.invalidate()
        runtime.refresh(True)
        return {'FINISHED'}

CLASSES=(BeamMember,BeamBlendGroup,BEAM_OT_create_group,BEAM_OT_group_action)


def matrix_metres(matrix,unit):
    result=[list(row) for row in matrix]
    for i in range(3): result[i][3]*=unit
    return result


def serialize(context):
    unit=context.scene.unit_settings.scale_length; result=[]
    for group in context.scene.ps_study.blend_groups:
        positions=cells(group.layout,len(group.members),group.columns)
        inverse=None
        if group.controller and abs(group.controller.matrix_world.determinant())>1e-12:
            inverse=group.controller.matrix_world.inverted()
        from . import runtime
        anchor=next((m.projector for m in group.members if m.projector and m.projector.ps.uuid==group.anchor_uuid),None)
        record=runtime.CACHE.get(anchor.as_pointer()) if anchor else None
        measurement_plane=None
        if record:
            plane=record['origin']+record['rotation']@Vector((0,0,-record['metrics'].distance/unit))
            measurement_plane=dict(space='blender_world',origin_m=list(plane*unit),rotation_quaternion_wxyz=list(record['rotation'].to_quaternion()),
                status='target' if record['hit'] else 'preview',distance_m=record['metrics'].distance,
                width_m=record['metrics'].width,height_m=record['metrics'].height)
        result.append(dict(uuid=group.uuid,name=group.name,layout=group.layout,anchor_projector_uuid=group.anchor_uuid,
            rows=max((row for col,row in positions),default=0)+1,
            columns=group.columns if group.layout=='ARRAY' else max((col for col,row in positions),default=0)+1,
            input_mode=group.input_mode,desired_horizontal_overlap=group.overlap_h,
            desired_vertical_overlap=group.overlap_v,measurement_plane=measurement_plane,reference_plane=dict(role='last_layout_reference_dimensions',distance_m=group.reference_distance,width_m=group.reference_width,height_m=group.reference_height),
            transform=None if not group.controller else dict(space='blender_world',matrix=matrix_metres(group.controller.matrix_world,unit),position_m=[v*unit for v in group.controller.matrix_world.translation],rotation_quaternion_wxyz=list(group.controller.matrix_world.to_quaternion())),
            members=[dict(member_index=i,column=positions[i][0],row=positions[i][1],local_offset_space='projector_basis_relative_to_layout_slot',
                          transform_in_group=matrix_metres(inverse@m.projector.matrix_world,unit) if m.projector and inverse is not None else None,
                          layout_slot_transform=matrix_metres(inverse@m.slot.matrix_world,unit) if m.slot and inverse is not None else None,
                          projector_uuid=m.projector.ps.uuid if m.projector else m.projector_uuid,local_offset_m=list(m.projector.location*unit) if m.projector else None,
                          local_rotation_quaternion_wxyz=list(m.projector.matrix_basis.to_quaternion()) if m.projector else None) for i,m in enumerate(group.members)],
            adjacent_pairs=[{k:v for k,v in pair.items() if k!='polygon'} for pair in pair_data(group,context)],
            notes=group.notes,preview_edge_blend=group.preview_edge_blend,combined_preview=group.combined))
    return result
