"""GPU surface projection with one cached first-depth map per projector.

The visual engine consumes scene surfaces and projector optics only. It never
uses the engineering hit, target object, target distance or nominal image plane.
"""
import bpy
import gpu
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader
from . import scene_geometry, typography

_depth_shader=None
_surface_shader=None
_blank=None
_batches={}
_maps={}


def projector_matrices(record,p,unit):
    view=record['rotation'].transposed().to_4x4()
    view.translation=-(record['rotation'].transposed()@record['origin'])
    near=.005/unit
    far=max(near*2,scene_geometry.beam_depth(record['origin'],record['rotation'],10/unit))
    aspect=p.resolution_y/p.resolution_x
    projection=Matrix(((2*p.throw_ratio,0,2*p.shift_h/100,0),
                       (0,2*p.throw_ratio/aspect,2*p.shift_v/100,0),
                       (0,0,-(far+near)/(far-near),-2*far*near/(far-near)),(0,0,-1,0)))
    return view,projection,near,far


def shaders():
    global _depth_shader,_surface_shader,_blank
    if _surface_shader is not None and _blank is not None: return
    interface=gpu.types.GPUStageInterfaceInfo('ps_linear_depth_interface')
    interface.smooth('FLOAT','linearDepth')
    info=gpu.types.GPUShaderCreateInfo()
    info.push_constant('MAT4','lightMatrix')
    info.vertex_in(0,'VEC3','position'); info.vertex_out(interface)
    info.fragment_out(0,'VEC4','firstDepth')
    info.vertex_source('void main(){gl_Position=lightMatrix*vec4(position,1.0);linearDepth=gl_Position.w;}')
    info.fragment_source('void main(){firstDepth=vec4(linearDepth,0.0,0.0,1.0);}')
    _depth_shader=gpu.shader.create_from_info(info)
    interface=gpu.types.GPUStageInterfaceInfo('ps_surface_interface')
    interface.smooth('VEC3','projectorPosition')
    info=gpu.types.GPUShaderCreateInfo()
    info.typedef_source('struct ProjectorUniforms { mat4 viewProjection; mat4 lightView; vec4 raster; vec4 studyColour; vec4 settings; vec4 shadowInfo; vec4 feather; vec4 canvas; vec4 preview; };')
    info.uniform_buf(0,'ProjectorUniforms','params')
    info.sampler(0,'FLOAT_2D','depthImage')
    info.sampler(1,'FLOAT_2D','outputImage')
    info.sampler(2,'FLOAT_2D','identifierImage')
    info.vertex_in(0,'VEC3','position'); info.vertex_out(interface)
    info.fragment_out(0,'VEC4','fragColor')
    info.vertex_source('''#define lightView params.lightView
#define viewProjection params.viewProjection
void main(){
        projectorPosition=(lightView*vec4(position,1.0)).xyz;
        gl_Position=viewProjection*vec4(position,1.0);
        gl_Position.z-=0.000002*gl_Position.w;
    }''')
    info.fragment_source('''
    #define raster params.raster
    #define studyColour params.studyColour
    #define settings params.settings
    #define shadowSize params.shadowInfo.xy
    #define nearPlane params.shadowInfo.z
    float lineAt(float d,float width){float aa=max(fwidth(d),0.00001);return 1.0-smoothstep(width,width+aa,abs(d));}
    vec3 displayRGB(vec3 c){return mix(12.92*c,1.055*pow(max(c,vec3(0.0)),vec3(1.0/2.4))-0.055,greaterThan(c,vec3(0.0031308)));}
    void main(){
        float depth=-projectorPosition.z;
        if(depth<=nearPlane) discard;
        vec2 uv=vec2(projectorPosition.x*raster.x/depth,
                     projectorPosition.y*raster.x/(depth*raster.y))+vec2(0.5)-raster.zw;
        if(any(lessThan(uv,vec2(0.0)))||any(greaterThanEqual(uv,vec2(1.0)))) discard;
        // Compare at the shadow texel's own ray, not at a different point on
        // an oblique receiver. This avoids slope acne without a large bias.
        vec2 sampleUV=(floor(uv*shadowSize)+vec2(0.5))/shadowSize;
        vec3 normal=cross(dFdx(projectorPosition),dFdy(projectorPosition));
        vec3 sampleRay=vec3((sampleUV.x-0.5+raster.z)/raster.x,
                           (sampleUV.y-0.5+raster.w)*raster.y/raster.x,-1.0);
        float denom=dot(normal,sampleRay);
        float receiverDepth=abs(denom)>0.00000001?dot(normal,projectorPosition)/denom:depth;
        float firstDepth=texture(depthImage,sampleUV).r;
        if(receiverDepth>firstDepth+max(settings.w,depth*0.000002)) discard;
        vec2 localUV=uv;
        if(params.preview.x>0.5) uv=params.canvas.xy+uv*params.canvas.zw;
        int mode=int(settings.x+0.5);
        float alpha=0.0; vec3 colour=studyColour.rgb;
        if(mode==0) alpha=0.45;
        if(mode==3){vec2 cells=floor(uv*vec2(16.0,max(2.0,round(16.0*raster.y))));alpha=mod(cells.x+cells.y,2.0)<1.0?0.45:0.0;}
        if(mode==1 && settings.y>0.5){
            vec2 n=vec2(16.0,max(2.0,round(16.0*raster.y)));
            vec2 d=fract(uv*n+vec2(0.5))-vec2(0.5);
            float grid=max(lineAt(d.x,0.008),lineAt(d.y,0.008));
            float edge=min(min(uv.x,1.0-uv.x),min(uv.y,1.0-uv.y)*raster.y);
            float border=1.0-smoothstep(0.004,0.007,edge);
            float diagonals=max(lineAt(uv.x-uv.y,0.0005),lineAt(uv.x+uv.y-1.0,0.0005));
            float crosshair=max(lineAt(uv.x-0.5,0.002)*float(abs(uv.y-0.5)<0.07),
                                lineAt(uv.y-0.5,0.002)*float(abs(uv.x-0.5)<0.04));
            alpha=max(max(grid*0.8,border),max(diagonals*0.65,crosshair));
        }
        if(mode>=4){vec4 source=texture(outputImage,uv);colour=displayRGB(source.rgb);alpha=source.a*0.85;}
        if(settings.z>0.5){
            vec4 textSample=texture(identifierImage,localUV);
            float textAlpha=textSample.a;
            colour=mix(colour,studyColour.rgb,textAlpha);
            alpha=max(alpha,textAlpha);
        }
        vec4 f=params.feather;
        float weight=1.0;
        if(f.x>0.0) weight*=clamp(localUV.x/f.x,0.0,1.0);
        if(f.y>0.0) weight*=clamp((1.0-localUV.x)/f.y,0.0,1.0);
        if(f.z>0.0) weight*=clamp(localUV.y/f.z,0.0,1.0);
        if(f.w>0.0) weight*=clamp((1.0-localUV.y)/f.w,0.0,1.0);
        alpha*=weight;
        if(params.preview.x>0.5) alpha*=0.35;
        if(alpha<0.001) discard;
        fragColor=vec4(colour,alpha);
    }''')
    _surface_shader=gpu.shader.create_from_info(info)
    _blank=gpu.types.GPUTexture((1,1),format='RGBA8',data=gpu.types.Buffer('FLOAT',4,[0.0,0.0,0.0,0.0]))


def prepare_batches():
    shaders(); scene_geometry.prepare()
    for key in list(_batches):
        if key not in scene_geometry.SURFACES: _batches.pop(key,None)
    for key,surface in scene_geometry.SURFACES.items():
        cached=_batches.get(key)
        if cached is None or cached[0] is not surface:
            # Both shaders share the same position vertex layout.
            batch=batch_for_shader(_depth_shader,'TRIS',{'position':surface.vertices},indices=surface.triangles)
            _batches[key]=(surface,batch)


def intersects(surface,matrix):
    points=[matrix@v.to_4d() for v in surface.bounds]
    return not any(all(sign*p[axis]>p.w for p in points) for axis in range(3) for sign in (-1,1))


def shadow_map(obj,record):
    prepare_batches()
    p=obj.ps; unit=bpy.context.scene.unit_settings.scale_length
    view,projection,near,far=projector_matrices(record,p,unit)
    limit=int(bpy.context.scene.ps_study.shadow_resolution)
    scale=limit/max(p.resolution_x,p.resolution_y)
    width=max(16,round(p.resolution_x*scale)); height=max(16,round(p.resolution_y*scale))
    signature=(tuple(v for row in view for v in row),p.throw_ratio,p.shift_h,p.shift_v,
               p.resolution_x,p.resolution_y,width,height,unit,scene_geometry.revision)
    key=obj.as_pointer(); cached=_maps.get(key)
    if cached and cached['signature']==signature: return cached
    if cached and cached['size']==(width,height):
        result=cached
    else:
        if cached: cached['offscreen'].free()
        offscreen=gpu.types.GPUOffScreen(width,height,format='RGBA32F')
        colour=offscreen.texture_color
        colour.filter_mode(False)
        result=dict(size=(width,height),texture=colour,offscreen=offscreen)
    matrix=projection@view
    receivers=[key for key,(surface,batch) in _batches.items() if intersects(surface,matrix)]
    old_viewport=gpu.state.viewport_get()
    try:
        with result['offscreen'].bind():
            gpu.state.viewport_set(0,0,width,height)
            gpu.state.depth_mask_set(True); gpu.state.depth_test_set('LESS_EQUAL'); gpu.state.blend_set('NONE')
            gpu.state.face_culling_set('NONE')
            gpu.state.active_framebuffer_get().clear(color=(far+1,0,0,1),depth=1)
            _depth_shader.bind(); _depth_shader.uniform_float('lightMatrix',matrix)
            for receiver in receivers: _batches[receiver][1].draw(_depth_shader)
    finally:
        gpu.state.viewport_set(*old_viewport)
        gpu.state.depth_mask_set(False)
    result.update(signature=signature,view=view,near=near,far=far,receivers=receivers)
    _maps[key]=result
    return result


def draw(obj,record,view_projection,projected_identifiers=True):
    if not _batches and not scene_geometry.SURFACES: scene_geometry.prepare()
    destination=gpu.state.active_framebuffer_get()
    viewport=gpu.state.viewport_get()
    shadow=shadow_map(obj,record)
    p=obj.ps
    from .blend_groups import preview,group_for,member_objects
    feather,canvas,combined=preview(obj)
    output=p; image_record=record
    if combined:
        anchor=member_objects(group_for(obj))[0]
        output=anchor.ps
        from . import runtime
        image_record=runtime.CACHE.get(anchor.as_pointer(),record)
    mode={'SOLID':0,'GRID':1,'ID':2,'CHECKER':3,'UV_GRID':4,'IMAGE':5,'COLOR_GRID':6}[output.output_mode]
    image=image_record.get('uv_image') if mode in (4,6) else output.image if mode==5 else None
    texture=gpu.texture.from_image(image) if image else _blank
    show_name=p.show_projected_identifier and projected_identifiers and not combined
    show_text=not combined and (show_name or (p.output_mode=='GRID' and p.show_grid))
    text=typography.texture(p.identifier,p.resolution_x,p.resolution_y,p.output_mode,p.colour,show_name) if show_text else _blank
    with destination.bind():
        gpu.state.viewport_set(*viewport)
        gpu.state.blend_set('ADDITIVE' if combined else 'ALPHA'); gpu.state.depth_test_set('LESS_EQUAL'); gpu.state.depth_mask_set(False)
        gpu.state.face_culling_set('NONE')
        shader=_surface_shader; shader.bind()
        values=[matrix[row][column] for matrix in (view_projection,shadow['view']) for column in range(4) for row in range(4)]
        values.extend((p.throw_ratio,p.resolution_y/p.resolution_x,p.shift_h/100,p.shift_v/100))
        values.extend((.9,.92,.95,1) if combined else (*p.colour,1))
        values.extend((mode,float(p.show_grid),float(show_text),.001/bpy.context.scene.unit_settings.scale_length))
        values.extend((*shadow['size'],shadow['near'],0))
        values.extend(feather); values.extend(canvas); values.extend((float(combined),0,0,0))
        uniforms=gpu.types.GPUUniformBuf(gpu.types.Buffer('FLOAT',len(values),values))
        shader.uniform_block('params',uniforms)
        shader.uniform_sampler('depthImage',shadow['texture'])
        shader.uniform_sampler('outputImage',texture); shader.uniform_sampler('identifierImage',text)
        for key in shadow['receivers']: _batches[key][1].draw(shader)


def clear():
    _batches.clear()
    for entry in _maps.values(): entry['offscreen'].free()
    _maps.clear()


def unregister():
    global _depth_shader,_surface_shader,_blank
    clear(); _depth_shader=None; _surface_shader=None; _blank=None
