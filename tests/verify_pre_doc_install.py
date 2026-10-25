"""Real extension ZIP installation and fresh-process first-use acceptance.
Use isolated BLENDER_USER_CONFIG and BLENDER_USER_EXTENSIONS. Phases: install, use, reopen.
"""
import bpy,sys,importlib,json,traceback,tomllib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'work/pre-doc-install';out.mkdir(exist_ok=True)
assert Path(bpy.utils.user_resource('CONFIG')).resolve()==(out/'config').resolve(), 'Refuse non-isolated preferences'
assert all(str(out/'extensions') in r.directory for r in bpy.context.preferences.extensions.repos if r.module in {'user_default','blender_org'}), 'Refuse non-isolated extension repositories'
phase=sys.argv[-1];version=tomllib.loads((root/'projection_study/blender_manifest.toml').read_text())['version']
module='bl_ext.user_default.projection_study';checks=[]
def fail():
 text=traceback.format_exc();print(text,flush=True);(out/(phase+'-result.txt')).write_text(text);bpy.ops.wm.quit_blender()
def native():
 a=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');r=next(r for r in a.regions if r.type=='WINDOW');return bpy.context.temp_override(area=a,region=r)
def install():
 try:
  before=tuple(bpy.context.preferences.themes[0].user_interface.wcol_regular.inner)
  assert bpy.ops.extensions.package_install_files(filepath=str(root/f'dist/beam-{version}.zip'),repo='user_default',enable_on_install=True)=={'FINISHED'}
  assert module in bpy.context.preferences.addons
  assert tuple(bpy.context.preferences.themes[0].user_interface.wcol_regular.inner)==before
  bpy.ops.wm.save_userpref();(out/'install-result.txt').write_text('PASS installed ZIP through Install from Disk, enabled extension, unchanged theme, saved isolated preferences')
  bpy.ops.wm.quit_blender()
 except:fail()
def refresh():bpy.context.view_layer.update();runtime.refresh(True)
def select(o):screen_objects.select(bpy.context,o);study_data.sync_selection(bpy.context)
def run():
 global runtime,study_data,screen_objects,reverse,analysis,views
 try:
  assert module in bpy.context.preferences.addons
  addon=importlib.import_module(module);runtime=importlib.import_module(module+'.runtime');study_data=importlib.import_module(module+'.study_data');screen_objects=importlib.import_module(module+'.screen_objects');reverse=importlib.import_module(module+'.reverse_mapping');analysis=importlib.import_module(module+'.analysis_runtime');views=importlib.import_module(module+'.study_views')
  assert 'work/pre-doc-install/extensions' in str(Path(addon.__file__))
  if phase=='reopen':
   bpy.ops.wm.open_mainfile(filepath=str(out/'Baseline.blend'));bpy.app.timers.register(reopened,first_interval=2);return
  with native():
   c=bpy.context;s=c.scene.ps_study
   for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
   c.scene.unit_settings.system='METRIC';c.scene.unit_settings.scale_length=1
   before=tuple(c.preferences.themes[0].user_interface.wcol_regular.inner)
   bpy.ops.beam.workspace();assert tuple(c.preferences.themes[0].user_interface.wcol_regular.inner)==before
  bpy.app.timers.register(first_use,first_interval=1)
 except:fail()
def first_use():
 try:
  with native():
   c=bpy.context;s=c.scene.ps_study;s.project_name='Documentation Baseline';s.venue='Disposable verification';s.display_units='m'
   assert c.workspace.get('beam_workspace')
   count=len(bpy.data.workspaces);bpy.ops.beam.workspace();assert len(bpy.data.workspaces)==count
   c.window.workspace=bpy.data.workspaces['Layout'];bpy.ops.beam.workspace();assert c.workspace.get('beam_workspace')
   d=c.scene.beam_screen_draft;d.width=16;d.height=4;d.aspect='FREE';assert bpy.ops.beam.screen_create()=={'FINISHED'};wall=c.object;wall.location=(0,10,-2)
   assert wall.beam_screen.identifier=='SCR001'
   bpy.ops.ps.add();pj=c.object;pj.location=(0,0,0);c.scene.cursor.location=(0,10,0);assert bpy.ops.ps.aim(mode='CURSOR')=={'FINISHED'}
   pj.ps.resolution_x=1920;pj.ps.resolution_y=1080;pj.ps.throw_ratio=1.5;pj.ps.output_mode='GRID';refresh();assert runtime.CACHE[pj.as_pointer()]['hit'];assert abs(runtime.CACHE[pj.as_pointer()]['metrics'].width-10/1.5)<.001
   members=[pj]
   for x in (-5,5):bpy.ops.ps.duplicate();o=c.object;o.location.x=x;members.append(o)
   select(pj)
   for o in members:o.select_set(True)
   assert bpy.ops.beam.create_group(from_selection=True)=={'FINISHED'}
   # Move the first group clear of the screen before creating an independent Auto Blend.
   g=s.blend_groups[0];g.controller.location.x+=30;refresh();select(wall)
   assert bpy.ops.beam.plan_new(use_template=False,count=3,overlap_h=200)=={'FINISHED'};assert bpy.ops.beam.reflow()=={'FINISHED'}
   g=s.blend_groups[-1];pj=g.members[0].projector
   # Exclude the displaced practice group from exports and active coverage.
   for o in members:o.ps.active=False
   select(pj);select(wall);assert s.active_projector==pj
   select(pj);s.pin_context=True;select(wall);assert s.active_projector==pj and s.inspector=='PROJECTOR' and s.reverse_receiver==wall
   s.pin_context=False;select(g.members[1].projector);assert s.active_projector==g.members[1].projector
   rv=c.space_data.region_3d;from mathutils import Vector
   rv.view_location=(0,7,0);rv.view_distance=24;rv.view_rotation=Vector((-12,22,-10)).to_track_quat('-Z','Y');rv.update()
   v=views.create_view(c,'Overview');v.resolution_x=1200;v.resolution_y=750
   s.analysis_receiver=wall;s.analysis_scope='GROUP'
   for detail in ('512','2048','8192'):
    s.analysis_detail=detail;assert bpy.ops.beam.analyse()=={'FINISHED'};assert not analysis.CACHE[c.scene.as_pointer()]['stale']
   for mode in ('DENSITY','STRETCH'):
    s.analysis_mode=mode;v.analysis_overlay=mode;views.export_view(c,v,out/(mode+'.png'),c.area)
   pj.location.x+=.01;refresh();assert analysis.CACHE[c.scene.as_pointer()]['stale'];bpy.ops.beam.analyse();v.analysis_overlay='NONE'
   select(wall);bpy.ops.beam.screen_action(action='PATTERN');s.reverse_receiver=wall;wall.beam_reverse.source='ALL';original=list(wall.data.materials)
   assert bpy.ops.beam.receiver_action(action='ENABLE')=={'FINISHED'}
   for source in ('ACTIVE','GROUP','ALL'):
    wall.beam_reverse.source=source;wall.beam_reverse.group_uuid=g.uuid
    for mode in ('COVERED','DIM','HIDDEN','OVERLAP'):
     wall.beam_reverse.mode=mode;refresh();reverse.refresh_gpu();assert not reverse._error
   assert bpy.ops.beam.receiver_action(action='DISABLE')=={'FINISHED'};assert list(wall.data.materials)==original
   select(pj);s.pin_context=True;select(wall)
   assert bpy.ops.ps.export(filepath=str(out/'Mapping-Matter.csv'))=={'FINISHED'}
   assert bpy.ops.beam.export_designer(filepath=str(out/'Designer.csv'))=={'FINISHED'}
   assert bpy.ops.ps.export_json(filepath=str(out/'Beam.json'))=={'FINISHED'}
   bpy.ops.beam.analyse()
   import shutil
   if (out/'Study-Package').exists():shutil.rmtree(out/'Study-Package')
   assert bpy.ops.beam.study_package(filepath=str(out/'Study-Package'))=={'FINISHED'}
   assert bpy.ops.beam.apply_theme()=={'FINISHED'}
   theme=importlib.import_module(module+'.ui_theme');backup=(theme.folder()/'previous.xml').read_bytes();bpy.ops.beam.apply_theme();assert (theme.folder()/'previous.xml').read_bytes()==backup
   s.pin_context=False;select(pj)
   bpy.ops.wm.save_as_mainfile(filepath=str(out/'Baseline.blend'));bpy.ops.wm.save_userpref()
   (out/'use-result.txt').write_text('PASS installed extension: blank-scene workflow, workspace reuse, screen/projectors/manual group/Auto Blend/Reflow, selected-active-pinned-receiver, Study View, 3 sample counts/2 modes/stale cache, 3 Reverse Mapping sources x 4 modes/material restoration, 2 CSVs/JSON/package, Apply twice, save')
  bpy.ops.wm.quit_blender()
 except:fail()
def reopened():
 try:
  with native():
   c=bpy.context;s=c.scene.ps_study
   assert c.workspace.get('beam_workspace');n=len(bpy.data.workspaces);bpy.ops.beam.workspace();assert len(bpy.data.workspaces)==n
   assert not analysis.CACHE;assert s.active_projector and s.analysis_receiver
   theme=importlib.import_module(module+'.ui_theme');assert theme._ready;assert bpy.ops.beam.restore_theme()=={'FINISHED'}
   assert len(s.blend_groups)==2 and len(s.views)==1
   (out/'reopen-result.txt').write_text('PASS fresh-process restart: extension enabled, one Beam workspace reused, active context/receivers/views/groups persisted, analysis transient, Restore Previous Theme available')
  bpy.ops.wm.quit_blender()
 except:fail()
bpy.app.timers.register(install if phase=='install' else run,first_interval=2)
