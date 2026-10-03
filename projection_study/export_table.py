"""Format-only writer, independent of bpy."""
import csv
import math

HEADER = 'Projector_Name,Projector_Qte(Stack),Projector_Native-Rez-X,Projector_Native-Rez-Y,Projector_Lumens(lux),Projector_Brightness(%),Projector_Total_Lumens(lux),Projector_Trow-Ratio,Lens_Shift-H(%),Lens_Shift-V(%),Lens_X,Lens_Y,Lens_Z,Pitch(deg),Yaw(deg),Roll(deg),Target_X,Target_Y,Target_Z,Target_Distance,Target_Width,Target_Height,Target_Illuminance,Target_DPI,Unit_Dim,Unit_Illuminance,Projector_UUID'.split(',')


def write_table(stream,rows):
    rows=list(rows)
    for row in rows:
        if len(row)!=len(HEADER): raise ValueError('Incorrect projector column count')
        if any(isinstance(v,float) and not math.isfinite(v) for v in row):
            raise ValueError('Non-finite export value')
    writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(HEADER)
    for row in rows:
        writer.writerow([format(v,'.10g') if isinstance(v,float) else v for v in row])
