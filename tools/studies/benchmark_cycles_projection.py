"""Small reproducible CPU benchmark; not a production venue performance claim."""
import bpy,sys,time,json,statistics,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import projection_study as addon
from projection_study import cycles_projection as cp
from projection_study.projector_object import create
addon.register()
version='.'.join(map(str,bpy.app.version))
fixture=ROOT/f'work/issue-14/render-tests-{version}/Beam-Cycles-Alpha-Test.blend'
bpy.ops.wm.open_mainfile(filepath=str(fixture));s=bpy.context.scene
bpy.data.objects['Cut-out cloth'].hide_render=True
p=next(o for o in s.objects if o.ps.is_projector);p.ps.output_mode='SOLID';p.ps.show_projected_identifier=False
s.render.resolution_x=256;s.render.resolution_y=160;s.cycles.samples=8;s.cycles.use_denoising=False;s.cycles.device='CPU'
s.render.use_persistent_data=True
results={'blender':bpy.app.version_string,'device':'CPU','resolution':[256,160],'samples':8,'trials':3,'cases':[]}
for count in (1,4,16):
    while len([o for o in s.objects if o.ps.is_projector])<count:create(bpy.context,source=p)
    bpy.context.view_layer.update();cp.sync(s)
    helpers=[o for o in s.objects if o.get(cp.TAG)]
    start=time.perf_counter()
    for _ in range(100):cp.sync(s)
    idle=(time.perf_counter()-start)/100
    for cone in ('tight','wide'):
        if cone=='wide':
            for o in helpers:
                old=o.data.spot_size;o.data.spot_size=math.pi-.0001
                o.data.energy*= (1-math.cos(o.data.spot_size/2))/(1-math.cos(old/2))
        durations=[]
        for trial in range(4):
            start=time.perf_counter();bpy.ops.render.render();durations.append(time.perf_counter()-start)
        results['cases'].append({'lights':count,'cone':cone,'initial_seconds':durations[0],
            'warm_median_seconds':statistics.median(durations[1:]),'warm_trials':durations[1:],
            'idle_sync_seconds':idle,'shared_groups':len([g for g in bpy.data.node_groups if g.get(cp.TAG)])})
    cp._signatures.clear();cp.sync(s)
path=ROOT/f'work/issue-14/benchmark-{version}.json';path.write_text(json.dumps(results,indent=2));print(json.dumps(results))
addon.unregister()
