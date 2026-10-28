"""Actual Blender undo/redo of render mode and generated resources."""
import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import projection_study as addon
from projection_study import cycles_projection as cp
from projection_study.projector_object import create
addon.register();bpy.context.preferences.edit.use_global_undo=True
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
create(bpy.context);bpy.ops.ed.undo_push(message='Planning')
bpy.context.scene.ps_study.projection_mode='CYCLES';bpy.ops.ed.undo_push(message='Cycles')
bpy.ops.ed.undo();cp.sync(bpy.context.scene)
assert bpy.context.scene.ps_study.projection_mode=='PLANNING'
assert not any(o.get(cp.TAG) for o in bpy.data.objects)
bpy.ops.ed.redo();cp.sync(bpy.context.scene)
assert bpy.context.scene.ps_study.projection_mode=='CYCLES'
assert len([o for o in bpy.data.objects if o.get(cp.TAG)])==1
addon.unregister();print('CYCLES UNDO REDO PASS')
