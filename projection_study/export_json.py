"""PATCH-ready JSON, no PATCH dependency or network integration."""
import json
import math
import tomllib
from pathlib import Path
import bpy
from . import runtime, transform_conversion
from .projector_object import projectors
from .interchange import SCHEMA_VERSION, timestamp
from .export_table import HEADER


EXPORTER_VERSION='1.0.0'

# Stable machine-readable conventions; additive fields do not change schema 1.0.
CONVENTIONS={
    'world':{'space':'blender_world','handedness':'right','up_axis':'+Z','position_unit':'m'},
    'projector_local':{'origin':'optical_origin','forward_axis':'-Z','up_axis':'+Y'},
    'euler':{'order':'XYZ','unit':'degrees','matrix_composition':'Rz @ Ry @ Rx','vectors':'column'},
    'quaternion_order':'wxyz',
    'matrix':{'storage':'row_major','vectors':'column','translation_unit':'m','scale':'dimensionless'},
    'reconstruction_authority':'projector_world_pose',
    'group_composition':'projector_world_matrix = group.transform.matrix @ member.transform_in_group',
    'member_order':{'basis':'stored_members_array','index_base':0,'layout':'row_major','column_axis':'+X','row_axis':'-Y','space':'group_local'},
    'throw_distance':'axial_depth_of_current_centre_hit_along_projector_local_minus_Z',
    'image_dimensions':'nominal_rectangle_perpendicular_to_optical_axis_at_throw_distance',
    'pixel_density':'horizontal_resolution_divided_by_nominal_image_width',
    'illuminance':'total_lumens_divided_by_nominal_image_area_no_surface_angle_or_loss_correction',
    'colour':'linear_RGB_sRGB_primaries_to_standard_sRGB_no_view_transform',
    'ui_state':'visibility_and_preview_fields_are_presentation_hints_not_technical_filters',
    'output_modes':['SOLID','GRID','ID','CHECKER','UV_GRID','COLOR_GRID','IMAGE']}



def display_colour(linear):
    """Standard sRGB swatch, independent of Blender exposure/view transforms."""
    rgb=[12.92*v if v<=0.0031308 else 1.055*v**(1/2.4)-0.055 for v in (max(0,min(1,float(c))) for c in linear)]
    return rgb,'#'+''.join(f'{int(v*255+.5):02X}' for v in rgb)


def document(context):
    context.view_layer.update()
    from . import target_raycast
    target_raycast.invalidate()
    runtime.refresh(True)
    scene=context.scene; unit=scene.unit_settings.scale_length
    settings=scene.ps_study
    items=[]
    for obj in sorted(projectors(scene),key=lambda o:o.ps.identifier):
        p=obj.ps; r=runtime.CACHE[obj.as_pointer()]; m=r['metrics']
        hit=r['hit']
        srgb,hex_colour=display_colour(p.colour)
        items.append(dict(
            uuid=p.uuid, name=p.identifier, object_name=obj.name, include_in_disguise_export=p.active,
            notes=p.notes, resolution={'x':p.resolution_x,'y':p.resolution_y}, throw_ratio=p.throw_ratio,
            lens_shift_percent={'horizontal':p.shift_h,'vertical':p.shift_v,'basis':'full_image_dimensions'},
            stack_quantity=p.stack,brightness_percent=p.brightness,nominal_lumens=p.lumens,total_lumens=m.total_lumens,
            position_m=[v*unit for v in r['origin']],
            rotation={'space':'blender_world','order':'XYZ','unit':'degrees',
                      'euler':[math.degrees(v) for v in r['rotation'].to_euler('XYZ')]},
            transform_valid=runtime.rigid(obj),
            target={'space':'blender_world','status':'hit' if hit else 'no_hit','point_m':[v*unit for v in hit[0]] if hit else None,
                    'object_name':hit[3] if hit else None,'filter_object_name':None,'automatic':True},
            calculated=None if not hit else dict(throw_distance_m=m.distance,centre_ray_distance_m=r['slant'],
                image_width_m=m.width,image_height_m=m.height,pixel_density_px_per_m=m.pixels_per_metre,
                pixel_size_m_per_px=m.pixel_size_m,pixel_size_mm_per_px=m.pixel_size_m*1000,
                dpi=m.dpi,estimated_illuminance_lux=m.lux),
            display_units=settings.display_units,study_colour_linear_rgb=list(p.colour),study_colour_srgb=srgb,study_colour_hex=hex_colour,output_mode=p.output_mode,
            visibility={'identifier':p.show_identifier,'projected_identifier':p.show_projected_identifier,'frustum':p.show_frustum,'centre_ray':p.show_centre_ray,'target_marker':p.show_target_marker,'grid':p.show_grid,'output':p.show_output}))
    from .study_views import proposed_names
    filenames=proposed_names(scene)
    views=[]
    for view in settings.views:
        camera=view.camera
        views.append(dict(uuid=view.uuid,name=view.name,camera_name=camera.name if camera else None,
            camera=None if camera is None else dict(space='blender_world',position_m=[v*unit for v in camera.matrix_world.translation],
                rotation_quaternion_wxyz=list(camera.matrix_world.to_quaternion()),type=camera.data.type,
                lens_mm=camera.data.lens,ortho_scale_m=camera.data.ortho_scale*unit),
            resolution={'x':view.resolution_x,'y':view.resolution_y},
            overlays={'projected_identifiers':view.include_projected_identifiers,'enabled':view.include_overlays,'labels':view.include_labels,'frustums':view.include_frustums,'grids':view.include_grids},
            expected_image_filename=filenames[view.uuid],
            exported_image_filename=view.image_filename or None,exported_at=view.exported_at or None))
    from .export_disguise import collect_rows
    rows,errors=collect_rows(context,refresh=False)
    error='; '.join(f"{e['projector_name'] or 'Export'}: {e['message']}" for e in errors) or None
    producer=dict(beam_version=tomllib.loads(Path(__file__).with_name('blender_manifest.toml').read_text())['version'],
        exporter_version=EXPORTER_VERSION,blender_version=bpy.app.version_string,
        blender_build_hash=bpy.app.build_hash.decode('ascii',errors='replace'))
    from .blend_groups import serialize
    data=dict(producer=producer,conventions=CONVENTIONS,product='Beam',maintainer='Twisted Pixel',project_metadata={key:getattr(settings,key) for key in ('project_name','venue','revision','client','author')},blend_groups=serialize(context),schema='projection-study',schema_version=SCHEMA_VERSION,exported_at=timestamp(),
        scene_name=scene.name,helper_visibility={key:getattr(settings,key) for key in ('show_frustums','show_centre_rays','show_projected_identifiers','show_labels','show_outputs','show_study_cameras')},projection_model={'receivers':'visible_evaluated_surfaces','coordinates':'perspective_raster','occlusion':'gpu_first_depth','target_role':'automatic_centre_reference_only','shadow_max_dimension':int(settings.shadow_resolution)},units={'internal_length':'m','display_length':settings.display_units,'disguise_length':'mm',
        'pixel_density':'px/m','pixel_size':'m/px','illuminance':'lux','coordinate_space':'blender_world','rotation':'degrees','quaternion':'unitless_wxyz','resolution':'px',
        'luminous_flux':'lm','brightness':'percent','lens_shift':'percent_of_full_image','dpi':'px/in','overlap_by_input_mode':{'PIXELS':'px','PERCENT':'percent','METRES':'m'}},
        projectors=items,study_views=views,
        current_view_image={'filename':settings.last_current_image or None,'exported_at':settings.last_current_exported_at or None},
        disguise={'transform_convention':transform_conversion.CONVENTION,'validated':transform_conversion.VALIDATED,
                  'convention_id':'blender_xyz_euler_xyz_unvalidated_v1','columns':HEADER,'rows':rows,'error':error,
                  'validation':{'scope':'disguise_rows','errors':errors}})
    from .json_contract import validate_relationships
    validate_relationships(data)
    return data


class PS_OT_export_json(bpy.types.Operator):
    bl_idname='ps.export_json'
    bl_label='Export Study Data (JSON)'
    filepath: bpy.props.StringProperty(subtype='FILE_PATH',default='Beam.json')
    filter_glob: bpy.props.StringProperty(default='*.json',options={'HIDDEN'})
    check_existing: bpy.props.BoolProperty(default=True,options={'HIDDEN'})
    def invoke(self,context,event):
        context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}
    def execute(self,context):
        try:
            path=Path(bpy.path.ensure_ext(self.filepath,'.json'))
            path.write_text(json.dumps(document(context),indent=2,allow_nan=False)+'\n',encoding='utf-8')
        except (OSError,ValueError) as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},'Study data exported'); return {'FINISHED'}
