"""Long disposable venue workflow; reacquire RNA after Undo and collection edits."""
import bpy,sys,time,math,json,statistics,traceback,gc,resource
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,projector_object,blend_groups,group_lifecycle,screen_objects,analysis_runtime,reverse_mapping,study_views,study_reporting,export_designer,export_disguise,inverse_solver,auto_layout,projection_renderer
out=root/'work/hardening/soak';out.mkdir(parents=True,exist_ok=True)
report={}
def refresh():bpy.context.view_layer.update();runtime.refresh()
def counts():
 return {k:len(getattr(bpy.data,k)) for k in ('objects','meshes','materials','images','node_groups','cameras')}
def handler_counts():return {k:len(getattr(bpy.app.handlers,k)) for k in ('depsgraph_update_post','load_post','undo_post','redo_post')}
def snapshot():
 c=bpy.context;s=c.scene.ps_study
 return dict(projectors=sorted((o.ps.uuid,o.ps.optics_model,o.ps.optics_lens) for o in projector_object.projectors(c.scene)),groups=sorted(g.uuid for g in s.blend_groups),screens=sorted(o.beam_screen.uuid for o in c.scene.objects if o.beam_screen.is_screen),views=[(v.uuid,v.analysis_overlay) for v in s.views],metadata=[s.project_name,s.venue,s.revision],analysis=[s.analysis_detail,s.analysis_mode,s.analysis_scope],pin=s.pin_context,active_projector=s.active_projector.ps.uuid if s.active_projector else None,inspector=s.inspector)
def run():
 try:
  c=bpy.context
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with c.temp_override(area=area,region=region):
   s=c.scene.ps_study;s.project_name='Internal beta production soak';s.venue='32-projector conference venue';s.revision='QA';s.display_units='m';s.shadow_resolution='512'
   for o in projector_object.projectors(c.scene):o.ps.optics_model='panasonic_rz990';o.ps.optics_lens='panasonic_dle150';o.ps.lumens=9400
   refresh();g=s.blend_groups[0];pj=g.members[0].projector;s.active_projector=pj;s.active_screen=g.layout_screen
   # Native Undo/Redo of a real inverse solve, then reacquire all RNA.
   screen_objects.select(c,pj);pj.ps.solve_by='LENS';old=pj.ps.throw_ratio
   bpy.ops.ed.undo_push(message='Before constrained solve');assert bpy.ops.beam.solve('EXEC_DEFAULT',True,field='RATIO',value=1.5)=={'FINISHED'}
   bpy.ops.ed.undo();refresh();assert abs(c.scene.ps_study.active_projector.ps.throw_ratio-old)<1e-6
   bpy.ops.ed.redo();refresh();assert abs(c.scene.ps_study.active_projector.ps.throw_ratio-1.5)<1e-6
   s=c.scene.ps_study;g=s.blend_groups[0];pj=g.members[0].projector
   # Duplicate projector; repair identity; remove disposable copy.
   screen_objects.select(c,pj);old_ids={o.ps.uuid for o in projector_object.projectors(c.scene)}
   bpy.ops.object.duplicate();duplicate=c.object;refresh();refresh();assert duplicate.ps.uuid not in old_ids
   bpy.data.objects.remove(duplicate,do_unlink=True);refresh()
   # Group duplicate creates ordinary independent members, then remove our copy.
   group_ids={x.uuid for x in s.blend_groups};copy=group_lifecycle.duplicate(s.blend_groups[0],c);copy_id=copy.uuid;members=list(blend_groups.member_objects(copy));controller=copy.controller
   assert copy_id not in group_ids and len(members)==4
   for o in members+[controller]:bpy.data.objects.remove(o,do_unlink=True)
   refresh()
   # Explicit reflow and transactional auto layout, on existing real optics.
   g=s.blend_groups[0];s.active_projector=g.members[0].projector;s.active_screen=g.layout_screen;screen_objects.select(c,g.controller)
   assert bpy.ops.beam.group_action(action='APPLY')=={'FINISHED'};refresh()
   before={o.as_pointer() for o in c.scene.objects}
   options=SimpleNamespace(use_template=True,layout_type='HORIZONTAL',count=4,columns=4,rows=1,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=8,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
   # Existing projector housings may block a new co-located layout; failure must be atomic.
   try:created,_=auto_layout.create(c,options)
   except ValueError:assert {o.as_pointer() for o in c.scene.objects}==before
   else:
    for o in list(c.scene.objects):
     if o.as_pointer() not in before:bpy.data.objects.remove(o,do_unlink=True)
   refresh();assert len(list(projector_object.projectors(c.scene)))==32
   s=c.scene.ps_study;s.pin_context=True;s.analysis_receiver=s.blend_groups[0].layout_screen
   # Warm renderer and analysis resources before measuring retention.
   objects=list(projector_object.projectors(c.scene));analysis_runtime.analyse(c,s.analysis_receiver,objects,512);reverse_mapping.refresh_gpu()
   view=s.views[0];study_views.export_view(c,view,out/'warm.png',area)
   baseline=counts();handlers=handler_counts();times=[];batches=[]
   for i in range(360):
    start=time.perf_counter();objects=list(projector_object.projectors(c.scene));o=objects[i%32]
    o.location.x+=.0001 if i%2 else -.0001;o.rotation_euler.z+=.00001 if i%2 else -.00001
    if i%3==0:s.blend_groups[(i//3)%len(s.blend_groups)].controller.location.x+=.0001
    if i%6==0:
     g=s.blend_groups[(i//6)%len(s.blend_groups)];g.overlap_h=26+(i%5)*.1
    if i%12==0:o.ps.optics_lens='panasonic_dle105' if o.ps.optics_lens=='panasonic_dle150' else 'panasonic_dle150'
    refresh();times.append(time.perf_counter()-start)
    if i%30==0:
     s.analysis_receiver=s.blend_groups[(i//30)%len(s.blend_groups)].layout_screen
     r=analysis_runtime.analyse(c,s.analysis_receiver,objects,512);assert not r['stale']
     view.analysis_overlay='DENSITY' if i%60==0 else 'STRETCH';s.analysis_mode=view.analysis_overlay
     study_views.export_view(c,view,out/f'analysis-{i:03d}.png',area)
     reverse_mapping.refresh_gpu();gc.collect();batches.append(counts())
   report.update(edits=360,group_moves=120,overlap_changes=60,lens_changes=30,analyses=12,analysis_exports=12,before=baseline,after=counts(),checkpoints=batches,first60_median=statistics.median(times[:60]),last60_median=statistics.median(times[-60:]),max_update_seconds=max(times),max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
   assert handler_counts()==handlers and bpy.app.timers.is_registered(runtime.tick)
   for key in baseline:assert counts()[key]<=baseline[key]+2,(key,baseline,counts())
   # Return all real lenses to valid range before final technical exports.
   for o in objects:o.ps.optics_lens='panasonic_dle150';o.ps.throw_ratio=1.4
   refresh();s.analysis_receiver=s.blend_groups[0].layout_screen;analysis_runtime.analyse(c,s.analysis_receiver,objects,2048)
   assert bpy.ops.ps.view_study(index=0)=={'FINISHED'};assert bpy.ops.ps.view_study(action='EXIT')=={'FINISHED'}
   assert bpy.ops.ps.export(filepath=str(out/'Mapping-Matter.csv'))=={'FINISHED'}
   assert bpy.ops.beam.export_designer(filepath=str(out/'Designer.csv'))=={'FINISHED'}
   package=out/'Study-Package'
   if package.exists():
    import shutil;shutil.rmtree(package)
   study_reporting.export(c,package,True,area)
   before=snapshot();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Soak.blend'));bpy.ops.wm.open_mainfile(filepath=str(out/'Beam-Soak.blend'));refresh()
   assert snapshot()==before;assert not analysis_runtime.CACHE
   ids=[o.ps.uuid for o in projector_object.projectors(bpy.context.scene)];assert len(set(ids))==32
   report.update(status='PASS',save_reopen=True,undo_redo=True,uuid_unique=True,handlers_stable=True)
   (out/'result.json').write_text(json.dumps(report,indent=2));print('SOAK PASS',flush=True)
 except Exception:
  report.update(status='FAIL',error=traceback.format_exc());(out/'result.json').write_text(json.dumps(report,indent=2));print(report['error'],flush=True)
 addon.unregister();gc.collect()
 bpy.app.timers.register(lambda:bpy.ops.wm.quit_blender() and None,first_interval=.2)
def setup():
 addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'work/production/benchmark/venue-32.blend'));bpy.app.timers.register(run,first_interval=1)
bpy.app.timers.register(setup,first_interval=2)
