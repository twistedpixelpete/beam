"""Generate actual Beam exporter input for live Mapping Matter import acceptance."""
import bpy,sys,csv,math,json
from pathlib import Path
from mathutils import Matrix,Euler
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,export_designer
addon.register()
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
expected=[]
for f in sorted((root/'tests/fixtures/mapping_matter').glob('*.csv')):
 row=list(csv.DictReader(f.open()))[-1];o=projector_object.create(bpy.context);p=o.ps
 p.identifier='Beam '+f.stem.removeprefix('Beam-MM-');o.name=p.identifier
 p.resolution_x=int(row['Projector_Native-Rez-X']);p.resolution_y=int(row['Projector_Native-Rez-Y']);p.throw_ratio=float(row['Projector_Trow-Ratio']);p.shift_h=float(row['Lens_Shift-H(%)'])/2;p.shift_v=float(row['Lens_Shift-V(%)'])/2;p.lumens=10000
 r=Euler(tuple(math.radians(float(row[k])) for k in ('Pitch(deg)','Roll(deg)','Yaw(deg)')),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X');m=r.to_4x4();m.translation=tuple(float(row[k])/1000 for k in ('Lens_X','Lens_Y','Lens_Z'));o.matrix_world=m
 expected.append(dict(name=p.identifier,reference=row))
out=root/'work/production';out.mkdir(exist_ok=True,parents=True)
export_designer.write_with_metadata(out/'Beam-Designer-fixtures.csv',export_designer.csv_text(export_designer.rows_for_scene(bpy.context)),export_designer.conversion.DESIGNER_CONVENTION_ID,[dict(name=o.ps.identifier,uuid=o.ps.uuid) for o in bpy.context.scene.objects if o.ps.is_projector])
(out/'designer-expected.json').write_text(json.dumps(expected,indent=2))
addon.unregister()

# Re-running this generator must retain the schema and numbers actually imported.
reference=root/'tests/fixtures/designer/Beam-Designer-fixtures.csv'
assert (out/'Beam-Designer-fixtures.csv').read_text()==reference.read_text()
print('PASS current Designer exporter reproduces externally imported CSV exactly')
