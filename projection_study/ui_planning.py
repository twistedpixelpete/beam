"""Compact planning dialog. The stable Auto Blend implementation remains authoritative."""
import bpy
from . import auto_layout
from .display_units import dimension

class BEAM_OT_plan_new(bpy.types.Operator):
    bl_idname='beam.plan_new';bl_label='New Auto Blend';bl_options={'REGISTER','UNDO'}
    bl_description='Create a new Blend Group and editable projectors; use Reflow Group to adjust an existing group'
    __annotations__=dict(auto_layout.BEAM_OT_auto_blend.__annotations__)
    pair_details:bpy.props.BoolProperty(name='Pair Details',default=False)
    def update_preview(self,context):
        try:
            self._result,*_=auto_layout.calculate(context,self);self._error=''
            from .blend_math import adjacent
            self._pairs=list(adjacent(self.layout_type,self._result['count'],self._result['columns']))
        except (ValueError,RuntimeError) as exc:self._result=None;self._error=str(exc);self._pairs=[]
    def invoke(self,context,event):
        self.use_template=bool(context.scene.ps_study.active_projector)
        self.update_preview(context)
        return auto_layout.BEAM_OT_auto_blend.invoke(self,context,event)
    def check(self,context):self.update_preview(context);return True
    def draw(self,context):
        from .ui import readout,status
        l=self.layout;l.use_property_split=True;l.use_property_decorate=False
        l.prop(self,'use_template');l.prop(self,'layout_type');l.prop(self,'auto_count')
        if self.auto_count:l.prop(self,'max_count')
        else:
            if self.layout_type=='ARRAY':
                row=l.row(align=True);row.prop(self,'columns');row.prop(self,'rows')
            else:l.prop(self,'count')
            l.prop(self,'fixed_distance')
        if self.auto_count or self.fixed_distance:l.prop(self,'distance')
        row=l.row(align=True);row.prop(self,'min_throw',text='Min Throw');row.prop(self,'max_throw',text='Max')
        l.prop(self,'input_mode')
        if self.layout_type!='VERTICAL':l.prop(self,'overlap_h',text='Horizontal')
        if self.layout_type!='HORIZONTAL':l.prop(self,'overlap_v',text='Vertical')
        l.separator();r=getattr(self,'_result',None)
        if not r:status(l,getattr(self,'_error','No preview'));return
        u=context.scene.ps_study.display_units
        status(l,'Valid · nominal fit',True);readout(l,'Projectors',str(r['count']));readout(l,'Coverage','100% nominal');readout(l,'Throw',dimension(r['distance'],u))
        for axis,title in [('h','Horizontal'),('v','Vertical')]:
            if (axis=='h' and r['columns']==1) or (axis=='v' and r['rows']==1):continue
            v=r['overlap_'+axis];readout(l,title,f"{v['pixels']:.0f} px · {dimension(v['metres'],u)}")
        l.prop(self,'pair_details',icon='TRIA_DOWN' if self.pair_details else 'TRIA_RIGHT',emboss=False)
        if self.pair_details:
            for a,b,axis in self._pairs:
                v=r['overlap_h' if axis=='H' else 'overlap_v'];readout(l,f'Slot {a+1} ↔ {b+1}',f"{v['pixels']:.0f} px · {v['percent']:.1f}%")
    def execute(self,context):return auto_layout.BEAM_OT_auto_blend.execute(self,context)

class BEAM_OT_reflow(bpy.types.Operator):
    bl_idname='beam.reflow';bl_label='Reflow Group';bl_options={'UNDO'}
    bl_description='Adjust the current group layout; keep its projectors and identity'
    def execute(self,context):return bpy.ops.beam.group_action(action='APPLY')

CLASSES=(BEAM_OT_plan_new,BEAM_OT_reflow)
