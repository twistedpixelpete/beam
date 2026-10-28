"""Persistent per-scene workflow data, separate from projector engineering."""
import bpy
from .blend_groups import BeamBlendGroup
from .analysis_display import MODES
from bpy.props import PointerProperty, EnumProperty, CollectionProperty, IntProperty, StringProperty, BoolProperty, FloatProperty

_seen_selection={}


def redraw(self=None,context=None):
    if context and context.screen:
        for area in context.screen.areas:
            if area.type in {'VIEW_3D','PROPERTIES'}: area.tag_redraw()


def projector_poll(self,obj):
    return obj.ps.is_projector and obj.name in self.id_data.objects


def camera_poll(self,obj):
    return obj.type=='CAMERA' and not obj.get('ps_helper')


class PS_StudyView(bpy.types.PropertyGroup):
    uuid: StringProperty()
    name: StringProperty(name='View Name',default='Overview')
    camera: PointerProperty(name='Camera',type=bpy.types.Object,poll=camera_poll)
    resolution_x: IntProperty(name='Width',default=1920,min=64,max=8192)
    resolution_y: IntProperty(name='Height',default=1080,min=64,max=8192)
    include_projected_identifiers: BoolProperty(name='Projected Names',default=True)
    include_labels: BoolProperty(name='Labels',description='Include engineering labels in this saved view’s export',default=True)
    include_frustums: BoolProperty(name='Frustums',description='Include projector frustums in this saved view’s export',default=True)
    include_grids: BoolProperty(name='Grids / Output',description='Include projected grids and output in this saved view’s export',default=True)
    include_overlays: BoolProperty(name='Study Overlays',default=True)
    analysis_overlay: EnumProperty(name='Analysis Overlay',items=[('NONE','None','')]+MODES,default='NONE')
    image_filename: StringProperty()
    exported_at: StringProperty()


def preview_get(self):
    obj=self.active_projector
    return (obj.ps.preview_distance if obj else 10)*(1000 if self.display_units=='mm' else 1)


def preview_set(self,value):
    if self.active_projector:
        self.active_projector.ps.preview_distance=value/(1000 if self.display_units=='mm' else 1)


def camera_visibility(self,context):
    for view in self.views:
        if view.camera: view.camera.hide_set(not self.show_study_cameras)
    redraw(self,context)


def analysis_changed(self,context):
    from .analysis_runtime import invalidate
    invalidate();redraw(self,context)

def observer_changed(self,context):
    from .analysis_runtime import invalidate
    invalidate('ACUITY');redraw(self,context)


def display_changed(self,context):
    from .analysis_runtime import update_display
    update_display(self);redraw(self,context)


def source_changed(self,context):
    if self.analysis_scope=='PROJECTOR':analysis_changed(self,context)
    else:redraw(self,context)


class PS_SceneSettings(bpy.types.PropertyGroup):
    create_projector_body: BoolProperty(name='Body for New Projectors', description='Create new projectors with a built-in body; duplicates inherit their source', default=True)
    analysis_receiver: PointerProperty(name='Receiver',type=bpy.types.Object,poll=lambda self,o:o.type=='MESH' and not o.ps.is_projector,update=analysis_changed)
    analysis_scope: EnumProperty(name='Projectors',items=[('ALL','All projectors',''),('PROJECTOR','Active projector',''),('GROUP','Active Blend Group','')],default='ALL',update=analysis_changed)
    analysis_detail: EnumProperty(name='Samples',items=[('512','Quick · 512',''),('2048','Standard · 2048',''),('8192','Detailed · 8192','')],default='2048',update=analysis_changed)
    analysis_show: BoolProperty(name='Show Heatmap',default=False,update=redraw)
    analysis_mode: EnumProperty(name='Heatmap',items=MODES,update=redraw)

    analysis_observer: PointerProperty(name='Observer',type=bpy.types.Object,poll=lambda self,o:o.beam_observer.is_observer and o.name in self.id_data.objects,update=observer_changed)
    illuminance_scale: EnumProperty(name='Lux Scale',items=[('AUTO','Auto Scale','Current analysis minimum to maximum'),('FIXED','Fixed Range','Zero to chosen maximum lux')],update=display_changed)
    illuminance_max: FloatProperty(name='Maximum Lux',default=1000,min=.01,update=display_changed)
    use_target_illuminance: BoolProperty(name='Target Illuminance',default=False,update=display_changed)
    target_illuminance: FloatProperty(name='Target Lux',default=300,min=0,update=display_changed)

    inspector: EnumProperty(name='Inspector',items=[('PROJECTOR','Projector',''),('SCREEN','Screen',''),('GROUP','Blend',''),('VIEW','Views',''),('EXPORT','Export','')],default='PROJECTOR',update=redraw)
    pin_context: BoolProperty(name='Pin Beam Context',description='Keep the active Beam objects and module when Blender selection changes',default=False,update=redraw)
    ui_create_screen: BoolProperty(default=False,update=redraw)
    reverse_receiver: PointerProperty(name='Receiver',type=bpy.types.Object,poll=lambda self,obj:obj.type=='MESH' and not obj.ps.is_projector,update=redraw)
    active_screen: PointerProperty(name='Active Screen',type=bpy.types.Object,poll=lambda self,obj:obj.type=='MESH' and hasattr(obj,'beam_screen') and obj.beam_screen.is_screen,update=redraw)
    project_name: StringProperty(name='Project Name')
    venue: StringProperty(name='Venue')
    revision: StringProperty(name='Revision')
    client: StringProperty(name='Client')
    author: StringProperty(name='Author')
    blend_groups: CollectionProperty(type=BeamBlendGroup)
    blend_group_index: IntProperty(default=0,update=analysis_changed)
    ui_member_index: IntProperty(default=0)
    label_detail: EnumProperty(name='Label Detail',description='Viewport annotations: Off keeps IDs; Minimal shows width/height; Full adds throw and blend measurements',items=[('OFF','Off','Keep projector IDs only'),('MINIMAL','Minimal','Discreet image width and height'),('FULL','Full','All technical viewport annotations')],default='MINIMAL',update=redraw)
    show_frustums: BoolProperty(name='Frustums',default=True,update=redraw)
    show_centre_rays: BoolProperty(name='Centre Rays',default=True,update=redraw)
    show_projected_identifiers: BoolProperty(name='Projected Names',default=True,update=redraw)
    show_labels: BoolProperty(name='Projector Labels',default=True,update=redraw)
    show_outputs: BoolProperty(name='Projected Output',default=True,update=redraw)
    show_study_cameras: BoolProperty(name='Study Cameras',default=True,update=camera_visibility)
    preview_distance_display: FloatProperty(name='Preview Distance',get=preview_get,set=preview_set,min=.01)
    active_projector: PointerProperty(name='Active Study Projector',description='Study controls follow this projector; selecting a Beam object defaults transforms to Local axes and restores the previous orientation for other objects',type=bpy.types.Object,poll=projector_poll,update=source_changed)
    display_units: EnumProperty(name='Display Units',items=[('m','m','Metres'),('mm','mm','Millimetres')],default='mm',update=display_changed)
    views: CollectionProperty(type=PS_StudyView)
    view_index: IntProperty(default=0)
    shadow_resolution: EnumProperty(name='Projection Detail',items=[('512','Fast (512)',''),('1024','Balanced (1024)',''),('2048','Fine (2048)','')],default='1024',update=redraw)
    last_current_image: StringProperty()
    last_current_exported_at: StringProperty()


def sync_selection(context):
    scene=context.scene
    obj=context.view_layer.objects.active
    key=scene.as_pointer()
    selection=obj.as_pointer() if obj and obj.select_get() else None
    changed=_seen_selection.get(key,selection if scene.ps_study.active_projector else object())!=selection
    _seen_selection[key]=selection
    settings=scene.ps_study
    if settings.active_projector and settings.active_projector.name not in scene.objects:
        settings.active_projector=None
    if settings.reverse_receiver and settings.reverse_receiver.name not in scene.objects:settings.reverse_receiver=None
    if changed and obj and obj.select_get() and obj.type=='MESH' and not obj.ps.is_projector and not obj.get('beam_screen_detail'):settings.reverse_receiver=obj
    if settings.pin_context:return changed
    if changed and obj and obj.select_get() and obj.ps.is_projector:
        settings.active_projector=obj;settings.inspector='PROJECTOR'
    if changed and obj and obj.select_get() and obj.beam_screen.is_screen:
        settings.active_screen=obj;settings.inspector='SCREEN'
    if settings.active_screen and settings.active_screen.name not in scene.objects:settings.active_screen=None
    if changed and obj and obj.select_get():
        for i,group in enumerate(settings.blend_groups):
            if group.controller==obj or any(m.projector==obj for m in group.members):
                settings.blend_group_index=i
                if group.controller==obj:settings.inspector='GROUP'
                break
        for i,view in enumerate(settings.views):
            if view.camera==obj:settings.view_index=i;settings.inspector='VIEW';break
    return changed


def active(context):
    # Panel drawing must never write ID data. The timer commits new selections.
    current=context.view_layer.objects.active
    key=context.scene.as_pointer()
    if not context.scene.ps_study.pin_context and current and current.select_get() and current.ps.is_projector and key in _seen_selection and _seen_selection[key]!=current.as_pointer():
        return current
    obj=context.scene.ps_study.active_projector
    return obj if obj and obj.ps.is_projector and obj.name in context.scene.objects else None


class PS_OT_active(bpy.types.Operator):
    bl_idname='ps.active_projector'
    bl_label='Use Selected Projector'
    bl_options={'REGISTER','UNDO'}
    clear: BoolProperty(default=False)
    def execute(self,context):
        obj=context.view_layer.objects.active
        if self.clear:
            context.scene.ps_study.active_projector=None
        elif obj and obj.ps.is_projector:
            context.scene.ps_study.active_projector=obj
        else:
            self.report({'WARNING'},'Select a projector first'); return {'CANCELLED'}
        _seen_selection[context.scene.as_pointer()]=obj.as_pointer() if obj and obj.select_get() else None
        return {'FINISHED'}

CLASSES=(PS_StudyView,PS_SceneSettings,PS_OT_active)
