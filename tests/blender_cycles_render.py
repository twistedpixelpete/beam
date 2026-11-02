"""Rendered Cycles regression: raster alignment, image orientation and alpha holes."""
import bpy,sys,math,json,time
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/('work/issue-14/render-tests-'+'.'.join(map(str,bpy.app.version)));OUT.mkdir(parents=True,exist_ok=True)
import projection_study as addon
from projection_study import cycles_projection as cp, runtime
from projection_study.projector_object import create
addon.register()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16
s.cycles.pixel_filter_type='BOX';s.cycles.filter_width=.01
s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.seed=14
s.cycles.max_bounces=4;s.cycles.diffuse_bounces=0;s.cycles.glossy_bounces=0;s.cycles.transparent_max_bounces=8
s.render.resolution_x=384;s.render.resolution_y=256;s.render.resolution_percentage=100
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32'
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0
p=create(bpy.context);p.ps.show_body=False;p.ps.show_projected_identifier=False;p.ps.output_mode='SOLID';p.ps.colour=(1,1,1)
p.ps.resolution_x=192;p.ps.resolution_y=108

def material(name,colour):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
    d=n.new('ShaderNodeBsdfDiffuse');d.inputs['Color'].default_value=(*colour,1)
    o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(d.outputs[0],o.inputs['Surface']);return m

def plane(name,y,width,height,mat):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-width/2,y,-height/2),(width/2,y,-height/2),(width/2,y,height/2),(-width/2,y,height/2)],[],[(0,3,2,1)])
    uv=mesh.uv_layers.new();
    for i,coord in enumerate([(0,0),(0,1),(1,1),(1,0)]):uv.data[i].uv=coord
    o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);mesh.materials.append(mat);return o
wall=plane('Backdrop',8,20,12,material('White',(1,1,1)))
cam=bpy.data.objects.new('Test camera',bpy.data.cameras.new('Test camera'));s.collection.objects.link(cam)
cam.location=(0,-2,0);cam.rotation_euler=(math.pi/2,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=12;s.camera=cam
s.ps_study.projection_mode='CYCLES'

def render(name):
    bpy.context.view_layer.update()  # render_pre must synchronize without timer/manual sync.
    s.render.filepath=str(OUT/(name+'.exr'));start=time.perf_counter();bpy.ops.render.render(write_still=True)
    image=bpy.data.images.load(s.render.filepath,check_existing=False)
    values=np.empty(len(image.pixels),np.float32);image.pixels.foreach_get(values)
    result=values.reshape(s.render.resolution_y,s.render.resolution_x,4).copy();bpy.data.images.remove(image)
    # PNG is only a visual preview; assertions use scene-linear EXR values.
    preview=bpy.data.images.load(s.render.filepath,check_existing=False)
    s.render.image_settings.file_format='PNG';preview.save_render(str(OUT/(name+'.png')),scene=s);bpy.data.images.remove(preview)
    s.render.image_settings.file_format='OPEN_EXR'
    return result,time.perf_counter()-start

results={}
a,t=render('solid');results['solid_seconds']=t
mask=a[:,:,:3].max(2)>.001
ys,xs=np.where(mask)
# Orthographic 12 m width, raster width 8 m, height 4.5 m.
assert abs(xs.min()-64)<=1 and abs(xs.max()-319)<=1,(xs.min(),xs.max())
assert abs(ys.min()-56)<=1 and abs(ys.max()-199)<=1,(ys.min(),ys.max())
results['solid_bounds']=[int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())]
p.ps.shift_h=20;p.ps.shift_v=-10
shift,t=render('shift');mask=shift[:,:,:3].max(2)>.001;ys,xs=np.where(mask)
assert abs(xs.min()-(64+51.2))<=1.34 and abs(ys.min()-(56-14.4))<=1.34,(xs.min(),ys.min())
results['shift_bounds']=[int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())]
p.ps.shift_h=0;p.ps.shift_v=0
# Marked image verifies orientation: lower left red, lower right green,
# upper left blue, upper right white.
image=bpy.data.images.new('Corners',width=32,height=32,float_buffer=True)
pixels=np.ones((32,32,4),np.float32);pixels[:16,:16,:3]=(1,0,0);pixels[:16,16:,:3]=(0,1,0);pixels[16:,:16,:3]=(0,0,1)
image.pixels.foreach_set(pixels.ravel());image.pack();p.ps.image=image;p.ps.output_mode='IMAGE'
colour,t=render('corners')
for y,x,channel in [(90,120,0),(90,260,1),(170,120,2)]:
    rgb=colour[y,x,:3];assert rgb[channel]>.01 and rgb[channel]>10*max(rgb[(channel+1)%3],rgb[(channel+2)%3]),(y,x,rgb)
results['orientation']='PASS'
# Moving/rotating the entire rig must not change its raster orientation.
original=[(obj,obj.matrix_world.copy()) for obj in (p,wall,cam)]
transform=Matrix.Translation((3,-2,1)) @ Matrix.Rotation(.73,4,'Z') @ Matrix.Rotation(.3,4,'X')
for obj,world in original:obj.matrix_world=transform@world
rotated,_=render('rotated')
assert np.allclose(rotated[80:180,90:290,:3],colour[80:180,90:290,:3],rtol=.02,atol=.003)
for obj,world in original:obj.matrix_world=world
# A scene expressed in centimetres must retain the same rendered brightness.
s.unit_settings.scale_length=.01
for obj in (p,wall,cam):obj.location*=100
wall.scale*=100;cam.data.ortho_scale*=100
units,_=render('centimetres')
assert np.allclose(units[90,260,:3],colour[90,260,:3],rtol=.02,atol=.001)
s.unit_settings.scale_length=1
for obj,world in original:obj.matrix_world=world
cam.data.ortho_scale/=100
results['rotation_and_units']='PASS'
# Native 1920 x 1080 raster with enough render pixels to resolve one source pixel.
p.ps.output_mode='SOLID';p.ps.resolution_x=1920;p.ps.resolution_y=1080
p.ps.shift_h=-13;p.ps.shift_v=17
s.render.resolution_x=3072;s.render.resolution_y=2048;s.cycles.samples=4
hd,_=render('full-hd-shift');ys,xs=np.where(hd[:,:,:3].max(2)>.001)
expected=(512-2048*.13,2559-2048*.13,448+1152*.17,1599+1152*.17)
actual=(xs.min(),xs.max(),ys.min(),ys.max())
assert max(abs(float(a)-b) for a,b in zip(actual,expected))<=2048/1920,(actual,expected)
results['full_hd_edge_error_projector_pixels']=max(abs(float(a)-b) for a,b in zip(actual,expected))*1920/2048
s.render.resolution_x=384;s.render.resolution_y=256;s.cycles.samples=16
p.ps.resolution_x=192;p.ps.resolution_y=108;p.ps.shift_h=0;p.ps.shift_v=0;p.ps.output_mode='IMAGE'

# A UV mask with transparent right half on a black cut-out cloth.
m=material('Alpha cloth',(0,0,0));n=m.node_tree.nodes;links=m.node_tree.links
mask_image=bpy.data.images.new('Cloth alpha',width=16,height=16,float_buffer=True)
mask_pixels=np.ones((16,16,4),np.float32);mask_pixels[:,8:,3]=0;mask_image.pixels.foreach_set(mask_pixels.ravel());mask_image.pack()
tex=n.new('ShaderNodeTexImage');tex.image=mask_image;tex.interpolation='Closest'
cut=n.new('ShaderNodeMath');cut.operation='SUBTRACT';cut.inputs[0].default_value=1;links.new(tex.outputs['Alpha'],cut.inputs[1])
transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');links.new(cut.outputs[0],mix.inputs[0]);links.new(n.get('Diffuse BSDF').outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],n.get('Material Output').inputs[0])
cloth=plane('Cut-out cloth',4,12,8,m)
alpha,t=render('alpha-cloth')
assert alpha[90,120,:3].max()<.001,alpha[90,120]
assert np.allclose(alpha[90,260,:3],colour[90,260,:3],rtol=.08,atol=.001),(alpha[90,260],colour[90,260])
results['alpha_pass_through']='PASS'
# Opaque cloth also receives the projector image, at the nearer throw distance.
n.get('Diffuse BSDF').inputs['Color'].default_value=(1,1,1,1)
opaque,_=render('white-cloth')
assert opaque[110,160,0]>.01 and opaque[110,160,0]>10*opaque[110,160,1]
# Fractional transmission: light and camera each traverse the black cloth.
n.get('Diffuse BSDF').inputs['Color'].default_value=(0,0,0,1)
mask_pixels[:,:,:3]=1;mask_pixels[:,:,3]=.5;mask_image.pixels.foreach_set(mask_pixels.ravel());mask_image.update()
fraction,_=render('half-transparent')
ratio=fraction[80:180,220:280,1].mean()/colour[80:180,220:280,1].mean()
assert .18<ratio<.32,ratio
results['fractional_transmission_ratio']=float(ratio)
extra=cloth.copy();extra.data=cloth.data.copy();s.collection.objects.link(extra);extra.location.y=1
layered,_=render('two-transparent-layers')
layer_ratio=layered[80:180,220:280,1].mean()/colour[80:180,220:280,1].mean()
assert .04<layer_ratio<.09,layer_ratio
results['two_layer_transmission_ratio']=float(layer_ratio)
bpy.data.objects.remove(extra,do_unlink=True)

# Restore binary alpha for the saved example and engineering check.
mask_pixels[:,:,3]=1;mask_pixels[:,8:,3]=0;mask_image.pixels.foreach_set(mask_pixels.ravel());mask_image.update()
n.get('Diffuse BSDF').inputs['Color'].default_value=(1,1,1,1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Beam-Cycles-Alpha-Test.blend'))

# Engineering target remains the cloth, independent of rendered transparency.
bpy.context.view_layer.update();runtime.refresh(True);assert p.ps.target==cloth

# All generated content modes produce usable light; missing images emit nothing.
cloth.hide_render=True
for mode in ('GRID','CHECKER','ID','UV_GRID','COLOR_GRID'):
    p.ps.output_mode=mode;p.ps.show_projected_identifier=True
    mode_pixels,_=render('mode-'+mode.lower())
    assert mode_pixels[:,:,:3].max()>.005,mode
p.ps.output_mode='IMAGE';p.ps.image=None
missing,_=render('missing-image');assert missing[:,:,:3].max()<1e-6
p.ps.image=image;p.ps.output_mode='SOLID';p.ps.colour=(1,1,1);p.ps.show_projected_identifier=False
# Combined canvas binds the actual anchor, even when it is not member zero.
from projection_study import blend_groups
second=create(bpy.context,source=p);second.ps.image=image;second.ps.output_mode='IMAGE'
second.location.x=6.4
bpy.context.view_layer.update();runtime.refresh(True)
group=blend_groups.create(bpy.context,[p,second],'HORIZONTAL',2,1,20,'PERCENT',preserve=True)
group.anchor_uuid=second.ps.uuid;group.combined=True;group.preview_edge_blend=True
cp.sync(s)
for member in (p,second):
    helper=next(o for o in s.objects if o.get(cp.TAG) and o.parent==member)
    source,feather,canvas,combined=cp.content(member)
    assert source==second and helper.data.node_tree.nodes['Content'].image==image
    values=[socket.default_value for socket in helper.data.node_tree.nodes['Raster'].inputs]
    assert np.allclose(values[4:8],feather) and np.allclose(values[8:12],canvas)
blend,_=render('combined-blend');assert blend[:,:,:3].max()>.005
results['all_modes_and_blend']='PASS'

s.ps_study.projection_mode='PLANNING';assert not any(o.get(cp.TAG) for o in bpy.data.objects)
assert not any(g.get(cp.TAG) for g in bpy.data.node_groups)
results['cleanup']='PASS';results['blender']=bpy.app.version_string
(OUT/'results.json').write_text(json.dumps(results,indent=2));print('CYCLES RENDER PASS',json.dumps(results))
addon.unregister()
