import math
import bpy
from mathutils import Matrix
from .utils import next_identifier, new_uuid, PALETTE


def projectors(scene):
    return [o for o in scene.objects if o.ps.is_projector]


def selected(context):
    from .study_data import active
    return active(context)


def body_mesh(name, unit):
    verts, faces = [], []
    # Optical origin is lens centre. Local -Z points forward, +Y up.
    for x,y,z in [(-.30,-.16,.06),(.30,-.16,.06),(.30,.16,.06),(-.30,.16,.06),
                  (-.30,-.16,.76),(.30,-.16,.76),(.30,.16,.76),(-.30,.16,.76)]:
        verts.append((x/unit,y/unit,z/unit))
    faces.extend([(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    for z in (0,.08):
        for i in range(24):
            a = i*math.tau/24
            verts.append((.105*math.cos(a)/unit,.105*math.sin(a)/unit,z/unit))
    for i in range(24):
        j = (i+1)%24
        faces.append((8+i,8+j,32+j,32+i))
    faces.append(tuple(range(8,32)))
    mesh = bpy.data.meshes.new(name+' Body')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def create(context, source=None):
    scene = context.scene
    unit = scene.unit_settings.scale_length
    name = next_identifier([o.ps.identifier for o in projectors(scene)] + list(bpy.data.objects.keys()))
    obj = bpy.data.objects.new(name, body_mesh(name, unit))
    context.collection.objects.link(obj)
    p = obj.ps
    if source:
        for prop in p.bl_rna.properties:
            if prop.identifier not in {'rna_type','is_projector','uuid','identifier'} and not prop.is_readonly:
                setattr(p, prop.identifier, getattr(source.ps, prop.identifier))
        obj.matrix_world = source.matrix_world.copy()
        if p.image:p.image=p.image.copy()
    else:
        obj.location = scene.cursor.location
        obj.rotation_euler = (math.pi/2,0,0) # forward +Y; up +Z
        p.colour = PALETTE[(int(name[2:])-1)%len(PALETTE)]
    p.colour = PALETTE[(int(name[2:])-1)%len(PALETTE)]
    p.identifier, p.uuid, p.is_projector = name, new_uuid(), True
    for suffix,colour in [('Chassis',(.085,.10,.12,1)),('Lens',(.025,.06,.075,1))]:
        material = bpy.data.materials.get('Beam '+suffix)
        if material is None:
            material = bpy.data.materials.new('Beam '+suffix)
            material.diffuse_color = colour
        obj.data.materials.append(material.copy())
    obj.data.polygons[-1].material_index = 1
    obj.lock_scale = (True,True,True)
    obj.color = (*p.colour,1)
    obj.show_name = False
    ensure_optics(obj, context.collection, unit)
    for item in context.selected_objects:
        item.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    context.scene.ps_study.active_projector = obj
    from . import runtime
    runtime._owners[p.uuid]=obj.as_pointer()
    runtime.invalidate()
    from .local_orientation import sync
    sync(context)
    return obj


def ensure_optics(obj, collection, unit):
    existing=next((c for c in obj.children if c.type=='CAMERA' and c.get('ps_helper')),None)
    if existing:
        if existing.data.users>1: existing.data=existing.data.copy()
        return
    cam = bpy.data.objects.new(obj.ps.identifier+' · Optics', bpy.data.cameras.new(obj.ps.identifier+' Optics'))
    collection.objects.link(cam)
    cam.parent = obj
    cam.matrix_parent_inverse = Matrix.Identity(4)
    cam.hide_select = True
    cam.hide_render = True
    cam['ps_helper'] = True
    cam.data.display_size = .08/unit
