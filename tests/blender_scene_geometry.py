"""Array-backed surfaces, move-without-rebuild and idle scheduling. Background, no GPU."""
import bpy,sys,time,random
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import numpy as np
import projection_study as addon
from projection_study import runtime,scene_geometry as geo,target_raycast as rays,projector_object,cycles_projection,analysis_runtime,screens
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
addon.register();c=bpy.context;scene=c.scene


def grid(name,n=20,size=10,y=10):
    v=[(x*size/n-size/2,y,z*size/n) for z in range(n+1) for x in range(n+1)]
    f=[(i+j*(n+1),i+1+j*(n+1),i+1+(j+1)*(n+1),i+(j+1)*(n+1)) for j in range(n) for i in range(n)]
    m=bpy.data.meshes.new(name);m.from_pydata(v,[],f);m.update()
    o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);return o


def settle():
    c.view_layer.update();rays.prepare()


def reference(origin,direction):
    """Brute force against freshly evaluated world geometry, independent of the cache."""
    graph=c.evaluated_depsgraph_get();best=None
    for inst in graph.object_instances:
        o=inst.object
        if o.type not in geo.SURFACE_TYPES or o.original.ps.is_projector or o.original.get('ps_helper'):continue
        if not inst.show_self or (not inst.is_instance and not o.original.visible_get()):continue
        mesh=o.to_mesh();mesh.calc_loop_triangles()
        tree=BVHTree.FromPolygons([inst.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
        o.to_mesh_clear();hit=tree.ray_cast(origin,direction)
        if hit[0] is not None and hit[3]>1e-6 and (best is None or hit[3]<best[0]):best=(hit[3],hit[0],o.original.name)
    return best


def agree(tries=200):
    random.seed(9)
    for _ in range(tries):
        origin=Vector((random.uniform(-8,8),random.uniform(-3,3),random.uniform(0,12)))
        direction=(Vector((random.uniform(-6,6),10,random.uniform(0,10)))-origin).normalized()
        expected=reference(origin,direction);actual=rays.cast(origin,direction)
        assert (expected is None)==(actual is None),(origin,direction,expected,actual)
        if expected:
            assert actual[3]==expected[2],(actual[3],expected[2])
            assert abs(actual[2]-expected[0])<2e-4,(actual[2],expected[0])
            assert (actual[0]-expected[1]).length<2e-4


wall=grid('Wall');moved=grid('Moved',y=7);moved.location=(1,0,1);moved.rotation_euler=(0,.3,.2);moved.scale=(1.4,.7,1.2)
child=grid('Child',n=5,size=2,y=5);child.parent=moved
settle()
assert isinstance(geo.SURFACES[wall.as_pointer()].vertices,np.ndarray)
assert geo.SURFACES[wall.as_pointer()].vertices.dtype==np.float32 and geo.SURFACES[wall.as_pointer()].triangles.dtype==np.int32
agree()

# Moving reuses the tree and the mesh arrays, and the hits follow the object.
key=moved.as_pointer();tree=rays._trees[key];ident=geo.SURFACES[key].geometry_id;local=geo.SURFACES[key].local_vertices;rev=geo.revision
built=[];original_build=rays.build_tree;rays.build_tree=lambda s:(built.append(s.name),original_build(s))[1]
moved.location=(-2,1,2);c.view_layer.update();settle()
assert not built,f'a move rebuilt {built}';assert rays._trees[key] is tree and geo.SURFACES[key].geometry_id==ident and geo.SURFACES[key].local_vertices is local
assert geo.revision>rev,'depth maps must see the move'
agree()
# A parent's move reaches the child, also without a rebuild.
moved.rotation_euler=(.1,.1,.4);c.view_layer.update();settle();assert not built;agree()
# A geometry edit does rebuild, and only that object.
moved.data.vertices[0].co.y-=1;moved.data.update();c.view_layer.update();settle()
assert built==['Moved'],built;built.clear();agree()
# A modifier change is a geometry change.
mod=moved.modifiers.new('Sub','SUBSURF');mod.levels=1;c.view_layer.update();settle();assert 'Moved' in built;built.clear();agree()
rays.build_tree=original_build

# Instances bake in world space and rebuild when their source moves.
source=grid('Source',n=2,size=2,y=4);source.hide_viewport=False
collection=bpy.data.collections.new('Inst');collection.objects.link(source);scene.collection.objects.unlink(source)
instancer=bpy.data.objects.new('Instancer',None);instancer.instance_type='COLLECTION';instancer.instance_collection=collection;instancer.location=(0,-1,2);scene.collection.objects.link(instancer)
c.view_layer.update();runtime.invalidate();rays.invalidate();settle()
assert not geo.SURFACES[source.as_pointer()].movable;agree()
instancer.location=(1,-1,3);c.view_layer.update();runtime.depsgraph_changed(scene,c.evaluated_depsgraph_get());rays.invalidate();settle();agree()
bpy.data.objects.remove(instancer,do_unlink=True)

# A curve and a hidden object behave as before.
curve=bpy.data.curves.new('Text','FONT');text=bpy.data.objects.new('Text',curve);scene.collection.objects.link(text);curve.body='B';text.location=(0,2,3);text.rotation_euler=(1.57,0,0)
c.view_layer.update();rays.invalidate();settle();assert text.as_pointer() in geo.SURFACES;agree(60)
wall.hide_set(True);c.view_layer.update();runtime.refresh();rays.invalidate();settle();assert wall.as_pointer() not in geo.SURFACES;agree(40);wall.hide_set(False)
c.view_layer.update();rays.invalidate();settle()

# Analysis over array surfaces: area and coverage from a known plane.
bpy.data.objects.remove(text,do_unlink=True);bpy.data.objects.remove(child,do_unlink=True);bpy.data.objects.remove(moved,do_unlink=True)
pj=projector_object.create(c);pj.location=(0,0,5);pj.rotation_euler=(1.5707963,0,0);c.view_layer.update();runtime.refresh(True)
stats=analysis_runtime.analyse(c,wall,[pj],256)['statistics']
assert abs(stats['surface_area_m2']-100)<1e-3,stats['surface_area_m2'];assert stats['sample_count']==256 and stats['coverage_percent']>0

# Idle ticks skip whole-scene work; every kind of change is still noticed.
for i in range(200):scene.collection.objects.link(bpy.data.objects.new(f'Empty{i}',None))
c.view_layer.update();runtime.refresh(True);runtime.tick()
counted=[];original=runtime.repair_identities
runtime.repair_identities=lambda *a:(counted.append(1),original(*a))[1]
runtime._next_heartbeat=time.monotonic()+60
for _ in range(10):runtime.refresh(idle_ok=True)
assert not counted,'idle tick scanned the scene'
extra=bpy.data.objects.new('Added',None);scene.collection.objects.link(extra);c.view_layer.update();runtime.refresh(idle_ok=True);assert counted,'added object not scanned';counted.clear()
runtime.refresh(idle_ok=True);assert not counted
# Native-style duplicate reaches identity repair and gets its own identity.
dup=pj.copy();dup.data=pj.data;scene.collection.objects.link(dup);c.view_layer.update();runtime.refresh(idle_ok=True)
assert counted and dup.ps.uuid!=pj.ps.uuid and dup.ps.identifier!=pj.ps.identifier and dup.data!=pj.data;counted.clear()
# The heartbeat catches a change no depsgraph update reported.
quiet=projector_object.create(c);quiet.ps.uuid='';runtime.refresh(idle_ok=True);runtime._next_heartbeat=0;runtime._seen_structure=runtime.structure;runtime._dirty=False;runtime.refresh(idle_ok=True);assert counted and quiet.ps.uuid
runtime.repair_identities=original
# A projector property still updates the cache without a whole-scene scan.
c.view_layer.update();runtime.refresh(True);pj.ps.throw_ratio=1.7;c.view_layer.update();runtime.refresh(idle_ok=True);assert abs(runtime.CACHE[pj.as_pointer()]['metrics'].width-runtime.CACHE[pj.as_pointer()]['metrics'].distance/1.7)<1e-3
# Moving a projector with a parent updates through the signature check.
empty=bpy.data.objects.new('Rig',None);scene.collection.objects.link(empty);pj.parent=empty;c.view_layer.update();runtime.refresh();before=runtime.CACHE[pj.as_pointer()]['origin'].copy()
empty.location=(0,1,0);c.view_layer.update();runtime.refresh();assert (runtime.CACHE[pj.as_pointer()]['origin']-before).length>.5
# Quiet Cycles and screen timers don't rescan.
calls=[];sync=cycles_projection.sync;cycles_projection.sync=lambda s:(calls.append(1),sync(s))[1]
cycles_projection.tick();calls.clear();cycles_projection._next_heartbeat=time.monotonic()+60;cycles_projection.tick();assert not calls
pj.ps.brightness=50;c.view_layer.update();cycles_projection.tick();assert calls,'Cycles missed a projector edit';cycles_projection.sync=sync
print('SCENE GEOMETRY PASS: casts match brute force through moves, edits, modifiers, instances and curves; moves reuse trees; idle ticks skip scene scans')
addon.unregister()
