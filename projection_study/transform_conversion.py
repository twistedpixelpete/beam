"""Single Blender → Mapping Matter CSV boundary, reference convention v1.

World XYZ is shared, Z up, mm. A neutral MM projector points +Y, up +Z;
Beam's optical frame points local -Z, up +Y. MM rotates Rz(yaw) @ Rx(pitch)
@ Ry(roll). MM shift percentages use HALF image dimensions (Beam uses full).
CSV target is a virtual optical-axis point at shifted-hit axial depth, not the
shifted physical surface hit. Controlled Mapping Matter exports prove this
convention. The separate Designer-study schema is tested in Mapping Matter,
not in the Designer application.
"""
import math
CONVENTION_ID='beam_mapping_matter_transform_v1'
CONVENTION='Mapping Matter v1: XYZ mm; Rz(yaw) Rx(pitch) Ry(roll); half-image shift; virtual axial target'
VALIDATED=False  # Actual Designer import remains unverified.
REFERENCE_VALIDATED=True

def position_mm(position_blender,metres_per_unit):return tuple(float(v)*metres_per_unit*1000 for v in position_blender)

def orientation_degrees(rotation_matrix):
    from mathutils import Matrix
    native=rotation_matrix@Matrix.Rotation(-math.pi/2,3,'X')
    e=native.to_euler('YXZ')
    return tuple(math.degrees(v) for v in (e.x,e.z,e.y))

def lens_shift_percent(horizontal,vertical):return 2*horizontal,2*vertical

def csv_target(origin,rotation,axial_distance_m,metres_per_unit):
    from mathutils import Vector
    return position_mm(origin+rotation@Vector((0,0,-axial_distance_m/metres_per_unit)),metres_per_unit)

# Designer Projector Study CSV, as consumed by Mapping Matter's Designer importer.
# UI probe: Designer (x,y,z) -> MM (x,z,y); rotation (x,y,z) -> MM (x,-z,-y).
DESIGNER_CONVENTION_ID='beam_designer_transform_v1'
DESIGNER_IMPORT_VALIDATED=True  # Ten actual Mapping Matter imports/reexports; not the Designer application.

def designer_position_m(position_blender,metres_per_unit):
    x,y,z=(float(v)*metres_per_unit for v in position_blender)
    return x,z,y

def designer_orientation_degrees(rotation_matrix):
    pitch,yaw,roll=orientation_degrees(rotation_matrix)
    return pitch,-yaw,-roll

def designer_lens_shift(horizontal,vertical):
    h,v=lens_shift_percent(horizontal,vertical)
    return h/100,v/100
