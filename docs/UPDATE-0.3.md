# Projection Study 0.3

## What changed

Automatic targeting and visible projection now have separate implementations. A single centre-raster ray finds the nearest surface for nominal calculations. Visible output uses a perspective GPU shader on evaluated scene triangles and a cached first-depth map for each projector. It does not read the target, target distance or nominal footprint. Rays beside a foreground object continue to farther surfaces. Scene bounds determine the displayed beam and GPU far plane.

All six output modes use the same coordinates and occlusion: Solid Colour, Calibration Grid, Identifier, Checkerboard, Blender UV Grid and Custom Image. Blender UV Grid uses an actual `generated_type='UV_GRID'` image, shared by native resolution. Resolutions up to 4096 on the longest side are exact; larger textures are capped at 4096 while retaining aspect as closely as integer dimensions permit. This cap does not change engineering resolution or projection aspect.

The existing active-projector workflow, pixel-size/unit display, Inter typography, study colours, UUIDs, body/optics, manipulation, camera views, PNG capture, JSON and disguise table remain. Saved-view export explicitly restores its framebuffer between GPU projection, annotations and readback.

## Use and migration

Install `dist/projection_study-0.3.0.zip` through Blender's Install from Disk command, replacing the earlier extension. Reload Blender after updating to avoid old Python module state. Keep existing .blend files; names, UUIDs, optics, colours, views and notes require no conversion.

An old manually assigned Target is now replaced by the first centre-ray hit on refresh. Automatic Target is read-only. No surface tagging or selection is needed. Hidden receivers follow view-layer visibility. Selecting a venue object retains the Active Study Projector.

The nominal engineering model is unchanged: throw is axial depth at the shifted centre-ray hit, and the separate Centre ray value is the actual ray length. Width = axial depth / throw ratio. No Target hides nominal values; projection onto other parts of the raster remains active. JSON exports `calculated: null` for a miss; disguise export still requires a valid centre hit and always uses millimetres.

Projection Quality sets the longest shadow-map dimension to 512, 1024 or 2048. Use 512 for larger projector counts or 2048 for finer occluders. Receiver geometry and GPU batches are shared; a depth map updates only when projector optics/transform, scene geometry, units or quality changes. Output-mode changes reuse visibility. Geometry changes recast one centre ray per projector because any surface can become the nearest target. No Python raster-per-pixel raycasting is used.

## Files changed

- Added `scene_geometry.py`: evaluated mesh-convertible surfaces, instances, bounds and incremental invalidation.
- Added `projection_renderer.py`: perspective shader, receiver-plane depth bias, GPU shadow cache and resource cleanup.
- Added `projection_images.py`: generated Blender UV Grid cache.
- Updated `target_raycast.py`, `runtime.py`: shared BVHs and automatic target data.
- Updated `projector_data.py`, `study_data.py`, `ui.py`, `operators.py`: output mode, quality and automatic target controls.
- Updated `viewport_display.py`, `study_views.py`: surface drawing, beam extent, saved-image framebuffer handling and converted-surface depth pass.
- Updated `export_json.py`: explicit projection model and automatic target semantics.
- Updated manifest, README, tests and example files. The extension is version 0.3.0.

Paths above are relative to `projection_study/` unless otherwise indicated.

## Acceptance procedure

Use a disposable Blender session with the extension enabled. Append the scene from `examples/0.3/projection-acceptance.blend`, or run `tests/verify_projection_engine.py` in a separate UI process. The script creates its own scene and quits only that process when complete.

1. PJ01 points along +Y; Foreground is at 10 m and Rear Wall at 15 m. Target is Foreground, nominal distance 10 m.
2. Observe the centre raster on Foreground, outer raster on Rear Wall, and the projection shadow on Rear Wall.
3. Move Foreground by +4 m along X. Target becomes Rear Wall at 15 m; Foreground receives the right part of the same raster.
4. Switch to Blender UV Grid. Geometry and shadow boundaries are unchanged.
5. Move both objects so the centre misses but side rays hit. The panel shows No Target and side projection remains visible.
6. Try all six modes, move/rotate PJ01, change resolution and shift, and export the current viewport or a saved view.

Automated checks cover GPU first-depth samples at centre/side rays; movement and no-centre-hit cases; shifted-centre targeting; native UV image dimensions; visibility-cache reuse; six output exports; and pixel differences against a clean saved view. The pixel checks verify that foreground and unblocked wall are illuminated while the blocked wall is not.

Run pure tests with `python3 -m unittest discover -s tests -p 'test_*.py' -v`. Run `tests/run_blender_tests.py` in a disposable Blender UI session for milestones 1–11. PNG/camera tests require a GPU context.

## JSON example

`examples/0.3/example-study.json` contains a complete actual export. Schema 1.0 retains stable existing fields and adds `projection_model` and `target.automatic`; deprecated `filter_object_name` is always null. Consumers should ignore unknown fields.

```json
{
  "schema": "projection-study",
  "schema_version": "1.0",
  "projection_model": {
    "receivers": "visible_evaluated_surfaces",
    "coordinates": "perspective_raster",
    "occlusion": "gpu_first_depth",
    "target_role": "automatic_centre_reference_only",
    "shadow_max_dimension": 1024
  }
}
```

Projector records include persistent UUID, SI position, rotation with explicit conventions, optics, target, nominal calculations (including pixel size), colour, notes and mode. View records include stable UUID, name, camera, resolution, overlay settings and image filenames. The JSON also contains the exact disguise columns and rows, or an export-validation error.

## Verified and limitations

Tested on Blender 5.2.2 LTS, macOS/Metal: 22 pure tests; integration milestones 1–11; six output-mode images; automatic-target/occlusion pixel checks; saved views and current composited viewport capture; extension archive validation. The manifest targets Blender 4.5+, but 4.5 and other platforms have not been exercised.

Shadow mapping is sampled, not an exact per-native-pixel visibility solution. Thin occluders, contact edges and extreme slopes can alias or leak within the depth bias. Quality affects memory and speed. Receiver bounds currently include the whole visible scene; very distant geometry can reduce depth precision. Complex venues and many GPU projectors need further profiling. The measured ~1.3 ms update for 32 projectors on one wall covers CPU engineering only, not GPU rendering.

Mesh, curve, surface, text and metaball geometry convertible to evaluated triangles can receive/occlude. Projection treats surfaces as opaque and double-sided; it ignores material transparency, volumes, hair and physical scattering. Projector bodies/helpers are excluded from receiver/occluder geometry. Native solid viewport and exported overlay images are the supported study workflow; these overlays do not become materials or appear in F12 renders. Overlapping projector outputs use alpha compositing rather than additive physical lighting. Geometry outside the active view layer is excluded. Simultaneous editing of different scenes in multiple windows is unsupported.

Illuminance remains a nominal estimate without incidence angle, reflectance or lens-loss modelling. Designer transform and shift conventions still require end-to-end validation in disguise. No direct PATCH connection is added.
