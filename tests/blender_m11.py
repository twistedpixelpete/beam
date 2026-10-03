"""Hard acceptance: independent GPU rays, automatic targets, continuous raster."""
import bpy,gpu
from mathutils import Vector
from projection_study import runtime,projection_renderer,scene_geometry
from projection_study.projection_math import image_point

def plane(name,y,x0,x1,z0,z1):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],[],[(0,1,2,3)])
    obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj)
    return obj

foreground=plane('Foreground',10,-2,2,-1.5,1.5)
wall=plane('Rear Wall',15,-10,10,-6,6)
bpy.ops.ps.add(); projector=bpy.context.object
p=projector.ps
bpy.context.view_layer.update(); runtime.refresh(True)
r=runtime.CACHE[projector.as_pointer()]
assert p.target==foreground and p.has_target
assert abs(r['metrics'].distance-10)<1e-4
assert r['beam_depth']>15
shadow=projection_renderer.shadow_map(projector,r)

def sample(uv):
    record=runtime.CACHE[projector.as_pointer()]
    entry=projection_renderer.shadow_map(projector,record)
    w,h=entry['size']
    with entry['offscreen'].bind():
        value=gpu.state.active_framebuffer_get().read_color(int(uv[0]*w),int(uv[1]*h),1,1,1,0,'FLOAT')
        value.dimensions=1
        return float(value[0])

assert abs(sample((.5,.5))-10)<.01
assert abs(sample((.2,.5))-15)<.01
assert abs(sample((.9,.5))-15)<.01
# UV Grid shares the exact same cached visibility and receiver mapping.
texture=shadow['texture']
p.output_mode='UV_GRID'; runtime.refresh()
r=runtime.CACHE[projector.as_pointer()]
assert r['uv_image'].generated_type=='UV_GRID'
assert tuple(r['uv_image'].size)==(1920,1080)
assert projection_renderer.shadow_map(projector,r)['texture']==texture
assert abs(sample((.5,.5))-10)<.01 and abs(sample((.2,.5))-15)<.01
p.output_mode='COLOR_GRID'; runtime.refresh()
r=runtime.CACHE[projector.as_pointer()]
assert r['uv_image'].generated_type=='COLOR_GRID'
assert tuple(r['uv_image'].size)==(1920,1080)
assert projection_renderer.shadow_map(projector,r)['texture']==texture
assert abs(sample((.5,.5))-10)<.01 and abs(sample((.2,.5))-15)<.01
# Foreground enters a different part of the same raster; no target assignment.
foreground.location.x=4
bpy.context.view_layer.update(); runtime.refresh()
assert p.target==wall and abs(p.target_distance_m-15)<.01
assert abs(sample((.5,.5))-15)<.01 and abs(sample((.9,.5))-10)<.01
# A hole at raster centre does not disable side projection.
foreground.location.z=-2
wall.location.x=15
bpy.context.view_layer.update(); runtime.refresh()
assert p.target is None and not p.has_target
assert runtime.CACHE[projector.as_pointer()]['hit'] is None
assert abs(sample((.95,.8))-15)<.01
assert abs(sample((.8,.2))-10)<.01
# Lens shift uses the true raster centre, not the bare optical axis.
foreground.location=(0,0,0); wall.location=(0,0,0)
p.shift_h=30
bpy.context.view_layer.update(); runtime.refresh()
assert p.target==wall
assert abs(runtime.CACHE[projector.as_pointer()]['hit'][0].x-4.5)<.01
# Restore acceptance fixture for visual capture.
p.shift_h=0; p.output_mode='GRID'
bpy.context.view_layer.update(); runtime.refresh()
assert p.target==foreground
print('MILESTONE 11 GPU first-depth / automatic target / no-target receivers / UV mode PASS')
