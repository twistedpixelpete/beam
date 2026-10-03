"""Disposable UI/export inspection and presentation-only invariants."""
import bpy,sys,json,traceback
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,study_views,export_json,presentation,viewport_display,typography
bpy.context.preferences.view.show_splash=False
out=root/'examples/0.7';out.mkdir(exist_ok=True)
state={}
def fail():
    text=traceback.format_exc();print(text,flush=True);(root/'work/beauty-result.txt').write_text(text);bpy.ops.wm.quit_blender()
def setup():
    try:
        addon.register();scene=bpy.data.scenes.new('Beam Beauty');bpy.context.window.scene=scene
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');state.update(area=area,region=region)
        with bpy.context.temp_override(area=area,region=region):
            mesh=bpy.data.meshes.new('Screen');mesh.from_pydata([(-8,10,-5),(20,10,-5),(20,10,5),(-8,10,5)],[],[(0,1,2,3)])
            wall=bpy.data.objects.new('Screen',mesh);scene.collection.objects.link(wall)
            bpy.ops.ps.add();bpy.ops.beam.create_group(count=2,overlap=20,input_mode='PERCENT')
            scene.ps_study.display_units='m'
            space=area.spaces.active;space.show_region_ui=True;space.shading.color_type='SINGLE';space.shading.single_color=(.35,.37,.4)
            space.region_3d.view_location=(4,7,0);space.region_3d.view_rotation=(Vector((4,7,0))-Vector((19,-23,14))).to_track_quat('-Z','Y');space.region_3d.view_distance=31;space.region_3d.view_perspective='PERSP';space.region_3d.update()
            runtime.refresh(True);area.tag_redraw()
        bpy.app.timers.register(focus_beam,first_interval=.3)
    except Exception:fail()
def focus_beam():
    try:
        ui=next(r for r in state['area'].regions if r.type=='UI')
        if ui.active_panel_category=='Beam' and ui.width>200:
            state['area'].spaces.active.show_region_ui=True
            state['area'].tag_redraw()
            bpy.app.timers.register(capture,first_interval=.7);return None
        step=state.get('tab_step',0)
        if step>45:
            bpy.ops.screen.screenshot(filepath=str(root/'work/beauty-focus.png'))
            raise AssertionError('Could not select Beam sidebar tab')

        state['tab_step']=step+1
        x=ui.x+ui.width-28;y=ui.y+ui.height-20-step*16
        bpy.context.window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
        bpy.context.window.event_simulate(type='LEFTMOUSE',value='PRESS',x=x,y=y)
        bpy.context.window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=x,y=y)
        return .08
    except Exception:fail();return None

def capture():
    try:
        area=state['area'];region=state['region'];settings=bpy.context.scene.ps_study
        with bpy.context.temp_override(area=area,region=region):
            bpy.ops.screen.screenshot(filepath=str(out/'sidebar.png'))
            view=study_views.create_view(bpy.context,'Beauty comparison');view.resolution_x=1600;view.resolution_y=1000
            view.include_frustums=True;view.include_labels=True;view.include_grids=True
            def technical():
                d=export_json.document(bpy.context);d.pop('exported_at');return d
            # Counting the annotation calls verifies Off keeps IDs and Minimal excludes throw/blend labels.
            original_label,original_annotation=typography.label,typography.annotation
            try:
                for mode,count in [('OFF',0),('MINIMAL',4),('FULL',6)]:
                    settings.label_detail=mode;calls=[];ids=[]
                    typography.annotation=lambda text,*args,**kwargs:calls.append(text)
                    typography.label=lambda text,*args,**kwargs:ids.append(text)
                    viewport_display.draw_labels(area.spaces.active.region_3d.perspective_matrix,1600,1000)
                    assert len(calls)==count,(mode,calls)
                    assert 'PJ01' in ids and 'PJ02' in ids
            finally:typography.label,typography.annotation=original_label,original_annotation
            baseline=technical()
            for mode in ('OFF','MINIMAL','FULL'):
                settings.label_detail=mode
                assert technical()==baseline,'Label detail changed technical export'
                study_views.export_view(bpy.context,view,out/f'labels-{mode.lower()}.png')
                baseline=technical() # Export timestamps/filenames legitimately update independently.
            assert (out/'labels-minimal.png').read_bytes()!=(out/'labels-full.png').read_bytes()
            assert (out/'labels-off.png').read_bytes()!=(out/'labels-minimal.png').read_bytes()
            settings.label_detail='FULL';materials=[(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials]
            before=technical();bpy.ops.beam.presentation();assert settings.label_detail=='MINIMAL'
            assert technical()==before,'Presentation changed technical export'
            assert materials==[(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials]
            # Use the live presentation camera styling to make a client-facing example.
            presentation_view=study_views.create_view(bpy.context,'Presentation');presentation_view.resolution_x=1600;presentation_view.resolution_y=1000
            study_views.export_view(bpy.context,presentation_view,out/'presentation.png')
            presentation.before_save();assert settings.label_detail=='FULL';presentation.after_save();assert settings.label_detail=='MINIMAL'
            bpy.ops.beam.presentation();assert settings.label_detail=='FULL'
            settings.label_detail='MINIMAL'
        (root/'work/beauty-result.txt').write_text('PASS: sidebar, Off/Minimal/Full annotations, ID retention, technical JSON equality, presentation/save restoration and unchanged materials')
        print('BEAUTY ACCEPTANCE PASS',flush=True)
    except Exception:fail();return
    bpy.ops.wm.quit_blender()
bpy.app.timers.register(setup,first_interval=2)
