import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects,projector_object,runtime,inverse_solver,auto_layout
from types import SimpleNamespace
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
s=c.scene.ps_study;s.display_units='m';d=c.scene.beam_screen_draft;d.width=6;d.height=3.375;d.aspect='FREE';d.origin='BOTTOM'
wall=screen_objects.create(c,d);wall.location=(0,8,-1.6875);p=projector_object.create(c);p.ps.resolution_x=1920;p.ps.resolution_y=1080;p.ps.throw_ratio=1
c.view_layer.update();runtime.refresh(True);m=runtime.CACHE[p.as_pointer()]['metrics'];assert abs(m.distance-8)<1e-5 and abs(m.width-8)<1e-5
inverse_solver.solve(c,p,'WIDTH',6);c.view_layer.update();runtime.refresh(True);assert abs(p.ps.throw_ratio-4/3)<1e-5
wall.beam_screen.width=18;screen_objects.update(c,wall)
s.active_projector=p;s.active_screen=wall
options=SimpleNamespace(use_template=True,layout_type='HORIZONTAL',count=3,columns=3,rows=1,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=8,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
g,result=auto_layout.create(c,options);assert len(g.members)==3
print('QUICK START 0.13 PASS: screen, 8m target, 6m inverse width, 18m three-projector layout')
addon.unregister()
