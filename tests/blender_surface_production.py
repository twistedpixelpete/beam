"""Sampled geometry acceptance: curved/disconnected/thin/closed and overlap."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,analysis_runtime,runtime
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
objects=[]
for x in (-.1,.1):
 o=projector_object.create(c);o.ps.throw_ratio=.6;o.ps.resolution_x=1920;o.ps.resolution_y=1200;m=Matrix.Rotation(math.pi/2,4,'X');m.translation=(x,0,0);o.matrix_world=m;objects.append(o)
mesh=bpy.data.meshes.new('Receiver');wall=bpy.data.objects.new('Receiver',mesh);c.scene.collection.objects.link(wall);wall['beam_receiver_uuid']='d2ffb8f6-ab0b-4521-97cf-13e6bbed52a5'
results={}
def analyse(name,vertices,faces):
 mesh.clear_geometry();mesh.from_pydata(vertices,[],faces);mesh.update();c.view_layer.update();runtime.invalidate()
 stats=[]
 for count in (512,2048,8192):
  r=analysis_runtime.analyse(c,wall,objects,count);s=r['statistics'];assert s['sample_count']==count;assert s['coverage_percent']>99 and s['overlap_percent']>99,(name,s);stats.append(s)
 results[name]=stats
vertices=[];faces=[]
for i in range(33):
 x=-3+6*i/32;y=6+.6*math.cos(x/3*math.pi);vertices.extend([(x,y,-1),(x,y,1)])
for i in range(32):faces.append((2*i,2*i+2,2*i+3,2*i+1))
analyse('curved',vertices,faces);assert results['curved'][-1]['max_anisotropy']>1.05
analyse('disconnected',[(-3,6,-1),(-1,6,-1),(-1,6,1),(-3,6,1),(1,6,-1),(3,6,-1),(3,6,1),(1,6,1)],[(0,1,2,3),(4,5,6,7)])
analyse('stepped',[(-3,6,-1),(0,6,-1),(0,6,1),(-3,6,1),(0,7,-1),(3,7,-1),(3,7,1),(0,7,1)],[(0,1,2,3),(4,5,6,7)])
analyse('flat',[(-3,6,-1),(3,6,-1),(3,6,1),(-3,6,1)],[(0,1,2,3)])
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,3,0));block=c.object;block.scale=(.2,.0001,2);c.view_layer.update()
r=analysis_runtime.analyse(c,wall,objects,8192);assert 80<r['statistics']['coverage_percent']<99;rstats=r['statistics'];results['thin_blocker']=rstats
bpy.data.objects.remove(block,do_unlink=True);bpy.data.objects.remove(wall,do_unlink=True)
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,6,0));wall=c.object;wall['beam_receiver_uuid']='d2ffb8f6-ab0b-4521-97cf-13e6bbed52a5';c.view_layer.update()
r=analysis_runtime.analyse(c,wall,objects,8192);s=r['statistics'];assert 15<s['coverage_percent']<25,s;assert s['occluded_sample_percent']>60,s;results['closed_box']=s
(root/'work/production/surface-tests.json').write_text(json.dumps(results,indent=2));print('PRODUCTION SURFACES PASS')
addon.unregister()
