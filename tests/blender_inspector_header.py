"""The inspector header stays short, and warnings sit beside what they affect. Background, no GPU."""
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402
from projection_study import projector_object, runtime, study_data, ui  # noqa: E402
from tests.ui_recorder import before_first_panel, draw_inspector, draw_project_settings, labels  # noqa: E402


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
    assert any(entry[0] == 'popover' for entry in header), 'project dropdown should be at the top'
    for name in ('project_name', 'revision', 'create_projector_body', 'display_units'):
        assert ('prop', name) not in header, f'{name} should not be in the header'
    assert log.index(('prop', 'create_projector_body')) > log.index(('panel', 'beam_projector_body'))
    assert settings.project_name == '', 'drawing must not change values'


def check_projector_order():
    panels = [entry[1] for entry in draw_inspector(ui, 'PROJECTOR') if entry[0] == 'panel']
    order = ['beam_position_aim', 'beam_projection', 'beam_calculated', 'beam_solver', 'beam_optics', 'beam_projector_output', 'beam_projector_body']
    assert [name for name in panels if name in order] == order, panels


def check_project_dropdown(settings):
    log = draw_project_settings(ui)
    assert not [entry for entry in log if entry[0] == 'panel'], "Blender doesn't allow layout panels in a dropdown"
    for name in ('project_name', 'revision', 'venue', 'client', 'author', 'display_units', 'projection_mode', 'label_detail'):
        assert ('prop', name) in log, f'{name} should be in the project dropdown'
    assert ('operator', 'beam.workspace') in log and ('operator', 'beam.apply_theme') in log
    assert ui.project_label(settings) == 'Project'
    settings.project_name, settings.revision = 'Town Hall', 'R02'
    assert ui.project_label(settings) == 'Town Hall · R02'
    settings.project_name, settings.revision = '', ''


def check_sections_appear_once():
    moved = ('beam_surface_analysis', 'beam_surface_analysis_result', 'beam_reverse_mapping', 'beam_render_projection', 'beam_display', 'beam_metadata')
    for inspector in ('PROJECTOR', 'SCREEN', 'GROUP', 'VIEW', 'EXPORT'):
        log = draw_inspector(ui, inspector)
        found = [entry[1] for entry in log if entry[0] == 'panel' and entry[1] in moved]
        assert not found, (inspector, found)
    log = draw_inspector(ui, 'SURFACE')
    assert ('panel', 'beam_surface_analysis') in log and ('panel', 'beam_reverse_mapping') in log


def check_surface_without_receiver(settings):
    settings.reverse_receiver = None
    log = draw_inspector(ui, 'SURFACE')
    assert ('prop', 'reverse_receiver') in log, 'the receiver can be chosen with nothing selected'
    assert ('label', 'Choose a mesh to show coverage on') in log


def check_receiver_warning(wall, settings):
    bpy.context.view_layer.objects.active = wall
    settings.reverse_receiver = wall
    for inspector in ('PROJECTOR', 'SCREEN', 'GROUP', 'VIEW'):
        header = labels(before_first_panel(draw_inspector(ui, inspector)))
        assert not any(text.startswith(('Receiver:', 'Coverage:', 'Reverse Mapping')) for text in header), (inspector, header)
        assert 'GPU viewport required' not in header, (inspector, header)
    log = draw_inspector(ui, 'SURFACE')
    section = log.index(('panel', 'beam_reverse_mapping'))
    warning = log.index(('label', 'GPU viewport required'))
    button = log.index(('operator', 'beam.receiver_action'))
    assert section < warning < button, 'warning belongs just above the button it disables'


def check_running_problem(wall):
    wall.beam_reverse['enabled'] = True
    header = labels(before_first_panel(draw_inspector(ui, 'PROJECTOR')))
    assert 'Reverse Mapping · GPU viewport required' in header, header
    wall.beam_reverse['enabled'] = False


def check_surface_stays_open(projector, settings):
    context = bpy.context
    settings.inspector = 'SURFACE'
    study_data.sync_selection(context)
    projector.select_set(True)
    context.view_layer.objects.active = projector
    study_data.sync_selection(context)
    assert settings.active_projector == projector, 'selecting still updates the active projector'
    assert settings.inspector == 'SURFACE', 'selecting a projector should not leave the Surface tab'
    settings.inspector = 'VIEW'
    assert settings.bl_rna.properties['inspector'].enum_items['VIEW'].value == 3, 'saved tab numbers must not change'


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
    check_projector_order()
    check_project_dropdown(settings)
    check_sections_appear_once()
    check_surface_without_receiver(settings)
    check_receiver_warning(wall, settings)
    check_running_problem(wall)
    check_surface_stays_open(projector, settings)
    print('INSPECTOR HEADER PASS: short header, project dropdown, one Surface tab, warnings beside their controls')
    addon.unregister()


main()
