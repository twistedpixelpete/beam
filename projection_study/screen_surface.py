"""Non-destructive source extraction, evaluated curve paths and conforming."""
import bpy,bmesh
from mathutils import Matrix,Vector
from . import screen_uv


def mesh_source(context,source,selected_only=False):
    if not source or source.type!='MESH':raise ValueError('Choose a mesh source')
    if source.name not in context.scene.objects:raise ValueError('Source must be in the current scene')
    if selected_only:
        if source.mode=='EDIT':
            bm=bmesh.from_edit_mesh(source.data).copy()
        else:
            bm=bmesh.new();bm.from_mesh(source.data)
        try:
            remove=[f for f in bm.faces if not f.select]
            bmesh.ops.delete(bm,geom=remove,context='FACES')
            loose=[v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm,geom=loose,context='VERTS')
            if not bm.faces:raise ValueError('Select source faces in Edit Mode first')
            mesh=bpy.data.meshes.new('Beam surface draft');bm.to_mesh(mesh)
        finally:bm.free()
    else:
        evaluated=source.evaluated_get(context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=context.evaluated_depsgraph_get())
    if not mesh.polygons:
        bpy.data.meshes.remove(mesh);raise ValueError('Source has no faces')
    return mesh


def curve_path(context,source):
    if not source or source.type!='CURVE':raise ValueError('Choose a Blender Curve source')
    if source.name not in context.scene.objects:raise ValueError('Curve source must be in the current scene')
    if len(source.data.splines)!=1:raise ValueError('Use one spline per screen; split disconnected paths first')
    spline=source.data.splines[0]
    temp=source.copy();temp.data=source.data.copy();temp.name='.Beam path evaluation'
    temp.data.bevel_depth=0;temp.data.extrude=0;temp.data.bevel_object=None
    temp.data.dimensions='3D';temp.data.fill_mode='FULL'
    context.scene.collection.objects.link(temp)
    try:
        context.view_layer.update();ev=temp.evaluated_get(context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        try:
            links={v.index:[] for v in mesh.vertices}
            for e in mesh.edges:
                a,b=e.vertices;links[a].append(b);links[b].append(a)
            if not links or any(len(v) not in (1,2) for v in links.values()):raise ValueError('Curve must evaluate to a single unbranched path without bevel or surface modifiers')
            ends=[k for k,v in links.items() if len(v)==1];closed=not ends
            first=Vector(spline.bezier_points[0].co if spline.type=='BEZIER' else spline.points[0].co[:3])
            start=min(ends or links.keys(),key=lambda i:(mesh.vertices[i].co-first).length)
            order=[start];previous=None;current=start
            while True:
                candidates=[k for k in links[current] if k!=previous]
                if not candidates:break
                nxt=candidates[0]
                if nxt==start:break
                if nxt in order:raise ValueError('Curve path folds into ambiguous topology')
                order.append(nxt);previous,current=current,nxt
            if len(order)!=len(links):raise ValueError('Curve contains disconnected paths')
            path=[source.matrix_world@mesh.vertices[i].co for i in order]
            if closed:path.append(path[0].copy())
            return path,closed
        finally:ev.to_mesh_clear()
    finally:
        data=temp.data;bpy.data.objects.remove(temp,do_unlink=True);bpy.data.curves.remove(data)


def remap(mesh,p):
    if p.uv_method=='EXISTING':
        if not mesh.uv_layers.active:raise ValueError('Source has no UV map; choose Projected or Surface Distance')
    else:screen_uv.assign(mesh,screen_uv.projected(mesh,p.uv_plane) if p.uv_method=='PROJECTED' else screen_uv.distance_grid(mesh))


def conform(context,obj):
    p=obj.beam_screen;target=p.conform_target
    if not target or target==obj or target.type!='MESH':raise ValueError('Choose a different mesh as Conform Target')
    if target.name not in context.scene.objects:raise ValueError('Conform target must be in this scene')
    # Keep a reversible shrinkwrap on the display object; exports evaluate it.
    # Modifiers do not support ID properties on every Blender version.
    modifier=obj.modifiers.get('Beam Conform')
    if modifier and modifier.type!='SHRINKWRAP':raise ValueError('Rename the existing Beam Conform modifier first')
    if modifier is None:modifier=obj.modifiers.new('Beam Conform','SHRINKWRAP')
    modifier.target=target;modifier.wrap_method='NEAREST_SURFACEPOINT';modifier.wrap_mode='ON_SURFACE';modifier.offset=p.conform_offset/context.scene.unit_settings.scale_length
    return modifier
