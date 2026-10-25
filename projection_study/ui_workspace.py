"""Optional native workspace and viewport-context bridges. No theme overrides."""
import bpy
from . import ui_context
from .study_views import viewport
_seen_ui={}


def is_beam(context):return bool(context.workspace and context.workspace.get('beam_workspace'))

class BEAM_OT_workspace(bpy.types.Operator):
    bl_options={'REGISTER'}
    bl_idname='beam.workspace';bl_label='Open Beam Workspace';bl_description='Duplicate this native layout as Beam; keep the original workspace and scene intact'
    def execute(self,context):
        existing=next((w for w in bpy.data.workspaces if w.get('beam_workspace')),None)
        if existing:
            context.window.workspace=existing
            for screen in existing.screens:
                for area in screen.areas:
                    if area.type=='PROPERTIES':
                        area.spaces.active.context='SCENE'
                        if hasattr(area.spaces.active,'outliner_sync'):area.spaces.active.outliner_sync='NEVER'
            return {'FINISHED'}
        if not {'VIEW_3D','OUTLINER','PROPERTIES'}<={a.type for a in context.screen.areas}:
            self.report({'WARNING'},'Open Layout with a 3D View, Outliner and Properties, then create Beam');return {'CANCELLED'}
        before=set(bpy.data.workspaces);bpy.ops.workspace.duplicate()
        created=next(iter(set(bpy.data.workspaces)-before),None)
        if not created:self.report({'WARNING'},'Workspace could not be duplicated');return {'CANCELLED'}
        created.name='Beam';created['beam_workspace']=True
        for screen in created.screens:
            for area in screen.areas:
                if area.type=='PROPERTIES':
                    area.spaces.active.context='SCENE'
                    if hasattr(area.spaces.active,'outliner_sync'):area.spaces.active.outliner_sync='NEVER'
                elif area.type=='VIEW_3D':
                    area.spaces.active.show_region_ui=False;area.spaces.active.show_region_toolbar=True
        return {'FINISHED'}

class BEAM_OT_ui_action(bpy.types.Operator):
    bl_idname='beam.ui_action';bl_label='Beam Action';bl_options={'UNDO'}
    action:bpy.props.EnumProperty(items=[(k,k.replace('_',' ').title(),'') for k in ('FRAME','LOCK','SOLO','PRESENTATION','LOOK','AIM_CLICK','ORGANIZE')])
    @classmethod
    def description(cls,context,properties):
        return {'FRAME':'Frame the active Beam object without changing selection','SOLO':'Isolate this projector or group’s projection output','LOCK':'Toggle native location and rotation locks','PRESENTATION':'Toggle reduced viewport guides; restore Technical settings on exit','ORGANIZE':'Organise Beam objects into native collections; keep venue geometry'}.get(properties.action,'Operate on the active Beam object')
    def execute(self,context):
        from . import ui_collections
        if self.action=='ORGANIZE':ui_collections.organize(context.scene);return {'FINISHED'}
        obj=ui_context.subject(context)
        if self.action=='LOCK':
            if not obj:self.report({'WARNING'},'No active Beam object');return {'CANCELLED'}
            locked=any(obj.lock_location) or any(obj.lock_rotation);obj.lock_location=(not locked,)*3;obj.lock_rotation=(not locked,)*3
            obj.lock_rotation_w=not locked;obj.lock_rotations_4d=not locked
            return {'FINISHED'}
        try:area,region=viewport(context)
        except ValueError as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        with context.temp_override(area=area,region=region):
            if self.action=='PRESENTATION':return bpy.ops.beam.presentation()
            if self.action=='LOOK':bpy.ops.ps.look('INVOKE_DEFAULT');return {'FINISHED'}
            if self.action=='AIM_CLICK':bpy.ops.ps.aim('INVOKE_DEFAULT',mode='CLICK');return {'FINISHED'}
            if self.action=='SOLO':
                if context.scene.ps_study.inspector=='GROUP':return bpy.ops.beam.group_action(action='SOLO')
                return bpy.ops.ps.isolate()
            if not obj:self.report({'WARNING'},'No active Beam object');return {'CANCELLED'}
            if context.mode!='OBJECT' or obj.name not in context.view_layer.objects or not obj.visible_get():
                self.report({'WARNING'},'Frame needs a visible active object in Object Mode');return {'CANCELLED'}
            selected=list(context.selected_objects);active=context.view_layer.objects.active
            try:
                for item in selected:item.select_set(False)
                obj.select_set(True);context.view_layer.objects.active=obj
                bpy.ops.view3d.view_selected(use_all_regions=False)
            finally:
                obj.select_set(False)
                for item in selected:item.select_set(True)
                context.view_layer.objects.active=active
        return {'FINISHED'}

class BEAM_OT_receiver(bpy.types.Operator):
    bl_idname='beam.receiver_action';bl_label='Reverse Mapping';bl_options={'UNDO'}
    action:bpy.props.EnumProperty(items=[('ENABLE','Enable',''),('DISABLE','Restore',''),('GROUP','Choose Group','')])
    group_uuid:bpy.props.StringProperty()
    def execute(self,context):
        from . import reverse_mapping
        obj=ui_context.receiver(context)
        if not obj:self.report({'WARNING'},'Select a receiving mesh');return {'CANCELLED'}
        try:
            if self.action=='GROUP':
                if not any(g.uuid==self.group_uuid for g in context.scene.ps_study.blend_groups):raise ValueError('Group is unavailable')
                obj.beam_reverse.group_uuid=self.group_uuid
            elif self.action=='DISABLE':reverse_mapping.disable(obj)
            else:
                if bpy.app.background:raise ValueError('GPU viewport required')
                area,region=viewport(context)
                with context.temp_override(area=area,region=region):reverse_mapping.enable(context,obj)
        except (ValueError,RuntimeError) as exc:self.report({'WARNING'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class BEAM_MT_receiver_groups(bpy.types.Menu):
    bl_label='Blend Group'
    def draw(self,context):
        for g in context.scene.ps_study.blend_groups:
            op=self.layout.operator('beam.receiver_action',text=g.name);op.action='GROUP';op.group_uuid=g.uuid


class BEAM_OT_ui_member(bpy.types.Operator):
    bl_idname='beam.ui_member';bl_label='Select Blend Member';bl_options={'UNDO'}
    index:bpy.props.IntProperty()
    def execute(self,context):
        from .study_data import sync_selection
        try:result=bpy.ops.beam.select_member(index=self.index)
        except RuntimeError:self.report({'WARNING'},'Member is unavailable in this view layer');return {'CANCELLED'}
        if result=={'FINISHED'}:
            sync_selection(context);context.scene.ps_study.inspector='GROUP';context.scene.ps_study.ui_member_index=self.index
        return result

class BEAM_OT_new_auto(bpy.types.Operator):
    bl_idname='beam.ui_new_auto';bl_label='New Auto Blend';bl_description='Create another layout on this group’s screen; the existing group is retained'
    def execute(self,context):
        from .blend_groups import active_group
        group=active_group(context)
        if not group or not group.layout_screen:self.report({'WARNING'},'No layout screen');return {'CANCELLED'}
        context.scene.ps_study.active_screen=group.layout_screen
        bpy.ops.beam.plan_new('INVOKE_DEFAULT');return {'FINISHED'}

class BEAM_OT_draft_preset(bpy.types.Operator):
    bl_idname='beam.draft_preset';bl_label='Apply Cabinet Preset';bl_options={'UNDO'}
    def execute(self,context):
        from .screen_operators import PRESETS
        p=context.scene.beam_screen_draft
        if p.preset not in PRESETS:self.report({'WARNING'},'Choose a cabinet preset');return {'CANCELLED'}
        for key,value in PRESETS[p.preset].items():setattr(p,key,value)
        return {'FINISHED'}


def tick():
    if not hasattr(bpy.types.Scene,'ps_study'):return None
    # Selection and summaries update outside panel drawing, on a modest UI cadence.
    from .study_data import sync_selection
    from . import runtime
    live={w.as_pointer() for w in bpy.context.window_manager.windows}
    for key in set(_seen_ui)-live:_seen_ui.pop(key,None)
    for window in bpy.context.window_manager.windows:
        with bpy.context.temp_override(window=window):
            sync_selection(bpy.context)
            if bpy.context.scene.ps_study.inspector=='GROUP':ui_context.update_summary(bpy.context)
            s=bpy.context.scene.ps_study;obj=bpy.context.view_layer.objects.active;receiver=ui_context.receiver(bpy.context)
            fingerprint=(bpy.context.scene.as_pointer(),s.inspector,s.pin_context,obj.as_pointer() if obj else None,
                         s.active_projector.as_pointer() if s.active_projector else None,s.active_screen.as_pointer() if s.active_screen else None,
                         s.blend_group_index,s.view_index,tuple((key,id(value)) for key,value in runtime.CACHE.items()),
                         receiver.beam_reverse.status if receiver else '',receiver.as_pointer() if receiver else None,
                         bpy.context.window_manager.beam_target.field,
                         bpy.context.window_manager.beam_target.value,bpy.context.window_manager.beam_target.message)
            if _seen_ui.get(window.as_pointer())!=fingerprint:
                _seen_ui[window.as_pointer()]=fingerprint
                for area in window.screen.areas:
                    if area.type in {'VIEW_3D','PROPERTIES'}:area.tag_redraw()
    return .25

def workspace_menu(self,context):
    # Normal Blender Menu Search indexes menu entries, not every registered operator.
    self.layout.separator()
    self.layout.operator('beam.workspace')

def register():
    bpy.types.VIEW3D_MT_view.append(workspace_menu)
    bpy.types.WindowManager.beam_target=bpy.props.PointerProperty(type=ui_context.BeamTargetDraft)
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if ui_context.clear not in handlers:handlers.append(ui_context.clear)
    if not bpy.app.timers.is_registered(tick):bpy.app.timers.register(tick,persistent=True)

def unregister():
    bpy.types.VIEW3D_MT_view.remove(workspace_menu)
    if bpy.app.timers.is_registered(tick):bpy.app.timers.unregister(tick)
    for handlers in (bpy.app.handlers.load_post,bpy.app.handlers.undo_post,bpy.app.handlers.redo_post):
        if ui_context.clear in handlers:handlers.remove(ui_context.clear)
    _seen_ui.clear();ui_context.clear();del bpy.types.WindowManager.beam_target

CLASSES=(*ui_context.CLASSES,BEAM_OT_workspace,BEAM_OT_ui_action,BEAM_OT_receiver,BEAM_MT_receiver_groups,BEAM_OT_ui_member,BEAM_OT_new_auto,BEAM_OT_draft_preset)
