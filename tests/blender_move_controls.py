"""Position fields, helper redirect and inspector layout. Background, no GPU."""
import bpy,math,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import blend_groups,projector_object,runtime,study_data,transform_conversion,ui
from mathutils import Vector
addon.register();c=bpy.context;s=c.scene
mesh=bpy.data.meshes.new('Wall');mesh.from_pydata([(-20,10,0),(20,10,0),(20,10,20),(-20,10,20)],[],[(0,1,2,3)]);mesh.update()
wall=bpy.data.objects.new('Wall',mesh);s.collection.objects.link(wall)
a=projector_object.create(c);b=projector_object.create(c);free=projector_object.create(c)
a.location=(-3,0,5);b.location=(3,0,5);free.location=(0,0,5);c.view_layer.update();runtime.refresh(True)
group=blend_groups.create(c,[a,b],'HORIZONTAL',2,1,200,'PIXELS',preserve=True);c.view_layer.update();runtime.refresh(True)

# Position is world space, for free and parented objects, in any scene unit.
free.beam_transform.position=(1,2,3);c.view_layer.update()
assert (free.matrix_world.translation-Vector((1,2,3))).length<1e-5
before=a.matrix_world.translation.copy();a.beam_transform.position=before+Vector((.25,-.5,1));c.view_layer.update()
assert (a.matrix_world.translation-before-Vector((.25,-.5,1))).length<1e-4,'member world position'
assert (b.matrix_world.translation-Vector((3,0,5))).length<1e-3,'other member stayed put'
assert runtime.rigid(a),'position keeps the transform rigid'

# A position edit reaches the projector cache.
c.view_layer.update();runtime.refresh(True);assert (runtime.CACHE[a.as_pointer()]['origin']-a.matrix_world.translation).length<1e-5

# Pitch, yaw and roll round-trip and agree with the CSV export values.
for pitch,yaw,roll in ((0,0,0),(11,0,0),(0,23,0),(0,0,17),(11,23,17),(-30,140,-8)):
    free.beam_transform.orientation=[math.radians(v) for v in (pitch,yaw,roll)];c.view_layer.update()
    got=transform_conversion.orientation_degrees(free.matrix_world.to_quaternion().to_matrix())
    assert all(abs(x-y)<1e-3 for x,y in zip(got,(pitch,yaw,roll))),((pitch,yaw,roll),got)
    assert all(abs(math.degrees(x)-y)<1e-3 for x,y in zip(free.beam_transform.orientation,(pitch,yaw,roll)))
    assert runtime.rigid(free)
free.beam_transform.orientation=(0,0,0);c.view_layer.update()
forward=free.matrix_world.to_3x3()@Vector((0,0,-1));assert (forward-Vector((0,1,0))).length<1e-5,'neutral faces +Y'

# The generic rotation keeps scale; a position edit keeps rotation.
wall.scale=(2,1,1);c.view_layer.update()
wall.beam_transform.rotation=(0,0,math.radians(30));c.view_layer.update()
assert abs(wall.matrix_world.to_scale().x-2)<1e-5 and abs(wall.matrix_world.to_euler().z-math.radians(30))<1e-5
rotation=wall.matrix_world.to_quaternion().copy();wall.beam_transform.position=(0,1,0);c.view_layer.update()
assert wall.matrix_world.to_quaternion().rotation_difference(rotation).angle<1e-5
wall.scale=(1,1,1);wall.rotation_euler=(0,0,0);wall.location=(0,0,0);c.view_layer.update()

# Locks hold.
free.lock_location=(True,)*3;held=free.matrix_world.translation.copy();free.beam_transform.position=(9,9,9);c.view_layer.update()
assert (free.matrix_world.translation-held).length<1e-6,'locked position moved';free.lock_location=(False,)*3
free.lock_rotation=(True,)*3;held=free.matrix_world.to_quaternion().copy();free.beam_transform.orientation=(1,1,1);c.view_layer.update()
assert free.matrix_world.to_quaternion().rotation_difference(held).angle<1e-5,'locked rotation moved';free.lock_rotation=(False,)*3

# Clicking a helper selects its projector once, and leaves the helper active so Outliner arrow keys can move on.
for item in c.selected_objects:item.select_set(False)
optics=runtime.optics(free);c.view_layer.objects.active=optics;study_data.sync_selection(c)
assert free.select_get() and c.view_layer.objects.active==optics and s.ps_study.active_projector==free
free.select_set(False);study_data.sync_selection(c);assert not free.select_get(),'deselecting must stick'
c.view_layer.objects.active=wall;study_data.sync_selection(c)
# ...but not when the projector can't take the selection.
free.hide_set(True);c.view_layer.objects.active=optics;study_data.sync_selection(c);assert not free.select_get();free.hide_set(False)
c.view_layer.objects.active=wall;study_data.sync_selection(c)

# Select Whole Group targets the controller.
assert bpy.ops.beam.select_group(group_uuid=group.uuid)=={'FINISHED'}
assert c.view_layer.objects.active==group.controller and s.ps_study.inspector=='GROUP'

# Inspector order, drawn against a recording layout.
class Layout:
    def __init__(self,log):self.__dict__['log']=log
    def __setattr__(self,k,v):pass
    def __getattr__(self,name):
        return self._call(name)
    def _call(self,name):
        def call(*args,**kw):
            if name=='prop':self.log.append(('prop',args[1],kw.get('text')))
            elif name=='operator':self.log.append(('operator',args[0],kw.get('text')))
            elif name=='label':self.log.append(('label',kw.get('text')))
            elif name=='panel':
                self.log.append(('panel',args[0]));return Layout(self.log),Layout(self.log)
            return Layout(self.log)
        return call
log=[];ui.projector(Layout(log),c)
panels=[e[1] for e in log if e[0]=='panel']
assert panels.index('beam_position_aim')<panels.index('beam_projection'),panels
props=[e[1] for e in log if e[0]=='prop'];assert 'position' in props and 'orientation' in props
s.ps_study.active_projector=a;log=[];ui.projector(Layout(log),c)
assert ('operator','beam.select_group','Select Whole Group') in log,'member offers whole-group selection'
print('MOVE CONTROLS PASS: world fields on free and parented objects, CSV-matching pitch/yaw/roll, locks, helper redirect, whole-group selection, inspector order')
addon.unregister()
