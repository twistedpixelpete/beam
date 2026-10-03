exec((root/'tests/blender_m3.py').read_text())
from projection_study import viewport_display as display
from projection_study.output_patterns import pattern
# The connected UI supplies a real GPU context for shader compilation/batches.
display.shaders()
for mode in ('SOLID','GRID','ID','CHECKER','UV_GRID','COLOR_GRID','IMAGE'):
    o.ps.output_mode=mode
    if mode=='IMAGE': o.ps.image=bpy.data.images.new('PS Test image',width=32,height=32)
    runtime.refresh(True)
    record=runtime.CACHE[o.as_pointer()]
    batches=display.build(o,record)
    assert 'frustum' in batches
    from projection_study import projection_renderer
    shadow=projection_renderer.shadow_map(o,record)
    assert shadow['receivers']
    if mode in {'UV_GRID','COLOR_GRID'}: assert record['uv_image'].generated_type==mode
assert len(pattern('GRID','PJ01',1920,1080)[0])>20
print('MILESTONE 4 PASS')
