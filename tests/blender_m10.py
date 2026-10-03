exec((root/'tests/blender_m3.py').read_text())
from projection_study import study_views,export_json
from projection_study.interchange import image_filename
import tempfile,struct
from pathlib import Path
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=area,region=region):
    source=area.spaces.active.region_3d.window_matrix.copy()
    view=study_views.create_view(bpy.context,'Overview')
    bpy.context.view_layer.update()
    camera_matrix=view.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=region.width,y=region.height)
    for i,j in ((0,0),(1,1),(0,2),(1,2)):
        assert abs(source[i][j]-camera_matrix[i][j])<1e-4,(source,camera_matrix)
    second=study_views.create_view(bpy.context,'Overview')
    assert second.name=='Overview 02' and view.uuid!=second.uuid
    for v in (view,second): v.resolution_x=640; v.resolution_y=480
    with tempfile.TemporaryDirectory(dir=root/'work') as folder:
        assert bpy.ops.ps.export_views(directory=folder,all_views=True)=={'FINISHED'}
        from projection_study.study_views import proposed_names
        paths=[Path(folder)/proposed_names(bpy.context.scene)[v.uuid] for v in (view,second)]
        assert all(path.exists() for path in paths)
        assert struct.unpack('!II',paths[0].read_bytes()[16:24])==(640,480)
        before=paths[0].read_bytes()
        view.include_overlays=False
        study_views.export_view(bpy.context,view,paths[0],area)
        assert paths[0].read_bytes()!=before
        # Partial batch must not overwrite existing images without opt-in.
        try:
            result=bpy.ops.ps.export_views(directory=folder,all_views=True)
            assert result=={'CANCELLED'}
        except RuntimeError as exc:
            assert 'already exists' in str(exc)
    data=export_json.document(bpy.context)
    assert len(data['study_views'])==2
    assert data['study_views'][0]['exported_image_filename']
    rv=area.spaces.active.region_3d
    previous=rv.view_perspective
    try:
        rv.view_perspective='ORTHO'; rv.update()
        expected=rv.window_matrix.copy()
        ortho=study_views.create_view(bpy.context,'Front Elevation')
        bpy.context.view_layer.update()
        assert ortho.camera.data.type=='ORTHO'
        actual=ortho.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=region.width,y=region.height)
        for i,j in ((0,0),(1,1),(0,3),(1,3)):
            assert abs(expected[i][j]-actual[i][j])<1e-4
        ortho.resolution_x=640; ortho.resolution_y=480
        with tempfile.TemporaryDirectory(dir=root/'work') as folder:
            study_views.export_view(bpy.context,ortho,Path(folder)/'ortho.png',area)
    finally:
        rv.view_perspective=previous; rv.update()
    # Saved camera references and view identity survive a library round trip.
    scene=bpy.context.scene
    path=str(root/'work/study-views-roundtrip.blend')
    bpy.data.libraries.write(path,{scene})
    with bpy.data.libraries.load(path,link=False) as (src,dst): dst.scenes=[scene.name]
    loaded=dst.scenes[0]
    assert loaded.ps_study.views[0].uuid==view.uuid and loaded.ps_study.views[0].camera
    for item in list(loaded.objects): bpy.data.objects.remove(item,do_unlink=True)
    bpy.data.scenes.remove(loaded)
print('MILESTONE 10 camera framing / batch PNG / toggles / view persistence PASS')
