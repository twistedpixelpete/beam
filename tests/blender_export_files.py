"""Every exporter writes shareable files, and Beam JSON resolves // paths. Background, no GPU."""
import os
import stat
import sys
import tempfile
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402
from projection_study import projector_object, runtime, screen_export, screen_objects, study_reporting  # noqa: E402


def mode(path):
    return stat.S_IMODE(Path(path).stat().st_mode)


def build_scene(context):
    mesh = bpy.data.meshes.new('Wall')
    mesh.from_pydata([(-20, 10, 0), (20, 10, 0), (20, 10, 20), (-20, 10, 20)], [], [(0, 1, 2, 3)])
    mesh.update()
    context.scene.collection.objects.link(bpy.data.objects.new('Wall', mesh))
    projector = projector_object.create(context)
    projector.location = (0, 0, 5)
    context.view_layer.update()
    runtime.refresh(True)


def check_operators(folder):
    assert bpy.ops.ps.export(filepath=str(folder / 'mm.csv')) == {'FINISHED'}
    assert bpy.ops.beam.export_designer(filepath=str(folder / 'designer.csv')) == {'FINISHED'}
    assert bpy.ops.ps.export_json(filepath=str(folder / 'beam.json')) == {'FINISHED'}
    for name in ('mm.csv', 'mm.metadata.json', 'designer.csv', 'designer.metadata.json', 'beam.json'):
        assert mode(folder / name) == 0o644, (name, oct(mode(folder / name)))


def check_overwrite_keeps_permissions(folder):
    target = folder / 'designer.csv'
    os.chmod(target, 0o660)
    assert bpy.ops.beam.export_designer(filepath=str(target)) == {'FINISHED'}
    assert mode(target) == 0o660
    target = folder / 'beam.json'
    os.chmod(target, 0o660)
    assert bpy.ops.ps.export_json(filepath=str(target)) == {'FINISHED'}
    assert mode(target) == 0o660


def check_screen_export(context, folder):
    screen = screen_objects.create(context, context.scene.beam_screen_draft)
    context.view_layer.update()
    path = screen_export.export(context, screen, folder / 'screen.obj', 'OBJ')
    assert mode(path) == 0o644, oct(mode(path))


def check_study_package(context, folder):
    destination = folder / 'package'
    study_reporting.export(context, str(destination), False, None)
    assert mode(destination) == 0o755, oct(mode(destination))
    assert mode(destination / 'beam-study.json') == 0o644


def check_relative_json(folder):
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / 'scene.blend'))
    assert bpy.ops.ps.export_json(filepath='//relative.json') == {'FINISHED'}
    assert (folder / 'relative.json').exists(), 'A // path should sit beside the saved file'
    assert not Path('//relative.json').exists() and not Path('/relative.json').exists()


def check_no_leftovers(folder):
    leftovers = [item.name for item in folder.iterdir() if item.name.startswith('.beam-')]
    assert not leftovers, leftovers


def main():
    os.umask(0o022)
    addon.register()
    context = bpy.context
    build_scene(context)
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        check_operators(folder)
        check_overwrite_keeps_permissions(folder)
        check_screen_export(context, folder)
        check_study_package(context, folder)
        check_relative_json(folder)
        check_no_leftovers(folder)
    print('EXPORT FILES PASS: normal permissions, overwrite keeps permissions, // paths, no temporary files left')
    addon.unregister()


main()
