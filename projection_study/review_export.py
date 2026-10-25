"""Local, immutable Review Package prototype. Reuses the authoritative study contract."""
import json
import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from uuid import uuid4
import bpy
from mathutils import Matrix, Vector
from . import study_reporting, runtime


def export(context, destination):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise ValueError('Choose a new revision folder; existing packages are never overwritten')
    if context.mode != 'OBJECT':
        raise ValueError('Switch to Object Mode before exporting a review')
    scene = context.scene
    data = study_reporting.document(context)
    study_reporting.validate(data)
    unit = scene.unit_settings.scale_length
    graph = context.evaluated_depsgraph_get()
    project_id = scene.get('beam_review_project_uuid') or str(uuid4())
    revision_id = str(uuid4())
    # Review-only presentation metadata; original Beam records and UUIDs stay intact.
    presentation = {'projectors': {}, 'views': {}, 'geometry': []}
    for obj in scene.objects:
        if not obj.ps.is_projector:
            continue
        r = runtime.CACHE[obj.as_pointer()]
        presentation['projectors'][obj.ps.uuid] = {
            'rotation_quaternion_wxyz': list(r['rotation'].to_quaternion()),
            'frustum_endpoints_m': [list(v * unit) for v in r['helper_corners']],
            'axis_endpoint_m': list((r['origin'] + r['rotation'] @ Vector((0, 0, -r['metrics'].distance / unit))) * unit),
            'endpoint_rule': 'first_scene_hit_or_nominal_preview_corner',
        }
    for view in scene.ps_study.views:
        cam = view.camera
        if cam is None:
            continue
        if cam.data.type not in {'PERSP','ORTHO'}:
            raise ValueError('Beam Review v0.1 supports perspective and orthographic Study Views only')
        projection = cam.calc_matrix_camera(graph, x=view.resolution_x, y=view.resolution_y, scale_x=1, scale_y=1)
        # Camera clipping and orthographic translation must use the package metre units.
        # Compute with a temporary camera data copy, without touching authoring settings.
        copy = cam.copy(); copy.data = cam.data.copy()
        try:
            copy.data.clip_start *= unit; copy.data.clip_end *= unit; copy.data.ortho_scale *= unit
            projection = copy.calc_matrix_camera(graph, x=view.resolution_x, y=view.resolution_y, scale_x=1, scale_y=1)
            presentation['views'][view.uuid] = {'projection_matrix_row_major': [list(row) for row in projection],
                'clip_start_m': copy.data.clip_start, 'clip_end_m': copy.data.clip_end}
        finally:
            camera_data = copy.data; bpy.data.objects.remove(copy); bpy.data.cameras.remove(camera_data)
    data['review'] = presentation
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.beam-review-', dir=destination.parent))
    temporary_scene = None
    created = []
    original_scene = context.window.scene
    try:
        (staging / 'assets').mkdir(); (staging / 'thumbnails').mkdir()
        (staging/'assets/README.txt').write_text('All current geometry textures are embedded in scene.glb.\n')
        (staging/'thumbnails/README.txt').write_text('Reserved for optional revision thumbnails; none generated in v0.1.\n')
        temporary_scene = bpy.data.scenes.new('Beam Review export (temporary)')
        temporary_scene.unit_settings.scale_length = 1
        for instance in graph.object_instances:
            obj = instance.object; original = obj.original
            if obj.type not in {'MESH','CURVE','SURFACE','FONT','META'} or original.ps.is_projector or original.get('ps_helper') or original.get('beam_screen_detail'):
                continue
            if not instance.show_self or (not instance.is_instance and not original.visible_get()):
                continue
            mesh = bpy.data.meshes.new_from_object(obj, preserve_all_data_layers=True, depsgraph=graph)
            if mesh is None:
                continue
            target = bpy.data.objects.new(original.name, mesh); created.append((target, mesh))
            temporary_scene.collection.objects.link(target)
            target.matrix_world = Matrix.Scale(unit, 4) @ instance.matrix_world
            uid = original.beam_screen.uuid if original.beam_screen.is_screen else original.get('beam_receiver_uuid')
            if uid:
                target['beam_uuid'] = uid
            target['beam_name'] = original.name
            target['beam_kind'] = 'screen' if original.beam_screen.is_screen else 'geometry'
            presentation['geometry'].append({'node_name':target.name,'source_name':original.name,'uuid':uid,'kind':target['beam_kind']})
        if not created:
            raise ValueError('No visible venue or receiver geometry to export')
        context.window.scene = temporary_scene
        with context.temp_override(scene=temporary_scene, view_layer=temporary_scene.view_layers[0]):
            result = bpy.ops.export_scene.gltf(filepath=str(staging/'scene.glb'), export_format='GLB',
                use_active_scene=True, export_yup=True, export_extras=True, export_cameras=False,
                export_lights=False, export_animations=False, export_apply=False)
        if result != {'FINISHED'}:
            raise RuntimeError('GLB export did not finish')
        context.window.scene = original_scene
        (staging/'beam.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        manifest = {'schema':'beam-review','schema_version':'0.1.0','product':'Beam Review','maintainer':'Twisted Pixel',
            'project_uuid':project_id,'revision_uuid':revision_id,'revision_label':scene.ps_study.revision or 'Unnumbered revision',
            'created_at':data['exported_at'],'beam':'beam.json','scene':'scene.glb',
            'coordinates':{'beam':'right-handed Z-up metres','scene':'right-handed Y-up metres','beam_to_scene':'[x, z, -y]'},
            'analysis':'Exported Authoring results only; no browser recomputation',
            'warnings':['Prototype review geometry is not a calibrated projection render. Procedural Blender shaders may not translate to glTF.'],
            'files':{name:{'sha256':hashlib.sha256((staging/name).read_bytes()).hexdigest(),'bytes':(staging/name).stat().st_size} for name in ('beam.json','scene.glb')}}
        (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        # No existing revision may be replaced.
        if destination.exists():
            raise ValueError('Destination appeared during export; choose a new folder')
        os.rename(staging,destination)
        scene['beam_review_project_uuid'] = project_id
        return manifest
    finally:
        context.window.scene = original_scene
        for obj,mesh in created:
            bpy.data.objects.remove(obj,do_unlink=True)
            if mesh.users == 0: bpy.data.meshes.remove(mesh)
        if temporary_scene: bpy.data.scenes.remove(temporary_scene)
        if staging.exists(): shutil.rmtree(staging)
        runtime.invalidate()


class BEAM_OT_export_review(bpy.types.Operator):
    bl_idname = 'beam.export_review'
    bl_label = 'Export for Beam Review'
    bl_description = 'Create a new local read-only review revision; never replace an existing folder'
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    def invoke(self,context,event):
        self.directory = str(Path(bpy.path.abspath('//')) / ('Beam-Review-' + str(uuid4())[:8]))
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        try:
            export(context,self.directory)
        except Exception as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},'Local Review Package created; open with the Beam Review prototype')
        return {'FINISHED'}
