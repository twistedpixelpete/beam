# Projection Study 0.4.0

Maintainer: **Twisted Pixel**.

## Changes

- Added Blender **Color Grid**, using Blender's generated COLOR_GRID image. All seven modes use the same perspective projection and first-depth occlusion.
- Made viewport IDs and distance annotations larger, with white Inter text, dark translucent plates and study-colour accent bars. Projected identifiers and resolution captions use the same visual style. A small second glyph pass gives a medium-weight appearance without requiring proprietary fonts.
- Add-on duplication, native Shift-D, linked duplication and copy/paste assign a fresh logical PJ identifier, UUID and the next muted palette colour. Technical properties remain copied. Body meshes, body materials and optical-camera data are independent. Identity ownership survives scene switches; pasting into another scene does not reuse the source UUID.
- Added **View** to each Study View row, plus View Selected, Previous, Next and Exit Study View. No numpad is needed. View makes the camera the active scene camera and enters camera perspective. Exit restores the previous camera, viewport framing and render dimensions/aspect. Saving, loading and disabling the extension clean up temporary navigation state.
- Renamed the table operator to **Export CSV**. The default filename is `projection_study.csv`; other suffixes are replaced with `.csv`. Feedback gives the full saved path and projector count. The exact 27-column Mapping Matter/disguise schema, `Projector_Trow-Ratio`, persistent UUIDs, mm and lux are unchanged.
- Added a centre-ray display and compact global controls for frustums, centre rays, labels, projected output and Study View cameras. Per-projector output controls remain. Global helper visibility is included in JSON.
- Retained location/rotation locking, persistent Active Study Projector, units, pixel size, rename safety, study-image exports and existing engineering calculations.

## Current projection implementation

Engineering uses one centre-raster ray per projector, through the shifted raster centre, to find the first evaluated-surface hit. Its axial depth drives nominal width, height, density, pixel size, DPI and illuminance. The separate Centre ray measurement reports slant distance. A miss clears the target and hides nominal values rather than presenting zero or stale calculations.

The visual layer independently projects onto evaluated scene triangles using one perspective raster and a cached GPU first-depth map. It never reads the centre-target object or distance as a projection boundary. Foreground geometry occludes only the covered portion of the raster; other rays continue to farther geometry. Receiver geometry, BVHs and GPU batches are cached; there is no dense Python pixel-ray loop. The 30 Hz dirty scheduler responds to projector and receiver changes. Normal study work needs no render or manual refresh.

## Files modified

All module paths below are under `projection_study/`:

- `blender_manifest.toml`: version and Twisted Pixel metadata.
- `projector_data.py`, `projection_images.py`, `runtime.py`, `projection_renderer.py`: Color Grid, stable enum IDs, copy identity and palette handling.
- `projector_object.py`: independent body/material/camera data and palette assignment on add-on duplication.
- `typography.py`, `viewport_display.py`: high-contrast labels, projected plates, centre rays and global visibility.
- `study_data.py`, `study_views.py`, `ui.py`, `__init__.py`: saved-view navigation, camera visibility and cleanup.
- `export_disguise.py`, `export_json.py`: CSV-only operator and JSON visibility fields.

Also updated README, tests 4/5/11, the integration runner, both UI verification scripts, TEST_RESULTS and release packaging. Added tests 12/13, this guide and the 0.4 examples. Earlier release archives remain in `dist/`.

## Migration

Install `dist/projection_study-0.4.0.zip` with Blender's Install from Disk command and restart Blender so old Python modules are unloaded. Existing projector IDs, UUIDs, custom colours, optics, notes and saved views remain valid. Existing Custom Image output retains its enum number; Color Grid has a new number and cannot reinterpret older saved modes.

Previously created duplicates keep their stored identity and manual colours. Newly duplicated or pasted projectors receive the palette colour for their new PJ number; manually override it afterwards if desired. The source projector retains its colour. Source/custom images and generated grid assets can remain shared as input resources; projector settings, body meshes/materials and optical cameras are independent. Use Blender's image single-user controls if you need separate editable source-image content.

Automatic targeting introduced in 0.3 remains: legacy manual target assignment does not restrict receivers. JSON schema 1.0 adds helper visibility while retaining existing fields. The JSON `disguise` section keeps its stable key despite the UI's Export CSV rename. Consumers should ignore unfamiliar fields.

Export CSV now replaces `.txt` or other suffixes with `.csv`; update any scripts that expect a text-file extension. Dimensions remain mm regardless of the panel's unit preference. Existing CSV column names and order have not changed.

## Test procedure and results

Verified on Blender 5.2.2 LTS / macOS Metal:

- 22 pure Python tests: maths, unit conversion, pixel size, patterns, naming and export schema.
- Blender milestones 1–13: creation, optics, targets, seven modes, transforms, locks, persistence, active-projector selection, JSON, camera exports, duplicates, paste, navigation and restoration.
- Native Shift-D, linked duplication and actual copybuffer/pastebuffer calls: new names/UUIDs/colours; technical values preserved; meshes, materials and optical camera data independent. Additional cross-scene paste test.
- CSV operator: a requested `.txt` path produces only `.csv`, exact header, five projector rows, mm/lux and persistent UUIDs.
- GPU acceptance fixture: foreground at 10 m, rear wall at 15 m, first-hit depth samples, foreground movement, centre miss with side receivers, shifted centre, UV Grid and Color Grid texture/depth-cache checks.
- Actual exported-image pixel comparisons verify foreground and unblocked wall illumination and a dark blocked-wall region. Global label/output toggles match the clean saved view.
- Visual inspection of Color Grid and high-contrast labels on the acceptance scene and two-projector viewport. Saved-view and composited current-view exports succeed.

From the project folder, run:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

For the full integration suite, run `tests/run_blender_tests.py` in a disposable Blender UI session with a 3D View. The two standalone scripts `tests/verify_projection_engine.py` and `tests/verify_view_exports.py` are intended for separate Blender processes: each quits its own process on completion. Their logs/results and images go to `work/`.

Manual acceptance: append the scene from `examples/0.4/projection-acceptance.blend`. Move Foreground sideways; watch target switch from Foreground to Rear Wall while output and occlusion remain continuous. Try Color Grid, duplicate PJ01, verify the new colour and independent controls, rename it, lock/unlock, select a wall, navigate saved views with View/Next/Previous/Exit, and export CSV. Inspect `examples/0.4/example-study.json` and `example-projectors.csv` for actual data.

## Known limitations

- Projection remains a viewport overlay, including study PNG exports; it does not appear in F12 renders or become receiver materials. Solid viewport mode is the verified workflow.
- Finite 512/1024/2048 shadow maps can alias thin occluders and contact edges. Geometry is treated as opaque and double-sided. No transparency transmission, volumes, hair or advanced photometry. Overlapping outputs use alpha compositing.
- Generated preview grids cap their longest texture dimension at 4096 for memory; native engineering resolution and projection aspect remain unchanged.
- Very dense scenes and high GPU projector counts need profiling. The simple 32-projector CPU update check is about 1.4–1.6 ms and excludes GPU time.
- Labels may still overlap in crowded views; projected identifiers naturally split or occlude with the projected raster. Visibility controls can reduce clutter.
- Simultaneous study navigation in multiple windows/scenes is not a supported workflow. Use Exit Study View before changing projects or opening another temporary camera preview.
- The manifest targets Blender 4.5+, but this pass was tested only on 5.2.2/macOS Metal. Other versions/backends remain unverified.
- Mapping Matter/disguise table structure is preserved, but Designer coordinate/rotation/lens-shift compatibility still needs end-to-end validation in Designer. No direct PATCH integration is added.
