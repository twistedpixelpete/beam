"""Read-only capability and raster-alignment study; run in background Blender."""
import bpy, json, math, random, sys
from pathlib import Path
from mathutils import Matrix, Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from projection_study.projection_math import image_point
rng=random.Random(14)
max_error=0
for i in range(10000):
    ratio=rng.uniform(.05,100); aspect=rng.choice([9/16,10/16,1,16/9])
    sx=rng.uniform(-3,3); sy=rng.uniform(-3,3)
    u,v=rng.random(),rng.random(); depth=rng.uniform(.1,100)
    x,y,z=image_point(u,v,depth,ratio,1920,1920*aspect,sx*100,sy*100)
    # Beam's existing GPU projection matrix, including homogeneous division.
    matrix=Matrix(((2*ratio,0,2*sx,0),(0,2*ratio/aspect,2*sy,0),(0,0,-1,-.01),(0,0,-1,0)))
    q=matrix@Vector((x,y,z,1))
    shader_u=x/(-z)*ratio+.5-sx
    shader_v=y/(-z)*ratio/aspect+.5-sy
    error=max(abs(shader_u-(q.x/q.w*.5+.5))*1920,abs(shader_v-(q.y/q.w*.5+.5))*1920*aspect)
    max_error=max(max_error,error)
light=bpy.data.lights.new('Beam study capability probe','SPOT')
try:
    if hasattr(light,'use_nodes'):light.use_nodes=True
    nodes=light.node_tree.nodes
    supported={}
    for kind in ['ShaderNodeNewGeometry','ShaderNodeVectorTransform','ShaderNodeSeparateXYZ','ShaderNodeMath','ShaderNodeTexImage','ShaderNodeEmission','ShaderNodeOutputLight','ShaderNodeGroup']:
        node=nodes.new(kind); supported[kind]=True;nodes.remove(node)
    result=dict(blender=bpy.app.version_string,cycles_available=hasattr(bpy.context.scene,'cycles'),light_node_types=supported,
        normalize_supported=hasattr(light,'normalize'),spot_max_radians=light.bl_rna.properties['spot_size'].hard_max,
        mapping_cases=10000,max_matrix_difference_pixels=max_error,
        limitation='No renders or timing benchmarks; light Incoming vector sign and radiometry remain to be tested in Cycles.')
    assert max_error<.01
    print(json.dumps(result,indent=2))
finally:bpy.data.lights.remove(light)
