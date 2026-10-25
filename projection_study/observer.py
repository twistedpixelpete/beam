"""Audience planning positions; empty objects with a world-up eye offset."""
import bpy
from bpy.props import BoolProperty,FloatProperty,StringProperty
from mathutils import Vector


def changed(self,context):
    from .analysis_runtime import invalidate
    invalidate('ACUITY')


class BeamObserver(bpy.types.PropertyGroup):
    is_observer: BoolProperty(default=False)
    uuid: StringProperty()
    identifier: StringProperty()
    eye_height: FloatProperty(name='Eye Height (m)',default=1.6,min=0,max=10,update=changed)
    threshold: FloatProperty(name='Acuity Threshold (arcmin)',default=1,min=.01,max=60,update=changed)


def eye_position(obj,unit):
    return obj.matrix_world.translation+Vector((0,0,obj.beam_observer.eye_height/unit))


def record(obj,unit):
    p=obj.beam_observer
    return dict(uuid=p.uuid,name=p.identifier,position_m=list(obj.matrix_world.translation*unit),
        eye_position_m=list(eye_position(obj,unit)*unit),eye_height_m=p.eye_height,threshold_arcmin=p.threshold,
        visibility='CPU first opaque geometry hit from eye to receiver sample',
        assumption='Nominal 1 arcminute guidance is adjustable; not universal human visual performance. Contrast, content, eyesight and ambient light are not modelled.',
        source_rule='Largest apparent pixel angular pitch among visible projectors (conservative coarsest structure); foreshortened tangent Jacobian')


class BEAM_OT_add_observer(bpy.types.Operator):
    bl_idname='beam.add_observer';bl_label='Add Observer';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        from .utils import new_uuid
        existing={o.name for o in context.scene.objects};i=1
        while f'OBS{i:02d}' in existing:i+=1
        obj=bpy.data.objects.new(f'OBS{i:02d}',None);context.scene.collection.objects.link(obj)
        obj.empty_display_type='SPHERE';obj.empty_display_size=.25/context.scene.unit_settings.scale_length
        obj.location=context.scene.cursor.location;obj.show_name=True
        p=obj.beam_observer;p.is_observer=True;p.uuid=new_uuid();p.identifier=obj.name
        for o in context.selected_objects:o.select_set(False)
        obj.select_set(True);context.view_layer.objects.active=obj;context.scene.ps_study.analysis_observer=obj
        return {'FINISHED'}

CLASSES=(BeamObserver,BEAM_OT_add_observer)


def repair_identities(scene):
    """Native duplication copies custom properties; keep each Observer addressable."""
    from .utils import new_uuid
    seen=set()
    for obj in sorted((o for o in scene.objects if o.beam_observer.is_observer),key=lambda o:o.name):
        p=obj.beam_observer
        if not p.uuid or p.uuid in seen:p.uuid=new_uuid()
        seen.add(p.uuid)
        if p.identifier!=obj.name:p.identifier=obj.name
