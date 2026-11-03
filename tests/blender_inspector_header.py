"""The inspector header stays short, and warnings sit beside what they affect. Background, no GPU."""
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402
from projection_study import projector_object, runtime, ui  # noqa: E402
from tests.ui_recorder import before_first_panel, draw_inspector, labels  # noqa: E402


def add_wall(scene):
    mesh = bpy.data.meshes.new('Wall')
    mesh.from_pydata([(-20, 10, 0), (20, 10, 0), (20, 10, 20), (-20, 10, 20)], [], [(0, 1, 2, 3)])
    mesh.update()
    wall = bpy.data.objects.new('Wall', mesh)
    scene.collection.objects.link(wall)
    return wall


def check_no_projector():
    log = draw_inspector(ui, 'PROJECTOR')
    assert ('prop', 'create_projector_body') in before_first_panel(log), 'body option sits by New Projector when there are none'


def check_projector_header(settings):
    log = draw_inspector(ui, 'PROJECTOR')
    panels = [entry[1] for entry in log if entry[0] == 'panel']
    header = before_first_panel(log)
    assert panels[0] == 'beam_position_aim', panels
    # Outside the Beam workspace this includes the Open Workspace button and the Frame, Solo and Lock row.
    assert len(header) <= 16, f'header has grown to {len(header)} entries: {header}'
    for name in ('project_name', 'revision', 'create_projector_body'):
        assert ('prop', name) not in header, f'{name} should not be in the header'
    assert log.index(('prop', 'project_name')) > log.index(('panel', 'beam_metadata'))
    assert log.index(('prop', 'create_projector_body')) > log.index(('panel', 'beam_projector_body'))
    assert settings.project_name == '', 'drawing must not change values'


def check_receiver_warning(wall, settings):
    bpy.context.view_layer.objects.active = wall
    settings.reverse_receiver = wall
    for inspector in ('PROJECTOR', 'SCREEN', 'GROUP', 'VIEW'):
        log = draw_inspector(ui, inspector)
        header = labels(before_first_panel(log))
        assert not any(text.startswith(('Receiver:', 'Coverage:', 'Reverse Mapping')) for text in header), (inspector, header)
        assert 'GPU viewport required' not in header, (inspector, header)
        section = log.index(('panel', 'beam_reverse_mapping'))
        warning = log.index(('label', 'GPU viewport required'))
        button = log.index(('operator', 'beam.receiver_action'))
        assert section < warning < button, 'warning belongs just above the button it disables'


def check_running_problem(wall):
    wall.beam_reverse['enabled'] = True
    header = labels(before_first_panel(draw_inspector(ui, 'PROJECTOR')))
    assert 'Reverse Mapping · GPU viewport required' in header, header
    wall.beam_reverse['enabled'] = False


def main():
    addon.register()
    context = bpy.context
    settings = context.scene.ps_study
    wall = add_wall(context.scene)
    context.view_layer.update()
    check_no_projector()
    projector = projector_object.create(context)
    projector.location = (0, 0, 5)
    context.view_layer.update()
    runtime.refresh(True)
    check_projector_header(settings)
    check_receiver_warning(wall, settings)
    check_running_problem(wall)
    print('INSPECTOR HEADER PASS: short header, project fields in Project / Workspace, warnings beside their controls')
    addon.unregister()


main()
