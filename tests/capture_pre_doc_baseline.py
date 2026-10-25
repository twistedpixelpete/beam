"""Reproducible documentation capture scene, not a training project."""
import bpy,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,study_data,screen_objects,analysis_runtime,reverse_mapping
out=root/'examples/manual-baseline';state={}
def native():
 a=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');r=next(r for r in a.regions if r.type=='WINDOW');return bpy.context.temp_override(area=a,region=r)
def fail():
 (out/'capture-result.txt').write_text(traceback.format_exc());bpy.ops.wm.quit_blender()
def setup():
 try:
  addon.register();bpy.ops.wm.open_mainfile(filepath=str(root/'examples/production/Beam-PATCH-fixture.blend'));bpy.app.timers.register(workspace,first_interval=1)
 except:fail()
def workspace():
 try:
  with native():
   bpy.ops.beam.workspace();bpy.ops.beam.apply_theme()
  bpy.app.timers.register(capture,first_interval=1)
 except:fail()
def capture():
 try:
  c=bpy.context;s=c.scene.ps_study
  with native():
   if not state:
    s.project_name='Documentation Baseline';s.revision='01';s.show_study_cameras=False;s.pin_context=False
    wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);s.analysis_receiver=wall;s.analysis_scope='ALL';s.analysis_detail='2048'
    pj=next(o for o in c.scene.objects if o.ps.is_projector);screen_objects.select(c,pj);study_data.sync_selection(c)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Documentation-Baseline.blend'))
    state['phase']='analysis';bpy.ops.beam.analyse();return 1
   for a in c.screen.areas:a.tag_redraw()
   bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
   name=state['phase'];bpy.ops.screen.screenshot(filepath=str(out/(name+'.png')))
   a=next(a for a in c.screen.areas if a.type=='PROPERTIES');r=next(r for r in a.regions if r.type=='WINDOW')
   with c.temp_override(area=a,region=r):bpy.ops.screen.screenshot_area(filepath=str(out/(name+'-inspector.png')))
   if name=='analysis':
    s.analysis_mode='STRETCH';state['phase']='stretch';return 1
   if name=='stretch':
    analysis_runtime.CACHE.clear();s.analysis_show=False
    # Expose real optics by clicking its native disclosure at the known current layout.
    state['phase']='optics-before';return 1
   if name=='optics-before':
    # Position measured from this capture at 3600x2084; scale to native window.
    x=3200;y=2084-1342
    for typ,val in [('MOUSEMOVE','NOTHING'),('LEFTMOUSE','PRESS'),('LEFTMOUSE','RELEASE')]:c.window.event_simulate(type=typ,value=val,x=x,y=y)
    state['phase']='optics';return 1
   if name=='optics':
    next(a for a in c.screen.areas if a.type=='VIEW_3D').spaces.active.show_region_toolbar=False;state['phase']='hidden-toolbar';return 1
   if name=='hidden-toolbar':
    (out/'capture-result.txt').write_text('PASS native analysis, optics disclosure and hidden-toolbar captures; saved real-optics baseline scene')
    addon.unregister();bpy.ops.wm.quit_blender();return
 except:fail()
bpy.app.timers.register(setup,first_interval=2)
