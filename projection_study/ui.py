"""Shared native Beam inspector: presentation only; operators own mutations."""
import bpy
import tomllib
from pathlib import Path
BEAM_VERSION = tomllib.loads((Path(__file__).parent / "blender_manifest.toml").read_text())["version"]
from . import runtime,ui_context
from .projector_object import selected
from .study_views import selected_view
MODULES=[('PROJECTOR','Projector','OUTLINER_OB_CAMERA'),('SCREEN','Screen','MESH_PLANE'),('GROUP','Blend','GROUP'),('VIEW','Views','CAMERA_DATA'),('EXPORT','Export','EXPORT')]


def section(layout,key,title,closed=False):
    header,body=layout.panel('beam_'+key,default_closed=closed);header.label(text=title)
    if body:body.use_property_decorate=False
    return body

def readout(layout,label,value):
    row=layout.row();row.label(text=label);r=row.row();r.alignment='RIGHT';r.label(text=value)

def length(value,units):return f'{value:,.2f} m' if units=='m' else f'{value*1000:,.0f} mm'

def status(layout,text,good=False,error=False):
    from . import ui_icons
    row=layout.row();row.alert=error;row.label(text=text,icon_value=ui_icons.icon('valid') if good else 0,icon='NONE' if good else ('ERROR' if error else 'INFO'))

def rail_visible(context):
    from .ui_workspace import is_beam
    return is_beam(context) and any(a.type=='VIEW_3D' and a.spaces.active.show_region_toolbar for a in context.screen.areas)

def navigation(layout,context,vertical=False):
    row=layout.column(align=True) if vertical else layout.grid_flow(row_major=True,columns=3,even_columns=True,align=True)
    compact=vertical and context.region.width<140
    for kind,title,icon in MODULES:
        op=row.operator('beam.inspector',text='' if compact else title,icon=icon,depress=context.scene.ps_study.inspector==kind);op.kind=kind

def actions(layout,context,vertical=False):
    if not vertical and rail_visible(context):return
    obj=ui_context.subject(context)
    if not obj:return
    row=layout.column(align=True) if vertical else layout.row(align=True)
    compact=vertical and context.region.width<140
    row.operator('beam.ui_action',text='' if compact else 'Frame',icon='VIEWZOOM').action='FRAME'
    if context.scene.ps_study.inspector in {'PROJECTOR','GROUP'}:row.operator('beam.ui_action',text='' if compact else 'Solo',icon='HIDE_OFF').action='SOLO'
    locked=any(obj.lock_location) or any(obj.lock_rotation)
    row.operator('beam.ui_action',text='' if compact else ('Unlock' if locked else 'Lock'),icon='LOCKED' if locked else 'UNLOCKED',depress=locked).action='LOCK'


def position_section(layout,context,obj,record,units):
    from . import blend_groups,transform_ui
    box=section(layout,'position_aim','Position and Aim')
    if not box:return
    transform_ui.draw_position(box,obj);transform_ui.draw_projector_rotation(box,obj)
    if any(obj.lock_location) or any(obj.lock_rotation):status(box,'Locked · use Unlock to move this projector')
    group=blend_groups.group_for(obj,context.scene)
    if group:
        status(box,f'Moves this projector only · member of {group.name}')
        box.operator('beam.select_group',text='Select Whole Group',icon='GROUP').group_uuid=group.uuid
    box.label(text='Aim At')
    row=box.row(align=True);row.operator('ps.aim',text='Object Centre').mode='OBJECT';row.operator('ps.aim',text='3D Cursor').mode='CURSOR'
    row=box.row(align=True);row.operator('beam.ui_action',text='Click Surface').action='AIM_CLICK';row.operator('beam.ui_action',text='Look Through').action='LOOK'
    box.label(text='Along Lens Axis')
    row=box.row(align=True);row.operator('ps.move',text='−1 m').distance=-1;row.operator('ps.move',text='+1 m').distance=1
    if record:readout(box,'Centre Ray',length(record['slant'],units) if record['hit'] else 'No hit')


def object_position_section(layout,obj):
    from . import transform_ui
    box=section(layout,'object_position','Position')
    if not box:return
    transform_ui.draw_position(box,obj);transform_ui.draw_rotation(box,obj)
    if any(obj.lock_location) or any(obj.lock_rotation):status(box,'Locked · use Unlock to move this')


def projector(layout,context):
    s=context.scene.ps_study;obj=selected(context);units=s.display_units
    row=layout.row(align=True);row.operator('ps.add',text='New Projector',icon='ADD')
    if obj:row.operator('ps.duplicate',text='Duplicate',icon='DUPLICATE')
    if not obj:
        layout.prop(s,'create_projector_body')
        status(layout,'No projector selected')
        return
    p=obj.ps;record=runtime.CACHE.get(obj.as_pointer());status(layout,'TARGET' if record and record['hit'] else 'No Target',bool(record and record['hit']))
    actions(layout,context)
    position_section(layout,context,obj,record,units)
    box=section(layout,'projection','Projection')
    if box:
        box.use_property_split=True
        row=box.row(align=True);row.use_property_split=False;row.prop(p,'resolution_x',text='X');row.prop(p,'resolution_y',text='Y')
        box.prop(p,'throw_ratio');row=box.row(align=True);row.use_property_split=False;row.prop(p,'shift_h',text='H Shift %');row.prop(p,'shift_v',text='V Shift %')
        box.prop(p,'output_mode',text='Output');box.prop(p,'colour',text='Study Colour')
        if p.output_mode=='IMAGE':box.template_ID(p,'image',open='ps.load_image')
    from .analysis_ui import optics
    optics(layout,p)
    draft=context.window_manager.beam_target
    editing=bool(draft.field and draft.projector==obj and draft.scene==context.scene)
    box=section(layout,'calculated','Calculated')
    if box:
        if record and record['hit']:
            m=record['metrics']
            entries=[('DISTANCE','Throw',length(m.distance,units)),('WIDTH','Width',length(m.width,units)),('HEIGHT','Height',length(m.height,units)),('RATIO','Ratio',f'{p.throw_ratio:.3f}'),('DENSITY','Density',f'{m.pixels_per_metre:,.0f} px/m'),('PIXEL_SIZE','Pixel Size',f'{m.pixel_size_m*1000:.2f} mm/px')]
            for field,title,value in entries:
                row=box.row(align=True);row.label(text=title)
                val=row.row();val.alignment='RIGHT';val.label(text=value)
                edit=row.row(align=True);edit.enabled=not ui_context.restriction(obj,record,field)
                edit.operator('beam.edit_target',text='',icon='GREASEPENCIL',depress=editing and draft.field==field).field=field
        else:box.prop(s,'preview_distance_display',text='Preview ('+units+')')
    reason=ui_context.restriction(obj,record,draft.field if editing else None)
    if reason and reason!='No Target':status(layout,reason)
    # Active drafts always expose their solver, even if the idle section was closed.
    box=layout.column() if editing else section(layout,'solver','Solver · '+{'LENS':'Lens','POSITION':'Position','AUTO':'Auto'}[p.solve_by],True)
    if box:
        if editing:box.label(text='Solver · '+dict(DISTANCE='Throw',WIDTH='Width',HEIGHT='Height',RATIO='Ratio',DENSITY='Density',PIXEL_SIZE='Pixel Size').get(draft.field,draft.field))
        box.prop(p,'solve_by',text='Solve By')
        row=box.row(align=True)
        for key,title in [('solve_lock_position','Position'),('solve_lock_lens','Lens'),('solve_lock_target','Target')]:row.prop(p,key,text=title,icon='LOCKED' if getattr(p,key) else 'UNLOCKED')
        if editing:
            row=box.row(align=True);row.prop(draft,'value',text=draft.units if draft.field in {'WIDTH','HEIGHT','DISTANCE','PIXEL_SIZE'} else 'Target')
            apply=row.row(align=True);apply.enabled=not reason;apply.operator('beam.apply_target',text='',icon='CHECKMARK')
            row.operator('beam.apply_target',text='',icon='X').cancel=True
            if draft.message:status(box,draft.message,error=True)
    box=section(layout,'projector_body','Projector Body',True)
    if box:
        row=box.row();row.enabled=obj.mode=='OBJECT';row.prop(p,'show_body')
        box.prop(s,'create_projector_body')
        box.label(text='Parent custom models to this projector.')
        box.label(text='Lens origin · −Z forward · +Y up')
        box.label(text='Child models do not block projection.')
    box=section(layout,'per_projector_display','This Projector · Annotations',True)
    if box:
        for a,b in [('show_identifier','show_projected_identifier'),('show_frustum','show_centre_ray'),('show_target_marker','show_grid')]:
            row=box.row(align=True);row.prop(p,a);row.prop(p,b)
        box.prop(p,'show_output',text='Projection Output')
    box=section(layout,'projector_advanced','Advanced',True)
    if box:
        for prop in ('stack','brightness','lumens','active','notes'):box.prop(p,prop)
        if record and record['hit']:
            readout(box,'DPI',f"{record['metrics'].dpi:.1f}");readout(box,'Illuminance',f"{record['metrics'].lux:,.0f} lux")


def views(layout,context):
    s=context.scene.ps_study;row=layout.row(align=True);row.operator('ps.create_view',text='New Study View',icon='ADD')
    if not s.views:status(layout,'No Study View');return
    layout.template_list('PS_UL_study_views','ps_views',s,'views',s,'view_index',rows=2)
    view=selected_view(context)
    if not view:return
    layout.prop(view,'name',text='Name')
    row=layout.row(align=True);row.operator('ps.view_study',text='View',icon='HIDE_OFF');row.operator('ps.view_study',text='Exit').action='EXIT'
    row=layout.row(align=True);row.operator('ps.view_study',text='Previous',icon='TRIA_LEFT').action='PREVIOUS';row.operator('ps.view_study',text='Next',icon='TRIA_RIGHT').action='NEXT'
    row=layout.row(align=True);row.prop(view,'resolution_x',text='Width');row.prop(view,'resolution_y',text='Height')
    layout.operator('ps.export_views',text='Export This View',icon='EXPORT')
    box=section(layout,'view_options','This View · Export Annotations',True)
    if box:
        from . import analysis_runtime
        result=analysis_runtime.CACHE.get(context.scene.as_pointer())
        row=box.row();row.enabled=bool(result and not result['stale']) or view.analysis_overlay!='NONE'
        row.prop(view,'analysis_overlay')
        for prop in ('include_overlays','include_labels','include_frustums','include_projected_identifiers','include_grids'):box.prop(view,prop)
    box=section(layout,'view_advanced','Camera / Editing',True)
    if box:box.prop(view,'camera');box.operator('ps.remove_view',text='Remove View',icon='REMOVE')


def exports(layout,context):
    layout.label(text='Projector Data')
    layout.operator('ps.export',text='Mapping Matter CSV',icon='EXPORT')
    layout.operator('beam.export_designer',text='Designer CSV',icon='EXPORT')
    layout.operator('ps.export_json',text='Beam JSON',icon='FILE_TEXT')
    status(layout,'Two explicit CSV formats · see export notes')
    layout.operator('beam.study_package',text='Study Package · JSON + HTML + Views',icon='EXPORT')
    box=section(layout,'image_exports','Images')
    if box:
        box.operator('ps.capture_current',text='Export Current View',icon='IMAGE_DATA')
        row=box.row();row.enabled=bool(context.scene.ps_study.views);row.operator('ps.export_views',text='Export All Study Views',icon='EXPORT').all_views=True
    from .screen_data import active
    screen=active(context,persistent=True)
    box=section(layout,'screen_export','Screen Geometry')
    if box:
        if screen:
            box.label(text=screen.beam_screen.identifier);box.prop(screen.beam_screen,'export_mode');box.prop(screen.beam_screen,'export_space')
            row=box.row(align=True)
            for fmt in ('OBJ','FBX'):row.operator('beam.screen_export',text=fmt,icon='EXPORT').format=fmt
        else:status(box,'No screen selected')


def reverse_problem(layout, context):
    """Shown above the module only when Reverse Mapping is on and has stopped working."""
    obj = ui_context.receiver(context)
    if not obj or not obj.beam_reverse.enabled:
        return
    warning = receiver_warning(context, obj)
    if warning:
        status(layout, 'Reverse Mapping · ' + warning, error=True)


def reverse_status(layout, context, obj, warning):
    """Coverage and any problem, directly above the button they affect."""
    p = obj.beam_reverse
    if p.source == 'ACTIVE':
        active = context.scene.ps_study.active_projector
        layout.label(text='Coverage: ' + (active.ps.identifier if active else 'No projector'))
    if warning:
        status(layout, warning)
    elif p.enabled:
        status(layout, p.status, True)


def receiver_warning(context,obj):
    from . import reverse_mapping
    p=obj.beam_reverse
    if bpy.app.background:return 'GPU viewport required'
    if not obj.data.uv_layers.active:return 'Receiver needs UVs'
    try:
        if not obj.material_slots:return 'Unsupported receiver material'
        for slot in obj.material_slots:reverse_mapping.surface_outputs(slot.material)
    except ValueError:return 'Unsupported receiver material'
    if not reverse_mapping.sources(context,p):return 'No Reverse Mapping source'
    if p.enabled and ('unavailable' in p.status.lower() or 'maximum' in p.status.lower()):return p.status
    return ''

def reverse(layout,context):
    from . import reverse_mapping
    obj=ui_context.receiver(context)
    if not obj:return
    selected_object=context.view_layer.objects.active
    if obj!=selected_object and not obj.beam_reverse.enabled:return
    p=obj.beam_reverse
    warning=receiver_warning(context,obj)
    box=section(layout,'reverse_mapping','Reverse Mapping',True)
    if box:
        box.prop(context.scene.ps_study,'reverse_receiver',text='Receiver');box.prop(p,'source');box.prop(p,'mode')
        if p.source=='SELECTED':box.prop(p,'projector')
        if p.source=='GROUP':
            g=next((g for g in context.scene.ps_study.blend_groups if g.uuid==p.group_uuid),None)
            box.menu('BEAM_MT_receiver_groups',text=g.name if g else 'Choose Blend Group')
        if p.mode=='DIM':box.prop(p,'dim')
        reverse_status(box,context,obj,warning)
        row=box.row();row.enabled=p.enabled or not warning
        row.operator('beam.receiver_action',text='Restore Materials' if p.enabled else 'Enable on Receiver').action='DISABLE' if p.enabled else 'ENABLE'


def draw_faults(layout):
    from . import faults
    lines=faults.summary()
    if not lines:return
    box=layout.box();box.alert=True
    box.label(text='Beam needs attention · details in the system console',icon='ERROR')
    for line in lines:box.label(text=line)


def draw(layout,context):
    draw_faults(layout)
    from . import presentation,ui_workspace
    s=context.scene.ps_study;layout.use_property_decorate=False
    if not ui_workspace.is_beam(context):layout.operator('beam.workspace',icon='WORKSPACE')
    area=next((a for a in context.screen.areas if a.type=='VIEW_3D'),None)
    row=layout.row(align=True);row.prop(s,'display_units',expand=True);row.operator('beam.ui_action',text='Presentation' if presentation.active(area) else 'Technical',icon='SHADING_SOLID',depress=presentation.active(area)).action='PRESENTATION'
    navigation(layout,context)
    if s.inspector!='EXPORT':
        current=context.view_layer.objects.active;active=ui_context.subject(context)
        if current!=active:
            row=layout.row();row.label(text='Selected: '+(current.name if current else '—'),icon='RESTRICT_SELECT_OFF')
        if current and current.get('ps_helper') and current.parent and current.parent.ps.is_projector:
            layout.operator('beam.select_projector',text='Select '+current.parent.ps.identifier,icon='RESTRICT_SELECT_OFF')
        row=layout.row(align=True)
        if s.inspector in {'PROJECTOR','SCREEN'}:row.prop(s,'active_projector' if s.inspector=='PROJECTOR' else 'active_screen',text='Pinned' if s.pin_context else 'Active')
        else:row.label(text=('Pinned: ' if s.pin_context else 'Active: ')+(active.name if active else '—'))
        row.prop(s,'pin_context',text='',icon='PINNED' if s.pin_context else 'UNPINNED',toggle=True)
        reverse_problem(layout,context)
    layout.separator(factor=.4)
    if s.inspector=='PROJECTOR':projector(layout,context)
    elif s.inspector=='SCREEN':
        from .screen_ui import draw_screen
        draw_screen(layout,context)
    elif s.inspector=='GROUP':
        from .blend_ui import draw_groups
        draw_groups(layout,context)
    elif s.inspector=='VIEW':views(layout,context)
    else:exports(layout,context)
    if s.inspector!='EXPORT':
        from .analysis_ui import draw as draw_analysis
        draw_analysis(layout,context)
        reverse(layout,context)
    box=section(layout,'render_projection','Projection Mode')
    if box:
        box.prop(s,'projection_mode',text='')
        if s.projection_mode=='CYCLES':
            if context.scene.render.engine!='CYCLES':box.label(text='Select Cycles in Render Properties.',icon='INFO')
            box.prop(s,'render_multiplier');box.prop(s,'render_efficacy')
            box.label(text='Use Rendered shading or F12.')
            box.label(text='Analysis still uses solid geometry.')
    box=section(layout,'display','Global · Viewport Display',True)
    if box:
        box.prop(s,'label_detail',text='Label Detail',expand=True)
        for a,b in [('show_frustums','show_centre_rays'),('show_labels','show_outputs')]:
            row=box.row(align=True);row.prop(s,a);row.prop(s,b)
        for prop in ('show_projected_identifiers','show_study_cameras','shadow_resolution'):box.prop(s,prop)
    box=section(layout,'metadata','Project / Workspace',True)
    if box:
        for prop in ('project_name','revision','venue','client','author'):box.prop(s,prop)
        box.operator('beam.workspace',icon='WORKSPACE');box.operator('beam.ui_action',text='Organise Beam Collections',icon='OUTLINER_COLLECTION').action='ORGANIZE'
        box.separator()
        box.operator('beam.apply_theme',text='Apply Beam Theme',icon='PREFERENCES')
        box.operator('beam.restore_theme',text='Restore Previous Theme',icon='LOOP_BACK')
        box.label(text=f'{BEAM_VERSION} Beta · Twisted Pixel')

class BEAM_UL_members(bpy.types.UIList):
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):
        if not item.projector:layout.label(text='Missing projector',icon='ERROR');return
        title=item.projector.ps.identifier+(' · Anchor' if item.projector.ps.uuid==data.anchor_uuid else '')
        layout.operator('beam.ui_member',text=title,icon='OUTLINER_OB_CAMERA',emboss=False).index=index

class PS_PT_main(bpy.types.Panel):
    bl_label='Beam';bl_idname='PS_PT_main';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Beam';bl_options={'HIDE_HEADER'}
    def draw(self,context):draw(self.layout,context)

class BEAM_PT_rail(bpy.types.Panel):
    bl_label='Beam';bl_idname='BEAM_PT_rail';bl_space_type='VIEW_3D';bl_region_type='TOOLS';bl_options={'HIDE_HEADER'};bl_order=-100
    @classmethod
    def poll(cls,context):
        from .ui_workspace import is_beam
        return is_beam(context)
    def draw(self,context):
        navigation(self.layout,context,True)
        self.layout.separator(factor=.5)
        actions(self.layout,context,True)
        self.layout.separator()

class BEAM_PT_workspace(bpy.types.Panel):
    bl_label='Beam';bl_idname='BEAM_PT_workspace';bl_space_type='PROPERTIES';bl_region_type='WINDOW';bl_context='scene';bl_order=-1000;bl_options={'HIDE_HEADER'}
    @classmethod
    def poll(cls,context):
        from .ui_workspace import is_beam
        return is_beam(context)
    def draw(self,context):draw(self.layout,context)

class BEAM_OT_inspector(bpy.types.Operator):
    bl_idname='beam.inspector';bl_label='Beam Module'
    kind:bpy.props.EnumProperty(items=[(k,t,t+' inspector') for k,t,i in MODULES])
    @classmethod
    def description(cls,context,properties):return next(t+' inspector' for k,t,i in MODULES if k==properties.kind)
    def execute(self,context):context.scene.ps_study.inspector=self.kind;return {'FINISHED'}

class BEAM_OT_select_projector(bpy.types.Operator):
    bl_idname='beam.select_projector';bl_label='Select Projector';bl_description="Select the projector this helper belongs to; helpers can't be moved themselves";bl_options={'UNDO'}
    def execute(self,context):
        helper=context.view_layer.objects.active
        if not helper or not helper.get('ps_helper') or not helper.parent or not helper.parent.ps.is_projector:return {'CANCELLED'}
        for item in context.selected_objects:item.select_set(False)
        projector=helper.parent
        projector.hide_set(False);projector.select_set(True);context.view_layer.objects.active=projector
        return {'FINISHED'}

class BEAM_OT_select_group(bpy.types.Operator):
    bl_idname='beam.select_group';bl_label='Select Whole Group';bl_description='Select the group controller, so moving it moves every member';bl_options={'UNDO'}
    group_uuid:bpy.props.StringProperty()
    def execute(self,context):
        s=context.scene.ps_study
        index=next((i for i,g in enumerate(s.blend_groups) if g.uuid==self.group_uuid and g.controller),None)
        if index is None:self.report({'WARNING'},'Group controller is missing');return {'CANCELLED'}
        controller=s.blend_groups[index].controller
        for item in context.selected_objects:item.select_set(False)
        controller.hide_set(False);controller.select_set(True);context.view_layer.objects.active=controller
        s.blend_group_index=index;s.inspector='GROUP'
        return {'FINISHED'}

CLASSES=(BEAM_UL_members,BEAM_OT_inspector,BEAM_OT_select_projector,BEAM_OT_select_group,PS_PT_main,BEAM_PT_workspace,BEAM_PT_rail)
