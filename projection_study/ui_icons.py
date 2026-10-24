"""Restrained positive-state icon; active controls use the native Blender theme."""
from pathlib import Path
import bpy.utils.previews
_preview=None

def icon(name):return _preview[name].icon_id if _preview and name in _preview else 0

def register():
    global _preview
    _preview=bpy.utils.previews.new()
    for name in ('valid',):_preview.load(name,str(Path(__file__).parent/'icons'/(name+'.png')),'IMAGE')

def unregister():
    global _preview
    if _preview:bpy.utils.previews.remove(_preview);_preview=None
