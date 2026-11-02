"""Shared evaluated surface cache; no projector targeting or GPU policy here.

Vertices are held as compact arrays. A surface that isn't instanced keeps its geometry in
object space, so moving that object replaces only its matrix: the mesh is not
read again and the ray-cast tree (see target_raycast) is reused.
"""
from dataclasses import dataclass
from itertools import count, product
import bpy
import numpy as np
from mathutils import Matrix, Vector

SURFACE_TYPES={'MESH','CURVE','SURFACE','FONT','META'}
_geometry_ids=count(1)


@dataclass
class Surface:
    name: str
    vertices: np.ndarray    # (N,3) float32, world space
    triangles: np.ndarray   # (M,3) int32
    bounds: list
    local_vertices: np.ndarray  # (N,3) float32, the space of `matrix`
    matrix: Matrix          # Identity when several instances were merged
    geometry_id: int        # Changes only when the mesh itself changes
    movable: bool           # One instance, so a transform can be applied alone


SURFACES={}
revision=0
_dirty=True
_dirty_keys=set()
_moved={}
_context=None


def invalidate(keys=None):
    global _dirty
    if keys is None: _dirty=True
    else: _dirty_keys.update(keys)


def moved(objects):
    """Record objects whose transform changed while their geometry did not."""
    _moved.update((obj.as_pointer(),obj) for obj in objects)


def clear():
    global _context,revision
    SURFACES.clear(); _dirty_keys.clear(); _moved.clear(); _context=None; revision+=1
    invalidate()


def to_world(vertices,matrix):
    m=np.array(matrix,dtype=np.float64)
    return (vertices.astype(np.float64)@m[:3,:3].T+m[:3,3]).astype(np.float32)


def world_bounds(vertices):
    return [Vector(p) for p in product(*zip(vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()))]


def mesh_arrays(mesh):
    """Read a mesh's vertices and triangles without creating Python objects per vertex."""
    mesh.calc_loop_triangles()
    vertices=np.empty(len(mesh.vertices)*3,np.float32); mesh.vertices.foreach_get('co',vertices)
    triangles=np.empty(len(mesh.loop_triangles)*3,np.int32); mesh.loop_triangles.foreach_get('vertices',triangles)
    return vertices.reshape(-1,3),triangles.reshape(-1,3)


def apply_moved(graph):
    """True when every pending move was applied without reading a mesh again."""
    for key,obj in _moved.items():
        surface=SURFACES.get(key)
        if key in _dirty_keys or surface is None:continue
        if not surface.movable:
            _dirty_keys.add(key);continue
        try:matrix=obj.evaluated_get(graph).matrix_world.copy()
        except ReferenceError:
            _dirty_keys.add(key);continue
        vertices=to_world(surface.local_vertices,matrix)
        SURFACES[key]=Surface(surface.name,vertices,surface.triangles,world_bounds(vertices),surface.local_vertices,matrix,surface.geometry_id,True)
    changed=bool(_moved)
    _moved.clear()
    return changed


def prepare():
    global _dirty,_context,revision
    context=(bpy.context.scene.as_pointer(),bpy.context.view_layer.as_pointer())
    if not _dirty and not _dirty_keys and not _moved and context==_context: return
    graph=bpy.context.evaluated_depsgraph_get()
    full=_dirty or context!=_context
    if full:
        SURFACES.clear();_moved.clear()
    elif apply_moved(graph) and not _dirty_keys:
        revision+=1;return
    if not full:
        for key in _dirty_keys: SURFACES.pop(key,None)
    from .projector_object import is_projector_model
    grouped={}; names={}
    for instance in graph.object_instances:
        obj=instance.object; original=obj.original; key=original.as_pointer()
        if not full and key not in _dirty_keys: continue
        if obj.type not in SURFACE_TYPES or original.ps.is_projector or original.get('ps_helper') or original.get('beam_screen_detail') or is_projector_model(original): continue
        if not instance.show_self or (not instance.is_instance and not original.visible_get()): continue
        names[key]=original.name
        parts=grouped.setdefault(key,[])
        mesh=obj.to_mesh()
        if mesh is None: continue
        try:
            parts.append((*mesh_arrays(mesh),instance.matrix_world.copy(),instance.is_instance))
        finally: obj.to_mesh_clear()
    for key,parts in grouped.items():
        parts=[part for part in parts if len(part[1])]
        if not parts: continue
        if len(parts)==1 and not parts[0][3]:
            local,triangles,matrix,_=parts[0]
            vertices=to_world(local,matrix)
            movable=True
        else:
            # Instances also depend on their instancer; they rebuild when moved.
            offsets=np.cumsum([0]+[len(part[0]) for part in parts[:-1]],dtype=np.int32)
            triangles=np.concatenate([part[1]+offset for part,offset in zip(parts,offsets)])
            vertices=np.concatenate([to_world(part[0],part[2]) for part in parts])
            local,matrix,movable=vertices,Matrix.Identity(4),False
        SURFACES[key]=Surface(names[key],vertices,triangles,world_bounds(vertices),local,matrix,next(_geometry_ids),movable)
    _dirty=False; _dirty_keys.clear(); _context=context; revision+=1


def beam_depth(origin,rotation,minimum):
    """Extent encloses scene receivers; NEVER depends on centre-ray distance."""
    prepare()
    forward=rotation@Vector((0,0,-1))
    far=max((forward.dot(v-origin) for s in SURFACES.values() for v in s.bounds),default=minimum)
    return max(minimum,far*1.05)
