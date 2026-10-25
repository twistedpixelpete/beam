"""Create disposable, packed Beam training scene and actual native UI captures."""
import bpy,sys,math,json,traceback
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,study_data,screen_objects,blend_groups,study_views,analysis_runtime,reverse_mapping,ui_context
out=root/'output/pdf/onboarding';shots=out/'screenshots'/'source';shots.mkdir(parents=True,exist_ok=True)
state={}
def native():
 a=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');r=next(r for r in a.regions if r.type=='WINDOW');return bpy.context.temp_override(area=a,region=r)
def select(o):screen_objects.select(bpy.context,o);study_data.sync_selection(bpy.context)
def refresh():bpy.context.view_layer.update();runtime.refresh(True)
def cube(name,loc,scale):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc,scale=scale);o=bpy.context.object;o.name=name;return o
def view(name,location,direction,distance):
 rv=bpy.context.space_data.region_3d;rv.view_location=location;rv.view_distance=distance;rv.view_rotation=Vector(direction).to_track_quat('-Z','Y');rv.view_perspective='PERSP';rv.update()
 v=study_views.create_view(bpy.context,name);v.resolution_x=1600;v.resolution_y=1000;return v
def fail():
 (out/'build-result.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);bpy.ops.wm.quit_blender()
def setup():
 try:
  assert Path(bpy.utils.user_resource('CONFIG')).resolve()==(root/'work/onboarding-build/config').resolve();addon.register();assert bpy.ops.beam.apply_theme()=={'FINISHED'}
  with native():
   c=bpy.context;s=c.scene.ps_study
   for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
   c.scene.unit_settings.system='METRIC';c.scene.unit_settings.scale_length=1
   s.project_name='Beam Training Project';s.venue='Twisted Pixel Training';s.revision='01';s.author='Twisted Pixel';s.display_units='m';s.show_study_cameras=False
   d=c.scene.beam_screen_draft;d.width=15;d.height=3.6;d.aspect='FREE';d.name='Training Screen';d.origin='BOTTOM'
   assert bpy.ops.beam.screen_create()=={'FINISHED'};wall=c.object;wall.location=(0,10,.5);wall.name='SCR001';refresh();select(wall)
   assert bpy.ops.beam.plan_new(use_template=False,count=3,overlap_h=240,layout_type='HORIZONTAL')=={'FINISHED'}
   g=s.blend_groups[0];members=list(blend_groups.member_objects(g))
   for i,o in enumerate(members):
    o.ps.show_projected_identifier=False;o.ps.show_centre_ray=False;o.ps.colour=[(.16,.4,.8),(.22,.65,.47),(.75,.35,.25)][i]
   members[0].ps.optics_model='panasonic_rz990';members[0].ps.optics_lens='panasonic_dle105';members[0].ps.lumens=9400
   # Keep raster 1920x1080 for this matched training blend (preset's native raster differs).
   # Use real preset model native raster for ALL members, then reflow consistent geometry.
   for o in members:o.ps.resolution_y=1200
   select(g.controller);assert bpy.ops.beam.reflow()=={'FINISHED'}
   # Screen has valid UVs; generated packed image provides obvious mapped content.
   im=bpy.data.images.new('Training UV Chart',width=512,height=512);im.generated_type='COLOR_GRID';im.pack()
   mat=bpy.data.materials.new('Training mapped content');mat.use_nodes=True;nodes=mat.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color']);wall.data.materials.clear();wall.data.materials.append(mat)
   cube('Venue Floor',(0,5,-.15),(21,18,.3));cube('Stage',(0,9,.15),(17,3,.3));cube('Architecture Wall',(0,10.5,2.8),(20,.25,5.6))
   # Small curved UV receiver at screen-right edge; leaves centre rays unobstructed.
   verts=[];faces=[]
   for z in (1,3.4):
    for i in range(25):
     a=(i/24-.5)*1.2;verts.append((6.9+1.4*math.sin(a),8.6+1.4*(1-math.cos(a)),z))
   for i in range(24):faces.append((i,i+1,i+26,i+25))
   mesh=bpy.data.meshes.new('Curved Training Receiver');mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
   for poly in mesh.polygons:
    for li in poly.loop_indices:
     vi=mesh.loops[li].vertex_index;uv.data[li].uv=(vi%25/24,vi//25)
   curved=bpy.data.objects.new('TRAINING_Curved_Receiver',mesh);c.scene.collection.objects.link(curved);mesh.materials.append(mat)
   cube('TRAINING_Occluder',(-9,7,2),(1.2,.25,2.2))
   s.analysis_receiver=wall;s.analysis_scope='GROUP';s.analysis_detail='2048';s.reverse_receiver=wall;wall.beam_reverse.source='GROUP';wall.beam_reverse.group_uuid=g.uuid
   for name,loc,di,dist in [('Overview',(0,6,2),(12,21,-12),24),('Front',(0,10,2.2),(0,1,-.02),20),('Blend',(0,8,2),(4,20,-8),19),('Reverse Mapping',(3,9,2),(2,20,-5),18),('Density',(0,10,2.2),(0,1,-.02),19),('Stretch',(6.8,9,2),(3,12,-3),7)]:
    v=view(name,loc,di,dist)
    if name in ('Density','Stretch'):v.analysis_overlay=name.upper();v.include_grids=False;v.include_frustums=False
   s.view_index=0
   rv=c.space_data.region_3d;rv.view_location=(0,6,2);rv.view_distance=24;rv.view_rotation=Vector((12,21,-12)).to_track_quat('-Z','Y');rv.update()
   c.space_data.shading.color_type='MATERIAL';c.space_data.overlay.show_extras=False
   select(members[1]);refresh();assert bpy.ops.beam.workspace()=={'FINISHED'}
  bpy.app.timers.register(ready,first_interval=2)
 except:fail()
def ready():
 try:
  with native():
   c=bpy.context;s=c.scene.ps_study;select(bpy.data.objects['PJ02']);s.analysis_show=False
   # Save clean baseline before analysis (analysis cache intentionally transient).
   bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam_Training_Project.blend'))
   state['phase']=0
  bpy.app.timers.register(step,first_interval=1)
 except:fail()
phases=['workspace','pinned','screen','blend','solver','views','export','density','occlusion','stretch','reverse-covered','reverse-dim','reverse-hidden','reverse-overlap','presentation']
def step():
 try:
  c=bpy.context;s=c.scene.ps_study;i=state['phase']
  if i>=len(phases):
   (out/'build-result.txt').write_text('PASS training scene and '+str(len(phases))+' fresh native screenshots');addon.unregister();bpy.ops.wm.quit_blender();return
  name=phases[i]
  with native():
   wall=bpy.data.objects['SCR001'];pj=bpy.data.objects['PJ02'];g=s.blend_groups[0]
   if not state.get('capture'):
    if name=='pinned':s.pin_context=True;select(wall)
    elif name=='screen':s.pin_context=False;select(wall)
    elif name=='blend':select(g.controller)
    elif name=='solver':select(pj);bpy.ops.beam.edit_target(field='WIDTH');c.window_manager.beam_target.value=6
    elif name=='views':bpy.ops.beam.apply_target(cancel=True);s.inspector='VIEW';s.view_index=0
    elif name=='export':s.inspector='EXPORT'
    elif name in ('density','occlusion','stretch'):
     s.inspector='PROJECTOR';select(pj);s.analysis_receiver=wall if name!='stretch' else bpy.data.objects['TRAINING_Curved_Receiver'];s.analysis_scope='ALL';s.analysis_detail='8192'
     if name=='occlusion':bpy.data.objects['TRAINING_Occluder'].location.x=0
     refresh();assert bpy.ops.beam.analyse()=={'FINISHED'};s.analysis_mode='STRETCH' if name=='stretch' else 'DENSITY'
     v=s.views[5 if name=='stretch' else 4];v.analysis_overlay=s.analysis_mode;study_views.export_view(c,v,shots/(name+'-asset.png'),c.area)
    elif name.startswith('reverse-'):
     s.analysis_show=False;bpy.data.objects['TRAINING_Occluder'].location.x=-9;select(wall);s.inspector='PROJECTOR';s.reverse_receiver=wall
     wall.beam_reverse.mode={'reverse-covered':'COVERED','reverse-dim':'DIM','reverse-hidden':'HIDDEN','reverse-overlap':'OVERLAP'}[name]
     if not wall.beam_reverse.enabled:assert bpy.ops.beam.receiver_action(action='ENABLE')=={'FINISHED'}
     reverse_mapping.refresh_gpu();c.space_data.shading.type='MATERIAL'
    elif name=='presentation':
     if wall.beam_reverse.enabled:reverse_mapping.disable(wall)
     c.space_data.shading.type='SOLID';select(pj);bpy.ops.beam.ui_action(action='PRESENTATION')
    refresh();state['capture']=True;return 2
   for a in c.screen.areas:a.tag_redraw()
   bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=2)
   bpy.ops.screen.screenshot(filepath=str(shots/(name+'.png')))
   props=next(a for a in c.screen.areas if a.type=='PROPERTIES');reg=next(r for r in props.regions if r.type=='WINDOW')
   with c.temp_override(area=props,region=reg):bpy.ops.screen.screenshot_area(filepath=str(shots/(name+'-inspector.png')))
  state['phase']+=1;state['capture']=False;return .2
 except:fail()
bpy.app.timers.register(setup,first_interval=2)
