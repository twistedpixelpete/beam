"""Single Blender → Mapping Matter CSV boundary, reference convention v1.

World XYZ is shared, Z up, mm. A neutral MM projector points +Y, up +Z;
Beam's optical frame points local -Z, up +Y. MM rotates Rz(yaw) @ Rx(pitch)
@ Ry(roll). MM shift percentages use HALF image dimensions (Beam uses full).
CSV target is a virtual optical-axis point at shifted-hit axial depth, not the
shifted physical surface hit. Controlled Mapping Matter exports prove this
convention; a Designer import has not been performed.
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
