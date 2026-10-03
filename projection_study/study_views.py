"""Camera-based study views and explicit, overlay-aware PNG capture."""
from pathlib import Path
import bpy
import gpu
import time
from mathutils import Matrix
from .utils import new_uuid
from .interchange import image_filename, beam_filename, timestamp, write_png
from . import runtime, viewport_display, typography

_captures=[]
_navigation={}


def viewport(context,preferred=None):
    area=preferred or context.area
    if not area or area.type!='VIEW_3D':
        area=next((a for a in context.screen.areas if a.type=='VIEW_3D'),None)
    if area is None: raise ValueError('A 3D View is required')
    region=next(r for r in area.regions if r.type=='WINDOW')
    return area,region


def create_view(context,name):
    area,region=viewport(context)
    space=area.spaces.active; rv=space.region_3d
    scene=context.scene; settings=scene.ps_study
    base=name.strip() or 'Study View'; name=base; count=2
    while any(v.name==name for v in settings.views):
        name=f'{base} {count:02d}'; count+=1
    camera=bpy.data.objects.new('Study · '+name,bpy.data.cameras.new('Study · '+name))
    scene.collection.objects.link(camera)
    camera.matrix_world=rv.view_matrix.inverted()
    camera.data.sensor_fit='HORIZONTAL'; camera.data.sensor_width=36
    projection=rv.window_matrix; aspect=region.width/region.height
    if rv.is_perspective:
        camera.data.type='PERSP'; camera.data.lens=36*projection[0][0]/2
        camera.data.shift_x=projection[0][2]/2
        camera.data.shift_y=projection[1][2]/(2*aspect)
    else:
        camera.data.type='ORTHO'; camera.data.ortho_scale=2/projection[0][0]
        camera.data.shift_x=-projection[0][3]/2
        camera.data.shift_y=-projection[1][3]/(2*aspect)
    camera.data.clip_start=space.clip_start; camera.data.clip_end=space.clip_end
    camera.hide_render=True
    camera.hide_set(not settings.show_study_cameras)
    view=settings.views.add(); view.uuid=new_uuid(); view.name=name; view.camera=camera
    view.resolution_x=min(8192,max(64,region.width)); view.resolution_y=min(8192,max(64,region.height))
    from . import presentation
    view.include_overlays=space.overlay.show_overlays or presentation.active(area)
    settings.view_index=len(settings.views)-1
    return view


def selected_view(context):
    s=context.scene.ps_study
    return s.views[s.view_index] if 0<=s.view_index<len(s.views) else None


def export_view(context,view,path,area=None):
    if not view.camera or view.camera.type!='CAMERA' or view.camera.name not in context.scene.objects:
        raise ValueError(f'{view.name}: missing scene camera')
    if view.camera.data.type not in {'PERSP','ORTHO'}: raise ValueError('Perspective and orthographic study cameras only')
    area,region=viewport(context,area)
    width,height=view.resolution_x,view.resolution_y
    options=dict(projected_identifiers=view.include_projected_identifiers,labels=view.include_labels,frustums=view.include_frustums,grids=view.include_grids,overlays=view.include_overlays)
    with context.temp_override(area=area,region=region):
        context.view_layer.update(); runtime.refresh(True)
        graph=context.evaluated_depsgraph_get(); cam=view.camera.evaluated_get(graph)
        view_matrix=cam.matrix_world.inverted()
        projection=cam.calc_matrix_camera(graph,x=width,y=height,scale_x=1,scale_y=1)
        off=gpu.types.GPUOffScreen(width,height)
        old_viewport=gpu.state.viewport_get()
        try:
            space=area.spaces.active
            old_overlays=space.overlay.show_overlays
            old_extras=space.overlay.show_extras
            viewport_display._suppress=True
            try:
                from . import presentation
                space.overlay.show_overlays=view.include_overlays and not presentation.active(area)
                space.overlay.show_extras=False
                off.draw_view3d(context.scene,context.view_layer,space,region,view_matrix,projection,
                                do_color_management=True,draw_background=True)
            finally:
                viewport_display._suppress=False
                space.overlay.show_overlays=old_overlays
                space.overlay.show_extras=old_extras
            with off.bind(),gpu.matrix.push_pop(),gpu.matrix.push_pop_projection():
                gpu.state.viewport_set(0,0,width,height)
                gpu.matrix.load_matrix(view_matrix); gpu.matrix.load_projection_matrix(projection)
                # draw_view3d resolves colour, but does not expose its scene depth.
                # Populate a depth-only mesh pass for correctly occluded overlays.
                if options['overlays']:
                    depth_pass(context,graph)
                    viewport_display.draw_3d(options,projection@view_matrix)
            with off.bind(),gpu.matrix.push_pop(),gpu.matrix.push_pop_projection():
                gpu.state.viewport_set(0,0,width,height)
                if options['overlays']:
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(typography.pixel_matrix(width,height))
                    viewport_display.draw_labels(projection@view_matrix,width,height,options)
            with off.bind():
                buffer=gpu.state.active_framebuffer_get().read_color(0,0,width,height,4,0,'UBYTE')
                buffer.dimensions=width*height*4
                write_png(path,width,height,buffer)
        finally:
            off.free(); gpu.state.viewport_set(*old_viewport)
    view.image_filename=Path(path).name; view.exported_at=timestamp()


class PS_OT_create_view(bpy.types.Operator):
    bl_idname='ps.create_view'
    bl_label='Create Study View From Current View'
    bl_options={'REGISTER','UNDO'}
    name: bpy.props.StringProperty(name='View Name',default='Overview')
    def invoke(self,context,event): return context.window_manager.invoke_props_dialog(self)
    def execute(self,context):
        try: create_view(context,self.name)
        except ValueError as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}


class PS_UL_study_views(bpy.types.UIList):
    def draw_item(self,context,layout,data,item,icon,active_data,active_property,index):
        row=layout.row(align=True)
        row.prop(item,'name',text='',emboss=False,icon='CAMERA_DATA')
        button=row.operator('ps.view_study',text='View')
        button.index=index


def exit_navigation(key):
    state=_navigation.pop(key,None)
    if not state: return
    try:
        scene,space,rv,old=state
        scene.camera=old['camera']
        scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=old['resolution']
        scene.render.pixel_aspect_x,scene.render.pixel_aspect_y=old['pixel_aspect']
        space.use_local_camera=old['local']; space.camera=old['space_camera']; space.lock_camera=old['lock']
        rv.view_location=old['location']; rv.view_rotation=old['rotation']; rv.view_distance=old['distance']
        rv.view_camera_zoom=old['zoom']; rv.view_camera_offset=old['offset']; rv.view_perspective=old['perspective']
    except (ReferenceError,TypeError): pass


class PS_OT_view_study(bpy.types.Operator):
    bl_idname='ps.view_study'
    bl_label='View Selected Study View'
    bl_description='Open the study camera without a numpad; Exit Study View restores the previous view'
    index: bpy.props.IntProperty(default=-1)
    action: bpy.props.EnumProperty(items=[('VIEW','View',''),('PREVIOUS','Previous',''),('NEXT','Next',''),('EXIT','Exit','')])
    def execute(self,context):
        try: area,region=viewport(context)
        except ValueError as exc:
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        key=area.as_pointer()
        if self.action=='EXIT':
            exit_navigation(key); area.tag_redraw(); return {'FINISHED'}
        settings=context.scene.ps_study
        if not settings.views:
            self.report({'WARNING'},'Create a study view first'); return {'CANCELLED'}
        index=self.index if self.index>=0 else settings.view_index
        if self.action in {'NEXT','PREVIOUS'}: index=(index+(1 if self.action=='NEXT' else -1))%len(settings.views)
        if not 0<=index<len(settings.views): return {'CANCELLED'}
        view=settings.views[index]; camera=view.camera
        if not camera or camera.type!='CAMERA' or camera.name not in context.scene.objects:
            self.report({'WARNING'},'Study view camera is missing from this scene'); return {'CANCELLED'}
        from .operators import restore_views
        restore_views()
        scene=context.scene; space=area.spaces.active; rv=space.region_3d
        if key not in _navigation:
            old=dict(camera=scene.camera,pixel_aspect=(scene.render.pixel_aspect_x,scene.render.pixel_aspect_y),resolution=(scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage),
                     local=space.use_local_camera,space_camera=space.camera,lock=space.lock_camera,
                     location=rv.view_location.copy(),rotation=rv.view_rotation.copy(),distance=rv.view_distance,
                     zoom=rv.view_camera_zoom,offset=tuple(rv.view_camera_offset),perspective=rv.view_perspective)
            _navigation[key]=(scene,space,rv,old)
        settings.view_index=index; scene.camera=camera
        space.use_local_camera=False; space.camera=camera; space.lock_camera=False
        scene.render.resolution_x=view.resolution_x; scene.render.resolution_y=view.resolution_y; scene.render.resolution_percentage=100
        scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
        rv.view_perspective='CAMERA'; rv.view_camera_zoom=0; rv.view_camera_offset=(0,0)
        area.tag_redraw(); return {'FINISHED'}


class PS_OT_remove_view(bpy.types.Operator):
    bl_idname='ps.remove_view'
    bl_label='Remove Study View Entry'
    bl_description='Remove the saved entry; keep its Blender camera'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        s=context.scene.ps_study
        if selected_view(context): s.views.remove(s.view_index); s.view_index=max(0,s.view_index-1)
        return {'FINISHED'}


def proposed_names(scene):
    settings=scene.ps_study; used=set(); names={}
    for view in settings.views:
        base=beam_filename(settings.project_name,settings.revision,view.name)
        name=base; index=2
        while name.casefold() in used:
            name=f'{Path(base).stem}_{index:02d}.png'; index+=1
        used.add(name.casefold()); names[view.uuid]=name
    return names


class BeamExportImageName(bpy.types.PropertyGroup):
    view_uuid: bpy.props.StringProperty()
    filename: bpy.props.StringProperty(name='Filename')


class PS_OT_export_views(bpy.types.Operator):
    bl_idname='ps.export_views'
    bl_label='Export Study Views'
    proposed_files: bpy.props.CollectionProperty(type=BeamExportImageName)
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default='*.png',options={'HIDDEN'})
    all_views: bpy.props.BoolProperty(default=False)
    overwrite: bpy.props.BoolProperty(name='Overwrite Existing Images',default=False)
    check_existing: bpy.props.BoolProperty(default=True,options={'HIDDEN'})
    def invoke(self,context,event):
        self.source_area=context.area
        self.proposed_files.clear()
        for identity,name in proposed_names(context.scene).items():
            item=self.proposed_files.add(); item.view_uuid=identity; item.filename=name
        if not self.all_views:
            view=selected_view(context)
            if not view: return {'CANCELLED'}
            self.filepath=proposed_names(context.scene)[view.uuid]
        context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}
    def check(self,context):
        if not self.all_views and self.filepath and not self.filepath.lower().endswith('.png'):
            self.filepath=str(Path(self.filepath).with_suffix('.png')); return True
        return False
    def draw(self,context):
        self.layout.prop(self,'overwrite')
        if self.all_views:
            self.layout.label(text='Proposed filenames:')
            for item in self.proposed_files: self.layout.prop(item,'filename',text='')
        else: self.layout.prop(self,'filepath',text='Filename / Path')
    def execute(self,context):
        views=list(context.scene.ps_study.views) if self.all_views else [selected_view(context)]
        views=[v for v in views if v]
        if not views:
            self.report({'WARNING'},'Create a study view first'); return {'CANCELLED'}
        try:
            if self.all_views:
                folder=Path(bpy.path.abspath(self.directory)); names=proposed_names(context.scene)
                names.update({item.view_uuid:item.filename for item in self.proposed_files})
                for name in names.values():
                    if Path(name).name!=name or Path(name).suffix.lower()!='.png': raise ValueError('Each filename must be a PNG basename without directories')
                if len({n.casefold() for n in names.values()})!=len(names): raise ValueError('Use a different filename for each study view')
                paths=[folder/names[v.uuid] for v in views]
            else:
                if not self.filepath: raise ValueError('Choose the PNG filename in the export dialog')
                path=Path(bpy.path.abspath(self.filepath))
                if path.suffix.lower()!='.png': raise ValueError('Filename must end in .png')
                folder=path.parent; paths=[path]
            if not folder.is_dir(): raise ValueError('Choose an existing export directory')
            for view,path in zip(views,paths):
                if not view.camera: raise ValueError(f'{view.name}: missing camera')
                if path.exists() and not self.overwrite: raise ValueError('An image already exists. Enable Overwrite Existing Images or choose another folder.')
            for view,path in zip(views,paths): export_view(context,view,path,getattr(self,'source_area',None))
        except (OSError,RuntimeError,ValueError) as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},f'Exported {len(views)} view(s) to {folder}'); return {'FINISHED'}


class PS_OT_capture_current(bpy.types.Operator):
    bl_idname='ps.capture_current'
    bl_label='Export Current View'
    filepath: bpy.props.StringProperty(subtype='FILE_PATH',default='current-view.png')
    filter_glob: bpy.props.StringProperty(default='*.png',options={'HIDDEN'})
    check_existing: bpy.props.BoolProperty(default=True,options={'HIDDEN'})
    def invoke(self,context,event):
        self.source_area=context.area
        settings=context.scene.ps_study
        self.filepath=beam_filename(settings.project_name,settings.revision,'Current View')
        context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}
    def check(self,context):
        if self.filepath and not self.filepath.lower().endswith('.png'):
            self.filepath=str(Path(self.filepath).with_suffix('.png')); return True
        return False
    def execute(self,context):
        try: self.area,self.region=viewport(context,getattr(self,'source_area',None))
        except ValueError as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.scene=context.scene; self.wm=context.window_manager
        self.started=time.monotonic()
        self.timer=self.wm.event_timer_add(.25,window=context.window)
        _captures.append(self)
        self.wm.modal_handler_add(self); self.area.tag_redraw()
        return {'RUNNING_MODAL'}
    def cleanup(self):
        if self in _captures:
            self.wm.event_timer_remove(self.timer); _captures.remove(self)
    def modal(self,context,event):
        if self not in _captures: return {'CANCELLED'}
        if event.type=='ESC': self.cleanup(); return {'CANCELLED'}
        if event.type!='TIMER' or time.monotonic()-self.started<.25: return {'PASS_THROUGH'}
        self.cleanup()
        try:
            path=Path(bpy.path.abspath(self.filepath))
            if path.suffix.lower()!='.png': raise ValueError('Filename must end in .png')
            # Blender's screenshot operator reads the fully composited editor,
            # unlike POST_PIXEL framebuffer reads which can contain overlays only.
            with context.temp_override(area=self.area,region=self.region):
                result=bpy.ops.screen.screenshot_area(filepath=str(path),hide_props_region=False)
            if result!={'FINISHED'} or not path.exists(): raise RuntimeError('Viewport screenshot failed')
            self.scene.ps_study.last_current_image=path.name
            self.scene.ps_study.last_current_exported_at=timestamp()
        except (OSError,RuntimeError,ValueError) as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},'Current viewport exported'); return {'FINISHED'}



@bpy.app.handlers.persistent
def cleanup(*args):
    for capture in list(_captures): capture.cleanup()
    for key in list(_navigation): exit_navigation(key)

CLASSES=(BeamExportImageName,PS_UL_study_views,PS_OT_view_study,PS_OT_create_view,PS_OT_remove_view,PS_OT_export_views,PS_OT_capture_current)


def depth_pass(context,graph):
    from gpu_extras.batch import batch_for_shader
    gpu.state.active_framebuffer_get().clear(depth=1)
    shader=gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA'); gpu.state.depth_test_set('LESS_EQUAL'); gpu.state.depth_mask_set(True)
    try:
        for instance in graph.object_instances:
            obj=instance.object
            if obj.type not in {'MESH','CURVE','SURFACE','FONT','META'} or not instance.show_self: continue
            if not instance.is_instance and not obj.original.visible_get(): continue
            mesh=obj.to_mesh()
            try:
                mesh.calc_loop_triangles()
                if not mesh.loop_triangles: continue
                positions=[instance.matrix_world@v.co for v in mesh.vertices]
                indices=[tuple(t.vertices) for t in mesh.loop_triangles]
                batch=batch_for_shader(shader,'TRIS',{'pos':positions},indices=indices)
                shader.bind(); shader.uniform_float('color',(0,0,0,0)); batch.draw(shader)
            finally: obj.to_mesh_clear()
    finally:
        gpu.state.depth_mask_set(False); gpu.state.blend_set('NONE')
