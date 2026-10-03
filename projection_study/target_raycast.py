"""Lightweight engineering raycasts against shared evaluated surface geometry."""
from mathutils.bvhtree import BVHTree
from . import scene_geometry

_trees={}


def invalidate(keys=None): scene_geometry.invalidate(keys)

def clear():
    _trees.clear(); scene_geometry.clear()


def prepare():
    scene_geometry.prepare()
    for key in list(_trees):
        if key not in scene_geometry.SURFACES: _trees.pop(key,None)
    for key,surface in scene_geometry.SURFACES.items():
        cached=_trees.get(key)
        if not cached or cached[0] is not surface:
            _trees[key]=(surface,BVHTree.FromPolygons(surface.vertices,surface.triangles,all_triangles=True))


def cast(origin,direction,target=None):
    """Optional restriction is for callers/tools only; engineering casts use all."""
    prepare()
    best=None
    entries=[_trees.get(target.as_pointer())] if target else _trees.values()
    for entry in entries:
        if entry is None: continue
        surface,tree=entry
        position,normal,index,distance=tree.ray_cast(origin,direction)
        if position is not None and distance>1e-6 and (best is None or distance<best[2]):
            best=(position,normal,distance,surface.name)
    return best
