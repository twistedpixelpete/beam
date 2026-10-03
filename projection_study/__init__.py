"""Beam: Blender 4.5+ extension. GPL-3.0-or-later."""
import bpy
from . import screens
from . import blend_groups, presentation, local_orientation, group_lifecycle
from . import projector_data, operators, ui, runtime, viewport_display, export_disguise, study_data, study_views, export_json

CLASSES = (*screens.CLASSES,*group_lifecycle.CLASSES,*blend_groups.CLASSES,*presentation.CLASSES,*study_data.CLASSES, projector_data.PS_Settings, *operators.CLASSES, export_disguise.PS_OT_export, *study_views.CLASSES, export_json.PS_OT_export_json, ui.PS_PT_main)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Object.ps = bpy.props.PointerProperty(type=projector_data.PS_Settings)
    bpy.types.Scene.ps_study = bpy.props.PointerProperty(type=study_data.PS_SceneSettings)
    screens.register()
    runtime.register()
    local_orientation.register()
    viewport_display.register()
    bpy.app.handlers.save_pre.append(operators.restore_views)
    bpy.app.handlers.load_pre.append(operators.restore_views)
    bpy.app.handlers.load_pre.append(study_views.cleanup)
    bpy.app.handlers.save_pre.append(study_views.cleanup)
    bpy.app.handlers.load_pre.append(presentation.cleanup)
    bpy.app.handlers.save_pre.append(presentation.before_save)
    bpy.app.handlers.save_post.append(presentation.after_save)

def unregister():
    screens.unregister()
    local_orientation.unregister()
    presentation.cleanup()
    for handlers,fn in ((bpy.app.handlers.save_pre,presentation.before_save),(bpy.app.handlers.save_post,presentation.after_save)):
        if fn in handlers: handlers.remove(fn)
    if presentation.cleanup in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.remove(presentation.cleanup)
    blend_groups.solo_uuid=None
    from . import blend_display
    blend_display._shader=None
    study_views.cleanup()
    if study_views.cleanup in bpy.app.handlers.save_pre: bpy.app.handlers.save_pre.remove(study_views.cleanup)
    if study_views.cleanup in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.remove(study_views.cleanup)
    operators.restore_views()
    for handlers in (bpy.app.handlers.save_pre,bpy.app.handlers.load_pre):
        if operators.restore_views in handlers: handlers.remove(operators.restore_views)
    viewport_display.unregister()
    runtime.unregister()
    study_data._seen_selection.clear()
    del bpy.types.Scene.ps_study
    del bpy.types.Object.ps
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
