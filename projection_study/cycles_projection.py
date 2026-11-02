"""Managed Cycles projector lights. Does not participate in engineering sampling."""
import math
import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix

TAG = 'beam_cycles_owned'
VERSION = 1
_signatures = {}
_busy = False
_rendering = False


def math_group():
    name = '.Beam Cycles Raster v1'
    group = next((g for g in bpy.data.node_groups if g.get(TAG) == VERSION), None)
    if group:
        return group
    group = bpy.data.node_groups.new(name, 'ShaderNodeTree'); group[TAG] = VERSION
    for name, value in [('Ratio',1),('Aspect',.5625),('Shift X',0),('Shift Y',0),
                        ('Left',0),('Right',0),('Bottom',0),('Top',0),
                        ('Canvas X',0),('Canvas Y',0),('Canvas W',1),('Canvas H',1)]:
        socket=group.interface.new_socket(name=name,in_out='INPUT',socket_type='NodeSocketFloat');socket.default_value=value
    group.interface.new_socket(name='UV',in_out='OUTPUT',socket_type='NodeSocketVector')
    group.interface.new_socket(name='Weight',in_out='OUTPUT',socket_type='NodeSocketFloat')
    n=group.nodes; links=group.links
    inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
    def op(operation,a,b=0):
        node=n.new('ShaderNodeMath');node.operation=operation
        for i,value in enumerate((a,b)):
            if isinstance(value,(int,float)):node.inputs[i].default_value=value
            else:links.new(value,node.inputs[i])
        return node.outputs[0]
    geo=n.new('ShaderNodeNewGeometry');transform=n.new('ShaderNodeVectorTransform')
    transform.vector_type='VECTOR';transform.convert_from='WORLD';transform.convert_to='OBJECT'
    links.new(geo.outputs['Incoming'],transform.inputs[0]);sep=n.new('ShaderNodeSeparateXYZ');links.new(transform.outputs[0],sep.inputs[0])
    z=op('MULTIPLY',sep.outputs['Z'],-1)
    u=op('SUBTRACT',op('ADD',op('MULTIPLY',op('DIVIDE',sep.outputs['X'],z),inp.outputs['Ratio']),.5),inp.outputs['Shift X'])
    v=op('SUBTRACT',op('ADD',op('DIVIDE',op('MULTIPLY',op('DIVIDE',sep.outputs['Y'],z),inp.outputs['Ratio']),inp.outputs['Aspect']),.5),inp.outputs['Shift Y'])
    weight=op('MULTIPLY',op('GREATER_THAN',u,0),op('LESS_THAN',u,1))
    weight=op('MULTIPLY',weight,op('MULTIPLY',op('GREATER_THAN',v,0),op('LESS_THAN',v,1)))
    for coordinate,key in [(u,'Left'),(op('SUBTRACT',1,u),'Right'),(v,'Bottom'),(op('SUBTRACT',1,v),'Top')]:
        fraction=op('DIVIDE',coordinate,op('MAXIMUM',inp.outputs[key],1e-8))
        weight=op('MULTIPLY',weight,op('MINIMUM',op('MAXIMUM',fraction,0),1))
    combine=n.new('ShaderNodeCombineXYZ')
    links.new(op('ADD',inp.outputs['Canvas X'],op('MULTIPLY',u,inp.outputs['Canvas W'])),combine.inputs['X'])
    links.new(op('ADD',inp.outputs['Canvas Y'],op('MULTIPLY',v,inp.outputs['Canvas H'])),combine.inputs['Y'])
    links.new(combine.outputs[0],out.inputs['UV']);links.new(weight,out.inputs['Weight'])
    return group


def solid_angle(p):
    a=p.resolution_y/p.resolution_x;t=p.throw_ratio
    x0=(-.5+p.shift_h/100)/t;x1=(.5+p.shift_h/100)/t
    y0=(-.5+p.shift_v/100)*a/t;y1=(.5+p.shift_v/100)*a/t
    def corner(x,y):return math.atan2(x*y,math.sqrt(1+x*x+y*y))
    angle=corner(x1,y1)-corner(x0,y1)-corner(x1,y0)+corner(x0,y0)
    cone=2*math.atan(max(math.hypot(x,y) for x in (x0,x1) for y in (y0,y1)))
    return max(angle,1e-10),min(math.pi,cone+1e-5)


def content(obj):
    from .blend_groups import preview, group_for, member_objects
    feather,canvas,combined=preview(obj)
    source=obj
    if combined:
        group=group_for(obj);members=member_objects(group)
        source=next((m for m in members if m.ps.uuid==group.anchor_uuid),members[0])
    return source,feather,canvas if combined else (0,0,1,1),combined


def image_for(obj, combined, identifiers=True):
    p=obj.ps
    if p.output_mode=='IMAGE':
        if p.image:return p.image
        from .render_patterns import black
        return black()
    if p.output_mode in {'UV_GRID','COLOR_GRID'}:
        from .projection_images import ensure_uv_grid
        return ensure_uv_grid(p.resolution_x,p.resolution_y,p.output_mode)
    from .render_patterns import ensure
    return ensure(p, identifiers=identifiers and p.show_projected_identifier and not combined)


def build(light, image):
    tree=light.node_tree;tree.nodes.clear();n=tree.nodes;links=tree.links
    raster=n.new('ShaderNodeGroup');raster.node_tree=math_group();raster.name='Raster'
    tex=n.new('ShaderNodeTexImage');tex.name='Content';tex.image=image;tex.extension='CLIP';tex.interpolation='Linear'
    links.new(raster.outputs['UV'],tex.inputs['Vector'])
    alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY'
    links.new(tex.outputs['Alpha'],alpha.inputs[0]);links.new(raster.outputs['Weight'],alpha.inputs[1])
    emission=n.new('ShaderNodeEmission');links.new(tex.outputs['Color'],emission.inputs['Color']);links.new(alpha.outputs[0],emission.inputs['Strength'])
    output=n.new('ShaderNodeOutputLight');links.new(emission.outputs[0],output.inputs['Surface'])


def cleanup(scene=None):
    for obj in list(bpy.data.objects):
        if obj.get(TAG) != VERSION or (scene is not None and obj.get('beam_render_scene')!=scene):continue
        data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if data and data.users==0 and data.get(TAG)==VERSION:bpy.data.lights.remove(data)
    for collection in list(bpy.data.collections):
        if collection.get(TAG)==VERSION and not collection.objects and not collection.children:
            bpy.data.collections.remove(collection)
    prune()
    _signatures.clear()


def prune():
    for light in list(bpy.data.lights):
        if light.get(TAG)==VERSION and light.users==0:bpy.data.lights.remove(light)
    for group in list(bpy.data.node_groups):
        if group.get(TAG)==VERSION and group.users==0:bpy.data.node_groups.remove(group)
    for image in list(bpy.data.images):
        if image.get('beam_render_pattern') and image.users==0:bpy.data.images.remove(image)


def source_visibility(layer, projector):
    """Collection exclusion affects render; eye visibility is viewport-only."""
    memberships=set(projector.users_collection)
    paths=[]
    def visit(node, excluded=False, render_hidden=False):
        excluded=excluded or node.exclude
        render_hidden=render_hidden or node.collection.hide_render
        if node.collection in memberships:paths.append((excluded,render_hidden))
        for child in node.children:
            if not child.collection.get(TAG):visit(child,excluded,render_hidden)
    visit(layer.layer_collection)
    return any(not excluded and not hidden for excluded,hidden in paths)


def sync(scene):
    global _busy
    if _busy or not hasattr(scene,'ps_study'):return
    _busy=True
    try:
        settings=scene.ps_study
        # Scene duplication can link/copy generated root objects. Each scene owns
        # a separate rig; unlink foreign helpers from this scene's root only.
        for collection in list(scene.collection.children):
            if collection.get(TAG)==VERSION and collection.get('beam_render_scene')!=scene:
                scene.collection.children.unlink(collection)
        for foreign in list(scene.collection.objects):
            if foreign.get(TAG)==VERSION and foreign.get('beam_render_scene')!=scene:
                scene.collection.objects.unlink(foreign)
                if foreign.users==0:
                    data=foreign.data;bpy.data.objects.remove(foreign)
                    if data.users==0 and data.get(TAG)==VERSION:bpy.data.lights.remove(data)
        if settings.projection_mode!='CYCLES':
            if any(o.get(TAG)==VERSION and o.get('beam_render_scene')==scene for o in bpy.data.objects):cleanup(scene)
            return
        from .projector_object import projectors
        live=projectors(scene)
        owned=[o for o in bpy.data.objects if o.get(TAG)==VERSION and o.get('beam_render_scene')==scene]
        used=set()
        for projector in live:
            p=projector.ps
            obj=next((o for o in owned if o.parent==projector and o.as_pointer() not in used),None)
            if obj is None:
                data=bpy.data.lights.new(p.identifier+' Cycles','SPOT');data[TAG]=VERSION
                if bpy.app.version<(5,0,0):data.use_nodes=True
                obj=bpy.data.objects.new(p.identifier+' · Cycles',data)
                collection=bpy.data.collections.new('.Beam Cycles · '+p.identifier)
                collection[TAG]=VERSION;collection['beam_render_scene']=scene;collection['beam_render_projector']=projector
                scene.collection.children.link(collection);collection.objects.link(obj)
                obj.parent=projector;obj['ps_helper']=True;obj[TAG]=VERSION;obj['beam_render_scene']=scene;obj.hide_select=True
            # Older/copy-generated helpers may be linked at root: move only our
            # owned helper into its own collection for per-view-layer exclusion.
            collection=next((c for c in obj.users_collection if c.get(TAG)==VERSION and c.get('beam_render_scene')==scene and c.get('beam_render_projector')==projector),None)
            if collection is None:
                collection=bpy.data.collections.new('.Beam Cycles · '+p.identifier)
                collection[TAG]=VERSION;collection['beam_render_scene']=scene;collection['beam_render_projector']=projector
                scene.collection.children.link(collection)
                for previous in list(obj.users_collection):previous.objects.unlink(obj)
                collection.objects.link(obj)
            used.add(obj.as_pointer())
            data=obj.data
            # A copied helper may still reference another scene or a shared light.
            if data.users>1:obj.data=data.copy();data=obj.data
            source,feather,canvas,combined=content(projector)
            sp=source.ps
            signature=(p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v,p.lumens,p.brightness,p.stack,
                       settings.render_multiplier,settings.render_efficacy,scene.unit_settings.scale_length,settings.show_projected_identifiers,
                       sp.output_mode,sp.identifier,sp.resolution_x,sp.resolution_y,tuple(sp.colour),sp.show_grid,
                       sp.show_projected_identifier,sp.image.as_pointer() if sp.image else 0,feather,canvas,combined)
            key=(scene.as_pointer(),obj.as_pointer())
            if _signatures.get(key)!=signature or 'Raster' not in data.node_tree.nodes:
                image=image_for(source,combined,settings.show_projected_identifiers)
                if 'Raster' not in data.node_tree.nodes:build(data,image)
                data.node_tree.nodes['Content'].image=image
                raster=data.node_tree.nodes['Raster']
                values=(p.throw_ratio,p.resolution_y/p.resolution_x,p.shift_h/100,p.shift_v/100,*feather,*canvas)
                for socket,value in zip(raster.inputs,values):socket.default_value=value
                angle,cone=solid_angle(p);data.spot_size=cone;data.spot_blend=0;data.shadow_soft_size=0
                if hasattr(data,'normalize'):data.normalize=True
                # Approximate luminous efficacy, angular-mask correction and SI distance scaling.
                data.energy=p.lumens*p.brightness/100*p.stack/settings.render_efficacy*settings.render_multiplier/(scene.unit_settings.scale_length**2)*(2*math.pi*(1-math.cos(cone/2))/angle)
                _signatures[key]=signature
            matrix=projector.matrix_world.to_quaternion().to_matrix().to_4x4();matrix.translation=projector.matrix_world.translation
            if obj.matrix_world!=matrix:obj.matrix_world=matrix
            hidden=scene.render.engine!='CYCLES' or not (p.show_output and settings.show_outputs) or projector.hide_render
            if obj.hide_render!=hidden:obj.hide_render=hidden
            viewport_hidden=hidden or projector.hide_viewport
            if obj.hide_viewport!=viewport_hidden:obj.hide_viewport=viewport_hidden
            for layer in scene.view_layers:
                if layer.layer_collection is None:continue
                node=layer.layer_collection.children.get(collection.name)
                excluded=not source_visibility(layer,projector)
                if node and node.exclude!=excluded:
                    node.exclude=excluded;layer.update()
                if obj.name in layer.objects:
                    local_hidden=not projector.visible_get(view_layer=layer)
                    if obj.hide_get(view_layer=layer)!=local_hidden:obj.hide_set(local_hidden,view_layer=layer)
        for obj in owned:
            if obj.as_pointer() not in used:
                data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
                if data.users==0 and data.get(TAG)==VERSION:bpy.data.lights.remove(data)
        active_keys={(scene.as_pointer(),o.as_pointer()) for o in scene.objects if o.get(TAG)==VERSION}
        for key in list(_signatures):
            if key[0]==scene.as_pointer() and key not in active_keys:_signatures.pop(key,None)
        for collection in list(bpy.data.collections):
            if collection.get(TAG)==VERSION and not collection.objects and not collection.children:
                bpy.data.collections.remove(collection)
        prune()
    finally:_busy=False


def changed(self,context):
    sync(self.id_data)
    for window in context.window_manager.windows:
        for area in window.screen.areas:area.tag_redraw()


def tick():
    if not _rendering:
        for scene in bpy.data.scenes:sync(scene)
    return .2


@persistent
def reset(*args):
    _signatures.clear()


@persistent
def render_pre(scene,*args):
    global _rendering
    sync(scene);_rendering=True


@persistent
def render_done(*args):
    global _rendering
    _rendering=False


def register():
    for handlers,fn in handlers_list():
        if fn not in handlers:handlers.append(fn)
    if not bpy.app.timers.is_registered(tick):bpy.app.timers.register(tick,persistent=True)


def handlers_list():
    return [(bpy.app.handlers.load_post,reset),(bpy.app.handlers.undo_post,reset),(bpy.app.handlers.redo_post,reset),
            (bpy.app.handlers.render_pre,render_pre),(bpy.app.handlers.render_complete,render_done),(bpy.app.handlers.render_cancel,render_done)]


def unregister():
    if bpy.app.timers.is_registered(tick):bpy.app.timers.unregister(tick)
    for handlers,fn in handlers_list():
        if fn in handlers:handlers.remove(fn)
    cleanup();render_done()
