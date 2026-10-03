"""Background integration: display-ray clipping cannot change technical geometry."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,target_raycast,frustum_helpers
from projection_study.projector_object import create
addon.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.scale_length=.01
unit=scene.unit_settings.scale_length
p=create(bpy.context);p.ps.throw_ratio=1;p.ps.preview_distance=20
# A sloping wall intersects corners at distinct depths; the centre hits 10 m.
mesh=bpy.data.meshes.new('Angled receiver');mesh.from_pydata([Vector(v)/unit for v in [(-20,6,-20),(20,14,-20),(20,14,20),(-20,6,20)]],[],[(0,1,2,3)])
wall=bpy.data.objects.new('Angled receiver',mesh);scene.collection.objects.link(wall)
def refresh():
    bpy.context.view_layer.update();target_raycast.invalidate();runtime.refresh(True)
    return runtime.CACHE[p.as_pointer()]
r=refresh()
assert abs(r['metrics'].distance-10)<1e-5
for fallback,endpoint in zip(r['corners'],r['helper_corners']):
    hit=target_raycast.cast(r['origin'],(fallback-r['origin']).normalized())
    assert hit and (hit[0]-endpoint).length*unit<1e-5
assert max(v.y for v in r['helper_corners'])-min(v.y for v in r['helper_corners'])>100
assert all(v.y>max(c.y for c in r['helper_corners']) for v in r['beam_corners'])
# Near object on exactly one corner ray must win over the farther wall.
near=r['helper_corners'][0]*.5
bpy.ops.mesh.primitive_cube_add(size=100,location=near);block=bpy.context.object
r=refresh(); assert (r['helper_corners'][0]-r['origin']).length<(near-r['origin']).length
assert abs(r['metrics'].distance-10)<1e-5
# Disabling the display endpoint calculation leaves all technical records intact.
original=frustum_helpers.endpoints
frustum_helpers.endpoints=lambda origin,corners:[v.copy() for v in corners]
uncut=refresh();frustum_helpers.endpoints=original
cut=refresh()
for key in ('metrics','hit','origin','rotation','corners','centre','beam_corners','beam_depth','slant'):
    assert cut[key]==uncut[key],key
assert cut['helper_corners']!=uncut['helper_corners']
# Receiver motion and visibility invalidate the display cache; misses use fallback.
wall.location.y+=200;r=refresh();assert r['helper_corners'][1].y>1000
wall.hide_set(True);block.hide_set(True);r=refresh()
assert r['hit'] is None and r['metrics'].distance==p.ps.preview_distance
assert r['helper_corners']==r['corners']
assert all(abs(v.y*unit-20)<1e-5 for v in r['helper_corners'])
# Partial receiver: corner miss uses nominal depth while other corners hit.
wall.hide_set(False);wall.location.y=0;wall.scale.x=.2;r=refresh()
assert r['hit'] is not None
assert sum((a-b).length<1e-5 for a,b in zip(r['helper_corners'],r['corners']))==2
print('FRUSTUM HELPERS PASS: independent first hits, nearer occluder, non-default units, movement, hidden receivers, finite misses; technical records unchanged')
addon.unregister()
