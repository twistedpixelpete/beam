"""Persistent per-scene workflow data, separate from projector engineering."""
import bpy
from .blend_groups import BeamBlendGroup
from bpy.props import PointerProperty, EnumProperty, CollectionProperty, IntProperty, StringProperty, BoolProperty, FloatProperty

_seen_selection={}


def redraw(self=None,context=None):
    if context and context.screen:
        for area in context.screen.areas:
            if area.type=='VIEW_3D': area.tag_redraw()


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
    include_labels: BoolProperty(name='Labels',default=True)
    include_frustums: BoolProperty(name='Frustums',default=True)
    include_grids: BoolProperty(name='Grids / Output',default=True)
    include_overlays: BoolProperty(name='Study Overlays',default=True)
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


class PS_SceneSettings(bpy.types.PropertyGroup):
    project_name: StringProperty(name='Project Name')
    venue: StringProperty(name='Venue')
    revision: StringProperty(name='Revision')
    client: StringProperty(name='Client')
    author: StringProperty(name='Author')
    blend_groups: CollectionProperty(type=BeamBlendGroup)
    blend_group_index: IntProperty(default=0)
    label_detail: EnumProperty(name='Label Detail',description='Viewport annotations: Off keeps IDs; Minimal shows width/height; Full adds throw and blend measurements',items=[('OFF','Off','Keep projector IDs only'),('MINIMAL','Minimal','Discreet image width and height'),('FULL','Full','All technical viewport annotations')],default='MINIMAL',update=redraw)
    show_frustums: BoolProperty(name='Frustums',default=True,update=redraw)
    show_centre_rays: BoolProperty(name='Centre Rays',default=True,update=redraw)
    show_projected_identifiers: BoolProperty(name='Projected Names',default=True,update=redraw)
    show_labels: BoolProperty(name='Projector Labels',default=True,update=redraw)
    show_outputs: BoolProperty(name='Projected Output',default=True,update=redraw)
    show_study_cameras: BoolProperty(name='Study Cameras',default=True,update=camera_visibility)
    preview_distance_display: FloatProperty(name='Preview Distance',get=preview_get,set=preview_set,min=.01)
    active_projector: PointerProperty(name='Active Study Projector',description='Study controls follow this projector; selecting a Beam object defaults transforms to Local axes and restores the previous orientation for other objects',type=bpy.types.Object,poll=projector_poll,update=redraw)
    display_units: EnumProperty(name='Display Units',items=[('m','Metres',''),('mm','Millimetres','')],default='mm',update=redraw)
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
    if changed and obj and obj.select_get() and obj.ps.is_projector:
        settings.active_projector=obj
    if changed and obj and obj.select_get():
        for i,group in enumerate(settings.blend_groups):
            if group.controller==obj or any(m.projector==obj for m in group.members):
                settings.blend_group_index=i;break
    return changed


def active(context):
    # Panel drawing must never write ID data. The timer commits new selections.
    current=context.view_layer.objects.active
    key=context.scene.as_pointer()
    if current and current.select_get() and current.ps.is_projector and key in _seen_selection and _seen_selection[key]!=current.as_pointer():
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
