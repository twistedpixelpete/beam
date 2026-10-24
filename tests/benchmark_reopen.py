"""Fresh-process save/reopen benchmark; includes file load and Beam rebuild."""
import bpy,sys,time,json,statistics
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime
addon.register();folder=root/'work/production/benchmark';data=json.loads((folder/'timings.json').read_text())
for count in (16,32):
 times=[]
 for _ in range(3):
  start=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(folder/f'venue-{count}.blend'));runtime.refresh(True);times.append(time.perf_counter()-start)
  assert len([o for o in bpy.context.scene.objects if o.ps.is_projector])==count
  assert len(bpy.context.scene.ps_study.blend_groups)==count//4
 data['measurements'].append(dict(projectors=count,operation='reopen_and_rebuild',median_seconds=statistics.median(times),max_seconds=max(times),runs=times))
(folder/'timings.json').write_text(json.dumps(data,indent=2));print('PASS reopen 16/32 projectors and group persistence')
addon.unregister()
