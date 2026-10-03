# Beam 0.5.0 — Twisted Pixel

## Delivered

Beam branding appears in the extension name, sidebar, About label, default resource names and release archives. Maintainer is **Twisted Pixel**. Existing projector maths, seven output modes, automatic centre target, multisurface projection, GPU occlusion, notes, UUIDs, palette, unit display, independent projected-name controls and CSV schema remain.

Presentation View is a reversible per-viewport shading/overlay preset. It uses neutral single-colour venue shading and background, studio lighting and fewer native guides/gizmos. It never edits venue materials. Technical View restores the previous settings. Save hooks temporarily restore the technical viewport for serialization, then reapply the live presentation preset. Loading another file or disabling Beam restores/clears temporary state.

The scene stores optional Project Name, Venue, Revision, Client and Author. Projector Notes remain plain persistent text. Management adds Frame Active Projector, explicit Lock/Unlock, target-marker visibility and clearer Solo naming. Saved-view navigation still provides View, Previous, Next and Exit without a numpad.

## Blend-group architecture

A scene-level `blend_groups` collection stores group UUID, display name, layout, anchor UUID, rows/columns, overlap input mode and values, reference dimensions, member pointers/UUIDs, notes and preview flags. JSON exports these plus current controller transform, member positional/rotational local offsets and desired/actual overlap for adjacent UUID pairs.

The hierarchy is:

```text
BG01 controller (group move / rotation)
  PJ01 layout slot
    PJ01 projector + optical helper
  PJ02 layout slot
    PJ02 projector + optical helper
  ...
```

The controller starts at the first projector's world pose. Projectors remain independent editable objects. Each layout slot is positioned directly from the anchor; layout is never chained from one member to the next. Slot placement changes with overlap while the projector's local transform stores manual fine adjustments. Controller movement naturally preserves these offsets.

Create Blend Group duplicates an anchor to the requested count or array dimensions. Each new member gets independent body/material/camera data, a new PJ identifier, UUID and palette colour; technical settings and notes copy from the anchor. Create From Selected Projectors preserves all existing world transforms and aims. Changing overlap or pressing Apply is the explicit request to align them.

Horizontal/vertical spacing is `anchor image dimension − desired overlap distance`. Arrays use separate horizontal/vertical spacing. Input can be pixels, percent or metres; switching representation preserves its value and does not itself align a manually arranged group. Desired layout overlap is bounded to 0–95%. All three representations are displayed per pair, with physical values using the scene's m/mm display preference.

Changing overlap preserves local positional tweaks. Apply Desired Overlap recalculates nominal dimensions from the current anchor and clears non-anchor positional tweaks; it preserves local aim/optics. Reset to Group Position clears only the active non-anchor member's positional tweak. Layout actions keep the anchor fixed. Changing group topology requires creating/regrouping; there is no matrix editor.

Actual overlap is a deterministic convex intersection of adjacent projector rasters on the current anchor's nominal plane. It responds to position, aim and lens-shift changes. Its px/% measures use the anchor pixel scale; it is not a dense measurement of real curved/occluded surface coverage. Different optics, oblique aiming or manual offsets can yield actual values different from desired.

Overlap visualization draws subtle nominal-plane regions and readable pair labels. The existing GPU renderer still applies real per-projector receiver occlusion. Optional edge preview multiplies output by linear ramps on shared edges. Combined preview maps the anchor output across the ideal combined canvas and uses low-gain additive display compositing to make feathered contributions continuous. Individual mode keeps each member's output and study colour.

Solo Blend Group temporarily suppresses unrelated study outputs. Removing members or ungrouping preserves world transforms and all projector data. Native duplication of a grouped member detaches the new copy from the source layout slot, preserving its world pose and making it independent.

## Export workflow

Default image names use sanitized `Project_Revision_View.png`, falling back to `Beam_View.png`. Spaces and invalid characters become single underscores; empty metadata is omitted. Sanitized/case-insensitive duplicate view names receive deterministic `_02`, `_03`, etc. suffixes.

Current/selected exports open Blender's normal file browser with the proposed filename already visible and editable. Users can edit the filename/destination or cancel. Batch export chooses one folder and exposes editable proposed filenames in the options panel. A chosen PNG filename is used exactly; bad suffixes, subdirectories in batch filenames and duplicate names are rejected before saving. Batch completion reports folder and count. Existing-output protection remains.

CSV is still the exact Mapping Matter/disguise-compatible 27-column schema, including `Projector_Trow-Ratio`, persistent projector UUIDs, `Unit_Dim=mm` and `Unit_Illuminance=lux`. Individual group members remain individual CSV rows. Filename and count feedback are retained. No disguise blend data is added.

JSON schema 1.0 adds `product`, `maintainer`, `project_metadata` and `blend_groups`. Existing stable fields remain, including the legacy `schema: "projection-study"` and `disguise` keys. Study-view records contain both expected/default and actually exported filenames. `examples/0.5/Beam_example.json` is a complete real export suitable as a future PATCH ingestion example.

## Files modified

New modules under `projection_study/`:

- `blend_math.py`: unit conversion, grid adjacency and convex intersection.
- `blend_groups.py`: persistent group/member data, controller/slot hierarchy, creation, layout, reset/remove/ungroup/solo, preview parameters and JSON serialization.
- `blend_ui.py`: compact group controls and desired/actual pair readouts.
- `blend_display.py`: nominal overlap regions and labels.
- `presentation.py`: reversible Technical/Presentation preset and save/load lifecycle.

Updated modules:

- `__init__.py`, `blender_manifest.toml`: registration, lifecycle, Beam identity/version; maintainer remains Twisted Pixel.
- `study_data.py`, `ui.py`: metadata, group collections, management and About controls.
- `operators.py`, `projector_data.py`: framing, explicit locks, solo and target-marker visibility.
- `projector_object.py`, `projection_images.py`: Beam resource naming.
- `runtime.py`: grouped-copy independence and repaired UUID references for appended group members.
- `projection_renderer.py`, `viewport_display.py`: group visibility, combined-canvas coordinates, feather ramps and overlap overlays.
- `interchange.py`, `study_views.py`, `export_json.py`, `export_disguise.py`: default naming, editable native/batch dialogs, metadata/group export and Beam defaults.

Updated packaging, README, regression tests and test log. Added blend math tests, Blender milestones 14/15 and `verify_beam_visuals.py`. No engineering raster-ray grid, calibration solver, manufacturer database, LED tool, PDF generator or direct PATCH connection was added.

## Migration

Install `dist/beam-0.5.0.zip` and restart Blender to unload old Python modules. This is the next version of the existing extension, not a second add-on. The manifest's stable technical ID `projection_study`, source module paths, `Object.ps`/`Scene.ps_study` data and existing operator IDs remain intentionally unchanged so earlier .blend files upgrade in place. Product-facing branding is Beam throughout. The existing Documents project folder is retained.

Existing UUIDs, manual colours, projector settings, notes and study views need no conversion. New project metadata is empty by default; groups are opt-in. Existing projectors remain individual unless explicitly grouped. New image defaults replace the old UUID-slug convention, but recorded previous image filenames remain in JSON until a new export. CSV dimensions/header are unchanged. Projected identifiers retain the unboxed styling and separate controls requested in 0.4.1.

The preset's neutral shading is a viewport choice, not a material edit. The combined preview fills an ideal combined canvas with the anchor's output; choose a source image aspect appropriate to that canvas. Input images can remain shared resources; internal projector transform/settings/mesh/material/camera data are independent.

## Validation and rerun procedure

Tested with Blender 5.2.2 LTS/macOS Metal:

- 27 pure tests: existing engineering/CSV/identity logic plus overlap units, clamps, array adjacency, polygon intersection and Beam filenames.
- Blender milestones 1–15 in disposable scenes: all prior functionality, 4-projector horizontal groups, vertical groups, 3×2 arrays, independent duplicates, anchor pose, pair overlap, controller movement/rotation, local nudge preservation, reset, ungroup and save/library roundtrip.
- Existing selection grouping preserves transforms. Native duplication inside a group becomes independent. CSV remains one valid row per member.
- Presentation toggles restore prior shading/overlays and Matcap choice without modifying materials; save hooks restore/reapply the preset.
- Selected export uses an explicitly edited path. Batch export uses explicitly edited per-view filenames. Native Current, Selected and All file-browser dialogs show editable proposed names and cancel normally.
- GPU acceptance retains foreground-at-10 m / wall-at-15 m projection and occlusion pixel tests, all seven modes and independent projected-name visibility controls.
- Separate four-projector GPU fixture verifies visibly different individual, combined and feathered outputs. Visual inspection checks continuous canvas coordinates and neutral presentation styling. JSON, CSV, .blend and PNG examples are provided.

Commands from the project directory:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

For full Blender integration, run `tests/run_blender_tests.py` in a disposable UI session with a 3D View open. For standalone GPU/file-browser checks, launch separate Blender processes with `--factory-startup --python tests/verify_projection_engine.py` and `--factory-startup --python tests/verify_beam_visuals.py`. These standalone scripts quit their own process and write results into `work/`.

Manual horizontal acceptance: start with PJ01 aimed at a wall; configure optics/output; Create Blend Group → Horizontal → 4 → 400 px. Verify PJ01–PJ04 identities/colours and fixed anchor, then change overlap. Compare each pair's readouts, move/rotate the controller, nudge PJ03, move again, reset PJ03, and ungroup. All projectors remain independent at their final world poses. Repeat in a fresh scene with Array → 3 columns × 2 rows and separate H/V overlap controls.

## Known limits and recommended follow-ups

Overlap/layout is nominal planar planning, not a calibration or freeform warp solver. Actual overlap on physical surfaces, gaps behind occluders and surface-distorted pixel size are not densely analysed. Desired spacing assumes compatible parallel optics; Apply does not solve arbitrary aim/rotation differences. Reapply after changing anchor optics or depth when you want new spacing. Manual offsets/heterogeneous optics can expose seams in the ideal combined preview.

Feathering is a simple linear brightness preview using ideal neighbor widths. There is no gamma, black-level, colour matching or disguise blend export. Combined additive preview is deliberately low-gain and display-referred, not a lux-accurate rendered image. A source image is fitted across the whole combined canvas, so its aspect matters.

The retained GPU projection uses finite-resolution shadow maps and opaque/double-sided triangle surfaces. Thin edges can alias; transparency transmission, hair/volumes and projector-body occlusion are not simulated. Overlays appear in viewport/study captures, not F12 renders. Generated grids cap preview texture size at 4096. Keep controller/projector world scales rigid; arbitrary constraints and simultaneous multiwindow/multiscene editing are unsupported.

Other Blender versions/backends, dense venues and large GPU projector/group counts need profiling. Existing simple-wall CPU timing is not a GPU performance guarantee. Designer transform/lens-shift conventions still require validation in Designer.

Useful follow-ups are real-project usability testing, platform/performance validation, a controlled Designer import test, and later surface-aware overlap measurement if needed. These are not required to use the initial Beam blend-group workflow.

When the anchor has no centre hit, group layout/overlap uses its no-hit preview plane. The group UI marks this explicitly, and JSON pairs report `reference_status` and `actual_plane_distance_m`. These are planned nominal overlaps, not measured receiver coverage.
