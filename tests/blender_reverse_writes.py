"""Reverse Mapping leaves shader inputs alone unless a value really changed. Background, no GPU."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import reverse_mapping
addon.register();c=bpy.context
m=bpy.data.materials.new('Mat');m.use_nodes=True
node=m.node_tree.nodes.new('ShaderNodeMath')
mesh=bpy.data.meshes.new('Wall');mesh.from_pydata([(0,0,0),(1,0,0),(1,0,1)],[],[(0,1,2)]);mesh.update();mesh.materials.append(m)
c.scene.collection.objects.link(bpy.data.objects.new('Wall',mesh));c.view_layer.update()
updates=[];handler=lambda scene,graph:updates.extend(graph.updates)
bpy.app.handlers.depsgraph_update_post.append(handler)
socket=node.inputs[1];ratios=(.8,.9,1,1.1,1.13,1.5,2,2.37);rasters=((1920,1080),(1920,1200),(3840,2160),(2716,1528))
values=[v for r in ratios for x,y in rasters for v in (r,r*x/y,.5-r/100)]
for value in values:
    socket.default_value=value;c.view_layer.update();updates.clear()
    for _ in range(3):
        reverse_mapping.set_input(socket,value);c.view_layer.update()
    assert not updates,f'{value!r} rewrote an unchanged input'
    assert abs(socket.default_value-value)<1e-6*max(1,abs(value))
# Small real changes still land.
socket.default_value=1;c.view_layer.update();updates.clear()
reverse_mapping.set_input(socket,1.001);c.view_layer.update()
assert updates and abs(socket.default_value-1.001)<1e-6,'real change was dropped'
bpy.app.handlers.depsgraph_update_post.remove(handler)
print(f'REVERSE WRITES PASS: {len(values)} unchanged values caused no updates; real changes apply')
addon.unregister()
