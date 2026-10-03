"""Run only in a disposable Blender process; the script exits Blender on completion."""
import bpy,sys,traceback,json
from pathlib import Path
from mathutils import Vector
bpy.context.preferences.view.show_splash=False
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
for name in ('current-view.png','saved-view.png','saved-view-clean.png','ui-result.txt'):
    (root/'work'/name).unlink(missing_ok=True)
import projection_study as addon

def fail():
    (root/'work/ui-result.txt').write_text(traceback.format_exc())
    print(traceback.format_exc(),flush=True)
    bpy.ops.wm.quit_blender()

def setup():
    try:
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            for n in (4,8,10,12,13):
                scene=bpy.data.scenes.new('UI test')
                bpy.context.window.scene=scene; addon.register()
                path=root/'tests'/f'blender_m{n}.py'
                exec(compile(path.read_text(),str(path),'exec'),{'root':root})
                addon.unregister()
                for obj in list(scene.objects): bpy.data.objects.remove(obj,do_unlink=True)
            scene=bpy.data.scenes.new('Projection Study 0.2 QA')
            bpy.context.window.scene=scene; addon.register()
            mesh=bpy.data.meshes.new('Wall')
            mesh.from_pydata([(-14,10,-5),(14,10,-5),(14,10,8),(-14,10,8)],[],[(0,1,2,3)])
            wall=bpy.data.objects.new('Screen',mesh); scene.collection.objects.link(wall)
            bpy.ops.ps.add(); a=bpy.context.object; a.location=(-3,0,1)
            bpy.ops.ps.add(); b=bpy.context.object; b.location=(3,0,1); b.ps.throw_ratio=1.2
            bpy.context.view_layer.update(); addon.runtime.refresh(True)
            space=area.spaces.active
            space.region_3d.view_location=(0,5,1)
            space.region_3d.view_rotation=(Vector((0,5,1))-Vector((13,-18,12))).to_track_quat('-Z','Y')
            space.region_3d.view_distance=25; space.region_3d.view_perspective='PERSP'
            space.shading.color_type='MATERIAL'; space.show_region_ui=False
            area.tag_redraw()
        bpy.app.timers.register(exports,first_interval=1)
    except Exception: fail()
    return None

def exports():
    try:
        from projection_study import study_views,export_json
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            v=study_views.create_view(bpy.context,'Overview')
            v.resolution_x=1200; v.resolution_y=800
            study_views.export_view(bpy.context,v,root/'work/saved-view.png')
            v.include_labels=False; v.include_frustums=False; v.include_grids=False
            study_views.export_view(bpy.context,v,root/'work/saved-view-clean.png')
            v.include_labels=True; v.include_frustums=True; v.include_grids=True
            (root/'work/example-study.json').write_text(json.dumps(export_json.document(bpy.context),indent=2))
            space=area.spaces.active; space.show_region_ui=True
            next(r for r in area.regions if r.type=='UI').active_panel_category='Beam'
            wall=bpy.context.scene.objects['Screen']
            for obj in bpy.context.selected_objects: obj.select_set(False)
            wall.select_set(True); bpy.context.view_layer.objects.active=wall
            addon.runtime.refresh()
            assert bpy.context.scene.ps_study.active_projector.ps.identifier=='PJ02'
            bpy.ops.ps.capture_current(filepath=str(root/'work/current-view.png'))
        bpy.app.timers.register(finish,first_interval=2)
    except Exception: fail()
    return None

def finish():
    try:
        assert (root/'work/current-view.png').exists(),'Current capture did not complete'
        from projection_study import export_json
        (root/'work/example-study.json').write_text(json.dumps(export_json.document(bpy.context),indent=2))
        (root/'work/ui-result.txt').write_text('PASS: GPU tests, camera restoration, saved camera PNG export, per-view toggles, JSON and composited current-view capture')
        print('UI EXPORT QA PASS',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception: fail()
    return None

bpy.app.timers.register(setup,first_interval=2)
