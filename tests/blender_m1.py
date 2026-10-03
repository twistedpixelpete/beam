import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy, projection_study as addon
addon.register()
bpy.ops.ps.add()
a=bpy.context.object
bpy.ops.ps.add()
b=bpy.context.object
assert (a.name,b.name)==('PJ01','PJ02')
assert a.ps.uuid != b.ps.uuid
assert len(a.data.vertices)==56
assert a.children[0].hide_select
addon.unregister()
print('MILESTONE 1 PASS')
