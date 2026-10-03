"""Run in a disposable background Blender; actual exports, no GPU required."""
import sys,math,json
from pathlib import Path
import bpy
from mathutils import Matrix,Euler
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,blend_groups,export_json,export_disguise
from projection_study.projector_object import create
from projection_study.json_contract import validate_relationships
addon.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
out=root/'work/json-contract';out.mkdir(parents=True,exist_ok=True)
def write(name,data):
    text=json.dumps(data,indent=2,allow_nan=False)+'\n'
    (out/name).write_text(text); assert json.loads(text)==data
    validate_relationships(data)
def refresh(): bpy.context.view_layer.update();runtime.refresh(True)
# Non-default world unit scale catches accidental Blender-unit serialization.
scene.unit_settings.scale_length=.01
mesh=bpy.data.meshes.new('Audit wall'); mesh.from_pydata([(-10000,1000,-10000),(10000,1000,-10000),(10000,1000,10000),(-10000,1000,10000)],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Audit wall',mesh);scene.collection.objects.link(wall)
a=create(bpy.context); b=create(bpy.context); b.location.x=750
refresh()
group=blend_groups.create(bpy.context,[a,b],'HORIZONTAL',2,1,20,'PERCENT',preserve=True)
b.location.x+=12; b.rotation_euler.z+=.02; group.controller.location.x=100;group.controller.rotation_euler.z=.1
missing=create(bpy.context);missing.location=(0,0,0);refresh()
assert runtime.CACHE[missing.as_pointer()]['hit']
# A previously valid hit must clear completely after rotating away.
missing.rotation_euler.x=-math.pi/2
scaled=create(bpy.context);scaled.scale=(2,1,1)
excluded=create(bpy.context);excluded.rotation_euler.x=-math.pi/2;excluded.ps.active=False
refresh()
data=export_json.document(bpy.context)
assert len(data['disguise']['rows'])==2
assert {r[-1] for r in data['disguise']['rows']}=={a.ps.uuid,b.ps.uuid}
assert {e['code'] for e in data['disguise']['validation']['errors']}=={'NO_TARGET','INVALID_TRANSFORM'}
for p in data['projectors']:
    if p['uuid'] in (missing.ps.uuid,excluded.ps.uuid):
        assert p['target']['status']=='no_hit' and p['target']['point_m'] is None and p['calculated'] is None
assert not missing.ps.has_target and missing.ps.target_distance_m==0
assert data['project_metadata']==dict.fromkeys(('project_name','venue','revision','client','author'),'')
assert data['study_views']==[] and data['disguise']['validated'] is False
try: export_disguise.rows_for_scene(bpy.context)
except ValueError: pass
else: raise AssertionError('Standalone CSV must remain atomic')
def check_pose(data):
    lookup={p['uuid']:p for p in data['projectors']}
    for g in data['blend_groups']:
        assert [m['member_index'] for m in g['members']]==list(range(len(g['members'])))
        for member in g['members']:
            world=Matrix(g['transform']['matrix'])@Matrix(member['transform_in_group'])
            p=lookup[member['projector_uuid']]
            assert max(abs(world.translation[i]-p['position_m'][i]) for i in range(3))<1e-5
            rotation=Euler([math.radians(v) for v in p['rotation']['euler']],'XYZ').to_matrix()
            assert max(abs(world[i][j]-rotation[i][j]) for i in range(3) for j in range(3))<1e-5
check_pose(data)
write('Beam_mixed_validity.json',data)
assert export_json.display_colour([0,1,.5])[1]=='#00FFBC'
# Populated view without UI dependency; camera snapshots are world SI poses.
v=scene.ps_study.views.add(); from projection_study.utils import new_uuid
v.uuid=new_uuid();v.name='Audit view';cam=bpy.data.cameras.new('Audit camera')
obj=bpy.data.objects.new('Audit camera',cam);scene.collection.objects.link(obj);obj.location=(100,200,300);v.camera=obj
v.resolution_x=1920;v.resolution_y=1080
v.image_filename='Audit_view.png';v.exported_at='2026-10-03T12:00:00+00:00'
# Remove invalid and excluded projectors to produce clean handoff fixture.
for obj in (missing,scaled,excluded): bpy.data.objects.remove(obj,do_unlink=True)
refresh();data=export_json.document(bpy.context);check_pose(data)
assert max(abs(x-y) for x,y in zip(data['study_views'][0]['camera']['position_m'],[1.,2.,3.]))<1e-6
assert not data['disguise']['validation']['errors']
write('Beam_valid.json',data)
# Preview plane and null calculations are both explicit if all targets disappear.
wall.hide_set(True);refresh();preview=export_json.document(bpy.context)
assert all(p['calculated'] is None for p in preview['projectors'])
assert preview['blend_groups'][0]['measurement_plane']['status']=='preview'
write('Beam_no_targets.json',preview)
wall.hide_set(False)
# Corrupt relationships fail with actionable errors instead of a broken file.
import copy
bad=copy.deepcopy(data);bad['blend_groups'][0]['members'][0]['projector_uuid']=new_uuid()
try: validate_relationships(bad)
except ValueError as e: assert 'unresolved' in str(e)
else: raise AssertionError('Dangling UUID accepted')
# Stable row-major metadata for vertical/array layouts, independent of names.
blend_groups.remove_member(group,1)
assert export_json.document(bpy.context)['blend_groups'][0]['columns']==1
blend_groups.remove_member(group,0)
scene.ps_study.blend_groups.clear()
for layout,count,cols in [('VERTICAL',3,1),('ARRAY',6,3)]:
    objects=[create(bpy.context) for _ in range(count)]
    for i,o in enumerate(objects):o.location=(i*75,0,0)
    refresh();g=blend_groups.create(bpy.context,objects,layout,cols,(count+cols-1)//cols,20,'PERCENT',preserve=True)
    snapshot=export_json.document(bpy.context);check_pose(snapshot)
    exported=snapshot['blend_groups'][-1]
    assert [(m['column'],m['row']) for m in exported['members']]==[(i%cols,i//cols) for i in range(count)]
empty=bpy.data.scenes.new('Empty audit study');bpy.context.window.scene=empty
empty_data=export_json.document(bpy.context)
assert empty_data['projectors']==[] and empty_data['study_views']==[]
assert empty_data['disguise']['validation']['errors'][0]['code']=='NO_ACTIVE_PROJECTORS'
write('Beam_empty.json',empty_data)
bpy.context.window.scene=scene
print('JSON CONTRACT PASS: SI transforms, mixed eligibility, stale target clearing, UUIDs, groups, row-major order, views, blank metadata, sRGB')
addon.unregister()
