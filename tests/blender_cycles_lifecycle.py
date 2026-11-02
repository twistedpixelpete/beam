"""Cycles mode lifecycle, content, shared math and engineering isolation."""
import bpy,sys,tempfile,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import projection_study as addon
from projection_study import cycles_projection as cp, runtime, target_raycast
from projection_study.projector_object import create
addon.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';p=create(bpy.context)
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,8,0))
def update():bpy.context.view_layer.update();runtime.refresh(True);cp.sync(s)
update();before=runtime.CACHE[p.as_pointer()]
from projection_study.export_json import document
before_json=document(bpy.context);before_json.pop('exported_at',None)
s.ps_study.projection_mode='CYCLES';update()
after=runtime.CACHE[p.as_pointer()]
after_json=document(bpy.context);after_json.pop('exported_at',None)
assert before_json==after_json, 'Engineering export changed with render mode'
for key in ('metrics','hit','origin','rotation','corners','beam_corners','target'):
    if key in before:assert before[key]==after[key],key
light=next(o for o in s.objects if o.get(cp.TAG));data=light.data;tree=data.node_tree
assert light.parent==p and light.get('ps_helper') and light.hide_select
assert not light.hide_render
signature=cp._signatures.copy();start=time.perf_counter()
for _ in range(100):cp.sync(s)
idle=(time.perf_counter()-start)/100
assert cp._signatures==signature and light.data==data and light.data.node_tree==tree
image=tree.nodes['Content'].image
for mode in ('SOLID','CHECKER','GRID','ID','UV_GRID','COLOR_GRID'):
    p.ps.output_mode=mode;cp.sync(s)
    assert tree.nodes['Content'].image is not None,mode
assert len([g for g in bpy.data.node_groups if g.get(cp.TAG)])==1
p.ps.output_mode='IMAGE';p.ps.image=None;cp.sync(s) # Missing image safely emits black.
p.ps.output_mode='GRID';cp.sync(s)
p.ps.show_output=False;cp.sync(s);assert light.hide_render
p.ps.show_output=True;s.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version<(5,0,0) else 'BLENDER_EEVEE';cp.sync(s);assert light.hide_render
s.render.engine='CYCLES';cp.sync(s);assert not light.hide_render
p.hide_set(True);cp.sync(s);assert light.hide_get();p.hide_set(False);cp.sync(s);assert not light.hide_get()
# Excluding a source collection also excludes its generated light per layer.
source_collection=p.users_collection[0]
def find_layer(node,collection):
    if node.collection==collection:return node
    for child in node.children:
        result=find_layer(child,collection)
        if result:return result
node=find_layer(bpy.context.view_layer.layer_collection,source_collection)
node.exclude=True;cp.sync(s)
helper_collection=light.users_collection[0]
assert bpy.context.view_layer.layer_collection.children[helper_collection.name].exclude
node.exclude=False;cp.sync(s)
assert not bpy.context.view_layer.layer_collection.children[helper_collection.name].exclude
source_collection.hide_render=True;cp.sync(s)
assert bpy.context.view_layer.layer_collection.children[helper_collection.name].exclude
source_collection.hide_render=False;cp.sync(s)
energy=data.energy;s.unit_settings.scale_length=.01;cp.sync(s);assert abs(data.energy/energy-10000)<.01
s.unit_settings.scale_length=1
q=create(bpy.context,source=p);update()
assert len([o for o in s.objects if o.get(cp.TAG)])==2
q.ps.throw_ratio=2;cp.sync(s);assert light.data.node_tree.nodes['Raster'].inputs['Ratio'].default_value==p.ps.throw_ratio
# Native duplication of both body and its managed child must not share light data.
native=p.copy();native.data=p.data.copy();s.collection.objects.link(native)
child=light.copy();child.parent=native;light.users_collection[0].objects.link(child);update()
assert child.users_collection[0]!=light.users_collection[0]
assert child.data!=light.data
bpy.data.objects.remove(native,do_unlink=True);update()
assert len([o for o in s.objects if o.get(cp.TAG)])==2
# Scene copies linking source objects must not double the lights.
other=bpy.data.scenes.new('Other scene');other.render.engine='CYCLES'
other.collection.objects.link(p);other.collection.objects.link(light)
other.ps_study.projection_mode='CYCLES';cp.sync(other)
assert light.name not in other.objects
assert len([o for o in other.objects if o.get(cp.TAG)])==1
other.ps_study.projection_mode='PLANNING';assert light.name in s.objects
bpy.data.scenes.remove(other)
# Save/load is self-contained; reload handlers must discard pointer caches.
with tempfile.TemporaryDirectory() as folder:
    path=str(Path(folder)/'cycles.blend');bpy.ops.wm.save_as_mainfile(filepath=path);bpy.ops.wm.open_mainfile(filepath=path)
    s=bpy.context.scene;cp.sync(s)
    assert len([o for o in s.objects if o.get(cp.TAG)])==2
    assert all(o.data.node_tree.nodes['Content'].image for o in s.objects if o.get(cp.TAG))
    s.ps_study.projection_mode='PLANNING'
    assert not any(o.get(cp.TAG) for o in bpy.data.objects)
    assert not any(g.get(cp.TAG) for g in bpy.data.node_groups)
    assert not any(i.get('beam_render_pattern') for i in bpy.data.images)
# Disabling the add-on cleans its own assets without removing unrelated lights.
s.ps_study.projection_mode='CYCLES';cp.sync(s)
user=bpy.data.lights.new('User light','POINT')
addon.unregister();assert bpy.data.lights.get('User light')==user
assert not any(o.get(cp.TAG) for o in bpy.data.objects)
print('CYCLES LIFECYCLE PASS; idle sync seconds:',idle)
