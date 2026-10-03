import bpy
from pathlib import Path
from . import runtime, transform_conversion as conversion
from .projector_object import projectors
from .export_table import write_table


def collect_rows(context,refresh=True):
    if refresh:
        context.view_layer.update()
        from . import target_raycast
        target_raycast.invalidate()
        runtime.refresh(True)
    active=sorted((o for o in projectors(context.scene) if o.ps.active),key=lambda o:int(o.ps.identifier[2:]))
    rows=[]; errors=[]
    if not active:
        errors.append(dict(projector_uuid=None,projector_name=None,code='NO_ACTIVE_PROJECTORS',message='No active projectors to export'))
    for obj in active:
        p=obj.ps; record=runtime.CACHE[obj.as_pointer()]
        problems=[]
        if not record['hit']:
            problems.append(('NO_TARGET','No centre target hit; aim at venue geometry or exclude from disguise export.'))
        if not runtime.rigid(obj):
            problems.append(('INVALID_TRANSFORM','Scaled or sheared projector transform; restore unit scale (including parents).'))
        for code,message in problems:
            errors.append(dict(projector_uuid=p.uuid,projector_name=p.identifier,code=code,message=message))
        if problems: continue
        m=record['metrics']
        unit=context.scene.unit_settings.scale_length
        position=conversion.position_mm(record['origin'],unit)
        target=conversion.position_mm(record['hit'][0],unit)
        angles=conversion.orientation_degrees(record['rotation'])
        shift=conversion.lens_shift_percent(p.shift_h,p.shift_v)
        rows.append([p.identifier,p.stack,p.resolution_x,p.resolution_y,p.lumens,p.brightness,
                     m.total_lumens,p.throw_ratio,*shift,*position,*angles,*target,
                     m.distance*1000,m.width*1000,m.height*1000,m.lux,m.dpi,'mm','lux',p.uuid])
    return rows,errors


def rows_for_scene(context):
    """Standalone CSV remains atomic: any invalid included projector blocks writing."""
    rows,errors=collect_rows(context)
    if errors:
        error=errors[0]; name=error['projector_name']
        if error['code']=='NO_TARGET':
            raise ValueError(f'{name}: no target hit. Aim at venue geometry or exclude it from export.')
        if error['code']=='INVALID_TRANSFORM':
            raise ValueError(f'{name}: scaled or sheared projector transform; restore unit scale (including parents).')
        raise ValueError('No active projectors to export')
    return rows


class PS_OT_export(bpy.types.Operator):
    bl_idname='ps.export'
    bl_label='Export CSV'
    bl_description='Export the supported table schema; transform convention still requires Designer validation'
    filepath: bpy.props.StringProperty(subtype='FILE_PATH',default='Beam_projectors.csv')
    filter_glob: bpy.props.StringProperty(default='*.csv',options={'HIDDEN'})
    check_existing: bpy.props.BoolProperty(default=True,options={'HIDDEN'})
    def check(self,context):
        path=str(Path(self.filepath).with_suffix('.csv'))
        changed=path!=self.filepath
        self.filepath=path
        return changed
    def invoke(self,context,event):
        self.check(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        try:
            rows=rows_for_scene(context)
            path=Path(bpy.path.abspath(self.filepath)).with_suffix('.csv')
            # Validate all rows before opening the destination file.
            import io
            buffer=io.StringIO(); write_table(buffer,rows)
            path.write_text(buffer.getvalue(),encoding='utf-8')
        except (ValueError,OSError) as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},f'Exported {len(rows)} projector(s) to {path}')
        return {'FINISHED'}
