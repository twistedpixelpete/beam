"""Viewport presentation: unlimited receiver projection plus study annotations."""
import bpy
import gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from .projector_object import projectors
from . import runtime, projection_renderer

_handles=[]
_batches={}
_line_shader=None
isolate_uuid=None
_suppress=False


def clear():
    _batches.clear(); projection_renderer.clear()


def visible(obj):
    from . import blend_groups
    if blend_groups.solo_uuid:
        group=blend_groups.group_for(obj)
        if not group or group.uuid!=blend_groups.solo_uuid: return False
    return obj.visible_get() and (not isolate_uuid or obj.ps.uuid==isolate_uuid)


def shaders():
    global _line_shader
    if _line_shader is None: _line_shader=gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    projection_renderer.shaders()


def build(obj,record):
    unit=bpy.context.scene.unit_settings.scale_length
    origin=record['origin']; border=record['helper_corners']
    frustum=[]
    for i in range(4): frustum.extend((origin,border[i],border[i],border[(i+1)%4]))
    r=record['rotation']; front=origin+r@Vector((0,0,-.5/unit))
    arrow=[origin,front,front,front+r@Vector((-.08/unit,0,.15/unit)),front,front+r@Vector((.08/unit,0,.15/unit))]
    batches={'frustum':batch_for_shader(_line_shader,'LINES',{'pos':frustum}),
             'arrow':batch_for_shader(_line_shader,'LINES',{'pos':arrow})}
    end=record['hit'][0] if record['hit'] else sum(record['beam_corners'],Vector())/4
    batches['centre_ray']=batch_for_shader(_line_shader,'LINES',{'pos':[origin,end]})
    if record['hit']:
        centre=record['hit'][0]; radius=.05/unit
        marker=[centre+r@Vector((-radius,0,0)),centre+r@Vector((radius,0,0)),
                centre+r@Vector((0,-radius,0)),centre+r@Vector((0,radius,0))]
        batches['target']=batch_for_shader(_line_shader,'LINES',{'pos':marker})
    return batches


def draw_3d(options=None,projection=None):
    if _suppress: return
    from . import presentation
    if not hasattr(bpy.types.Object,'ps') or (options is None and not bpy.context.space_data.overlay.show_overlays and not presentation.active(bpy.context.area)): return
    options=options or dict(labels=True,frustums=True,grids=True,overlays=True)
    if not options['overlays']: return
    projection=projection if projection is not None else bpy.context.region_data.perspective_matrix
    destination=gpu.state.active_framebuffer_get()
    viewport=gpu.state.viewport_get()
    shaders()
    for key in list(_batches):
        if key not in runtime.CACHE: _batches.pop(key,None)
    for key in list(projection_renderer._maps):
        if key not in runtime.CACHE: projection_renderer._maps.pop(key)['offscreen'].free()
    try:
        for obj in projectors(bpy.context.scene):
            if not visible(obj): continue
            key=obj.as_pointer(); record=runtime.CACHE.get(key)
            if not record: continue
            p=obj.ps
            settings=bpy.context.scene.ps_study
            if p.show_output and options['grids'] and settings.show_outputs:
                projection_renderer.draw(obj,record,projection,options.get('projected_identifiers',True) and settings.show_projected_identifiers)
            cached=_batches.get(key)
            if not cached or cached[0] is not record:
                cached=(record,build(obj,record)); _batches[key]=cached
            with destination.bind():
                gpu.state.viewport_set(*viewport)
                gpu.state.blend_set('ALPHA'); gpu.state.depth_test_set('LESS_EQUAL'); gpu.state.depth_mask_set(False)
                _line_shader.bind()
                _line_shader.uniform_float('viewportSize',gpu.state.viewport_get()[2:])
                _line_shader.uniform_float('lineWidth',1.5)
                _line_shader.uniform_float('color',(*p.colour,.8))
                for name,batch in cached[1].items():
                    if name=='frustum' and (not p.show_frustum or not options['frustums'] or not settings.show_frustums): continue
                    if name=='centre_ray' and (not p.show_centre_ray or not settings.show_centre_rays or not options['frustums']): continue
                    if name=='target' and not p.show_target_marker: continue
                    batch.draw(_line_shader)
        if options['grids']:
            with destination.bind():
                gpu.state.viewport_set(*viewport)
                from . import blend_display
                blend_display.draw()
    finally:
        gpu.state.depth_mask_set(True); gpu.state.depth_test_set('NONE'); gpu.state.blend_set('NONE')


def draw_labels(projection,width,height,options=None):
    from . import typography
    from .display_units import dimension
    options=options or dict(labels=True,frustums=True,grids=True,overlays=True)
    if not options['overlays'] or not options['labels'] or not bpy.context.scene.ps_study.show_labels: return
    from . import blend_display
    detail=bpy.context.scene.ps_study.label_detail
    if options['grids'] and detail=='FULL': blend_display.labels(projection,width,height)
    def screen(point):
        clip=projection@Vector((*point,1))
        if clip.w<=0: return None
        return ((clip.x/clip.w+1)*width/2,(clip.y/clip.w+1)*height/2)
    # A small screen-space heuristic keeps shared-edge dimensions out of
    # neighbouring images without changing any world-space study geometry.
    footprints={}
    for other in projectors(bpy.context.scene):
        cached=runtime.CACHE.get(other.as_pointer())
        if not cached or not visible(other) or not other.ps.show_output:continue
        points=[screen(c) for c in cached['corners']]
        if all(p is not None for p in points):
            footprints[other.as_pointer()]=(min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points))
    for obj in projectors(bpy.context.scene):
        if not visible(obj) or not obj.ps.show_identifier: continue
        record=runtime.CACHE.get(obj.as_pointer())
        if not record: continue
        location=screen(record['origin'])
        if location:
            typography.label(obj.ps.identifier,location[0]+12,location[1]+10,16,(*obj.ps.colour,1),active=obj==bpy.context.scene.ps_study.active_projector)
        if detail!='OFF' and record['hit'] and obj.ps.show_output and options['grids']:
            target=screen(record['centre'])
            if target and detail=='FULL':
                typography.annotation(dimension(record['metrics'].distance,bpy.context.scene.ps_study.display_units),
                                 target[0]+12,target[1]-30,12)
            # Nominal dimensions at the centre target's axial depth. These do
            # not claim to measure the distorted multi-surface footprint.
            units=bpy.context.scene.ps_study.display_units
            corners=record['corners']; metrics=record['metrics']
            for text,candidates,offset in (
                ('W '+(f'{metrics.width:.2f} m' if units=='m' else f'{metrics.width*1000:,.0f} mm'),[(corners[2]+corners[3])/2,(corners[0]+corners[1])/2],(12,18)),
                ('H '+(f'{metrics.height:.2f} m' if units=='m' else f'{metrics.height*1000:,.0f} mm'),[(corners[1]+corners[2])/2,(corners[0]+corners[3])/2],(18,0)),
            ):
                centre=screen(record['centre'])
                def crowded(point):
                    pos=screen(point)
                    if pos is None:return float('inf')
                    delta=Vector(pos)-Vector(centre) if centre else Vector(offset)
                    if delta.length:delta.normalize()
                    x,y=Vector(pos)+delta*18
                    return sum(left<=x<=right and bottom<=y<=top for key,(left,right,bottom,top) in footprints.items() if key!=obj.as_pointer())
                position=screen(min(candidates,key=crowded))
                if position:
                    # Offset outward in screen space, independent of camera roll.
                    centre=screen(record['centre'])
                    delta=Vector(position)-Vector(centre) if centre else Vector(offset)
                    if delta.length:delta.normalize()
                    typography.annotation(text,position[0]+delta.x*18,position[1]+delta.y*18,12,align='CENTER' if abs(delta.y)>abs(delta.x) else 'RIGHT' if delta.x<0 else 'LEFT')



def draw_2d():
    if _suppress: return
    context=bpy.context
    from . import presentation
    if not context.region_data or not hasattr(bpy.types.Object,'ps') or (not context.space_data.overlay.show_overlays and not presentation.active(context.area)): return
    draw_labels(context.region_data.perspective_matrix,context.region.width,context.region.height)


def register():
    _handles.extend([bpy.types.SpaceView3D.draw_handler_add(draw_3d,(),'WINDOW','POST_VIEW'),
                     bpy.types.SpaceView3D.draw_handler_add(draw_2d,(),'WINDOW','POST_PIXEL')])


def unregister():
    global _line_shader,isolate_uuid
    for handle in _handles: bpy.types.SpaceView3D.draw_handler_remove(handle,'WINDOW')
    _handles.clear(); clear()
    from . import typography
    typography.clear(); projection_renderer.unregister()
    _line_shader=None; isolate_uuid=None
