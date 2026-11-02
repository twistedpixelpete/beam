"""Lightweight engineering raycasts against shared evaluated surface geometry."""
import bpy
from mathutils.bvhtree import BVHTree
from . import scene_geometry

# Trees live in each surface's local space and are keyed by geometry, so moving
# an object transforms the ray instead of rebuilding its tree.
_trees={}


def invalidate(keys=None): scene_geometry.invalidate(keys)

def moved(objects): scene_geometry.moved(objects)

def clear():
    _trees.clear(); scene_geometry.clear()


def build_tree(surface):
    # Native construction is faster and avoids a large temporary Python list.
    source=surface.source
    if surface.movable and source is not None:
        try:
            if source.type=='MESH':
                graph=bpy.context.evaluated_depsgraph_get()
                return BVHTree.FromObject(source.evaluated_get(graph),graph)
        except (ReferenceError,ValueError):pass
    return BVHTree.FromPolygons(surface.local_vertices.tolist(),surface.triangles.tolist(),all_triangles=True)


def prepare():
    scene_geometry.prepare()
    for key in list(_trees):
        if key not in scene_geometry.SURFACES: _trees.pop(key,None)
    for key,surface in scene_geometry.SURFACES.items():
        cached=_trees.get(key)
        if not cached or cached[0]!=surface.geometry_id:
            _trees[key]=(surface.geometry_id,build_tree(surface))


def cast(origin,direction,target=None):
    """Optional restriction is for callers/tools only; engineering casts use all."""
    prepare()
    best=None
    keys=[target.as_pointer()] if target else _trees
    for key in keys:
        entry=_trees.get(key)
        if entry is None: continue
        surface=scene_geometry.SURFACES[key];tree=entry[1]
        if surface.movable:
            matrix=surface.matrix;inverse=matrix.inverted_safe()
            position,normal,index,distance=tree.ray_cast(inverse@origin,inverse.to_3x3()@direction)
            if position is None: continue
            position=matrix@position
            normal=(inverse.to_3x3().transposed()@normal).normalized()
            distance=(position-origin).length
        else:
            position,normal,index,distance=tree.ray_cast(origin,direction)
            if position is None: continue
        if distance>1e-6 and (best is None or distance<best[2]):
            best=(position,normal,distance,surface.name)
    return best
