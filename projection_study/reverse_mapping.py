"""Reversible material wrappers fed by the existing GPU first-hit depth maps.

Source shader graphs and UVs are untouched. Coverage is evaluated in projector
space, while the source material continues to evaluate in its own UV space.
"""
import bpy
import gpu
import logging
import numpy as np
from . import runtime,projection_renderer

_images={}
_signatures={}
_busy=False
_error=''
_object_errors={}

class BeamReverseSlot(bpy.types.PropertyGroup):
    index:bpy.props.IntProperty()
    material:bpy.props.PointerProperty(type=bpy.types.Material)
    wrapper:bpy.props.PointerProperty(type=bpy.types.Material)
    link:bpy.props.StringProperty()

class BeamReverseSettings(bpy.types.PropertyGroup):
    enabled:bpy.props.BoolProperty(default=False)
    source:bpy.props.EnumProperty(name='Coverage From',items=[('ACTIVE','Active Projector',''),('SELECTED','Selected Projector','Choose a specific projector'),('GROUP','Blend Group',''),('ALL','All Active Projectors','Visible projectors included in the study')],default='ACTIVE')
    projector:bpy.props.PointerProperty(name='Projector',type=bpy.types.Object,poll=lambda self,obj:obj.ps.is_projector)
    group_uuid:bpy.props.StringProperty()
    mode:bpy.props.EnumProperty(name='Mode',items=[('COVERED','Covered Only','Neutral surface outside coverage'),('DIM','Uncovered Dimmed',''),('HIDDEN','Uncovered Hidden','Transparent outside coverage'),('OVERLAP','Overlap Diagnostic','Amber where two or more projectors cover')],default='DIM')
    dim:bpy.props.FloatProperty(name='Outside Brightness',default=.12,min=0,max=1)
    slots:bpy.props.CollectionProperty(type=BeamReverseSlot)
    status:bpy.props.StringProperty()


def sources(context,p):
    from . import blend_groups
    if p.source=='ACTIVE':objects=[context.scene.ps_study.active_projector]
    elif p.source=='SELECTED':objects=[p.projector]
    elif p.source=='GROUP':
        group=next((g for g in context.scene.ps_study.blend_groups if g.uuid==p.group_uuid),None)
        objects=blend_groups.member_objects(group) if group else []
    else:objects=[o for o in context.scene.objects if o.ps.is_projector and o.ps.active]
    return [o for o in objects if o and o.name in context.scene.objects and o.ps.is_projector and o.visible_get()]


def managed(obj):
    return hasattr(obj,'beam_reverse') and obj.beam_reverse.enabled


def socket(value):return hasattr(value,'is_output')


def build_group(projectors,mode,dim):
    group=bpy.data.node_groups.new('Beam · Coverage Mask','ShaderNodeTree');group['beam_reverse']=True
    group.interface.new_socket(name='Covered',in_out='OUTPUT',socket_type='NodeSocketFloat')
    group.interface.new_socket(name='Overlap',in_out='OUTPUT',socket_type='NodeSocketFloat')
    nodes=group.nodes;links=group.links
    def math_node(operation,a,b=0,name=None):
        node=nodes.new('ShaderNodeMath');node.operation=operation
        if name:node.name=name
        for i,value in enumerate((a,b)):
            if socket(value):links.new(value,node.inputs[i])
            else:node.inputs[i].default_value=value
        return node.outputs[0]
    total=0
    for obj in projectors:
        prefix=obj.ps.uuid
        coords=nodes.new('ShaderNodeTexCoord');coords.object=obj
        xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(coords.outputs['Object'],xyz.inputs[0])
        depth=math_node('MULTIPLY',xyz.outputs['Z'],-1)
        x=math_node('DIVIDE',xyz.outputs['X'],depth);y=math_node('DIVIDE',xyz.outputs['Y'],depth)
        x=math_node('MULTIPLY',x,obj.ps.throw_ratio,prefix+' ratio_x')
        y=math_node('MULTIPLY',y,obj.ps.throw_ratio*obj.ps.resolution_x/obj.ps.resolution_y,prefix+' ratio_y')
        u=math_node('ADD',x,.5-obj.ps.shift_h/100,prefix+' shift_x');v=math_node('ADD',y,.5-obj.ps.shift_v/100,prefix+' shift_y')
        uv=nodes.new('ShaderNodeCombineXYZ');links.new(u,uv.inputs['X']);links.new(v,uv.inputs['Y'])
        texture=nodes.new('ShaderNodeTexImage');texture.name=prefix+' depth';texture.interpolation='Closest';texture.extension='EXTEND';links.new(uv.outputs[0],texture.inputs['Vector'])
        channel=nodes.new('ShaderNodeSeparateColor');channel.mode='RGB';links.new(texture.outputs['Color'],channel.inputs[0])
        texdepth=math_node('ADD',channel.outputs['Red'],.003,prefix+' bias')
        mask=math_node('LESS_THAN',depth,texdepth)
        for factor in (math_node('GREATER_THAN',depth,.005,prefix+' near'),math_node('GREATER_THAN',u,0),math_node('LESS_THAN',u,1),math_node('GREATER_THAN',v,0),math_node('LESS_THAN',v,1)):
            mask=math_node('MULTIPLY',mask,factor)
        valid=math_node('MULTIPLY',mask,0,prefix+' valid');total=math_node('ADD',total,valid)
    union=math_node('MINIMUM',total,1);overlap=math_node('GREATER_THAN',total,1.5)
    output=nodes.new('NodeGroupOutput');links.new(union,output.inputs['Covered']);links.new(overlap,output.inputs['Overlap'])
    return group


def surface_outputs(material):
    if not material or not material.use_nodes:raise ValueError('Assign node-based source materials first')
    # Blender may resolve an engine-specific output whose active flag is false.
    outputs=list(dict.fromkeys(n for engine in ('ALL','EEVEE','CYCLES')
                              if (n:=material.node_tree.get_output_node(engine)) is not None))
    if not outputs or any(not n.inputs['Surface'].is_linked for n in outputs):
        raise ValueError('Each active material output needs a connected Surface shader')
    return outputs


def wrap(source,coverage,p):
    surface_outputs(source)
    material=source.copy();material.name='Beam Reverse · '+source.name;material['beam_reverse']=True
    material.use_fake_user=False
    nodes=material.node_tree.nodes;links=material.node_tree.links
    # Materials can have separate active EEVEE/Cycles outputs. Wrap every one.
    for output in surface_outputs(material):
        original=output.inputs['Surface'].links[0].from_socket
        mask=nodes.new('ShaderNodeGroup');mask.node_tree=coverage;mask.name='Beam Coverage';mask['beam_reverse_mask']=True
        outside=nodes.new('ShaderNodeBsdfTransparent' if p.mode=='HIDDEN' else 'ShaderNodeBsdfDiffuse')
        outside.inputs[0].default_value=(1,1,1,1) if p.mode=='HIDDEN' else (.055,.065,.08,1)
        outside_shader=outside.outputs[0]
        if p.mode=='DIM':
            outside.inputs[0].default_value=(0,0,0,1)
            dim=nodes.new('ShaderNodeMixShader');dim.inputs[0].default_value=p.dim;links.new(outside_shader,dim.inputs[1]);links.new(original,dim.inputs[2]);outside_shader=dim.outputs[0]
        mix=nodes.new('ShaderNodeMixShader');links.new(mask.outputs['Covered'],mix.inputs[0]);links.new(outside_shader,mix.inputs[1]);links.new(original,mix.inputs[2]);final=mix.outputs[0]
        if p.mode=='OVERLAP':
            highlight=nodes.new('ShaderNodeEmission');highlight.inputs[0].default_value=(1,.42,.08,1)
            diagnosis=nodes.new('ShaderNodeMixShader');links.new(mask.outputs['Overlap'],diagnosis.inputs[0]);links.new(final,diagnosis.inputs[1]);links.new(highlight.outputs[0],diagnosis.inputs[2]);final=diagnosis.outputs[0]
        links.new(final,output.inputs['Surface'])
    if hasattr(material,'surface_render_method'):material.surface_render_method='DITHERED'
    return material


def bindings(obj):
    """Match by wrapper identity: Blender material slots can move or disappear."""
    saved={entry.wrapper.as_pointer():entry for entry in obj.beam_reverse.slots if entry.wrapper}
    return [(slot,saved[slot.material.as_pointer()]) for slot in obj.material_slots
            if slot.material and slot.material.as_pointer() in saved]


def coverage_groups(p):
    return {n.node_tree for saved in p.slots if saved.wrapper and saved.wrapper.use_nodes
            for n in saved.wrapper.node_tree.nodes if n.type=='GROUP' and n.get('beam_reverse_mask') and n.node_tree}


def invalidate_masks(p):
    for group in coverage_groups(p):
        for node in group.nodes:
            if node.type=='MATH' and node.name.endswith(' valid') and node.inputs[1].default_value:
                node.inputs[1].default_value=0


def enable(context,obj):
    if not obj or obj.type!='MESH' or obj.ps.is_projector:raise ValueError('Select a UV-mapped receiving mesh')
    if obj.library and not obj.override_library:raise ValueError('Make the receiving object local before enabling Reverse Mapping')
    if not obj.data.uv_layers.active:raise ValueError('The selected mesh needs an active UV map')
    if not obj.material_slots or any(not s.material or not s.material.use_nodes for s in obj.material_slots):raise ValueError('Assign node-based source materials first')
    p=obj.beam_reverse
    if p.enabled:raise ValueError('Disable Reverse Mapping before replacing its source materials')
    if p.source=='SELECTED' and not p.projector:
        p.projector=next((o for o in context.selected_objects if o.ps.is_projector),context.scene.ps_study.active_projector)
    if p.source=='GROUP' and not p.group_uuid:
        from .blend_groups import active_group
        g=active_group(context);p.group_uuid=g.uuid if g else ''
    selected=sources(context,p)
    if not selected:raise ValueError('Choose a visible coverage projector or blend group')
    if len(selected)>32:raise ValueError('Reverse Mapping supports up to 32 coverage projectors per object')
    for slot in obj.material_slots:surface_outputs(slot.material)
    coverage=build_group(selected,p.mode,p.dim)
    wrappers=[]
    try:
        for slot in obj.material_slots:wrappers.append(wrap(slot.material,coverage,p))
        p.slots.clear()
        for i,(slot,wrapper) in enumerate(zip(obj.material_slots,wrappers)):
            saved=p.slots.add();saved.index=i;saved.material=slot.material;saved.link=slot.link;saved.wrapper=wrapper
            slot.link='OBJECT';slot.material=wrapper
        p.enabled=True;p.status='Waiting for coverage';_signatures[obj.as_pointer()]=(tuple(o.ps.uuid for o in selected),p.mode,p.dim)
    except Exception:
        for saved in p.slots:
            if saved.index<len(obj.material_slots):
                slot=obj.material_slots[saved.index]
                if slot.material==saved.wrapper:slot.material=saved.material;slot.link=saved.link
        p.slots.clear();p.enabled=False
        for wrapper in wrappers:
            if wrapper.users==0:bpy.data.materials.remove(wrapper)
        if coverage.users==0:bpy.data.node_groups.remove(coverage)
        raise
    if context.area and context.area.type=='VIEW_3D':context.space_data.shading.type='MATERIAL'


def disable(obj):
    p=obj.beam_reverse
    for slot,saved in bindings(obj):
        slot.material=saved.material;slot.link=saved.link
    p.enabled=False;p.slots.clear();p.status='Original materials restored';_signatures.pop(obj.as_pointer(),None)
    cleanup_orphans()


def cleanup_orphans():
    for material in list(bpy.data.materials):
        if material.get('beam_reverse') and material.users==0:bpy.data.materials.remove(material)
    for group in list(bpy.data.node_groups):
        if group.get('beam_reverse') and group.users==0:bpy.data.node_groups.remove(group)
    for key,cached in list(_images.items()):
        try:
            if cached[1].users==0:_images.pop(key,None)
        except ReferenceError:_images.pop(key,None)
    for image in list(bpy.data.images):
        if image.get('beam_coverage') and image.users==0:bpy.data.images.remove(image)


def image_for(obj,record):
    shadow=projection_renderer.shadow_map(obj,record);key=obj.as_pointer();cached=_images.get(key)
    if cached:
        try:cached[1].name
        except ReferenceError:_images.pop(key,None);cached=None
    # Images are refreshed only when optics, transforms, receivers or quality change.
    if cached and cached[0]==shadow['signature'] and cached[1].name in bpy.data.images:return cached[1]
    width,height=shadow['size'];image=cached[1] if cached else next((i for i in bpy.data.images if i.get('beam_coverage_uuid')==obj.ps.uuid),None)
    if image is None:image=bpy.data.images.new('.Beam Coverage '+obj.ps.uuid,width,height,float_buffer=True)
    image['beam_coverage_uuid']=obj.ps.uuid
    image.colorspace_settings.name='Non-Color';image['beam_coverage']=True
    if tuple(image.size)!=(width,height):image.scale(width,height)
    with shadow['offscreen'].bind():
        buffer=__import__('gpu').state.active_framebuffer_get().read_color(0,0,width,height,4,0,'FLOAT');buffer.dimensions=width*height*4
        pixels=np.asarray(buffer,dtype=np.float32).reshape(-1).copy()
    image.pixels.foreach_set(pixels);image.update();_images[key]=(shadow['signature'],image)
    return image


def refresh_object(obj):
    p=obj.beam_reverse
    attached=bindings(obj)
    if not attached:
        p.status='No managed material slots; restore materials before enabling again'
        return
    projectors=sources(bpy.context,p)
    too_many=len(projectors)>32
    if too_many:projectors=[]
    key=(tuple(o.ps.uuid for o in projectors),p.mode,p.dim)
    groups=coverage_groups(p)
    if _signatures.get(obj.as_pointer())!=key:
        records={saved.as_pointer():saved for slot,saved in attached}
        for saved in records.values():surface_outputs(saved.material)
        coverage=build_group(projectors,p.mode,p.dim);replacements={}
        try:
            for identity,saved in records.items():replacements[identity]=wrap(saved.material,coverage,p)
        except Exception:
            cleanup_orphans();raise
        for slot,saved in attached:slot.material=replacements[saved.as_pointer()]
        for identity,saved in records.items():saved.wrapper=replacements[identity]
        groups={coverage};_signatures[obj.as_pointer()]=key;cleanup_orphans()
    for projector in projectors:
        record=runtime.CACHE.get(projector.as_pointer());uuid=projector.ps.uuid
        if not record or not runtime.rigid(projector):
            for group in groups:
                node=group.nodes.get(uuid+' valid')
                if node and node.inputs[1].default_value!=0:node.inputs[1].default_value=0
            continue
        image=image_for(projector,record);shadow=projection_renderer._maps[projector.as_pointer()]
        for group in groups:
            node=group.nodes.get(uuid+' depth')
            if not node:continue
            if node.image!=image:node.image=image
            vals={'ratio_x':projector.ps.throw_ratio,'ratio_y':projector.ps.throw_ratio*projector.ps.resolution_x/projector.ps.resolution_y,
                  'shift_x':.5-projector.ps.shift_h/100,'shift_y':.5-projector.ps.shift_v/100,
                  'near':shadow['near'],'bias':max(.003/bpy.context.scene.unit_settings.scale_length,record['metrics'].distance/bpy.context.scene.unit_settings.scale_length/min(shadow['size'])*.5),'valid':1}
            for suffix,value in vals.items():
                n=group.nodes.get(uuid+' '+suffix)
                if n and abs(n.inputs[1].default_value-value)>1e-8:n.inputs[1].default_value=value
    status='Too many coverage projectors (maximum 32)' if too_many else f'{len(projectors)} coverage projectors · {p.mode.title()}' if projectors else 'No visible coverage source'
    if p.status!=status:p.status=status


def refresh_gpu():
    """Refresh in a GPU context; isolate receiver failures and restore draw state."""
    global _busy,_error
    if _busy or not hasattr(bpy.types.Object,'beam_reverse'):return
    live={o.as_pointer() for o in bpy.data.objects if managed(o)}
    removed=set(_signatures)-live
    if removed:
        for key in removed:_signatures.pop(key,None);_object_errors.pop(key,None)
        cleanup_orphans()
    objects=[o for o in bpy.context.scene.objects if managed(o)]
    if not objects:_error='';return
    state=(gpu.state.blend_get(),gpu.state.depth_test_get(),gpu.state.depth_mask_get(),gpu.state.viewport_get())
    _busy=True;errors=[]
    try:
        for obj in objects:
            try:
                refresh_object(obj);_object_errors.pop(obj.as_pointer(),None)
            except Exception as exc:
                message=str(exc);errors.append(message)
                if _object_errors.get(obj.as_pointer())!=message:
                    logging.getLogger(__name__).exception('Beam coverage refresh failed for %s',obj.name)
                _object_errors[obj.as_pointer()]=message
                invalidate_masks(obj.beam_reverse)
                status='Coverage unavailable: check GPU/material setup, or restore materials'
                if obj.beam_reverse.status!=status:obj.beam_reverse.status=status
        _error='; '.join(errors)
    finally:
        gpu.state.blend_set(state[0]);gpu.state.depth_test_set(state[1]);gpu.state.depth_mask_set(state[2]);gpu.state.viewport_set(*state[3])
        _busy=False


@bpy.app.handlers.persistent
def reset(*args):
    global _error
    _images.clear();_signatures.clear();_object_errors.clear();_error=''

@bpy.app.handlers.persistent
def pack(*args):
    for image in bpy.data.images:
        if image.get('beam_coverage'):image.pack()

class BEAM_OT_reverse(bpy.types.Operator):
    bl_idname='beam.reverse_mapping';bl_label='Reverse Mapping';bl_options={'REGISTER','UNDO'}
    action:bpy.props.EnumProperty(items=[('ENABLE','Enable',''),('DISABLE','Disable','')])
    def execute(self,context):
        obj=context.view_layer.objects.active
        try:
            if self.action=='DISABLE':
                if not obj or not managed(obj):raise ValueError('Select a Reverse Mapping object')
                disable(obj)
            else:
                if bpy.app.background:raise ValueError('Reverse Mapping needs an interactive GPU viewport')
                enable(context,obj)
        except (ValueError,RuntimeError) as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class BEAM_OT_reverse_group(bpy.types.Operator):
    bl_idname='beam.reverse_group';bl_label='Use Active Blend Group';bl_options={'UNDO'}
    group_uuid:bpy.props.StringProperty()
    def execute(self,context):
        obj=context.view_layer.objects.active;group=next((g for g in context.scene.ps_study.blend_groups if g.uuid==self.group_uuid),None)
        if not obj or obj.type!='MESH' or not group:
            self.report({'WARNING'},'Choose a receiving mesh and an active Blend Group');return {'CANCELLED'}
        obj.beam_reverse.group_uuid=group.uuid
        return {'FINISHED'}

class BEAM_MT_reverse_groups(bpy.types.Menu):
    bl_label='Coverage Blend Group'
    def draw(self,context):
        for group in context.scene.ps_study.blend_groups:
            self.layout.operator('beam.reverse_group',text=group.name).group_uuid=group.uuid
        if not context.scene.ps_study.blend_groups:self.layout.label(text='Create a Blend Group first')

CLASSES=(BeamReverseSlot,BeamReverseSettings,BEAM_OT_reverse,BEAM_OT_reverse_group,BEAM_MT_reverse_groups)

def register():
    bpy.types.Object.beam_reverse=bpy.props.PointerProperty(type=BeamReverseSettings)
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if reset not in handlers:handlers.append(reset)
    if pack not in bpy.app.handlers.save_pre:bpy.app.handlers.save_pre.append(pack)

def unregister():
    for obj in bpy.data.objects:
        if managed(obj):disable(obj)
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if reset in handlers:handlers.remove(reset)
    if pack in bpy.app.handlers.save_pre:bpy.app.handlers.save_pre.remove(pack)
    del bpy.types.Object.beam_reverse;reset()
