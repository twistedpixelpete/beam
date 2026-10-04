"""Undoable Screen Builder actions with validation and explicit state changes."""
import json
import bpy
from bpy.props import StringProperty,EnumProperty,BoolProperty
from . import screen_data,screen_objects,screen_surface,screen_uv,screen_patterns,screen_export

PRESETS={
 'GENERIC500':dict(manufacturer='Generic example',model='500 / 192',cabinet_width=.5,cabinet_height=.5,cabinet_depth=.08,cabinet_px=192,cabinet_py=192),
 'GENERIC1000':dict(manufacturer='Generic example',model='500 × 1000 / 192 × 384',cabinet_width=.5,cabinet_height=1.,cabinet_depth=.08,cabinet_px=192,cabinet_py=384),
}


class BEAM_OT_screen_create(bpy.types.Operator):
    bl_idname='beam.screen_create';bl_label='Create Screen';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        p=context.scene.beam_screen_draft
        if p.screen_type in {'CURVE','SURFACE'} and not p.source:p.source=context.view_layer.objects.active
        try:obj=screen_objects.create(context,p)
        except (ValueError,RuntimeError,TypeError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        screen_objects.select(context,obj);return {'FINISHED'}


class BEAM_OT_screen_action(bpy.types.Operator):
    bl_idname='beam.screen_action';bl_label='Screen Action';bl_options={'REGISTER','UNDO'}
    action: EnumProperty(items=[(x,x.title(),'') for x in ('UPDATE','DUPLICATE','FLIP','PATTERN','NEUTRAL','VALIDATE','REMAP','CONFORM','SURFACE','BAKE','SOURCE','PRESET')])
    @classmethod
    def description(cls,context,properties):
        return {'UPDATE':'Regenerate from parameters; replaces manual edits on the display mesh',
                'SURFACE':'Retain the current evaluated mesh as an editable Surface screen; disconnect procedural source',
                'BAKE':'Bake evaluated geometry and remove Screen Builder editing; undo restores it',
                'CONFORM':'Add or update a reversible nearest-surface shrinkwrap; source geometry stays intact',
                'FLIP':'Reverse face winding and screen direction, without duplicating surfaces',
                'REMAP':'Apply the chosen UV method to the current display mesh',
                'VALIDATE':'Check geometry, winding, UV range, zero area, overlaps and texel density',
                'PATTERN':'Apply a packed orientation chart with corners, UV directions and native resolution',
                'SOURCE':'Use the selected mesh or curve as the source for a new screen'}.get(properties.action,'Manage the selected screen')
    def invoke(self,context,event):
        if self.action in {'BAKE','SURFACE'}:return context.window_manager.invoke_props_dialog(self,width=360)
        return self.execute(context)
    def draw(self,context):
        self.layout.label(text='Keep geometry; disconnect parametric editing.' if self.action=='SURFACE' else 'Bake modifiers and remove Screen Builder metadata.')
        self.layout.label(text='Undo restores the previous screen.')
    def execute(self,context):
        obj=screen_data.active(context)
        try:
            if self.action=='SOURCE':
                source=context.view_layer.objects.active
                if not source or source.type not in {'MESH','CURVE'}:raise ValueError('Select a mesh or curve source')
                p=context.scene.beam_screen_draft;p.source=source;p.screen_type='CURVE' if source.type=='CURVE' else 'SURFACE'
                return {'FINISHED'}
            p=obj.beam_screen if obj else context.scene.beam_screen_draft
            if self.action=='PRESET':
                if p.preset not in PRESETS:raise ValueError('Choose an example preset or enter custom cabinet values')
                for key,value in PRESETS[p.preset].items():
                    if hasattr(p,key):setattr(p,key,value)
                return {'FINISHED'}
            if not obj:raise ValueError('Select a Screen Builder display object')
            if obj.mode!='OBJECT':raise ValueError('Leave Edit Mode before this operation')
            if self.action=='UPDATE':
                screen_objects.update(context,obj)
            elif self.action=='DUPLICATE':
                copy=obj.copy();copy.data=obj.data.copy();obj.users_collection[0].objects.link(copy)
                for child in obj.children:
                    if child.get('beam_screen_detail'):
                        d=child.copy();d.data=child.data.copy();obj.users_collection[0].objects.link(d);d.parent=copy
                screen_objects.reconcile();screen_objects.select(context,copy)
            elif self.action=='FLIP':
                if obj.data.users>1:obj.data=obj.data.copy()
                obj.data.flip_normals();p.direction='REVERSED' if p.direction=='FRONT' else 'FRONT';screen_objects.acknowledge(p,'direction');screen_objects.sync_detail(obj,True)
            elif self.action=='PATTERN':screen_patterns.apply(obj)
            elif self.action=='NEUTRAL':obj.data.materials.clear();obj.data.materials.append(screen_objects.material(p.category=='LED'))
            elif self.action=='VALIDATE':
                ev=obj.evaluated_get(context.evaluated_depsgraph_get());mesh=ev.to_mesh()
                try:
                    m=json.loads(p.metrics);r=screen_uv.diagnose(mesh,context.scene.unit_settings.scale_length,m.get('rx',p.resolution_x),m.get('ry',p.resolution_y),p.direction=='REVERSED')
                finally:ev.to_mesh_clear()
                p.diagnostic=r['summary'];self.report({'WARNING'} if r['errors'] else {'INFO'},p.diagnostic)
            elif self.action=='REMAP':
                mesh=obj.data.copy()
                try:screen_surface.remap(mesh,p)
                except Exception:bpy.data.meshes.remove(mesh);raise
                old=obj.data;obj.data=mesh
                if old.users==0:bpy.data.meshes.remove(old)
                screen_objects.acknowledge(p,'uv_method','uv_plane')
                p.diagnostic='Row/column distance mapping; validate stretch on non-developable surfaces' if p.uv_method=='DISTANCE' else 'Remapped · run Validate UV'
            elif self.action=='CONFORM':screen_surface.conform(context,obj);screen_objects.acknowledge(p,'conform_target','conform_offset');p.diagnostic='Conformed · UVs retained; Validate UV for stretch'
            elif self.action in {'SURFACE','BAKE'}:
                graph=context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
                old=obj.data;obj.data=mesh;obj.modifiers.clear()
                if old.users==0:bpy.data.meshes.remove(old)
                p.screen_type='SURFACE';p.category='PROJECTION';p.source=None;p.conform_target=None;p.uv_method='EXISTING';p.built_signature=screen_objects.signature(p)
                if self.action=='BAKE':
                    obj['beam_baked_screen_id']=p.identifier;p.is_screen=False
                    for c in obj.children:
                        if c.get('beam_screen_detail'):del c['beam_screen_detail'];c.hide_select=False
            from . import runtime,target_raycast
            target_raycast.invalidate();runtime.invalidate()
        except (ValueError,RuntimeError,TypeError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}


class BEAM_OT_screen_export(bpy.types.Operator):
    bl_idname='beam.screen_export';bl_label='Export Screen Geometry'
    bl_description='Export only this screen in SI metres, Blender +Z up / +Y forward; production omits all detail and materials'
    filepath: StringProperty(subtype='FILE_PATH')
    format: EnumProperty(items=[('OBJ','OBJ',''),('FBX','FBX','')])
    filter_glob: StringProperty(default='*.obj;*.fbx',options={'HIDDEN'})
    overwrite: BoolProperty(name='Overwrite',default=False)
    def invoke(self,context,event):
        obj=screen_data.active(context)
        if not obj:self.report({'ERROR'},'Select a screen');return {'CANCELLED'}
        self.filepath=obj.beam_screen.identifier+('.obj' if self.format=='OBJ' else '.fbx');context.window_manager.fileselect_add(self);return {'RUNNING_MODAL'}
    def draw(self,context):
        self.layout.prop(self,'format');self.layout.prop(self,'overwrite');obj=screen_data.active(context)
        if obj:self.layout.label(text=obj.beam_screen.export_mode.title()+' · metres · Z up')
    def execute(self,context):
        obj=screen_data.active(context)
        if not obj:self.report({'ERROR'},'Select a screen');return {'CANCELLED'}
        try:path=screen_export.export(context,obj,self.filepath,self.format,obj.beam_screen.export_mode,obj.beam_screen.export_space,self.overwrite)
        except (ValueError,RuntimeError,OSError,TypeError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        self.report({'INFO'},f'Exported {path.name}');return {'FINISHED'}

CLASSES=(BEAM_OT_screen_create,BEAM_OT_screen_action,BEAM_OT_screen_export)
