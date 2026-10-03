exec((root/'tests/blender_m5.py').read_text())
from projection_study.export_disguise import rows_for_scene
from projection_study.export_table import write_table, HEADER
import io,csv
rows=rows_for_scene(bpy.context)
assert len(rows)==3
assert len(HEADER)==27
assert all(len(row)==27 for row in rows)
assert rows[0][0]=='PJ01' and rows[0][-1]==original_uuid
assert rows[0][-3:-1]==['mm','lux']
assert rows[0][19]>14000
assert abs(rows[0][23]-rows[0][2]/(rows[0][20]/25.4))<1e-6
buf=io.StringIO(); write_table(buf,rows)
assert 'Projector_Trow-Ratio' in buf.getvalue()
assert len(list(csv.reader(io.StringIO(buf.getvalue()))))==4
# No-hit export must not silently use the preview distance.
wall.hide_set(True)
target_raycast.invalidate()
try:
    rows_for_scene(bpy.context)
    raise AssertionError('No-hit export accepted')
except ValueError as exc:
    assert 'no target hit' in str(exc)
print('MILESTONE 6 PASS')
