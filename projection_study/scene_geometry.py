"""Shared evaluated surface cache; no projector targeting or GPU policy here."""
from dataclasses import dataclass
from itertools import product
import bpy
from mathutils import Vector

SURFACE_TYPES={'MESH','CURVE','SURFACE','FONT','META'}
@dataclass
class Surface:
    name: str
    vertices: list
    triangles: list
    bounds: list

SURFACES={}
revision=0
_dirty=True
_dirty_keys=set()
_context=None


def invalidate(keys=None):
    global _dirty
    if keys is None: _dirty=True
    else: _dirty_keys.update(keys)


def clear():
    global _context,revision
    SURFACES.clear(); _dirty_keys.clear(); _context=None; revision+=1
    invalidate()


def prepare():
    global _dirty,_context,revision
    context=(bpy.context.scene.as_pointer(),bpy.context.view_layer.as_pointer())
    if not _dirty and not _dirty_keys and context==_context: return
    full=_dirty or context!=_context
    if full: SURFACES.clear()
    else:
        for key in _dirty_keys: SURFACES.pop(key,None)
    grouped={}; names={}
    graph=bpy.context.evaluated_depsgraph_get()
    for instance in graph.object_instances:
        obj=instance.object; original=obj.original; key=original.as_pointer()
        if not full and key not in _dirty_keys: continue
        if obj.type not in SURFACE_TYPES or original.ps.is_projector or original.get('ps_helper') or original.get('beam_screen_detail'): continue
        if not instance.show_self or (not instance.is_instance and not original.visible_get()): continue
        names[key]=original.name
        vertices,triangles=grouped.setdefault(key,([],[]))
        mesh=obj.to_mesh()
        if mesh is None: continue
        try:
            mesh.calc_loop_triangles()
            offset=len(vertices); matrix=instance.matrix_world
            vertices.extend(matrix@v.co for v in mesh.vertices)
            triangles.extend(tuple(offset+i for i in tri.vertices) for tri in mesh.loop_triangles)
        finally: obj.to_mesh_clear()
    for key,(vertices,triangles) in grouped.items():
        if not triangles: continue
        low=[min(v[i] for v in vertices) for i in range(3)]
        high=[max(v[i] for v in vertices) for i in range(3)]
        bounds=[Vector(p) for p in product(*zip(low,high))]
        SURFACES[key]=Surface(names[key],vertices,triangles,bounds)
    _dirty=False; _dirty_keys.clear(); _context=context; revision+=1


def beam_depth(origin,rotation,minimum):
    """Extent encloses scene receivers; NEVER depends on centre-ray distance."""
    prepare()
    forward=rotation@Vector((0,0,-1))
    far=max((forward.dot(v-origin) for s in SURFACES.values() for v in s.bounds),default=minimum)
    return max(minimum,far*1.05)
