"""Transactional operator adapter for the pure inverse solver."""
import bpy,math,textwrap
from . import runtime,planning_math
from .projector_object import selected

FIELDS=[('DISTANCE','Throw Distance',''),('WIDTH','Image Width',''),('HEIGHT','Image Height',''),
        ('RATIO','Throw Ratio',''),('DENSITY','Pixel Density',''),('PIXEL_SIZE','Pixel Size','')]


def measurement(record,field,p):
    m=record['metrics']
    return {'DISTANCE':m.distance,'WIDTH':m.width,'HEIGHT':m.height,'RATIO':p.throw_ratio,
            'DENSITY':m.pixels_per_metre,'PIXEL_SIZE':m.pixel_size_m}[field]


def solve(context,obj,field,value):
    if not obj or not obj.ps.is_projector:raise ValueError('Choose a Beam projector')
    context.view_layer.update();runtime.refresh()
    record=runtime.CACHE.get(obj.as_pointer());p=obj.ps
    if not record:raise ValueError('Projector is unavailable in the active scene')
    if not record['hit']:raise ValueError('No Target: aim at a visible surface before solving')
    if not runtime.rigid(obj):raise ValueError('Restore projector and parent scale to 1 before solving')
    if obj.constraints:raise ValueError('Disable projector constraints before solving')
    poslock=p.solve_lock_position or any(obj.lock_location)
    d,tr,mode=planning_math.inverse(field,value,p.solve_by,record['metrics'].distance,p.throw_ratio,
                                   p.resolution_x,p.resolution_y,poslock,p.solve_lock_lens)
    if mode=='POSITION' and (abs(p.shift_h)>1e-6 or abs(p.shift_v)>1e-6):
        raise ValueError('Position solving needs zero lens shift to preserve both optical-axis motion and target aim')
    from .optics_validation import require
    require(p,tr)
    world=obj.matrix_world.copy();ratio=p.throw_ratio;target=record['hit'][0].copy();target_name=record['hit'][3]
    unit=context.scene.unit_settings.scale_length
    try:
        if mode=='POSITION':
            # Zero shift makes this target direction parallel to the optical axis.
            # Preserve the exact centre target and orientation.
            ray=(target-record['origin'])/(record['metrics'].distance/unit)
            matrix=world.copy();matrix.translation=target-ray*(d/unit);obj.matrix_world=matrix
        else:p.throw_ratio=tr
        for iteration in range(16):
            context.view_layer.update();runtime.invalidate(obj);runtime.refresh()
            current=runtime.CACHE[obj.as_pointer()]
            if not current['hit']:raise ValueError('Requested result loses the centre target; no changes applied')
            if (mode=='POSITION' or p.solve_lock_target) and (current['hit'][3]!=target_name or (current['hit'][0]-target).length*unit>.002):
                raise ValueError('The target is blocked or would move with these settings')
            actual=measurement(current,field,p)
            if math.isclose(actual,value,rel_tol=1e-4,abs_tol=1e-7):break
            if mode!='LENS' or field in {'RATIO','DISTANCE'}:raise ValueError('Cannot achieve the requested value with current constraints')
            width=planning_math.desired_width(field,value,p.resolution_x,p.resolution_y)
            tr=current['metrics'].distance/width
            if not .05<=tr<=100:raise ValueError('Required throw ratio is outside 0.05–100')
            require(p,tr)
            p.throw_ratio=tr
        else:raise ValueError('Cannot converge on this surface; try Position or a simpler target')
    except Exception:
        obj.matrix_world=world;p.throw_ratio=ratio;context.view_layer.update();runtime.invalidate(obj);runtime.refresh()
        raise
    return f"Solved by {'lens' if mode=='LENS' else 'position'} · throw {current['metrics'].distance:.3f} m · ratio {p.throw_ratio:.4f}"


class BEAM_OT_solve(bpy.types.Operator):
    bl_idname='beam.solve';bl_label='Set Projection Target';bl_options={'REGISTER','UNDO'}
    field:bpy.props.EnumProperty(items=FIELDS,default='WIDTH')
    value:bpy.props.FloatProperty(name='Desired Value',default=6,min=.000001,precision=4)
    def invoke(self,context,event):
        runtime.refresh();obj=selected(context)
        r=runtime.CACHE.get(obj.as_pointer()) if obj else None
        if not r or not r['hit']:self.report({'WARNING'},'No Target: aim at a surface first');return {'CANCELLED'}
        self._projector=obj;self._world=obj.matrix_world.copy();self._ratio=obj.ps.throw_ratio;self._mode=obj.ps.solve_by;self._factor=self.factor(context);self._last=None;self._feedback=''
        self.value=measurement(r,self.field,obj.ps)*self.factor(context)
        self._previewing=True
        return context.window_manager.invoke_props_dialog(self,width=360,confirm_text='Apply Target')
    def factor(self,context):
        if getattr(self,'_previewing',False):return self._factor
        return 1000 if self.field in {'DISTANCE','WIDTH','HEIGHT','PIXEL_SIZE'} and context.scene.ps_study.display_units=='mm' else 1
    def draw(self,context):
        obj=getattr(self,'_projector',None) or selected(context);layout=self.layout
        if not obj:layout.label(text='Projector unavailable');return
        layout.prop(obj.ps,'solve_by',text='Solve By')
        units=context.scene.ps_study.display_units if self.field in {'DISTANCE','WIDTH','HEIGHT','PIXEL_SIZE'} else 'px/m' if self.field=='DENSITY' else 'ratio'
        layout.prop(self,'value',text=dict((a,b) for a,b,c in FIELDS)[self.field]+' ('+units+')')
        for line in textwrap.wrap(getattr(self,'_feedback','') or 'Edit to preview · Cancel restores the original state',48):layout.label(text=line)
    def restore_preview(self,context):
        obj=getattr(self,'_projector',None)
        if obj and obj.name in context.scene.objects:
            obj.matrix_world=self._world;obj.ps.throw_ratio=self._ratio
            context.view_layer.update();runtime.invalidate(obj);runtime.refresh()
    def check(self,context):
        if not getattr(self,'_previewing',False):return False
        key=(self.value,self._projector.ps.solve_by)
        if key==self._last:return False
        self._last=key;self.restore_preview(context)
        try:self._feedback=solve(context,self._projector,self.field,self.value/self.factor(context))
        except (ValueError,RuntimeError) as exc:self._feedback=str(exc)
        return True
    def cancel(self,context):
        self.restore_preview(context)
        obj=getattr(self,'_projector',None)
        if obj and obj.name in context.scene.objects:obj.ps.solve_by=self._mode
    def execute(self,context):
        if getattr(self,'_previewing',False):self.restore_preview(context)
        try:message=solve(context,getattr(self,'_projector',None) or selected(context),self.field,self.value/self.factor(context))
        except (ValueError,RuntimeError) as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        self.report({'INFO'},message);return {'FINISHED'}

CLASSES=(BEAM_OT_solve,)
