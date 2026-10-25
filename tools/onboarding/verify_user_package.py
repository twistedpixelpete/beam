"""Run in a fresh background Blender process with a disposable configuration."""
import bpy
import sys
import tempfile
import zipfile
from pathlib import Path
root = Path(__file__).resolve().parents[2]
package = root / 'output/pdf/Beam_Onboarding'
assert not hasattr(bpy.types.Object, 'ps'), 'Use a fresh disposable Blender configuration'
with tempfile.TemporaryDirectory(prefix='beam-clean-package-') as temp:
    with zipfile.ZipFile(package/'Install/beam-0.13.0.zip') as archive:
        archive.extractall(Path(temp)/'projection_study')
    sys.path.insert(0, temp)
    import projection_study as addon
    addon.register()
    try:
        bpy.ops.wm.open_mainfile(filepath=str(package/'Beam_Training_Project.blend'), load_ui=False)
        settings = bpy.context.scene.ps_study
        assert len(settings.views) == 9 and all(v.camera for v in settings.views)
        assert len(settings.blend_groups) == 1 and len(settings.blend_groups[0].members) == 3
        assert bpy.data.images['Training UV Chart'].packed_file
        assert bpy.data.objects['OBS01'].beam_observer.is_observer
        from projection_study.export_json import document
        assert len(document(bpy.context)['projectors']) == 3
        print('PASS: cleaned package installation archive registers; training file opens with three projectors, group, nine cameras, Observer and packed chart; JSON contract validates.')
    finally:
        addon.unregister()
