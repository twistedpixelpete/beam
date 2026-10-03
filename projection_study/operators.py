import bpy
from .projector_object import create

class PS_OT_add(bpy.types.Operator):
    bl_idname = 'ps.add'
    bl_label = 'Add Projector'
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context):
        create(context)
        return {'FINISHED'}

CLASSES = (PS_OT_add,)

from mathutils import Vector
from bpy_extras import view3d_utils
from .projector_object import selected
from . import runtime
from .projection_math import image_point


def aim(obj, point):
    origin,_ = runtime.frame(obj)
    direction = point-origin
    if direction.length<1e-6: return False
    if any(obj.lock_rotation): return False
    # Aim the shifted image centre, retaining a stable world-up convention.
    p = obj.ps
    local = Vector(image_point(.5,.5,1,p.throw_ratio,p.resolution_x,p.resolution_y,p.shift_h,p.shift_v)).normalized()
    offset = Vector((0,0,-1)).rotation_difference(local)
    rotation = direction.to_track_quat('-Z','Y') @ offset.inverted()
    matrix = rotation.to_matrix().to_4x4()
    matrix.translation = origin
    obj.matrix_world = matrix
    runtime.invalidate()
    return True

class PS_OT_aim(bpy.types.Operator):
    bl_idname = 'ps.aim'
    bl_label = 'Aim Projector'
    bl_options = {'REGISTER','UNDO'}
    mode: bpy.props.EnumProperty(items=[('OBJECT','Object Centre',''),('CURSOR','3D Cursor',''),('CLICK','Click Surface','')])
    @classmethod
    def poll(cls, context): return selected(context) is not None
    def execute(self, context):
        obj = selected(context)
        target = next((o for o in context.selected_objects if o!=obj and not o.ps.is_projector and not o.get('ps_helper')),None) or obj.ps.target
        if self.mode=='OBJECT' and target is None:
            self.report({'WARNING'},'Select a venue object, or aim at a surface')
            return {'CANCELLED'}
        point = context.scene.cursor.location if self.mode=='CURSOR' else target.matrix_world.translation
        if not aim(obj,point):
            self.report({'WARNING'},'Unlock rotation or choose a point away from the lens')
            return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self, context, event):
        if self.mode!='CLICK': return self.execute(context)
        self.projector = selected(context)
        context.window_manager.modal_handler_add(self)
        context.window.cursor_modal_set('CROSSHAIR')
        context.area.header_text_set('Click a venue surface to aim • Esc to cancel')
        return {'RUNNING_MODAL'}
    def modal(self, context, event):
        def done():
            context.window.cursor_modal_restore()
            context.area.header_text_set(None)
        if event.type in {'ESC','RIGHTMOUSE'}:
            done(); return {'CANCELLED'}
        if event.type=='LEFTMOUSE' and event.value=='PRESS':
            from .target_raycast import cast
            region = next(r for r in context.area.regions if r.type=='WINDOW')
            coord = (event.mouse_x-region.x,event.mouse_y-region.y)
            rv3d = context.space_data.region_3d
            origin = view3d_utils.region_2d_to_origin_3d(region,rv3d,coord)
            direction = view3d_utils.region_2d_to_vector_3d(region,rv3d,coord)
            hit = cast(origin,direction)
            if hit and aim(self.projector,hit[0]):
                done(); return {'FINISHED'}
            self.report({'WARNING'},'No eligible surface hit, or rotation is locked')
        return {'RUNNING_MODAL'}

CLASSES += (PS_OT_aim,)

class PS_OT_duplicate(bpy.types.Operator):
    bl_idname='ps.duplicate'
    bl_label='Duplicate Projector'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return selected(context) is not None
    def execute(self,context):
        create(context,selected(context))
        return {'FINISHED'}

class PS_OT_move(bpy.types.Operator):
    bl_idname='ps.move'
    bl_label='Move Projector'
    bl_options={'REGISTER','UNDO'}
    distance: bpy.props.FloatProperty(name='Distance (m)',default=1)
    maintain_aim: bpy.props.BoolProperty(name='Maintain Aim',default=False)
    @classmethod
    def poll(cls,context): return selected(context) is not None
    def execute(self,context):
        obj=selected(context)
        if any(obj.lock_location):
            self.report({'WARNING'},'Unlock the projector transform first'); return {'CANCELLED'}
        context.view_layer.update(); runtime.refresh(True)
        record=runtime.CACHE[obj.as_pointer()]
        direction=record['rotation']@Vector((0,0,-1))
        delta=self.distance/context.scene.unit_settings.scale_length
        if self.maintain_aim:
            if not record['hit']:
                self.report({'WARNING'},'A target hit is required'); return {'CANCELLED'}
            direction=(record['centre']-record['origin']).normalized()
            if delta>=(record['centre']-record['origin']).length:
                self.report({'WARNING'},'Move would pass the target'); return {'CANCELLED'}
        matrix=obj.matrix_world.copy(); matrix.translation += direction*delta
        obj.matrix_world=matrix
        runtime.invalidate()
        return {'FINISHED'}

class PS_OT_lock(bpy.types.Operator):
    bl_idname='ps.lock'
    bl_label='Lock / Unlock Transform'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return selected(context) is not None
    action: bpy.props.EnumProperty(items=[('TOGGLE','Toggle',''),('LOCK','Lock',''),('UNLOCK','Unlock','')])
    def execute(self,context):
        obj=selected(context); lock=not all(obj.lock_location) if self.action=='TOGGLE' else self.action=='LOCK'
        obj.lock_location=(lock,)*3; obj.lock_rotation=(lock,)*3
        obj.lock_rotation_w=lock; obj.lock_rotations_4d=lock
        return {'FINISHED'}

class PS_OT_isolate(bpy.types.Operator):
    bl_idname='ps.isolate'
    bl_label='Solo Active Projector / Show All'
    @classmethod
    def poll(cls,context): return selected(context) is not None
    def execute(self,context):
        from . import viewport_display as display
        from . import blend_groups
        blend_groups.solo_uuid=None
        identity=selected(context).ps.uuid
        display.isolate_uuid=None if display.isolate_uuid==identity else identity
        context.area.tag_redraw()
        return {'FINISHED'}

_view_sessions=[]

@bpy.app.handlers.persistent
def restore_views(*args):
    for session in list(_view_sessions): session.restore()

class PS_OT_look(bpy.types.Operator):
    bl_idname='ps.look'
    bl_label='Look Through Projector'
    @classmethod
    def poll(cls,context):
        return selected(context) is not None and context.area and context.area.type=='VIEW_3D'
    def restore(self):
        try:
            for key,value in self.render_settings.items(): setattr(self.scene.render,key,value)
            self.space.camera=self.old_camera
            self.space.use_local_camera=self.old_local
            self.space.lock_camera=self.old_lock
            self.space.region_3d.view_perspective=self.old_perspective
            self.wm.event_timer_remove(self.timer)
            self.area.header_text_set(None)
        except ReferenceError: pass
        if self in _view_sessions: _view_sessions.remove(self)
    def invoke(self,context,event):
        restore_views()
        obj=selected(context)
        self.scene=context.scene; self.space=context.space_data; self.area=context.area
        self.wm=context.window_manager
        self.render_settings={k:getattr(self.scene.render,k) for k in ('resolution_x','resolution_y','pixel_aspect_x','pixel_aspect_y')}
        self.old_camera=self.space.camera; self.old_local=self.space.use_local_camera
        self.old_lock=self.space.lock_camera
        self.old_perspective=self.space.region_3d.view_perspective
        self.scene.render.resolution_x=obj.ps.resolution_x
        self.scene.render.resolution_y=obj.ps.resolution_y
        self.scene.render.pixel_aspect_x=self.scene.render.pixel_aspect_y=1
        self.space.use_local_camera=True
        self.space.camera=runtime.optics(obj)
        self.space.lock_camera=False
        self.space.region_3d.view_perspective='CAMERA'
        self.timer=self.wm.event_timer_add(.1,window=context.window)
        self.area.header_text_set('Projector view • Esc to exit and restore render aspect')
        _view_sessions.append(self)
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def modal(self,context,event):
        if self not in _view_sessions: return {'CANCELLED'}
        if event.type=='ESC' or self.space.region_3d.view_perspective!='CAMERA':
            self.restore(); return {'FINISHED'}
        return {'PASS_THROUGH'}

class PS_OT_load_image(bpy.types.Operator):
    bl_idname='ps.load_image'
    bl_label='Load Custom Image'
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default='*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.exr',options={'HIDDEN'})
    @classmethod
    def poll(cls,context): return selected(context) is not None
    def invoke(self,context,event):
        self.projector=selected(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        obj=getattr(self,'projector',None) or selected(context)
        try: obj.ps.image=bpy.data.images.load(self.filepath,check_existing=True)
        except (RuntimeError,ReferenceError) as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        obj.ps.output_mode='IMAGE'
        return {'FINISHED'}

CLASSES += (PS_OT_duplicate,PS_OT_move,PS_OT_lock,PS_OT_isolate,PS_OT_look,PS_OT_load_image)


class BEAM_OT_frame(bpy.types.Operator):
    bl_idname='beam.frame_projector'; bl_label='Frame Active Projector'
    def execute(self,context):
        obj=selected(context)
        if not obj or not context.area or context.area.type!='VIEW_3D': return {'CANCELLED'}
        before=list(context.selected_objects); active=context.view_layer.objects.active
        try:
            for item in before: item.select_set(False)
            obj.select_set(True); context.view_layer.objects.active=obj
            region=next(r for r in context.area.regions if r.type=='WINDOW')
            with context.temp_override(region=region): bpy.ops.view3d.view_selected(use_all_regions=False)
        finally:
            obj.select_set(False)
            for item in before: item.select_set(True)
            context.view_layer.objects.active=active
        return {'FINISHED'}

CLASSES += (BEAM_OT_frame,)
