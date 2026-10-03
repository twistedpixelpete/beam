"""Small 30 Hz dirty scheduler. GPU drawing only consumes cached results."""
import bpy
import math
from bpy.app.handlers import persistent
from mathutils import Vector
from .projector_object import projectors
from .projection_math import calculate, image_point, camera_parameters

CACHE = {}
_dirty = True
_busy = False
_signatures = {}
_dirty_ids = set()
_owners = {}
_known_objects = None
_context = None
_venue_membership = None


def invalidate(obj=None):
    global _dirty
    if obj is None: _dirty = True
    elif isinstance(obj,bpy.types.Object): _dirty_ids.add(obj.as_pointer())


def frame(obj):
    matrix = obj.matrix_world
    return matrix.translation.copy(), matrix.to_quaternion().to_matrix()


def optics(obj):
    return next((c for c in obj.children if c.type=='CAMERA' and c.get('ps_helper')), None)


def update_one(obj, scene):
    p = obj.ps
    origin, rotation = frame(obj)
    unit = scene.unit_settings.scale_length
    depth = p.preview_distance
    hit = None
    # Added by target milestone; geometry and maths remain separate.
    try:
        from .target_raycast import cast
        direction = rotation @ Vector(image_point(.5,.5,1,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v))
        hit = cast(origin, direction.normalized())
    except ImportError:
        pass
    target=bpy.data.objects.get(hit[3]) if hit else None
    if p.target!=target: p.target=target
    point=tuple(v*unit for v in hit[0]) if hit else (0,0,0)
    if any(not math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7) for a,b in zip(p.target_point_m,point)): p.target_point_m=point
    if p.has_target!=bool(hit): p.has_target=bool(hit)
    if hit:
        depth = -(rotation.transposed() @ (hit[0]-origin)).z*unit
    if not math.isclose(p.target_distance_m,depth if hit else 0,rel_tol=1e-6,abs_tol=1e-7): p.target_distance_m=depth if hit else 0
    from . import scene_geometry
    beam_depth=scene_geometry.beam_depth(origin,rotation,p.preview_distance/unit)
    uv_image=None
    if p.output_mode in {'UV_GRID','COLOR_GRID'}:
        from .projection_images import ensure_uv_grid
        uv_image=ensure_uv_grid(p.resolution_x,p.resolution_y,p.output_mode)
    m = calculate(depth,p.throw_ratio,p.resolution_x,p.resolution_y,p.lumens,p.brightness,p.stack)
    def world(u,v):
        return origin + rotation @ (Vector(image_point(u,v,depth/unit,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v)))
    corners = [world(0,0),world(1,0),world(1,1),world(0,1)]
    from .frustum_helpers import endpoints
    helper_corners=endpoints(origin,corners)
    beam_corners=[origin+rotation@Vector(image_point(u,v,beam_depth,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v))
                  for u,v in ((0,0),(1,0),(1,1),(0,1))]
    cam = optics(obj)
    if cam:
        for key,value in camera_parameters(p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v).items():
            if getattr(cam.data,key)!=value: setattr(cam.data,key,value)
    if tuple(obj.color[:3]) != tuple(p.colour): obj.color=(*p.colour,1)
    return dict(metrics=m, hit=hit, origin=origin, rotation=rotation, corners=corners,
                centre=world(.5,.5), world=world, helper_corners=helper_corners, beam_corners=beam_corners, beam_depth=beam_depth, uv_image=uv_image,
                slant=(hit[0]-origin).length*unit if hit else None)


def refresh(force=False):
    global _dirty, _busy, _context, _venue_membership
    if _busy or not hasattr(bpy.types.Object,'ps'): return
    _busy = True
    did_change = False
    try:
        scene = bpy.context.scene
        current = (scene.as_pointer(),bpy.context.view_layer.as_pointer())
        if current!=_context:
            reset(); _context=current
        from .study_data import sync_selection
        did_change = sync_selection(bpy.context) or did_change
        membership=tuple((o.as_pointer(),o.data.as_pointer() if o.data else 0,o.visible_get())
                         for o in scene.objects if o.type in {'MESH','CURVE','SURFACE','FONT','META'} and not o.ps.is_projector and not o.get('ps_helper'))
        if membership!=_venue_membership:
            from . import target_raycast
            target_raycast.invalidate(); invalidate()
            _venue_membership=membership
        from . import group_lifecycle,local_orientation
        if group_lifecycle.defer_native_copy(bpy.context):return False
        group_lifecycle.reconcile(bpy.context)
        local_orientation.sync(bpy.context)
        live = projectors(scene)
        repair_identities(live,scene)
        keys = {o.as_pointer() for o in live}
        for key in list(CACHE):
            if key not in keys:
                CACHE.pop(key,None); _signatures.pop(key,None)
                did_change = True
        for obj in live:
            key = obj.as_pointer()
            signature = (tuple(v for row in obj.matrix_world for v in row), scene.unit_settings.scale_length)
            if force or _dirty or key in _dirty_ids or _signatures.get(key)!=signature:
                CACHE[key] = update_one(obj, scene)
                did_change = True
                _signatures[key] = signature
        group_lifecycle.prune(bpy.context)
        for group in scene.ps_study.blend_groups: group_lifecycle.snapshot_if_needed(group,bpy.context,force or did_change)
        _dirty = False
        _dirty_ids.clear()
    finally:
        _busy = False
    return did_change


def tick():
    changed = refresh()
    if not changed: return 1/30
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type=='VIEW_3D': area.tag_redraw()
    return 1/30

@persistent
def depsgraph_changed(scene, depsgraph):
    if _busy: return
    from . import target_raycast
    changed_keys=set()
    broad=False
    for update in depsgraph.updates:
        item=update.id.original
        if isinstance(item,bpy.types.Object):
            if item.ps.is_projector:
                invalidate(item); continue
            if item.get('ps_helper') or item.type in {'CAMERA','LIGHT'}: continue
            if not (update.is_updated_transform or update.is_updated_geometry): continue
            if item.type in {'MESH','CURVE','SURFACE','FONT','META'}: changed_keys.add(item.as_pointer())
            elif item.instance_type!='NONE': broad=True
        elif isinstance(item,(bpy.types.Mesh,bpy.types.Curve,bpy.types.MetaBall)) and update.is_updated_geometry:
            changed_keys.update(o.as_pointer() for o in scene.objects
                                if o.type in {'MESH','CURVE','SURFACE','FONT','META'} and o.data==item and not o.ps.is_projector)
        elif isinstance(item,bpy.types.Collection): broad=True
    if broad:
        target_raycast.invalidate(); invalidate()
    elif changed_keys:
        target_raycast.invalidate(changed_keys)
        # Automatic first-hit targets mean any moved surface can become nearer.
        # One centre ray/projector is cheap; only changed surface BVHs rebuild.
        for obj in projectors(scene): invalidate(obj)

@persistent
def reset(*args):
    global _venue_membership,_known_objects
    _known_objects=None
    _venue_membership=None
    from . import target_raycast
    target_raycast.clear()
    CACHE.clear(); _signatures.clear(); _dirty_ids.clear(); invalidate()
    from . import viewport_display
    viewport_display.clear()


def register():
    for handlers,fn in [(bpy.app.handlers.depsgraph_update_post,depsgraph_changed),
                        (bpy.app.handlers.load_post,reset),(bpy.app.handlers.undo_post,reset),
                        (bpy.app.handlers.redo_post,reset)]:
        if fn not in handlers: handlers.append(fn)
    if not bpy.app.timers.is_registered(tick): bpy.app.timers.register(tick,persistent=True)


def unregister():
    if bpy.app.timers.is_registered(tick): bpy.app.timers.unregister(tick)
    for handlers,fn in [(bpy.app.handlers.depsgraph_update_post,depsgraph_changed),
                        (bpy.app.handlers.load_post,reset),(bpy.app.handlers.undo_post,reset),
                        (bpy.app.handlers.redo_post,reset)]:
        if fn in handlers: handlers.remove(fn)
    reset()


def repair_identities(live,scene):
    global _known_objects
    from .utils import new_uuid,next_identifier,PALETTE
    from .projector_object import ensure_optics
    existing=[o for o in bpy.data.objects if o.ps.is_projector]
    used={o.ps.identifier for o in existing}
    global_ids={o.as_pointer() for o in existing}
    incoming=set() if _known_objects is None else global_ids-_known_objects
    fresh_copies={o.as_pointer() for o in existing if o.as_pointer() in incoming and o.ps.uuid and _owners.get(o.ps.uuid)!=o.as_pointer()}
    _known_objects=global_ids
    for identity,key in list(_owners.items()):
        if key not in global_ids: _owners.pop(identity,None)
    # Keep ownership across scene switches and paste into another scene.
    for item in sorted(existing,key=lambda o: (o.name!=o.ps.identifier,o.name)):
        if item.ps.uuid: _owners.setdefault(item.ps.uuid,item.as_pointer())
    grouped={m.projector.as_pointer() for s in bpy.data.scenes for g in s.ps_study.blend_groups for m in g.members if m.projector}
    seen_uuid=set(); seen_name=set()
    # Prefer existing ownership when Blender Shift-D copied a UUID.
    ordered=sorted(live,key=lambda o: _owners.get(o.ps.uuid)!=o.as_pointer())
    for obj in ordered:
        p=obj.ps
        if p.data_version<1:
            obj.show_name=False
            p.data_version=1
        duplicate=obj.as_pointer() in fresh_copies or p.uuid in seen_uuid or p.identifier in seen_name or (p.uuid in _owners and _owners[p.uuid]!=obj.as_pointer())
        if duplicate:
            if obj.parent and obj.parent.get('beam_layout_slot') and obj.as_pointer() not in grouped:
                world=obj.matrix_world.copy(); obj.parent=None; obj.matrix_world=world
            if obj.data: obj.data=obj.data.copy()
            if p.image:p.image=p.image.copy()
            for slot in obj.material_slots:
                if slot.material: slot.material=slot.material.copy()
        elif obj.data and obj.data.users>1:
            # Alt-D must not link the projector's editable body mesh.
            obj.data=obj.data.copy()
        if not p.uuid or duplicate:
            if _owners.get(p.uuid)==obj.as_pointer(): _owners.pop(p.uuid,None)
            p.uuid=new_uuid()
        if not p.identifier or duplicate:
            p.identifier=next_identifier(used | set(bpy.data.objects.keys()))
            used.add(p.identifier); obj.name=p.identifier
            if duplicate: p.colour=PALETTE[(int(p.identifier[2:])-1)%len(PALETTE)]
        seen_uuid.add(p.uuid); seen_name.add(p.identifier)
        _owners[p.uuid]=obj.as_pointer()
        # Appended scenes can receive repaired projector UUIDs. Keep their
        # explicit group references in step without relying on display names.
        for group in scene.ps_study.blend_groups:
            for member in group.members:
                if member.projector==obj and member.projector_uuid!=p.uuid:
                    if group.anchor_uuid==member.projector_uuid: group.anchor_uuid=p.uuid
                    member.projector_uuid=p.uuid
        ensure_optics(obj,obj.users_collection[0],scene.unit_settings.scale_length)
    for obj in list(scene.objects):
        if obj.get('ps_helper') and (not obj.parent or not obj.parent.ps.is_projector):
            bpy.data.objects.remove(obj,do_unlink=True)


def rigid(obj):
    matrix=obj.matrix_world.to_3x3()
    cols=[matrix.col[i] for i in range(3)]
    return (abs(matrix.determinant()-1)<1e-4 and
            all(abs(c.length-1)<1e-4 for c in cols) and
            all(abs(cols[i].dot(cols[j]))<1e-4 for i,j in ((0,1),(0,2),(1,2))))
