# Learn Beam scene
`Learn-Beam.blend` teaches Beam through setups you can change. It's a row of stations in job order, each with one working setup and a sign saying what to try.

| Station | What it teaches |
|---|---|
| Learn Beam | Where the interface is, and how to take the tour |
| 1 Projector | Moving and aiming a projector, reading Calculated, and solving for a width |
| 2 Screens | Changing a curved screen and checking how content wraps |
| 3 Blend | An Auto Blend group, its overlap, moving the group and previewing the blends |
| 4 Surface Analysis | Heatmaps, shadows, the Observer, and Optics Guidance |
| 5 Reverse Mapping | Seeing content only where the light lands |
| 6 Cycles Render | Light passing through a cut-out cloth |
| 7 Views and Export | Saving views and exporting your work |

## Using it
Open the file with Beam installed. It opens on the Beam workspace. On the **Views** tab, press **View**, then **Next**, to visit each station, and **Exit** to look around. The same steps are in the file's text block, **Learn Beam**, in Blender's Text Editor.

Change whatever you like. To start again, reopen the file without saving.

## Building it
The scene is generated, so it stays current with the code. Run this in a new Blender, never one with work open:

```sh
blender --factory-startup --python tools/learn_scene.py -- Learn-Beam.blend --keep
```

The script checks every station, saves the file, reopens it and checks it again, then writes the outcome to `Learn-Beam.blend.result.json`. Without `--keep`, Blender quits when it's finished.

The file is meant to be attached to a release rather than committed, to keep the repository small.

## Changing it
The signs name controls in the interface, so update `tools/learn_scene.py` when a control is renamed. Use [`tests/feature_scene.py`](../tests/feature_scene.py) for testing, not this scene. It leaves out stress cases, such as the heavy scan and the projector with no target, so it won't show those problems.
