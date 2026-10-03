import bpy
from pathlib import Path
from projection_study import study_views,presentation
from projection_study.interchange import beam_filename
scene=bpy.context.scene; area=bpy.context.area; space=area.spaces.active
original=(space.shading.type,space.shading.color_type,space.overlay.show_floor,space.overlay.show_overlays)
materials=[(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials]
assert bpy.ops.beam.presentation()=={'FINISHED'}
assert presentation.active(area) and not space.overlay.show_floor and not space.overlay.show_overlays
assert materials==[(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials]
presentation.before_save(); assert not presentation.active(area)
assert original==(space.shading.type,space.shading.color_type,space.overlay.show_floor,space.overlay.show_overlays)
presentation.after_save(); assert presentation.active(area) and not space.overlay.show_floor
assert bpy.ops.beam.presentation()=={'FINISHED'}
assert original==(space.shading.type,space.shading.color_type,space.overlay.show_floor,space.overlay.show_overlays)
old_light=space.shading.light; old_studio=space.shading.studio_light
space.shading.light='MATCAP'; matcap=space.shading.studio_light
bpy.ops.beam.presentation(); bpy.ops.beam.presentation()
assert space.shading.light=='MATCAP' and space.shading.studio_light==matcap
space.shading.light=old_light; space.shading.studio_light=old_studio
s=scene.ps_study;s.project_name='Melbourne Town Hall';s.revision='R02'
v=study_views.create_view(bpy.context,'PJ01 Coverage');v.resolution_x=320;v.resolution_y=200
assert study_views.proposed_names(scene)[v.uuid]=='Melbourne_Town_Hall_R02_PJ01_Coverage.png'
assert beam_filename('','','PJ01 Coverage')=='Beam_PJ01_Coverage.png'
assert '/' not in beam_filename('../Venue:/ hall','R 02','View ** A')
path=root/'work/User_Edited_Name.png'; path.unlink(missing_ok=True)
assert bpy.ops.ps.export_views(filepath=str(path))=={'FINISHED'}
assert path.exists() and v.image_filename==path.name
print('MILESTONE 15 Presentation restore / metadata names / exact edited export path PASS')

import tempfile
with tempfile.TemporaryDirectory(dir=root/'work') as directory:
    assert bpy.ops.ps.export_views(directory=directory,all_views=True,proposed_files=[{'name':'Edited view','view_uuid':v.uuid,'filename':'Batch_Edited.png'}])=={'FINISHED'}
    assert (Path(directory)/'Batch_Edited.png').exists()
print('Editable batch filename PASS')
