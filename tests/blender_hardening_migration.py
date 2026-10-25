"""Read old fixtures without modifying them; save/reopen only disposable copies."""
import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import projection_study as addon
from projection_study import runtime,analysis_runtime,projector_object,transform_conversion
addon.register();out=root/'work/hardening/migration';out.mkdir(parents=True,exist_ok=True);results=[]
def snapshot():
 s=bpy.context.scene.ps_study
 return dict(projectors=sorted((o.ps.uuid,o.ps.identifier,o.ps.optics_model,o.ps.optics_lens) for o in projector_object.projectors(bpy.context.scene)),groups=sorted(g.uuid for g in s.blend_groups),screens=sorted(o.beam_screen.uuid for o in bpy.context.scene.objects if o.beam_screen.is_screen),views=[(v.uuid,v.analysis_overlay) for v in s.views],metadata=(s.project_name,s.venue,s.revision),analysis=(s.analysis_detail,s.analysis_mode,s.analysis_scope),pin=s.pin_context,active_projector=s.active_projector.ps.uuid if s.active_projector else None,inspector=s.inspector)
for index,name in enumerate(('examples/0.4/projection-acceptance.blend','examples/0.6/Beam_group_lifecycle.blend','examples/0.8/Beam-Screen-Builder.blend','examples/0.9/Beam-Auto-Blend.blend','examples/production/Beam-PATCH-fixture.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(root/name));runtime.refresh(True);before=snapshot();assert not analysis_runtime.CACHE
 assert all(v.analysis_overlay=='NONE' for v in bpy.context.scene.ps_study.views) if index<4 else True
 if index<4:assert all(o.ps.optics_model=='MANUAL' and o.ps.optics_lens=='MANUAL' for o in projector_object.projectors(bpy.context.scene))
 bpy.ops.wm.save_as_mainfile(filepath=str(out/f'copy-{index}.blend'));bpy.ops.wm.open_mainfile(filepath=str(out/f'copy-{index}.blend'));runtime.refresh(True);assert snapshot()==before;assert not analysis_runtime.CACHE
 results.append(dict(fixture=name,projector_count=len(before['projectors']),status='PASS'))
assert transform_conversion.CONVENTION_ID=='beam_mapping_matter_transform_v1' and transform_conversion.DESIGNER_CONVENTION_ID=='beam_designer_transform_v1'
(out/'result.json').write_text(json.dumps(results,indent=2));print('MIGRATION PASS: five generations, stable UUIDs/presets/views/configuration, transient analysis and safe defaults')
addon.unregister()
