import bpy
from bpy.props import (BoolProperty, IntProperty, FloatProperty, FloatVectorProperty,
                       StringProperty, EnumProperty, PointerProperty)


def changed(self, context):
    from . import runtime
    runtime.invalidate(self.id_data)


class PS_Settings(bpy.types.PropertyGroup):
    data_version: IntProperty(default=0,options={'HIDDEN'})
    is_projector: BoolProperty(default=False)
    identifier: StringProperty()
    uuid: StringProperty()
    notes: StringProperty(name='Notes',description='Projector notes included in JSON interchange')
    active: BoolProperty(name='Include in Export', default=True, update=changed)
    resolution_x: IntProperty(name='Resolution X', default=1920, min=1, max=32768, update=changed)
    resolution_y: IntProperty(name='Resolution Y', default=1080, min=1, max=32768, update=changed)
    throw_ratio: FloatProperty(name='Throw Ratio', default=1.0, min=0.05, max=100, update=changed)
    shift_h: FloatProperty(name='Horizontal Shift %', precision=1, description='Image-centre offset as percent of full image width; positive right', default=0, min=-300, max=300, update=changed)
    shift_v: FloatProperty(name='Vertical Shift %', precision=1, description='Image-centre offset as percent of full image height; positive up', default=0, min=-300, max=300, update=changed)
    stack: IntProperty(name='Stack Quantity', default=1, min=1, update=changed)
    brightness: FloatProperty(name='Brightness %', precision=1, default=100, min=0, max=100, update=changed)
    lumens: FloatProperty(name='Nominal Lumens', precision=0, default=20000, min=0, update=changed)
    colour: FloatVectorProperty(name='Study Colour', subtype='COLOR', size=3, min=0, max=1, default=(0.77, 0.39, 0.36), update=changed)
    # Explicit enum numbers preserve modes saved by versions 0.1–0.3.
    output_mode: EnumProperty(name='Output Mode',items=[
        ('SOLID','Solid Colour','',0,0),('GRID','Calibration Grid','',0,1),
        ('ID','Identifier','',0,2),('CHECKER','Checkerboard','',0,3),
        ('UV_GRID','Blender UV Grid','',0,4),('COLOR_GRID','Blender Color Grid','',0,6),
        ('IMAGE','Custom Image','',0,5)],default='GRID',update=changed)

    image: PointerProperty(name='Custom Image', type=bpy.types.Image, update=changed)
    show_grid: BoolProperty(name='Show Grid', default=True, update=changed)
    show_projected_identifier: BoolProperty(name='Projected Name',default=True,update=changed)
    show_identifier: BoolProperty(name='Body / Measurement Labels', default=True, update=changed)
    show_frustum: BoolProperty(name='Show Frustum', default=True, update=changed)
    show_target_marker: BoolProperty(name='Target Marker',default=True,update=changed)
    show_centre_ray: BoolProperty(name='Centre Ray',default=True,update=changed)
    show_output: BoolProperty(name='Show Projected Output', default=True, update=changed)
    target: PointerProperty(name='Automatic Target', type=bpy.types.Object, description='Computed first centre-raster hit; never a receiver filter')
    has_target: BoolProperty(default=False,options={'HIDDEN'})
    target_point_m: FloatVectorProperty(size=3,options={'HIDDEN'})
    target_distance_m: FloatProperty(options={'HIDDEN'})
    preview_distance: FloatProperty(name='No-hit Preview (m)', default=10, min=0.01, update=changed)
