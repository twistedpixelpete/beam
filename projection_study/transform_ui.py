"""World position and rotation fields for the Beam inspectors.

The fields read and write the object's world matrix, so they mean the same thing
for a parented Blend Group member as for a free object. Nothing is stored here.
Lengths use Blender's scene units, so typing "2.5 m" or "2500 mm" both work.
"""
import math

import bpy
from mathutils import Euler, Matrix

from . import runtime, transform_conversion


def _apply(obj, location=None, rotation=None):
    current_location, current_rotation, scale = obj.matrix_world.decompose()
    obj.matrix_world = Matrix.LocRotScale(
        current_location if location is None else location,
        current_rotation if rotation is None else rotation,
        scale,
    )
    runtime.invalidate(obj)


def _position_get(self):
    return self.id_data.matrix_world.translation


def _position_set(self, value):
    if not any(self.id_data.lock_location):
        _apply(self.id_data, location=value)


def _rotation_get(self):
    return self.id_data.matrix_world.to_euler('XYZ')


def _rotation_set(self, value):
    if not any(self.id_data.lock_rotation):
        _apply(self.id_data, rotation=Euler(value, 'XYZ').to_quaternion())


def _orientation_get(self):
    """Pitch, yaw and roll, as in the Mapping Matter CSV: neutral faces +Y with +Z up."""
    rotation = self.id_data.matrix_world.to_quaternion().to_matrix()
    return tuple(math.radians(v) for v in transform_conversion.orientation_degrees(rotation))


def _orientation_set(self, value):
    if any(self.id_data.lock_rotation):
        return
    pitch, yaw, roll = value
    native = Euler((pitch, roll, yaw), 'YXZ').to_matrix()
    _apply(self.id_data, rotation=(native @ Matrix.Rotation(math.pi / 2, 3, 'X')).to_quaternion())


class BeamTransform(bpy.types.PropertyGroup):
    position: bpy.props.FloatVectorProperty(
        name='Position', description='World position; type a unit such as 2500 mm if you need one',
        subtype='TRANSLATION', unit='LENGTH', size=3, precision=3, get=_position_get, set=_position_set)
    rotation: bpy.props.FloatVectorProperty(
        name='Rotation', description='World rotation', subtype='EULER', unit='ROTATION', size=3,
        get=_rotation_get, set=_rotation_set)
    orientation: bpy.props.FloatVectorProperty(
        name='Orientation', description='Pitch, yaw and roll, matching the Mapping Matter CSV export',
        unit='ROTATION', size=3, get=_orientation_get, set=_orientation_set)


CLASSES = (BeamTransform,)


def draw_position(layout, obj):
    row = layout.column(align=True)
    row.enabled = not any(obj.lock_location)
    row.prop(obj.beam_transform, 'position')


def draw_rotation(layout, obj):
    column = layout.column(align=True)
    column.enabled = not any(obj.lock_rotation)
    column.prop(obj.beam_transform, 'rotation')


def draw_projector_rotation(layout, obj):
    column = layout.column(align=True)
    column.enabled = not any(obj.lock_rotation)
    for index, label in enumerate(('Pitch', 'Yaw', 'Roll')):
        column.prop(obj.beam_transform, 'orientation', index=index, text=label)


def register():
    bpy.types.Object.beam_transform = bpy.props.PointerProperty(type=BeamTransform)


def unregister():
    del bpy.types.Object.beam_transform
