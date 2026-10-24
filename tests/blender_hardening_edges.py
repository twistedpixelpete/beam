"""Interop edge matrices, fractional output and additive-preset safety."""
import sys,math
from pathlib import Path
import bpy
from mathutils import Matrix,Euler
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import projector_object,export_designer as export,transform_conversion as t,optics_library
addon.register();c=bpy.context
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
o=projector_object.create(c);p=o.ps;p.lumens=12345.5;p.brightness=37.25;p.stack=2
cases=0
for position in ((-123,-456,-789),(100000,-200000,30000),(.0001,-.0003,.0007)):
 for angles in ((89.999,173,71),(-89.999,-173,-71),(17,383,377),(70,-135,150)):
  for shift,ratio,raster in (((25,-30),.1,(4096,2160)),((-35,40),8.5,(1200,1920))):
   p.shift_h,p.shift_v=shift;p.throw_ratio=ratio;p.resolution_x,p.resolution_y=raster
   r=Euler(tuple(math.radians(v) for v in (angles[0],angles[2],angles[1])),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X');m=r.to_4x4();m.translation=position;o.matrix_world=m
   row=export.rows_for_scene(c)[0];assert row[:3]==[p.identifier,*raster]
   assert abs(row[3]-12345.5*.3725*2)<.01
   assert max(abs(a-b) for a,b in zip(row[7:10],(position[0],position[2],position[1])))<.01
   assert max(abs(a-b) for a,b in zip(row[5:7],(shift[0]/50,shift[1]/50)))<1e-6
   x,y,z=row[10:];rebuilt=Euler(tuple(math.radians(v) for v in (x,-z,-y)),'YXZ').to_matrix()@Matrix.Rotation(math.pi/2,3,'X')
   assert max(abs(r[i][j]-rebuilt[i][j]) for i in range(3) for j in range(3))<5e-5
   assert export.csv_text([row])==export.csv_text(export.rows_for_scene(c));cases+=1
assert len(optics_library.UNSUPPORTED_OPTICS)==3
assert all(key not in optics_library.LENSES for key in optics_library.UNSUPPORTED_OPTICS)
print(f'HARDENING EDGES PASS: {cases} combined translation/rotation/shift/raster/brightness/throw cases')
addon.unregister()
