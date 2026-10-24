"""Disposable AV venue benchmark. Run native GPU Blender; costs are not FPS."""
import bpy,sys,time,math,statistics,json,traceback,platform,shutil
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,screen_objects,blend_groups,runtime,analysis_runtime,study_views,study_reporting,reverse_mapping
out=root/'work/production/benchmark';out.mkdir(parents=True,exist_ok=True)
report={'platform':platform.platform(),'blender':bpy.app.version_string,'measurements':[]}
def measure(count,name,fn,n=3):
 values=[]
 for i in range(n):
  start=time.perf_counter();fn();values.append(time.perf_counter()-start)
 record=dict(projectors=count,operation=name,median_seconds=statistics.median(values),max_seconds=max(values),runs=values)
 report['measurements'].append(record);(out/'timings.json').write_text(json.dumps(report,indent=2));print(record,flush=True)
def run():
 try:
  import gpu
  report['gpu']=gpu.platform.renderer_get();addon.register();c=bpy.context
  area=next(a for a in c.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
  with c.temp_override(area=area,region=region):
   for count in (16,32):
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    c.scene.ps_study.views.clear();c.scene.ps_study.blend_groups.clear();runtime.reset()
    # Raked auditorium seating with curved seat backs, stage steps and roof trusses.
    venue=[]
    for row in range(12):
     for col in range(24):
      bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=((col-11.5)*.8,-4-row*.9,.4+row*.15));o=c.object;o.name='Auditorium seat';o.scale=(.32,.3,.45);venue.append(o)
    for level in range(5):
     bpy.ops.mesh.primitive_cube_add(size=2,location=(0,13+level*.4,-.5+level*.08));o=c.object;o.scale=(23,2-level*.3,.2);venue.append(o)
    for x in (-22,22):
     bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.1,depth=45,location=(0,x,9),rotation=(0,math.pi/2,0));venue.append(c.object)
    for o in c.selected_objects:o.select_set(False)
    for o in venue:o.select_set(True)
    c.view_layer.objects.active=venue[0];bpy.ops.object.join();venue_mesh=c.object;venue_mesh.name='Venue seating stage and truss'
    objects=[];walls=[];groups=[]
    for g in range(count//4):
     draft=c.scene.beam_screen_draft;draft.width=18;draft.height=3.75;draft.aspect='FREE'
     wall=screen_objects.create(c,draft);wall.location=((g%4-1.5)*20,10+(g//4)*12,1);walls.append(wall)
     members=[]
     for x in (-6.3,-2.1,2.1,6.3):
      obj=projector_object.create(c);obj.ps.resolution_x=1920;obj.ps.resolution_y=1200;obj.ps.throw_ratio=1.4
      matrix=Matrix.Rotation(math.pi/2,4,'X');matrix.translation=(wall.location.x+x,wall.location.y-8,2.875);obj.matrix_world=matrix;members.append(obj)
     c.view_layer.update();runtime.refresh(True)
     group=blend_groups.create(c,members,'HORIZONTAL',4,1,26.5,'PERCENT',preserve=True);group.layout_screen=wall;groups.append(group);objects.extend(members)
    groups=list(c.scene.ps_study.blend_groups)
    rv=area.spaces.active.region_3d;target=Vector((0,7,2));eye=Vector((45,-45,40));rv.view_location=target;rv.view_rotation=(target-eye).to_track_quat('-Z','Y');rv.view_distance=65;rv.update()
    view=study_views.create_view(c,'Venue overview');view.resolution_x=1200;view.resolution_y=750
    c.view_layer.update();runtime.refresh(True)
    report.setdefault('scenes',[]).append(dict(projectors=count,groups=len(groups),screens=len(walls),objects=len(c.scene.objects),venue_vertices=len(venue_mesh.data.vertices),venue_polygons=len(venue_mesh.data.polygons)))
    measure(count,'idle_update',lambda:runtime.refresh(),10)
    def move_one():objects[0].location.x+=.001;c.view_layer.update();runtime.refresh()
    measure(count,'projector_transform_refresh',move_one)
    def recalculate():
     from projection_study import layout_coverage
     layout_coverage._cache.clear()
     return [blend_groups.pair_data(g,c) for g in groups]
    measure(count,'blend_overlap_recalculation',recalculate)
    def move_many():
     for group in groups:group.controller.location.x+=.001
     c.view_layer.update();runtime.refresh()
    measure(count,'multi_group_movement',move_many)
    for budget in (512,2048,8192):measure(count,f'analysis_{budget}',lambda b=budget:analysis_runtime.analyse(c,walls[0],objects,b))
    reverse_mapping.enable(c,walls[0]);reverse_mapping.refresh_gpu()
    def reverse():objects[0].location.x+=.001;c.view_layer.update();runtime.refresh();reverse_mapping.refresh_gpu()
    measure(count,'reverse_mapping_refresh',reverse)
    measure(count,'study_view_export',lambda:study_views.export_view(c,view,out/f'venue-{count}.png',area))
    def package():
     path=out/f'package-{count}'
     if path.exists():shutil.rmtree(path)
     study_reporting.export(c,path,True,area)
    measure(count,'study_package_export',package)
    measure(count,'save',lambda:bpy.ops.wm.save_as_mainfile(filepath=str(out/f'venue-{count}.blend')))
   (out/'result.txt').write_text('PASS benchmark operations completed; timings are wall-clock costs, not FPS')
 except Exception:
  text=traceback.format_exc();print(text,flush=True);(out/'result.txt').write_text(text)
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=2)
