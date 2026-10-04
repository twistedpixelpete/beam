"""Transactional screen creation, explicit updates and independent identities."""
import json,re
import bpy,bmesh
from mathutils import Matrix,Vector
from . import screen_math,screen_uv,screen_surface,screen_data
from .utils import new_uuid

_owners={}
_busy=False


def next_id(scene=None):
    maximum=max([s.get('beam_screen_counter',0) for s in bpy.data.scenes]+[0])
    for o in bpy.data.objects:
        match=re.fullmatch(r'SCR(\d+)',o.beam_screen.identifier)
        if match:maximum=max(maximum,int(match[1]))
    value=maximum+1
    (scene or bpy.context.scene)['beam_screen_counter']=value
    return f'SCR{value:03d}'


def parameter_values(p):
    return {k:(getattr(p,k).name_full if getattr(p,k) else None) if k in {'source','conform_target'} else getattr(p,k) for k in screen_data.PARAMETERS if k not in {'name','preset'}}


def signature(p):
    return json.dumps(parameter_values(p),sort_keys=True)


def acknowledge(p,*keys):
    """A UV/normal operation must not clear unrelated pending geometry edits."""
    try:built=json.loads(p.built_signature)
    except (ValueError,TypeError):return
    current=parameter_values(p)
    for key in keys:built[key]=current[key]
    p.built_signature=json.dumps(built,sort_keys=True)


def collection(scene):
    c=next((c for c in scene.collection.children if c.get('beam_screens')),None)
    if c is None:
        c=bpy.data.collections.new('Beam · Screens');c['beam_screens']=True;scene.collection.children.link(c)
    return c


def material(led=False):
    name='Beam · LED Off' if led else 'Beam · Screen Neutral'
    mat=bpy.data.materials.get(name)
    if mat is None:
        mat=bpy.data.materials.new(name);mat.diffuse_color=(.035,.04,.045,1) if led else (.65,.65,.65,1)
        mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=mat.diffuse_color;bsdf.inputs['Roughness'].default_value=.8
    return mat


def make_mesh(name,geometry,unit):
    vertices,faces,uvs=geometry
    mesh=bpy.data.meshes.new(name)
    try:
        mesh.from_pydata([tuple(x/unit for x in p) for p in vertices],[],faces);mesh.update()
        screen_uv.assign(mesh,uvs)
        return mesh
    except Exception:
        bpy.data.meshes.remove(mesh);raise


def dimensions(mesh,matrix,unit):
    points=[matrix.to_3x3()@v.co*unit for v in mesh.vertices]
    # Surface dimensions are oriented bounding extents, never claimed as path length.
    return dict(width=max(v.x for v in points)-min(v.x for v in points),height=max(v.z for v in points)-min(v.z for v in points))


def draft(context,p):
    unit=context.scene.unit_settings.scale_length;matrix=Matrix.Translation(context.scene.cursor.location);mesh=None
    if p.category=='LED' and p.screen_type not in {'FLAT','ARC','CLOSED'}:raise ValueError('Cabinet-based LED supports Flat, Arc and Closed; use Projection for arbitrary surfaces')
    try:
        if p.screen_type in {'FLAT','ARC','CLOSED'}:
            if p.screen_type=='FLAT' and p.category=='PROJECTION' and p.aspect!='FREE':
                ratio=p.aspect_ratio if p.aspect=='CUSTOM' else float(p.aspect.split(':')[0])/float(p.aspect.split(':')[1])
                if p.width/ratio<.001:raise ValueError('This aspect ratio produces a height below 1 mm')
                p.height=p.width/ratio
            geometry,metrics=screen_math.build(p);mesh=make_mesh('Beam display draft',geometry,unit)
        elif p.screen_type=='CURVE':
            path,closed=screen_surface.curve_path(context,p.source)
            rotation=p.source.matrix_world.to_quaternion().to_matrix();inverse=rotation.transposed()
            # Preserve source-local up, but bake source scale into physical geometry.
            origin=p.source.matrix_world.translation
            points=[inverse@(v-origin)*unit for v in path]
            anchor=Vector(((min(v.x for v in points)+max(v.x for v in points))/2,(min(v.y for v in points)+max(v.y for v in points))/2,min(v.z for v in points)))
            points=[tuple(v-anchor) for v in points]
            length=sum((Vector(a)-Vector(b)).length for a,b in zip(points,points[1:]))
            geometry=screen_math.strip(points,p.height,p.vertical_segments,closed,p.origin=='CENTRE');mesh=make_mesh('Beam curve display',geometry,unit)
            matrix=rotation.to_4x4();matrix.translation=origin+rotation@(anchor/unit)
            metrics=dict(width=length,length=length,height=p.height,chord=(Vector(points[-1])-Vector(points[0])).length,rx=p.resolution_x,ry=p.resolution_y,curve_sampled=True)
        else:
            mesh=screen_surface.mesh_source(context,p.source,p.selected_faces)
            # Bake source scale/shear in its rotation frame; keep sensible local axes.
            rotation=p.source.matrix_world.to_quaternion().to_matrix();linear=rotation.transposed()@p.source.matrix_world.to_3x3()
            mesh.transform(linear.to_4x4())
            low=Vector(tuple(min(v.co[i] for v in mesh.vertices) for i in range(3)));high=Vector(tuple(max(v.co[i] for v in mesh.vertices) for i in range(3)))
            anchor=(low+high)/2
            if p.origin=='BOTTOM':anchor.z=low.z
            mesh.transform(Matrix.Translation(-anchor));screen_surface.remap(mesh,p)
            matrix=rotation.to_4x4();matrix.translation=p.source.matrix_world.translation+rotation@anchor
            axes={'XZ':(0,2),'XY':(0,1),'YZ':(1,2)}[p.uv_plane]
            metrics=dict(width=(high[axes[0]]-low[axes[0]])*unit,height=(high[axes[1]]-low[axes[1]])*unit,depth=(high.y-low.y)*unit,rx=p.resolution_x,ry=p.resolution_y,surface_bounds=True)
        if p.direction=='REVERSED':mesh.flip_normals()
        mesh.update()
        return mesh,metrics,matrix
    except Exception:
        if mesh and mesh.users==0:bpy.data.meshes.remove(mesh)
        raise


def detail_mesh(obj):
    """Consolidated backs/sides; front faces belong ONLY to the display object."""
    p=obj.beam_screen;unit=p.unit_scale
    # Cabinet cells are exact for flat/faceted walls, chordal approximations for smooth arcs.
    if p.screen_type=='FLAT':path=screen_math.faceted_path(p.cabinet_width,p.columns,0)
    elif p.led_geometry=='FACETED' and p.screen_type=='ARC':path=screen_math.faceted_path(p.cabinet_width,p.columns,p.joint_angle*(1 if p.curvature=='CONVEX' else -1))
    else:
        metrics=json.loads(p.metrics);path=screen_math.circular_path(metrics['radius'],metrics['angle'],p.columns,p.curvature=='CONVEX',p.seam_angle,p.screen_type=='CLOSED')
    verts,faces,uvs=screen_math.strip(path,p.rows*p.cabinet_height,p.rows,False,p.origin=='CENTRE')
    result=[];polys=[];maps=[]
    for face in faces:
        front=[Vector(verts[i]) for i in face];normal=(front[1]-front[0]).cross(front[3]-front[0]).normalized()
        if p.direction=='REVERSED':normal.negate();front.reverse()
        back=[v-normal*p.cabinet_depth for v in front];start=len(result);result.extend(tuple(v) for v in front+back)
        for f in [(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:
            polys.append(tuple(start+i for i in f));maps.append(((0,0),(1,0),(1,1),(0,1)))
    return make_mesh(obj.name+' · Cabinet backs',(result,polys,maps),unit)


def sync_detail(obj,rebuild=False):
    p=obj.beam_screen;children=[c for c in obj.children if c.get('beam_screen_detail')]
    detail=children[0] if children else None
    if p.category=='LED' and p.show_detail:
        if rebuild or not detail:
            mesh=detail_mesh(obj)
            if detail:
                old=detail.data;detail.data=mesh
                if old.users==0:bpy.data.meshes.remove(old)
            else:
                detail=bpy.data.objects.new(p.identifier+' · Cabinets',mesh);obj.users_collection[0].objects.link(detail);detail.parent=obj;detail['beam_screen_detail']=True
            detail.hide_select=True;detail.data.materials.append(material(True))
        if detail.hide_viewport:detail.hide_viewport=False
        if detail.hide_render:detail.hide_render=False
    elif detail:
        if not detail.hide_viewport:detail.hide_viewport=True
        if not detail.hide_render:detail.hide_render=True
    if obj.show_wire!=p.show_wire:obj.show_wire=p.show_wire
    if obj.show_all_edges!=p.show_wire:obj.show_all_edges=p.show_wire


def create(context,p):
    mesh,metrics,matrix=draft(context,p);obj=None
    try:
        obj=bpy.data.objects.new('Screen',mesh);collection(context.scene).objects.link(obj)
        screen_data.copy_settings(p,obj.beam_screen);s=obj.beam_screen;s.is_screen=True;s.uuid=new_uuid();s.identifier=next_id(context.scene);obj.name=s.identifier+' · '+s.name
        obj.matrix_world=matrix;s.unit_scale=context.scene.unit_settings.scale_length;s.metrics=json.dumps(metrics);s.built_signature=signature(s)
        mesh.materials.clear();mesh.materials.append(material(s.category=='LED'))
        sync_detail(obj);_owners[s.uuid]=obj.as_pointer()
        return obj
    except Exception:
        if obj:
            for child in list(obj.children):
                data=child.data;bpy.data.objects.remove(child,do_unlink=True)
                if data and data.users==0:bpy.data.meshes.remove(data)
            bpy.data.objects.remove(obj,do_unlink=True)
        if mesh.users==0:bpy.data.meshes.remove(mesh)
        raise


def update(context,obj):
    p=obj.beam_screen
    if obj.mode!='OBJECT':raise ValueError('Leave Edit Mode before regenerating a screen')
    if p.source==obj:raise ValueError('A screen cannot use itself as its source')
    if p.screen_type=='SURFACE' and not p.source:
        mesh=obj.data.copy()
        try:screen_surface.remap(mesh,p)
        except Exception:bpy.data.meshes.remove(mesh);raise
        axes={'XZ':(0,2),'XY':(0,1),'YZ':(1,2)}[p.uv_plane];unit=context.scene.unit_settings.scale_length
        extent=[(max(v.co[i] for v in mesh.vertices)-min(v.co[i] for v in mesh.vertices))*unit for i in range(3)]
        metrics=dict(width=extent[axes[0]],height=extent[axes[1]],depth=extent[1],rx=p.resolution_x,ry=p.resolution_y,surface_bounds=True)
    else:mesh,metrics,_=draft(context,p)
    # Preserve user-assigned materials, transforms, links and non-Beam modifiers.
    old=obj.data
    for mat in old.materials:mesh.materials.append(mat)
    obj.name=p.identifier+' · '+p.name
    obj.data=mesh;p.unit_scale=context.scene.unit_settings.scale_length;p.metrics=json.dumps(metrics);p.built_signature=signature(p);p.diagnostic='Updated · run Validate UV'
    if old.users==0:bpy.data.meshes.remove(old)
    sync_detail(obj,True)
    if obj.active_material and obj.active_material.get('beam_screen_pattern'):
        from .screen_patterns import apply
        apply(obj)
    from . import runtime,target_raycast
    target_raycast.invalidate();runtime.invalidate()


def reconcile():
    global _busy
    if _busy or not hasattr(bpy.types.Object,'beam_screen'):return
    _busy=True
    try:
        for child in list(bpy.data.objects):
            if child.get('beam_screen_detail') and (not child.parent or not child.parent.beam_screen.is_screen):
                data=child.data;bpy.data.objects.remove(child,do_unlink=True)
                if data and data.users==0:bpy.data.meshes.remove(data)
        screens=[o for o in bpy.data.objects if o.type=='MESH' and o.beam_screen.is_screen and not o.library]
        keys={o.as_pointer() for o in screens}
        for uid,key in list(_owners.items()):
            if key not in keys:_owners.pop(uid,None)
        for o in sorted(screens,key=lambda o:o.name):_owners.setdefault(o.beam_screen.uuid,o.as_pointer())
        ids=set()
        for obj in sorted(screens,key=lambda o:_owners.get(o.beam_screen.uuid)!=o.as_pointer()):
            p=obj.beam_screen
            if not p.uuid or _owners.get(p.uuid)!=obj.as_pointer() or p.identifier in ids:
                p.uuid=new_uuid();p.identifier=next_id(obj.users_scene[0] if obj.users_scene else bpy.context.scene);obj.name=p.identifier+' · '+p.name
                obj.data=obj.data.copy()
                # Copied test-pattern materials carry the old ID: regenerate on explicit Apply Pattern.
                for index,mat in enumerate(obj.data.materials):
                    if mat and mat.get('beam_screen_pattern'):obj.data.materials[index]=material(p.category=='LED')
                for child in obj.children:
                    if child.get('beam_screen_detail'):
                        child.name=p.identifier+' · Cabinets'
                        if child.data.users>1:child.data=child.data.copy()
            elif obj.data.users>1:obj.data=obj.data.copy()
            ids.add(p.identifier);_owners[p.uuid]=obj.as_pointer()
            sync_detail(obj)
    finally:_busy=False


def select(context,obj):
    if context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    for other in context.selected_objects:other.select_set(False)
    obj.select_set(True);context.view_layer.objects.active=obj
