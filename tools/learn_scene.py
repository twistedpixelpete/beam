"""Builds Learn-Beam.blend, a scene that teaches Beam through setups you can change.

Run in a new interactive Blender, never one with work open:

    blender --factory-startup --python tools/learn_scene.py -- Learn-Beam.blend [--keep]

The scene is a row of stations, each with one setup and a sign saying what to try.
Saved Study Views visit them in order, so the Views tab's Next button is the tour.
The script checks the scene, saves it, reopens it and checks it again, and writes
the outcome to Learn-Beam.blend.result.json.

The signs name controls in the interface. When a control is renamed, update them here.
"""
import json
import math
import sys
import tempfile
import textwrap
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402

SPACING = 42
SIGN_WIDTH = 58
SIGN_SIZE = .78
SIGN_Y = 18
SIGN_Z = 11
SIGN_LEFT = 12
GUIDE_NAME = 'Learn Beam'


@dataclass
class Station:
    """One stop on the tour: where it is, what it builds and what its sign says."""
    title: str
    x: float
    steps: tuple
    build: object


def modules():
    from projection_study import auto_layout, operators, optics_library, projector_object, screen_objects, study_views
    return SimpleNamespace(auto=auto_layout, ops=operators, optics=optics_library, projectors=projector_object,
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


def rectangle(name, x0, x1, y, z0, z1, target):
    obj = mesh_object(name, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(0, 1, 2, 3)], target)
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


# ---- Stations. Each build returns the names its check needs later.

def build_projector(context, m, x):
    target = collection(context, '1 Projector')
    wall = rectangle('Wall', x - 10, x + 10, 14, 0, 10, target)
    obj = projector(context, m, (x, 0, 4), (x, 14, 5))
    return dict(projector=obj.ps.identifier, target=wall.name)


def build_screens(context, m, x):
    draft = context.scene.beam_screen_draft
    draft.screen_type, draft.category, draft.arc_input = 'ARC', 'PROJECTION', 'RADIUS_ANGLE'
    draft.radius, draft.angle, draft.height, draft.name, draft.aspect = 10, 90, 5, 'Curved Screen', 'FREE'
    arc = m.screens.create(context, draft)
    arc.location = (x, 16, 0)
    context.view_layer.update()
    obj = projector(context, m, (x, 4, 3), (x, 14, 3), .8)
    obj.ps.output_mode = 'UV_GRID'
    return dict(projector=obj.ps.identifier, target=arc.name)


def build_blend(context, m, x):
    settings = context.scene.ps_study
    draft = context.scene.beam_screen_draft
    draft.screen_type, draft.category, draft.aspect = 'FLAT', 'PROJECTION', 'FREE'
    draft.width, draft.height, draft.name = 16, 3.375, 'Wide Screen'
    wall = m.screens.create(context, draft)
    wall.location = (x, 14, 1.5)
    context.view_layer.update()
    m.screens.select(context, wall)
    settings.active_screen = wall
    layout = SimpleNamespace(use_template=False, layout_type='HORIZONTAL', count=3, columns=2, rows=2, auto_count=False,
                             overlap_h=200, overlap_v=200, input_mode='PIXELS', distance=10, fixed_distance=False,
                             max_count=32, min_throw=.1, max_throw=100)
    group, _ = m.auto.create(context, layout)
    return dict(group=group.name, target=wall.name, members=[i.projector.ps.identifier for i in group.members])


def choose_lens(m, obj):
    model_id = next(key for key, value in m.optics.PROJECTORS.items() if value.lenses)
    model = m.optics.PROJECTORS[model_id]
    lens = m.optics.LENSES[model.lenses[0]]
    p = obj.ps
    p.optics_model, p.optics_lens = model_id, model.lenses[0]
    p.resolution_x, p.resolution_y = model.resolution
    p.lumens = model.lumens
    p.throw_ratio = (lens.throw_min + lens.throw_max) / 2


def build_surface(context, m, x):
    target = collection(context, '4 Surface Analysis')
    box('Facade Wall', (x - 8, 14, 0), (x + 8, 14.3, 10), target)
    for index, offset in enumerate((-6, -2, 2, 6)):
        box(f'Facade Column {index + 1}', (x + offset - .4, 13, 0), (x + offset + .4, 14, 10), target)
    box('Facade Lintel', (x - 8, 13.2, 8), (x + 8, 14, 8.8), target)
    box('Truss', (x - 4, 6, 6), (x + 4, 6.3, 6.3), target)
    obj = projector(context, m, (x, -2, 3), (x, 14, 5))
    choose_lens(m, obj)
    obj.ps.shift_v = 10
    context.view_layer.update()
    m.ops.aim(obj, Vector((x, 14, 5)))
    bpy.ops.beam.add_observer()
    observer = context.view_layer.objects.active
    observer.location = (x, 2, 0)
    settings = context.scene.ps_study
    settings.analysis_receiver = bpy.data.objects['Facade Wall']
    settings.analysis_observer = observer
    settings.analysis_scope, settings.analysis_detail = 'ALL', '2048'
    return dict(projector=obj.ps.identifier, target='Facade Wall')


def build_reverse(context, m, x):
    target = collection(context, '5 Reverse Mapping')
    wall = rectangle('Mapped Wall', x - 10, x + 10, 14, 0, 10, target)
    image = bpy.data.images.new('Learn Beam Colour Grid', 2048, 1024)
    image.generated_type = 'COLOR_GRID'
    material = bpy.data.materials.new('Mapped Wall Content')
    material.use_nodes = True
    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    material.node_tree.links.new(texture.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    wall.data.materials.append(material)
    obj = projector(context, m, (x, 0, 5), (x, 14, 5), 1.1)
    obj.ps.output_mode = 'SOLID'
    wall.beam_reverse.source, wall.beam_reverse.projector, wall.beam_reverse.mode = 'SELECTED', obj, 'DIM'
    return dict(projector=obj.ps.identifier, target=wall.name)


def build_cycles(context, m, x):
    target = collection(context, '6 Cycles Render')
    rectangle('Backdrop', x - 10, x + 10, 16, 0, 10, target)
    cloth = rectangle('Cut-out Cloth', x - 8, x + 8, 12, 1, 9, target)
    material = bpy.data.materials.new('Cut-out')
    material.use_nodes = True
    tree = material.node_tree
    checker = tree.nodes.new('ShaderNodeTexChecker')
    checker.inputs['Scale'].default_value = 6
    tree.links.new(tree.nodes.new('ShaderNodeTexCoord').outputs['UV'], checker.inputs['Vector'])
    tree.links.new(checker.outputs['Fac'], tree.nodes['Principled BSDF'].inputs['Alpha'])
    cloth.data.materials.append(material)
    obj = projector(context, m, (x, 0, 5), (x, 14, 5), 1.1)
    return dict(projector=obj.ps.identifier, target=cloth.name)


def build_nothing(context, m, x):
    return {}


STATIONS = (
    Station('Learn Beam', -SPACING, (
        'Everything here is a real setup. Change whatever you like.',
        'Beam is on the right. Its tabs follow a job: Projector, Screen, Blend, Surface, Views, Export.',
        'The dropdown above the tabs holds project details, units and display settings.',
        'To tour the stations, open Views and press View, then Next. Press Exit to look around.',
        'Each sign says what to try. To start again, reopen this file without saving.',
    ), build_nothing),
    Station('1 Projector', 0, (
        'Click the projector. The Projector tab shows its settings.',
        'Type a Position, or drag the arrows in the viewport.',
        'Under Aim At, press Click Surface, then click the wall.',
        'Change Throw Ratio and watch Throw, Width and Height in Calculated.',
        'In Calculated, press a pencil, type the width you need, and tick to solve it.',
    ), build_projector),
    Station('2 Screens', SPACING, (
        'Click the screen. The Screen tab shows its settings.',
        'Change Angle or Height, then press Update Screen.',
        'The projector shows a UV Grid, so you can see how content wraps.',
        'Press New Screen to build a flat, curved or LED screen of your own.',
    ), build_screens),
    Station('3 Blend', 2 * SPACING, (
        'Auto Blend fitted three projectors to this screen.',
        'Click a projector, then press Select Whole Group to open the Blend tab.',
        'Change the Overlap. Beam moves the group and shows the measured result.',
        'Type a Position to move the whole group together.',
        'In Preview / Editing, turn on Feather to see the edge blends.',
    ), build_blend),
    Station('4 Surface Analysis', 3 * SPACING, (
        'Open the Surface tab. The receiver is the Facade Wall. Press Analyse Surface.',
        'Change Heatmap to compare Density, Stretch, Illuminance and Distance.',
        'Acuity uses the Observer on the floor: what a viewer there can resolve.',
        'Move the Truss. The result is marked out of date until you analyse again.',
        'Back on the Projector tab, Optics Guidance checks throw and shift against the lens.',
    ), build_surface),
    Station('5 Reverse Mapping', 4 * SPACING, (
        'Click the wall and open the Surface tab.',
        'Under Reverse Mapping, press Enable on Receiver.',
        'Switch the viewport to Material Preview. Content shows only where light lands.',
        'Move the projector, and the coverage follows.',
        'Press Restore Materials to put the original material back.',
    ), build_reverse),
    Station('6 Cycles Render', 5 * SPACING, (
        'Planning treats this cloth as solid, so the projection stops on it.',
        'In the dropdown above the tabs, set Projection Mode to Cycles Render.',
        'In Render Properties choose Cycles, then use Rendered viewport shading.',
        'Light now passes through the holes and lands on the backdrop.',
        'Set Projection Mode back to Planning when you are done.',
    ), build_cycles),
    Station('7 Views and Export', 6 * SPACING, (
        'On Views, New Study View saves the current camera. Export This View saves a PNG.',
        'On Export, Mapping Matter CSV and Designer CSV hold your projector list.',
        'Beam JSON holds the whole study. Study Package adds a report and images.',
        'Screen Geometry exports the selected screen as OBJ or FBX.',
        'You are done. Now try it with your own venue.',
    ), build_nothing),
)


# ---- Signs and the guide.

def sign_material():
    material = bpy.data.materials.new('Learn Beam Sign')
    material.diffuse_color = (.02, .05, .12, 1)
    material.use_nodes = True
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.02, .05, .12, 1)
    return material


def sign_text(station):
    lines = [station.title.upper(), '']
    for step in station.steps:
        lines.extend(textwrap.wrap('- ' + step, SIGN_WIDTH, subsequent_indent='  '))
    return '\n'.join(lines)


def add_sign(station, material, target):
    """A billboard above and behind each setup, clear of its projection, and it can't be clicked by accident."""
    curve = bpy.data.curves.new(f'Sign {station.title}', 'FONT')
    curve.body = sign_text(station)
    curve.align_x = 'LEFT'
    curve.align_y = 'BOTTOM'
    curve.size = SIGN_SIZE
    curve.materials.append(material)
    obj = bpy.data.objects.new(f'Sign {station.title}', curve)
    obj.location = (station.x - SIGN_LEFT, SIGN_Y, SIGN_Z)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.hide_select = True
    target.objects.link(obj)
    return obj


def add_guide_text():
    text = bpy.data.texts.new(GUIDE_NAME)
    parts = []
    for station in STATIONS:
        parts.append(station.title)
        parts.extend('- ' + step for step in station.steps)
        parts.append('')
    text.write('\n'.join(parts))


def add_floor(target):
    low, high = STATIONS[0].x - 20, STATIONS[-1].x + 20
    mesh_object('Floor', [(low, -40, 0), (high, -40, 0), (high, 40, 0), (low, 40, 0)], [(0, 1, 2, 3)], target)


# ---- Views: the tour.

def view_from(x):
    return Vector((x, -25, 9)), Vector((x, 9, 9))


def add_tour(context, m):
    for station in STATIONS:
        view = m.views.create_view(context, station.title)
        eye, look = view_from(station.x)
        rotation = (look - eye).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
        view.camera.matrix_world = Matrix.Translation(eye) @ rotation
        view.camera.data.lens = 35
        view.camera.data.shift_x, view.camera.data.shift_y = 0, 0
        view.camera.data.clip_end = 1000
        view.camera.data.display_size = .6
        view.resolution_x, view.resolution_y = 1600, 900
    context.scene.ps_study.view_index = 0


def frame_start(context):
    space = context.space_data
    eye, look = view_from(STATIONS[0].x)
    space.clip_end = 1000
    view = space.region_3d
    view.view_perspective = 'PERSP'
    view.view_location = look
    view.view_rotation = (look - eye).to_track_quat('-Z', 'Y')
    view.view_distance = (look - eye).length


def select_first_projector(context, facts):
    obj = identifier_of(facts['1 Projector']['projector'])
    for item in context.selected_objects:
        item.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    settings = context.scene.ps_study
    settings.active_projector = obj
    settings.inspector = 'PROJECTOR'


def build_scene(context):
    """Everything that doesn't need a viewport. Returns the facts the checks read back."""
    from projection_study import projector_object
    m = modules()
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = context.scene
    settings = scene.ps_study
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
    settings.project_name, settings.venue, settings.revision, settings.display_units = 'Learn Beam', 'Practice stage', 'R1', 'm'
    venue = collection(context, 'Venue')
    signs = collection(context, 'Guide Signs')
    add_floor(venue)
    material = sign_material()
    facts = {}
    for station in STATIONS:
        add_sign(station, material, signs)
        facts[station.title] = station.build(context, m, station.x)
    add_guide_text()
    context.view_layer.update()
    assert projector_object.projectors(scene), 'The scene should have projectors'
    return facts


# ---- Checks.

def identifier_of(name):
    return next(o for o in bpy.data.objects if o.ps.is_projector and o.ps.identifier == name)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_targets(facts):
    for title, values in facts.items():
        if 'projector' in values:
            target = identifier_of(values['projector']).ps.target
            require(target and target.name == values['target'], f'{title}: projector should hit {values["target"]}')
    for name in facts['3 Blend']['members']:
        target = identifier_of(name).ps.target
        require(target and target.name == facts['3 Blend']['target'], f'{name} should hit the Blend screen')


def check_signs():
    for station in STATIONS:
        sign = bpy.data.objects[f'Sign {station.title}']
        require(sign.hide_select, f'{sign.name} should not be selectable')
        require(sign.matrix_world.translation.z >= SIGN_Z, f'{sign.name} should sit above its setup')


def check_analysis(context, facts):
    from projection_study import analysis_runtime
    obj = identifier_of(facts['4 Surface Analysis']['projector'])
    stats = analysis_runtime.analyse(context, bpy.data.objects['Facade Wall'], [obj], 512)['statistics']
    require(0 < stats['coverage_percent'] < 100, 'The columns should leave partial coverage on the facade')
    require(stats['occluded_sample_count'] > 0, 'The columns and truss should shadow the facade')


def check_exports():
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        require(bpy.ops.ps.export(filepath=str(folder / 'beam.csv')) == {'FINISHED'}, 'Mapping Matter CSV should export')
        require(bpy.ops.beam.export_designer(filepath=str(folder / 'designer.csv')) == {'FINISHED'}, 'Designer CSV should export')
        require(bpy.ops.ps.export_json(filepath=str(folder / 'beam.json')) == {'FINISHED'}, 'Beam JSON should export')


def check_scene(context, facts):
    from projection_study import runtime
    context.view_layer.update()
    runtime.refresh(True)
    check_targets(facts)
    check_signs()
    check_analysis(context, facts)
    check_exports()
    require(GUIDE_NAME in bpy.data.texts, 'The written guide should be in the file')


def check_tour(context):
    views = [view.name for view in context.scene.ps_study.views]
    require(views == [station.title for station in STATIONS], f'The tour should visit every station in order: {views}')


def check_reverse_mapping(context, facts):
    """Station 5's button has to work, and the file has to be left as it was."""
    wall = bpy.data.objects[facts['5 Reverse Mapping']['target']]
    active = context.view_layer.objects.active
    original = wall.material_slots[0].material
    for item in context.selected_objects:
        item.select_set(False)
    wall.select_set(True)
    context.view_layer.objects.active = wall
    require(bpy.ops.beam.reverse_mapping(action='ENABLE') == {'FINISHED'}, 'Reverse Mapping should enable')
    require(wall.beam_reverse.enabled, 'Reverse Mapping should be on')
    require(bpy.ops.beam.reverse_mapping(action='DISABLE') == {'FINISHED'}, 'Reverse Mapping should restore')
    require(not wall.beam_reverse.enabled and wall.material_slots[0].material == original, 'The original material should return')
    wall.select_set(False)
    context.view_layer.objects.active = active
    if active:
        active.select_set(True)


# ---- Running it in a new Blender.

def in_viewport(window):
    area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return bpy.context.temp_override(window=window, area=area, region=region, space_data=area.spaces.active)


class Run:
    def __init__(self, out, keep):
        self.out = out
        self.keep = keep
        self.result_path = out.with_name(out.name + '.result.json')
        self.report = dict(failures=[])
        self.facts = None

    def finish(self, error=None):
        if error:
            self.report['failures'].append(error)
        self.report['passed'] = not self.report['failures']
        self.result_path.write_text(json.dumps(self.report, indent=2))
        print(('LEARN SCENE PASS' if self.report['passed'] else 'LEARN SCENE FAIL') + f': {self.result_path}', flush=True)
        if not self.keep:
            bpy.ops.wm.quit_blender()

    def build(self):
        try:
            addon.register()
            window = bpy.context.window_manager.windows[0]
            with in_viewport(window):
                context = bpy.context
                self.facts = build_scene(context)
                add_tour(context, modules())
                frame_start(context)
                check_scene(context, self.facts)
                check_reverse_mapping(context, self.facts)
                check_tour(context)
                select_first_projector(context, self.facts)
                context.scene['learn_beam_facts'] = json.dumps(self.facts)
                bpy.ops.beam.workspace()
            # The window changes workspace on its next update, so save after that.
            bpy.app.timers.register(self.save, first_interval=.5)
        except Exception:
            self.finish(traceback.format_exc())

    def save(self):
        try:
            self.out.parent.mkdir(parents=True, exist_ok=True)
            with in_viewport(bpy.context.window_manager.windows[0]):
                bpy.ops.wm.save_as_mainfile(filepath=str(self.out))
            bpy.app.timers.register(self.reopen, first_interval=.5)
        except Exception:
            self.finish(traceback.format_exc())

    def reopen(self):
        try:
            bpy.ops.wm.open_mainfile(filepath=str(self.out))
            bpy.app.timers.register(self.after_reopen, first_interval=2)
        except Exception:
            self.finish(traceback.format_exc())

    def after_reopen(self):
        try:
            window = bpy.context.window_manager.windows[0]
            require(window.workspace.get('beam_workspace'), 'The scene should open on the Beam workspace')
            with in_viewport(window):
                context = bpy.context
                check_scene(context, json.loads(context.scene['learn_beam_facts']))
                check_tour(context)
                require(context.scene.ps_study.projection_mode == 'PLANNING', 'The scene should open in Planning mode')
                require(context.scene.ps_study.inspector == 'PROJECTOR', 'The scene should open on the Projector tab')
            bpy.ops.wm.revert_mainfile()
            self.finish()
        except Exception:
            self.finish(traceback.format_exc())


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    paths = [arg for arg in args if not arg.startswith('--')]
    out = Path(paths[0]).resolve() if paths else ROOT / 'work/Learn-Beam.blend'
    run = Run(out, '--keep' in args)
    bpy.app.timers.register(run.build, first_interval=2)


if __name__ == '__main__':
    main()
