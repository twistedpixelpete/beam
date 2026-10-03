"""Screen-only overlays reuse Beam typography; never exported as geometry."""
import json
import bpy,gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from . import typography

_cache={}
_shader=None
_texture_shader=None


def clear(*args):_cache.clear()


def geometry(obj):
    key=obj.as_pointer()
    if key in _cache:return _cache[key]
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    try:
        mesh.calc_loop_triangles();points=[v.co.copy() for v in mesh.vertices];counts={}
        for face in mesh.polygons:
            for edge in face.edge_keys:counts[edge]=counts.get(edge,0)+1
        border=[points[i] for edge,n in counts.items() if n==1 for i in edge]
        all_edges=[points[i] for e in mesh.edges for i in e.vertices]
        # A representative normal, not a claim of a single normal for curved surfaces.
        face=mesh.polygons[len(mesh.polygons)//2] if mesh.polygons else None
        normal=[face.center.copy(),face.center+face.normal*.4/bpy.context.scene.unit_settings.scale_length] if face else []
        positions=[];uvs=[]
        if mesh.uv_layers.active:
            for tri in mesh.loop_triangles:
                for loop in tri.loops:
                    positions.append(points[mesh.loops[loop].vertex_index]);uvs.append(tuple(mesh.uv_layers.active.data[loop].uv))
        centre=sum(points,Vector())/max(len(points),1)
        _cache[key]=dict(border=border,edges=all_edges,normal=normal,positions=positions,uvs=uvs,centre=centre,faces=[f.center.copy() for f in mesh.polygons])
        return _cache[key]
    finally:ev.to_mesh_clear()


def screens():
    if not hasattr(bpy.types.Object,'beam_screen'):return []
    return [o for o in bpy.context.scene.objects if o.type=='MESH' and o.beam_screen.is_screen and o.visible_get()]


def draw_3d(options):
    global _shader,_texture_shader
    if not options.get('overlays',True):return
    if _shader is None:_shader=gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    if _texture_shader is None:
        info=gpu.types.GPUShaderCreateInfo();info.push_constant('MAT4','mvp');info.sampler(0,'FLOAT_2D','image')
        info.vertex_in(0,'VEC3','pos');info.vertex_in(1,'VEC2','texCoord')
        interface=gpu.types.GPUStageInterfaceInfo('beam_screen_uv');interface.smooth('VEC2','uv');info.vertex_out(interface)
        info.fragment_out(0,'VEC4','colour')
        info.vertex_source('void main(){uv=texCoord;gl_Position=mvp*vec4(pos,1.0);gl_Position.z-=0.000005*gl_Position.w;}')
        info.fragment_source('void main(){vec4 c=texture(image,uv);vec3 rgb=mix(12.92*c.rgb,1.055*pow(max(c.rgb,vec3(0.0)),vec3(1.0/2.4))-0.055,step(vec3(0.0031308),c.rgb));colour=vec4(rgb,c.a);}')
        _texture_shader=gpu.shader.create_from_info(info)
    try:
        gpu.state.depth_test_set('LESS_EQUAL');gpu.state.depth_mask_set(False);gpu.state.blend_set('ALPHA')
        for obj in screens():
            p=obj.beam_screen;data=geometry(obj)
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(obj.matrix_world)
                mat=obj.active_material
                image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if mat and mat.use_nodes and mat.get('beam_screen_pattern') else None
                if image and options.get('grids',True) and data['positions']:
                    batch=batch_for_shader(_texture_shader,'TRIS',{'pos':data['positions'],'texCoord':data['uvs']});_texture_shader.bind();_texture_shader.uniform_float('mvp',gpu.matrix.get_projection_matrix()@gpu.matrix.get_model_view_matrix());_texture_shader.uniform_sampler('image',gpu.texture.from_image(image));batch.draw(_texture_shader)
                lines=(data['border'] if p.show_outline else [])+(data['normal'] if p.show_normal else [])
                if p.show_cabinet_lines and p.category=='LED':lines+=cabinet_overlay(obj,data)[0]
                if p.show_centre:
                    z=[v.z for v in data['positions']];c=data['centre'];lines+=[Vector((c.x,c.y,min(z,default=0))),Vector((c.x,c.y,max(z,default=0)))]
                if lines:
                    batch=batch_for_shader(_shader,'LINES',{'pos':lines});_shader.bind();_shader.uniform_float('viewportSize',gpu.state.viewport_get()[2:]);_shader.uniform_float('lineWidth',1.);_shader.uniform_float('color',(.72,.77,.8,.5));batch.draw(_shader)
    finally:gpu.state.depth_mask_set(True);gpu.state.depth_test_set('NONE');gpu.state.blend_set('NONE')


def labels(projection,width,height,options):
    if not options.get('overlays',True) or not options.get('labels',True):return
    def screen(v):
        c=projection@Vector((*v,1))
        return ((c.x/c.w+1)*width/2,(c.y/c.w+1)*height/2) if c.w>0 else None
    for obj in screens():
        p=obj.beam_screen
        if not p.show_label:continue
        point=screen(obj.matrix_world.translation)
        if point:
            x,y=point;typography.label(p.identifier+' · '+p.name[:36],x+12,y-25,14,(.5,.65,.68,1))
            if p.show_dimensions:
                m=json.loads(p.metrics);text=('Nominal ' if obj.modifiers or any(abs(s-1)>1e-5 for s in obj.matrix_world.to_scale()) else 'Bounds ' if m.get('surface_bounds') else '')+f"{m.get('width',0):.2f} × {m.get('height',0):.2f} m · {m.get('rx',p.resolution_x)} × {m.get('ry',p.resolution_y)}"
                if 'pitch_x' in m:text+=f" · {m['pitch_x']:.3f} mm"
                typography.annotation(text,x+12,y-44,12)
        if p.show_cabinet_ids and p.category=='LED':
            centres=cabinet_overlay(obj,geometry(obj))[1]
            if len(centres)<=400:
                for i,centre in centres.items():
                    point=screen(obj.matrix_world@centre)
                    if point:typography.annotation(str(i),*point,11,align='CENTER')


def cabinet_overlay(obj,data):
    """Iso-UV cabinet borders and centres, independent of tessellation density."""
    p=obj.beam_screen;signature=(p.columns,p.rows)
    if data.get('cabinet_signature')==signature:return data['cabinet_lines'],data['cabinet_centres']
    lines=[];centres={};positions=data['positions'];uvs=data['uvs']
    for k in range(0,len(positions),3):
        xyz=positions[k:k+3];tri=uvs[k:k+3]
        for axis,count in ((0,p.columns),(1,p.rows)):
            low=min(v[axis] for v in tri);high=max(v[axis] for v in tri)
            for cut in range(max(1,int(low*count)+1),min(count,int(high*count)+1)):
                value=cut/count;hits=[]
                for a,b in ((0,1),(1,2),(2,0)):
                    delta=tri[b][axis]-tri[a][axis]
                    if abs(delta)<1e-10:continue
                    t=(value-tri[a][axis])/delta
                    if -1e-7<=t<=1+1e-7:hits.append(xyz[a].lerp(xyz[b],max(0,min(1,t))))
                if len(hits)>=2:lines.extend(hits[:2])
        if p.columns*p.rows<=400:
            # Barycentric lookup at each cabinet centre; at most 400 labels.
            a,b,c=map(Vector,tri);den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
            if abs(den)<1e-12:continue
            for j in range(max(0,int(min(v[1] for v in tri)*p.rows)),min(p.rows,int(max(v[1] for v in tri)*p.rows)+1)):
                for i in range(max(0,int(min(v[0] for v in tri)*p.columns)),min(p.columns,int(max(v[0] for v in tri)*p.columns)+1)):
                    u,v=(i+.5)/p.columns,(j+.5)/p.rows
                    wa=((b.y-c.y)*(u-c.x)+(c.x-b.x)*(v-c.y))/den;wb=((c.y-a.y)*(u-c.x)+(a.x-c.x)*(v-c.y))/den;wc=1-wa-wb
                    if min(wa,wb,wc)>=-1e-6:centres[j*p.columns+i+1]=xyz[0]*wa+xyz[1]*wb+xyz[2]*wc
    data.update(cabinet_signature=signature,cabinet_lines=lines,cabinet_centres=centres)
    return lines,centres
