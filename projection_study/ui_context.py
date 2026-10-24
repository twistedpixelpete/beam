"""UI-only drafts and cached summaries. Panel drawing never runs a solver."""
import bpy
from . import runtime
_summaries={}


def receiver(context):
    obj=context.scene.ps_study.reverse_receiver
    return obj if obj and obj.name in context.scene.objects and obj.type=='MESH' and not obj.ps.is_projector else None


def subject(context):
    from . import study_data,screen_data,blend_groups,study_views
    kind=context.scene.ps_study.inspector
    if kind=='PROJECTOR':return study_data.active(context)
    if kind=='SCREEN':return screen_data.active(context,persistent=True)
    if kind=='GROUP':
        g=blend_groups.active_group(context);return g.controller if g else None
    if kind=='VIEW':
        v=study_views.selected_view(context);return v.camera if v else None
    return None


def restriction(obj,record,field=None):
    if not obj:return 'No projector'
    if not record or not record['hit']:return 'No Target'
    if not runtime.rigid(obj):return 'Scale must be 1'
    if obj.constraints:return 'Projector constraints enabled'
    p=obj.ps;mode=p.solve_by
    position=mode=='POSITION' or mode=='AUTO' and (field=='DISTANCE' or p.solve_lock_lens)
    if field=='DISTANCE' and mode=='LENS':return 'Distance needs Position or Auto'
    if field=='RATIO':
        if p.solve_lock_lens:return 'Throw Ratio Locked'
        if mode=='POSITION':return 'Ratio needs Lens or Auto'
        return ''
    if position:
        if p.solve_lock_position or any(obj.lock_location):return 'Position Locked'
        if abs(p.shift_h)>1e-6 or abs(p.shift_v)>1e-6:return 'Lens Shift prevents Position Solve'
    elif p.solve_lock_lens:return 'Throw Ratio Locked'
    return ''


def summary(context,group):return _summaries.get((context.scene.as_pointer(),group.uuid),{}).get('value',{})

def update_summary(context):
    from . import blend_groups,layout_coverage
    g=blend_groups.active_group(context)
    if not g:return
    key=(context.scene.as_pointer(),g.uuid)
    # Runtime record identities change when engineering inputs change. Screen
    # transforms/mesh edits are also represented by the shared coverage cache.
    coverage=layout_coverage.report(g,context) if g.layout_screen else None
    stamp=(id(coverage),g.anchor_uuid,g.input_mode,g.overlap_h,g.overlap_v,g.layout,g.columns,
           tuple((m.projector_uuid,id(runtime.CACHE.get(m.projector.as_pointer()))) if m.projector else None for m in g.members))
    if _summaries.get(key,{}).get('stamp')==stamp:return
    if len(_summaries)>64:_summaries.clear()
    pairs=coverage['pairs'] if coverage else blend_groups.pair_data(g,context)
    _summaries[key]=dict(stamp=stamp,value=dict(coverage=coverage,pairs=pairs))

class BeamTargetDraft(bpy.types.PropertyGroup):
    field:bpy.props.StringProperty()
    projector:bpy.props.PointerProperty(type=bpy.types.Object)
    scene:bpy.props.PointerProperty(type=bpy.types.Scene)
    value:bpy.props.FloatProperty(name='Target',min=.000001,precision=4)
    factor:bpy.props.FloatProperty(default=1)
    units:bpy.props.StringProperty()
    message:bpy.props.StringProperty()

class BEAM_OT_edit_target(bpy.types.Operator):
    bl_idname='beam.edit_target';bl_label='Edit Calculated Target';bl_description='Stage a target here; Apply solves it with native Undo support'
    field:bpy.props.StringProperty()
    @classmethod
    def description(cls,context,properties):
        from .study_data import active
        obj=active(context);record=runtime.CACHE.get(obj.as_pointer()) if obj else None
        return restriction(obj,record,properties.field) or 'Stage this target inline; Apply solves it and Cancel discards the draft'
    def execute(self,context):
        from .study_data import active
        from .inverse_solver import measurement
        obj=active(context);record=runtime.CACHE.get(obj.as_pointer()) if obj else None
        reason=restriction(obj,record,self.field)
        if reason:self.report({'WARNING'},reason);return {'CANCELLED'}
        d=context.window_manager.beam_target;d.projector=obj;d.scene=context.scene;d.field=self.field
        d.factor=1000 if self.field=='PIXEL_SIZE' or self.field in {'WIDTH','HEIGHT','DISTANCE'} and context.scene.ps_study.display_units=='mm' else 1
        d.units='mm' if self.field=='PIXEL_SIZE' else context.scene.ps_study.display_units;d.value=measurement(record,self.field,obj.ps)*d.factor;d.message=''
        return {'FINISHED'}

class BEAM_OT_apply_target(bpy.types.Operator):
    bl_idname='beam.apply_target';bl_label='Apply Target';bl_options={'UNDO'}
    cancel:bpy.props.BoolProperty(default=False)
    def execute(self,context):
        from .inverse_solver import solve
        from .study_data import active
        d=context.window_manager.beam_target
        if self.cancel:d.field='';d.message='';return {'FINISHED'}
        if d.scene!=context.scene or d.projector!=active(context):
            self.report({'WARNING'},'Target context changed; edit the active projector value again');return {'CANCELLED'}
        try:solve(context,d.projector,d.field,d.value/d.factor)
        except (ValueError,RuntimeError) as exc:d.message=str(exc);self.report({'WARNING'},str(exc));return {'CANCELLED'}
        d.field='';d.message='';return {'FINISHED'}

@bpy.app.handlers.persistent
def clear(*args):
    _summaries.clear()
    for wm in bpy.data.window_managers:
        if hasattr(wm,'beam_target'):wm.beam_target.field='';wm.beam_target.message=''

CLASSES=(BeamTargetDraft,BEAM_OT_edit_target,BEAM_OT_apply_target)
