"""Persistent screen parameters. Length inputs are explicitly SI metres."""
import bpy
from bpy.props import BoolProperty,EnumProperty,FloatProperty,IntProperty,StringProperty,PointerProperty
from .study_data import redraw


def source_poll(self,obj): return obj.type in {'MESH','CURVE'} and not obj.get('beam_screen_detail')


class BeamScreen(bpy.types.PropertyGroup):
    is_screen: BoolProperty(default=False)
    version: IntProperty(default=1)
    unit_scale: FloatProperty(default=1,options={'HIDDEN'})
    uuid: StringProperty()
    identifier: StringProperty()
    name: StringProperty(name='Name',default='Screen')
    screen_type: EnumProperty(name='Type',items=[(x,x.title(),'') for x in ('FLAT','ARC','CURVE','CLOSED','SURFACE')])
    category: EnumProperty(name='Category',items=[('PROJECTION','Projection',''),('LED','LED','')])
    width: FloatProperty(name='Width (m)',default=6,min=.001,precision=3)
    height: FloatProperty(name='Height (m)',default=3.375,min=.001,precision=3)
    aspect: EnumProperty(name='Aspect',items=[('FREE','Free',''),('16:9','16:9','Height follows width'),('16:10','16:10',''),('4:3','4:3',''),('1:1','1:1',''),('CUSTOM','Custom','')])
    aspect_ratio: FloatProperty(name='W / H',default=1.7777778,min=.01)
    arc_input: EnumProperty(name='Define By',items=[('LENGTH_RADIUS','Arc Length + Radius',''),('LENGTH_ANGLE','Arc Length + Angle',''),('RADIUS_ANGLE','Radius + Angle',''),('CHORD_RADIUS','Chord + Radius','Minor arc, at most 180°'),('CHORD_ANGLE','Chord + Angle','')],default='RADIUS_ANGLE')
    radius: FloatProperty(name='Radius (m)',default=10,min=.001,precision=3)
    angle: FloatProperty(name='Angle (°)',default=90,min=.001,max=360,precision=3)
    arc_length: FloatProperty(name='Arc Length (m)',default=12,min=.001,precision=3)
    chord: FloatProperty(name='Chord (m)',default=10,min=.001,precision=3)
    curvature: EnumProperty(name='Curvature',items=[('CONCAVE','Concave','Viewer inside curve, front normal at centre is -Y'),('CONVEX','Convex','Viewer outside curve')])
    seam_angle: FloatProperty(name='Seam Rotation (°)',default=0,precision=2)
    origin: EnumProperty(name='Origin',items=[('BOTTOM','Bottom Centre',''),('CENTRE','Centre','')])
    direction: EnumProperty(name='Direction',items=[('FRONT','Front','Default local front -Y'),('REVERSED','Reversed','Opposite geometric normals')])
    projection_side: EnumProperty(name='Projection',items=[('FRONT','Front','Metadata only'),('REAR','Rear','Metadata only')])
    quality: EnumProperty(name='Quality',items=[('SEGMENTS','Segments',''),('LENGTH','Segment Length','')])
    segments: IntProperty(name='Horizontal Segments',default=48,min=1,max=4096)
    vertical_segments: IntProperty(name='Vertical Segments',default=1,min=1,max=512)
    segment_length: FloatProperty(name='Segment Length (m)',default=.25,min=.001)
    resolution_x: IntProperty(name='Resolution X',default=1920,min=1,max=131072)
    resolution_y: IntProperty(name='Resolution Y',default=1080,min=1,max=131072)
    source: PointerProperty(name='Source',type=bpy.types.Object,poll=source_poll)
    conform_target: PointerProperty(name='Conform Target',type=bpy.types.Object,poll=lambda self,o:o.type=='MESH' and not o.get('beam_screen_detail'))
    selected_faces: BoolProperty(name='Selected Faces Only',default=False)
    uv_method: EnumProperty(name='UV Method',items=[('EXISTING','Existing UV','Preserve valid source loop UVs'),('PROJECTED','Projected','Planar mapping in screen-local coordinates'),('DISTANCE','Surface Distance','Rectangular quad grid only; other topology is rejected')],default='PROJECTED')
    uv_plane: EnumProperty(name='Plane',items=[('XZ','X / Z','Front -Y'),('XY','X / Y','Front +Z'),('YZ','Y / Z','Front +X')])
    preset: EnumProperty(name='Cabinet Preset',items=[('CUSTOM','Custom',''),('GENERIC500','Example 500 mm / 192 px','Generic example, not a manufacturer specification'),('GENERIC1000','Example 500 × 1000 mm','Generic example, not a manufacturer specification')])
    cabinet_width: FloatProperty(name='Cabinet Width (m)',default=.5,min=.001,precision=3)
    cabinet_height: FloatProperty(name='Cabinet Height (m)',default=.5,min=.001,precision=3)
    cabinet_depth: FloatProperty(name='Depth (m)',default=.08,min=.001,precision=3)
    cabinet_px: IntProperty(name='Cabinet Pixels X',default=192,min=1,max=16384)
    cabinet_py: IntProperty(name='Cabinet Pixels Y',default=192,min=1,max=16384)
    columns: IntProperty(name='Columns',default=20,min=1,max=512)
    rows: IntProperty(name='Rows',default=8,min=1,max=512)
    led_geometry: EnumProperty(name='LED Geometry',items=[('SMOOTH','Smooth Arc','Ideal cylindrical display; cabinet backs are a previs approximation'),('FACETED','Faceted Cabinets','Flat cabinets, N-1 physical joins')],default='FACETED')
    joint_angle: FloatProperty(name='Joint Angle (°)',default=2.5,min=-45,max=45,precision=3)
    show_detail: BoolProperty(name='Detailed Cabinets',default=False,update=redraw)
    show_label: BoolProperty(name='Screen Label',default=True,update=redraw)
    show_dimensions: BoolProperty(name='Dimensions / Resolution',default=True,update=redraw)
    show_outline: BoolProperty(name='Outline',default=True,update=redraw)
    show_normal: BoolProperty(name='Front Direction',default=False,update=redraw)
    show_wire: BoolProperty(name='Wireframe',default=False,update=redraw)
    show_cabinet_lines: BoolProperty(name='Cabinet Lines',default=False,update=redraw)
    show_cabinet_ids: BoolProperty(name='Cabinet IDs',default=False,update=redraw)
    show_centre: BoolProperty(name='Centre Line',default=False,update=redraw)
    export_mode: EnumProperty(name='Export',items=[('PRODUCTION','Production Surface','Only clean front surface, no preview materials or detail'),('DETAILED','Detailed / Previs','Display plus cabinet backing, no annotations')])
    export_space: EnumProperty(name='Coordinates',items=[('WORLD','World Metres','Bake world transform; origin at world zero'),('LOCAL','Screen Local Metres','Local shape at screen origin; world transform omitted')])
    metrics: StringProperty(default='{}')
    diagnostic: StringProperty(default='Not validated')
    built_signature: StringProperty()
    conform_offset: FloatProperty(name='Offset (m)',default=.001,min=0)


PARAMETERS=('name','screen_type','category','width','height','aspect','aspect_ratio','arc_input','radius','angle','arc_length','chord','curvature','seam_angle','origin','direction','projection_side','quality','segments','vertical_segments','segment_length','resolution_x','resolution_y','source','conform_target','selected_faces','uv_method','uv_plane','preset','cabinet_width','cabinet_height','cabinet_depth','cabinet_px','cabinet_py','columns','rows','led_geometry','joint_angle','conform_offset')


def copy_settings(source,dest):
    for prop in source.bl_rna.properties:
        if prop.identifier not in {'rna_type','uuid','identifier','is_screen'} and not prop.is_readonly:
            setattr(dest,prop.identifier,getattr(source,prop.identifier))


def active(context):
    obj=context.view_layer.objects.active
    if obj and obj.get('beam_screen_detail'):obj=obj.parent
    return obj if obj and obj.type=='MESH' and obj.beam_screen.is_screen else None

CLASSES=(BeamScreen,)
