# Projection Study 0.2 — workflow and study exports

The v0.1 projector body, identifier/UUID system, throw-ratio model, camera optics, raycasts, palette, five output modes and disguise table format are retained. This release adds workflow state and export presentation around that core.

## Changes

- **Pixel Size** is nominal horizontal pixel pitch: image width in metres / native X resolution. It is stored in metres per pixel and shown as mm/px by default. At 10 m width and 3840 pixels it is 2.60 mm/px. Pixel Density remains px/m.
- **Metres / Millimetres** is a scene-level display preference. It affects throw, slant distance, image dimensions, lens/target coordinates, preview-distance input, distance labels and movement-button labels. Metre mode shows m/px and a second mm/px row for pixel size. It does not change Blender scene scale, calculations, projector positioning, or disguise's mandatory mm output. Movement operators' F9 input remains explicitly labelled in metres.
- **Active Study Projector** is a persistent scene reference, independent of Blender selection. Selecting a new projector adopts it; selecting geometry retains it. Use the object dropdown, eyedropper/Use Selected Projector button, or clear button to change it. Clear remains effective until a new projector selection or an explicit choice. Projector operators use this active reference. Aim at Object Centre now prefers selected ordinary geometry, then the configured target filter.
- **Receiver updates** invalidate the affected receiver BVHs. Projectors filtered to another receiver are left cached; unfiltered projectors must be reconsidered because the moved object could become their nearest hit. Creation, removal, visibility/collection changes and undo/load can require broader invalidation. Camera and light transforms do not invalidate venue raycasts.
- **Clean identifiers** use Blender's bundled Inter sans-serif (fallback: Blender's default font). Smooth cached font textures replace the block-pixel projected identifier. Body labels use the same face with a subtle shadow. The palette is unchanged. No Apple fonts are used or distributed.
- **Notes** is a projector string field preserved in .blend files and JSON.

## Current-view images

Choose **Export Current View**, select a PNG destination, and confirm. After the file chooser closes and the viewport redraws, Blender captures the **fully composited 3D editor** at its current pixel dimensions. It preserves the scene, enabled study overlays, ordinary viewport overlays and visible editor chrome/sidebar. This is intentionally an exact ad-hoc study screenshot, not an F12 render. Close menus or other popups before capturing. Use a saved view for a clean camera image at a specific resolution.

The most recent successful current-image filename and UTC export timestamp are recorded in scene data and JSON. The filename is user-selected, defaulting to `current-view.png`.

## Saved camera views

1. Position the viewport in perspective or orthographic mode.
2. Choose **Create Study View From Current View** and name it, e.g. `Overview` or `Front Elevation`.
3. The add-on creates an ordinary Blender camera and a scene view entry. It does not replace the scene's production camera or change selection. Its framing is derived from the actual viewport projection, including pan/shift. Initial resolution matches the viewport; edit Width/Height as needed.
4. In the view list, select the entry. Set the camera, export size, Study Overlays, Labels, Frustums and Grids / Output options.
5. Choose **Export Selected Study View** or **Export All Study Views**, then choose a directory. An existing destination image is protected unless **Overwrite Existing Images** is enabled in the file chooser.

Duplicate view names created through the operator are suffixed `02`, `03`, etc. Every view has its own UUID. Filenames are stable for a given name/UUID, for example `pj01-coverage--6c03f582.png`. Renaming a view changes the slug; its UUID is retained. **Remove Study View Entry** keeps the camera, so it cannot accidentally delete a camera used elsewhere.

Named exports use the current scene geometry, viewport shading, projector settings and isolate state. They are repeatable camera framing, not snapshots of all scene state. Projector visibility settings are respected in addition to the view's toggles. A camera can be repositioned with normal Blender tools before re-exporting.

Exports use GPU offscreen drawing, explicit study-overlay composition and a mesh depth pass; no Cycles requirement. They preserve ordinary floor/axis overlays according to the originating viewport's settings when Study Overlays is on, but omit camera/light/empty extras. The PNG is written at exactly the view's Width × Height. Renderer settings, active camera and viewport overlay settings are restored.

## JSON interchange for PATCH Documents

Use **Export Study Data (JSON)**. There is no PATCH connection, upload, API call or automatic document creation. Blender remains the source of technical data.

The root identifiers are `schema: "projection-study"` and `schema_version: "1.0"`. This schema version is independent of the add-on version. The document includes:

- Scene name, UTC export timestamp and explicit units.
- All projector records, including those excluded from disguise, with the inclusion flag, persistent UUID, stable PJ name, Blender object name, notes, optics/output settings, transform, receiver hit information, display preference and visibility.
- Calculations with unit-bearing field names, including both `pixel_size_m_per_px` and convenience `pixel_size_mm_per_px`.
- Named views: UUID, name, camera transform/type, resolution, overlay settings, expected filename, most recent successful filename and export timestamp.
- The most recent current-view image filename/timestamp.
- The exact disguise column list and rows when all included projectors can be exported. Otherwise `disguise.rows` is empty and `disguise.error` explains the issue; usable JSON projector records are still exported.

Coordinates are **Blender world axes in metres**. Projector rotation is XYZ Euler in degrees, explicitly labelled. View cameras use WXYZ quaternions. Colour components are linear RGB. A missing hit has `target.status: "no_hit"`, null target point/object, and `calculated: null`; preview-distance estimates are never presented as measured data. The target's actual hit mesh name is separate from its optional filter object name. Lens shift is percent of the full image dimensions.

The file `examples/0.2/example-study.json` is a complete generated example. This abbreviated record illustrates the calculation fields (other fields omitted here only for readability):

```json
{
  "schema": "projection-study",
  "schema_version": "1.0",
  "scene_name": "Example Study",
  "units": {
    "internal_length": "m",
    "display_length": "mm",
    "disguise_length": "mm",
    "coordinate_space": "blender_world"
  },
  "projectors": [
    {
      "uuid": "cecc3d27-1132-440a-9a82-878298ee7dc2",
      "name": "PJ01",
      "notes": "Front screen",
      "resolution": {"x": 3840, "y": 2160},
      "calculated": {
        "throw_distance_m": 10.0,
        "image_width_m": 10.0,
        "image_height_m": 5.625,
        "pixel_density_px_per_m": 384.0,
        "pixel_size_m_per_px": 0.0026041666666666665,
        "pixel_size_mm_per_px": 2.6041666666666665,
        "dpi": 9.7536,
        "estimated_illuminance_lux": 355.55555555555554
      }
    }
  ]
}
```

Consumers should key projectors/views by UUID, treat unknown fields as extensions, and use declared units rather than the user's display preference. Exported filenames describe the most recent successful asset; geometry/view changes do not automatically regenerate it. Export images first, then JSON, and keep them together for a future PATCH importer.

## Migration and installation

Install `dist/projection_study-0.2.0.zip` through Blender's Install from Disk and enable the extension. Restart Blender after replacing an already loaded 0.1 package to avoid stale Python classes. Keep the same extension ID, `projection_study`.

Existing projector settings and UUIDs stay in the same `Object.ps` property group. New fields receive defaults. Scene workflow data lives in `Scene.ps_study`; default display units are mm. No geometry or scene-unit conversion occurs. A one-time data-version marker disables Blender's old duplicate native object-name labels so the new typography is not doubled. It does not rename objects or regenerate valid UUIDs. Save the .blend after upgrading to persist the new scene settings. Existing 0.1 demo files remain usable.

The update package has not been installed into your running Blender session automatically. Tests use separate factory-startup Blender processes; your open scene is untouched.

## Files added or modified

Added:

- `display_units.py`: SI-to-display formatting.
- `study_data.py`: active projector and persistent study-view properties.
- `study_views.py`: camera creation, selected/all view export and current-view capture.
- `typography.py`: font loading, cached projected text and viewport labels.
- `interchange.py`: version, timestamps, predictable filenames and PNG encoding.
- `export_json.py`: structured study data collection/export.
- `tests/blender_m9.py`, `tests/blender_m10.py`: workflow and view-export checks.
- `tests/verify_view_exports.py`: isolated UI/GPU capture QA script.
- `docs/UPDATE-0.2.md` and the generated JSON/image examples.
- `tools/build_release.py`: reproducible installer/source packaging.

Modified:

- `projection_math.py`: pixel pitch field/function.
- `projector_data.py`, `projector_object.py`: notes, migration marker and active-projector handling.
- `runtime.py`, `target_raycast.py`: targeted receiver invalidation, active state and actual hit-object metadata.
- `viewport_display.py`: smooth text and reusable overlay drawing for exports.
- `operators.py`: active-projector-aware target selection.
- `ui.py`, `__init__.py`, `blender_manifest.toml`: workflow controls, registration and version 0.2.0.
- `tests/test_core.py`, `tests/blender_m4.py`, `tests/run_blender_tests.py`: new fields/typography and extended suite.
- `README.md`, `TEST_RESULTS.txt`, packaged extension README and release archives.

The disguise transform-conversion module and CSV header/writer are unchanged.

## Test procedure

Automated maths/data tests:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

For all ten integration checks, use a disposable Blender session with a 3D View and run `tests/run_blender_tests.py` from the Text Editor, with the installed extension disabled. GPU tests require a UI context. For separate-process visual/export QA, launch Blender with `--factory-startup --python tests/verify_view_exports.py`; this test closes its own Blender process when complete and writes results to `work/`.

Manual acceptance:

1. Create PJ01/PJ02 and confirm the existing body, calibration grid, palette and throw maths.
2. Set width to 10 m with TR 1 at 10 m distance, resolution 3840×2160: density 384 px/m; size 2.60 mm/px.
3. Toggle m/mm. Confirm dimensions and coordinate labels change, while the frustum and geometry do not. Export disguise in both modes; rows must be identical and use mm.
4. Select PJ01, then a screen; move the screen. PJ01 stays active and its distance, dimensions, density, pitch, DPI and lux update. Select PJ02 and repeat. Exercise dropdown and clear controls.
5. Duplicate, rename, save and reopen: UUID rules and manual colours remain intact; the active reference and notes persist.
6. Capture Current View and inspect the PNG. Create named perspective and orthographic views, export selected/all at a known resolution, test overlay toggles and overwrite protection.
7. Export JSON after images. Check UUIDs, notes, actual receiver name, null no-hit records, units, views and filenames. Compare its disguise rows with the TXT export.

## Remaining limits

- Centre-ray/tangent-plane coverage and basic lux remain unchanged. There is no mesh-boundary clipping, curved-surface sampling, blend analysis or photometric simulation.
- Study exports need an interactive 3D View/GPU. Solid viewport mode is the verified export path. Rendered/material-preview modes, other platforms and Blender 4.5 have not been validated in this pass.
- Current View is an editor screenshot, including visible sidebar/header/gizmos and any popups; its resolution is the editor's resolution. Saved views are the clean camera-output path.
- Saved views reuse current scene/shading/visibility/isolation. Changes to aspect ratio intentionally change framing. Supported cameras are perspective and orthographic, not panoramic or stereo. Multiwindow/different-scene workflows remain outside v0.2 scope.
- The export depth pass treats visible meshes as opaque. Transparency, volumes and non-mesh occluders can differ from a shaded viewport. Large-resolution or complex-venue exports may be slower than interactive motion; they run only when requested.
- JSON is an explicit lightweight interchange proposal, not a claim of compatibility with an existing PATCH Documents importer.
- Designer coordinate/Euler/lens-shift conventions remain unvalidated. The CSV dimension unit remains mm and no new conversion guesses were introduced.
