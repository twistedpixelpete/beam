"""Validated flat-screen frame shared by planning and live measurements."""
import math
from mathutils import Vector
from . import runtime,screen_objects


def screen_frame(context,obj):
    if not obj or obj.type!='MESH' or not obj.beam_screen.is_screen or obj.beam_screen.screen_type!='FLAT':raise ValueError('Select a flat rectangular Beam Screen')
    if obj.modifiers:raise ValueError('Auto Blend needs a flat screen without modifiers')
    if not runtime.rigid(obj):raise ValueError('Auto Blend needs screen scale 1 and no shear')
    if obj.beam_screen.built_signature!=screen_objects.signature(obj.beam_screen):raise ValueError('Update Screen before Auto Blend')
    unit=context.scene.unit_settings.scale_length
    if abs(unit-obj.beam_screen.unit_scale)>1e-8:raise ValueError('Scene units changed: Update Screen first')
    points=[v.co for v in obj.data.vertices]
    if not points:raise ValueError('Screen has no geometry; Update Screen first')
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    if min(high.x-low.x,high.z-low.z)<=1e-6:raise ValueError('Screen needs positive width and height')
    if high.y-low.y>1e-5:raise ValueError('Screen is no longer planar')
    # Planarity, bounds and area checks reject holes, missing faces and non-rectangular edits.
    rectangle=(high.x-low.x)*(high.z-low.z)
    area=sum(face.area for face in obj.data.polygons)
    if not math.isclose(area,rectangle,rel_tol=1e-5,abs_tol=1e-10):
        raise ValueError('Screen must be a complete rectangle; Update Screen to restore its geometry')
    return (high.x-low.x)*unit,(high.z-low.z)*unit,obj.matrix_world@((low+high)/2),obj.matrix_world.to_quaternion().to_matrix()

