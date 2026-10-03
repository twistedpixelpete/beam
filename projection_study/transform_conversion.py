"""The ONLY boundary for Blender -> disguise transforms.

No disguise axis/Euler convention has been validated. v0.1 intentionally emits
an explicitly labelled diagnostic baseline: Blender world XYZ and XYZ Euler
components placed in Pitch/Yaw/Roll fields respectively. This is NOT a claim
that disguise uses those axes, handedness, zero pose or rotation order.

Replace position_mm() and orientation_degrees() together after the controlled
Designer import described in README. Do not fix signs in the CSV writer.
Lens shift is percent of FULL image width/height. Its sign/range convention in
Designer also awaits validation; adjust lens_shift_percent() here if needed.
"""
import math

CONVENTION = 'UNVALIDATED: raw Blender XYZ / XYZ Euler baseline'
VALIDATED = False


def position_mm(position_blender, metres_per_unit):
    return tuple(float(v)*metres_per_unit*1000 for v in position_blender)


def orientation_degrees(rotation_matrix):
    euler=rotation_matrix.to_euler('XYZ')
    return tuple(math.degrees(v) for v in euler)


def lens_shift_percent(horizontal,vertical):
    return horizontal,vertical
