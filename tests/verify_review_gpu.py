"""PR #2: realistic GPU sanity, durable state, Position/Reflow Undo and cleanup.
Run in a disposable factory-startup interactive Blender process.
"""
import bpy,sys,json,time,statistics,traceback,gpu
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import screen_objects as screens,runtime,auto_layout,layout_coverage,blend_groups,inverse_solver,reverse_mapping as reverse,projection_renderer,study_views
out=root/'work/review-gpu';out.mkdir(parents=True,exist_ok=True)
state={};results={};uploads=[0];original_image=reverse.image_for

def tracked(obj,record):
 shadow=projection_renderer.shadow_map(obj,record);cached=reverse._images.get(obj.as_pointer())
 if not cached or cached[0]!=shadow['signature']:uploads[0]+=1
 return original_image(obj,record)
reverse.image_for=tracked

def refresh():bpy.context.view_layer.update();runtime.refresh(True)
def context():
 area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
 return bpy.context.temp_override(area=area,region=region)
def fail():
 text=traceback.format_exc();print(text,flush=True);(out/'result.txt').write_text(text);bpy.ops.wm.quit_blender()
def snapshot():
 s=bpy.context.scene;g=s.ps_study.blend_groups[0]
 return dict(project=s.ps_study.project_name,venue=s.ps_study.venue,revision=s.ps_study.revision,screen=s.ps_study.active_screen.beam_screen.uuid,
 group=g.uuid,layout_screen=g.layout_screen.beam_screen.uuid,members=[m.projector_uuid for m in g.members],anchor=g.anchor_uuid,
 projectors=[dict(uuid=m.projector.ps.uuid,identifier=m.projector.ps.identifier,ratio=m.projector.ps.throw_ratio,solve=m.projector.ps.solve_by,
 locks=[m.projector.ps.solve_lock_position,m.projector.ps.solve_lock_lens,m.projector.ps.solve_lock_target],position=list(m.projector.matrix_world.translation)) for m in g.members],
 reverse=[dict(name=o.name,enabled=o.beam_reverse.enabled,source=o.beam_reverse.source,group=o.beam_reverse.group_uuid,mode=o.beam_reverse.mode,originals=[r.material.name for r in o.beam_reverse.slots]) for o in s.objects if o.beam_reverse.enabled])
def setup():
 try:
  addon.register()
  with context():
   c=bpy.context;s=c.scene
   for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
   s.ps_study.display_units='m';s.ps_study.shadow_resolution='512';s.ps_study.project_name='PR2 engineering review';s.ps_study.venue='Eight projector venue';s.ps_study.revision='beta-test'
   p=s.beam_screen_draft;p.width=24;p.height=6;p.aspect='FREE';wall=screens.create(c,p);wall.location=(0,10,-3);screens.select(c,wall)
   options=SimpleNamespace(use_template=False,layout_type='ARRAY',count=8,columns=4,rows=2,auto_count=False,overlap_h=200,overlap_v=200,input_mode='PIXELS',distance=10,fixed_distance=False,max_count=32,min_throw=.1,max_throw=100)
   g,_=auto_layout.create(c,options);refresh();assert len(g.members)==8
   # Position solve and group reflow through native undo/redo, not manual snapshots.
   pj=g.members[0].projector;screens.select(c,pj);s.ps_study.active_projector=pj;pj.ps.solve_by='POSITION';refresh()
   old=list(pj.matrix_world.translation);d=runtime.CACHE[pj.as_pointer()]['metrics'].distance
   bpy.ops.ed.undo_push(message='Before position solve');bpy.ops.beam.solve('EXEC_DEFAULT',True,field='DISTANCE',value=d-.2)
   moved=list(c.scene.ps_study.active_projector.matrix_world.translation);assert moved!=old
   bpy.ops.ed.undo();refresh();assert (c.scene.ps_study.active_projector.matrix_world.translation-Vector(old)).length<1e-5
   bpy.ops.ed.redo();refresh();assert (c.scene.ps_study.active_projector.matrix_world.translation-Vector(moved)).length<1e-5
   g=c.scene.ps_study.blend_groups[0];g.members[1].projector.location.x+=.2;refresh();before=list(g.members[1].projector.matrix_world.translation)
   bpy.ops.ed.undo_push(message='Before reflow');bpy.ops.beam.group_action('EXEC_DEFAULT',True,action='APPLY');refresh()
   after=list(c.scene.ps_study.blend_groups[0].members[1].projector.matrix_world.translation);assert before!=after
   bpy.ops.ed.undo();refresh();assert (c.scene.ps_study.blend_groups[0].members[1].projector.matrix_world.translation-Vector(before)).length<1e-5
   bpy.ops.ed.redo();refresh();assert (c.scene.ps_study.blend_groups[0].members[1].projector.matrix_world.translation-Vector(after)).length<1e-5
   s=c.scene;g=s.ps_study.blend_groups[0];wall=g.layout_screen
   g.members[0].projector.ps.solve_lock_lens=True;g.members[0].projector.ps.solve_lock_position=True
   for loc,scale in [((0,5,-4),(18,12,.2)),((18,5,0),(.2,12,5)),((-18,5,0),(.2,12,5))]:bpy.ops.mesh.primitive_cube_add(size=1,location=loc,scale=scale)
   for i in range(20):bpy.ops.mesh.primitive_cube_add(size=.4,location=(15,2+i*.4,-2+i*.1))
   wall.data.materials.clear()
   for name in ('Review source A','Review source B'):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;wall.data.materials.append(mat)
   screens.select(c,wall);wall.beam_reverse.source='GROUP';wall.beam_reverse.group_uuid=g.uuid;reverse.enable(c,wall)
   space=c.space_data;space.shading.type='MATERIAL';space.overlay.show_overlays=True
   space.region_3d.view_location=(0,7,0);space.region_3d.view_distance=30;space.region_3d.view_rotation=Vector((0,1,-.25)).to_track_quat('-Z','Y');space.region_3d.update()
   view=study_views.create_view(c,'Review venue');view.resolution_x=1000;view.resolution_y=600;view.camera.location=(18,-18,12);view.camera.rotation_euler=(Vector((0,8,0))-view.camera.location).to_track_quat('-Z','Y').to_euler()
   refresh();state['phase']='warm';bpy.app.timers.register(step,first_interval=5)
  results['native_undo']='Position solve and group Reflow Undo/Redo passed'
 except:fail()
def step():
 try:
  with context():
   c=bpy.context;s=c.scene;g=s.ps_study.blend_groups[0];wall=g.layout_screen
   if state['phase']=='warm':
    runtime.refresh();reverse.refresh_gpu();assert not reverse._error,reverse._error
    baseline=uploads[0];wrappers=[r.wrapper.as_pointer() for r in wall.beam_reverse.slots];samples=[]
    for _ in range(30):
     start=time.perf_counter();runtime.refresh();reverse.refresh_gpu();layout_coverage.report(g,c);samples.append((time.perf_counter()-start)*1000)
    assert uploads[0]==baseline;assert wrappers==[r.wrapper.as_pointer() for r in wall.beam_reverse.slots]
    results['idle_30_refreshes_ms']=dict(median=statistics.median(samples),max=max(samples),extra_uploads=uploads[0]-baseline)
    samples=[];measure=[]
    for _ in range(8):
     pj=g.members[3].projector;pj.location.x+=.01;start=time.perf_counter();c.view_layer.update();runtime.refresh();t=time.perf_counter();layout_coverage.report(g,c);measure.append((time.perf_counter()-t)*1000);reverse.refresh_gpu();samples.append((time.perf_counter()-start)*1000)
    results['movement_refresh_ms']=dict(median=statistics.median(samples),max=max(samples));results['overlap_recalculation_ms']=dict(median=statistics.median(measure),max=max(measure))
    pj=g.members[2].projector;pj.ps.solve_by='LENS';start=time.perf_counter();inverse_solver.solve(c,pj,'WIDTH',runtime.CACHE[pj.as_pointer()]['metrics'].width*.99);results['lens_solve_ms']=(time.perf_counter()-start)*1000
    saved=(gpu.state.blend_get(),gpu.state.depth_test_get(),gpu.state.depth_mask_get(),gpu.state.viewport_get());reverse.refresh_gpu()
    assert saved==(gpu.state.blend_get(),gpu.state.depth_test_get(),gpu.state.depth_mask_get(),gpu.state.viewport_get())
    # Reordered slots survive a mode-triggered wrapper rebuild, then restore correctly.
    screens.select(c,wall);wall.active_material_index=1;bpy.ops.object.material_slot_move(direction='UP');wall.beam_reverse.mode='OVERLAP';reverse.refresh_gpu();assert not reverse._error
    reverse.disable(wall);assert [slot.material.name for slot in wall.material_slots]==['Review source B','Review source A']
    for _ in range(3):
     reverse.enable(c,wall);reverse.refresh_gpu();assert not reverse._error;reverse.disable(wall)
     assert not [m for m in bpy.data.materials if m.get('beam_reverse')]
     assert not [n for n in bpy.data.node_groups if n.get('beam_reverse')]
     assert not [i for i in bpy.data.images if i.get('beam_coverage')]
    reverse.enable(c,wall);reverse.refresh_gpu()
    results['cleanup']='Reorder + mode rebuild, three GPU enable/disable cycles: zero wrapper, group or coverage-image orphans'
    start=time.perf_counter();study_views.export_view(c,s.ps_study.views[0],out/'venue.png');results['viewport_export_ms']=(time.perf_counter()-start)*1000
    screens.select(c,wall);s.ps_study.active_screen=wall;refresh();state['expected']=snapshot();bpy.ops.wm.save_as_mainfile(filepath=str(out/'review.blend'))
    state['phase']='reload';bpy.ops.wm.open_mainfile(filepath=str(out/'review.blend'));bpy.app.timers.register(step,first_interval=5);return
   if state['phase']=='reload':
    refresh();reverse.refresh_gpu();assert not reverse._error;assert snapshot()==state['expected'],(snapshot(),state['expected'])
    results['persistence']='Projector/group UUIDs, identifiers, membership, settings, locks, layout screen, metadata, active screen and material restore references exact after reopen'
    # Failure in one receiver must not prevent a second receiver from updating.
    second=wall.copy();second.data=wall.data.copy();s.collection.objects.link(second);second.beam_reverse.enabled=False;second.beam_reverse.slots.clear()
    for slot in second.material_slots:
     slot.link='DATA';slot.material=slot.material.copy()
    second.location.z+=8;second.beam_reverse.source='GROUP';second.beam_reverse.group_uuid=g.uuid
    reverse.enable(c,second);source=wall.beam_reverse.slots[0].material;output=reverse.surface_outputs(source)[0];socket=output.inputs['Surface'].links[0].from_socket;source.node_tree.links.remove(output.inputs['Surface'].links[0])
    wall.beam_reverse.mode='HIDDEN';second.beam_reverse.mode='DIM';reverse.refresh_gpu()
    assert 'unavailable' in wall.beam_reverse.status and '8 coverage' in second.beam_reverse.status
    source.node_tree.links.new(socket,output.inputs['Surface']);reverse.refresh_gpu();assert not reverse._error
    reverse.disable(second);bpy.data.objects.remove(second,do_unlink=True);reverse.disable(wall)
    # Deleting source resources is pruned even with overlays switched off.
    c.space_data.overlay.show_overlays=False;key=g.members[-1].projector.as_pointer();bpy.data.objects.remove(g.members[-1].projector,do_unlink=True);refresh()
    from projection_study import viewport_display
    viewport_display.draw_3d();assert key not in projection_renderer._maps
    results['failure_isolation']='One invalid source failed closed while the other receiver refreshed; repair recovered; overlays-off deleted GPU map pruned'
    # Full unregister must remove handlers/timers; re-register must not duplicate.
    for _ in range(2):
     addon.unregister()
     for name in ('load_post','save_pre','save_post','undo_post','redo_post','depsgraph_update_post'):
      assert not [f for f in getattr(bpy.app.handlers,name) if getattr(f,'__module__','').startswith('projection_study')],name
     from projection_study import screens as lifecycle
     assert not bpy.app.timers.is_registered(lifecycle.tick)
     addon.register()
    addon.unregister();results['registration']='Two repeated unregister/register cycles: no Beam handlers or screen timer survive unregister'
    results['scene']='8 projectors, 1 array Blend Group, 24 × 6 m Screen Builder screen, 23 venue meshes, Reverse Mapping, overlays; 512 depth detail'
    results['platform']=bpy.app.version_string+' macOS Metal';(out/'metrics.json').write_text(json.dumps(results,indent=2));(out/'result.txt').write_text('PASS engineering GPU, performance sanity, Undo/Redo, persistence and cleanup');print(json.dumps(results,indent=2),flush=True);bpy.ops.wm.quit_blender();return
 except:fail()
bpy.app.timers.register(setup,first_interval=2)
