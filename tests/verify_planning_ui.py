"""Native Undo/Redo and GPU reverse coverage; disposable Blender UI session."""
import bpy,sys,traceback,json
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,screen_objects,projector_object,reverse_mapping as reverse,study_views,auto_layout,layout_coverage
out=root/'work/planning-ui';out.mkdir(exist_ok=True,parents=True);state={};samples={}
def fail():
 text=traceback.format_exc();print(text,flush=True);(out/'result.txt').write_text(text);bpy.ops.wm.quit_blender()
def select(obj):screen_objects.select(bpy.context,obj)
def refresh():bpy.context.view_layer.update();runtime.refresh(True)
def setup():
 try:
  addon.register()
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');state.update(area=area,region=region)
  with bpy.context.temp_override(area=area,region=region):
   c=bpy.context;s=c.scene;s.ps_study.display_units='m';s.ps_study.show_outputs=False
   p=s.beam_screen_draft;p.width=10;p.height=5
   wall=screen_objects.create(c,p);wall.location=(0,6,-2.5);wall.beam_screen.show_label=False;wall.beam_screen.show_dimensions=False
   image=bpy.data.images.new('Continuous UV chart',1024,512);image.generated_type='COLOR_GRID';image.pack()
   mat=bpy.data.materials.new('Original UV chart');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();tex=n.new('ShaderNodeTexImage');tex.image=image;em=n.new('ShaderNodeEmission');output=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(tex.outputs[0],em.inputs[0]);mat.node_tree.links.new(em.outputs[0],output.inputs['Surface']);wall.data.materials.clear();wall.data.materials.append(mat)
   pj=projector_object.create(c);refresh();pj.ps.solve_by='LENS'
   bpy.ops.ed.undo_push(message='Before inverse')
   bpy.ops.beam.solve('EXEC_DEFAULT',True,field='HEIGHT',value=3)
   bpy.ops.ed.undo();refresh();assert abs(c.scene.ps_study.active_projector.ps.throw_ratio-1)<1e-5
   bpy.ops.ed.redo();refresh();assert abs(runtime.CACHE[c.scene.ps_study.active_projector.as_pointer()]['metrics'].height-3)<.001
   wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);select(wall);s=c.scene;s.ps_study.active_screen=wall
   bpy.ops.ed.undo_push(message='Before layout')
   bpy.ops.beam.auto_blend('EXEC_DEFAULT',True,use_template=False,count=2,overlap_h=400)
   assert len(s.ps_study.blend_groups)==1
   bpy.ops.ed.undo();refresh();assert not c.scene.ps_study.blend_groups
   bpy.ops.ed.redo();refresh();assert len(c.scene.ps_study.blend_groups)==1
   # Independent two-projector UV demonstration after successful layout undo test.
   s=c.scene;s.ps_study.blend_groups.clear()
   for o in list(s.objects):
    if not o.beam_screen.is_screen:bpy.data.objects.remove(o,do_unlink=True)
   wall=next(o for o in s.objects if o.beam_screen.is_screen)
   for x in (-1.4,1.4):
    pj=projector_object.create(c);pj.location=(x,0,0);pj.ps.throw_ratio=1.5;pj.ps.show_frustum=False;pj.ps.show_centre_ray=False;pj.ps.show_identifier=False;pj.ps.show_target_marker=False
   select(wall);wall.beam_reverse.source='ALL';refresh()
   bpy.ops.ed.undo_push(message='Before reverse')
   bpy.ops.beam.reverse_mapping('EXEC_DEFAULT',True,action='ENABLE');assert wall.beam_reverse.enabled
   bpy.ops.ed.undo();refresh();wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);assert not wall.beam_reverse.enabled and wall.active_material.name=='Original UV chart'
   bpy.ops.ed.redo();refresh();wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);assert wall.beam_reverse.enabled
   bpy.ops.beam.reverse_mapping('EXEC_DEFAULT',True,action='DISABLE');assert wall.active_material.name=='Original UV chart'
   bpy.ops.ed.undo();refresh();wall=next(o for o in c.scene.objects if o.beam_screen.is_screen);assert wall.beam_reverse.enabled
   reverse.disable(wall);state['wall_name']=wall.name
   space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_overlays=False
   rv=space.region_3d;target=Vector((0,6,0));rv.view_location=target;rv.view_rotation=Vector((0,1,0)).to_track_quat('-Z','Y');rv.view_distance=10;rv.view_perspective='ORTHO';rv.update()
   view=study_views.create_view(c,'Continuous UV coverage');view.resolution_x=1400;view.resolution_y=800;view.include_overlays=False;view.camera.location=(0,-12,0);view.camera.rotation_euler=Vector((0,1,0)).to_track_quat('-Z','Y').to_euler();view.camera.data.type='ORTHO';view.camera.data.ortho_scale=12;state['view_uuid']=view.uuid
   state['phase']=0;refresh()
  print('PASS native inverse, layout, reverse enable/disable Undo/Redo',flush=True)
  bpy.app.timers.register(step,first_interval=4)
 except:fail()
phases=['original','dim','covered','hidden','overlap','moved','occluded','restored']
def step():
 try:
  with bpy.context.temp_override(area=state['area'],region=state['region']):
   c=bpy.context;wall=bpy.data.objects[state['wall_name']];view=next(v for v in c.scene.ps_study.views if v.uuid==state['view_uuid']);phase=state['phase'];name=phases[phase]
   if 0<phase<7:
    from projection_study import projection_renderer
    for pj in (o for o in c.scene.objects if o.ps.is_projector):
     shadow=projection_renderer.shadow_map(pj,runtime.CACHE[pj.as_pointer()])
     assert reverse._images[pj.as_pointer()][0]==shadow['signature'],'Live mask did not update with overlays disabled'
   assert not reverse._error,reverse._error
   study_views.export_view(c,view,out/(name+'.png'))
   image=bpy.data.images.load(str(out/(name+'.png')),check_existing=False);data=np.array(image.pixels[:]).reshape(800,1400,4);bpy.data.images.remove(image)
   camera=view.camera;projection=camera.calc_matrix_camera(c.evaluated_depsgraph_get(),x=1400,y=800);matrix=projection@camera.matrix_world.inverted()
   def sample(x,z):
    v=matrix@Vector((x,6,z,1));u=int((v.x/v.w*.5+.5)*1400);y=int((v.y/v.w*.5+.5)*800);return data[y-2:y+3,u-2:u+3,:3].mean(axis=(0,1)).tolist()
   samples[name]={key:sample(x,z) for key,x,z in [('outside',4,1.8),('left',-2.5,.6),('overlap',0,.6),('right',2.5,.6)]}
   if phase==0:reverse.enable(c,wall);wall.beam_reverse.mode='DIM'
   elif phase in (1,2,3):wall.beam_reverse.mode={1:'COVERED',2:'HIDDEN',3:'OVERLAP'}[phase]
   elif phase==4:
    wall.beam_reverse.mode='COVERED';pjs=sorted((o for o in c.scene.objects if o.ps.is_projector),key=lambda o:o.location.x);pjs[0].location.x=-.2
   elif phase==5:
    bpy.ops.mesh.primitive_cube_add(location=(1.4,3,.4),scale=(.6,.1,.6));bpy.context.object.name='Coverage occluder';select(wall)
   elif phase==6:reverse.disable(wall)
   else:
    (out/'samples.json').write_text(json.dumps(samples,indent=2))
    for mode in ('dim','covered','hidden'):
     assert np.linalg.norm(np.array(samples[mode]['left'])-samples['original']['left'])<.12,(mode,'UV changed')
    assert np.mean(samples['dim']['outside'])<np.mean(samples['original']['outside'])*.6
    assert np.linalg.norm(np.array(samples['overlap']['overlap'])-samples['original']['overlap'])>.15
    assert np.linalg.norm(np.array(samples['moved']['left'])-samples['covered']['left'])>.1
    assert np.linalg.norm(np.array(samples['occluded']['right'])-samples['moved']['right'])>.15
    assert np.linalg.norm(np.array(samples['hidden']['outside'])-samples['covered']['outside'])>.05
    assert wall.active_material.name=='Original UV chart'
    select(wall);reverse.enable(c,wall);wall.beam_reverse.mode='OVERLAP';refresh();reverse.refresh_gpu();bpy.ops.wm.save_as_mainfile(filepath=str(out/'Reverse-Mapping.blend'))
    (out/'result.txt').write_text('PASS: native Undo/Redo for inverse, Auto Blend and Reverse Mapping; UV continuity, dim, hidden, union, overlap, projector movement, occluder shadow, original material restoration and live refresh with native overlays disabled.')
    print((out/'result.txt').read_text(),flush=True);bpy.ops.wm.quit_blender();return
   state['phase']+=1;refresh();state['area'].tag_redraw()
  return 3
 except:fail()
bpy.app.timers.register(setup,first_interval=2)
