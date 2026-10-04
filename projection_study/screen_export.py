"""Isolated OBJ/FBX export: evaluated, SI-baked meshes and no scene mutation."""
from pathlib import Path
import os,tempfile,json
import bpy
from mathutils import Matrix
from . import screen_uv,screen_objects


def export(context,obj,filepath,fmt,mode='PRODUCTION',space='WORLD',overwrite=False):
    if context.mode!='OBJECT':raise ValueError('Leave Edit Mode before exporting')
    path=Path(bpy.path.abspath(str(filepath))).with_suffix('.obj' if fmt=='OBJ' else '.fbx')
    if path.exists() and not overwrite:raise ValueError('File exists; enable Overwrite or choose a new filename')
    if not path.parent.is_dir():raise ValueError('Choose an existing export folder')
    if abs(obj.matrix_world.determinant())<1e-12:raise ValueError('Screen transform has zero scale')
    # Never export stale parameters silently.
    p=obj.beam_screen
    if abs(p.unit_scale-context.scene.unit_settings.scale_length)>1e-8:raise ValueError('Scene unit scale changed; Update Screen before exporting')
    if p.built_signature!=screen_objects.signature(p):raise ValueError('Parameters changed; Update Screen before exporting')
    if mode=='DETAILED' and p.category=='LED' and obj.modifiers:raise ValueError('Deformed LED: export Production Surface; parametric cabinet backs do not follow modifiers')
    graph=context.evaluated_depsgraph_get();temporary=[];scene=None;draftpath=None
    window=context.window;original_scene=window.scene if window else None
    try:
        sources=[obj];extra=None
        if mode=='DETAILED' and p.category=='LED':
            extra=screen_objects.detail_mesh(obj)
        ev=obj.evaluated_get(graph);mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=graph);temporary.append(mesh)
        metric=json.loads(p.metrics)
        report=screen_uv.diagnose(mesh,context.scene.unit_settings.scale_length,metric.get('rx',p.resolution_x),metric.get('ry',p.resolution_y),p.direction=='REVERSED')
        if report['errors']:raise ValueError('Export blocked: '+report['errors'][0])
        if extra:temporary.append(extra);extra=None
        scene=bpy.data.scenes.new('.Beam export isolation');scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
        matrix=obj.matrix_world.copy() if space=='WORLD' else Matrix.Identity(4)
        matrix=Matrix.Scale(context.scene.unit_settings.scale_length,4)@matrix
        for i,data in enumerate(temporary):
            data.transform(matrix)
            if matrix.determinant()<0:data.flip_normals()
            data.materials.clear()
            active_name=data.uv_layers.active.name if data.uv_layers.active else None
            for index in reversed(range(len(data.uv_layers))):
                if data.uv_layers[index].name!=active_name:data.uv_layers.remove(data.uv_layers[index])
            data.update()
            out=bpy.data.objects.new(p.identifier+('_Display' if i==0 else '_Cabinets'),data);scene.collection.objects.link(out);out.select_set(True,view_layer=scene.view_layers[0])
        scene.view_layers[0].objects.active=next(iter(scene.objects))
        fd,draftpath=tempfile.mkstemp(prefix='.beam-export-',suffix=path.suffix,dir=path.parent);os.close(fd)
        if window:window.scene=scene
        export_objects=list(scene.objects)
        with context.temp_override(scene=scene,view_layer=scene.view_layers[0],selected_objects=export_objects,selected_editable_objects=export_objects,active_object=export_objects[0],object=export_objects[0]):
            if fmt=='OBJ':
                status=bpy.ops.wm.obj_export(filepath=draftpath,export_selected_objects=True,forward_axis='Y',up_axis='Z',global_scale=1,apply_modifiers=False,export_materials=False,export_uv=True,export_normals=True)
            else:
                status=bpy.ops.export_scene.fbx(filepath=draftpath,use_selection=True,object_types={'MESH'},axis_forward='Y',axis_up='Z',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=False,colors_type='NONE',bake_anim=False,add_leaf_bones=False,path_mode='STRIP')
        if 'FINISHED' not in status or not Path(draftpath).stat().st_size:raise ValueError('Blender exporter did not produce a file')
        os.replace(draftpath,path);draftpath=None
        return path
    finally:
        if window and original_scene:window.scene=original_scene
        if scene:
            for item in list(scene.objects):bpy.data.objects.remove(item,do_unlink=True)
            bpy.data.scenes.remove(scene)
        for mesh in temporary:
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        if 'extra' in locals() and extra and extra not in temporary and extra.users==0:bpy.data.meshes.remove(extra)
        if draftpath:Path(draftpath).unlink(missing_ok=True)
