"""0.9 planning acceptance. Run in a disposable factory-startup Blender process."""
import bpy,sys,math,json
from pathlib import Path
from types import SimpleNamespace
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects,projector_object,runtime,inverse_solver,auto_layout,layout_coverage,blend_groups,group_lifecycle,reverse_mapping,study_data
addon.register()
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
c=bpy.context;s=c.scene

def refresh():c.view_layer.update();runtime.refresh(True)
def near(a,b,tol=1e-4):assert abs(a-b)<tol,(a,b)
def reject(call):
    try:call()
    except ValueError:return
    raise AssertionError('Invalid operation accepted')
def clear():
    s.ps_study.blend_groups.clear()
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    runtime.reset();layout_coverage._cache.clear()
def wall(w=30,h=15):
    p=s.beam_screen_draft;p.width=w;p.height=h;p.aspect='FREE'
    o=screen_objects.create(c,p);o.location=(0,10,-h/2);s.ps_study.active_screen=o;return o
def opts(**kwargs):
    d=dict(use_template=False,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=6,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100);d.update(kwargs);return SimpleNamespace(**d)

receiver=wall();pj=projector_object.create(c);refresh();pose=pj.matrix_world.copy();target=Vector(pj.ps.target_point_m)
for field,value in [('HEIGHT',6),('WIDTH',12),('DENSITY',300),('PIXEL_SIZE',.005),('RATIO',1.25)]:
    inverse_solver.solve(c,pj,field,value);assert pj.matrix_world==pose
    near(inverse_solver.measurement(runtime.CACHE[pj.as_pointer()],field,pj.ps),value)
pj.ps.solve_by='POSITION';ratio=pj.ps.throw_ratio
inverse_solver.solve(c,pj,'DISTANCE',5);near(pj.matrix_world.translation.x,0);near(pj.matrix_world.translation.z,0)
near((Vector(pj.ps.target_point_m)-target).length,0);near(pj.ps.throw_ratio,ratio)
for name in ('solve_lock_position','solve_lock_lens'):
    setattr(pj.ps,name,True);pj.ps.solve_by='POSITION' if name.endswith('position') else 'LENS'
    state=(pj.matrix_world.copy(),pj.ps.throw_ratio)
    reject(lambda:inverse_solver.solve(c,pj,'WIDTH',4));assert pj.matrix_world==state[0];near(pj.ps.throw_ratio,state[1]);setattr(pj.ps,name,False)
pj.ps.solve_by='POSITION';pj.ps.shift_h=8;reject(lambda:inverse_solver.solve(c,pj,'DISTANCE',6));pj.ps.shift_h=0
# Parent transforms and metre conversion preserve the same physical solution.
parent=bpy.data.objects.new('Rig',None);s.collection.objects.link(parent);world=pj.matrix_world.copy();parent.location=(2,-1,3);pj.parent=parent;c.view_layer.update();pj.matrix_world=world
inverse_solver.solve(c,pj,'DISTANCE',7);near(runtime.CACHE[pj.as_pointer()]['metrics'].distance,7)
pj.ps.solve_by='LENS';pj.ps.solve_lock_target=False;pj.ps.shift_h=12
receiver.rotation_euler.z=.1;refresh();inverse_solver.solve(c,pj,'WIDTH',8);near(runtime.CACHE[pj.as_pointer()]['metrics'].width,8,.001)
print('PASS inverse: all six values, locks, parent, angled target, shifted position rejection')

clear();receiver=wall(16,3.375);screen_objects.select(c,receiver)
g,result=auto_layout.create(c,opts());members=blend_groups.member_objects(g)
assert len(members)==3 and len({p.ps.uuid for p in members})==3 and len({p.ps.identifier for p in members})==3 and len({tuple(p.ps.colour) for p in members})==3
report=layout_coverage.report(g,c);near(report['coverage'],100,.01)
for pair in report['pairs']:near(pair['actual']['pixels'],200,.01);near(pair['actual']['metres'],.625,.001)
spacing=[members[i+1].matrix_world.translation.x-members[i].matrix_world.translation.x for i in range(2)];near(*spacing)
members[1].location.x+=1;refresh();changed=layout_coverage.report(g,c);assert changed['coverage']<100 and any(p['gap_m']>0 for p in changed['pairs'])
members[1].location.x-=1;members[0].ps.resolution_x=3840;refresh();near(layout_coverage.report(g,c)['pairs'][0]['actual']['pixels'],400,.02);members[0].ps.resolution_x=1920
receiver.location.x+=1;refresh();assert layout_coverage.report(g,c)['coverage']<100;receiver.location.x-=1
receiver.rotation_euler.z=.08;refresh();assert layout_coverage.report(g,c)['pairs']!=report['pairs'];receiver.rotation_euler.z=0;refresh()
copy=group_lifecycle.duplicate(g,c);assert copy.layout_screen==receiver
assert json.loads(copy.controller['beam_group_recipe'])['layout_screen_uuid']==receiver.beam_screen.uuid
export=blend_groups.serialize(c);assert export[0]['measurement_plane']['origin_m']==list(layout_coverage.report(g,c)['centre'])
# Persistent screen actions operate on the shown screen, not selected venue geometry.
bpy.ops.mesh.primitive_cube_add(location=(100,100,100));study_data.sync_selection(c)
assert s.ps_study.active_screen==receiver
receiver.beam_screen.width=17;bpy.ops.beam.screen_action(action='UPDATE');near(receiver.dimensions.x,17,.001)
print('PASS horizontal: identity, equal spacing, live px/m/%, gaps, resolution, screen movement, duplicate recipe, persistent screen')

for kind,w,h,extra in [('VERTICAL',6,9,dict(count=3)),('ARRAY',11,6,dict(columns=2,rows=2)),('HORIZONTAL',16,3.375,dict(auto_count=True))]:
    clear();receiver=wall(w,h);receiver.rotation_euler.z=.27;screen_objects.select(c,receiver)
    g,r=auto_layout.create(c,opts(layout_type=kind,**extra));near(layout_coverage.report(g,c)['coverage'],100,.01)
    assert len(g.members)==r['count']
print('PASS vertical, array, auto count and rotated screens')
# Template optics, shifts, per-projector editable data; failed creation is atomic.
clear();receiver=wall(16,3.375);template=projector_object.create(c);template.ps.shift_h=5;template.ps.shift_v=4;template.ps.lumens=28000;template.ps.brightness=72;template.ps.stack=2
screen_objects.select(c,receiver);g,r=auto_layout.create(c,opts(use_template=True));assert all(p.ps.shift_h==5 and p.ps.lumens==28000 and p.ps.stack==2 for p in blend_groups.member_objects(g))
clear();receiver=wall(16,3.375);bpy.ops.mesh.primitive_cube_add(location=(0,8,0),scale=(20,.3,4));screen_objects.select(c,receiver)
before=set(bpy.data.objects);reject(lambda:auto_layout.create(c,opts()));assert set(bpy.data.objects)==before and not s.ps_study.blend_groups
print('PASS template and obstructed creation rollback')
clear();s.unit_settings.scale_length=.01;receiver=wall(16,3.375);screen_objects.select(c,receiver)
g,r=auto_layout.create(c,opts());near(layout_coverage.report(g,c)['pairs'][0]['actual']['metres'],.625,.001)
near(runtime.CACHE[g.members[0].projector.as_pointer()]['metrics'].distance,6,.001)
from projection_study.export_json import document
from projection_study.json_contract import validate_relationships
payload=document(c);validate_relationships(payload)
(root/'work/auto-blend-contract.json').write_text(json.dumps(payload,indent=2,allow_nan=False))
clear();s.unit_settings.scale_length=1
print('PASS physical scene-unit scale and Auto Blend JSON relationships')

# Material reversibility across shared meshes, multiple slots and user replacement.
clear();receiver=wall();pj=projector_object.create(c);screen_objects.select(c,receiver)
original=bpy.data.materials.new('Original UV');original.use_nodes=True
receiver.data.materials.clear();receiver.data.materials.append(original)
other=receiver.copy();s.collection.objects.link(other)
pj2=projector_object.create(c);refresh();rp=receiver.beam_reverse
rp.source='ACTIVE';assert reverse_mapping.sources(c,rp)==[pj2]
rp.source='SELECTED';rp.projector=pj;assert reverse_mapping.sources(c,rp)==[pj]
rp.source='ALL';pj2.ps.active=False;assert reverse_mapping.sources(c,rp)==[pj];pj2.ps.active=True
coverage_group=blend_groups.create(c,[pj,pj2],'HORIZONTAL',2,1,10,'PERCENT',preserve=True)
rp.source='GROUP';rp.group_uuid=coverage_group.uuid;assert set(reverse_mapping.sources(c,rp))=={pj,pj2}
rp.source='SELECTED';screen_objects.select(c,receiver)
uvs=[tuple(v.uv) for v in receiver.data.uv_layers.active.data]
node_names=[n.name for n in original.node_tree.nodes]
reverse_mapping.enable(c,receiver);assert receiver.active_material!=original and other.active_material==original
assert [tuple(v.uv) for v in receiver.data.uv_layers.active.data]==uvs and [n.name for n in original.node_tree.nodes]==node_names
reverse_mapping.disable(receiver);assert receiver.active_material==original and receiver.material_slots[0].link=='DATA'
reverse_mapping.enable(c,receiver);replacement=original.copy();receiver.material_slots[0].material=replacement;reverse_mapping.disable(receiver);assert receiver.active_material==replacement
print('PASS non-destructive materials, shared mesh isolation, UV preservation, user replacements')
addon.unregister();addon.register();addon.unregister()
print('PASS PLANNING MILESTONE')
