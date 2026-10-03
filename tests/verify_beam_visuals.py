"""Standalone Beam GPU acceptance and native file-browser filename checks."""
import bpy,sys,traceback,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));(root/'work').mkdir(exist_ok=True)
import projection_study as addon
from projection_study import runtime,study_views,blend_groups,presentation,export_json
bpy.context.preferences.view.show_splash=False
state={}
def fail():
    (root/'work/beam-visual-result.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);bpy.ops.wm.quit_blender()
def setup():
    try:
        scene=bpy.data.scenes.new('Beam Blend Acceptance');bpy.context.window.scene=scene;addon.register()
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
        state.update(area=area,region=region)
        with bpy.context.temp_override(area=area,region=region):
            mesh=bpy.data.meshes.new('Venue wall');mesh.from_pydata([(-8,10,-7),(40,10,-7),(40,10,7),(-8,10,7)],[],[(0,1,2,3)])
            wall=bpy.data.objects.new('Venue wall',mesh);scene.collection.objects.link(wall)
            bpy.ops.ps.add();anchor=bpy.context.object;anchor.ps.output_mode='COLOR_GRID';anchor.ps.resolution_x=1920;anchor.ps.resolution_y=1080
            bpy.context.view_layer.update();runtime.refresh(True)
            bpy.ops.beam.create_group(layout_type='HORIZONTAL',count=4,overlap=20,input_mode='PERCENT')
            state['group']=blend_groups.active_group(bpy.context)
            s=scene.ps_study;s.project_name='Melbourne Town Hall';s.venue='Main Hall';s.revision='R02';s.client='Example Client';s.author='Twisted Pixel'
            space=area.spaces.active;space.region_3d.view_location=(12,9,0)
            space.region_3d.view_rotation=(Vector((12,9,0))-Vector((35,-35,20))).to_track_quat('-Z','Y')
            space.region_3d.view_distance=50;space.region_3d.view_perspective='PERSP';space.show_region_ui=False
            space.region_3d.update();bpy.ops.beam.presentation()
            area.tag_redraw()
            bpy.ops.ps.capture_current(filepath=str(root/'work/beam-presentation-current.png'))
        bpy.app.timers.register(export,first_interval=1.0)
    except Exception:fail()
def export():
    try:
        area=state['area'];region=state['region'];group=state['group']
        with bpy.context.temp_override(area=area,region=region):
            assert (root/'work/beam-presentation-current.png').exists()
            view=study_views.create_view(bpy.context,'Blend Overview');view.resolution_x=1600;view.resolution_y=900;state['view']=view
            scene=bpy.context.scene;scene.ps_study.show_frustums=False;scene.ps_study.show_centre_rays=False
            study_views.export_view(bpy.context,view,root/'work/beam-individual.png')
            group.combined=True;group.show_overlap=False;scene.ps_study.show_labels=False
            study_views.export_view(bpy.context,view,root/'work/beam-combined-hard.png')
            group.preview_edge_blend=True
            study_views.export_view(bpy.context,view,root/'work/beam-combined-feather.png')
            assert (root/'work/beam-combined-hard.png').read_bytes()!=(root/'work/beam-combined-feather.png').read_bytes()
            assert (root/'work/beam-individual.png').read_bytes()!=(root/'work/beam-combined-feather.png').read_bytes()
            (root/'work/beam-example.json').write_text(json.dumps(export_json.document(bpy.context),indent=2))
            bpy.ops.ps.export(filepath=str(root/'work/Beam_projectors.csv'))
            bpy.data.libraries.write(str(root/'work/beam-blend-acceptance.blend'),{scene})
            # Normal invoke must put a proposed, editable name in the real browser.
            assert bpy.ops.ps.export_views('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        bpy.app.timers.register(check_dialog,first_interval=.6)
    except Exception:fail()
def check_dialog():
    try:
        browsers=[(w,a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type=='FILE_BROWSER']
        assert browsers,'File browser did not open'
        window,area=browsers[0];params=area.spaces.active.params
        assert params.filename=='Melbourne_Town_Hall_R02_Blend_Overview.png',params.filename
        params.filename='User_Edited_View.png'
        assert params.filename=='User_Edited_View.png'
        with bpy.context.temp_override(window=window,area=area):bpy.ops.file.cancel()
        bpy.app.timers.register(current_dialog,first_interval=.3)
    except Exception:fail()
def current_dialog():
    try:
        with bpy.context.temp_override(area=state['area'],region=state['region']):
            assert bpy.ops.ps.capture_current('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        bpy.app.timers.register(check_current,first_interval=.6)
    except Exception:fail()
def check_current():
    try:
        window,area=next((w,a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type=='FILE_BROWSER')
        assert area.spaces.active.params.filename=='Melbourne_Town_Hall_R02_Current_View.png',area.spaces.active.params.filename
        with bpy.context.temp_override(window=window,area=area):bpy.ops.file.cancel()
        bpy.app.timers.register(batch_dialog,first_interval=.3)
    except Exception:fail()
def batch_dialog():
    try:
        with bpy.context.temp_override(area=state['area'],region=state['region']):
            assert bpy.ops.ps.export_views('INVOKE_DEFAULT',all_views=True)=={'RUNNING_MODAL'}
        bpy.app.timers.register(check_batch,first_interval=.6)
    except Exception:fail()
def check_batch():
    try:
        window,area=next((w,a) for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type=='FILE_BROWSER')
        operator=area.spaces.active.active_operator
        assert len(operator.proposed_files)==1
        assert operator.proposed_files[0].filename=='Melbourne_Town_Hall_R02_Blend_Overview.png'
        operator.proposed_files[0].filename='Edited_Batch.png'
        assert operator.proposed_files[0].filename=='Edited_Batch.png'
        with bpy.context.temp_override(window=window,area=area):bpy.ops.file.cancel()
        (root/'work/beam-visual-result.txt').write_text('PASS: GPU individual/combined/feather; metadata JSON/CSV; native selected/current/batch filename dialogs editable and cancellable')
        print('BEAM VISUAL AND FILE DIALOG ACCEPTANCE PASS',flush=True);bpy.ops.wm.quit_blender()
    except Exception:fail()
bpy.app.timers.register(setup,first_interval=2)
