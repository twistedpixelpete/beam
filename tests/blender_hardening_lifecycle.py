"""Real optics group copying is order-independent and transactional."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,group_lifecycle as life
addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'examples/production/Beam-PATCH-fixture.blend'));c=bpy.context;runtime.refresh(True)
g=c.scene.ps_study.blend_groups[0];source=g.controller;old={o.ps.uuid for o in c.scene.objects if o.ps.is_projector}
copy=life.duplicate(g,c);runtime.refresh(True)
assert all(m.projector.ps.optics_model=='panasonic_rz990' and m.projector.ps.optics_lens=='panasonic_dle150' and m.projector.ps.uuid not in old for m in copy.members)
recipe=json.loads(source['beam_group_recipe']);recipe['members'][1]['settings']['optics_lens']='unavailable_lens'
def counts():return tuple(len(getattr(bpy.data,k)) for k in ('objects','meshes','cameras','images','materials'))+(len(c.scene.ps_study.blend_groups),)
before=counts();active=c.view_layer.objects.active
try:life.instantiate(recipe,c,source)
except TypeError:pass
else:raise AssertionError('Invalid dependent lens accepted')
assert counts()==before,(before,counts());assert c.view_layer.objects.active==active
print('HARDENING LIFECYCLE PASS: sourced model before lens, independent UUIDs, complete rollback on invalid recipe')
addon.unregister()
