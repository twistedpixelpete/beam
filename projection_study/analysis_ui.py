"""Small explicit analysis tool. Draw consumes cached results only."""
import bpy
from bpy.app.handlers import persistent
from . import analysis_runtime,optics_library,optics_validation
_handle=None
_legend_handle=None

class BEAM_OT_analyse(bpy.types.Operator):
    bl_idname='beam.analyse';bl_label='Analyse Surface';bl_options={'REGISTER'}
    def execute(self,context):
        from .projector_object import projectors
        s=context.scene.ps_study;receiver=s.analysis_receiver
        if s.analysis_mode=='ACUITY' and not s.analysis_observer:self.report({'ERROR'},'Choose or add an Observer');return {'CANCELLED'}
        if not receiver:self.report({'ERROR'},'Choose a receiver surface');return {'CANCELLED'}
        objects=list(projectors(context.scene))
        if s.analysis_scope=='PROJECTOR':objects=[s.active_projector] if s.active_projector else []
        elif s.analysis_scope=='GROUP':
            from .blend_groups import active_group,member_objects
            group=active_group(context);objects=member_objects(group) if group else []
        try:
            if not receiver.beam_screen.is_screen and not receiver.get('beam_receiver_uuid'):
                from .utils import new_uuid
                receiver['beam_receiver_uuid']=new_uuid()
            analysis_runtime.analyse(context,receiver,objects,int(s.analysis_detail));s.analysis_show=True
        except (ValueError,RuntimeError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class BEAM_OT_apply_optics(bpy.types.Operator):
    bl_idname='beam.apply_optics';bl_label='Use Preset Values';bl_options={'UNDO'}
    @classmethod
    def poll(cls,context):
        obj=context.scene.ps_study.active_projector
        return bool(obj and obj.ps.is_projector)
    def execute(self,context):
        p=context.scene.ps_study.active_projector.ps;model=optics_library.PROJECTORS.get(p.optics_model)
        if not model:return {'CANCELLED'}
        p.resolution_x,p.resolution_y=model.resolution;p.lumens=model.lumens
        return {'FINISHED'}

class BEAM_OT_study_package(bpy.types.Operator):
    bl_idname='beam.study_package';bl_label='Export Study Package'
    filepath:bpy.props.StringProperty(subtype='DIR_PATH',default='Beam-Study')
    include_views:bpy.props.BoolProperty(name='Render Study Views',default=True)
    def invoke(self,context,event):
        self.source_area=next((a for a in context.screen.areas if a.type=='VIEW_3D'),None)
        context.window_manager.fileselect_add(self);return {'RUNNING_MODAL'}
    def execute(self,context):
        from .study_reporting import export
        try:export(context,bpy.path.abspath(self.filepath),self.include_views,getattr(self,'source_area',None))
        except (ValueError,RuntimeError,OSError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        self.report({'INFO'},'Study JSON, HTML and views exported');return {'FINISHED'}

def draw(layout,context):
    has_result=bool(analysis_runtime.CACHE.get(context.scene.as_pointer()))
    header,body=layout.panel('beam_surface_analysis_result' if has_result else 'beam_surface_analysis',default_closed=not has_result);header.label(text='Surface Analysis')
    if body is None:return
    s=context.scene.ps_study
    body.prop(s,'analysis_mode')
    body.prop(s,'analysis_receiver');body.prop(s,'analysis_scope');body.prop(s,'analysis_detail')
    if s.analysis_mode=='ACUITY':
        body.prop(s,'analysis_observer');body.operator('beam.add_observer',icon='EMPTY_AXIS')
        obj=s.analysis_observer
        if obj:
            body.prop(obj,'location',text='Base Position');body.prop(obj.beam_observer,'eye_height');body.prop(obj.beam_observer,'threshold')
        body.label(text='Nominal eyesight guidance · viewer visibility tested',icon='INFO')
    elif s.analysis_mode=='ILLUMINANCE':
        body.prop(s,'illuminance_scale')
        if s.illuminance_scale=='FIXED':body.prop(s,'illuminance_max')
        body.prop(s,'use_target_illuminance')
        if s.use_target_illuminance:body.prop(s,'target_illuminance')
    body.operator('beam.analyse')
    result=analysis_runtime.CACHE.get(context.scene.as_pointer())
    if not result:return
    if analysis_runtime.stale(result,s.analysis_mode):body.label(text='Scene changed · Analyse again',icon='ERROR');return
    if s.analysis_mode=='ACUITY' and not result.get('observer'):body.label(text='Choose Observer · Analyse again',icon='INFO');return
    body.label(text=result['receiver_name']);body.label(text='Sources: '+', '.join(result['projector_names']))
    body.prop(s,'analysis_show')
    from .analysis_display import lines
    for line in lines(result,s.analysis_mode,s.display_units):body.label(text=line)
    body.label(text='Sampled estimate · gaps untested',icon='INFO')


def optics(layout,p):
    header,body=layout.panel('beam_optics',default_closed=True);header.label(text='Optics Guidance')
    if body is None:return
    body.prop(p,'optics_model');body.prop(p,'optics_lens')
    if p.optics_model=='MANUAL':return
    body.operator('beam.apply_optics')
    lens=optics_library.LENSES.get(p.optics_lens)
    if lens:
        body.label(text=f'Throw range {lens.throw_min:.2f}–{lens.throw_max:.2f}')
        for label,value,limits in [('H',p.shift_h,lens.h_limits),('V',p.shift_v,lens.v_limits)]:
            if limits:body.label(text=f'{label} {value:+.1f}% · range {limits[0]:+.0f} to {limits[1]:+.0f}%')
    issues=optics_validation.validate(p.optics_model,p.optics_lens,p.throw_ratio,p.shift_h,p.shift_v,(p.resolution_x,p.resolution_y))
    for text in issues:body.label(text=text,icon='ERROR')
    if not issues:body.label(text='VALID · known limits',icon='CHECKMARK')
    if lens and lens.h_limits is None:
        body.label(text='Shift limits unavailable',icon='INFO')
        body.label(text=f'H {p.shift_h:+.1f}% · V {p.shift_v:+.1f}% · limit unknown')

def overlay():
    from . import viewport_display
    if viewport_display._suppress:return
    context=bpy.context
    if not context.scene or not hasattr(context.scene,'ps_study') or not context.region_data:return
    if not context.space_data.overlay.show_overlays:return
    s=context.scene.ps_study;r=analysis_runtime.CACHE.get(context.scene.as_pointer())
    if not s.analysis_show or not r or analysis_runtime.stale(r,s.analysis_mode):return
    draw_cached(r,s.analysis_mode,context.region_data.perspective_matrix)

def overlay_legend():
    from . import viewport_display,analysis_images
    if viewport_display._suppress:return
    c=bpy.context
    if not c.scene or not hasattr(c.scene,'ps_study') or not c.region:return
    if not c.space_data.overlay.show_overlays:return
    s=c.scene.ps_study;r=analysis_runtime.CACHE.get(c.scene.as_pointer())
    if s.analysis_show and r and not analysis_runtime.stale(r,s.analysis_mode) and s.analysis_mode in r.get('_batches',{}):
        analysis_images.legend(r,s.analysis_mode,c.region.width,c.region.height)


def draw_cached(r,mode,matrix):
    import gpu
    # Batches built once per mode/result; no geometry or analysis work in draw.
    entry=r.get('_batches',{}).get(mode)
    if entry is None:return
    shader,batch=entry
    gpu.state.depth_test_set('LESS_EQUAL');gpu.state.depth_mask_set(False);gpu.state.program_point_size_set(True)
    try:
        shader.bind();shader.uniform_float('viewProjection',matrix);batch.draw(shader)
    finally:gpu.state.depth_test_set('NONE');gpu.state.depth_mask_set(True);gpu.state.program_point_size_set(False)

@persistent
def changed(scene,graph):
    for update in graph.updates:
        obj=update.id
        if not (update.is_updated_geometry or update.is_updated_transform):continue
        if isinstance(obj,bpy.types.Object):
            if obj.beam_observer.is_observer:analysis_runtime.invalidate('ACUITY');continue
            if obj.type not in analysis_runtime.scene_geometry.SURFACE_TYPES or obj.get('ps_helper') or obj.get('beam_screen_detail'):continue
            analysis_runtime.invalidate();return
        if isinstance(obj,bpy.types.Mesh):
            if any(o.data==obj and not o.get('ps_helper') and not o.get('beam_screen_detail') for o in scene.objects):
                analysis_runtime.invalidate();return

def register():
    global _handle,_legend_handle
    if not bpy.app.background:
        _handle=bpy.types.SpaceView3D.draw_handler_add(overlay,(),'WINDOW','POST_VIEW')
        _legend_handle=bpy.types.SpaceView3D.draw_handler_add(overlay_legend,(),'WINDOW','POST_PIXEL')
    bpy.app.handlers.depsgraph_update_post.append(changed)
def unregister():
    global _handle,_legend_handle
    if _handle:bpy.types.SpaceView3D.draw_handler_remove(_handle,'WINDOW');_handle=None
    if _legend_handle:bpy.types.SpaceView3D.draw_handler_remove(_legend_handle,'WINDOW');_legend_handle=None
    if changed in bpy.app.handlers.depsgraph_update_post:bpy.app.handlers.depsgraph_update_post.remove(changed)
    analysis_runtime.CACHE.clear()
CLASSES=(BEAM_OT_analyse,BEAM_OT_apply_optics,BEAM_OT_study_package)
