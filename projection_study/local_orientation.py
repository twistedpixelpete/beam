"""Selection-scoped Local orientation; restore the user's scene orientation."""
import bpy
from bpy.app.handlers import persistent
_saved={}
_selection={}


def restore(scene):
    key=scene.as_pointer()
    previous=_saved.pop(key,None)
    if previous is not None:
        try: scene.transform_orientation_slots[0].type=previous
        except (TypeError,ReferenceError): scene.transform_orientation_slots[0].type='GLOBAL'
    _selection.pop(key,None)


def sync(context):
    scene=context.scene
    for other in bpy.data.scenes:
        if other!=scene and other.as_pointer() in _saved: restore(other)
    obj=context.view_layer.objects.active
    beam=obj and obj.select_get() and (obj.ps.is_projector or obj.get('beam_group_uuid') or (hasattr(obj,'beam_screen') and obj.beam_screen.is_screen))
    key=scene.as_pointer()
    if not beam:
        restore(scene);return
    identity=obj.as_pointer()
    if _selection.get(key)==identity:return
    if key not in _saved:_saved[key]=scene.transform_orientation_slots[0].type
    scene.transform_orientation_slots[0].type='LOCAL'
    _selection[key]=identity


@persistent
def cleanup(*args):
    for scene in bpy.data.scenes: restore(scene)
    _saved.clear();_selection.clear()


@persistent
def resume(*args):
    if bpy.context.scene:sync(bpy.context)


def register():
    for handlers,fn in ((bpy.app.handlers.save_pre,cleanup),(bpy.app.handlers.save_post,resume),(bpy.app.handlers.load_pre,cleanup)):
        if fn not in handlers:handlers.append(fn)


def unregister():
    cleanup()
    for handlers,fn in ((bpy.app.handlers.save_pre,cleanup),(bpy.app.handlers.save_post,resume),(bpy.app.handlers.load_pre,cleanup)):
        if fn in handlers:handlers.remove(fn)
