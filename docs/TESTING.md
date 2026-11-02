# Testing Beam

## The feature test scene
Every Beam feature is tested in one generated scene, so a change can be checked against everything else at once. The scene is built by [`tests/feature_scene.py`](../tests/feature_scene.py) rather than stored as a `.blend`, which keeps it current with the code and keeps the repository small.

Run it in a new Blender, never one with work open:

```sh
blender --factory-startup --python tests/feature_scene.py -- ~/Desktop/Beam-Test-Scene.blend --keep
```

The script builds and checks the scene, saves it, reopens it and checks it again, then measures idle redraws with Reverse Mapping on. It writes the outcome to `Beam-Test-Scene.blend.result.json` next to the scene. With `--keep`, Blender stays open for hands-on testing. Without it, Blender quits, which suits automated runs. It needs a GPU viewport, so it can't run in background mode.

## The rule for new features
A feature isn't finished until it's in the scene. Each one adds:

1. A `Section` in `tests/feature_scene.py` that builds a realistic setup. Add to an existing section where the feature belongs there.
2. A `verify` function that checks the result without a person, including after save and reopen.
3. Hands-on steps in the checklist below, for anything only a person can judge.

When a bug is fixed, add a check for it to the section where it would show up.

## Hands-on checklist
Each section has a numbered label on the floor. Note the Beam version and Blender version with your results.

### Moving things
- [ ] Clicking a projector shows its position, pitch, yaw and roll at the top of the inspector, and typing values moves it.
- [ ] Typing `2500 mm` into a position field works.
- [ ] Clicking `· Optics` in the Outliner selects the projector instead.
- [ ] A locked object's fields are greyed out and say why.
- [ ] A new Beam workspace opens on the Move tool, so selecting something shows the arrows.

### 1. Auto Blend
- [ ] Moving the group controller moves all three projectors, using its fields or the arrows.
- [ ] Selecting a member offers Select Whole Group, and the member's fields move only that member.
- [ ] Changing the overlap reflows the group, and the measured overlap matches.
- [ ] Shift-D on the controller makes a complete, independent group with new projector names.
- [ ] Combined Blend Preview and Preview Edge Blend look correct.

### 2. Facade and analysis
- [ ] The truss and columns cast shadows on the facade.
- [ ] Optics Guidance shows the preset and its limits.
- [ ] Analyse Surface works in Density, Stretch, Illuminance and Distance.
- [ ] With Heatmap set to Acuity and an Observer chosen, Analyse Surface gives Acuity results.
- [ ] Moving the truss marks the analysis as stale.

### 3. Reverse Mapping
- [ ] In Material Preview, the colour grid appears inside the projector's coverage.
- [ ] Left alone, the viewport stays idle.
- [ ] Moving the projector updates the coverage.
- [ ] Each mode looks correct, and Restore brings back the original material.

### 4. Heavy venue scan
- [ ] Dragging the mesh stays usable, and the projection follows it.
- [ ] Changing the Subdivision level causes one short pause, then works.
- [ ] Undo and redo of the move work.

### 5. Screens and output modes
- [ ] The UV grid wraps correctly on the arc screen.
- [ ] Update Screen, Validate UV and Export Screen Geometry work on the arc.
- [ ] The open-air projector shows No Target.
- [ ] Mapping Matter CSV export refuses until that projector is fixed or excluded.

### 6. Cycles projection
- [ ] With Projection Mode on Cycles Render, the engine on Cycles and the viewport on Rendered, the projection appears.
- [ ] Light passes through the cloth's cut-outs onto the backdrop.
- [ ] Switching back to Planning removes the Cycles lights.

### General
- [ ] The scene feels responsive when idle, with 3,000 extra objects loaded.
- [ ] Study Views open, step and exit, and each exports a PNG.
- [ ] Every export writes files you can open: CSV, Designer CSV, JSON, Study Package, screen OBJ and FBX.
- [ ] Hide, unhide, duplicate, undo, redo, save and reopen all behave.
- [ ] No red "Beam needs attention" box appears. If one does, record its text and what you were doing.

## Other tests
- **Pure tests:** `python3 -m unittest discover -s tests -p 'test_*.py'`
- **Background suites:** `tests/blender_*.py` and `tests/validate_*.py` run without a GPU. Some need a `work/` folder or other setup, and `blender_refinement.py` needs its `apply` and `restore` phases run separately.
- **GPU suites:** `tests/verify_*.py` and `tests/run_blender_tests.py` need an interactive, disposable Blender.

Some suites rewrite files under `examples/`. Restore those with `git checkout -- examples` rather than committing them with an unrelated change.
