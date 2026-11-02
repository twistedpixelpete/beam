"""Builds Beam's feature test scene, checks it, and saves it.

Run in a new interactive Blender, never one with work open:

    blender --factory-startup --python tests/feature_scene.py -- OUT.blend [--keep]

The script checks the scene, saves it to OUT.blend, reopens it, and checks it
again. With --keep, Blender stays open on the saved scene for hands-on testing.
Without it, Blender quits and the result is written to OUT.blend.result.json.

To cover a new feature, add a Section to SECTIONS, then add its hands-on steps
to docs/TESTING.md. See that page for the rule.
"""
import json
import math
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
KEEP = '--keep' in args
paths = [a for a in args if not a.startswith('--')]
OUT = Path(paths[0]).resolve() if paths else ROOT / 'work/Beam-Feature-Test-Scene.blend'
RESULT = OUT.with_name(OUT.name + '.result.json')
SPACING = 30
IDLE_SECONDS = 6
report = dict(built={}, checks={}, reopened={}, idle={}, failures=[])


@dataclass
class Section:
    """One feature area: its floor label and x position, how to build it, what must be true."""
    key: str
    label: str
    x: float
    build: object
    verify: object


def modules():
    from projection_study import (analysis_runtime, auto_layout, export_disguise, faults, operators,
                                  optics_library, projector_object, runtime, screen_objects, study_views)
    return SimpleNamespace(analysis=analysis_runtime, auto=auto_layout, disguise=export_disguise, faults=faults,
                           ops=operators, optics=optics_library, projectors=projector_object, runtime=runtime,
                           screens=screen_objects, views=study_views)


def collection(context, name):
    result = bpy.data.collections.new(name)
    context.scene.collection.children.link(result)
    return result


def mesh_object(name, vertices, faces, target):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    return obj


def box(name, low, high, target):
    (a, b, c), (d, e, f) = low, high
    vertices = [(a, b, c), (d, b, c), (d, e, c), (a, e, c), (a, b, f), (d, b, f), (d, e, f), (a, e, f)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_object(name, vertices, faces, target)


def rectangle(name, x0, x1, y, z0, z1, target, uv=False):
    obj = mesh_object(name, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(0, 1, 2, 3)], target)
    if uv:
        layer = obj.data.uv_layers.new(name='UVMap')
        for loop, co in zip(layer.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop.uv = co
    return obj


def projector(context, m, location, aim_at, ratio=1.2):
    obj = m.projectors.create(context)
    obj.location = location
    obj.ps.throw_ratio = ratio
    context.view_layer.update()
    m.ops.aim(obj, Vector(aim_at))
    context.view_layer.update()
    return obj


def identifier_of(name):
    """The projector that a section recorded, by the name saved in its build result."""
    return next(o for o in bpy.data.objects if o.ps.is_projector and o.ps.identifier == name)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


# ---- Sections. Each build returns JSON-friendly facts; each verify reads them back.

def build_blend(context, m, x):
    settings = context.scene.ps_study
    draft = context.scene.beam_screen_draft
    draft.screen_type, draft.category, draft.aspect = 'FLAT', 'PROJECTION', 'FREE'
    draft.width, draft.height, draft.name = 16, 3.375, 'Flat Screen'
    wall = m.screens.create(context, draft)
    wall.location = (x, 14, 1.5)
    context.view_layer.update()
    m.screens.select(context, wall)
    settings.active_screen = wall
    layout = SimpleNamespace(use_template=False, layout_type='HORIZONTAL', count=3, columns=2, rows=2, auto_count=False,
                             overlap_h=200, overlap_v=200, input_mode='PIXELS', distance=10, fixed_distance=False,
                             max_count=32, min_throw=.1, max_throw=100)
    group, _ = m.auto.create(context, layout)
    return dict(group=group.name, screen=wall.name, members=[i.projector.ps.identifier for i in group.members])


def verify_blend(context, m, facts):
    group = next(g for g in context.scene.ps_study.blend_groups if g.name == facts['group'])
    require(len(group.members) == 3, 'Auto Blend should have three members')
    for name in facts['members']:
        target = identifier_of(name).ps.target
        require(target and target.name == facts['screen'], f'{name} should hit the flat screen')
    # The position fields move one member in world space, and the controller moves them all.
    member = identifier_of(facts['members'][1])
    start = member.matrix_world.translation.copy()
    member.beam_transform.position = start + Vector((.5, 0, 0))
    context.view_layer.update()
    require((member.matrix_world.translation - start - Vector((.5, 0, 0))).length < 1e-4, 'Position field should move a member in world space')
    member.beam_transform.position = start
    controller = group.controller
    origin, before = controller.matrix_world.translation.copy(), identifier_of(facts['members'][0]).matrix_world.translation.copy()
    controller.beam_transform.position = origin + Vector((0, 0, 1))
    context.view_layer.update()
    require((identifier_of(facts['members'][0]).matrix_world.translation - before - Vector((0, 0, 1))).length < 1e-4, 'Moving the controller should move its members')
    controller.beam_transform.position = origin
    context.view_layer.update()


def build_facade(context, m, x):
    target = collection(context, '2 Facade and Analysis')
    box('Facade Wall', (x - 8, 14, 0), (x + 8, 14.3, 10), target)
    for index, offset in enumerate((-6, -2, 2, 6)):
        box(f'Facade Column {index + 1}', (x + offset - .4, 13, 0), (x + offset + .4, 14, 10), target)
    box('Facade Lintel', (x - 8, 13.2, 8), (x + 8, 14, 8.8), target)
    box('Truss Occluder', (x - 4, 6, 6), (x + 4, 6.3, 6.3), target)
    obj = projector(context, m, (x, -2, 3), (x, 14, 5))
    model_id = next(k for k, v in m.optics.PROJECTORS.items() if v.lenses)
    model = m.optics.PROJECTORS[model_id]
    lens = m.optics.LENSES[model.lenses[0]]
    p = obj.ps
    p.optics_model, p.optics_lens = model_id, model.lenses[0]
    p.resolution_x, p.resolution_y = model.resolution
    p.lumens = model.lumens
    p.throw_ratio = (lens.throw_min + lens.throw_max) / 2
    p.shift_v = 10
    context.view_layer.update()
    m.ops.aim(obj, Vector((x, 14, 5)))
    bpy.ops.beam.add_observer()
    observer = context.view_layer.objects.active
    observer.location = (x, 2, 0)
    settings = context.scene.ps_study
    settings.analysis_receiver = bpy.data.objects['Facade Wall']
    settings.analysis_observer = observer
    settings.analysis_scope, settings.analysis_detail = 'ALL', '2048'
    return dict(projector=p.identifier, optics=f'{model_id} / {model.lenses[0]}', observer=observer.name)


def check_group_selection_keeps_analysis(context, m):
    settings = context.scene.ps_study
    key = context.scene.as_pointer()
    held, scope, index = m.analysis.CACHE.get(key), settings.analysis_scope, settings.blend_group_index
    m.analysis.CACHE[key] = dict(stale=False)
    settings.analysis_scope = 'ALL'
    m.analysis.CACHE[key]['stale'] = False
    settings.blend_group_index = index
    require(not m.analysis.CACHE[key]['stale'], 'Selecting a group should not stale an All Projectors analysis')
    settings.analysis_scope = scope
    if held:
        m.analysis.CACHE[key] = held
    else:
        m.analysis.CACHE.pop(key)


def verify_facade(context, m, facts):
    check_group_selection_keeps_analysis(context, m)
    obj = identifier_of(facts['projector'])
    require(obj.ps.target and obj.ps.target.name == 'Facade Wall', 'Facade projector should hit the wall')
    context.view_layer.update()
    m.runtime.refresh(True)
    stats = m.analysis.analyse(context, bpy.data.objects['Facade Wall'], [obj], 512)['statistics']
    require(0 < stats['coverage_percent'] < 100, 'Columns should leave partial coverage on the wall')
    require(stats['occluded_sample_count'] > 0, 'Columns and truss should occlude some samples')


def build_reverse(context, m, x):
    target = collection(context, '3 Reverse Mapping')
    wall = rectangle('Reverse Receiver', x - 10, x + 10, 14, 0, 10, target, uv=True)
    image = bpy.data.images.new('Test Colour Grid', 2048, 1024)
    image.generated_type = 'COLOR_GRID'
    material = bpy.data.materials.new('Reverse Source')
    material.use_nodes = True
    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    material.node_tree.links.new(texture.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    wall.data.materials.append(material)
    obj = projector(context, m, (x, 0, 5), (x, 14, 5), 1.1)
    obj.ps.output_mode = 'SOLID'
    for item in context.selected_objects:
        item.select_set(False)
    wall.select_set(True)
    context.view_layer.objects.active = wall
    wall.beam_reverse.source, wall.beam_reverse.projector, wall.beam_reverse.mode = 'SELECTED', obj, 'DIM'
    require(bpy.ops.beam.reverse_mapping(action='ENABLE') == {'FINISHED'}, 'Reverse Mapping did not enable')
    context.space_data.shading.type = 'SOLID'
    return dict(projector=obj.ps.identifier)


def verify_reverse(context, m, facts):
    wall = bpy.data.objects['Reverse Receiver']
    require(wall.beam_reverse.enabled, 'Reverse Mapping should be enabled')
    require(wall.material_slots[0].material.get('beam_reverse'), 'Receiver should use a coverage wrapper')


def build_heavy(context, m, x):
    target = collection(context, '4 Heavy Venue Scan')
    n = 125
    vertices = [((i / n - .5) * 20, math.sin(i * .3) * math.cos(j * .2) * .4, j / n * 10) for j in range(n + 1) for i in range(n + 1)]
    faces = [(i + j * (n + 1), i + 1 + j * (n + 1), i + 1 + (j + 1) * (n + 1), i + (j + 1) * (n + 1)) for j in range(n) for i in range(n)]
    scan = mesh_object('Venue Scan', vertices, faces, target)
    scan.location = (x, 14, 0)
    modifier = scan.modifiers.new('Scan Density', 'SUBSURF')
    modifier.subdivision_type, modifier.levels, modifier.render_levels = 'SIMPLE', 3, 3
    context.view_layer.update()
    obj = projector(context, m, (x, 0, 5), (x, 14, 5), 1.1)
    obj.ps.output_mode = 'CHECKER'
    return dict(projector=obj.ps.identifier)


def verify_heavy(context, m, facts):
    scan = bpy.data.objects['Venue Scan']
    graph = context.evaluated_depsgraph_get()
    evaluated = scan.evaluated_get(graph)
    count = len(evaluated.to_mesh().vertices)
    evaluated.to_mesh_clear()
    require(count > 900000, f'Heavy scan should evaluate near 1M vertices, not {count}')
    require(identifier_of(facts['projector']).ps.target == scan, 'Heavy scan projector should hit the scan')
    from projection_study import scene_geometry, target_raycast
    target_raycast.prepare()
    surface = scene_geometry.SURFACES[scan.as_pointer()]
    tree = target_raycast._trees[scan.as_pointer()]
    original = scan.location.copy()
    started = time.perf_counter()
    scan.location.x += .1
    context.view_layer.update()
    target_raycast.prepare()
    moved = time.perf_counter() - started
    require(target_raycast._trees[scan.as_pointer()] is tree, 'A move should not rebuild the ray-cast tree')
    require(scene_geometry.SURFACES[scan.as_pointer()].geometry_id == surface.geometry_id, 'A move should not re-read the mesh')
    scan.location = original
    context.view_layer.update()
    report['checks']['heavy_move_seconds'] = round(moved, 3)


def build_screens(context, m, x):
    draft = context.scene.beam_screen_draft
    draft.screen_type, draft.category, draft.arc_input = 'ARC', 'PROJECTION', 'RADIUS_ANGLE'
    draft.radius, draft.angle, draft.height, draft.name, draft.aspect = 10, 90, 5, 'Arc Screen', 'FREE'
    arc = m.screens.create(context, draft)
    arc.location = (x, 16, 0)
    context.view_layer.update()
    grid = projector(context, m, (x, 4, 3), (x, 14, 3), .8)
    grid.ps.output_mode = 'UV_GRID'
    open_air = projector(context, m, (x - 10, 4, 3), (x - 10, 4, 20), 1)
    open_air.ps.output_mode = 'ID'
    return dict(screen=arc.name, grid=grid.ps.identifier, open_air=open_air.ps.identifier)


def verify_screens(context, m, facts):
    grid = identifier_of(facts['grid'])
    require(grid.ps.target and grid.ps.target.name == facts['screen'], 'UV grid projector should hit the arc')
    open_air = identifier_of(facts['open_air'])
    require(open_air.ps.target is None, 'Open-air projector should have no target')
    _, errors = m.disguise.collect_rows(context)
    require(any(e['projector_name'] == open_air.ps.identifier and e['code'] == 'NO_TARGET' for e in errors), 'CSV checks should report No Target')


def build_cycles(context, m, x):
    target = collection(context, '6 Cycles Cloth')
    rectangle('Backdrop', x - 10, x + 10, 16, 0, 10, target)
    cloth = rectangle('Cut-out Cloth', x - 8, x + 8, 12, 1, 9, target, uv=True)
    material = bpy.data.materials.new('Cut-out')
    material.use_nodes = True
    tree = material.node_tree
    checker = tree.nodes.new('ShaderNodeTexChecker')
    checker.inputs['Scale'].default_value = 6
    tree.links.new(tree.nodes.new('ShaderNodeTexCoord').outputs['UV'], checker.inputs['Vector'])
    tree.links.new(checker.outputs['Fac'], tree.nodes['Principled BSDF'].inputs['Alpha'])
    cloth.data.materials.append(material)
    obj = projector(context, m, (x, 0, 5), (x, 14, 5), 1.1)
    return dict(projector=obj.ps.identifier)


def verify_cycles(context, m, facts):
    require(context.scene.ps_study.projection_mode == 'PLANNING', 'The scene should open in Planning mode')
    require(identifier_of(facts['projector']).ps.target.name == 'Cut-out Cloth', 'Planning treats the cloth as solid')


def build_load(context, m, x):
    target = collection(context, '7 Idle Load (excluded)')
    for index in range(3000):
        target.objects.link(bpy.data.objects.new(f'Load {index:04d}', None))
    context.scene.view_layers[0].layer_collection.children[target.name].exclude = True
    return dict(objects=3000)


def verify_load(context, m, facts):
    require(sum(o.name.startswith('Load ') for o in context.scene.objects) == 3000, 'Idle load objects are missing')


def build_views(context, m, x):
    names = []
    for name, eye, look in (('Overview', (12, -90, 60), (12, 6, 3)), ('Auto Blend', (0, -6, 5), (0, 14, 3)), ('Facade', (SPACING, -5, 6), (SPACING, 14, 5))):
        view = m.views.create_view(context, name)
        rotation = (Vector(look) - Vector(eye)).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
        view.camera.matrix_world = Matrix.Translation(eye) @ rotation
        view.camera.data.display_size = .6
        view.resolution_x, view.resolution_y = 1600, 900
        names.append(view.name)
    return dict(views=names)


def verify_views(context, m, facts):
    settings = context.scene.ps_study
    require([v.name for v in settings.views] == facts['views'], 'Study Views changed')
    require(all(v.camera for v in settings.views), 'A Study View lost its camera')


SECTIONS = (
    Section('blend', '1 Auto Blend', 0, build_blend, verify_blend),
    Section('facade', '2 Facade + Analysis', SPACING, build_facade, verify_facade),
    Section('reverse', '3 Reverse Mapping', -SPACING, build_reverse, verify_reverse),
    Section('heavy', '4 Heavy Scan (~1M verts)', 2 * SPACING, build_heavy, verify_heavy),
    Section('screens', '5 Arc Screen + Modes', -2 * SPACING, build_screens, verify_screens),
    Section('cycles', '6 Cycles Cut-out Cloth', 3 * SPACING, build_cycles, verify_cycles),
    Section('load', '', 0, build_load, verify_load),
    Section('views', '', 0, build_views, verify_views),
)


# ---- Running it.

def viewport():
    window = bpy.context.window_manager.windows[0]
    area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return window, area, region


def in_viewport():
    window, area, region = viewport()
    return bpy.context.temp_override(window=window, area=area, region=region, space_data=area.spaces.active)


def finish(error=None):
    if error:
        report['failures'].append(error)
    report['passed'] = not report['failures']
    RESULT.write_text(json.dumps(report, indent=2))
    print(('FEATURE SCENE PASS' if report['passed'] else 'FEATURE SCENE FAIL') + f': {RESULT}', flush=True)
    if not KEEP:
        bpy.ops.wm.quit_blender()


def check_all(phase):
    m = modules()
    context = bpy.context
    context.view_layer.update()
    m.runtime.refresh(True)
    for section in SECTIONS:
        try:
            section.verify(context, m, json.loads(context.scene['beam_feature_scene'])[section.key])
            report[phase][section.key] = 'pass'
        except Exception:
            report[phase][section.key] = 'FAIL'
            report['failures'].append(f'{phase} {section.key}: {traceback.format_exc()}')
    summary = m.faults.summary()
    if summary:
        report['failures'].append(f'{phase} faults: {summary}')


def build():
    try:
        addon.register()
        with in_viewport():
            context = bpy.context
            scene = context.scene
            for obj in list(bpy.data.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            m = modules()
            settings = scene.ps_study
            scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
            settings.project_name, settings.venue, settings.display_units = 'Beam Feature Test Scene', 'Test stage', 'm'
            venue = collection(context, 'Venue')
            labels = collection(context, 'Test Labels')
            mesh_object('Floor', [(-110, -30, 0), (110, -30, 0), (110, 40, 0), (-110, 40, 0)], [(0, 1, 2, 3)], venue)
            facts = {}
            for section in SECTIONS:
                if section.label:
                    label = bpy.data.objects.new(section.label, None)
                    labels.objects.link(label)
                    label.location, label.show_name, label.show_in_front = (section.x, -4, .1), True, True
                    label.empty_display_size = .5
                facts[section.key] = section.build(context, m, section.x)
                report['built'][section.key] = facts[section.key]
            scene['beam_feature_scene'] = json.dumps(facts)
            space = context.space_data
            space.clip_end = 1000
            view = space.region_3d
            view.view_location = (12, 6, 3)
            view.view_rotation = (Vector((12, 6, 3)) - Vector((12, -90, 60))).to_track_quat('-Z', 'Y')
            view.view_distance, view.view_perspective = 135, 'PERSP'
            check_all('checks')
            OUT.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
        bpy.app.timers.register(reopen, first_interval=.5)
    except Exception:
        finish(traceback.format_exc())


def reopen():
    try:
        identities = {o.ps.identifier: o.ps.uuid for o in bpy.data.objects if o.ps.is_projector}
        report['_identities'] = identities
        bpy.ops.wm.open_mainfile(filepath=str(OUT))
        bpy.app.timers.register(after_reopen, first_interval=2)
    except Exception:
        finish(traceback.format_exc())


def after_reopen():
    try:
        identities = report.pop('_identities')
        now = {o.ps.identifier: o.ps.uuid for o in bpy.data.objects if o.ps.is_projector}
        if now != identities:
            report['failures'].append(f'Projector identities changed on reopen: {identities} became {now}')
        check_all('reopened')
        bpy.ops.wm.revert_mainfile()
        bpy.app.timers.register(idle_start, first_interval=4)
    except Exception:
        finish(traceback.format_exc())


counter = dict(draws=0, handle=None)


def count_draw():
    counter['draws'] += 1


def idle_start():
    try:
        viewport()[1].spaces.active.shading.type = 'MATERIAL'
        counter['handle'] = bpy.types.SpaceView3D.draw_handler_add(count_draw, (), 'WINDOW', 'POST_PIXEL')
        bpy.app.timers.register(idle_measure, first_interval=6)
    except Exception:
        finish(traceback.format_exc())


def idle_measure():
    counter['draws'] = 0
    counter['started'] = time.monotonic()
    bpy.app.timers.register(idle_end, first_interval=IDLE_SECONDS)


def idle_end():
    try:
        rate = counter['draws'] / (time.monotonic() - counter['started'])
        report['idle']['reverse_mapping_draws_per_second'] = round(rate, 1)
        if rate > 5:
            report['failures'].append(f'Viewport redraws while idle with Reverse Mapping on: {rate:.0f} per second')
        bpy.types.SpaceView3D.draw_handler_remove(counter['handle'], 'WINDOW')
        viewport()[1].spaces.active.shading.type = 'SOLID'
        finish()
    except Exception:
        finish(traceback.format_exc())


bpy.app.timers.register(build, first_interval=2)
