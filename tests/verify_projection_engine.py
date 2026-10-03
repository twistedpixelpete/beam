"""Standalone UI/GPU acceptance process; closes only its own Blender process."""
import bpy,sys,traceback,json,struct,zlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root)); (root/'work').mkdir(exist_ok=True)
bpy.context.preferences.view.show_splash=False
import projection_study as addon


def run():
    try:
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        scene=bpy.data.scenes.new('Multi-surface Projection Acceptance')
        bpy.context.window.scene=scene; addon.register()
        with bpy.context.temp_override(area=area,region=region):
            scope={'root':root}
            path=root/'tests/blender_m11.py'
            exec(compile(path.read_text(),str(path),'exec'),scope)
            space=area.spaces.active
            space.region_3d.view_location=(0,10,0)
            space.region_3d.view_rotation=(Vector((0,10,0))-Vector((18,-6,9))).to_track_quat('-Z','Y')
            space.region_3d.view_distance=25; space.region_3d.view_perspective='PERSP'
            space.shading.color_type='MATERIAL'; space.show_region_ui=False
            space.region_3d.update(); area.tag_redraw()
        bpy.app.timers.register(export,first_interval=.5)
    except Exception:
        (root/'work/projection-engine-result.txt').write_text(traceback.format_exc())
        print(traceback.format_exc(),flush=True); bpy.ops.wm.quit_blender()
    return None


def export():
    try:
        from projection_study import study_views,export_json
        scene=bpy.context.scene
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            view=study_views.create_view(bpy.context,'Multi-surface overview')
            view.resolution_x=1600; view.resolution_y=1000
            view.include_frustums=False
            projector=next(o for o in scene.objects if o.ps.is_projector)
            # A known image also exercises the custom-image sampler.
            image=bpy.data.images.new('Acceptance custom image',width=64,height=36)
            image.pixels=[component for y in range(36) for x in range(64) for component in (x/63,y/35,.2,1)]
            projector.ps.image=image
            for mode in ('GRID','UV_GRID','COLOR_GRID','SOLID','CHECKER','ID','IMAGE'):
                projector.ps.output_mode=mode; addon.runtime.refresh()
                study_views.export_view(bpy.context,view,root/'work'/f'acceptance-{mode.lower()}.png')
            scene.ps_study.show_labels=False; scene.ps_study.show_outputs=False
            study_views.export_view(bpy.context,view,root/'work/acceptance-global-hidden.png')
            scene.ps_study.show_labels=True; scene.ps_study.show_outputs=True
            view.include_grids=False; view.include_labels=False
            study_views.export_view(bpy.context,view,root/'work/acceptance-clean.png')
            view.include_grids=True; view.include_labels=True
            # Verify actual surface-shader output against the same clean view.
            def png(name):
                data=(root/'work'/name).read_bytes(); pos=8; chunks=[]
                while pos<len(data):
                    size=struct.unpack('!I',data[pos:pos+4])[0]
                    if data[pos+4:pos+8]==b'IDAT': chunks.append(data[pos+8:pos+8+size])
                    pos+=size+12
                return zlib.decompress(b''.join(chunks))
            base=png('acceptance-clean.png'); solid=png('acceptance-solid.png')
            assert png('acceptance-global-hidden.png')==base, 'Global labels/output toggles must suppress surface output'
            matrix=view.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1600,y=1000)@view.camera.matrix_world.inverted()
            def difference(point):
                q=matrix@Vector((*point,1)); x=round((q.x/q.w+1)*800); y=999-round((q.y/q.w+1)*500)
                offsets=[yy*(1600*4+1)+1+xx*4+c for yy in range(y-1,y+2) for xx in range(x-1,x+2) for c in range(3)]
                return sum(abs(solid[i]-base[i]) for i in offsets)/len(offsets)
            assert difference((0,10,0))>8, 'Foreground must receive solid output'
            assert difference((5,15,0))>8, 'Unblocked rear wall must receive output'
            assert difference((0,15,0))<3, 'Blocked rear wall must remain unprojected'
            # Projected names are independent of body/distance annotations.
            projector.ps.output_mode='ID'; view.include_labels=False
            def capture_name(name):
                study_views.export_view(bpy.context,view,root/'work'/name)
                return png(name)
            names=capture_name('acceptance-name-only.png')
            assert names!=base
            projector.ps.show_identifier=False; scene.ps_study.show_labels=False
            assert capture_name('acceptance-name-with-labels-hidden.png')==names
            projector.ps.show_projected_identifier=False
            assert capture_name('acceptance-name-hidden.png')==base
            projector.ps.show_projected_identifier=True
            view.include_projected_identifiers=False
            assert capture_name('acceptance-view-name-hidden.png')==base
            view.include_projected_identifiers=True
            scene.ps_study.show_projected_identifiers=False
            assert capture_name('acceptance-global-name-hidden.png')==base
            scene.ps_study.show_projected_identifiers=True
            projector.ps.show_identifier=True; scene.ps_study.show_labels=True; view.include_labels=True
            projector.ps.output_mode='GRID'
            scene.objects['Foreground'].location.x=4
            bpy.context.view_layer.update(); addon.runtime.refresh()
            assert projector.ps.target.name=='Rear Wall'
            study_views.export_view(bpy.context,view,root/'work/acceptance-moved.png')
            scene.objects['Foreground'].location.x=0
            bpy.context.view_layer.update(); addon.runtime.refresh()
            (root/'work/acceptance-study.json').write_text(json.dumps(export_json.document(bpy.context),indent=2))
            bpy.data.libraries.write(str(root/'work/projection-acceptance.blend'),{scene})
        (root/'work/projection-engine-result.txt').write_text('PASS: automatic targets, GPU shadow depths, UV Grid, side receivers without centre hit; exported acceptance images')
        print('PROJECTION ENGINE ACCEPTANCE PASS',flush=True)
    except Exception:
        (root/'work/projection-engine-result.txt').write_text(traceback.format_exc())
        print(traceback.format_exc(),flush=True)
    bpy.ops.wm.quit_blender()
    return None

bpy.app.timers.register(run,first_interval=2)
