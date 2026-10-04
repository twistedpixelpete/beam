"""Screen Builder acceptance: geometry, UV, lifecycle, SI and export round trips.
Run in disposable Blender; run run() through MCP for live validation too.
"""
import sys,json,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import projection_study as addon
from projection_study import screen_objects as objects,screen_math,screen_uv,screen_surface,screen_patterns,screen_export,screen_data


def close(a,b,tol=1e-5):assert abs(a-b)<tol,(a,b)


def run(output=None):
    output=Path(output or ROOT/'work/screen-tests');output.mkdir(parents=True,exist_ok=True)
    if not hasattr(bpy.types.Object,'beam_screen'):addon.register()
    scene=bpy.data.scenes.new('Beam Screen Builder Validation');bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    p=scene.beam_screen_draft;created=[]
    def make(kind,name,**kwargs):
        # Reset parameters without losing installed RNA; each fixture is independent.
        for prop in p.bl_rna.properties:
            if prop.identifier!='rna_type' and not prop.is_readonly:p.property_unset(prop.identifier)
        p.screen_type=kind;p.name=name
        for k,v in kwargs.items():setattr(p,k,v)
        obj=objects.create(bpy.context,p);created.append(obj);return obj
    flat=make('FLAT','Flat Projection',width=6,height=3.375,segments=4,vertical_segments=2)
    assert flat.data.polygons[0].normal.y<-.99
    arc=make('ARC','90 Degree Arc',radius=10,angle=90,height=4,segments=64)
    m=json.loads(arc.beam_screen.metrics);close(m['length'],math.pi*5);close(m['chord'],math.sqrt(200))
    close((arc.data.vertices[64].co-arc.data.vertices[0].co).length,math.sqrt(200))
    uv=arc.data.uv_layers.active;close(uv.data[arc.data.polygons[32].loop_start].uv.x,.5)
    curve=bpy.data.curves.new('S path','CURVE');curve.dimensions='3D';curve.resolution_u=24
    spline=curve.splines.new('BEZIER');spline.bezier_points.add(3)
    for point,co in zip(spline.bezier_points,[(-6,0,0),(-2,2,0),(2,-2,0),(6,0,0)]):point.co=co;point.handle_left_type=point.handle_right_type='AUTO'
    source=bpy.data.objects.new('S Curve Source',curve);scene.collection.objects.link(source)
    curved=make('CURVE','S Curve',source=source,height=3,vertical_segments=2)
    closed=make('CLOSED','360 Cylinder',radius=3,angle=360,height=3,segments=96)
    assert len(closed.data.vertices)==192
    counts={}
    for f in closed.data.polygons:
        for e in f.edge_keys:counts[e]=counts.get(e,0)+1
    assert sum(v==1 for v in counts.values())==192 # top/bottom only, no vertical seam
    verts,faces,uvs=screen_math.strip([(-3+i,0,.1*math.sin(i)) for i in range(7)],3,3)
    mesh=objects.make_mesh('Uneven source',(verts,faces,uvs),1)
    for v in mesh.vertices:v.co.y=.25*math.sin(v.co.x)*math.sin(v.co.z)
    source_surface=bpy.data.objects.new('Uneven Source',mesh);scene.collection.objects.link(source_surface)
    before=[tuple(v.co) for v in mesh.vertices]
    surface=make('SURFACE','Mapped Surface',source=source_surface,uv_method='DISTANCE')
    assert before==[tuple(v.co) for v in mesh.vertices] and surface.data!=mesh
    led=make('FLAT','Flat LED',category='LED',columns=20,rows=8,show_detail=True)
    m=json.loads(led.beam_screen.metrics);close(m['width'],10);close(m['height'],4);assert (m['rx'],m['ry'])==(3840,1536);close(m['pitch_x'],2.6041666667)
    faceted=make('ARC','Faceted LED',category='LED',columns=20,rows=8,joint_angle=2.5,led_geometry='FACETED',show_detail=True)
    m=json.loads(faceted.beam_screen.metrics);close(m['angle'],47.5)
    for i,f in enumerate(faceted.data.polygons[:20]):
        pts=[faceted.data.vertices[k].co for k in f.vertices]
        close((pts[1]-pts[0]).length,.5);assert abs((pts[3]-pts[0]).dot((pts[1]-pts[0]).cross(pts[2]-pts[0])))<1e-6
        if i:close(math.degrees(f.normal.angle(faceted.data.polygons[i-1].normal)),2.5,2e-4)
    assert len(faceted.children)==1 and len(faceted.children[0].data.polygons)==20*8*5
    # Mapping checks on every generated type, not just successful creation.
    for obj in created:
        m=json.loads(obj.beam_screen.metrics);report=screen_uv.diagnose(obj.data,1,m['rx'],m['ry']);assert not report['errors'],(obj.name,report)
        screen_patterns.apply(obj)
    # Conform keeps source intact and preserves UVs, with evaluated production geometry.
    conform=make('FLAT','Conformed Display',width=5,height=2.5,segments=20,vertical_segments=10)
    conform.beam_screen.conform_target=source_surface;screen_surface.conform(bpy.context,conform);conform.beam_screen.built_signature=objects.signature(conform.beam_screen)
    assert before==[tuple(v.co) for v in mesh.vertices]
    # Update each parametric family and verify mesh datablock cleanup.
    for obj in created[:4]+[led,faceted]:
        old=obj.data.name;obj.beam_screen.height+=.1 if obj.beam_screen.category!='LED' else 0
        if obj.beam_screen.category=='LED':obj.beam_screen.rows+=1
        objects.update(bpy.context,obj);assert old not in bpy.data.meshes
    # Independent native linked duplicate identity repair.
    objects.select(bpy.context,arc);old_id=arc.beam_screen.identifier;old_uuid=arc.beam_screen.uuid
    bpy.ops.object.duplicate(linked=True);copy=bpy.context.object;objects.reconcile()
    assert copy.beam_screen.identifier!=old_id and copy.beam_screen.uuid!=old_uuid and copy.data!=arc.data
    original_radius=arc.beam_screen.radius;copy.beam_screen.radius+=1;objects.update(bpy.context,copy);close(arc.beam_screen.radius,original_radius)
    bpy.ops.beam.screen_action(action='FLIP');assert copy.beam_screen.direction=='REVERSED'
    assert not screen_uv.diagnose(copy.data,reverse=True)['errors']
    # Conversion and bake leave a normal editable mesh, with undo handled by operators.
    bpy.ops.beam.screen_action(action='SURFACE');assert copy.beam_screen.screen_type=='SURFACE' and copy.beam_screen.source is None
    bpy.ops.beam.screen_action(action='BAKE');assert not copy.beam_screen.is_screen
    # Export/reimport every family with nontrivial transforms in a separate scene.
    reports=[]
    for index,obj in enumerate(created[:7]):
        obj.location=(index*18,10,1);obj.rotation_euler.z=.17
        bpy.context.view_layer.update()
        expected=sorted(tuple(round(c,4) for c in obj.matrix_world@v.co) for v in obj.data.vertices)
        for fmt in ('OBJ','FBX'):
            path=screen_export.export(bpy.context,obj,output/(obj.beam_screen.identifier+'.'+fmt.lower()),fmt,overwrite=True)
            original_scene=bpy.context.window.scene;clean=bpy.data.scenes.new('Roundtrip');bpy.context.window.scene=clean
            try:
                if fmt=='OBJ':bpy.ops.wm.obj_import(filepath=str(path),forward_axis='Y',up_axis='Z')
                else:bpy.ops.import_scene.fbx(filepath=str(path))
                meshes=[o for o in clean.objects if o.type=='MESH'];assert len(meshes)==1,(fmt,[o.name for o in clean.objects])
                actual=meshes[0];bpy.context.view_layer.update()
                got=sorted(tuple(round(c,4) for c in actual.matrix_world@v.co) for v in actual.data.vertices)
                assert len(got)==len(expected),(obj.name,fmt,len(got),len(expected))
                assert max(abs(x-y) for a,b in zip(got,expected) for x,y in zip(a,b))<.001,(obj.name,fmt,got[:2],expected[:2])
                assert len(actual.data.polygons)==len(obj.data.polygons)
                assert actual.data.uv_layers.active and not actual.data.materials
                check=screen_uv.diagnose(actual.data);assert not check['errors'],(fmt,check)
                normals=[actual.matrix_world.to_3x3().inverted().transposed()@f.normal for f in actual.data.polygons]
                wanted=[obj.matrix_world.to_3x3().inverted().transposed()@f.normal for f in obj.data.polygons]
                assert all(a.dot(b)>.999 for a,b in zip(normals,wanted)),(obj.name,fmt,'normal mismatch')
                reports.append((obj.beam_screen.identifier,fmt,'PASS'))
            finally:
                bpy.context.window.scene=original_scene
                for o in list(clean.objects):d=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(d)
                bpy.data.scenes.remove(clean)
    # Non-metre Blender units, baked geometry still 6 physical metres wide.
    scaled=bpy.data.scenes.new('Centimetres');bpy.context.window.scene=scaled;scaled.unit_settings.scale_length=.01
    small=objects.create(bpy.context,scaled.beam_screen_draft);close(small.dimensions.x*.01,6,.001)
    path=screen_export.export(bpy.context,small,output/'centimetres.obj','OBJ',overwrite=True)
    bpy.context.window.scene=scene
    # Existing projectors and groups can target the new screens normally.
    from projection_study import projector_object,runtime,blend_groups
    projector=projector_object.create(bpy.context);projector.location=flat.location+Vector((0,-8,1));bpy.context.view_layer.update();runtime.refresh(True)
    assert runtime.CACHE[projector.as_pointer()]['hit'],'Screen did not receive a projector ray'
    second=projector_object.create(bpy.context,projector);group=blend_groups.create(bpy.context,[projector,second],'HORIZONTAL',2,1,200,'PIXELS');assert len(group.members)==2
    # Preserve useful showcase arrangement, hide sources from view only (still editable).
    source.hide_set(True);source_surface.hide_set(True);conform.location=(0,-12,0)
    objects.select(bpy.context,faceted)
    bpy.data.libraries.write(str(output/'Beam-Screen-Builder.blend'),{scene},fake_user=True)
    (output/'results.json').write_text(json.dumps({'roundtrips':reports,'screens':[o.name for o in created],'status':'PASS'},indent=2))
    return {'scene':scene.name,'screens':len(created),'roundtrips':len(reports),'blend':str(output/'Beam-Screen-Builder.blend')}

if __name__=='__main__':print(run(),flush=True)
