"""Designer Projector Study CSV; distinct from Mapping Matter's export schema."""
import csv,io,json,math,hashlib,os,tempfile
from pathlib import Path
import bpy
from . import runtime,transform_conversion as conversion
from .projector_object import projectors
from .interchange import timestamp

HEADER=['Name','Resolution X','Resolution Y','Brightness (lum)','Throw Ratio','Lens Shift Horizontal','Lens Shift Vertical','Position X (m)','Position Y (m)','Position Z (m)','Rotation X (deg)','Rotation Y (deg)','Rotation Z (deg)']
EXPORTER_VERSION='1.2.0'

def rows_for_scene(context):
    context.view_layer.update();runtime.refresh(True)
    objects=sorted((o for o in projectors(context.scene) if o.ps.active),key=lambda o:o.ps.identifier)
    if not objects:raise ValueError('No active projectors to export')
    rows=[]
    for obj in objects:
        if not runtime.rigid(obj):raise ValueError(f'{obj.ps.identifier}: restore unit scale; scaled/sheared transforms cannot be exported')
        p=obj.ps;r=runtime.CACHE[obj.as_pointer()]
        rows.append([p.identifier,p.resolution_x,p.resolution_y,r['metrics'].total_lumens,p.throw_ratio,
            *conversion.designer_lens_shift(p.shift_h,p.shift_v),*conversion.designer_position_m(r['origin'],context.scene.unit_settings.scale_length),*conversion.designer_orientation_degrees(r['rotation'])])
    return rows

def csv_text(rows):
    buffer=io.StringIO();writer=csv.writer(buffer,lineterminator='\n');writer.writerow(HEADER)
    for row in rows:
        if len(row)!=len(HEADER) or any(isinstance(v,float) and not math.isfinite(v) for v in row):raise ValueError('Invalid Designer CSV row')
        writer.writerow([format(v,'.10g') if isinstance(v,float) else v for v in row])
    return buffer.getvalue()

def write_with_metadata(path,text,convention,identities):
    path=Path(path);meta=dict(exporter='Beam',exporter_version=EXPORTER_VERSION,transform_convention=convention,exported_at=timestamp(),csv_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),projectors=identities,
        validation_scope='Mapping Matter importer / controlled fixtures' if convention==conversion.DESIGNER_CONVENTION_ID else 'Mapping Matter export fixtures',designer_application_tested=False)
    # Stage both files before replacement. Hash checks detect an interrupted pair
    # update; two separate filesystem paths cannot be committed atomically.
    staged=[]
    try:
        for destination,payload in ((path,text.encode('utf-8')),(path.with_suffix('.metadata.json'),(json.dumps(meta,indent=2)+'\n').encode('utf-8'))):
            fd,name=tempfile.mkstemp(prefix='.beam-export-',dir=path.parent)
            staged.append((Path(name),destination))
            with os.fdopen(fd,'wb') as handle:handle.write(payload)
        for temporary,destination in reversed(staged):os.replace(temporary,destination)
    finally:
        for temporary,_ in staged:temporary.unlink(missing_ok=True)

class BEAM_OT_export_designer(bpy.types.Operator):
    bl_idname='beam.export_designer';bl_label='Export Designer CSV'
    bl_description='Designer Projector Study schema for Mapping Matter Import Projectors from Designer CSV; includes convention metadata sidecar'
    filepath:bpy.props.StringProperty(subtype='FILE_PATH',default='Beam_Designer.csv')
    filter_glob:bpy.props.StringProperty(default='*.csv',options={'HIDDEN'})
    check_existing:bpy.props.BoolProperty(default=True,options={'HIDDEN'})
    def check(self,context):
        path=str(Path(self.filepath).with_suffix('.csv'));changed=path!=self.filepath;self.filepath=path;return changed
    def invoke(self,context,event):
        self.check(context);context.window_manager.fileselect_add(self);return {'RUNNING_MODAL'}
    def execute(self,context):
        try:
            text=csv_text(rows_for_scene(context));identities=[dict(name=o.ps.identifier,uuid=o.ps.uuid) for o in projectors(context.scene) if o.ps.active]
            write_with_metadata(Path(bpy.path.abspath(self.filepath)).with_suffix('.csv'),text,conversion.DESIGNER_CONVENTION_ID,identities)
        except (ValueError,OSError) as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
