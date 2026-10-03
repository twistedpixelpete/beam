"""Screen subsystem lifecycle; existing projector data/export contracts stay separate."""
import bpy
from bpy.app.handlers import persistent
from . import screen_data,screen_operators,screen_ui,screen_objects,screen_display
CLASSES=(*screen_data.CLASSES,*screen_operators.CLASSES,*screen_ui.CLASSES)

@persistent
def changed(scene=None,graph=None):
    if graph and any(u.is_updated_geometry or u.is_updated_transform for u in graph.updates):screen_display.clear()

@persistent
def reset(*args):
    screen_objects._owners.clear();screen_display.clear()

def tick():
    from .group_lifecycle import defer_native_copy
    if bpy.context.scene and not defer_native_copy(bpy.context):screen_objects.reconcile()
    return .25

def register():
    bpy.types.Object.beam_screen=bpy.props.PointerProperty(type=screen_data.BeamScreen)
    bpy.types.Scene.beam_screen_draft=bpy.props.PointerProperty(type=screen_data.BeamScreen)
    for handlers,fn in [(bpy.app.handlers.depsgraph_update_post,changed),(bpy.app.handlers.load_post,reset),(bpy.app.handlers.undo_post,reset),(bpy.app.handlers.redo_post,reset)]:
        if fn not in handlers:handlers.append(fn)
    if not bpy.app.timers.is_registered(tick):bpy.app.timers.register(tick,persistent=True)

def unregister():
    if bpy.app.timers.is_registered(tick):bpy.app.timers.unregister(tick)
    for handlers,fn in [(bpy.app.handlers.depsgraph_update_post,changed),(bpy.app.handlers.load_post,reset),(bpy.app.handlers.undo_post,reset),(bpy.app.handlers.redo_post,reset)]:
        if fn in handlers:handlers.remove(fn)
    reset();del bpy.types.Object.beam_screen;del bpy.types.Scene.beam_screen_draft
