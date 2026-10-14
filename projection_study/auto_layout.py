"""Flat-screen layouts produce ordinary projectors and ordinary blend groups."""
import math,textwrap
import bpy
from mathutils import Vector,Matrix
from . import planning_math,screen_objects,projector_object,runtime,blend_groups
from .projection_math import image_point
from .display_units import dimension


def screen(context):
    obj=context.view_layer.objects.active
    if obj and obj.beam_screen.is_screen:return obj
    obj=context.scene.ps_study.active_screen
    return obj if obj and obj.name in context.scene.objects and obj.beam_screen.is_screen else None


def screen_frame(context,obj):
    if not obj or obj.beam_screen.screen_type!='FLAT':raise ValueError('Select a flat rectangular Beam Screen')
    if obj.modifiers:raise ValueError('Auto Blend needs a flat screen without modifiers')
    if not runtime.rigid(obj):raise ValueError('Auto Blend needs screen scale 1 and no shear')
    if obj.beam_screen.built_signature!=screen_objects.signature(obj.beam_screen):raise ValueError('Update Screen before Auto Blend')
    unit=context.scene.unit_settings.scale_length
    if abs(unit-obj.beam_screen.unit_scale)>1e-8:raise ValueError('Scene units changed: Update Screen first')
    points=[v.co for v in obj.data.vertices]
    if not points:raise ValueError('Screen has no geometry; Update Screen first')
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    if min(high.x-low.x,high.z-low.z)<=1e-6:raise ValueError('Screen needs positive width and height')
    if high.y-low.y>1e-5:raise ValueError('Screen is no longer planar')
    return (high.x-low.x)*unit,(high.z-low.z)*unit,obj.matrix_world@((low+high)/2),obj.matrix_world.to_quaternion().to_matrix()


def calculate(context,op):
    target=screen(context);width,height,centre,rotation=screen_frame(context,target)
    template=context.scene.ps_study.active_projector if op.use_template else None
    if template and template.name not in context.scene.objects:template=None
    p=template.ps if template else None
    result=planning_math.plan(width,height,p.resolution_x if p else 1920,p.resolution_y if p else 1080,
        p.throw_ratio if p else 1,op.layout_type,op.count,op.columns,op.rows,op.auto_count,
        op.overlap_h,op.overlap_v,op.input_mode,op.distance,op.fixed_distance,op.max_count,op.min_throw,op.max_throw)
    return result,target,template,centre,rotation


def create(context,op):
    context.view_layer.update()
    result,target,template,centre,rotation=calculate(context,op)
    unit=context.scene.unit_settings.scale_length;made=[];group=None
    data_before={name:set(getattr(bpy.data,name)) for name in ('meshes','cameras','materials','images')}
    previous=set(bpy.data.objects);previous_groups={g.uuid for g in context.scene.ps_study.blend_groups}
    selected=list(context.selected_objects);active=context.view_layer.objects.active
    old_active=context.scene.ps_study.active_projector
    try:
        r=rotation@Matrix.Rotation(math.pi/2,3,'X')
        spacing_x=result['width']-result['overlap_h']['metres'];spacing_y=result['height']-result['overlap_v']['metres']
        for row in range(result['rows']):
            for col in range(result['columns']):
                obj=projector_object.create(context,template);p=obj.ps
                point=centre+rotation@Vector(((col-(result['columns']-1)/2)*spacing_x/unit,0,((result['rows']-1)/2-row)*spacing_y/unit))
                lens=point-r@Vector(image_point(.5,.5,result['distance']/unit,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v))
                matrix=r.to_4x4();matrix.translation=lens;obj.matrix_world=matrix;made.append(obj)
        context.view_layer.update();runtime.refresh(True)
        for obj in made:
            hit=runtime.CACHE[obj.as_pointer()]['hit']
            # First-hit obstruction checks are conservative at each centre. Dense
            # partial occlusions remain a viewport inspection, not a coverage claim.
            if not hit or hit[3]!=target.name:raise ValueError('A projector centre misses the screen or is blocked; adjust overlap, count or throw')
        group=blend_groups.create(context,made,op.layout_type,result['columns'],result['rows'],result['overlap_h']['percent'],'PERCENT',preserve=True)
        was_updating=blend_groups._updating;blend_groups._updating=True
        try:group.overlap_v=result['overlap_v']['percent'];group.layout_screen=target
        finally:blend_groups._updating=was_updating
        from .group_lifecycle import snapshot
        snapshot(group,context)
        for obj in context.selected_objects:obj.select_set(False)
        group.controller.select_set(True);context.view_layer.objects.active=group.controller
        context.scene.ps_study.inspector='GROUP'
        runtime.invalidate();runtime.refresh(True)
    except Exception:
        for i in reversed(range(len(context.scene.ps_study.blend_groups))):
            if context.scene.ps_study.blend_groups[i].uuid not in previous_groups:context.scene.ps_study.blend_groups.remove(i)
        for obj in list(bpy.data.objects):
            if obj not in previous:bpy.data.objects.remove(obj,do_unlink=True)
        for name,old in data_before.items():
            data=getattr(bpy.data,name)
            for item in set(data)-old:
                if item.users==0:data.remove(item)
        context.scene.ps_study.active_projector=old_active
        for obj in selected:
            if obj.name in context.scene.objects:obj.select_set(True)
        context.view_layer.objects.active=active
        runtime.reset();raise
    return group,result


class BEAM_OT_auto_blend(bpy.types.Operator):
    bl_idname='beam.auto_blend';bl_label='Create Layout';bl_description='Preview a flat-screen arrangement, then create editable Beam projectors and a group';bl_options={'REGISTER','UNDO'}
    layout_type:bpy.props.EnumProperty(name='Layout',items=[(x,x.title(),'') for x in ('HORIZONTAL','VERTICAL','ARRAY')])
    use_template:bpy.props.BoolProperty(name='Use Active Projector Template',default=True)
    auto_count:bpy.props.BoolProperty(name='Auto Count',default=False)
    count:bpy.props.IntProperty(name='Projectors',default=3,min=1,max=32)
    columns:bpy.props.IntProperty(name='Columns',default=2,min=1,max=32)
    rows:bpy.props.IntProperty(name='Rows',default=2,min=1,max=32)
    max_count:bpy.props.IntProperty(name='Maximum Projectors',default=32,min=1,max=32)
    input_mode:bpy.props.EnumProperty(name='Overlap Units',items=[('PIXELS','Pixels',''),('PERCENT','Percent',''),('METRES','Metres','')])
    overlap_h:bpy.props.FloatProperty(name='Horizontal Overlap',default=200,min=0)
    overlap_v:bpy.props.FloatProperty(name='Vertical Overlap',default=200,min=0)
    fixed_distance:bpy.props.BoolProperty(name='Lock Throw Distance',default=False)
    distance:bpy.props.FloatProperty(name='Throw (m)',default=10,min=.01)
    min_throw:bpy.props.FloatProperty(name='Minimum Throw (m)',default=.1,min=.01)
    max_throw:bpy.props.FloatProperty(name='Maximum Throw (m)',default=100,min=.01)
    def invoke(self,context,event):
        try:screen_frame(context,screen(context))
        except ValueError as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self,width=440,confirm_text='Create Layout')
    def check(self,context):return True
    def draw(self,context):
        layout=self.layout;layout.use_property_split=True
        layout.label(text='Auto Blend · Flat Screen')
        layout.prop(self,'use_template');layout.prop(self,'layout_type');layout.prop(self,'auto_count')
        if not self.auto_count:
            if self.layout_type=='ARRAY':layout.prop(self,'columns');layout.prop(self,'rows')
            else:layout.prop(self,'count')
            layout.prop(self,'fixed_distance')
        else:layout.prop(self,'max_count')
        if self.auto_count or self.fixed_distance:layout.prop(self,'distance')
        layout.prop(self,'min_throw');layout.prop(self,'max_throw');layout.prop(self,'input_mode')
        if self.layout_type!='VERTICAL':layout.prop(self,'overlap_h')
        if self.layout_type!='HORIZONTAL':layout.prop(self,'overlap_v')
        box=layout.box();box.label(text='Auto Blend Result · recalculates as you edit')
        try:
            result,*_=calculate(context,self);units=context.scene.ps_study.display_units
            box.label(text=f"{result['count']} projectors · {result['columns']} × {result['rows']} · Valid nominal fit",icon='CHECKMARK')
            box.label(text=f"Coverage 100% nominal · Throw {dimension(result['distance'],units)}")
            box.label(text=f"Image {dimension(result['width'],units)} × {dimension(result['height'],units)}")
            box.label(text=f"Density {result['density']:.1f} px/m")
            for axis in ('h','v'):
                if (axis=='h' and result['columns']==1) or (axis=='v' and result['rows']==1):continue
                v=result['overlap_'+axis];box.label(text=('Horizontal' if axis=='h' else 'Vertical')+' · Requested = nominal actual')
                box.label(text=f"{v['pixels']:.1f} px · {dimension(v['metres'],units)} · {v['percent']:.1f}%")
            from .blend_math import adjacent
            for a,b,axis in adjacent(self.layout_type,result['count'],result['columns']):
                v=result['overlap_h' if axis=='H' else 'overlap_v']
                box.label(text=f"Slot {a+1} ↔ {b+1} ({axis}): {v['pixels']:.1f} px · {dimension(v['metres'],units)} · {v['percent']:.1f}%")
            box.label(text='Centre hits checked on creation; inspect partial obstructions.')
        except ValueError as exc:
            for line in textwrap.wrap(str(exc),58):box.label(text=line,icon='ERROR')
    def execute(self,context):
        try:group,result=create(context,self)
        except (ValueError,RuntimeError) as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        self.report({'INFO'},f"{group.name}: {result['count']} editable projectors created");return {'FINISHED'}

CLASSES=(BEAM_OT_auto_blend,)
