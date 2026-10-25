"""Upgrade the existing training scene; validate exercises in a disposable profile."""
import bpy,sys,json,traceback,shutil,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,analysis_runtime,study_views,study_reporting,blend_groups,reverse_mapping,inverse_solver,screen_objects,study_data
out=root/'output/pdf/onboarding-0.13';state={};report={}
def fail():
 t=traceback.format_exc();print(t,flush=True);(out/'FAIL.txt').write_text(t);bpy.ops.wm.quit_blender()
def load():
 try:
  assert Path(bpy.utils.user_resource('CONFIG')).resolve()==(root/'work/onboarding-013/config').resolve()
  addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'output/pdf/onboarding-0.12/Beam_Training_Project.blend'),load_ui=False);bpy.app.timers.register(run,first_interval=1)
 except Exception:fail()
def run():
 try:
  c=bpy.context;s=c.scene.ps_study;a=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in a.regions if r.type=='WINDOW')
  with c.temp_override(area=a,region=region):
   wall=bpy.data.objects['SCR001'];p=bpy.data.objects['PJ02'];block=bpy.data.objects['TRAINING_Occluder'];g=s.blend_groups[0]
   def select(obj):screen_objects.select(c,obj);study_data.sync_selection(c)
   def refresh():c.view_layer.update();runtime.refresh(True)
   def analyse(mode='DENSITY',receiver=wall):
    s.analysis_receiver=receiver;s.analysis_mode=mode;refresh();assert bpy.ops.beam.analyse()=={'FINISHED'};return analysis_runtime.CACHE[c.scene.as_pointer()]['statistics'].copy()
   # Upgrade the original starting project before exercise modifications.
   c.scene.cursor.location=(0,-6,0);assert bpy.ops.beam.add_observer()=={'FINISHED'};viewer=s.analysis_observer;viewer.beam_observer.eye_height=1.65
   s.revision='0.13 training';s.analysis_receiver=wall;s.analysis_scope='GROUP';s.analysis_detail='2048'
   source=s.views[4].camera
   for mode in ('ILLUMINANCE','DISTANCE','ACUITY'):
    v=s.views.add();v.uuid=str(__import__('uuid').uuid4());v.name=mode.title();v.camera=source.copy();v.camera.data=source.data.copy();source.users_collection[0].objects.link(v.camera);v.resolution_x=1600;v.resolution_y=1000;v.analysis_overlay=mode;v.include_grids=False;v.include_frustums=False;v.include_labels=False;v.include_projected_identifiers=False
   select(p);s.analysis_show=False;refresh();bpy.data.images['Training UV Chart'].pack();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam_Training_Project.blend'))
   # Exercise 1–7: module/context, move, ratio, inverse solve, overlap/reflow.
   for name in ('PROJECTOR','SCREEN','GROUP','VIEW','EXPORT'):s.inspector=name
   select(p);assert s.active_projector==p;old=p.location.copy();p.location.x+=1;refresh();assert (p.location-old).length>.9;p.location=old
   p.ps.throw_ratio=1.2;refresh();assert abs(runtime.CACHE[p.as_pointer()]['metrics'].width-5.3333)<.03
   p.ps.solve_by='LENS';inverse_solver.solve(c,p,'WIDTH',6);refresh();assert abs(runtime.CACHE[p.as_pointer()]['metrics'].width-6)<.01
   p.ps.throw_ratio=1;g.overlap_h=15;select(g.controller);assert bpy.ops.beam.reflow()=={'FINISHED'};refresh();report['1-7']='PASS modules, context, movement/reset, ratio, inverse solve, overlap and reflow'
   report['density_before']=analyse();block.location.x=0;refresh();assert analysis_runtime.CACHE[c.scene.as_pointer()]['stale'];report['density_after']=analyse();assert report['density_after']['coverage_percent']<report['density_before']['coverage_percent']
   report['stretch_flat']=analyse('STRETCH');report['stretch_curved']=analyse('STRETCH',bpy.data.objects['TRAINING_Curved_Receiver']);assert report['stretch_curved']['max_anisotropy']>1
   s.analysis_show=False;s.reverse_receiver=wall;select(wall);wall.beam_reverse.source='GROUP';wall.beam_reverse.group_uuid=g.uuid
   reverse_mapping.enable(c,wall)
   for mode in ('COVERED','DIM','HIDDEN','OVERLAP'):wall.beam_reverse.mode=mode;reverse_mapping.refresh_gpu()
   reverse_mapping.disable(wall);report['8-13']='PASS density/stale/occlusion, flat and curved Stretch, four Reverse Mapping modes and restore'
   # New exercises: illuminate, distance, closer/farther Observer, threshold.
   block.location.x=-9;report['illuminance_before']=analyse('ILLUMINANCE');block.location.x=0;report['illuminance_after']=analyse('ILLUMINANCE');assert report['illuminance_after']['illuminance_average_lux']<report['illuminance_before']['illuminance_average_lux']
   s.illuminance_scale='FIXED';s.illuminance_max=1000;assert not analysis_runtime.CACHE[c.scene.as_pointer()]['stale'];s.illuminance_scale='AUTO'
   report['distance_before']=analyse('DISTANCE');old=p.matrix_world.copy();p.location.y-=1;report['distance_after']=analyse('DISTANCE');assert report['distance_before']['distance_average_m']!=report['distance_after']['distance_average_m'];p.matrix_world=old
   viewer.location.y=-2;report['acuity_near']=analyse('ACUITY');viewer.location.y=-12;report['acuity_far']=analyse('ACUITY');assert report['acuity_near']['acuity_average_arcmin']>report['acuity_far']['acuity_average_arcmin'];viewer.location.y=-6;viewer.beam_observer.threshold=.7;report['acuity_threshold']=analyse('ACUITY');viewer.beam_observer.threshold=1
   report['19-21']='PASS illuminance blocker/fixed range, projector distance movement, Observer distance and threshold'
   # Export every saved camera; views retain framing, not receiver configuration.
   analyse();s.show_frustums=False;s.show_outputs=False
   for v in s.views:
    assert v.camera;study_views.export_view(c,v,out/(v.name.replace(' ','_')+'.png'),a)
   assert bpy.ops.ps.export(filepath=str(out/'Beam_projectors.csv'))=={'FINISHED'}
   assert bpy.ops.beam.export_designer(filepath=str(out/'Beam_Designer.csv'))=={'FINISHED'}
   dest=out/'Training_Study_Package'
   if dest.exists():shutil.rmtree(dest)
   data=study_reporting.export(c,dest,True,a);study_reporting.validate(data);assert len(data['views'])==9
   report['14-18']='PASS nine saved cameras/export, Density sidecar, both CSVs and Study Package'
   (out/'exercise-results.json').write_text(json.dumps(report,indent=2))
   # Native current-build screenshots for all new modes and Observer setup.
   state.update(area=a,region=region,phase=0)
  bpy.app.timers.register(capture,first_interval=.5)
 except Exception:fail()
def capture():
 try:
  c=bpy.context;s=c.scene.ps_study;i=state['phase'];modes=('DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY')
  if i==len(modes):print('ONBOARDING 0.13 TRAINING PASS',flush=True);bpy.ops.wm.quit_blender();return
  with c.temp_override(area=state['area'],region=state['region']):
   s.inspector='PROJECTOR';screen_objects.select(c,bpy.data.objects['PJ02']);s.analysis_mode=modes[i];s.analysis_show=True
   # Reuse unchanged analysis; actual scene/inspector screen pixels, not mockups.
   bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
   bpy.ops.screen.screenshot(filepath=str(out/'screenshots/source'/f'{modes[i].lower()}-ui.png'))
  state['phase']+=1;return .5
 except Exception:fail()
bpy.app.timers.register(load,first_interval=1)
