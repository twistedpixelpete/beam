"""Run from Blender Text Editor in a disposable session with a 3D View."""
import bpy
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import projection_study as addon
if hasattr(bpy.types.Object,'ps'):
    raise RuntimeError('Disable the installed extension before running source tests in this disposable session')
(root/'work').mkdir(exist_ok=True)
original=bpy.context.window.scene
try:
    for milestone in range(1,16):
        scene=bpy.data.scenes.new('Projection Study test')
        bpy.context.window.scene=scene
        meshes=set(bpy.data.meshes); cameras=set(bpy.data.cameras)
        try:
            if milestone!=1: addon.register()
            path=root/'tests'/f'blender_m{milestone}.py'
            area=next((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),None)
            if area is None: raise RuntimeError('Keep a 3D View open for GPU integration tests')
            region=next(r for r in area.regions if r.type=='WINDOW')
            with bpy.context.temp_override(area=area,region=region):
                exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path),'root':root})
        finally:
            if hasattr(bpy.types.Object,'ps'): addon.unregister()
            bpy.context.window.scene=original
            for obj in list(scene.objects): bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.scenes.remove(scene)
            for data,previous in ((bpy.data.meshes,meshes),(bpy.data.cameras,cameras)):
                for item in set(data)-previous:
                    if item.users==0: data.remove(item)
finally:
    bpy.context.window.scene=original
print('ALL BLENDER INTEGRATION TESTS PASSED')
