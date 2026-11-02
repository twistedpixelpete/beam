"""Timers survive failures; failed group copies keep their objects. Background, no GPU."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,faults,group_lifecycle as life,blend_groups,projector_object
from mathutils import Vector
addon.register();c=bpy.context
mesh=bpy.data.meshes.new('Wall');mesh.from_pydata([(-20,10,0),(20,10,0),(20,10,20),(-20,10,20)],[],[(0,1,2,3)]);mesh.update()
wall=bpy.data.objects.new('Wall',mesh);c.scene.collection.objects.link(wall)
a=projector_object.create(c);b=projector_object.create(c);a.location=(-3,0,5);b.location=(3,0,5)
c.view_layer.update();runtime.refresh(True)
group=blend_groups.create(c,[a,b],'HORIZONTAL',2,1,200,'PIXELS',preserve=True);c.view_layer.update();runtime.refresh(True)

# 1. A raising refresh returns a retry interval rather than killing the timer.
original=runtime.refresh
def explode(*args,**kwargs):raise RuntimeError('simulated failure')
runtime.refresh=explode
assert runtime.tick()==1.0,'guarded tick must retry'
assert any('simulated failure' in line for line in faults.summary())
runtime.refresh=original
assert runtime.tick()==1/30 and not faults.summary(),'recovery clears the fault'

# 2. A native copy whose recipe can't be restored keeps its objects, reports, and stops retrying.
for label,mutate in (('unknown enum',lambda r:r['members'][0]['settings'].__setitem__('output_mode','HOLOGRAM')),
                     ('missing field',lambda r:r.pop('world'))):
    controller=group.controller
    copy=controller.copy();c.scene.collection.objects.link(copy)
    slot=bpy.data.objects.new('copied slot',None);c.scene.collection.objects.link(slot);slot['beam_layout_slot']=True;slot.parent=copy
    recipe=json.loads(controller['beam_group_recipe']);mutate(recipe);copy['beam_group_recipe']=json.dumps(recipe)
    c.view_layer.update()
    groups=len(c.scene.ps_study.blend_groups);objects=len(bpy.data.objects)
    runtime.invalidate();runtime.refresh(True)
    assert slot.name in bpy.data.objects,f'{label}: copied rig was deleted by a failed rebuild'
    assert len(c.scene.ps_study.blend_groups)==groups,f'{label}: partial group left behind'
    assert any(copy.name in line for line in faults.summary()),f'{label}: failure not reported {faults.summary()}'
    calls=[];instantiate=life.instantiate
    life.instantiate=lambda *args,**kwargs:calls.append(1)
    runtime.invalidate();runtime.refresh(True);life.instantiate=instantiate
    assert not calls,f'{label}: rejected recipe retried'
    assert runtime.tick()==1/30,f'{label}: scheduler stalled'
    bpy.data.objects.remove(slot,do_unlink=True);bpy.data.objects.remove(copy,do_unlink=True);life._rejected.clear();faults.clear()

# 3. Corrupt JSON in a recipe is also contained.
copy=group.controller.copy();c.scene.collection.objects.link(copy);copy['beam_group_recipe']='{not json'
c.view_layer.update();runtime.invalidate();runtime.refresh(True)
assert any(copy.name in line for line in faults.summary())
bpy.data.objects.remove(copy,do_unlink=True);life._rejected.clear();faults.clear()

# 4. A valid native copy still becomes a complete independent group.
copy=group.controller.copy();c.scene.collection.objects.link(copy);c.view_layer.update()
before=len(c.scene.ps_study.blend_groups);runtime.invalidate();runtime.refresh(True)
assert len(c.scene.ps_study.blend_groups)==before+1 and not faults.summary()
print('RESILIENCE PASS: timers retry and recover, failed group copies keep their objects and stop retrying')
addon.unregister()
