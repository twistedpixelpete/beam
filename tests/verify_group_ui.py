"""Disposable foreground UI, native undo/redo and membership-panel smoke test."""
import bpy,sys,traceback
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,blend_groups,group_lifecycle
bpy.context.preferences.view.show_splash=False

class BEAM_PT_lifecycle_qa(bpy.types.Panel):
    bl_idname='BEAM_PT_lifecycle_qa';bl_label='Beam Lifecycle QA';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Item';bl_order=-100
    def draw(self,context):
        from projection_study.blend_ui import draw_groups
        draw_groups(self.layout,context)

def run():
    try:
        addon.register();bpy.utils.register_class(BEAM_PT_lifecycle_qa);scene=bpy.data.scenes.new('Beam Lifecycle UI');bpy.context.window.scene=scene
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            bpy.ops.ps.add();bpy.ops.beam.create_group(count=3,overlap=18,input_mode='PERCENT')
            g=scene.ps_study.blend_groups[0];g.members[2].projector.location.x=.15
            bpy.context.view_layer.update();runtime.refresh(True)
            bpy.ops.beam.group_action(action='SELECT')
            bpy.context.preferences.edit.use_global_undo=True
            bpy.ops.ed.undo_push(message='Beam group baseline')
            bpy.ops.object.duplicate('EXEC_DEFAULT',True)
            runtime.refresh(True);assert len(bpy.context.scene.ps_study.blend_groups)==2
            bpy.ops.ed.undo();runtime.refresh(True)
            assert len(bpy.context.scene.ps_study.blend_groups)==1,'Native undo left duplicate group'
            bpy.ops.ed.redo();runtime.refresh(True)
            assert len(bpy.context.scene.ps_study.blend_groups)==2,'Native redo failed group reconstruction'
            scene=bpy.context.scene
            mesh=bpy.data.meshes.new('Wall');mesh.from_pydata([(-10,10,-6),(30,10,-6),(30,10,6),(-10,10,6)],[],[(0,1,2,3)])
            wall=bpy.data.objects.new('Wall',mesh);scene.collection.objects.link(wall)
            g=scene.ps_study.blend_groups[-1];g.controller.location.x+=3
            space=area.spaces.active;space.show_region_ui=True
            space.region_3d.view_location=(9,5,0);space.region_3d.view_distance=33
            space.region_3d.view_rotation=(Vector((9,5,0))-Vector((28,-25,18))).to_track_quat('-Z','Y');space.region_3d.view_perspective='PERSP';space.region_3d.update()
            ui=next(r for r in area.regions if r.type=='UI')

            runtime.refresh(True);area.tag_redraw()
            # Duplicate a selected hierarchy through the real modal drag path.
            for obj in bpy.context.selected_objects:obj.select_set(False)
            g.controller.select_set(True);bpy.context.view_layer.objects.active=g.controller
            for obj in g.controller.children_recursive:obj.select_set(True)
            assert bpy.ops.object.duplicate_move('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
            assert group_lifecycle.defer_native_copy(bpy.context)
            runtime.refresh(True);assert len(scene.ps_study.blend_groups)==2
            bpy.context.window.event_simulate(type='ESC',value='PRESS')
            bpy.context.window.event_simulate(type='ESC',value='RELEASE')
        bpy.app.timers.register(finish,first_interval=1)
    except Exception:fail()

def finish():
    try:
        runtime.refresh(True)
        assert len(bpy.context.scene.ps_study.blend_groups)==3
        assert sum(o.ps.is_projector for o in bpy.context.scene.objects)==9
        bpy.ops.screen.screenshot(filepath=str(root/'work/beam-lifecycle-ui.png'))
        (root/'work/group-ui-result.txt').write_text('PASS: native duplicate undo/redo and live group panel')
        print('GROUP UI / UNDO / REDO PASS',flush=True)
    except Exception:fail();return
    bpy.ops.wm.quit_blender()

def fail():
    message=traceback.format_exc();print(message,flush=True);(root/'work/group-ui-result.txt').write_text(message);bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=2)
