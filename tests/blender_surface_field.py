"""Disposable architectural field validation; run in native GPU Blender."""
import bpy,sys,math,json,time,traceback,shutil,platform
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,screen_objects,blend_groups,analysis_runtime,study_views,study_reporting,runtime
from projection_study.utils import new_uuid
out=root/'examples/surface-intelligence/field';out.mkdir(parents=True,exist_ok=True)
def mesh(name,verts,faces,colour):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o)
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*colour,1);o.data.materials.append(mat);return o
def box(name,loc,scale,colour=(.12,.15,.17)):
 bpy.ops.mesh.primitive_cube_add(size=2,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*colour,1);o.data.materials.append(mat);return o
def run():
 try:
  addon.register();c=bpy.context
  for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
  s=c.scene.ps_study;s.project_name='Civic Hall · Architectural Projection Study';s.author='Twisted Pixel';s.venue='Disposable irregular facade / audience plaza';s.revision='0.13 Internal Production Beta validation';s.display_units='m';s.shadow_resolution='512'
  # One analysed architectural envelope: oblique wings, recessed central wall,
  # a curved return and stepped lintel. It is deliberately not one flat screen.
  profile=[(-12,13),(-9,15),(-6,15),(-6,17),(-3,17),(0,18),(3,17),(6,17),(6,15),(9,15)]
  profile += [(9+3*math.sin(i*math.pi/12),12+3*math.cos(i*math.pi/12)) for i in range(1,7)]
  verts=[];faces=[]
  for i,(x,y) in enumerate(profile):
   top=7 if abs(x)>6 else 8
   verts.extend([(x,y,.6),(x,y,top)])
  for i in range(len(profile)-1):faces.append((2*i,2*i+2,2*i+3,2*i+1))
  wall=mesh('Civic Hall · Facade Receiver',verts,faces,(.48,.50,.51));wall['beam_receiver_uuid']=new_uuid()
  box('Plaza',(0,4,-.25),(17,19,.25),(.09,.11,.13))
  for i in range(3):box('Entrance step '+str(i+1),(0,14.2+i*.55,.1+i*.13),(5,1.1-i*.22,.1+i*.13),(.22,.24,.26))
  blocker=box('Portico column · opaque blocker',(1,10.5,3),(.55,.55,3),(.28,.30,.32))
  box('Portico lintel',(1,10.5,6.15),(5.5,.6,.2),(.25,.27,.30))
  # A Beam Screen and Blend Group are included for persistence checks.
  draft=c.scene.beam_screen_draft;draft.width=3;draft.height=2;draft.aspect='FREE';screen=screen_objects.create(c,draft);screen.location=(-14,14,1)
  objects=[]
  for i,x in enumerate((-8,-2.8,2.8,8)):
   obj=projector_object.create(c);p=obj.ps;p.optics_model='christie_4k10';p.optics_lens='christie_085';p.resolution_x=2716;p.resolution_y=1528;p.lumens=10000;p.throw_ratio=.95
   origin=Vector((x,-1,2.7));aim=Vector((x*.8,16,4));obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(aim-origin).to_track_quat('-Z','Y');obj.location=origin
   p.show_projected_identifier=False;p.show_centre_ray=False;objects.append(obj)
   box('Projector platform '+str(i+1),(x,-1,1.15),(.38,.4,1.15),(.04,.05,.06))
  c.view_layer.update();runtime.refresh(True)
  group=blend_groups.create(c,objects,'HORIZONTAL',4,1,25,'PERCENT',preserve=True);group.name='Facade projectors';group.show_overlap=False
  c.scene.cursor.location=(0,-7,0);bpy.ops.beam.add_observer();viewer=s.analysis_observer;viewer.beam_observer.eye_height=1.65;viewer.beam_observer.threshold=1
  s.analysis_receiver=wall;s.analysis_scope='ALL';s.analysis_detail='8192';s.analysis_mode='ILLUMINANCE';s.analysis_show=True;s.use_target_illuminance=True;s.target_illuminance=100
  s.show_labels=False;s.show_projected_identifiers=False;s.show_frustums=False;s.show_outputs=False
  for o in c.selected_objects:o.select_set(False)
  s.active_projector=objects[1];s.active_screen=screen
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with c.temp_override(area=area,region=region):
   space=area.spaces.active;space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.shading.light='STUDIO';space.overlay.show_floor=False;space.overlay.show_axis_x=False;space.overlay.show_axis_y=False;space.overlay.show_relationship_lines=False;space.overlay.show_cursor=False
   rv=space.region_3d;target=Vector((0,13,3.7));eye=Vector((25,-32,22));rv.view_location=target;rv.view_rotation=(target-eye).to_track_quat('-Z','Y');rv.view_distance=(target-eye).length;rv.view_perspective='PERSP';rv.update()
   def analyse():
    c.view_layer.update();return analysis_runtime.analyse(c,wall,objects,8192)
   r=analyse();stats=r['statistics'];report={'blender':bpy.app.version_string,'platform':platform.platform(),'baseline':stats,'shared_solve_seconds':r['elapsed_seconds']}
   assert stats['coverage_percent']>60 and stats['overlap_percent']>20,stats
   assert stats['max_anisotropy']>1.1 and stats['distance_variation_m']>2,stats
   assert stats['illuminance_min_lux']==0 and stats['illuminance_max_lux']>stats['illuminance_average_lux'],stats
   assert 0<stats['acuity_evaluated_area_m2']<stats['visible_covered_area_m2'],stats
   report['distance_source_count']=len({x['distance_projector_uuid'] for x in r['samples'] if x['distance_projector_uuid']});assert report['distance_source_count']>=3
   for mode in ('NONE','DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY'):
    s.show_frustums=mode=='NONE';s.show_outputs=mode=='NONE'
    view=study_views.create_view(c,'Overview' if mode=='NONE' else mode.title());view.resolution_x=1600;view.resolution_y=1000;view.analysis_overlay=mode;view.include_labels=False;view.include_projected_identifiers=False;view.include_grids=mode=='NONE';view.include_frustums=mode=='NONE'
    # Same surveyed position, tighter surface framing for the technical views.
    if mode!='NONE':
     pos=Vector((17,-18,14));view.camera.location=pos;view.camera.rotation_euler=(Vector((0,15,4))-pos).to_track_quat('-Z','Y').to_euler();view.camera.data.lens=45
    study_views.export_view(c,view,out/(mode.lower()+'.png'),area)
   illuminance=s.views[3];s.illuminance_scale='FIXED';s.illuminance_max=250
   assert not analysis_runtime.stale(r,'ILLUMINANCE');study_views.export_view(c,illuminance,out/'illuminance-fixed.png',area)
   s.illuminance_scale='AUTO'
   # Viewpoint and threshold changes must alter only Acuity until explicitly rerun.
   viewer.location.y=-1;c.view_layer.update();runtime.refresh();assert analysis_runtime.stale(r,'ACUITY') and not analysis_runtime.stale(r,'ILLUMINANCE')
   close=analyse();report['observer_close']=close['statistics'];assert close['statistics']['acuity_average_arcmin']>stats['acuity_average_arcmin']
   viewer.location.y=-18;far=analyse();report['observer_far']=far['statistics'];assert far['statistics']['acuity_average_arcmin']<stats['acuity_average_arcmin']
   viewer.location.y=-7;viewer.beam_observer.threshold=.7;threshold=analyse();report['threshold_0_7']=threshold['statistics'];assert threshold['statistics']['acuity_at_or_above_threshold_percent']>=stats['acuity_at_or_above_threshold_percent']
   viewer.beam_observer.threshold=1;r=analyse()
   package=out/'Study-Package'
   if package.exists():shutil.rmtree(package)
   data=study_reporting.export(c,package,True,area);study_reporting.validate(data)
   assert len(data['views'])==6 and len(data['projectors'])==4 and data['observers'][0]['threshold_arcmin']==1
   report['persistent']={'observer_uuid':viewer.beam_observer.uuid,'projectors':[o.ps.uuid for o in objects],'screen_uuid':screen.beam_screen.uuid,'group_uuid':group.uuid,'view_uuids':[v.uuid for v in s.views]}
   (out/'results.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Beam-Civic-Hall-Field.blend'))
   print('SURFACE FIELD PASS',json.dumps(report['baseline']),flush=True)
 except Exception:traceback.print_exc();(out/'FAIL.txt').write_text(traceback.format_exc())
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=2)
