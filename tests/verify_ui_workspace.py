"""Disposable native workspace UI acceptance and screenshots. No user scene edits."""
import bpy,sys,traceback,json,time
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects as screens,projector_object,runtime,auto_layout,study_data,ui_context,ui_workspace,blend_groups,reverse_mapping,study_views
from projection_study import ui,layout_coverage
original_draw=ui.draw
def checked_draw(layout,context):
 with patch.object(runtime,'refresh',side_effect=AssertionError('Runtime refresh in panel draw')),patch.object(blend_groups,'pair_data',side_effect=AssertionError('Pair calculation in panel draw')),patch.object(layout_coverage,'report',side_effect=AssertionError('Coverage computation in panel draw')):
  if context.window_manager.beam_target.field:
   d=context.window_manager.beam_target
   assert d.projector==study_data.active(context) and d.scene==context.scene
   state["draft_drawn"]=True
  original_draw(layout,context)
ui.draw=checked_draw
themed='--beam-theme' in sys.argv
if themed:
 bpy.ops.script.execute_preset(filepath=str(root/'projection_study/themes/Beam.xml'),menu_idname='USERPREF_MT_interface_theme_presets')
out=root/('work/theme-workspace' if themed else 'work/ui-workspace');out.mkdir(parents=True,exist_ok=True);state={};checks=[]

def fail():
 text=traceback.format_exc();print(text,flush=True);(out/'result.txt').write_text(text);bpy.ops.wm.quit_blender()
def refresh():bpy.context.view_layer.update();runtime.refresh(True);study_data.sync_selection(bpy.context)
def select(obj):
 for o in bpy.context.selected_objects:o.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj;refresh()
def native():
 area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
 return bpy.context.temp_override(area=area,region=region)
def setup():
 try:
  addon.register()
  with native():
   c=bpy.context;s=c.scene
   for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
   s.ps_study.project_name='Town Hall';s.ps_study.revision='R02';s.ps_study.display_units='m'
   p=s.beam_screen_draft;p.width=16;p.height=4;p.aspect='FREE';wall=screens.create(c,p);wall.location=(0,10,0);select(wall)
   options=SimpleNamespace(use_template=False,layout_type='HORIZONTAL',count=3,columns=2,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
   group,_=auto_layout.create(c,options);pj=group.members[0].projector
   for o in blend_groups.member_objects(group):o.ps.show_centre_ray=False;o.ps.show_projected_identifier=False
   bpy.ops.mesh.primitive_cube_add(size=1,location=(0,6,-.35),scale=(24,18,.3));floor=c.object;floor.name='Venue Floor'
   bpy.ops.mesh.primitive_cube_add(size=1,location=(0,10.5,4),scale=(23,.4,8));venue=c.object;venue.name='Venue Wall'
   select(wall);bpy.ops.beam.screen_action(action='PATTERN')
   rv=c.space_data.region_3d;rv.view_location=(0,7,2);rv.view_distance=24;rv.view_rotation=Vector((-15,23,-11)).to_track_quat('-Z','Y');rv.view_perspective='PERSP';rv.update()
   view=study_views.create_view(c,'Stage overview');view.resolution_x=1000;view.resolution_y=600
   state.update(wall=wall.name,pj=pj.name,venue=venue.name,group=group.uuid,view=view.uuid,original_workspace=c.workspace.name)
   select(pj);assert s.ps_study.inspector=='PROJECTOR'
   state['old_screens']={w.name:[a.type for screen in w.screens for a in screen.areas] for w in bpy.data.workspaces}
   assert bpy.ops.beam.workspace()=={'FINISHED'}
  bpy.app.timers.register(workspace_ready,first_interval=1)
 except:fail()
def workspace_ready():
 try:
  c=bpy.context;s=c.scene;assert ui_workspace.is_beam(c)
  assert {'VIEW_3D','OUTLINER','PROPERTIES'}<={a.type for a in c.screen.areas}
  for name,areas in state['old_screens'].items():assert areas==[a.type for screen in bpy.data.workspaces[name].screens for a in screen.areas]
  with native():
   pj=bpy.data.objects[state['pj']];select(pj);refresh();before=pj.ps.throw_ratio
   bpy.ops.ed.undo_push(message='Before inline target');assert bpy.ops.beam.edit_target(field='HEIGHT')=={'FINISHED'}
   d=c.window_manager.beam_target;d.value=5
   assert pj.ps.throw_ratio==before,'Draft mutated projector'
   assert bpy.ops.beam.apply_target('EXEC_DEFAULT',True)=={'FINISHED'};refresh();assert abs(runtime.CACHE[c.scene.ps_study.active_projector.as_pointer()]['metrics'].height-5)<.001
   bpy.ops.ed.undo();refresh();assert abs(c.scene.ps_study.active_projector.ps.throw_ratio-before)<1e-6
   bpy.ops.ed.redo();refresh();assert abs(runtime.CACHE[c.scene.ps_study.active_projector.as_pointer()]['metrics'].height-5)<.001
   pj=c.scene.ps_study.active_projector;pj.ps.solve_lock_position=True;pj.ps.solve_by='POSITION';assert ui_context.restriction(pj,runtime.CACHE[pj.as_pointer()])=='Position Locked';pj.ps.solve_lock_position=False;pj.ps.solve_by='LENS'
   bpy.ops.beam.edit_target(field='WIDTH');ratio=pj.ps.throw_ratio;c.window_manager.beam_target.value=2;assert bpy.ops.beam.apply_target(cancel=True)=={'FINISHED'};assert pj.ps.throw_ratio==ratio
   c.scene.ps_study.pin_context=True;select(bpy.data.objects[state['wall']]);assert c.scene.ps_study.active_projector==pj and c.scene.ps_study.inspector=='PROJECTOR'
   c.scene.ps_study.pin_context=False;select(pj);select(bpy.data.objects[state['venue']]);assert c.scene.ps_study.active_projector==pj and c.scene.ps_study.inspector=='PROJECTOR'
   assert c.scene.ps_study.reverse_receiver.name==state['venue']
   select(pj)
  checks.extend(['Optional workspace preserves existing layouts and native editors','Inline target draft/apply/cancel and native Undo/Redo','Visible lock restriction','Pinned context and normal venue selection preserve active projector'])
  c.window.workspace=bpy.data.workspaces[state['original_workspace']];state['phase']='switch_back';bpy.app.timers.register(step,first_interval=.5)
 except:fail()
phases=['projector','inline-target','screen','blend','views','venue','reverse','export']
def capture(name):
 if name=='inline-target':
  d=bpy.context.window_manager.beam_target
  assert d.field=='HEIGHT' and d.projector==study_data.active(bpy.context) and d.scene==bpy.context.scene,(d.field,d.projector,d.scene)
 assert next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES').spaces.active.context=='SCENE','Native Outliner switched away from Beam inspector'
 for area in bpy.context.screen.areas:area.tag_redraw()
 bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
 if name=='inline-target':assert state.get('draft_drawn'),'Staged target was not drawn'
 bpy.ops.screen.screenshot(filepath=str(out/(name+'.png')))
 area=next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES');region=next(r for r in area.regions if r.type=='WINDOW')
 with bpy.context.temp_override(area=area,region=region):bpy.ops.screen.screenshot_area(filepath=str(out/(name+'-inspector.png')))
def step():
 try:
  c=bpy.context;s=c.scene
  if state['phase']=='switch_back':
   assert not ui_workspace.is_beam(c);bpy.ops.beam.workspace();state['phase']='outliner_start';return 1
  name=state['phase']
  if name=='reloaded':
   assert ui_workspace.is_beam(c);assert {'VIEW_3D','PROPERTIES','OUTLINER'}<={a.type for a in c.screen.areas}
   r=next(o for o in s.objects if o.beam_reverse.enabled);originals=[item.material for item in r.beam_reverse.slots];reverse_mapping.disable(r);assert all(slot.material in originals for slot in r.material_slots)
   props=next(a for a in c.screen.areas if a.type=='PROPERTIES');region=next(r for r in props.regions if r.type=='WINDOW')
   pj=bpy.data.objects[state['pj']];select(pj)
   with c.temp_override(area=props,region=region):
    before=c.view_layer.objects.active
    assert bpy.ops.beam.ui_action(action='FRAME')=={'FINISHED'};assert c.view_layer.objects.active==before
    assert bpy.ops.beam.ui_action(action='LOCK')=={'FINISHED'};assert all(pj.lock_location);bpy.ops.beam.ui_action(action='LOCK');assert not any(pj.lock_location)
    bpy.ops.beam.ui_action(action='PRESENTATION');bpy.ops.beam.ui_action(action='PRESENTATION')
    assert bpy.ops.ps.export_views(filepath=str(out/'export-from-inspector.png'),overwrite=True)=={'FINISHED'}
   with c.temp_override(area=props,region=region):
    wall=bpy.data.objects[state['wall']];select(wall);width=wall.beam_screen.width;wall.beam_screen.width=width+1
    assert bpy.ops.beam.screen_action(action='UPDATE')=={'FINISHED'};c.view_layer.update();assert abs(wall.dimensions.x-(width+1))<.001
    wall.beam_screen.width=width;bpy.ops.beam.screen_action(action='UPDATE')
    count=len(c.scene.ps_study.blend_groups);bpy.ops.ed.undo_push(message='Inspector Auto Blend')
    assert bpy.ops.beam.auto_blend('EXEC_DEFAULT',True,use_template=False,count=3,overlap_h=200)=={'FINISHED'}
    assert len(c.scene.ps_study.blend_groups)==count+1
    bpy.ops.ed.undo();refresh();assert len(c.scene.ps_study.blend_groups)==count
    bpy.ops.ed.redo();refresh();assert len(c.scene.ps_study.blend_groups)==count+1
    bpy.ops.ed.undo();refresh();s=c.scene.ps_study
    s.blend_group_index=0;assert bpy.ops.beam.ui_member(index=1)=={'FINISHED'};assert s.inspector=='GROUP'
    member=c.view_layer.objects.active;assert member==s.blend_groups[0].members[1].projector
    bpy.ops.ps.add();new=c.view_layer.objects.active;s.blend_group_index=0
    n=len(s.blend_groups[0].members);assert bpy.ops.beam.group_action(action='ADD_SELECTED')=={'FINISHED'};assert len(s.blend_groups[0].members)==n+1
    assert bpy.ops.beam.group_action(action='REMOVE')=={'FINISHED'};assert len(s.blend_groups[0].members)==n
    bpy.data.objects.remove(new,do_unlink=True);assert bpy.ops.beam.group_action(action='APPLY')=={'FINISHED'}
   checks.append('Screen edit/update, Auto Blend Undo/Redo, member selection/add/remove and Reflow from Properties inspector')
   s=c.scene
   checks.extend(['Workspace and receiver restoration survive save/reload','Frame, Lock, Presentation and PNG export from Properties inspector'])
   import statistics
   s.ps_study.inspector='GROUP';ui_workspace.tick();samples=[]
   for _ in range(100):
    start=time.perf_counter();ui_workspace.tick();samples.append((time.perf_counter()-start)*1000)
   (out/'timing.json').write_text(json.dumps(dict(ui_tick_ms_median=statistics.median(samples),ui_tick_ms_max=max(samples)),indent=2))
   checks.append('Panel drawing passed with runtime/coverage/pair computations forbidden')
   addon.unregister();assert not bpy.app.timers.is_registered(ui_workspace.tick)
   (out/'result.txt').write_text('PASS\n'+'\n'.join(checks));print('UI WORKSPACE PASS',checks,flush=True);bpy.ops.wm.quit_blender();return
  if name=='outliner_start':
   area=next(a for a in c.screen.areas if a.type=='OUTLINER');region=next(r for r in area.regions if r.type=='WINDOW')
   with c.temp_override(area=area,region=region):bpy.ops.outliner.show_hierarchy()
   x=region.x+120;y=region.y+region.height//2;state['outliner_xy']=(x,y)
   c.window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
   c.window.event_simulate(type='LEFTMOUSE',value='PRESS',x=x,y=y);c.window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=x,y=y)
   for _ in range(40):
    c.window.event_simulate(type='UP_ARROW',value='PRESS',x=x,y=y);c.window.event_simulate(type='UP_ARROW',value='RELEASE',x=x,y=y)
   state['walk']=0;state['seen']=set();state['phase']='outliner_walk';return .5
  if name=='outliner_walk':
   area=next(a for a in c.screen.areas if a.type=='OUTLINER');region=next(r for r in area.regions if r.type=='WINDOW')
   x,y=state['outliner_xy']
   c.window.event_simulate(type='DOWN_ARROW',value='PRESS',x=x,y=y);c.window.event_simulate(type='DOWN_ARROW',value='RELEASE',x=x,y=y)
   study_data.sync_selection(c);obj=c.view_layer.objects.active
   if obj and obj.select_get():
    expected='PROJECTOR' if obj.ps.is_projector else 'SCREEN' if obj.beam_screen.is_screen else 'GROUP' if obj.get('beam_group_uuid') else 'VIEW' if any(v.camera==obj for v in s.ps_study.views) else None
    if expected:assert s.ps_study.inspector==expected,(obj.name,s.ps_study.inspector,expected);state['seen'].add(expected)
   state['walk']+=1
   if len(state['seen'])==4:
    checks.append('Native Outliner selection followed all four Beam object types');state['phase']='projector';return .5
   if state['walk']>70:raise AssertionError(('Outliner selection coverage incomplete',state['seen']))
   return .08
  if name.endswith('_capture') and state.get('capture_ready')!=name:
   state['capture_ready']=name
   for area in c.screen.areas:area.tag_redraw()
   bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
   return .5
  if name.endswith('_capture'):
   capture(name.removesuffix('_capture'));i=phases.index(name.removesuffix('_capture'))+1
   if i==len(phases):
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Workspace.blend'));state['phase']='reloaded';bpy.ops.wm.open_mainfile(filepath=str(out/'Beam-Workspace.blend'));bpy.app.timers.register(step,first_interval=2);return
   state['phase']=phases[i];return .25
  with native():
   if name=='projector':
    assert ui_workspace.is_beam(c);select(bpy.data.objects[state['pj']]);checks.append('Switch away/back preserves native workspace')
   elif name=='inline-target':
    assert bpy.ops.beam.edit_target(field='HEIGHT')=={'FINISHED'};c.window_manager.beam_target.value=4.75
   elif name=='screen':
    bpy.ops.beam.apply_target(cancel=True);select(bpy.data.objects[state['wall']]);assert s.ps_study.inspector=='SCREEN'
   elif name=='blend':
    g=next(g for g in s.ps_study.blend_groups if g.uuid==state['group']);select(g.controller);assert s.ps_study.inspector=='GROUP';ui_context.update_summary(c);assert ui_context.summary(c,g)['pairs']
   elif name=='views':select(s.ps_study.views[0].camera);assert s.ps_study.inspector=='VIEW';assert bpy.ops.ps.view_study()=={'FINISHED'};assert bpy.ops.ps.view_study(action='EXIT')=={'FINISHED'}
   elif name=='venue':
    select(bpy.data.objects[state['venue']]);s.ps_study.inspector='PROJECTOR';assert ui.receiver_warning(c,c.scene.ps_study.reverse_receiver)=='Unsupported receiver material'
   elif name=='reverse':
    select(bpy.data.objects[state['wall']]);s.ps_study.reverse_receiver=bpy.data.objects[state['wall']];r=s.ps_study.reverse_receiver;r.beam_reverse.source='ALL';assert bpy.ops.beam.receiver_action(action='ENABLE')=={'FINISHED'};reverse_mapping.refresh_gpu();assert not reverse_mapping._error;assert s.ps_study.active_projector.name==state['pj'];s.ps_study.inspector='PROJECTOR'
   elif name=='export':s.ps_study.inspector='EXPORT'
   checks.append(name+' inspector / actions')
  state['phase']=name+'_capture';return 1.5
 except:fail()
bpy.app.timers.register(setup,first_interval=2)
