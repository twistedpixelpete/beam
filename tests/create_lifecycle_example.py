"""Reproducible three-member duplication fixture for release 0.6."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,blend_groups as groups,group_lifecycle as life,local_orientation
from projection_study.projector_object import create
from projection_study.export_json import document
addon.register();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
mesh=bpy.data.meshes.new('Receiving wall');mesh.from_pydata([(-10,10,-10),(35,10,-10),(35,10,10),(-10,10,10)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Receiving wall',mesh);scene.collection.objects.link(wall)
a=create(bpy.context);a.ps.resolution_x=3840;a.ps.resolution_y=2160;a.ps.shift_h=5;a.ps.brightness=80;a.ps.lumens=25000;a.ps.notes='Technical template'
objects=[a,create(bpy.context,a),create(bpy.context,a)]
bpy.context.view_layer.update();runtime.refresh(True)
group=groups.create(bpy.context,objects,'HORIZONTAL',3,1,20,'PERCENT');group.notes='Three-projector rig; third member has a 150 mm local offset'
objects[2].location.x=.15;bpy.context.view_layer.update();runtime.refresh(True)
duplicate=life.duplicate(group,bpy.context);runtime.refresh(True)
assert [m.projector.ps.identifier for m in duplicate.members]==['PJ04','PJ05','PJ06']
assert duplicate.name=='BG02' and abs(duplicate.members[2].projector.location.x-.15)<1e-6
out=root/'examples/0.6';out.mkdir(exist_ok=True)
(out/'Beam_group_lifecycle.json').write_text(json.dumps(document(bpy.context),indent=2,allow_nan=False)+'\n')
local_orientation.cleanup();bpy.data.libraries.write(str(out/'Beam_group_lifecycle.blend'),{scene})
addon.unregister()
print('EXAMPLE PASS: BG01 PJ01–PJ03; independent BG02 PJ04–PJ06, 150 mm offset preserved')
